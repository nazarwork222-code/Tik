"""Ролик «Лазерна трубка CO2 Reci W6 130 Вт» (CNCPROM) — гачок «Як підключити лазерну трубку і не зіпсувати її в перший день?».
Акцент: підключення (огляд → вода → живлення → порядок увімкнення → холод) + що вміє.
Збірка: python build.py videos/co2tube all
Події прив'язані до частки тривалості репліки (at/D), тож після реальної озвучки синхрон зберігається;
за потреби уточнити по `python build.py videos/co2tube words`.
"""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw
from stepan import INK, WHITE
from kit import *

SLUG = "co2tube"

LINES = {
 "s1":  "[curious] Як підключити лазерну трубку і не зіпсувати її в перший день? [excited] Дивись!",
 "s2":  "[thoughtful] Скляна трубка на сто тридцять ват: усередині газ, подаєш напругу — і виходить промінь.",
 "s2w": "[whispers] Я теж світюся від напруги.",
 "s3":  "[calm] Крок нульовий: ціле скло перевір ще на пошті, до підпису.",
 "s4":  "[thoughtful] Крок перший — вода. Тільки дистильована, три-п'ять літрів на хвилину, від чилера.",
 "s5":  "[thoughtful] Крок другий: плюс високої напруги — на анод, під силіконовий ковпак. Мінус — на катод.",
 "s5w": "[whispers] Двадцять вісім кіловольт. Я не дивлюся.",
 "s6":  "[confident] Блок живлення — трохи потужніший за трубку, а лазер — не вище дев'яноста відсотків.",
 "s7":  "[thoughtful] Порядок: спершу чилер, щоб не було бульбашок, — потім лазер.",
 "s8":  "[calm] І не морозь її: нижче плюс п'яти — не вмикати. Тоді прослужить до десяти тисяч годин.",
 "s9":  "[excited] Ріже фанеру, акрил, шкіру, гравіює камінь. [confident] А окуляри — завжди.",
 "s9w": "[whispers] Мені теж купили.",
}
ORDER = [("s1", .30), ("s2", .25), ("s2w", .35), ("s3", .30), ("s4", .30), ("s5", .25), ("s5w", .35),
         ("s6", .30), ("s7", .30), ("s8", .35), ("s9", .25), ("s9w", .40)]

# нові звуки (у цій теці вже лежать синтезовані версії; видали mp3 — і build.py згенерує через ElevenLabs)
SFX = {
    "glass_crack": ("glass tube cracking, sharp brittle crack, short", 1.2),
    "water_flow":  ("water flowing through plastic hoses, gentle gurgle, pump", 3.0),
    "hv_crackle":  ("high voltage electric spark crackle, short zap", 1.2),
    "laser_zap":   ("co2 laser cutting plywood, buzzing hiss, short", 2.0),
}
MUSIC = None

TEST_POINTS = ["s1:0.6", "s1:2.4", "s1:4.0", "s2:1.5", "s2:4.6", "s2w:1.0", "s3:2.5", "s4:3.5",
               "s5:3.0", "s5:5.6", "s5w:1.6", "s6:1.5", "s6:4.5", "s7:1.8", "s7:3.8", "s8:1.5",
               "s8:4.5", "s9:1.8", "s9:3.6", "s9w:0.7"]


# ---------- час: події прив'язані до частки репліки ----------
def D(k):
    keys = [x[0] for x in ORDER]; i = keys.index(k)
    end = LS[keys[i + 1]] if i + 1 < len(keys) else INFO["total"]
    return end - LS[k] - ORDER[i][1]


def at(k, frac):
    """секунда від початку репліки k, що відповідає частці frac її тривалості"""
    return D(k) * frac


# ---------- палітра ролика ----------
GLASS = (214, 236, 244); GLASS_D = (150, 190, 205); INNER = (236, 246, 250)
WATER = (120, 190, 235); WATER_D = (60, 140, 200); GLOW = (255, 120, 190)
BEAM = (255, 50, 60); RED_W = (220, 50, 50); BLACK_W = (45, 45, 52); CARD = (205, 160, 105); CARD_D = (165, 120, 70)


def mix(a, b, k):
    k = clamp(k); return tuple(int(lerp(a[i], b[i], k)) for i in range(3))


def partial(pts, k):
    """перші k (0..1) довжини ламаної"""
    if k <= 0:
        return []
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = sum(seg) * clamp(k); out = [pts[0]]
    for i, s in enumerate(seg):
        if L >= s:
            out.append(pts[i + 1]); L -= s
        else:
            a = L / s if s else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], a), lerp(pts[i][1], pts[i + 1][1], a))); break
    return out


def point_on(pts, k):
    p = partial(pts, k)
    return p[-1] if p else pts[0]


