"""Ролик «Вимірювальний рольганг» (CNCPROM) — гачок «Як нарізати сто однакових брусків…».
Еталон стандарту: дивись, як описано репліки, сцени й звуки. Збірка: python build.py videos/rolgang all
"""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw
from stepan import INK, WHITE
from kit import *

SLUG = "rolgang"

# ---------- озвучка: key -> текст (теги емоцій, числа словами, без наголосів). key з "w" на кінці = шепіт ----------
LINES = {
 "s1":  "[curious] Як нарізати сто однакових брусків і жодного разу не схибити? [excited] Вимірювальний рольганг!",
 "s2":  "[calm] Вручну як буває: міряєш, ставиш риску, ріжеш... а кожен брусок трохи інший.",
 "s2w": "[whispers] А потім ще шукаєш, хто взяв рулетку.",
 "s3":  "[calm] А це стіл на три з половиною метри. Дев'ять роликів — і заготовка котиться по них сама.",
 "s4":  "[thoughtful] На екрані вводиш потрібну довжину, наприклад, тисяча двісті п'ятдесят... і тиснеш старт.",
 "s5":  "[thoughtful] Упор сам їде по двох рейках. Везе його кроковий двигун з енкодером. [excited] Між іншим — мій родич.",
 "s5w": "[whispers] Двоюрідний. По маминій обмотці.",
 "s6":  "[thoughtful] Енкодер стежить за кожним кроком, тож упор стає з точністю до двох десятих міліметра.",
 "s7":  "[confident] Підсунув, відрізав, наступний. [excited] А ще він пам'ятає тридцять шість шаблонів розмірів.",
 "s8":  "[calm] Брус, профіль, труби — усе в розмір. [confident] А браку — до тридцяти відсотків менше.",
 "s9":  "[confident] А рулетку можна повісити на стіну... [whispers] На пам'ять.",
}
# порядок реплік і пауза після кожної, с (0.25 перед шепотом, 0.3–0.4 між сценами)
ORDER = [("s1", .30), ("s2", .25), ("s2w", .35), ("s3", .30), ("s4", .30), ("s5", .25), ("s5w", .35),
         ("s6", .30), ("s7", .30), ("s8", .35), ("s9", .40)]

# звуки, яких нема в sfx_lib/ — згенеруються через ElevenLabs: name -> (опис англійською, секунди)
SFX = {"rollers": ("wooden plank rolling over steel conveyor rollers, soft rumble, workshop", 3.0)}
MUSIC = None   # None = спільна музика з sfx_lib/music.mp3; рядок-промпт = своя музика

TEST_POINTS = ["s1:1.5", "s1:4.2", "s2:3.4", "s2:5.3", "s2w:1.0", "s3:3.6", "s4:3.2",
               "s5:3.0", "s5w:1.0", "s6:1.2", "s6:3.6", "s7:3.6", "s8:3.5", "s9:2.4"]


