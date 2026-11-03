"""Степан — кроковий двигун. Reusable drawing for sheets and animation."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

INK = (24, 22, 30)
WHITE = (255, 255, 255)
BODY = (40, 44, 54)
FIN = (70, 76, 90)
CAP = (185, 192, 205)
CAP_L = (215, 220, 230)
SCREEN = (12, 18, 22)
GREEN = (60, 255, 160)
RED = (255, 70, 80)
AMBER = (255, 190, 60)
PINK = (255, 110, 170)
CABLE = (230, 70, 70)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class Pen:
    def __init__(self, d, ox, oy, k):
        self.d, self.ox, self.oy, self.k = d, ox, oy, k

    def p(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    def pts(self, *xy):
        return [self.p(x, y) for x, y in xy]

    def box(self, x0, y0, x1, y1):
        a, b = self.p(x0, y0), self.p(x1, y1)
        return [a[0], a[1], b[0], b[1]]

    def w(self, v):
        return max(1, int(v * self.k))


def arm(pn, side, angle_deg, length=110, hand=True):
    """side -1 left, +1 right. angle from horizontal outward, positive = up."""
    sx, sy = side * 170, 470
    a = math.radians(angle_deg)
    ex, ey = sx + side * length * math.cos(a), sy - length * math.sin(a)
    mx, my = (sx + ex) / 2 + side * 10, (sy + ey) / 2 + 12
    pn.d.line(pn.pts((sx, sy), (mx, my), (ex, ey)), fill=INK, width=pn.w(22), joint="curve")
    pn.d.line(pn.pts((sx, sy), (mx, my), (ex, ey)), fill=CAP, width=pn.w(12), joint="curve")
    if hand:
        pn.d.ellipse(pn.box(ex - 30, ey - 30, ex + 30, ey + 30), fill=CAP_L, outline=INK, width=pn.w(6))
        pn.d.line(pn.pts((ex - 12, ey - 4), (ex + 12, ey - 4)), fill=FIN, width=pn.w(4))
    return ex, ey


def face(pn, mood, t=0.0):
    d = pn.d
    col = {"error": RED, "love": PINK, "think": AMBER}.get(mood, GREEN)
    L, R, Y = -55, 55, 470
    def eye_rect(x, h=60, w=52, dy=0):
        d.rounded_rectangle(pn.box(x - w / 2, Y - h / 2 + dy, x + w / 2, Y + h / 2 + dy), pn.w(14), fill=col)
    if mood == "happy":
        for x in (L, R):
            eye_rect(x)
            d.ellipse(pn.box(x - 18, Y - 22, x - 4, Y - 8), fill=WHITE)
        d.arc(pn.box(-50, 500, 50, 560), 20, 160, fill=col, width=pn.w(10))
    elif mood == "smile":  # ^^ closed happy
        for x in (L, R):
            d.line(pn.pts((x - 26, Y + 12), (x, Y - 16), (x + 26, Y + 12)), fill=col, width=pn.w(12), joint="curve")
        d.chord(pn.box(-55, 495, 55, 565), 0, 180, fill=col)
    elif mood == "wow":
        for x in (L, R):
            d.ellipse(pn.box(x - 32, Y - 36, x + 32, Y + 36), outline=col, width=pn.w(10))
            d.ellipse(pn.box(x - 10, Y - 10, x + 10, Y + 10), fill=col)
        d.ellipse(pn.box(-22, 515, 22, 565), outline=col, width=pn.w(9))
    elif mood == "error":
        for x, s in ((L, 1), (R, -1)):
            d.polygon(pn.pts((x - 28, Y - 10 - s * 12), (x + 28, Y - 10 + s * 12), (x + 28, Y + 28), (x - 28, Y + 28)), fill=col)
        d.line(pn.pts((-45, 545), (-22, 530), (0, 545), (22, 530), (45, 545)), fill=col, width=pn.w(8))
        f = ImageFont.truetype(BOLD, pn.w(26))
        d.text(pn.p(-30, 405), "ERR", font=f, fill=col)
    elif mood == "think":
        for x in (L, R):
            eye_rect(x + 14, h=44, w=40, dy=-14)
        d.line(pn.pts((-30, 540), (30, 540)), fill=col, width=pn.w(9))
        n = int(t * 3) % 4
        for i in range(3 if t == 0 else n):
            d.ellipse(pn.box(48 + i * 24, 530, 62 + i * 24, 544), fill=col)
    elif mood == "blink":
        for x in (L, R):
            d.line(pn.pts((x - 26, Y + 6), (x + 26, Y + 6)), fill=col, width=pn.w(10))
        d.arc(pn.box(-50, 500, 50, 560), 20, 160, fill=col, width=pn.w(10))
    elif mood == "sleep":
        for x in (L, R):
            d.line(pn.pts((x - 26, Y + 6), (x + 26, Y + 6)), fill=col, width=pn.w(10))
        d.ellipse(pn.box(-14, 525, 14, 550), outline=col, width=pn.w(7))
        f = ImageFont.truetype(BOLD, pn.w(34))
        d.text(pn.p(60, 395), "z", font=f, fill=col)
        d.text(pn.p(85, 365), "Z", font=ImageFont.truetype(BOLD, pn.w(44)), fill=col)
    elif mood == "love":
        for x in (L, R):
            hx, hy = x, Y + 4
            d.ellipse(pn.box(hx - 28, hy - 26, hx + 2, hy + 4), fill=col)
            d.ellipse(pn.box(hx - 2, hy - 26, hx + 28, hy + 4), fill=col)
            d.polygon(pn.pts((hx - 27, hy - 6), (hx + 27, hy - 6), (hx, hy + 30)), fill=col)
        d.arc(pn.box(-45, 505, 45, 560), 20, 160, fill=col, width=pn.w(10))


def stepan(im, cx, foot_y, k=1.0, mood="happy", arms=((-1, -30), (1, -30)), squash=0.0,
           shaft_rot=0.0, t=0.0, shadow=True, cable=True):
    """foot_y = bottom of feet. Local coordinate origin: x=0 center, y=790 at feet bottom."""
    d = ImageDraw.Draw(im)
    ox = cx
    oy = foot_y - 790 * k
    pn = Pen(d, ox, oy, k)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse(pn.box(-190, 775, 190, 805), fill=(0, 0, 0, 80))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(2, 10 * k))))
        d = ImageDraw.Draw(im)
        pn.d = d
    # squash: compress vertically above feet
    sq = 1 - squash
    pn_body = Pen(d, ox, oy + (1 - sq) * 730 * k, k)  # simple shift down
    pb = pn_body
    if cable:
        pb.d.line(pb.pts((150, 640), (215, 715), (285, 775), (340, 770)), fill=INK, width=pb.w(16), joint="curve")
        pb.d.line(pb.pts((150, 640), (215, 715), (285, 775), (340, 770)), fill=CABLE, width=pb.w(8), joint="curve")
        pb.d.rounded_rectangle(pb.box(335, 752, 375, 787), pb.w(6), fill=WHITE, outline=INK, width=pb.w(4))
    # feet (unshifted)
    for fx in (-90, 90):
        d.rounded_rectangle(pn.box(fx - 50, 730, fx + 50, 790), pn.w(20), fill=BODY, outline=INK, width=pn.w(5))
    # arms behind body
    for side, ang in arms:
        if side is not None:
            arm(pb, side, ang)
    # body
    pb.d.rounded_rectangle(pb.box(-170, 330, 170, 700), pb.w(30), fill=BODY, outline=INK, width=pb.w(6))
    for i in range(8):
        y = 360 + i * 42
        pb.d.line(pb.pts((-168, y), (168, y)), fill=FIN, width=pb.w(8))
    # shaft with flat that rotates
    pb.d.rectangle(pb.box(-18, 220, 18, 300), fill=(210, 215, 225), outline=INK, width=pb.w(5))
    fx = 14 * math.sin(shaft_rot)
    pb.d.rectangle(pb.box(fx - 5, 224, fx + 5, 296), fill=(245, 247, 252))
    pb.d.rounded_rectangle(pb.box(-180, 300, 180, 370), pb.w(22), fill=CAP, outline=INK, width=pb.w(6))
    pb.d.rounded_rectangle(pb.box(-180, 670, 180, 730), pb.w(22), fill=CAP, outline=INK, width=pb.w(6))
    for (sx, sy) in ((-150, 335), (150, 335), (-150, 700), (150, 700)):
        pb.d.ellipse(pb.box(sx - 9, sy - 9, sx + 9, sy + 9), fill=FIN)
    # screen
    pb.d.rounded_rectangle(pb.box(-130, 400, 130, 600), pb.w(26), fill=SCREEN, outline=(110, 120, 135), width=pb.w(6))
    face(pb, mood, t)
    # badge
    f = ImageFont.truetype(BOLD, pb.w(20))
    pb.d.text(pb.p(-52, 625), "CNCPROM", font=f, fill=(150, 210, 240))
    return pn
