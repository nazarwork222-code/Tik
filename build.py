"""Конвеєр ролика. Запуск з кореня набору:
  python build.py videos/<slug> voice     # синтез реплік (тільки відсутніх; --force — усіх)
  python build.py videos/<slug> sfx       # звуки й музика (тільки відсутні)
  python build.py videos/<slug> timing    # тривалості, таймлайн, перевірка довжини
  python build.py videos/<slug> test [s2:1.0 ...]  # контрольні кадри + аркуш build/contact.png
  python build.py videos/<slug> all       # voice → sfx → timing → render → mix → final
  python build.py videos/<slug> render|mix|final
  python build.py videos/<slug> words     # час кожного слова в репліках (для синхрону анімації)
  python build.py videos/<slug> check     # гучність, тривалість, розпізнавання мови (faster-whisper)
"""
import sys, os, json, math, subprocess, importlib.util, urllib.request, urllib.error, multiprocessing as mp
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import kit
from kit import W, H, FPS

# ---------- стандарт озвучки (див. voice_notes.md) ----------
VOICE_ID = "TEyBWD5tAHAWqAGEv6yI"     # Yevhen – Resonant and Distinctive
MODEL_ID = "eleven_v4"
OUT_FMT = "mp3_44100_128"             # pcm_44100 — лише Pro; Starter дає mp3_44100_128 / pcm_24000
API = "https://api.elevenlabs.io/v1"
TEMPO = 1.2                           # speed у v4 ігнорується — прискорюємо ffmpeg
WHISPER_GAIN_DB = -5
MAX_LEN = 55.0
END = 3.0                             # фінал endcard.py
SR = 44100

VCHAIN = ("highpass=f=90,equalizer=f=300:t=q:w=1:g=-2,equalizer=f=2500:t=q:w=1:g=-1.5,deesser=i=0.4,"
          "acompressor=ratio=3:threshold=-20dB:attack=10:release=200:makeup=2,highshelf=f=10000:g=1.5,"
          "aecho=0.9:0.6:28|47:0.12|0.07")
WCHAIN = ",highpass=f=280,lowpass=f=5500,equalizer=f=1800:t=q:w=1:g=3"   # «вбік» для шепоту
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse")


def is_whisper(k):
    return k.endswith("w")


def run(*a, **kw):
    return subprocess.run(list(a), check=True, **kw)


def probe_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def post(url, body, out):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(out, "wb") as f:
            f.write(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API {e.code} для {out}: {e.read()[:300]!r}")


def load_video(vdir):
    spec = importlib.util.spec_from_file_location("video", os.path.join(vdir, "video.py"))
    v = importlib.util.module_from_spec(spec); sys.modules["video"] = v
    spec.loader.exec_module(v)
    return v


# ---------- кроки ----------
def step_voice(V, vdir, force=False):
    os.makedirs(f"{vdir}/vo", exist_ok=True)
    for k, text in V.LINES.items():
        out = f"{vdir}/vo/{k}.mp3"
        if os.path.exists(out) and not force:
            continue
        post(f"{API}/text-to-speech/{VOICE_ID}?output_format={OUT_FMT}",
             {"text": text, "model_id": MODEL_ID, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}, out)
        print("voice", k, round(probe_dur(out), 2))
    step_proc(V, vdir)


def step_proc(V, vdir):
    os.makedirs(f"{vdir}/vo_proc", exist_ok=True)
    tempo = getattr(V, "TEMPO", TEMPO)
    durs = {}
    for k in V.LINES:
        af = f"aresample={SR},{TRIM},atempo={tempo},{VCHAIN}{WCHAIN if is_whisper(k) else ''},loudnorm=I=-16:TP=-1.5:LRA=11,aresample={SR}"
        run("ffmpeg", "-loglevel", "error", "-y", "-i", f"{vdir}/vo/{k}.mp3", "-af", af, "-ac", "1", "-ar", str(SR), f"{vdir}/vo_proc/{k}.wav")
        durs[k] = round(probe_dur(f"{vdir}/vo_proc/{k}.wav"), 4)
    os.makedirs(f"{vdir}/build", exist_ok=True)
    json.dump(durs, open(f"{vdir}/build/durs.json", "w"), indent=1)
    print("speech total", round(sum(durs.values()), 2), "s")


def find_sfx(vdir, name):
    for p in (f"{vdir}/sfx/{name}.mp3", f"{ROOT}/sfx_lib/{name}.mp3"):
        if os.path.exists(p):
            return p
    return None


def step_sfx(V, vdir):
    os.makedirs(f"{vdir}/sfx", exist_ok=True)
    for name, (prompt, dur) in getattr(V, "SFX", {}).items():
        if find_sfx(vdir, name):
            continue
        post(f"{API}/sound-generation", {"text": prompt, "duration_seconds": dur, "prompt_influence": 0.6}, f"{vdir}/sfx/{name}.mp3")
        print("sfx", name)
    if getattr(V, "MUSIC", None) and not os.path.exists(f"{vdir}/sfx/music.mp3"):
        post(f"{API}/music?output_format=mp3_44100_128", {"prompt": V.MUSIC, "music_length_ms": 50000}, f"{vdir}/sfx/music.mp3")
        print("music generated")


def timeline(V, vdir):
    durs = json.load(open(f"{vdir}/build/durs.json"))
    tot = kit.build_timeline(V.ORDER, durs, list(V.SCENES))
    return tot


def voice_env(V, vdir):
    tot = kit.INFO["total"]; nfr = kit.INFO["nfr"]
    a = np.zeros(int((tot + 1) * SR), np.float32)
    for k in kit.LS:
        x = load_audio(f"{vdir}/vo_proc/{k}.wav")
        s = int(kit.LS[k] * SR); a[s:s + len(x)] += x[:len(a) - s]
    hop = SR // FPS
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(nfr + 2)])
    e = e / (e.max() + 1e-9)
    return np.convolve(e, [0.25, 0.5, 0.25], "same")