# ---------- реквізит саме цього ролика ----------
def rolgang(d, x0, x1, ytop, n=9, roll=0.0, pops=None, stop_x=None, saw_down=0.0, saw_spin=0.0, legs=True):
    if legs:
        for lx in (x0 + 40, (x0 + x1) / 2, x1 - 40):
            d.rectangle([lx - 12, ytop + 56, lx + 12, ytop + 250], fill=STEEL_D, outline=INK, width=4)
            d.rounded_rectangle([lx - 34, ytop + 244, lx + 34, ytop + 262], 6, fill=DARK, outline=INK, width=3)
        d.line([(x0 + 40, ytop + 200), (x1 - 40, ytop + 200)], fill=STEEL_D, width=10)
    d.rounded_rectangle([x0, ytop + 18, x1, ytop + 58], 8, fill=STEEL, outline=INK, width=4)
    d.rectangle([x0 + 12, ytop + 40, x1 - 12, ytop + 54], fill=(255, 220, 60))
    for tx in range(int(x0) + 16, int(x1) - 12, 10):
        d.line([(tx, ytop + 40), (tx, ytop + (52 if (tx - x0) % 50 < 10 else 46))], fill=INK, width=2)
    for i in range(n):
        s = 1.0 if pops is None else pops[i]
        if s <= 0.02:
            continue
        cx = x0 + 40 + i * (x1 - x0 - 80) / (n - 1); cy = ytop + 12; r = 21 * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=STEEL_L, outline=INK, width=4)
        a = roll
        d.line([(cx - r * 0.7 * math.cos(a), cy - r * 0.7 * math.sin(a)), (cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a))], fill=STEEL_D, width=4)
    if stop_x is not None:
        d.rounded_rectangle([stop_x - 6, ytop - 150, stop_x + 70, ytop - 96], 8, fill=DARK, outline=INK, width=4)
        d.rectangle([stop_x - 14, ytop - 110, stop_x + 10, ytop - 8], fill=BLUE, outline=INK, width=4)
    if x0 > 150:
        miter_saw(d, x0 - 75, ytop - 8, saw_down, saw_spin)



# ---------- сцени ----------


def sc_s1(im, d, lt, t):
    caption(im, ["Як нарізати 100", "однакових брусків", "і не схибити?"], y=CAP_Y, lt=lt, size=62,
               colors=[INK, INK, BLUE_D])
    # 100 bars grid
    rnd = random.Random(3)
    for n in range(100):
        r_, c_ = divmod(n, 10)
        st = 0.25 + n * 0.022
        if lt < st:
            continue
        s = back((lt - st) / 0.18)
        x = 105 + c_ * 76; y = 520 + r_ * 40
        wdt, hh = 60 * s, 22 * s
        bad = 2.85 < lt < 3.6 and n in (13, 47, 72, 88)
        dx = 6 * math.sin(lt * 40) if bad else 0
        wood(d, x + dx + (60 - wdt) / 2, y + (22 - hh) / 2, x + dx + (60 + wdt) / 2, y + (22 + hh) / 2,
             col=BAD if bad else WOOD, grain=False)
    # tape: appears, gets crossed, flies away
    if lt > 0.4:
        ap = back((lt - 0.4) / 0.3)
        crossed = lt > 4.05
        if lt < 4.4:
            paste_scaled(im, tape_icon(crossed), 270, 1050, 0.9 * ap)
        else:
            u = ease((lt - 4.4) / 0.7)
            paste_scaled(im, tape_icon(True), 270 - 500 * u, 1050 - 450 * u, 0.9 * (1 - 0.5 * u), rot=360 * u)
    # product banner slam
    if lt > 3.62:
        slam(im, ("ВИМІРЮВАЛЬНИЙ", "РОЛЬГАНГ"), lt - 3.62, cy=730, size=72)
    mood = "think" if lt < 3.62 else "wow"
    arms = REST if lt < 3.62 else ((-1, 60), (1, 60))
    return mood, arms