def bolt(d, x, y, dx, dy, seed, col=(255, 230, 60), width=6, n=6):
    r = random.Random(seed); pts = [(x, y)]
    for i in range(1, n + 1):
        f = i / n
        pts.append((x + dx * f + r.uniform(-14, 14) * (1 - f * 0.5), y + dy * f + r.uniform(-14, 14)))
    d.line(pts, fill=INK, width=width + 6, joint="curve"); d.line(pts, fill=col, width=width, joint="curve")


# ---------- реквізит ----------
def tube(d, x0, x1, cy, water=0.0, glow=0.0, gas=0.0, t=0.0, bubbles=(), crack=0.0, beam=0.0,
         cap=1.0, cap_hi=0.0, label=False, noz_down=False):
    """скляна CO2-трубка: зліва анод (силіконовий ковпак), справа катод і вихідне вікно"""
    R = 52
    for nx in (x0 + 90, x1 - 90):                       # патрубки води
        if noz_down:
            d.rounded_rectangle([nx - 11, cy + R - 6, nx + 11, cy + R + 38], 4, fill=GLASS, outline=INK, width=4)
        else:
            d.rounded_rectangle([nx - 11, cy - R - 38, nx + 11, cy - R + 6], 4, fill=GLASS, outline=INK, width=4)
    d.rounded_rectangle([x0, cy - R, x1, cy + R], R, fill=GLASS, outline=INK, width=5)
    if water > 0:
        wx = x0 + 8 + (x1 - x0 - 16) * clamp(water)
        if wx - x0 > 30:
            d.rounded_rectangle([x0 + 8, cy - R + 8, wx, cy + R - 8], R - 8, fill=WATER)
    d.line([(x0 + 30, cy - R + 12), (x1 - 30, cy - R + 12)], fill=WHITE, width=4)   # відблиск
    col = mix(INNER, GLOW, glow)
    if glow > 0.05:
        d.rounded_rectangle([x0 + 40, cy - 28, x1 - 40, cy + 28], 26, fill=mix(GLASS, GLOW, glow * 0.6))
    d.rounded_rectangle([x0 + 48, cy - 17, x1 - 48, cy + 17], 15, fill=col, outline=GLASS_D, width=3)
    if gas > 0:
        r = random.Random(5); cols = ((90, 90, 100), (60, 140, 230), (240, 170, 40))
        for i in range(int(22 * gas)):
            gx = x0 + 70 + r.random() * (x1 - x0 - 140) + 6 * math.sin(t * 5 + i)
            gy = cy + r.uniform(-8, 8) + 3 * math.cos(t * 6 + i * 2)
            d.ellipse([gx - 6, gy - 6, gx + 6, gy + 6], fill=cols[i % 3])
    for ex in (x0 + 40, x1 - 52):                        # електроди
        d.rectangle([ex, cy - 26, ex + 12, cy + 26], fill=STEEL_D, outline=INK, width=2)
    d.ellipse([x1 - 14, cy - 22, x1 + 14, cy + 22], fill=(200, 230, 255), outline=INK, width=3)  # вихідне вікно
    for bx, by, br in bubbles:
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=WHITE, outline=WATER_D, width=3)
    if cap > 0.02:                                        # силіконовий ковпак анода
        s = cap * (1 + 0.25 * cap_hi)
        d.rounded_rectangle([x0 - 52 * s, cy - 40 * s, x0 + 22, cy + 40 * s], int(14 * s),
                            fill=mix((245, 245, 240), (255, 230, 120), cap_hi), outline=INK, width=4)
    if crack > 0:
        mx = (x0 + x1) / 2 + 40
        pts = [(mx, cy - R), (mx - 18, cy - 22), (mx + 14, cy - 2), (mx - 10, cy + 20), (mx + 12, cy + R)]
        d.line(partial(pts, crack), fill=INK, width=6, joint="curve")
        if crack > 0.6:
            d.line([(mx - 18, cy - 18), (mx - 50, cy - 30)], fill=INK, width=4)
            d.line([(mx + 14, cy - 2), (mx + 48, cy + 6)], fill=INK, width=4)
    if beam > 0:
        bx = x1 + 12 + (W + 40 - x1) * clamp(beam)
        d.line([(x1 + 12, cy), (bx, cy)], fill=(255, 150, 160), width=22)
        d.line([(x1 + 12, cy), (bx, cy)], fill=BEAM, width=10)
        d.line([(x1 + 12, cy), (bx, cy)], fill=WHITE, width=3)
    if label:
        text_c(d, "АНОД +", x0 + 20, cy + R + 18, 30, RED_W)
        text_c(d, "КАТОД −", x1 - 40, cy + R + 18, 30, INK)