def step_timing(V, vdir):
    tot = timeline(V, vdir)
    np.save(f"{vdir}/build/env.npy", voice_env(V, vdir))
    json.dump({"total": tot, "voice": kit.LS, "scenes": kit.SST, "sfx": V.sfx_events()},
              open(f"{vdir}/build/timeline.json", "w"), ensure_ascii=False, indent=1)
    full = tot + END
    print(f"контент {tot:.2f} с + фінал {END} = {full:.2f} с")
    for k in V.SCENES:
        print(f"  {k}: {kit.SST[k]:6.2f} с")
    if full > MAX_LEN:
        print(f"!! довше за {MAX_LEN} с: скоротіть текст або паузи в ORDER (чи TEMPO до 1.25)")


# ---------- рендер ----------
_V = None


def frame(i):
    t = i / FPS
    im = kit.BG.copy()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    scenes = list(_V.SCENES)
    k = kit.scene_at(t, scenes)
    mood, arms = _V.SCENES[k](im, d, t - kit.SST[k], t)
    kit.draw_stepan(im, t, i, mood, arms)
    return im.convert("RGB")


def _init(vdir):
    global _V
    _V = sys.modules["video"]
    kit.ENV["a"] = np.load(f"{vdir}/build/env.npy")


def _render(i):
    return frame(i).tobytes()


