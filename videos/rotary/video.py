"""Ролик «Поворотна вісь для лазерного верстата RALM-SC3-D125» (CNCPROM).
Гачок: «Чашку крутиш руками під лазером, а напис виходить кривий?» Збірка: python build.py videos/rotary all
Товар: https://cncprom.ua/ua/p1224902334-povorotnaya-dlya-lazernogo.html
"""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter
from stepan import INK, WHITE
from kit import *

SLUG = "rotary"

LINES = {
 "s1":  "[curious] Чашку крутиш руками під лазером, а напис виходить кривий? [excited] Є поворотна вісь!",
 "s2":  "[calm] Бо лазер пише по площині: зверху чашки — чітко, а збоку — розмито й криво.",
 "s2w": "[whispers] А в мене ще й руки тремтять.",
 "s3":  "[calm] А це вона: патрон сто двадцять п'ять міліметрів, три кулачки — самі стають по центру.",
 "s4":  "[thoughtful] Крутить її кроковий двигун через ремінь, і деталь повертається рівно під промінь.",
 "s4w": "[whispers] Знову мій родич. Теж кроковий.",
 "s5":  "[thoughtful] Точність — дев'ять сотих міліметра. Тому напис замикається по колу без шва.",
 "s6":  "[thoughtful] Довга труба проходить крізь отвір у двадцять п'ять міліметрів. А саму вісь можна нахилити.",
 "s7":  "[excited] Кільця, ручки, келихи, вали, фланці... [confident] усе, що кругле.",
 "s8":  "[confident] Ставиш на стіл лазерного маркера — і деталь обертається на всі триста шістдесят.",
 "s8w": "[whispers] У мене від цього теж голова крутиться.",
}
ORDER = [("s1", .30), ("s2", .25), ("s2w", .35), ("s3", .30), ("s4", .25), ("s4w", .35),
         ("s5", .30), ("s6", .30), ("s7", .30), ("s8", .25), ("s8w", .40)]
SFX = {"laser_mark": ("fiber laser marking metal, soft high pitched buzzing hiss, close up", 3.0)}
MUSIC = None
TEST_POINTS = ["s1:1.5", "s1:3.8", "s2:2.2", "s2:4.6", "s2w:1.0", "s3:1.6", "s3:4.4", "s4:1.0", "s4:2.8",
               "s4w:1.2", "s5:1.2", "s5:4.6", "s6:2.2", "s6:4.8", "s7:1.5", "s7:3.6", "s8:1.2", "s8:3.6", "s8w:1.2"]

SKIN = (246, 200, 160); SKIN_D = (205, 150, 110)
BEAM = (255, 60, 90); BEAM_L = (255, 170, 190)
CER = (250, 250, 252); BAND = (200, 230, 248)

# ---------- точка роботи (вигляд з торця) ----------
WX, WY, WR = 470, 900, 175           # центр і радіус деталі
TEXT = "CNCPROM ✦ CNCPROM ✦ "        # кільцевий напис, 20 знаків → 18° на знак
DA = 2 * math.pi / len(TEXT)


@lru_cache(None)
def glyph(ch, size=50, col=BLUE_D, blur=0):
    lay = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((lay.width / 2, lay.height / 2), ch, font=F(size), fill=col, anchor="mm")
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return lay


@lru_cache(None)
def mug_layer(handle=True):
    """чашка з торця: керамічний обідок, синя смуга під напис, отвір, ручка праворуч"""
    S = 2 * WR + 180
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    c = S / 2
    if handle:
        hx = c + WR + 18
        ld.rounded_rectangle([hx - 40, c - 70, hx + 70, c + 70], 50, fill=CER, outline=INK, width=6)
        ld.rounded_rectangle([hx - 20, c - 34, hx + 34, c + 34], 30, fill=(0, 0, 0, 0), outline=INK, width=5)
    ld.ellipse([c - WR, c - WR, c + WR, c + WR], fill=CER, outline=INK, width=6)
    ld.ellipse([c - WR * .93, c - WR * .93, c + WR * .93, c + WR * .93], fill=BAND)
    ld.ellipse([c - WR * .62, c - WR * .62, c + WR * .62, c + WR * .62], fill=CER, outline=INK, width=4)
    ld.ellipse([c - WR * .54, c - WR * .54, c + WR * .54, c + WR * .54], fill=(92, 60, 40), outline=INK, width=3)
    ld.ellipse([c - WR * .4, c - WR * .44, c - WR * .05, c - WR * .2], fill=(130, 92, 66))
    return lay