def chiller(d, x, y, on=False, t=0.0):
    d.rounded_rectangle([x, y, x + 240, y + 210], 18, fill=(225, 230, 238), outline=INK, width=5)
    d.rounded_rectangle([x + 18, y + 22, x + 140, y + 82], 10, fill=(12, 30, 26), outline=INK, width=3)
    text_c(d, "20°C" if on else "--°C", x + 79, y + 52, 34, (60, 255, 160) if on else (60, 90, 80), anchor="mm")
    for k in range(5):
        d.line([(x + 160, y + 30 + k * 14), (x + 220, y + 30 + k * 14)], fill=STEEL_D, width=5)
    d.ellipse([x + 196, y + 110, x + 220, y + 134], fill=OK if on else GRAY, outline=INK, width=3)
    text_c(d, "ЧИЛЕР", x + 120, y + 168, 34, INK, anchor="mm")
    return (x + 60, y), (x + 180, y)


def hose(d, pts, k=1.0, flow_t=None):
    p = partial(pts, k)
    if len(p) < 2:
        return
    d.line(p, fill=INK, width=20, joint="curve"); d.line(p, fill=(150, 200, 230), width=11, joint="curve")
    if flow_t is not None and k >= 1:
        for j in range(8):
            f = (flow_t * 0.6 + j / 8) % 1
            x, y = point_on(pts, f)
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=WATER_D)


def hv_psu(d, x, y):
    d.rounded_rectangle([x, y, x + 290, y + 190], 16, fill=DARK, outline=INK, width=5)
    d.polygon([(x + 50, y + 40), (x + 30, y + 100), (x + 52, y + 100), (x + 38, y + 150), (x + 82, y + 82),
               (x + 60, y + 82), (x + 74, y + 40)], fill=YEL, outline=INK)
    text_c(d, "HV", x + 175, y + 45, 56, YEL)
    text_c(d, "150 Вт", x + 175, y + 115, 40, STEEL_L)
    tp, tm = (x + 120, y), (x + 240, y)
    d.ellipse([tp[0] - 18, tp[1] - 18, tp[0] + 18, tp[1] + 18], fill=RED_W, outline=INK, width=4)
    d.ellipse([tm[0] - 18, tm[1] - 18, tm[0] + 18, tm[1] + 18], fill=BLACK_W, outline=INK, width=4)
    text_c(d, "+", tp[0], tp[1] - 2, 30, WHITE, anchor="mm"); text_c(d, "−", tm[0], tm[1] - 2, 30, WHITE, anchor="mm")
    return tp, tm


def wire(d, pts, k, col):
    p = partial(pts, k)
    if len(p) >= 2:
        d.line(p, fill=INK, width=16, joint="curve"); d.line(p, fill=col, width=9, joint="curve")


def switch(d, cx, cy, label, on, num):
    d.rounded_rectangle([cx - 150, cy - 70, cx + 150, cy + 70], 24, fill=WHITE, outline=INK, width=5)
    d.ellipse([cx - 130, cy - 40, cx - 50, cy + 40], fill=OK if on else (200, 205, 212), outline=INK, width=5)
    text_c(d, num, cx - 90, cy, 42, WHITE if on else GRAY, anchor="mm")
    text_c(d, label, cx + 40, cy, 40, INK if on else GRAY, anchor="mm")