def step_test(V, vdir, pts):
    step_timing(V, vdir); _init(vdir)
    from PIL import Image
    pts = pts or getattr(V, "TEST_POINTS", None) or [f"{k}:1.5" for k in V.SCENES]
    files = []
    for p in pts:
        k, x = p.split(":")
        f = f"{vdir}/build/test_{k}_{x}.png"
        frame(int((kit.LS[k] + float(x)) * FPS)).save(f); files.append(f)
    cols = min(7, len(files)); rows = math.ceil(len(files) / cols)
    sheet = Image.new("RGB", (270 * cols, 480 * rows), "white")
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).resize((270, 480)), ((i % cols) * 270, (i // cols) * 480))
    sheet.save(f"{vdir}/build/contact.png"); print("контрольний аркуш:", f"{vdir}/build/contact.png")


def step_render(V, vdir):
    step_timing(V, vdir); _init(vdir)
    out = f"{vdir}/build/content.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    with mp.get_context("fork").Pool(os.cpu_count(), initializer=_init, initargs=(vdir,)) as pool:
        for b in pool.imap(_render, range(kit.INFO["nfr"]), chunksize=8):
            p.stdin.write(b)
    p.stdin.close()
    if p.wait():
        sys.exit("рендер не вдався")
    print("відео без звуку:", out)


# ---------- звук ----------
def load_audio(path, ch=1):
    b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", str(ch), "-ar", str(SR), "-"],
                       capture_output=True, check=True).stdout
    a = np.frombuffer(b, np.int16).astype(np.float32) / 32768
    return a.reshape(-1, ch) if ch > 1 else a


def db(x):
    return 10 ** (x / 20)


rng = np.random.default_rng(7)


def _exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def _fade(a, fin=0.005, fout=0.05):
    a = a.copy(); i, o = int(fin * SR), int(fout * SR)
    if i: a[:i] *= np.linspace(0, 1, i)
    if o and len(a) > o: a[-o:] *= np.linspace(1, 0, o)
    return a


def proc_sfx(name):
    """дрібні звуки, які дешевше синтезувати, ніж генерувати: click tick beep pop err"""
    tt = lambda n: np.arange(n) / SR
    if name == "click":
        n = int(0.04 * SR); return rng.standard_normal(n) * _exp(n, 0.004) + np.sin(2 * np.pi * 2400 * tt(n)) * _exp(n, 0.006) * 0.6
    if name == "tick":
        n = int(0.03 * SR); return (rng.standard_normal(n) * 0.5 + np.sin(2 * np.pi * 3200 * tt(n))) * _exp(n, 0.003)
    if name == "beep":
        n = int(0.22 * SR); x = tt(n); return _fade(np.sin(2 * np.pi * 1320 * x) * 0.8 + 0.2 * np.sin(2 * np.pi * 2640 * x), 0.005, 0.04)
    if name == "pop":
        n = int(0.09 * SR); f = 900 * np.exp(-tt(n) * 30) + 220
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _exp(n, 0.025)
    if name == "err":
        n = int(0.42 * SR); x = tt(n)
        sq = np.sign(np.sin(2 * np.pi * 180 * x)) * 0.5 + np.sign(np.sin(2 * np.pi * 240 * x)) * 0.3
        return _fade(sq * ((x % 0.2) < 0.15), 0.003, 0.03)
    return None


def step_mix(V, vdir):
    TL = json.load(open(f"{vdir}/build/timeline.json"))
    TOT = TL["total"] + END; N = int(TOT * SR) + SR // 2; end = int(TOT * SR)

    def place(dst, src, t, g=1.0):
        s = int(t * SR)
        if s < len(dst):
            n = min(len(src), len(dst) - s); dst[s:s + n] += src[:n] * g

    voice = np.zeros(N, np.float32); main = np.zeros(N, np.float32)
    for k, t in TL["voice"].items():
        a = load_audio(f"{vdir}/vo_proc/{k}.wav")
        place(voice, a, t, db(WHISPER_GAIN_DB) if is_whisper(k) else 1.0)
        if not is_whisper(k):
            place(main, np.abs(a), t)
    # механічний шар під мовою Степана
    win = int(0.08 * SR)
    ev = np.convolve(main, np.ones(win) / win, "same"); ev = np.clip(ev / (ev.max() + 1e-9) * 3, 0, 1)
    x = np.arange(N) / SR
    hum = 0.5 * np.sin(2 * np.pi * 330 * x) + 0.25 * np.sin(2 * np.pi * 660 * x + 0.3)
    ticks = np.zeros(N, np.float32); tk = proc_sfx("tick")
    for s in range(0, N - len(tk), int(SR / 14)):
        ticks[s:s + len(tk)] += tk
    fx = ((hum * 0.35 + ticks * 0.8) * ev * db(-34)).astype(np.float32)
    cache = {}
    for t, name, g in TL["sfx"]:
        if name not in cache:
            a = proc_sfx(name)
            if a is None:
                p = find_sfx(vdir, name)
                if not p:
                    sys.exit(f"нема звуку {name}: додайте в SFX у video.py або в sfx_lib/")
                a = _fade(load_audio(p), 0.003, 0.25)
            cache[name] = (a / (np.abs(a).max() + 1e-9) * db(-3)).astype(np.float32)
        place(fx, cache[name], t, db(g))
    amb1 = load_audio(find_sfx(vdir, "ambience"))
    amb = np.tile(amb1, N // len(amb1) + 2)[:N]
    amb = amb / (np.sqrt(np.mean(amb ** 2)) + 1e-9) * db(-40); amb[:SR // 2] *= np.linspace(0, 1, SR // 2)
    mpath = find_sfx(vdir, "music"); mu = load_audio(mpath, 2); xf = int(1.5 * SR)
    while len(mu) < N:
        seg = load_audio(mpath, 2); r = np.linspace(0, 1, xf)[:, None]
        mu = np.concatenate([mu[:-xf], mu[-xf:] * (1 - r) + seg[:xf] * r, seg[xf:]])
    mu = mu[:N] / (np.sqrt(np.mean(mu[:N] ** 2)) + 1e-9) * db(-27)
    fo = SR
    mu[end - fo:end] *= np.linspace(1, 0, fo)[:, None]; mu[end:] = 0
    amb[end - fo:end] *= np.linspace(1, 0, fo); amb[end:] = 0

    b = f"{vdir}/build"
    for n, a in (("voice", voice), ("fx", fx), ("amb", amb), ("music", mu)):
        a = np.clip(a, -1, 1)
        if a.ndim == 1:
            a = np.stack([a, a], 1)
        run("ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", f"{b}/st_{n}.wav",
            input=a.astype(np.float32).tobytes())
    FC = ("[0:a]asplit=3[v][k1][k2];"
          "[3:a][k1]sidechaincompress=threshold=0.05:ratio=4:attack=200:release=1000[m];"
          "[2:a][k2]sidechaincompress=threshold=0.05:ratio=3:attack=200:release=1000[a];"
          "[v][1:a][a][m]amix=inputs=4:normalize=0[mix]")
    ins = sum((["-i", f"{b}/st_{n}.wav"] for n in ("voice", "fx", "amb", "music")), [])
    run("ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", FC, "-map", "[mix]", "-t", f"{TOT:.3f}", f"{b}/premix.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{b}/premix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    run("ffmpeg", "-loglevel", "error", "-y", "-i", f"{b}/premix.wav", "-af", af, f"{b}/mix.wav")
    print("звук:", f"{b}/mix.wav", round(TOT, 2), "с")


def step_final(V, vdir):
    ec = f"{ROOT}/build/endcard.mp4"
    if not os.path.exists(ec):
        os.makedirs(f"{ROOT}/build", exist_ok=True)
        run(sys.executable, "endcard.py", ec, cwd=ROOT)
    out = f"{vdir}/{V.SLUG}_tiktok.mp4"
    run("ffmpeg", "-loglevel", "error", "-y", "-i", f"{vdir}/build/content.mp4", "-i", ec, "-i", f"{vdir}/build/mix.wav",
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]", "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", out)
    print("ГОТОВО:", out)
    step_check(V, vdir, asr=False)


def step_check(V, vdir, asr=True):
    out = f"{vdir}/{V.SLUG}_tiktok.mp4"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    summ = r[r.rindex("Summary"):]
    I = [l.strip() for l in summ.splitlines() if l.strip().startswith(("I:", "Peak:"))]
    print(f"тривалість {probe_dur(out):.2f} с |", " | ".join(I))
    if asr:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            sys.exit("pip install faster-whisper  (для перевірки мови)")
        b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", out, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                           capture_output=True).stdout
        a = np.frombuffer(b, np.int16).astype(np.float32) / 32768
        for s in WhisperModel("small", device="cpu", compute_type="int8").transcribe(a, language="uk")[0]:
            print(f"{s.start:5.1f}-{s.end:5.1f} {s.text.strip()}")


def step_words(V, vdir):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("pip install faster-whisper")
    m = WhisperModel("small", device="cpu", compute_type="int8"); out = {}
    for k in V.LINES:
        b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"{vdir}/vo_proc/{k}.wav", "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                           capture_output=True).stdout
        a = np.frombuffer(b, np.int16).astype(np.float32) / 32768
        out[k] = [(w.word.strip(), round(w.start, 2)) for s in m.transcribe(a, language="uk", word_timestamps=True)[0] for w in s.words]
        print(k, " ".join(f"{w}@{x}" for w, x in out[k]))
    json.dump(out, open(f"{vdir}/build/words.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.chdir(ROOT)
    vdir, what = sys.argv[1].rstrip("/"), sys.argv[2]
    V = load_video(vdir)
    rest = [a for a in sys.argv[3:] if not a.startswith("--")]
    if what == "voice": step_voice(V, vdir, "--force" in sys.argv)
    elif what == "proc": step_proc(V, vdir)
    elif what == "sfx": step_sfx(V, vdir)
    elif what == "timing": step_timing(V, vdir)
    elif what == "test": step_test(V, vdir, rest)
    elif what == "render": step_render(V, vdir)
    elif what == "mix": step_timing(V, vdir); step_mix(V, vdir)
    elif what == "final": step_final(V, vdir)
    elif what == "check": step_check(V, vdir)
    elif what == "words": step_words(V, vdir)
    elif what == "all":
        step_voice(V, vdir); step_sfx(V, vdir); step_render(V, vdir); step_mix(V, vdir); step_final(V, vdir)
    else:
        sys.exit(__doc__)