def ring_text(im, rot, upto, jitter=None, blur_fn=None, col_fn=None, cx=WX, cy=WY):
    """кільцевий напис: знак i має кут i*DA на деталі; деталь повернута на rot (проти годинникової)"""
    rr = WR * .775
    for i, ch in enumerate(TEXT):
        if i >= upto:
            break
        if ch == " ":
            continue
        a = i * DA - rot
        dr = da = 0
        if jitter:
            dr, da = jitter[i]
        x = cx + (rr + dr) * math.sin(a + da); y = cy - (rr + dr) * math.cos(a + da)
        blur = blur_fn(a) if blur_fn else 0
        col = col_fn(a) if col_fn else BLUE_D
        paste_scaled(im, glyph(ch, 46, col, blur), x, y, 1.0, rot=-math.degrees(a + da))


def laser_head(d, x, ytip, on=False, t=0.0, label=False, hit_y=None):
    """головка лазерного маркера; ytip — кінчик лінзи; on — промінь до hit_y"""
    d.rectangle([x - 22, ytip - 205, x + 22, ytip - 150], fill=STEEL_D, outline=INK, width=4)
    d.rounded_rectangle([x - 110, ytip - 175, x + 110, ytip - 60], 18, fill=DARK, outline=INK, width=5)
    d.rounded_rectangle([x - 90, ytip - 160, x - 30, ytip - 135], 6, fill=(255, 80, 80) if on and int(t * 6) % 2 else (90, 30, 30))
    d.polygon([(x - 50, ytip - 60), (x + 50, ytip - 60), (x + 26, ytip), (x - 26, ytip)], fill=STEEL, outline=INK)
    d.rectangle([x - 18, ytip - 8, x + 18, ytip + 4], fill=INK)
    if label:
        text_c(d, "ЛАЗЕР", x + 30, ytip - 118, 30, YEL, anchor="mm")
    if on and hit_y is not None:
        d.line([(x, ytip + 4), (x, hit_y)], fill=BEAM_L, width=16)
        d.line([(x, ytip + 4), (x, hit_y)], fill=BEAM, width=6)
        r = 16 + 6 * math.sin(t * 50)
        for k in range(8):
            a = k * math.pi / 4 + t * 7
            d.line([(x, hit_y), (x + r * math.cos(a), hit_y + r * math.sin(a))], fill=(255, 230, 120), width=4)
        d.ellipse([x - 9, hit_y - 9, x + 9, hit_y + 9], fill=WHITE, outline=BEAM, width=3)


def hand(d, x, y, s=1.0):
    d.rounded_rectangle([x - 10 * s, y - 40 * s, x + 120 * s, y + 46 * s], int(36 * s), fill=SKIN, outline=INK, width=5)
    for k in range(3):
        fy = y - 40 * s + k * 28 * s
        d.rounded_rectangle([x - 40 * s, fy, x + 30 * s, fy + 26 * s], int(13 * s), fill=SKIN, outline=INK, width=4)
    d.rectangle([x + 118 * s, y - 34 * s, x + 220 * s, y + 40 * s], fill=(70, 110, 170), outline=INK, width=5)


# ---------- поворотна вісь збоку (шар) ----------
LW, LH = 840, 600


