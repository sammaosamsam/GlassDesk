# -*- coding: utf-8 -*-
"""v6：底板略缩进画布，右下角投影完整不被裁切"""
import sys, random
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import compose_icons as CI
import rebuild4c as R
import plate_v5 as P5

S = 256
PAD = 8
INNER = S - PAD * 2


def make_icon(logo_path, alpha_base=216, box=0.68):
    plate = P5.plate_v5(alpha_base=alpha_base, size=INNER)
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(plate, (PAD, PAD), plate)

    logo = Image.open(logo_path).convert("RGBA")
    logo = R.key_out(logo, thresh=200)
    logo = CI.trim(logo.crop(logo.getchannel("A").getbbox()))
    b = int(S * box)
    logo.thumbnail((b, b), Image.LANCZOS)
    w, h = logo.size
    pos = (S // 2 - w // 2, S // 2 - h // 2)
    logo = ImageEnhance.Color(logo).enhance(1.14)
    logo = ImageEnhance.Brightness(logo).enhance(1.04)
    col = CI.dominant_color(logo)

    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(b * 0.58)
    gd.ellipse([S // 2 - gr, S // 2 - gr, S // 2 + gr, S // 2 + gr], fill=col + (34,))
    glow = glow.filter(ImageFilter.GaussianBlur(b * 0.30))
    canvas = Image.alpha_composite(canvas, glow)

    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((64, 76, 104, 90), pos, logo.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.paste(logo, pos, logo)
    return canvas


RAWS = [("微信", r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\ai_raw\微信.lnk.png"),
        ("Chrome", r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\ai_raw\Google Chrome.lnk.png")]

items = [(name, make_icon(path)) for name, path in RAWS]

bg = Image.new("RGB", (700, 480), (40, 60, 90))
d = ImageDraw.Draw(bg)
random.seed(7)
for i in range(26):
    x = random.randint(-60, 760)
    y = random.randint(-60, 540)
    r = random.randint(60, 190)
    c = random.choice([(46, 86, 140), (120, 72, 150), (40, 110, 120), (170, 120, 60), (70, 70, 110)])
    d.ellipse([x - r, y - r, x + r, y + r], fill=c)
bg = bg.filter(ImageFilter.GaussianBlur(28))

cw = 330
f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
d = ImageDraw.Draw(bg)
for i, (name, ic) in enumerate(items):
    x = 20 + i * cw
    bg.paste(ic, (x + 20, 24), ic)
    s = ic.resize((48, 48), Image.LANCZOS)
    bg.paste(s, (x + 20, 300), s)
    d.text((x + 20, 356), name, fill=(255, 255, 255), font=f)
bg.save(r"C:\Users\Administrator\Doubao\chats\2026-11-18\new-chat-5\样张_磨砂悬浮2.png")
print("ok", bg.size)
