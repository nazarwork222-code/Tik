"""Рушій роликів «CNC TikTok»: стандартні стилі, компонування, Степан, таймлайн за озвучкою.
Не містить нічого про конкретний товар — усе специфічне живе у videos/<slug>/video.py.
stepan.py і brand.py не змінювати.
"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from stepan import stepan, BOLD, INK, WHITE
from brand import background

# ---------------- формат ----------------
W, H, FPS = 1080, 1920, 30
BG = background(W, H)
SAFE_X0, SAFE_X1 = 60, 900          # важливий вміст лише тут
SAFE_Y1 = int(H * 0.85)             # нижче (1632) — без тексту (підпис TikTok)
CX = (SAFE_X0 + SAFE_X1) // 2       # 480 — центр безпечної зони
CAP_Y = 270                         # центр верхнього титру
STAGE = (430, 1230)                 # зона ілюстрації по y

# ---------------- палітра ----------------
BLUE = (3, 167, 226); BLUE_D = (2, 110, 160); GREEN_D = (30, 110, 80)
STEEL = (196, 205, 216); STEEL_D = (120, 132, 148); STEEL_L = (230, 234, 240)
WOOD = (222, 178, 112); WOOD_D = (176, 128, 70); YEL = (250, 200, 40)
OK = (40, 165, 90); BAD = (225, 60, 60); GRAY = (105, 110, 122); DARK = (40, 44, 54)
LOVE = (210, 60, 120); GOLD_BG = (255, 236, 160); WARN_BG = (255, 240, 120)

# ---------------- Степан (стандартна позиція) ----------------
SX, SF, SK = 730, 1600, 0.62        # центр x, низ ніг y, масштаб — правий нижній кут
REST = ((-1, -30), (1, -30))        # руки вниз
POINT = ((-1, 25), (1, -35))        # показує ліворуч на ілюстрацію
HUSH = ((-1, 75), (1, -30))         # рука до рота — для шепоту
JOY = ((-1, 60), (1, 60))           # обидві вгору — wow / радість


@lru_cache(None)
def F(s):
    return ImageFont.truetype(BOLD, int(s))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t); return t * t * (3 - 2 * t)


def back(t):
    t = clamp(t); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def pop(lt, dur=0.25):
    """масштаб «вискакування» для елемента, що з'явився lt секунд тому"""
    return 0.6 + 0.4 * back(lt / dur) if lt < dur else 1.0


def paste_scaled(im, layer, cx, cy, s=1.0, alpha=1.0, rot=0.0):
    if s <= 0.02 or alpha <= 0.01:
        return
    l = layer
    if abs(s - 1) > 1e-3:
        l = l.resize((max(1, int(l.width * s)), max(1, int(l.height * s))), Image.BILINEAR)
    if rot:
        l = l.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        l = l.copy(); l.putalpha(l.split()[3].point(lambda v: int(v * alpha)))
    im.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))


def text_c(d, s, cx, y, size, fill=INK, anchor="mt"):
    d.text((cx, y), s, font=F(size), fill=fill, anchor=anchor)


def dashed(d, a, b, fill=BLUE_D, width=5, n=20):
    for k in range(0, n, 2):
        p0, p1 = k / n, (k + 1) / n
        d.line([(lerp(a[0], b[0], p0), lerp(a[1], b[1], p0)), (lerp(a[0], b[0], p1), lerp(a[1], b[1], p1))], fill=fill, width=width)


def check(d, cx, cy, r=30, k=1.0):
    """зелений кружок з галочкою; k — фаза появи 0..1"""
    rr = r * k
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=OK, outline=INK, width=4)
    if k > 0.6:
        d.line([(cx - r * .45, cy), (cx - r * .12, cy + r * .4), (cx + r * .5, cy - r * .4)], fill=WHITE, width=max(3, int(r / 5)))