def rotary_layer(spin=0.0, window=False, work="mug", tube_x=None, belt=0.0):
    """вигляд збоку. локально: вісь y=300, плита y 520–560, корпус x 150–360, патрон x 360–430"""
    lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    AY = 300
    # плита
    d.rounded_rectangle([110, 520, 640, 562], 10, fill=STEEL_D, outline=INK, width=5)
    for bx in (140, 610):
        d.ellipse([bx - 9, 532, bx + 9, 550], fill=DARK)
    # двигун ззаду
    d.rounded_rectangle([20, 380, 170, 512], 12, fill=DARK, outline=INK, width=5)
    for k in range(4):
        d.line([(34, 400 + k * 28), (156, 400 + k * 28)], fill=(75, 82, 96), width=5)
    text_c(d, "60HS88", 95, 488, 22, STEEL_L, anchor="mm")
    d.line([(20, 470), (-10, 520)], fill=INK, width=8)
    # корпус
    d.rounded_rectangle([150, 150, 362, 520], 22, fill=STEEL, outline=INK, width=6)
    d.rectangle([168, 500, 344, 520], fill=STEEL_D)
    if window:
        d.rounded_rectangle([170, 170, 342, 500], 16, fill=(16, 42, 72), outline=(120, 200, 255), width=4)
        bc, br, sc_, sr = (256, AY), 72, (256, 440), 29
        # ремінь: дві дотичні + дуги
        d.line([(bc[0] - br, AY), (sc_[0] - sr, sc_[1])], fill=(30, 30, 34), width=12)
        d.line([(bc[0] + br, AY), (sc_[0] + sr, sc_[1])], fill=(30, 30, 34), width=12)
        d.ellipse([bc[0] - br - 6, AY - br - 6, bc[0] + br + 6, AY + br + 6], outline=(30, 30, 34), width=12)
        d.ellipse([sc_[0] - sr - 6, sc_[1] - sr - 6, sc_[0] + sr + 6, sc_[1] + sr + 6], outline=(30, 30, 34), width=12)
        for k in range(12):                                       # зуби ременя бігуть
            u = (k / 12 + belt) % 1.0
            y = lerp(AY, sc_[1], u)
            for sx, rr in ((-1, lerp(br, sr, u)), (1, lerp(br, sr, u))):
                d.line([(bc[0] + sx * (rr + 2), y), (bc[0] + sx * (rr + 10), y)], fill=YEL, width=4)
        for (cx, cy), r, sp in ((bc, br, spin), (sc_, sr, spin * 2.5)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=STEEL_L, outline=INK, width=4)
            for k in range(3):
                a = sp + k * 2 * math.pi / 3
                d.line([(cx, cy), (cx + r * .8 * math.cos(a), cy + r * .8 * math.sin(a))], fill=STEEL_D, width=6)
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=INK)
        d.text((256, 196), "1 : 2,5", font=F(26), fill=(120, 200, 255), anchor="mm")
    else:
        d.ellipse([226, 270, 286, 330], fill=STEEL_D, outline=INK, width=4)
        d.line([(180, 470), (330, 470)], fill=STEEL_D, width=4)
    # труба наскрізь (позаду патрона)
    if tube_x is not None:
        d.rounded_rectangle([tube_x, AY - 24, 800, AY + 24], 10, fill=(214, 220, 228), outline=INK, width=4)
        d.line([(tube_x + 10, AY - 10), (790, AY - 10)], fill=WHITE, width=4)
    # патрон
    d.rounded_rectangle([360, AY - 160, 432, AY + 160], 14, fill=STEEL_L, outline=INK, width=6)
    for k in range(5):                                            # блиск обертається
        yy = AY + 140 * math.cos(spin * 1.0 + k * 1.25)
        d.line([(370, yy), (422, yy)], fill=STEEL, width=6)
    jaws = []
    for k in range(3):
        a = spin + k * 2 * math.pi / 3
        jaws.append((math.sin(a), AY - 118 * math.cos(a)))
    for front, y in sorted(jaws):
        col = BLUE if front > 0 else BLUE_D
        d.rounded_rectangle([426, y - 26, 478, y + 26], 8, fill=col, outline=INK, width=4)
    if tube_x is not None:
        d.rounded_rectangle([430, AY - 24, 800, AY + 24], 10, fill=(214, 220, 228), outline=INK, width=4)
        d.line([(440, AY - 10), (790, AY - 10)], fill=WHITE, width=4)
    if work == "mug":
        hy = AY - 130 * math.cos(spin); behind = math.sin(spin) < 0
        def handle():
            d.rounded_rectangle([560, hy - 34, 680, hy + 34], 30, fill=CER, outline=INK, width=5)
        if behind: handle()
        d.rounded_rectangle([450, AY - 118, 790, AY + 118], 30, fill=CER, outline=INK, width=6)
        d.rectangle([520, AY - 112, 720, AY + 112], fill=BAND)
        for k in range(6):                                         # напис «пробігає» по боці
            yy = AY + 100 * math.sin(spin * 1.0 + k * 1.05)
            if math.cos(spin + k * 1.05) > 0:
                d.rounded_rectangle([540, yy - 7, 700, yy + 7], 6, fill=BLUE_D)
        d.ellipse([764, AY - 118, 812, AY + 118], fill=(92, 60, 40), outline=INK, width=5)
        if not behind: handle()
    return lay


