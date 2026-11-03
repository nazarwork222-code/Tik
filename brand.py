"""Фірмовий фон CNCPROM / Степан — однаковий у всіх роликах. Не змінювати."""
from PIL import Image, ImageDraw

TOP = (196, 242, 220)
BOTTOM = (156, 220, 190)


def background(w=1080, h=1920):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * k) for i in range(3)))
    return im