def sc_s2(im, d, lt, t):
    l = t - LS["s2"]; w = t - LS["s2w"]
    steps = "міряєш"
    if l > 2.08: steps += " → риска"
    if l > 3.12: steps += " → ріжеш"
    if l < 4.1:
        caption(im, ["Вручну:", steps], y=CAP_Y - 20, lt=lt, size=50, colors=[BLUE_D, INK])
    else:
        caption(im, ["Кожен брусок", "трохи інший"], y=CAP_Y - 20, lt=l - 4.1, size=60, colors=[INK, BAD])
    MX = 640
    cut = l > 3.95
    # board
    if not cut:
        wood(d, 80, 600, 880, 670)
    else:
        wood(d, 80, 600, MX - 6, 670); wood(d, MX + 6 + 20 * ease((l - 3.95) / 0.3), 600, 880 + 20 * ease((l - 3.95) / 0.3), 670)
    # tape measure (gone during whisper)
    if w < 0:
        ext = (MX - 214) * ease((l - 0.9) / 0.7) if l < 3.0 else (MX - 214) * (1 - ease((l - 3.0) / 0.25))
        tape_blade(d, 214, 584, ext)
        tape_case(d, 82, 470)
    # pencil mark
    if l > 2.08:
        k = ease((l - 2.08) / 0.5)
        d.line([(MX, 600), (MX, 600 + 70 * k)], fill=INK, width=5)
        if l < 2.9:
            pencil(d, MX, 600 + 70 * k)
    # saw
    if 3.0 < l < 4.05:
        u = l - 3.0
        off = 40 * math.sin(u * 16)
        hand_saw(d, MX - 40 + off * 0.8, 560 + off * 0.45 + 30 * ease(u / 0.9), math.radians(-28))
    # resulting pieces
    for j, (lab, ln, c) in enumerate((("1250 ✓", 420, OK), ("1247 ✗", 400, BAD), ("1253 ✗", 440, BAD))):
        st = 4.14 + j * 0.3
        if l < st:
            continue
        s = back((l - st) / 0.25)
        y = 760 + j * 100
        wood(d, 130, y, 130 + ln * s, y + 56)
        d.text((150 + ln * s, y + 28), lab, font=F(46), fill=c, anchor="lm")
    if l > 4.3:
        for yy in range(745, 1050, 22):
            d.line([(550, yy), (550, yy + 12)], fill=GRAY, width=4)
    if w > 0:
        whisper(im, ["А потім ще шукаєш,", "хто взяв рулетку."], w)
        return "smile", HUSH
    if l > 4.84:
        return "error", ((-1, 50), (1, 50))
    return "happy", POINT if 1.0 < l < 3.8 else REST


def sc_s3(im, d, lt, t):
    l = t - LS["s3"]
    slide = 700 * (1 - ease(lt / 0.35))
    x0, x1, yt = 250 + slide, 880 + slide, 820
    pops = [back((l - 2.04 - i * 0.07) / 0.2) if l > 2.04 else 0.0 for i in range(9)] if l < 2.04 + 9 * 0.07 + 0.2 else None
    roll = -(l - 3.0) * 9 if l > 3.0 else 0.0
    rolgang(d, x0, x1, yt, pops=pops, stop_x=None, roll=roll)
    # bar rolling on rollers
    if l > 3.0:
        u = ease((l - 3.0) / 1.6)
        bx = lerp(900, 330, u)
        wood(d, bx, yt - 48, bx + 520, yt - 8)
    # dimension arrow
    if l > 0.72:
        k = ease((l - 0.72) / 0.35)
        mid = (x0 + x1) / 2; half = (x1 - x0) / 2 * k
        y = yt - 120
        d.line([(mid - half, y), (mid + half, y)], fill=INK, width=5)
        for sx in (-1, 1):
            ex = mid + sx * half
            d.polygon([(ex, y), (ex - sx * 22, y - 12), (ex - sx * 22, y + 12)], fill=INK)
            d.line([(ex, y - 26), (ex, y + 26)], fill=INK, width=4)
        if k > 0.5:
            tw = d.textlength("3,5 м", font=F(54))
            d.rounded_rectangle([mid - tw / 2 - 18, y - 42, mid + tw / 2 + 18, y + 40], 16, fill=BG.getpixel((int(mid), int(y)))[:3])
            text_c(d, "3,5 м", mid, y, 54, BLUE_D, anchor="mm")
    if l > 2.04:
        for i in range(9):
            if pops and pops[i] < 0.5:
                continue
            cx = x0 + 40 + i * (x1 - x0 - 80) / 8
            text_c(d, str(i + 1), cx, yt + 70, 30, INK)
    if l > 0.72:
        cap = "3,5 м · 9 роликів" if l > 2.04 else "Стіл 3,5 м"
        caption(im, [cap], y=CAP_Y, lt=l - (2.04 if l > 2.04 else 0.72), size=62,
                   colors=None)
    return "smile", POINT if l > 2.0 else REST


KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "OK"]
KX = [200, 312, 424]; KY = [770, 866, 962, 1058]


def key_pos(ch):
    i = KEYS.index(ch); return KX[i % 3], KY[i // 3]


TYPE_T = [2.40, 2.75, 3.10, 3.45]


def sc_s4(im, d, lt, t):
    l = t - LS["s4"]
    dy = 500 * (1 - ease(lt / 0.3))
    d.rounded_rectangle([150, 470 + dy, 810, 1170 + dy], 40, fill=DARK, outline=INK, width=6)
    d.rounded_rectangle([170, 490 + dy, 790, 1150 + dy], 30, outline=(80, 88, 104), width=3)
    text_c(d, "ДОВЖИНА, мм", 480, 508 + dy, 34, STEEL_L)
    started = l > 4.98
    d.rounded_rectangle([190, 560 + dy, 770, 720 + dy], 20, fill=(10, 30, 26) if not started else (10, 50, 30),
                        outline=(60, 255, 160), width=4)
    n = sum(1 for tt in TYPE_T if l >= tt)
    digits = "1250"[:n]
    cur = "_" if (int(l * 3) % 2 == 0 and not started) else ""
    text_c(d, digits + cur if digits or cur else " ", 480, 640 + dy, 110, (60, 255, 160), anchor="mm")
    for ch in KEYS:
        kx, ky = key_pos(ch)
        pressed = any(0 <= l - tt < 0.15 and "1250"[j] == ch for j, tt in enumerate(TYPE_T))
        fill = BLUE if pressed else (70, 76, 90)
        d.rounded_rectangle([kx, ky + dy + (4 if pressed else 0), kx + 96, ky + 80 + dy], 14, fill=fill, outline=INK, width=4)
        text_c(d, ch, kx + 48, ky + 42 + dy, 40 if len(ch) == 1 else 30, WHITE, anchor="mm")
    for j, tt in enumerate(TYPE_T):
        u = l - tt
        if 0 <= u < 0.3:
            kx, ky = key_pos("1250"[j]); r = 30 + 60 * u / 0.3
            d.ellipse([kx + 48 - r, ky + 40 - r + dy, kx + 48 + r, ky + 40 + r + dy], outline=(120, 220, 255), width=5)
    # START button
    pr = 0 <= l - 4.98 < 0.2
    cx, cy, r = 655, 935 + dy, 92
    d.ellipse([cx - r, cy - r + 10, cx + r, cy + r + 10], fill=(20, 90, 50))
    d.ellipse([cx - r, cy - r + (8 if pr else 0), cx + r, cy + r + (8 if pr else 0)], fill=OK if not started else (60, 220, 120), outline=INK, width=5)
    text_c(d, "СТАРТ", cx, cy + (8 if pr else 0), 36, WHITE, anchor="mm")
    if started:
        u = l - 4.98; rr = r + 90 * u
        if u < 0.4:
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(60, 220, 120), width=6)
    cap = ["Вводиш довжину"] if not started else ["Довжина ✓  →  СТАРТ"]
    caption(im, cap, y=CAP_Y, lt=l if not started else l - 4.98, size=58, colors=[INK] if not started else [GREEN_D])
    return "think", POINT if 2.2 < l < 5.2 else REST