def rotary_at(im, cx, cy, s=1.0, rot=0.0, **kw):
    paste_scaled(im, rotary_layer(**kw), cx, cy, s, rot=rot)


# ---------- патрон з торця ----------
def chuck_front(d, cx, cy, R, jaw_k, rot=0.0, work_r=None, off=(0, 0)):
    d.ellipse([cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10], fill=STEEL_D, outline=INK, width=6)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=STEEL_L, outline=INK, width=5)
    d.ellipse([cx - R * .82, cy - R * .82, cx + R * .82, cy + R * .82], outline=STEEL, width=8)
    d.ellipse([cx - R * .2, cy - R * .2, cx + R * .2, cy + R * .2], fill=(30, 34, 42), outline=INK, width=4)
    for k in range(3):                                            # пази
        a = rot + k * 2 * math.pi / 3
        ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
        p = lambda r, w: (cx + ux * r + px * w, cy + uy * r + py * w)
        d.polygon([p(R * .24, -20), p(R * .96, -20), p(R * .96, 20), p(R * .24, 20)], fill=STEEL_D)
    if work_r:
        wx, wy = cx + off[0], cy + off[1]
        d.ellipse([wx - work_r, wy - work_r, wx + work_r, wy + work_r], fill=(240, 196, 60), outline=INK, width=6)
        d.ellipse([wx - work_r * .62, wy - work_r * .62, wx + work_r * .62, wy + work_r * .62], fill=(150, 110, 40), outline=INK, width=4)
    tip_open, tip_closed = R * .86, (work_r or R * .3)
    for k in range(3):
        a = rot + k * 2 * math.pi / 3
        ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
        r0 = lerp(tip_open, tip_closed, jaw_k)
        p = lambda r, w: (cx + ux * r + px * w, cy + uy * r + py * w)
        d.polygon([p(r0, -30), p(r0 + 46, -30), p(r0 + 46, -40), p(r0 + 120, -40), p(r0 + 120, 40), p(r0 + 46, 40),
                   p(r0 + 46, 30), p(r0, 30)], fill=BLUE, outline=INK)
        d.line([p(r0, -30), p(r0, 30)], fill=INK, width=5)


# ---------- предмети для сцени 7 ----------
def icon(d, kind, cx, cy, t):
    if kind == "ring":
        d.ellipse([cx - 70, cy - 55, cx + 70, cy + 85], fill=(240, 196, 60), outline=INK, width=5)
        d.ellipse([cx - 48, cy - 33, cx + 48, cy + 63], fill=WHITE, outline=INK, width=4)
        d.polygon([(cx, cy - 95), (cx + 30, cy - 62), (cx, cy - 40), (cx - 30, cy - 62)], fill=(120, 210, 255), outline=INK)
        for k in range(3):
            d.line([(cx - 40 + k * 26, cy + 70), (cx - 30 + k * 26, cy + 78)], fill=BLUE_D, width=3)
    elif kind == "handle":
        d.rounded_rectangle([cx - 36, cy - 90, cx + 36, cy + 50], 26, fill=(230, 80, 60), outline=INK, width=5)
        for k in range(3):
            d.line([(cx - 14 + k * 14, cy - 70), (cx - 14 + k * 14, cy + 30)], fill=(180, 50, 40), width=4)
        d.rectangle([cx - 9, cy + 50, cx + 9, cy + 100], fill=STEEL, outline=INK, width=4)
        d.rectangle([cx - 30, cy - 20, cx + 30, cy - 6], fill=BLUE_D)
    elif kind == "glass":
        d.polygon([(cx - 60, cy - 95), (cx + 60, cy - 95), (cx + 46, cy - 10), (cx, cy + 15), (cx - 46, cy - 10)],
                  fill=(225, 240, 250), outline=INK)
        d.line([(cx - 60, cy - 95), (cx + 60, cy - 95)], fill=INK, width=5)
        d.rectangle([cx - 6, cy + 15, cx + 6, cy + 80], fill=(225, 240, 250), outline=INK, width=4)
        d.ellipse([cx - 50, cy + 74, cx + 50, cy + 96], fill=(225, 240, 250), outline=INK, width=4)
        d.line([(cx - 30, cy - 60), (cx + 30, cy - 60)], fill=BLUE_D, width=5)
    elif kind == "shaft":
        d.rounded_rectangle([cx - 95, cy - 26, cx + 95, cy + 26], 10, fill=STEEL_L, outline=INK, width=5)
        d.rounded_rectangle([cx - 40, cy - 46, cx + 40, cy + 46], 10, fill=STEEL, outline=INK, width=5)
        d.rectangle([cx + 40, cy - 26, cx + 80, cy - 14], fill=DARK)
        d.line([(cx - 30, cy - 10), (cx + 30, cy - 10)], fill=BLUE_D, width=5)
        d.line([(cx - 30, cy + 8), (cx + 14, cy + 8)], fill=BLUE_D, width=5)
    elif kind == "flange":
        d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=STEEL, outline=INK, width=5)
        d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(60, 66, 80), outline=INK, width=4)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            hx, hy = cx + 62 * math.cos(a), cy + 62 * math.sin(a)
            d.ellipse([hx - 11, hy - 11, hx + 11, hy + 11], fill=(60, 66, 80), outline=INK, width=3)
        d.arc([cx - 80, cy - 80, cx + 80, cy + 80], 200, 340, fill=BLUE_D, width=6)


