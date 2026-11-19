# -*- coding: utf-8 -*-
"""
把原始应用图标合成到「深色磨砂圆角底板」上，输出多尺寸 .ico
风格参考：深色 squircle 底板 + 彩色前景 logo + 柔和高光/投影
"""
import os, sys, json, colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

RAW = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\raw"
PLATE_SRC = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\plate_raw.png"
OUT_PNG = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\png"
OUT_ICO = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\dark"
S = 256                    # 母版边长
RADIUS_RATIO = 0.235       # 底板圆角
LOGO_BOX = 0.52           # 前景 logo 占据的边长比例
PLATE_DARKEN = 0.86       # 底板整体压暗系数
ICO_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]


def squircle_mask(size, radius_ratio, inset=0, feather=1.6):
    ss = 4
    big = size * ss
    m = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(m)
    pad = int(inset * ss)
    d.rounded_rectangle([pad, pad, big - 1 - pad, big - 1 - pad],
                        radius=int(radius_ratio * (big - 2 * pad)),
                        fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather / 2))
    return m


def build_plate():
    """裁出底板方块并转成带透明外缘的 256 底图"""
    src = Image.open(PLATE_SRC).convert("RGBA")
    g = src.convert("L")
    # 找出亮度高于背景的部分（方块本体 + 高光边）
    th = 26
    mask = g.point(lambda v: 255 if v > th else 0)
    bbox = mask.getbbox()
    # 收紧一点，避免把外发光算进去
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    shave_x, shave_y = int(w * 0.012), int(h * 0.012)
    box = (x0 + shave_x, y0 + shave_y, x1 - shave_x, y1 - shave_y)
    plate = src.crop(box).convert("RGBA")
    plate = plate.resize((S, S), Image.LANCZOS)
    plate = ImageEnhance.Brightness(plate).enhance(PLATE_DARKEN)
    plate = ImageEnhance.Contrast(plate).enhance(1.06)
    # 透明外缘遮罩，轻微外扩让高光边保留
    m = squircle_mask(S, RADIUS_RATIO, inset=-1, feather=2.0)
    plate.putalpha(ImageChops.multiply(plate.getchannel("A"), m))
    return plate


def trim(img):
    bbox = img.getchannel("A").getbbox()
    return img.crop(bbox) if bbox else img


def dominant_color(img):
    """取前景里饱和度较高的主色，用于做柔光"""
    small = img.convert("RGBA").resize((48, 48), Image.LANCZOS)
    px = [p for p in small.getdata() if p[3] > 140]
    if not px:
        return (120, 140, 255)
    best, best_score = (120, 140, 255), -1
    buckets = {}
    for r, g, b, a in px:
        buckets.setdefault((r // 32, g // 32, b // 32), []).append((r, g, b))
    for key, vals in buckets.items():
        n = len(vals)
        if n < 8:
            continue
        ar = sum(v[0] for v in vals) / n
        ag = sum(v[1] for v in vals) / n
        ab = sum(v[2] for v in vals) / n
        hh, ss, vv = colorsys.rgb_to_hsv(ar / 255, ag / 255, ab / 255)
        score = ss * 1.6 + vv * 0.8 + (n / len(px)) * 0.9
        if score > best_score:
            best_score, best = score, (int(ar), int(ag), int(ab))
    return best


def is_full_tile(img):
    """原图是否本身就是铺满画布的色块（自带底板）"""
    a = img.getchannel("A")
    bb = a.getbbox()
    if not bb:
        return False
    w, h = img.size
    fill = (bb[2] - bb[0]) * (bb[3] - bb[1]) / float(w * h)
    # 采样内部像素是否几乎不透明
    inner = a.crop((int(w * .25), int(h * .25), int(w * .75), int(h * .75)))
    opaque = sum(1 for v in inner.getdata() if v > 200) / (inner.width * inner.height)
    return fill > 0.90 and opaque > 0.95


def shadow_layer(size, radius, alpha=95, blur=9, dy=4, spread=0.98):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    b = int(size * (1 - spread) / 2)
    d.rounded_rectangle([b, b + dy, size - b, size - b + dy], radius=radius, fill=alpha)
    return m.filter(ImageFilter.GaussianBlur(blur))


def compose(plate, logo, full_tile):
    canvas = plate.copy()
    box = int(S * LOGO_BOX)
    logo = trim(logo)
    # 统一缩放到 box 内
    logo.thumbnail((box, box), Image.LANCZOS)
    lw, lh = logo.size
    cx, cy = S // 2, S // 2
    pos = (cx - lw // 2, cy - lh // 2)

    # 前景微调：饱和度/对比，让彩色更"发光"
    if not full_tile:
        logo = ImageEnhance.Color(logo).enhance(1.18)
        logo = ImageEnhance.Brightness(logo).enhance(1.04)
    else:
        # 自带色块的原图标：把外缘圆角化，避免直角戳在底板上
        r = int(min(lw, lh) * 0.22)
        ss = 3
        m = Image.new("L", (lw * ss, lh * ss), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, lw * ss - 1, lh * ss - 1], radius=r * ss, fill=255)
        m = m.resize((lw, lh), Image.LANCZOS)
        logo.putalpha(ImageChops.multiply(logo.getchannel("A"), m))

    # 主色柔光（营造氛围）
    col = dominant_color(logo)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(box * 0.72)
    gd.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=col + (58,))
    glow = glow.filter(ImageFilter.GaussianBlur(box * 0.22))
    canvas = Image.alpha_composite(canvas, glow)

    # 投影
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), pos, logo.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    canvas = Image.alpha_composite(canvas, sh)

    canvas.paste(logo, pos, logo)
    return canvas


def main():
    os.makedirs(OUT_PNG, exist_ok=True)
    os.makedirs(OUT_ICO, exist_ok=True)
    plate = build_plate()
    plate.save(os.path.join(OUT_PNG, "_plate.png"))

    files = [f for f in sorted(os.listdir(RAW)) if f.lower().endswith(".png")]
    done = []
    for f in files:
        key = f[:-4]
        src = Image.open(os.path.join(RAW, f)).convert("RGBA")
        full = is_full_tile(src)
        out = compose(plate, src, full)
        png_path = os.path.join(OUT_PNG, key + ".png")
        out.save(png_path)
        ico_path = os.path.join(OUT_ICO, key + ".ico")
        out.save(ico_path, format="ICO", sizes=ICO_SIZES)
        done.append({"key": key, "ico": ico_path, "full_tile": full})
        print("OK", key, "fulltile" if full else "glyph")

    json.dump(done, open(os.path.join(OUT_ICO, "_list.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