def ruler(d, x0, x1, y, labels=True):
    d.rectangle([x0, y, x1, y + 56], fill=(255, 220, 60), outline=INK, width=4)
    for i, tx in enumerate(range(int(x0) + 10, int(x1) - 4, 15)):
        big = i % 10 == 0
        d.line([(tx, y + 2), (tx, y + (30 if big else (20 if i % 5 == 0 else 12)))], fill=INK, width=3 if big else 2)
        if big and labels:
            text_c(d, str(i // 10 * 250), tx, y + 32, 20, INK)


def stop_carriage(d, x, step_phase=0.0, dy=0):
    d.rounded_rectangle([x - 60, 600 + dy, x + 60, 712 + dy], 14, fill=BLUE_D, outline=INK, width=5)
    d.rectangle([x - 14, 440 + dy, x + 14, 606 + dy], fill=BLUE, outline=INK, width=5)
    d.rounded_rectangle([x - 92, 532 + dy, x - 18, 604 + dy], 10, fill=DARK, outline=INK, width=4)
    for k in range(3):
        d.line([(x - 90, 548 + k * 16 + dy), (x - 20, 548 + k * 16 + dy)], fill=(75, 82, 96), width=4)
    fx = 8 * math.sin(step_phase)
    d.ellipse([x - 55 + fx - 6, 518 + dy, x - 55 + fx + 6, 530 + dy], fill=STEEL_L, outline=INK, width=2)


def sc_s5(im, d, lt, t):
    l = t - LS["s5"]; w = t - LS["s5w"]
    ap = ease(lt / 0.3); DY = 200
    for ry in (628, 676):
        d.rounded_rectangle([60, ry + DY, 60 + 800 * ap, ry + 18 + DY], 6, fill=STEEL, outline=INK, width=4)
    ruler(d, 60, 60 + 800 * ap, 740 + DY)
    u = ease((l - 0.25) / 3.6)
    steps = int(u * 60) if l > 0.25 else 0
    x = 100 + steps * (720 / 60)
    stop_carriage(d, x, step_phase=steps * 1.3, dy=DY)
    mm = int(round(steps / 60 * 1250))
    text_c(d, f"{mm} мм", 480, 830 + DY, 64, BLUE_D)
    if l < 1.9:
        caption(im, ["Упор їде сам"], y=CAP_Y, lt=lt, size=64)
    else:
        caption(im, ["Кроковий двигун", "+ енкодер"], y=CAP_Y, lt=l - 1.9, size=60, colors=[INK, BLUE_D])
    if l > 1.9:
        s = back((l - 1.9) / 0.3)
        ax, ay, bx, by = x - 55, 525 + DY, 330, 560
        for k in range(0, 20, 2):
            p0, p1 = k / 20, (k + 1) / 20
            d.line([(lerp(ax, bx, p0), lerp(ay, by, p0)), (lerp(ax, bx, p1), lerp(ay, by, p1))], fill=BLUE_D, width=5)
        mood = "love" if l > 4.86 else "smile"
        if w > 0:
            mood = "blink" if (w % 1.2) < 0.15 else "smile"
        paste_scaled(im, mini_stepan_xray(mood, t), 250, 560, 0.9 * s)
        if l > 4.86 and w < 0:
            text_c(d, "мій родич ♥", 640, 520, 44, (210, 60, 120))
    if w > 0:
        whisper(im, ["Двоюрідний.", "По маминій обмотці."], w)
        return "smile", HUSH
    if l > 4.86:
        return "love", ((-1, 40), (1, 40))
    return "happy", POINT if 1.9 < l < 4.5 else REST


def sc_s6(im, d, lt, t):
    l = t - LS["s6"]
    # step tracker row
    for i in range(12):
        x = 92 + i * 66; y = 470
        done = l > 0.2 + i * 0.17
        d.rounded_rectangle([x, y, x + 54, y + 54], 10, fill=OK if done else WHITE, outline=INK, width=4)
        if done:
            d.line([(x + 12, y + 28), (x + 23, y + 40), (x + 43, y + 14)], fill=WHITE, width=7)
    text_c(d, "кроки ↔ енкодер", 480, 538, 30, GREEN_D)
    # stop plate stepping to final position
    u = clamp((l - 0.2) / (12 * 0.17))
    sx = 700 - int(u * 12) * 15
    d.rectangle([sx, 620, sx + 40, 960], fill=BLUE, outline=INK, width=6)
    d.rounded_rectangle([sx + 40, 640, sx + 200, 760], 16, fill=DARK, outline=INK, width=5)
    # bar arrives after stop settles
    if l > 2.6:
        k = ease((l - 2.6) / 0.35)
        wood(d, 60, 820, lerp(150, sx, k), 920)
    ruler(d, 60, 860, 975, labels=False)
    if l > 2.54 and l < 2.9:
        r = 20 + 200 * (l - 2.54)
        d.ellipse([sx + 20 - r, 870 - r, sx + 20 + r, 870 + r], outline=OK, width=6)
    if l > 2.95:
        s = back((l - 2.95) / 0.3)
        paste_scaled(im, lens_layer(), sx - 120, 900, 0.85 * s)
    if l < 2.92:
        caption(im, ["Енкодер стежить", "за кожним кроком"], y=CAP_Y - 20, lt=lt, size=56)
    else:
        caption(im, ["Точність", "0,2 мм"], y=CAP_Y - 20, lt=l - 2.92, size=72, colors=[INK, BLUE_D])
    return ("wow", ((-1, 60), (1, 60))) if l > 2.92 else ("happy", POINT)


CYC0, CYC = 0.1, 0.5


def sc_s7(im, d, lt, t):
    l = t - LS["s7"]
    yt = 1010
    n_done = clamp(int((l - CYC0) / CYC), 0, 10) if l > CYC0 else 0
    c = (l - CYC0) / CYC - n_done if l > CYC0 and n_done < 10 else 1.0
    if n_done >= 10:
        c = 1.0
    saw_down = math.sin(math.pi * clamp((c - 0.5) / 0.3)) if c < 0.8 else 0
    rolgang(d, 260, 890, yt, roll=l * 6, stop_x=690, saw_down=saw_down, saw_spin=l * 30, legs=False)
    # feeding bar
    if n_done < 10:
        if c < 0.35:
            bx1 = lerp(330, 680, ease(c / 0.35))
        else:
            bx1 = 680
        left = -40
        if c < 0.62:
            wood(d, left, yt - 48, bx1, yt - 8)
        else:
            wood(d, left, yt - 48, 175, yt - 8)
            k = ease((c - 0.62) / 0.38)
            # piece flies to the stack
            slot = n_done
            tx0, ty = 560, 800 - slot * 30
            x0 = lerp(185, tx0, k); x1 = lerp(680, tx0 + 300, k); y0 = lerp(yt - 48, ty, k)
            wood(d, x0, y0, x1, y0 + lerp(40, 26, k), grain=False)
    # stack
    for j in range(n_done):
        ty = 800 - j * 30
        wood(d, 560, ty, 860, ty + 26, grain=False)
        text_c(d, "1250", 710, ty + 13, 20, INK, anchor="mm")
    if n_done:
        text_c(d, f"1250 мм × {n_done}", 300, 640, 58, BLUE_D, anchor="mm")
    cap = ["Підсунув"]
    if l > 0.62: cap = ["Підсунув → відрізав"]
    if l > 1.34: cap = ["Підсунув → відрізав", "→ наступний!"]
    caption(im, cap, y=CAP_Y, lt=l if l < 0.62 else (l - 0.62 if l < 1.34 else l - 1.34), size=54,
               colors=[INK, BLUE_D] if len(cap) == 2 else None)
    if l > 3.06:
        lay = plate(("36 шаблонів", "розмірів"), 56, (WHITE, WHITE), BLUE, WHITE)
        paste_scaled(im, lay, 300, 1225, 0.6 + 0.4 * back((l - 3.06) / 0.25), rot=3)
    return "happy", ((-1, 20 + 15 * math.sin(l * 12)), (1, -30))


def icon_beam(d, cx, cy):
    d.polygon([(cx - 80, cy - 10), (cx + 30, cy - 10), (cx + 70, cy - 50), (cx - 40, cy - 50)], fill=(235, 200, 140), outline=INK)
    d.polygon([(cx + 30, cy - 10), (cx + 70, cy - 50), (cx + 70, cy + 20), (cx + 30, cy + 60)], fill=WOOD_D, outline=INK)
    d.rectangle([cx - 80, cy - 10, cx + 30, cy + 60], fill=WOOD, outline=INK, width=4)
    for r in (8, 18, 28):
        d.arc([cx + 50 - r * 0.5, cy + 5 - r, cx + 50 + r * 0.5, cy + 5 + r], 0, 360, fill=(140, 95, 45), width=2)


def icon_profile(d, cx, cy):
    s = 72
    d.rounded_rectangle([cx - s, cy - s + 10, cx + s, cy + s + 10], 12, fill=STEEL, outline=INK, width=5)
    for ang in range(4):
        a = math.radians(ang * 90)
        ox, oy = cx + math.cos(a) * (s - 18), cy + 10 + math.sin(a) * (s - 18)
        if ang % 2 == 0:
            d.rectangle([ox - 18, oy - 14, ox + 18, oy + 14], fill=WHITE, outline=INK, width=3)
        else:
            d.rectangle([ox - 14, oy - 18, ox + 14, oy + 18], fill=WHITE, outline=INK, width=3)
    d.ellipse([cx - 16, cy - 6, cx + 16, cy + 26], fill=WHITE, outline=INK, width=4)


def icon_pipe(d, cx, cy):
    d.rectangle([cx - 70, cy - 30, cx + 50, cy + 50], fill=STEEL_D, outline=INK, width=4)
    d.line([(cx - 70, cy - 30), (cx + 50, cy - 30)], fill=INK, width=4)
    d.line([(cx - 60, cy - 14), (cx + 40, cy - 14)], fill=STEEL_L, width=6)
    d.ellipse([cx + 22, cy - 30, cx + 78, cy + 50], fill=STEEL, outline=INK, width=4)
    d.ellipse([cx + 36, cy - 12, cx + 64, cy + 32], fill=DARK, outline=INK, width=3)
    d.ellipse([cx - 98, cy - 30, cx - 42, cy + 50], fill=STEEL_D, outline=INK, width=4)


def sc_s8(im, d, lt, t):
    l = t - LS["s8"]
    items = ((185, "Брус", icon_beam, 0.0), (480, "Профіль", icon_profile, 0.58), (775, "Труби", icon_pipe, 1.24))
    for cx, lab, fn, st in items:
        if l < st:
            continue
        s = back((l - st) / 0.25)
        lay = Image.new("RGBA", (260, 330), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        tile_box(ld, 130, 135); fn(ld, 130, 120)
        ld.text((130, 300), lab, font=F(40), fill=INK, anchor="mm")
        paste_scaled(im, lay, cx, 650, s)
        if l > 2.26:
            k = back((l - 2.26 - (cx - 185) / 2950) / 0.2)
            r = 30 * k
            d.ellipse([cx + 80 - r, 520 - r, cx + 80 + r, 520 + r], fill=OK, outline=INK, width=4)
            if k > 0.6:
                d.line([(cx + 66, 520), (cx + 76, 532), (cx + 95, 508)], fill=WHITE, width=6)
    if l > 1.9:
        caption(im, ["Усе — в розмір!"], y=CAP_Y, lt=l - 1.9, size=66)
    if l > 2.9:
        lay = plate(("−30 %", "браку"), 92, ((210, 40, 50), INK), (255, 240, 120), INK)
        paste_scaled(im, lay, 330, 1040, 0.5 + 0.5 * back((l - 2.9) / 0.3), rot=-5)
    return ("happy", ((-1, 60), (1, 60))) if l > 2.9 else ("smile", POINT)


@lru_cache(None)
def frame_layer():
    lay = Image.new("RGBA", (560, 560), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    px, py = 280, 30  # nail pivot
    ld.line([(px, py), (110, 170)], fill=(120, 90, 60), width=5); ld.line([(px, py), (450, 170)], fill=(120, 90, 60), width=5)
    ld.rectangle([70, 150, 490, 520], fill=(150, 95, 45), outline=INK, width=6)
    ld.rectangle([100, 180, 460, 490], fill=(250, 246, 235), outline=INK, width=4)
    lay.alpha_composite(tape_icon(False).resize((280, 161)), (140, 255))
    ld.rounded_rectangle([200, 438, 360, 474], 6, fill=(220, 180, 70), outline=INK, width=3)
    ld.text((280, 456), "1250?", font=F(22), fill=INK, anchor="mm")
    return lay


def sc_s9(im, d, lt, t):
    l = t - LS["s9"]
    px, py = 480, 470
    ang = 10 * math.exp(-2.2 * lt) * math.sin(lt * 8) if lt > 0 else 0
    drop = 300 * (1 - ease(lt / 0.25))
    lay = frame_layer().rotate(ang, resample=Image.BICUBIC, center=(280, 30))
    im.alpha_composite(lay, (px - 280, int(py - 30 - drop)))
    d = ImageDraw.Draw(im)
    d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=STEEL_D, outline=INK, width=4)
    caption(im, ["А рулетку —", "на стіну"], y=CAP_Y - 30, lt=lt, size=62)
    if l > 1.92:
        lay2 = plate(("На пам'ять",), 60, None, (255, 236, 160), INK)
        paste_scaled(im, lay2, 480, 1110, 0.6 + 0.4 * back((l - 1.92) / 0.25))
    if 0.35 < l < 1.0:
        return "blink", REST
    return ("happy", ((-1, -30), (1, 50 + 12 * math.sin(l * 9)))) if l > 1.0 else ("smile", REST)




# сцена -> функція (im, d, lt, t) -> (mood, arms). Ключ сцени = ключ її першої репліки.
SCENES = {"s1": sc_s1, "s2": sc_s2, "s3": sc_s3, "s4": sc_s4, "s5": sc_s5, "s6": sc_s6, "s7": sc_s7, "s8": sc_s8, "s9": sc_s9}


def sfx_events():
    E = []
    def e(t, name, db=0.0): E.append((round(t, 3), name, db))
    s = LS
    e(s["s1"] + 3.60, "whoosh", -4); e(s["s1"] + 4.40, "tape", -5)
    for n in range(0, 100, 10):
        e(s["s1"] + 0.25 + n * 0.022, "pop", -20)
    e(s["s2"] + 0.90, "tape", -9); e(s["s2"] + 3.0, "handsaw", -6); e(s["s2"] + 4.84, "err", -12)
    for j in range(3): e(s["s2"] + 4.14 + j * 0.3, "pop", -14)
    e(SST["s3"], "whoosh", -12); e(s["s3"] + 3.0, "rollers", -7)
    for i in range(9): e(s["s3"] + 2.04 + i * 0.07, "pop", -18)
    e(SST["s4"], "whoosh", -14)
    for tt in TYPE_T: e(s["s4"] + tt, "click", -10)
    e(s["s4"] + 4.98, "beep", -12)
    e(s["s5"] + 0.25, "stepper", -8); e(s["s5"] + 1.9, "pop", -12)
    for i in range(12): e(s["s6"] + 0.2 + i * 0.17, "tick", -16)
    e(s["s6"] + 2.54, "ding", -8); e(s["s6"] + 2.95, "whoosh", -14)
    for n in range(10): e(s["s7"] + CYC0 + n * CYC + 0.55 * CYC, "chop", -11)
    e(s["s7"] + 3.06, "pop", -10)
    for st in (0.0, 0.58, 1.24): e(s["s8"] + st, "pop", -9)
    e(s["s8"] + 2.9, "ding", -9)
    e(SST["s9"] + 0.05, "nail", -6)
    e(INFO["total"], "whoosh", -10)
    return E