# ---------- сцени ----------
_rnd = random.Random(5)
JIT = [(_rnd.uniform(-18, 18), _rnd.uniform(-0.12, 0.12)) for _ in TEXT]


def sc_s1(im, d, lt, t):
    l = since("s1", t)
    caption(im, ["Крутиш чашку руками,", "а напис кривий?"], lt, size=56, colors=[INK, BAD])
    t_name = 3.26
    if l < t_name:
        # рука смикає чашку: оберт ривками
        steps = l * 1.8
        rot = 0.45 * math.sin(math.floor(steps) * 2.1) * ease((steps % 1) / 0.3) + 0.1 * math.sin(l * 9)
        jx = 6 * math.sin(l * 31); jy = 5 * math.sin(l * 23)
        paste_scaled(im, mug_layer(), WX + jx, WY + jy, 1.0, rot=math.degrees(rot))
        upto = min(len(TEXT), int(l * 4.4) + 1)
        bad = l > 2.64
        ring_text(im, rot, upto, jitter=JIT, col_fn=(lambda a: BAD) if bad else None, cx=WX + jx, cy=WY + jy)
        a = -rot                                                    # ручка на куті rot (вправо = 90°)
        hx = WX + jx + (WR + 60) * math.cos(-rot); hy = WY + jy + (WR + 60) * math.sin(-rot)
        hand(d, hx + 20, hy, 0.9)
        laser_head(d, WX, WY - WR - 120, on=True, t=t, hit_y=WY - WR + 30)
        if bad:
            for k, (x, y) in enumerate(((240, 740), (720, 760), (300, 1110))):
                s = back((l - 2.64 - k * 0.08) / 0.2)
                if s > 0.05:
                    d.line([(x - 26 * s, y - 26 * s), (x + 26 * s, y + 26 * s)], fill=BAD, width=12)
                    d.line([(x - 26 * s, y + 26 * s), (x + 26 * s, y - 26 * s)], fill=BAD, width=12)
            return "error", ((-1, 50), (1, 50))
        return "think", REST
    u = l - t_name
    rotary_at(im, 470, 960, 0.85 * back(u / 0.4), spin=u * 3)
    slam(im, ("ПОВОРОТНА", "ВІСЬ"), u, cy=620, size=78)
    return "wow", JOY