@lru_cache(None)
def goggles_layer():
    lay = Image.new("RGBA", (440, 210), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.arc([10, 20, 430, 260], 200, 340, fill=INK, width=18); ld.arc([10, 20, 430, 260], 200, 340, fill=DARK, width=10)
    for x0 in (40, 230):
        ld.rounded_rectangle([x0, 60, x0 + 170, 180], 50, fill=(110, 200, 140), outline=INK, width=8)
        ld.arc([x0 + 25, 78, x0 + 110, 150], 200, 260, fill=WHITE, width=8)
    ld.rounded_rectangle([200, 95, 240, 125], 10, fill=DARK, outline=INK, width=5)
    return lay


def mat_tile(name, verb, fn):
    lay = Image.new("RGBA", (260, 300), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    tile_box(ld, 130, 140, 240, 270)
    fn(ld, 130, 115)
    ld.text((130, 222), name, font=F(36), fill=INK, anchor="mm")
    ld.text((130, 258), verb, font=F(26), fill=BLUE_D if verb == "ріже" else GREEN_D, anchor="mm")
    return lay


def ic_plywood(d, cx, cy):
    d.rounded_rectangle([cx - 85, cy - 55, cx + 85, cy + 55], 8, fill=WOOD, outline=INK, width=4)
    for k in (-20, 20):
        d.line([(cx - 75, cy + k), (cx + 75, cy + k + 4)], fill=WOOD_D, width=3)
    d.ellipse([cx - 32, cy - 30, cx + 2, cy + 2], fill=WHITE, outline=INK, width=3)
    d.ellipse([cx - 2, cy - 30, cx + 32, cy + 2], fill=WHITE, outline=INK, width=3)
    d.polygon([(cx - 31, cy - 10), (cx + 31, cy - 10), (cx, cy + 32)], fill=WHITE)
    d.line([(cx - 31, cy - 10), (cx, cy + 32), (cx + 31, cy - 10)], fill=INK, width=3)


def ic_acrylic(d, cx, cy):
    d.rounded_rectangle([cx - 85, cy - 55, cx + 85, cy + 55], 10, fill=(170, 220, 245), outline=INK, width=4)
    d.line([(cx - 70, cy - 40), (cx - 30, cy - 40)], fill=WHITE, width=6)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; r = 36 if i % 2 == 0 else 15
        pts.append((cx + 10 + r * math.cos(a), cy + 6 + r * math.sin(a)))
    d.polygon(pts, fill=WHITE, outline=INK)


def ic_leather(d, cx, cy):
    d.rounded_rectangle([cx - 85, cy - 55, cx + 85, cy + 55], 26, fill=(150, 90, 50), outline=INK, width=4)
    dashed(d, (cx - 66, cy - 38), (cx + 66, cy - 38), fill=(240, 210, 160), width=4, n=18)
    dashed(d, (cx - 66, cy + 38), (cx + 66, cy + 38), fill=(240, 210, 160), width=4, n=18)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(110, 60, 30), outline=INK, width=3)


def ic_stone(d, cx, cy):
    d.polygon([(cx - 85, cy - 45), (cx - 60, cy - 58), (cx + 80, cy - 52), (cx + 88, cy + 48), (cx - 80, cy + 56)],
              fill=(170, 172, 180), outline=INK)
    d.line([(cx - 85, cy - 45), (cx - 60, cy - 58), (cx + 80, cy - 52), (cx + 88, cy + 48), (cx - 80, cy + 56), (cx - 85, cy - 45)],
           fill=INK, width=4)
    d.text((cx, cy), "CNC", font=F(40), fill=(95, 98, 108), anchor="mm")


MATS = [("Фанера", "ріже", ic_plywood), ("Акрил", "ріже", ic_acrylic), ("Шкіра", "ріже", ic_leather), ("Камінь", "гравіює", ic_stone)]


@lru_cache(None)
def mat_layers():
    return [mat_tile(n, v, f) for n, v, f in MATS]


# ---------- сцени ----------
TX0, TX1 = 110, 830     # трубка в кадрі


def sc_s1(im, d, lt, t):
    l = since("s1", t)
    caption(im, ["Як підключити трубку", "і не зіпсувати?"], lt, size=58, colors=[INK, BAD])
    tc, tr, tn = at("s1", 0.38), at("s1", 0.66), at("s1", 0.84)    # тріщина, «перемотка», «Дивись!»
    slide = 800 * (1 - ease(lt / 0.4))
    shake = 7 * math.sin(l * 60) * (1 - clamp((l - tc) / 0.5)) if tc < l < tc + 0.5 else 0
    crack = ease((l - tc) / 0.25) if tc < l < tr else (1 - ease((l - tr) / 0.3) if tr <= l < tr + 0.3 else 0)
    tube(d, TX0 + slide + shake, TX1 + slide + shake, 1000, crack=crack, t=t)
    if tc < l < tr:
        badge(im, ["ERR"], l - tc, 300, 860, size=64, bg=BAD, rot=-6)
    if tr < l < tr + 0.45:                                          # «перемотка назад»
        k = (l - tr) / 0.45
        for j in range(2):
            x = 430 + j * 60 - 30 * k
            d.polygon([(x, 870), (x + 50, 840), (x + 50, 900)], fill=BLUE_D, outline=INK)
    if l > tn:
        slam(im, ("ЛАЗЕРНА", "ТРУБКА CO₂"), l - tn, cy=650)
        return "wow", JOY
    if tc < l < tr + 0.3:
        return "error", ((-1, 50), (1, 50))
    return "think", REST


def sc_s2(im, d, lt, t):
    l = since("s2", t); w = since("s2w", t)
    tg, tv, tb = at("s2", 0.40), at("s2", 0.62), at("s2", 0.86)    # «газ», «напругу», «промінь»
    glow = ease((l - tv) / 0.4) if l > tv else 0
    if w > 0:
        glow = 1.0
    beam = ease((l - tb) / 0.3) if l > tb else 0
    if w > 0:
        beam = 1.0
    cy = 800
    tube(d, TX0, TX1, cy, gas=ease((l - tg) / 0.4) if l > tg else 0, glow=glow, beam=beam, t=t)
    # розмір
    k = ease((l - 0.3) / 0.4)
    if k > 0:
        y = cy - 125; mid = (TX0 + TX1) / 2; half = (TX1 - TX0) / 2 * k
        d.line([(mid - half, y), (mid + half, y)], fill=INK, width=5)
        for sx in (-1, 1):
            ex = mid + sx * half
            d.polygon([(ex, y), (ex - sx * 20, y - 11), (ex - sx * 20, y + 11)], fill=INK)
        if k > 0.6:
            tw = d.textlength("1680 мм", font=F(46))
            d.rounded_rectangle([mid - tw / 2 - 16, y - 34, mid + tw / 2 + 16, y + 32], 14, fill=BG.getpixel((int(mid), int(y)))[:3])
            text_c(d, "1680 мм", mid, y, 46, BLUE_D, anchor="mm")
    if tv < l < tv + 0.6:
        bolt(d, TX0 + 40, cy - 90, 0, 70, int(l * 20))
        bolt(d, TX1 - 46, cy - 90, 0, 70, int(l * 20) + 3)
    if l > tg:
        lx = 150
        for i, (nm, c) in enumerate((("CO₂", (90, 90, 100)), ("N₂", (60, 140, 230)), ("He", (240, 170, 40)))):
            if l > tg + i * 0.15:
                d.ellipse([lx + i * 150, 925, lx + i * 150 + 26, 951], fill=c, outline=INK, width=2)
                text_c(d, nm, lx + i * 150 + 36, 938, 36, INK, anchor="lm")
    if l > 0.15:
        badge(im, ["130 Вт"], l - 0.15, 280, 1080, size=60, rot=-4)
    if l < tv:
        caption(im, ["Скляна трубка", "130 Вт"], lt, size=62, colors=[INK, BLUE_D])
    else:
        caption(im, ["Газ + напруга", "= промінь"], l - tv, size=62, colors=[INK, BAD])
    if w > 0:
        whisper(im, ["Я теж світюся", "від напруги."], w)
        return "love", HUSH
    return ("wow", JOY) if l > tb else ("think", POINT)


def sc_s3(im, d, lt, t):
    l = since("s3", t)
    t_ok, t_sign = at("s3", 0.62), at("s3", 0.82)
    # коробка
    pop_k = back(lt / 0.3)
    bx0, bx1, by0, by1 = 90, 870, 610, 900
    d.rounded_rectangle([bx0, by0, bx1, by1], 10, fill=CARD, outline=INK, width=5)
    d.rectangle([bx0 + 20, by0 + 20, bx1 - 20, by1 - 20], fill=(235, 215, 180), outline=CARD_D, width=4)
    d.polygon([(bx0, by0), (bx0 + 60, by0 - 70 * pop_k), (bx1 - 60, by0 - 70 * pop_k), (bx1, by0)], fill=CARD_D, outline=INK)
    tube(d, 150, 810, 760, t=t, cap=1.0)
    text_c(d, "ОБЕРЕЖНО: СКЛО", 480, 845, 30, CARD_D, anchor="mm")
    # лупа ходить уздовж
    if 0.3 < l < t_ok + 0.2:
        u = ease((l - 0.3) / max(0.3, t_ok - 0.3))
        lx, ly = lerp(220, 740, u), 760
        d.ellipse([lx - 70, ly - 70, lx + 70, ly + 70], outline=INK, width=14)
        d.ellipse([lx - 64, ly - 64, lx + 64, ly + 64], outline=STEEL, width=5)
        d.line([(lx + 50, ly + 50), (lx + 110, ly + 120)], fill=INK, width=26)
        d.line([(lx + 52, ly + 52), (lx + 108, ly + 118)], fill=(190, 70, 50), width=16)
    if l > t_ok:
        check(d, 780, 640, 46, back((l - t_ok) / 0.25))
    # накладна з підписом
    nx, ny = 150, 960
    d.rounded_rectangle([nx, ny, nx + 300, ny + 220], 10, fill=WHITE, outline=INK, width=4)
    text_c(d, "НАКЛАДНА", nx + 150, ny + 22, 28, INK)
    for k in range(3):
        d.line([(nx + 24, ny + 80 + k * 30), (nx + 276, ny + 80 + k * 30)], fill=STEEL, width=4)
    d.line([(nx + 24, ny + 190), (nx + 200, ny + 190)], fill=INK, width=3)
    if l > t_sign:
        k = ease((l - t_sign) / 0.5)
        pts = [(nx + 30 + i * 8, ny + 180 - 14 * math.sin(i * 1.1)) for i in range(int(21 * k) + 1)]
        if len(pts) > 1:
            d.line(pts, fill=BLUE_D, width=5, joint="curve")
    caption(im, ["Крок 0:", "перевір на пошті"], lt, size=62, colors=[BLUE_D, INK])
    return ("happy", POINT) if l > t_ok else ("think", POINT)


def sc_s4(im, d, lt, t):
    l = since("s4", t)
    t_on, t_dist, t_flow = at("s4", 0.12), at("s4", 0.30), at("s4", 0.62)
    cy = 590
    out_p, in_p = chiller(d, 90, 990, on=l > t_on, t=t)
    nL, nR = TX0 + 90, TX1 - 90
    h1 = [out_p, (out_p[0], 830), (nL, 830), (nL, cy + 88)]
    h2 = [(nR, cy + 88), (nR, 770), (in_p[0], 770), in_p]
    kk = ease((l - 0.1) / 0.5)
    hose(d, h1, kk, flow_t=t if l > t_on else None)
    hose(d, h2, kk, flow_t=t if l > t_on else None)
    water = ease((l - t_on) / max(0.4, t_dist - t_on + 0.6)) if l > t_on else 0
    tube(d, TX0, TX1, cy, water=water, t=t, noz_down=True)
    # правила води
    items = ((("з крана",), BAD, "✗"), (("антифриз",), BAD, "✗"), (("дистильована",), OK, "✓"))
    for i, (ln, c, m) in enumerate(items):
        st = t_dist + i * 0.3
        if l > st:
            lay = plate((ln[0] + " " + m,), 40, (c,))
            paste_scaled(im, lay, 640, 930 + i * 95, pop(l - st))
    if l > t_flow:
        badge(im, ["3–5 л/хв"], l - t_flow, 690, 470, size=54, rot=-4)
    caption(im, ["Крок 1: вода"] if l < t_dist else ["Крок 1: вода", "лише дистильована"], lt if l < t_dist else l - t_dist,
            size=60, colors=[BLUE_D] if l < t_dist else [BLUE_D, INK])
    return "happy", POINT


def sc_s5(im, d, lt, t):
    l = since("s5", t); w = since("s5w", t)
    t_plus, t_cap, t_minus = at("s5", 0.22), at("s5", 0.55), at("s5", 0.80)
    cy = 600
    tp, tm = hv_psu(d, 110, 900)
    a_pt = [tp, (tp[0], 840), (TX0 - 75, 840), (TX0 - 75, cy), (TX0 - 45, cy)]
    k_pt = [tm, (tm[0], 790), (TX1 + 35, 790), (TX1 + 35, cy + 70), (TX1 - 46, cy + 24)]
    wire(d, a_pt, ease((l - t_plus) / 0.6) if l > t_plus else 0, RED_W)
    wire(d, k_pt, ease((l - t_minus) / 0.5) if l > t_minus else 0, BLACK_W)
    hi = math.sin(math.pi * clamp((l - t_cap) / 0.8)) if l > t_cap and w < 0 else 0
    tube(d, TX0, TX1, cy, water=1.0, t=t, cap_hi=hi)
    if l > t_plus + 0.3:
        text_c(d, "АНОД +", TX0 + 45, cy + 68, 34, RED_W)
    if l > t_minus + 0.3:
        text_c(d, "КАТОД −", TX1 - 170, cy + 68, 34, INK)
    if l > t_cap and w < 0:
        text_c(d, "ковпак", TX0 + 30, cy - 110, 34, (200, 140, 20))
    if w > 0:
        if (w * 6) % 1 < 0.5:
            bolt(d, TX0 - 20, cy - 110, 40, 70, int(w * 12))
        badge(im, ["28 000 В!"], w, 640, 960, size=58, bg=YEL, fg=INK, rot=5)
        whisper(im, ["28 кіловольт.", "Я не дивлюся."], w)
        return ("sleep" if w > D("s5w") * 0.55 else "wow"), HUSH
    cap = ["Крок 2: живлення"] if l < t_plus else ["Анод «+»" + ("  ·  катод «−»" if l > t_minus else "")]
    caption(im, cap, lt if l < t_plus else (l - t_plus if l < t_minus else l - t_minus), size=58,
            colors=[BLUE_D] if l < t_plus else [INK])
    return "think", POINT


def gauge(d, cx, cy, r, val):
    for a in range(0, 180, 2):
        v = a / 180 * 100
        c = BAD if v >= 90 else (OK if v < 70 else YEL)
        a0 = math.radians(180 + a)
        x0, y0 = cx + (r - 30) * math.cos(a0), cy + (r - 30) * math.sin(a0)
        x1, y1 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        d.line([(x0, y0), (x1, y1)], fill=c, width=8)
    d.arc([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], 180, 360, fill=INK, width=6)
    for v in (0, 50, 90, 100):
        a0 = math.radians(180 + v / 100 * 180)
        text_c(d, str(v), cx + (r - 62) * math.cos(a0), cy + (r - 62) * math.sin(a0), 26, INK, anchor="mm")
    a = math.radians(180 + val / 100 * 180)
    d.line([(cx, cy), (cx + (r - 20) * math.cos(a), cy + (r - 20) * math.sin(a))], fill=INK, width=12)
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=DARK, outline=INK, width=4)


