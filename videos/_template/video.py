"""ШАБЛОН нового ролика. Скопіюй папку: cp -r videos/_template videos/<slug>, заміни SLUG, LINES, ORDER, сцени.
Повний приклад — videos/rolgang/video.py.

Правила компонування (див. README_PROJECT.md → СТАНДАРТ):
  титр зверху: caption(...)      — y=CAP_Y (270), ширина ≤ 840 px, ≤ 3 рядки
  ілюстрація:  зона y 430–1230, x 60–900
  Степан:      завжди праворуч унизу (kit.SX/SF/SK) — малюється автоматично; сцена лише повертає (mood, arms)
  шепіт:       whisper(...) — ліворуч від Степана, сіра пунктирна бульбашка
  щось змінюється кожні 2–3 с; події прив'язуй до слів: l = t - LS["s2"]; if l > 1.26: ...
  (час слів: build/words або на слух; після test дивись build/contact.png)
"""
import math
from PIL import Image, ImageDraw
from stepan import INK, WHITE
from kit import *

SLUG = "template"

LINES = {
    "s1": "[curious] Назва товару: питання, яке одразу каже, про що ролик? [excited] Назва товару!",
    "s2": "[thoughtful] Пояснення по кроках. Число словами: двісті кроків — повний оберт.",
    "s2w": "[whispers] Жарт убік.",
    "s3": "[confident] Фінальна репліка під тему.",
}
ORDER = [("s1", .30), ("s2", .25), ("s2w", .35), ("s3", .40)]
SFX = {}          # name -> ("english prompt", seconds) — лише якщо нема в sfx_lib/
MUSIC = None      # None = sfx_lib/music.mp3
TEST_POINTS = ["s1:0.5", "s1:3.0", "s2:1.5", "s2w:0.8", "s3:1.0"]


def sc_s1(im, d, lt, t):
    # гачок: титр з темою з першого кадру → банер з назвою товару на слові-назві
    caption(im, ["Питання про", "товар?"], lt, size=64, colors=[INK, BLUE_D])
    t_name = 2.5                                   # секунда, коли звучить назва товару
    if lt > t_name:
        slam(im, ("НАЗВА", "ТОВАРУ"), lt - t_name)
        return "wow", JOY
    return "think", REST


def sc_s2(im, d, lt, t):
    l = since("s2", t); w = since("s2w", t)
    caption(im, ["Крок за кроком"], lt)
    for i in range(5):                             # приклад: кроки з'являються по черзі
        if l > 0.3 + i * 0.4:
            k = back((l - 0.3 - i * 0.4) / 0.25)
            check(d, 140 + i * 170, 700, 50, k)
    if l > 2.0:
        badge(im, ["200 кроків", "= 1 оберт"], l - 2.0, 380, 1000)
    if w > 0:
        whisper(im, ["Жарт убік."], w)
        return "smile", HUSH
    return "happy", POINT


def sc_s3(im, d, lt, t):
    caption(im, ["Фінальна думка"], lt)
    return ("blink", REST) if 0.3 < lt < 0.7 else ("happy", JOY)


SCENES = {"s1": sc_s1, "s2": sc_s2, "s3": sc_s3}


def sfx_events():
    """(час, звук, гучність dB). Звуки: процедурні click tick beep pop err + будь-що з sfx_lib/ чи SFX."""
    E = []
    def e(t, name, db=0.0): E.append((round(t, 3), name, db))
    e(LS["s1"] + 2.5, "whoosh", -4)
    for i in range(5): e(LS["s2"] + 0.3 + i * 0.4, "pop", -12)
    e(LS["s2"] + 2.0, "ding", -9)
    e(INFO["total"], "whoosh", -10)                # перехід у фінал
    return E