def sc_s2(im, d, lt, t):
    l = since("s2", t); w = since("s2w", t)
    if l < 1.55:
        caption(im, ["Лазер пише", "по площині"], lt, size=64, colors=[INK, BLUE_D])
    else:
        caption(im, ["Зверху — чітко", "збоку — розмито"] if l > 3.4 else ["Зверху — чітко"], l - (3.4 if l > 3.4 else 1.55),
                size=62, colors=[OK, BAD])
    shake = 5 * math.sin(t * 40) if w > 0 else 0
    paste_scaled(im, mug_layer(), WX + shake, WY, 1.0, rot=-90)
    ytip = WY - WR - 120
    laser_head(d, WX, ytip, on=l > 0.3, t=t, hit_y=WY - WR + 30)
    # площина фокуса
    if l > 0.84:
        k = ease((l - 0.84) / 0.4)
        y = WY - WR + 30
        dashed(d, (WX - 330 * k, y), (WX + 330 * k, y), fill=BLUE_D, width=6, n=26)
        if k > 0.9:
            text_c(d, "фокус", WX + 255, y - 44, 32, BLUE_D)
    # знаки: в центрі чіткі, з боків розмиті
    def blur_fn(a):
        return 0 if l < 3.4 else int(min(9, abs(math.sin(a)) * 14))
    def col_fn(a):
        return BAD if l > 3.4 and abs(math.sin(a)) > 0.45 else BLUE_D
    if l > 1.62:
        n = 0 if l < 1.62 else (7 if l < 3.4 else len(TEXT))
        rot = 3 * DA                                                    # «CNC» у центрі зверху
        if l < 3.4:
            ring_text(im, rot, n)
        else:
            ring_text(im, rot - 0.0, len(TEXT), blur_fn=blur_fn, col_fn=col_fn)
    if l > 3.6:                                                          # розбіжні промені вбік
        for sx in (-1, 1):
            k = ease((l - 3.6) / 0.4)
            ex = WX + sx * WR * .95 * k; ey = WY - 10
            d.line([(WX, ytip + 4), (ex, ey)], fill=BEAM_L, width=8)
            r = 30 * k
            d.ellipse([ex - r, ey - r * .6, ex + r, ey + r * .6], outline=BAD, width=5)
    if w > 0:
        whisper(im, ["А в мене ще й", "руки тремтять."], w)
        return "smile", HUSH
    return ("error", POINT) if l > 3.4 else ("think", POINT)


def sc_s3(im, d, lt, t):
    l = since("s3", t)
    if l < 2.75:
        caption(im, ["Поворотна вісь", "RALM-SC3-D125"] if l < 0.82 else ["Патрон Ø125 мм"], l - (0.82 if l > 0.82 else 0),
                size=60, colors=[INK, BLUE_D] if l < 0.82 else [BLUE_D])
        slide = 600 * (1 - ease(lt / 0.35))
        rotary_at(im, 470 + slide, 900, 0.95, spin=l * 1.5)
        if l > 1.2:
            badge(im, ["Ø 125 мм"], l - 1.2, 300, 600, size=60)
        return "smile", POINT if l > 0.8 else REST
    u = l - 2.75
    caption(im, ["3 кулачки —", "самі по центру"], u, size=62, colors=[INK, BLUE_D])
    k = ease((l - 3.5) / 0.8)
    off = (lerp(70, 0, k), lerp(-55, 0, k))
    chuck_front(d, WX, WY, 260 * pop(u, 0.3), k, rot=0.0, work_r=105, off=off)
    if l > 4.36:
        d2 = l - 4.36
        for kk in range(3):
            a = kk * 2 * math.pi / 3
            check(d, WX + 330 * math.sin(a + .6), WY - 330 * math.cos(a + .6), 32, back(d2 / 0.25))
        return "wow", JOY
    return "think", POINT


def sc_s4(im, d, lt, t):
    l = since("s4", t); w = since("s4w", t)
    if l < 1.4:
        caption(im, ["Кроковий двигун"], lt, size=64, colors=[BLUE_D])
    elif l < 2.2:
        caption(im, ["двигун → ремінь", "→ патрон"], l - 1.4, size=60, colors=[INK, BLUE_D])
    else:
        caption(im, ["Деталь —", "рівно під промінь"], l - 2.2, size=60, colors=[INK, BLUE_D])
    spin = l * 2.2
    rotary_at(im, 470, 920, 0.95, spin=spin, window=True, belt=l * 1.4)
    # кінчик чашки: локально x≈620, верх y=300-118 → екран (470-420*.95+620*.95, 920-300*.95+182*.95)
    mx = 470 + (620 - LW / 2) * .95; my = 920 + (182 - LH / 2) * .95
    if l > 2.26:
        laser_head(d, mx, my - 110, on=True, t=t, hit_y=my + 6)
    if 0.6 < l and w < 0 or w > 0:
        k = l - 0.6
        paste_scaled(im, mini_stepan_xray("happy" if w < 0 else "love", t), 205, 640, 0.62 * pop(k, 0.3))
    if l > 1.46 and w < 0:
        badge(im, ["1,8° на крок"], l - 1.46, 300, 1265, size=46, rot=-3)
    if w > 0:
        whisper(im, ["Знову мій родич.", "Теж кроковий."], w)
        return "love", HUSH
    return "think", POINT