# ---------------- титри й бульбашки ----------------
@lru_cache(None)
def plate(lines, size=62, colors=None, bg=WHITE, fg=INK, outline=INK, radius=30):
    """біла табличка з тінню; lines — tuple рядків, colors — tuple кольорів на рядок"""
    f = F(size); pad = 30; lh = int(size * 1.2)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(max(tmp.textlength(l, font=f) for l in lines) + pad * 2)
    h = int(lh * len(lines) + pad * 2 - size * 0.2)
    lay = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([8, 11, w + 8, h + 11], radius, fill=(0, 0, 0, 60))
    ld.rounded_rectangle([3, 3, w + 3, h + 3], radius, fill=bg, outline=outline, width=6)
    for i, l in enumerate(lines):
        c = colors[i] if colors else fg
        ld.text((w / 2 + 3, pad + 3 + i * lh), l, font=f, fill=c, anchor="mt")
    if w + 16 > SAFE_X1 - SAFE_X0:
        print(f"!! титр ширший за безпечну зону ({w + 16}px): {lines}")
    return lay


def caption(im, lines, lt, size=62, colors=None, y=CAP_Y, **kw):
    """верхній титр, вискакує; lt — скільки секунд тому з'явився"""
    lay = plate(tuple(lines), size, tuple(colors) if colors else None, **kw)
    paste_scaled(im, lay, CX, y, pop(lt))


def badge(im, lines, lt, cx, cy, size=56, colors=None, bg=BLUE, fg=WHITE, rot=3):
    """яскравий бейдж-факт (цифра, перевага) — нахилений, вискакує"""
    lay = plate(tuple(lines), size, tuple(colors) if colors else None, bg, fg)
    paste_scaled(im, lay, cx, cy, pop(lt), rot=rot)


def slam(im, lines, lt, cy=730, size=72, rot=4):
    """банер з назвою товару в гачку: падає з 1.6x і пружинить"""
    u = lt
    s = 1.0 + 0.6 * (1 - ease(u / 0.18)) if u < 0.18 else 1.0 + 0.04 * math.exp(-6 * (u - 0.18)) * math.sin(30 * (u - 0.18))
    lay = plate(tuple(lines), size, tuple([WHITE] * len(lines)), BLUE, WHITE)
    paste_scaled(im, lay, CX, cy, s, alpha=ease(u / 0.1), rot=rot)


