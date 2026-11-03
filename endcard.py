import sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from stepan import stepan, BOLD, INK

W, H, FPS, DUR = 1080, 1920, 30, 3.0
N = int(FPS * DUR)
BLUE = (3, 167, 226)
BLUE_D = (2, 110, 160)
GREEN_D = (30, 110, 80)
STEEL = (196, 205, 216)
STEEL_D = (120, 132, 148)
STEEL_L = (230, 234, 240)
F_LAB = ImageFont.truetype(BOLD, 30)
F_URL = ImageFont.truetype(BOLD, 96)
F_SM = ImageFont.truetype(BOLD, 40)
F_B = ImageFont.truetype(BOLD, 44)
F_H = ImageFont.truetype(BOLD, 50)


def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


def back(t):
    t = max(0, min(1, t)); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ---------- static layers ----------
from brand import background
BG = background(W, H)

logo = Image.open("logo.png").convert("RGBA")
logo = logo.resize((210, 210), Image.LANCZOS)


# product icons, drawn in a 240x240 tile, centre (120,105)
def tile(draw_fn, label):
    S = 2
    t = Image.new("RGBA", (260 * S, 280 * S), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    td.rounded_rectangle([6 * S, 6 * S, 254 * S, 274 * S], 34 * S, fill=(255, 255, 255, 255), outline=INK, width=5 * S)
    draw_fn(td, S)
    tw = td.textlength(label, font=ImageFont.truetype(BOLD, 28 * S))
    td.text(((260 * S - tw) / 2, 220 * S), label, font=ImageFont.truetype(BOLD, 28 * S), fill=INK)
    return t.resize((260, 280), Image.LANCZOS)


def B(S, *v):
    return [x * S for x in v]


def mills(d, S):
    for x, top, h in ((75, 40, 160), (130, 30, 170), (185, 55, 145)):
        d.rounded_rectangle(B(S, x - 16, top, x + 16, top + h * 0.45), 5 * S, fill=STEEL, outline=INK, width=4 * S)
        fy = top + h * 0.45
        d.rectangle(B(S, x - 16, fy, x + 16, top + h), fill=STEEL_L, outline=INK, width=4 * S)
        for i in range(4):
            yy = fy + 8 + i * (h * 0.55 - 16) / 4
            d.line(B(S, x - 16, yy, x + 16, yy + 14), fill=STEEL_D, width=4 * S)
    d.rectangle(B(S, 114, 30, 146, 50), fill=BLUE)


def spindle(d, S):
    d.rounded_rectangle(B(S, 80, 30, 180, 150), 14 * S, fill=(70, 76, 90), outline=INK, width=4 * S)
    for i in range(5):
        d.line(B(S, 82, 50 + i * 20, 178, 50 + i * 20), fill=(110, 118, 135), width=5 * S)
    d.rectangle(B(S, 95, 150, 165, 172), fill=STEEL, outline=INK, width=4 * S)
    d.polygon(B(S, 108, 172, 152, 172, 140, 190, 120, 190), fill=STEEL_D, outline=INK)
    d.rectangle(B(S, 125, 190, 135, 205), fill=STEEL_L, outline=INK, width=3 * S)
    d.rounded_rectangle(B(S, 70, 22, 190, 42), 8 * S, fill=BLUE, outline=INK, width=4 * S)


def motor(d, S):
    d.rectangle(B(S, 121, 30, 139, 62), fill=STEEL_L, outline=INK, width=4 * S)
    d.rounded_rectangle(B(S, 60, 58, 200, 190), 16 * S, fill=(40, 44, 54), outline=INK, width=4 * S)
    for i in range(5):
        d.line(B(S, 62, 82 + i * 20, 198, 82 + i * 20), fill=(75, 82, 96), width=5 * S)
    d.rounded_rectangle(B(S, 55, 55, 205, 80), 10 * S, fill=STEEL, outline=INK, width=4 * S)
    d.rounded_rectangle(B(S, 55, 168, 205, 195), 10 * S, fill=STEEL, outline=INK, width=4 * S)
    d.line(B(S, 200, 150, 225, 175, 235, 205), fill=(230, 70, 70), width=6 * S)


def rail(d, S):
    d.rounded_rectangle(B(S, 20, 140, 240, 172), 6 * S, fill=STEEL, outline=INK, width=4 * S)
    for x in range(40, 240, 40):
        d.ellipse(B(S, x - 6, 150, x + 6, 162), fill=STEEL_D)
    d.rounded_rectangle(B(S, 80, 85, 180, 150), 10 * S, fill=BLUE, outline=INK, width=4 * S)
    for x in (100, 160):
        d.ellipse(B(S, x - 7, 100, x + 7, 114), fill=BLUE_D)
    d.line(B(S, 85, 135, 175, 135), fill=BLUE_D, width=4 * S)


def ballscrew(d, S):
    d.rectangle(B(S, 20, 112, 240, 138), fill=STEEL, outline=INK, width=4 * S)
    for x in range(26, 238, 12):
        d.line(B(S, x, 112, x + 8, 138), fill=STEEL_D, width=3 * S)
    d.rounded_rectangle(B(S, 105, 85, 165, 165), 10 * S, fill=(220, 175, 70), outline=INK, width=4 * S)
    d.rounded_rectangle(B(S, 90, 70, 110, 180), 6 * S, fill=(200, 155, 50), outline=INK, width=4 * S)


def collet(d, S):
    d.polygon(B(S, 85, 40, 175, 40, 160, 180, 100, 180), fill=STEEL, outline=INK)
    d.line(B(S, 85, 40, 175, 40, 160, 180, 100, 180, 85, 40), fill=INK, width=4 * S)
    for x0, x1 in ((110, 113), (130, 130), (150, 147)):
        d.line(B(S, x0, 50, x1, 150), fill=STEEL_D, width=5 * S)
    d.ellipse(B(S, 105, 25, 155, 55), fill=STEEL_L, outline=INK, width=4 * S)
    d.ellipse(B(S, 120, 33, 140, 47), fill=INK)




def driver(d, S):
    d.rounded_rectangle(B(S, 45, 60, 215, 175), 10 * S, fill=(30, 110, 60), outline=INK, width=4 * S)
    for x in range(70, 200, 22):
        d.rectangle(B(S, x, 30, x + 12, 70), fill=STEEL, outline=INK, width=2 * S)
    d.rectangle(B(S, 60, 115, 120, 160), fill=INK)
    for x in range(140, 205, 16):
        d.rectangle(B(S, x, 120, x + 10, 160), fill=(60, 150, 230), outline=INK, width=2 * S)
    d.ellipse(B(S, 70, 80, 84, 94), fill=(255, 80, 80))


def psu(d, S):
    d.rounded_rectangle(B(S, 35, 50, 225, 180), 8 * S, fill=STEEL, outline=INK, width=4 * S)
    for yy in range(65, 165, 14):
        for xx in range(55, 150, 14):
            d.ellipse(B(S, xx, yy, xx + 8, yy + 8), fill=STEEL_D)
    d.rectangle(B(S, 160, 65, 212, 165), fill=(40, 44, 54), outline=INK, width=3 * S)
    for yy in range(75, 160, 15):
        d.rectangle(B(S, 168, yy, 204, yy + 8), fill=(230, 200, 80))


def machine(d, S):
    d.rectangle(B(S, 25, 160, 235, 185), fill=(40, 44, 54), outline=INK, width=4 * S)
    d.rectangle(B(S, 45, 135, 215, 160), fill=(222, 178, 112), outline=INK, width=3 * S)
    d.rectangle(B(S, 40, 55, 62, 160), fill=BLUE, outline=INK, width=4 * S)
    d.rectangle(B(S, 198, 55, 220, 160), fill=BLUE, outline=INK, width=4 * S)
    d.rectangle(B(S, 40, 45, 220, 70), fill=BLUE_D, outline=INK, width=4 * S)
    d.rounded_rectangle(B(S, 115, 60, 150, 115), 6 * S, fill=(70, 76, 90), outline=INK, width=4 * S)
    d.rectangle(B(S, 128, 115, 137, 132), fill=STEEL_L, outline=INK, width=2 * S)


TILES = [tile(mills, "Фрези"), tile(spindle, "Шпинделі"), tile(motor, "Двигуни"),
         tile(driver, "Драйвери"), tile(rail, "Рейки"), tile(ballscrew, "ШВП"),
         tile(collet, "Цанги"), tile(psu, "Живлення"), tile(machine, "Верстати")]
TPOS = [(215 + (i % 3) * 245, 395 + (i // 3) * 232) for i in range(9)]


def paste_scaled(im, layer, cx, cy, s, alpha=1.0):
    if s <= 0.02:
        return
    l = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
    if alpha < 1:
        a = l.split()[3].point(lambda v: int(v * alpha))
        l.putalpha(a)
    im.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))


# URL button layer
URLB = Image.new("RGBA", (900, 200), (0, 0, 0, 0))
ud = ImageDraw.Draw(URLB)
ud.rounded_rectangle([10, 14, 890, 194], 60, fill=INK)
ud.rounded_rectangle([10, 4, 890, 184], 60, fill=BLUE, outline=INK, width=6)
tw = ud.textlength("cncprom.ua", font=F_URL)
ud.text(((900 - tw) / 2, 36), "cncprom.ua", font=F_URL, fill=(255, 255, 255))


def bubble_layer(lines):
    w = max(ImageDraw.Draw(URLB).textlength(l, font=F_B) for l in lines) + 70
    h = len(lines) * 58 + 44
    lay = Image.new("RGBA", (int(w) + 20, h + 90), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([6, 6, w + 6, h], 36, fill=(255, 255, 255), outline=INK, width=6)
    ld.polygon([(50, h - 4), (120, h - 4), (20, h + 70)], fill=(255, 255, 255))
    ld.line([(50, h), (20, h + 70), (120, h)], fill=INK, width=6)
    for i, l in enumerate(lines):
        ld.text((40, 28 + i * 58), l, font=F_B, fill=INK)
    return lay


BUB = bubble_layer(["Усе для твого", "верстата — тут!"])


def frame(i):
    t = i / FPS
    im = BG.copy()
    d = ImageDraw.Draw(im)
    # header: mini logo + line
    a = ease(t / 0.3)
    paste_scaled(im, logo, 460, 150, 0.5 + 0.28 * back(t / 0.4), a)
    # product tiles pop
    for k, (tl, (x, y)) in enumerate(zip(TILES, TPOS)):
        st = 0.12 + k * 0.06
        p = back((t - st) / 0.3)
        if t > st:
            paste_scaled(im, tl, x, y, p * 0.78)
    # URL button
    st = 0.85
    if t > st:
        p = back((t - st) / 0.4)
        pulse = 1 + 0.035 * math.sin((t - 1.3) * 9) if t > 1.3 else 1
        paste_scaled(im, URLB, 460, 1145, 0.8 * p * pulse)
    d = ImageDraw.Draw(im)
    if t > 0.7:
        a = ease((t - 0.7) / 0.3)
        s0 = "...і багато іншого"
        tw = d.textlength(s0, font=F_SM)
        bgc = BG.getpixel((460, 1020))[:3]
        d.text((460 - tw / 2, 1000), s0, font=F_SM, fill=tuple(int(c * a + b * (1 - a)) for c, b in zip(INK, bgc)))
    if t > 1.1:
        a = ease((t - 1.1) / 0.3)
        s = "посилання — у профілі"
        tw = d.textlength(s, font=F_SM)
        bgc = BG.getpixel((460, 1250))[:3]
        col = tuple(int(c * a + b * (1 - a)) for c, b in zip(GREEN_D, bgc))
        d.text((460 - tw / 2, 1235), s, font=F_SM, fill=col)
    # Stepan rises from bottom, points up to the button
    rise = back(t / 0.5)
    foot = 1830 + (1 - rise) * 600
    wave = 8 * math.sin(t * 10) if t > 0.6 else 0
    mood = "happy"
    if 2.0 < t < 2.12:
        mood = "blink"
    stepan(im, 270, foot, k=0.85, mood=mood, arms=((-1, -45), (1, 70 + wave)), shaft_rot=t * 10, cable=True)
    # bubble
    if t > 0.9:
        p = back((t - 0.9) / 0.35)
        paste_scaled(im, BUB, 700, 1440, 0.85 * p)
    return im.convert("RGB")


if __name__ == "__main__":
    if sys.argv[1] == "test":
        frame(N - 1).save("end_last.png")
        frame(20).save("end_mid.png")
    else:
        out = sys.argv[1]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(N):
            p.stdin.write(frame(i).tobytes())
        p.stdin.close()
        sys.exit(p.wait())