def sc_s6(im, d, lt, t):
    l = since("s6", t)
    t_gauge = at("s6", 0.50)
    base = 1080
    for i, (lab, wv, c) in enumerate((("Блок", 150, BLUE), ("Трубка", 130, STEEL))):
        x = 100 + i * 230
        k = back((l - 0.2 - i * 0.35) / 0.35) if l > 0.2 + i * 0.35 else 0
        h = wv * 3.3 * k
        if h > 4:
            d.rounded_rectangle([x, base - h, x + 150, base], 14, fill=c, outline=INK, width=5)
            text_c(d, f"{wv} Вт", x + 75, base - h - 50, 42, INK)
        text_c(d, lab, x + 75, base + 16, 36, INK)
    if l > 1.1:
        text_c(d, "≥", 290, 820, 80, BLUE_D, anchor="mm")
        check(d, 290, 520, 40, back((l - 1.1) / 0.25))
    if l > t_gauge:
        u = ease((l - t_gauge) / 0.9)
        val = 88 * u + (6 * math.sin((l - t_gauge) * 14) * math.exp(-4 * (l - t_gauge)) if u >= 1 else 0)
        gauge(d, 715, 900, 175, val)
        text_c(d, "потужність", 715, 940, 32, INK)
    cap = ["Блок потужніший", "за трубку"] if l < t_gauge else ["Лазер — не вище", "90 %"]
    caption(im, cap, lt if l < t_gauge else l - t_gauge, size=60, colors=[INK, BLUE_D] if l < t_gauge else [INK, BAD])
    return ("happy", POINT) if l < t_gauge else ("think", POINT)