def sc_s5(im, d, lt, t):
    l = since("s5", t)
    if l < 2.35:
        caption(im, ["Точність", "0,09 мм"], lt, size=64, colors=[INK, BLUE_D])
    else:
        caption(im, ["Напис по колу —", "без шва"], l - 2.35, size=62, colors=[INK, OK])
    # пише рівно: деталь крутиться плавно, знаки з'являються зверху
    T0, T1 = 0.2, 4.3
    p = clamp((l - T0) / (T1 - T0))
    rot = p * 2 * math.pi
    paste_scaled(im, mug_layer(), WX, WY, 1.0, rot=math.degrees(rot) - 90)
    upto = int(rot / DA + 0.5) + 1 if l > T0 else 0
    ring_text(im, rot, upto)
    laser_head(d, WX, WY - WR - 120, on=T0 < l < T1 + 0.05, t=t, hit_y=WY - WR + 30)
    # стрілка обертання
    if l < T1:
        d.arc([WX - WR - 50, WY - WR - 50, WX + WR + 50, WY + WR + 50], 200, 320, fill=BLUE_D, width=8)
        ax, ay = WX + (WR + 50) * math.cos(math.radians(200)), WY + (WR + 50) * math.sin(math.radians(200))
        d.polygon([(ax - 4, ay - 22), (ax - 22, ay + 16), (ax + 18, ay + 14)], fill=BLUE_D)
    if l > 0.6:
        paste_scaled(im, lens_layer("0,09 мм"), 760, 640, 0.5 * pop(l - 0.6, 0.3))
    if l > 4.32:
        check(d, WX, WY - WR - 40, 46, back((l - 4.32) / 0.25))
        return "happy", JOY
    return "think", POINT


def sc_s6(im, d, lt, t):
    l = since("s6", t)
    if l < 3.4:
        caption(im, ["Довга труба —", "наскрізь"], lt, size=62, colors=[INK, BLUE_D])
    else:
        caption(im, ["А вісь", "нахиляється"], l - 3.4, size=62, colors=[INK, BLUE_D])
    tube_x = lerp(-400, -60, ease((l - 0.3) / 1.6))
    tilt = 0.0
    if l > 3.6:
        tilt = 18 * math.sin(clamp((l - 3.6) / 1.4) * math.pi * 1.5) * min(1, (l - 3.6) / 0.4)
    # праву частину труби шар обрізає по x 800 — для «довгої» труби вистачає
    rotary_at(im, 470, 930, 0.92, rot=tilt, spin=l * 1.2, work=None, tube_x=tube_x)
    if l > 1.88:
        badge(im, ["отвір Ø25 мм"], l - 1.88, 330, 640, size=54)
    if l > 3.6:
        cx, cy = 470, 930
        d.arc([cx - 360, cy - 360, cx + 360, cy + 360], 320, 355, fill=BLUE_D, width=8)
        d.arc([cx - 360, cy - 360, cx + 360, cy + 360], 5, 40, fill=BLUE_D, width=8)
        for ang in (320, 40):
            ax, ay = cx + 360 * math.cos(math.radians(ang)), cy + 360 * math.sin(math.radians(ang))
            d.ellipse([ax - 12, ay - 12, ax + 12, ay + 12], fill=BLUE_D)
        if l > 4.5:
            badge(im, ["кут нахилу ↕"], l - 4.5, 300, 1230, size=46, bg=WHITE, fg=BLUE_D, rot=-3)
    return ("wow", POINT) if l > 4.5 else ("think", POINT)


ITEMS = [("ring", "кільця", 190, 650, 0.0), ("handle", "ручки", 480, 650, 0.62), ("glass", "келихи", 770, 650, 1.1),
         ("shaft", "вали", 330, 960, 1.7), ("flange", "фланці", 620, 960, 2.12)]


