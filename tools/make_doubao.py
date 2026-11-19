# -*- coding: utf-8 -*-
"""豆包图标：官方 3D 头像 + 玻璃镜头质感（环形高光/柔光/内阴影），放在乳白/深色底板上"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import retheme_v5 as R5
import compose_icons as CI

S = 1024
TEMP = os.environ["TEMP"]

src = Image.open(r"C:\Users\Administrator\Doubao\chats\2026-11-18\new-chat-5\豆包原图标.png").convert("RGBA")
av = src.resize((S, S), Image.LANCZOS)
mask = av.getchannel("A")  # 官方图标本身就是圆形，直接用它的圆

base = ImageEnhance.Brightness(av).enhance(1.02)
base = ImageEnhance.Color(base).enhance(1.06)

def masked(layer):
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(layer, (0, 0), mask)
    return out

# 顶部左柔光
hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
hd = ImageDraw.Draw(hl)
hd.ellipse([int(S * 0.06), int(-S * 0.14), int(S * 0.60), int(S * 0.44)], fill=(255, 255, 255, 96))
hl = masked(hl.filter(ImageFilter.GaussianBlur(S * 0.085)))

# 小高光斑
sp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
spd = ImageDraw.Draw(sp)
spd.ellipse([int(S * 0.13), int(S * 0.08), int(S * 0.29), int(S * 0.19)], fill=(255, 255, 255, 140))
sp = masked(sp.filter(ImageFilter.GaussianBlur(S * 0.022)))

# 底部内侧阴影
ish = Image.new("RGBA", (S, S), (0, 0, 0, 0))
isd = ImageDraw.Draw(ish)
isd.arc([0, 0, S, S], start=95, end=265, fill=(8, 18, 38, 105), width=int(S * 0.085))
ish = masked(ish.filter(ImageFilter.GaussianBlur(S * 0.05)))

# 环形高光：整圈细亮线 + 左上角更亮
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring)
w1 = max(3, int(S * 0.012))
rd.ellipse([w1 // 2, w1 // 2, S - w1 // 2, S - w1 // 2], outline=(255, 255, 255, 95), width=w1)
rd.arc([w1 // 2, w1 // 2, S - w1 // 2, S - w1 // 2], start=155, end=25, fill=(255, 255, 255, 215), width=w1)
ring = masked(ring.filter(ImageFilter.GaussianBlur(S * 0.006)))

lens = base.copy()
for layer in (ish, hl, sp, ring):
    lens = Image.alpha_composite(lens, layer)
lens = masked(lens)

# 外圈补 12% 透明，让镜头在底板上不顶满
m = S // 8
canvas = Image.new("RGBA", (S + m * 2, S + m * 2), (0, 0, 0, 0))
canvas.paste(lens, (m, m), lens)

p_dark = Image.open(os.path.join("png", "_plate_v6_dark.png")).convert("RGBA")
p_light = Image.open(os.path.join("png_light", "_plate_v6_light.png")).convert("RGBA")
d = R5.compose(p_dark, canvas, True)
l = R5.compose(p_light, canvas, False)

OUT = r"C:\Users\Administrator\Doubao\chats\2026-11-18\new-chat-5\DesktopTheme_Portable\assets\icons"
d.save(os.path.join(OUT, "doubao.ico"), format="ICO", sizes=CI.ICO_SIZES)
l.save(os.path.join(OUT, "l_doubao.ico"), format="ICO", sizes=CI.ICO_SIZES)
d.save(os.path.join(TEMP, "doubao_dark.png"))
l.save(os.path.join(TEMP, "doubao_light.png"))

pv = Image.new("RGBA", (512 * 2 + 24, 512), (255, 255, 255, 0))
pv.paste(d.resize((512, 512), Image.LANCZOS), (0, 0))
pv.paste(l.resize((512, 512), Image.LANCZOS), (536, 0))
pv.save(r"C:\Users\Administrator\Doubao\chats\2026-11-18\new-chat-5\样张_豆包玻璃.png")
print("ok")