def sc_s7(im, d, lt, t):
    l = since("s7", t)
    t_ch, t_las = at("s7", 0.20), at("s7", 0.78)
    cy = 640
    r = random.Random(11)
    bub = []
    for i in range(9):
        bx = TX0 + 120 + r.random() * (TX1 - TX0 - 240); by = cy + r.uniform(-24, 24)
        if l > t_ch:
            u = clamp((l - t_ch) / max(0.5, t_las - t_ch - 0.3))
            bx = lerp(bx, TX1 - 90, ease(u)); by = lerp(by, cy - 70, ease(clamp(u * 1.3 - 0.3)))
            if u >= 1:
                continue
        bub.append((bx, by, 9 + i % 3 * 3))
    glow = ease((l - t_las) / 0.3) if l > t_las else 0
    tube(d, TX0, TX1, cy, water=1.0, bubbles=bub, glow=glow, beam=glow, t=t)
    switch(d, 290, 900, "ЧИЛЕР", l > t_ch, "1")
    switch(d, 660, 900, "ЛАЗЕР", l > t_las, "2")
    if l < t_ch:
        caption(im, ["Порядок увімкнення"], lt, size=58)
    elif l < t_las:
        caption(im, ["1. Чилер —", "без бульбашок"], l - t_ch, size=60, colors=[BLUE_D, INK])
    else:
        caption(im, ["2. Потім лазер!"], l - t_las, size=64, colors=[OK])
    return ("wow", JOY) if l > t_las else ("think", POINT)