def sc_s7(im, d, lt, t):
    l = since("s7", t)
    if l < 2.9:
        caption(im, ["Що можна маркувати?"], lt, size=56)
    else:
        caption(im, ["Усе, що кругле!"], l - 2.9, size=70, colors=[BLUE_D])
    for kind, lab, x, y, st in ITEMS:
        if l < st:
            continue
        s = pop(l - st, 0.3)
        lay = Image.new("RGBA", (250, 280), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        tile_box(ld, 125, 140, 230, 260)
        icon(ld, kind, 125, 120, t)
        ld.text((125, 238), lab, font=F(34), fill=INK, anchor="mm")
        paste_scaled(im, lay, x, y, s)
        if l > 2.98:
            check(d, x + 95, y - 110, 26, back((l - 2.98 - ITEMS.index((kind, lab, x, y, st)) * 0.06) / 0.25))
    return ("wow", JOY) if l > 2.98 else ("happy", POINT)


def sc_s8(im, d, lt, t):
    l = since("s8", t); w = since("s8w", t)
    if l < 1.8:
        caption(im, ["На стіл", "лазерного маркера"], lt, size=60, colors=[INK, BLUE_D])
    else:
        caption(im, ["Обертає на", "всі 360°"], l - 1.8, size=64, colors=[INK, BLUE_D])
    rot = max(0.0, l - 1.84) * 2.6 + (w * 2.6 if w > 0 else 0)
    paste_scaled(im, mug_layer(), WX, WY, 1.0, rot=math.degrees(rot) - 90)
    ring_text(im, rot, len(TEXT))
    laser_head(d, WX, WY - WR - 120, on=False, t=t, label=l > 0.76)
    if l > 3.14:
        k = ease((l - 3.14) / 0.5)
        d.arc([WX - WR - 55, WY - WR - 55, WX + WR + 55, WY + WR + 55], -90, -90 + 350 * k, fill=BLUE_D, width=10)
        if k > 0.95:
            badge(im, ["360°"], l - 3.64, 760, 1120, size=72)
    if w > 0:
        whisper(im, ["У мене від цього", "голова крутиться."], w)
        return "wow", HUSH
    return ("happy", JOY) if l > 3.14 else ("smile", POINT)


SCENES = {"s1": sc_s1, "s2": sc_s2, "s3": sc_s3, "s4": sc_s4, "s5": sc_s5, "s6": sc_s6, "s7": sc_s7, "s8": sc_s8}


def sfx_events():
    E = []
    def e(t, name, db=0.0): E.append((round(t, 3), name, db))
    s = LS
    for k in range(6):
        e(s["s1"] + k / 1.8, "tick", -12)
    e(s["s1"] + 0.3, "laser_mark", -16)
    e(s["s1"] + 2.64, "err", -12)
    e(s["s1"] + 3.2, "whoosh", -4)
    e(s["s2"] + 0.3, "laser_mark", -18)
    e(s["s2"] + 0.84, "pop", -12)
    e(s["s2"] + 3.4, "err", -13)
    e(s["s3"] + 0.0, "whoosh", -8)
    e(s["s3"] + 1.2, "pop", -10)
    e(s["s3"] + 3.5, "stepper", -14)
    e(s["s3"] + 4.25, "click", -6)
    e(s["s3"] + 4.36, "ding", -10)
    e(s["s4"] + 0.2, "stepper", -13)
    e(s["s4"] + 0.6, "pop", -10)
    e(s["s4"] + 2.26, "laser_mark", -16)
    e(s["s5"] + 0.2, "stepper", -15)
    e(s["s5"] + 0.25, "laser_mark", -15)
    e(s["s5"] + 0.6, "pop", -10)
    e(s["s5"] + 4.32, "ding", -8)
    e(s["s6"] + 0.3, "whoosh", -12)
    e(s["s6"] + 1.88, "pop", -10)
    e(s["s6"] + 3.6, "stepper", -15)
    for _, _, _, _, st in ITEMS:
        e(s["s7"] + st, "pop", -9)
    e(s["s7"] + 2.98, "ding", -9)
    e(s["s8"] + 1.84, "stepper", -14)
    e(s["s8"] + 3.64, "ding", -10)
    e(INFO["total"], "whoosh", -10)
    return E