@lru_cache(None)
def whisper_layer(lines):
    f = F(40); pad = 34; lh = 52
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(max(tmp.textlength(l, font=f) for l in lines) + pad * 2)
    LBL = 36                                   # висота підпису «пошепки:»
    h = pad + LBL + lh * len(lines) + pad - 6   # текст повністю всередині рамки
    if len(lines) > 2 or w > 540:
        print(f"!! шепіт задовгий ({w}px, {len(lines)} рядки): ≤ 2 рядки по ~22 символи — {lines}")
    lay = Image.new("RGBA", (w + 120, h + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    fill = (244, 244, 246); col = (140, 144, 156)
    ld.rounded_rectangle([4, 4, w, h], 34, fill=fill)
    ld.polygon([(w - 90, h - 6), (w - 30, h - 6), (w + 70, h + 60)], fill=fill)
    r = 34; dash, gap = 18, 12

    def dline(x0, y0, x1, y1):
        L = math.hypot(x1 - x0, y1 - y0); n = 0.0
        while n < L:
            a, b = n / L, min(L, n + dash) / L
            ld.line([(lerp(x0, x1, a), lerp(y0, y1, a)), (lerp(x0, x1, b), lerp(y0, y1, b))], fill=col, width=5)
            n += dash + gap
    dline(4 + r, 4, w - r, 4); dline(4 + r, h, w - 90, h); dline(4, 4 + r, 4, h - r); dline(w, 4 + r, w, h - r)
    for box, a0 in (([4, 4, 4 + 2 * r, 4 + 2 * r], 180), ([w - 2 * r, 4, w, 4 + 2 * r], 270),
                    ([w - 2 * r, h - 2 * r, w, h], 0), ([4, h - 2 * r, 4 + 2 * r, h], 90)):
        ld.arc(box, a0, a0 + 90, fill=col, width=5)
    dline(w - 30, h, w + 70, h + 60); dline(w - 90, h, w + 70, h + 60)
    ld.text((pad, pad - 4), "пошепки:", font=F(26), fill=(165, 168, 178))
    for i, l in enumerate(lines):
        ld.text((pad, pad + LBL + i * lh), l, font=f, fill=GRAY)
    return lay


def whisper(im, lines, lt):
    """сіра пунктирна бульбашка «пошепки» зліва від Степана (рядки ≤ ~20 символів)"""
    lay = whisper_layer(tuple(lines))
    left = max(SAFE_X0 + 10, 610 - (lay.width - 50))     # кінчик хвостика завжди біля екрана Степана
    paste_scaled(im, lay, left + lay.width / 2, 1395 - lay.height / 2, pop(lt))


# ---------------- таймлайн ----------------
LS = {}      # key -> старт репліки, с
SST = {}     # сцена -> старт сцени, с
INFO = {"total": 0.0, "nfr": 0}
SCENE_LEAD = 0.12   # картинка змінюється трохи раніше за голос


def build_timeline(order, durs, scenes, lead_in=0.15):
    """order: [(key, пауза_після)], durs: {key: тривалість}, scenes: ключі сцен по порядку"""
    LS.clear(); SST.clear()
    t = lead_in
    for k, g in order:
        LS[k] = t; t += durs[k] + g
    for i, k in enumerate(scenes):
        SST[k] = 0.0 if i == 0 else LS[k] - SCENE_LEAD
    INFO["total"] = t; INFO["nfr"] = int(round(t * FPS))
    return t


def scene_at(t, scenes):
    cur = scenes[0]
    for k in scenes:
        if t >= SST[k]:
            cur = k
    return cur


def since(key, t, dt=0.0):
    """скільки секунд минуло від старту репліки key (+dt — від слова в ній)"""
    return t - LS[key] - dt


# ---------------- Степан у кадрі ----------------
ENV = {"a": None}
_sh = Image.new("RGBA", (int(380 * SK) + 60, int(30 * SK) + 60), (0, 0, 0, 0))
ImageDraw.Draw(_sh).ellipse([30, 30, 30 + 380 * SK, 30 + 30 * SK], fill=(0, 0, 0, 80))
SHADOW = _sh.filter(ImageFilter.GaussianBlur(10 * SK))


def draw_stepan(im, t, i, mood, arms):
    """стандартний Степан: моргає, «дихає», присідає в такт голосу, вал крутиться"""
    if mood == "happy" and (t % 3.3) < 0.1:
        mood = "blink"
    im.alpha_composite(SHADOW, (int(SX - 190 * SK - 30), int(SF - 15 * SK - 30)))
    env = ENV["a"]
    e = env[min(i, len(env) - 1)] if env is not None else 0
    sq = 0.006 * (1 + math.sin(t * 2.6)) + 0.03 * e
    stepan(im, SX, SF, k=SK, mood=mood, arms=arms, squash=sq, shaft_rot=t * 5, t=t, shadow=False, cable=True)


def mini_stepan_xray(mood, t, label="X-RAY"):
    """кругла «рентген»-вставка з маленьким Степаном (показати двигун усередині товару)"""
    lay = Image.new("RGBA", (340, 340), (16, 42, 72, 255))
    ld = ImageDraw.Draw(lay)
    for g in range(0, 340, 34):
        ld.line([(g, 0), (g, 340)], fill=(30, 70, 110), width=2); ld.line([(0, g), (340, g)], fill=(30, 70, 110), width=2)
    stepan(lay, 170, 300, k=0.34, mood=mood, arms=((-1, -20), (1, -20)), shaft_rot=t * 25, t=t, shadow=False, cable=True)
    m = Image.new("L", (340, 340), 0); ImageDraw.Draw(m).ellipse([0, 0, 339, 339], fill=255)
    out = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    out.paste(lay, (10, 10), m)
    od = ImageDraw.Draw(out)
    od.ellipse([4, 4, 355, 355], outline=INK, width=10); od.ellipse([10, 10, 349, 349], outline=(120, 200, 255), width=4)
    od.rounded_rectangle([120, 18, 240, 52], 10, fill=INK); od.text((180, 35), label, font=F(22), fill=(120, 200, 255), anchor="mm")
    return out


@lru_cache(None)
def lens_layer(text="0,2 мм"):
    """лупа з підписом (точність, дрібна деталь)"""
    R = 150
    lay = Image.new("RGBA", (2 * R, 2 * R), (255, 226, 90, 255))
    ld = ImageDraw.Draw(lay)
    for i, gx in enumerate(range(-140, 2 * R + 140, 80)):
        ld.line([(gx, 0), (gx, 90 if i % 2 == 0 else 60)], fill=INK, width=8)
    ld.line([(110, 120), (190, 120)], fill=BLUE_D, width=6)
    for ex, s in ((110, 1), (190, -1)):
        ld.polygon([(ex, 120), (ex + s * 16, 110), (ex + s * 16, 130)], fill=BLUE_D)
    ld.text((150, 180), text, font=F(44), fill=BLUE_D, anchor="mm")
    m = Image.new("L", (2 * R, 2 * R), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    out = Image.new("RGBA", (2 * R + 200, 2 * R + 200), (0, 0, 0, 0))
    out.paste(lay, (20, 20), m)
    od = ImageDraw.Draw(out)
    od.line([(20 + R + R * 0.7, 20 + R + R * 0.7), (2 * R + 180, 2 * R + 180)], fill=INK, width=44)
    od.line([(20 + R + R * 0.72, 20 + R + R * 0.72), (2 * R + 176, 2 * R + 176)], fill=(190, 70, 50), width=30)
    od.ellipse([14, 14, 26 + 2 * R, 26 + 2 * R], outline=INK, width=16)
    od.ellipse([20, 20, 20 + 2 * R, 20 + 2 * R], outline=STEEL, width=6)
    od.arc([50, 50, 2 * R - 10, 2 * R - 10], 200, 250, fill=(255, 255, 255), width=8)
    return out


def tile_box(d, cx, cy, w=230, h=250):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 30, fill=WHITE, outline=INK, width=5)


# ---------------- типові майстерняні предмети ----------------
def wood(d, x0, y0, x1, y1, col=WOOD, outline=INK, grain=True):
    if x1 - x0 < 2:
        return
    d.rounded_rectangle([x0, y0, x1, y1], 6, fill=col, outline=outline, width=4)
    if grain and x1 - x0 > 40:
        hh = y1 - y0
        for j, k in enumerate((0.33, 0.62)):
            yy = y0 + hh * k
            d.line([(x0 + 14 + j * 20, yy), (x1 - 20 - j * 15, yy + (3 if j else -2))], fill=WOOD_D, width=3)


def ruler(d, x0, x1, y, labels=True, step_mm=250):
    d.rectangle([x0, y, x1, y + 56], fill=(255, 220, 60), outline=INK, width=4)
    for i, tx in enumerate(range(int(x0) + 10, int(x1) - 4, 15)):
        big = i % 10 == 0
        d.line([(tx, y + 2), (tx, y + (30 if big else (20 if i % 5 == 0 else 12)))], fill=INK, width=3 if big else 2)
        if big and labels:
            text_c(d, str(i // 10 * step_mm), tx, y + 32, 20, INK)


def tape_case(d, x, y, s=1.0):
    d.rounded_rectangle([x, y, x + 130 * s, y + 120 * s], int(26 * s), fill=YEL, outline=INK, width=5)
    d.ellipse([x + 30 * s, y + 25 * s, x + 100 * s, y + 95 * s], fill=(225, 175, 20), outline=INK, width=4)
    d.ellipse([x + 55 * s, y + 50 * s, x + 75 * s, y + 70 * s], fill=INK)
    d.rectangle([x + 10 * s, y + 104 * s, x + 50 * s, y + 116 * s], fill=DARK)


def tape_blade(d, x, y, ext):
    if ext < 4:
        return
    d.rectangle([x, y, x + ext, y + 16], fill=(255, 220, 60), outline=INK, width=3)
    for tx in range(int(x) + 6, int(x + ext) - 2, 12):
        d.line([(tx, y + 2), (tx, y + (12 if (tx - x) % 60 < 12 else 7))], fill=INK, width=2)
    d.rectangle([x + ext - 4, y - 8, x + ext + 4, y + 18], fill=STEEL_D, outline=INK, width=2)


@lru_cache(None)
def tape_icon(crossed=False):
    lay = Image.new("RGBA", (330, 190), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    tape_blade(ld, 140, 112, 160)
    tape_case(ld, 15, 20)
    if crossed:
        ld.line([(20, 20), (310, 170)], fill=BAD, width=20)
        ld.line([(20, 170), (310, 20)], fill=BAD, width=20)
    return lay


def rot_pts(pts, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def hand_saw(d, cx, cy, ang):
    blade = [(cx - 170, cy - 30), (cx + 120, cy - 22), (cx + 120, cy + 22), (cx - 170, cy + 34)]
    teeth = []
    for i in range(16):
        x = cx - 165 + i * 18
        teeth += [(x, cy + 32 - i * 0.7), (x + 9, cy + 44 - i * 0.7)]
    d.polygon(rot_pts(blade, cx, cy, ang), fill=(205, 210, 220), outline=INK)
    d.line(rot_pts(teeth, cx, cy, ang), fill=INK, width=3)
    handle = [(cx + 110, cy - 40), (cx + 200, cy - 50), (cx + 215, cy + 30), (cx + 120, cy + 34)]
    d.polygon(rot_pts(handle, cx, cy, ang), fill=(190, 70, 50), outline=INK)
    hole = rot_pts([(cx + 145, cy - 20), (cx + 190, cy - 26), (cx + 195, cy + 10), (cx + 148, cy + 12)], cx, cy, ang)
    d.polygon(hole, fill=BG.getpixel((int(cx), int(cy)))[:3], outline=INK)


def pencil(d, x, y):
    d.polygon([(x, y), (x + 4, y - 40), (x + 22, y - 30)], fill=(240, 210, 160), outline=INK)
    d.polygon([(x + 4, y - 40), (x + 22, y - 30), (x + 76, y - 122), (x + 58, y - 132)], fill=(250, 190, 30), outline=INK)
    d.polygon([(x, y), (x + 3, y - 10), (x + 8, y - 6)], fill=INK)


def miter_saw(d, x, ytab, down=0.0, spin=0.0):
    d.rounded_rectangle([x - 85, ytab, x + 85, ytab + 60], 10, fill=DARK, outline=INK, width=4)
    d.rectangle([x + 60, ytab - 150, x + 82, ytab], fill=STEEL_D, outline=INK, width=4)
    by = ytab - 80 + down * 48
    d.line([(x + 70, ytab - 140), (x + 10, by - 20)], fill=INK, width=18)
    d.line([(x + 70, ytab - 140), (x + 10, by - 20)], fill=BLUE, width=10)
    r = 64
    teeth = []
    for i in range(24):
        a = spin + i * math.pi / 12
        rr = r if i % 2 == 0 else r - 9
        teeth.append((x + rr * math.cos(a), by + rr * math.sin(a)))
    d.polygon(teeth, fill=(212, 216, 224), outline=INK)
    d.ellipse([x - 14, by - 14, x + 14, by + 14], fill=STEEL_D, outline=INK, width=3)
    d.pieslice([x - r - 12, by - r - 12, x + r + 12, by + r + 12], 180, 360, fill=BLUE, outline=INK, width=4)
    d.rounded_rectangle([x - 40, by - r - 50, x + 40, by - r - 8], 12, fill=DARK, outline=INK, width=4)