def thermometer(d, x, y0, y1, level):
    d.rounded_rectangle([x - 32, y0, x + 32, y1], 32, fill=WHITE, outline=INK, width=6)
    d.ellipse([x - 56, y1 - 40, x + 56, y1 + 72], fill=BAD, outline=INK, width=6)
    top = lerp(y1 - 10, y0 + 30, level)
    d.rectangle([x - 14, top, x + 14, y1 + 10], fill=BAD)
    for i, v in enumerate((-20, 0, 5, 20, 40)):
        yy = lerp(y1 - 10, y0 + 30, (v + 20) / 60)
        d.line([(x + 34, yy), (x + 60, yy)], fill=INK, width=4)
        text_c(d, f"{v:+d}" if v else "0", x + 70, yy, 30 if v != 5 else 38, BLUE_D if v == 5 else INK, anchor="lm")


def snowflake(d, cx, cy, r):
    for k in range(6):
        a = k * math.pi / 3
        ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
        d.line([(cx, cy), (ex, ey)], fill=(80, 160, 230), width=10)
        for s in (-1, 1):
            mx, my = cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a)
            d.line([(mx, my), (mx + r * 0.3 * math.cos(a + s * 0.8), my + r * 0.3 * math.sin(a + s * 0.8))], fill=(80, 160, 230), width=8)


def sc_s8(im, d, lt, t):
    l = since("s8", t)
    t_cross, t_life = at("s8", 0.30), at("s8", 0.62)
    lvl = (5 + 20) / 60 + 0.05 * math.sin(l * 3) * (1 - clamp(l / 2))
    thermometer(d, 220, 520, 1000, lvl)
    sx, sy = 620, 700
    snowflake(d, sx, sy, 110 * back(lt / 0.3))
    if l > t_cross:
        k = ease((l - t_cross) / 0.25)
        d.line([(sx - 120, sy - 120), (sx - 120 + 240 * k, sy - 120 + 240 * k)], fill=BAD, width=22)
        if k > 0.5:
            k2 = ease((l - t_cross - 0.12) / 0.25)
            d.line([(sx + 120, sy - 120), (sx + 120 - 240 * k2, sy - 120 + 240 * k2)], fill=BAD, width=22)
    if l > t_life:
        badge(im, ["до 10 000", "годин"], l - t_life, 600, 1010, size=56, bg=OK, rot=-4)
    if l < t_life:
        caption(im, ["Нижче +5 °C —", "не вмикати!"], lt, size=62, colors=[INK, BAD])
        return ("error", ((-1, 50), (1, 50))) if l > t_cross else ("think", POINT)
    caption(im, ["І служить довго"], l - t_life, size=62, colors=[OK])
    return "happy", JOY


def sc_s9(im, d, lt, t):
    l = since("s9", t); w = since("s9w", t)
    t_gog = at("s9", 0.62)
    pos = ((300, 590), (660, 590), (300, 885), (660, 885))
    for i, (lay, (x, y)) in enumerate(zip(mat_layers(), pos)):
        st = at("s9", 0.05 + i * 0.13)
        if l > st:
            paste_scaled(im, lay, x, y, 1.0 * back((l - st) / 0.25))
            if l < st + 0.35:
                bolt(d, x - 60, y - 140, 40, 60, int(l * 30) + i, col=(255, 90, 100), width=5, n=4)
    if l > t_gog:
        u = l - t_gog
        drop = 260 * (1 - ease(u / 0.25))
        ang = 8 * math.exp(-3 * u) * math.sin(u * 10)
        paste_scaled(im, goggles_layer(), 330, 1105 - drop, 0.66, rot=ang)
    if l < t_gog:
        caption(im, ["Ріже й гравіює"], lt, size=62)
    else:
        caption(im, ["Окуляри —", "завжди!"], l - t_gog, size=64, colors=[INK, BAD])
    if w > 0:
        whisper(im, ["Мені теж купили."], w)
        return "smile", HUSH
    return ("happy", JOY) if l > t_gog else ("wow", POINT)


SCENES = {"s1": sc_s1, "s2": sc_s2, "s3": sc_s3, "s4": sc_s4, "s5": sc_s5, "s6": sc_s6, "s7": sc_s7, "s8": sc_s8, "s9": sc_s9}


def sfx_events():
    E = []
    def e(t, name, db=0.0): E.append((round(t, 3), name, db))
    s = LS; A = lambda k, f: s[k] + at(k, f)
    e(0.05, "whoosh", -10)
    e(A("s1", 0.38), "glass_crack", -5); e(A("s1", 0.40), "err", -13)
    e(A("s1", 0.66), "whoosh", -12); e(A("s1", 0.84), "whoosh", -4)
    e(SST["s2"], "whoosh", -14); e(A("s2", 0.62), "hv_crackle", -8); e(A("s2", 0.86), "laser_zap", -10)
    for i in range(3): e(A("s2", 0.40) + i * 0.15, "pop", -18)
    e(s["s2"] + 0.15, "pop", -12)
    e(SST["s3"], "whoosh", -14); e(s["s3"] + 0.05, "tape", -14)
    e(A("s3", 0.62), "ding", -9); e(A("s3", 0.82), "tick", -14)
    e(SST["s4"], "whoosh", -14); e(A("s4", 0.12), "beep", -14); e(A("s4", 0.12) + 0.1, "water_flow", -10)
    for i in range(3): e(A("s4", 0.30) + i * 0.3, "pop", -12)
    e(A("s4", 0.62), "pop", -10)
    e(SST["s5"], "whoosh", -14); e(A("s5", 0.22), "click", -8); e(A("s5", 0.55), "pop", -12)
    e(A("s5", 0.80), "click", -8); e(s["s5w"] + 0.05, "hv_crackle", -12); e(s["s5w"] + 0.1, "pop", -12)
    e(SST["s6"], "whoosh", -14); e(s["s6"] + 0.2, "pop", -12); e(s["s6"] + 0.55, "pop", -12)
    e(s["s6"] + 1.1, "ding", -12); e(A("s6", 0.50), "tick", -12)
    e(SST["s7"], "whoosh", -14); e(A("s7", 0.20), "click", -6); e(A("s7", 0.20) + 0.05, "water_flow", -12)
    e(A("s7", 0.78), "click", -6); e(A("s7", 0.78) + 0.05, "laser_zap", -10)
    e(SST["s8"], "whoosh", -14); e(A("s8", 0.30), "err", -14); e(A("s8", 0.62), "ding", -8)
    e(SST["s9"], "whoosh", -14)
    for i in range(4): e(A("s9", 0.05 + i * 0.13), "laser_zap" if i == 0 else "pop", -12 if i == 0 else -10)
    e(A("s9", 0.62) + 0.22, "chop", -14)
    e(INFO["total"], "whoosh", -10)
    return E
