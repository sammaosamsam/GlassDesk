# -*- coding: utf-8 -*-
"""按用户最终选定的样张参数（底板几乎满幅 inset=4、徽标 62%、柔和投影）重做全套图标"""
import os, sys, json, glob, time
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import compose_icons as CI
import rebuild4c as R
import light_icons as LI

THEME = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme"
S = 256
INSET = 4
BAND = 15
LOGO_RATIO = 0.66          # 与样张比例一致（徽标占比接近参考图）


def vgrad(size, top, bottom):
    im = Image.new("RGB", (1, 2))
    im.putpixel((0, 0), top)
    im.putpixel((0, 1), bottom)
    return im.resize((size, size), Image.BICUBIC)


def top_fade(size, start=0.06, end=0.34):
    """阴影遮罩：顶部 0 → 34% 处满强度，保证顶部/左上完全不出现投影"""
    m = Image.new("L", (1, size), 0)
    y0, y1 = int(size * start), int(size * end)
    for y in range(size):
        v = 0 if y <= y0 else (255 if y >= y1 else int(255 * (y - y0) / max(1, y1 - y0)))
        m.putpixel((0, y), v)
    return m.resize((size, size))



def diag(size, wx, wy, power=1.15):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    for y in range(size):
        for x in range(size):
            t = 1.0 - (wx * x / size + wy * y / size)
            t = max(0.0, min(1.0, t)) ** power
            d.point((x, y), fill=int(255 * t))
    return m


def diag_radial(size, alpha):
    rad = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(rad)
    cx2, cy2, Rr = size * 1.02, size * 1.02, size * 1.02
    for y in range(size):
        for x in range(size):
            dist = ((x - cx2) ** 2 + (y - cy2) ** 2) ** 0.5
            dr.point((x, y), fill=int(255 * max(0.0, 1.0 - dist / Rr) ** 1.5))
    return rad.filter(ImageFilter.GaussianBlur(size * 0.04))


def plate_light(size=S):
    mask = CI.squircle_mask(size, CI.RADIUS_RATIO, inset=INSET, feather=1.0)
    body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    body.paste(vgrad(size, (255, 255, 255), (232, 238, 248)).convert("RGBA"), (0, 0))

    band = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(BAND)).filter(ImageFilter.GaussianBlur(2)))
    band = band.filter(ImageFilter.GaussianBlur(3.5))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0),
               ImageChops.multiply(band, diag(size, 0.50, 0.40)).point(lambda v: int(v * 0.60)))
    body.paste(Image.new("RGBA", (size, size), (138, 152, 176, 255)), (0, 0),
               ImageChops.multiply(band, diag(size, -0.50, -0.40)).point(lambda v: int(v * 0.30)))

    sheen = Image.new("L", (size, size), 0)
    ds = ImageDraw.Draw(sheen)
    ds.ellipse([-size * 0.28, int(-size * 0.60), size * 1.28, int(size * 0.34)], fill=255)
    sheen = sheen.filter(ImageFilter.GaussianBlur(size * 0.11)).point(lambda v: int(v * 48 / 255))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), sheen)

    spec = Image.new("L", (size, size), 0)
    dsp = ImageDraw.Draw(spec)
    dsp.rounded_rectangle([int(size * 0.13), int(size * 0.10), int(size * 0.87), int(size * 0.21)],
                          radius=int(size * 0.055), fill=255)
    spec = spec.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 80 / 255))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), spec)

    sh = Image.new("L", (size, size), 0)
    dsh = ImageDraw.Draw(sh)
    dsh.rounded_rectangle([int(size * 0.04), int(size * 0.74), int(size * 0.96), size + int(size * 0.25)],
                          radius=int(size * 0.2), fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.10)).point(lambda v: int(v * 22 / 255))
    body.paste(Image.new("RGBA", (size, size), (128, 142, 166, 255)), (0, 0), sh)

    body.putalpha(ImageChops.multiply(body.getchannel("A"), mask))

    osh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh_off = ImageChops.offset(mask, int(size * 0.012), int(size * 0.027)).filter(
        ImageFilter.GaussianBlur(size * 0.012))
    grown = mask.filter(ImageFilter.MaxFilter(7))  # 收边：阴影最多只比图标轮廓外扩 3px
    osh.paste(Image.new("RGBA", (size, size), (86, 100, 126, 255)), (0, 0),
              ImageChops.multiply(ImageChops.multiply(ImageChops.multiply(sh_off, grown),
                                  Image.new("L", (size, size), 96)), top_fade(size)))
    return Image.alpha_composite(osh, body)


def plate_dark(size=S):
    mask = CI.squircle_mask(size, CI.RADIUS_RATIO, inset=INSET, feather=1.0)
    body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    body.paste(vgrad(size, (52, 58, 68), (16, 19, 24)).convert("RGBA"), (0, 0))

    band = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(BAND)).filter(ImageFilter.GaussianBlur(2)))
    band = band.filter(ImageFilter.GaussianBlur(3.4))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0),
               ImageChops.multiply(band, diag(size, 0.50, 0.40)).point(lambda v: int(v * 0.62)))
    body.paste(Image.new("RGBA", (size, size), (4, 6, 9, 255)), (0, 0),
               ImageChops.multiply(band, diag(size, -0.50, -0.40)).point(lambda v: int(v * 0.55)))

    sheen = Image.new("L", (size, size), 0)
    ds = ImageDraw.Draw(sheen)
    ds.ellipse([-size * 0.28, int(-size * 0.60), size * 1.28, int(size * 0.34)], fill=255)
    sheen = sheen.filter(ImageFilter.GaussianBlur(size * 0.11)).point(lambda v: int(v * 44 / 255))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), sheen)

    spec = Image.new("L", (size, size), 0)
    dsp = ImageDraw.Draw(spec)
    dsp.rounded_rectangle([int(size * 0.14), int(size * 0.10), int(size * 0.86), int(size * 0.20)],
                          radius=int(size * 0.05), fill=255)
    spec = spec.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 66 / 255))
    body.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), spec)

    sh = Image.new("L", (size, size), 0)
    dsh = ImageDraw.Draw(sh)
    dsh.rounded_rectangle([int(size * 0.04), int(size * 0.73), int(size * 0.96), size + int(size * 0.22)],
                          radius=int(size * 0.2), fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.09)).point(lambda v: int(v * 44 / 255))
    body.paste(Image.new("RGBA", (size, size), (0, 0, 0, 255)), (0, 0), sh)

    body.putalpha(ImageChops.multiply(body.getchannel("A"), mask).point(lambda v: int(v * 238 / 255)))

    sh_off = ImageChops.offset(mask, int(size * 0.012), int(size * 0.027)).filter(
        ImageFilter.GaussianBlur(size * 0.012))
    grown = mask.filter(ImageFilter.MaxFilter(7))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (size, size), (0, 0, 0, 255)), (0, 0),
                 ImageChops.multiply(ImageChops.multiply(ImageChops.multiply(sh_off, grown),
                                     Image.new("L", (size, size), 150)), top_fade(size)))
    return Image.alpha_composite(shadow, body)


def compose(plate, logo, dark):
    canvas = plate.copy()
    plate_w = S - INSET * 2
    box = int(plate_w * LOGO_RATIO)
    logo = CI.trim(logo)
    logo.thumbnail((box, box), Image.LANCZOS)
    w, h = logo.size
    pos = (S // 2 - w // 2, S // 2 - h // 2)
    logo = ImageEnhance.Color(logo).enhance(1.14)
    logo = ImageEnhance.Brightness(logo).enhance(1.04)

    col = CI.dominant_color(logo)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(box * 0.58)
    gd.ellipse([S // 2 - gr, S // 2 - gr, S // 2 + gr, S // 2 + gr], fill=col + ((40 if dark else 36),))
    glow = glow.filter(ImageFilter.GaussianBlur(box * 0.30))
    canvas = Image.alpha_composite(canvas, glow)

    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 130) if dark else (64, 76, 104, 92), pos, logo.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.paste(logo, pos, logo)
    return canvas


def main():
    t0 = time.time()
    idx = LI.raw_index()
    slugs = LI.slug_set()
    mp = LI.resolve(idx, slugs)
    print("slugs", len(slugs), "resolved", len(mp))

    p_light = plate_light()
    p_dark = plate_dark()
    p_light.save(os.path.join(THEME, "png_light", "_plate_v5_light.png"))
    p_dark.save(os.path.join(THEME, "png", "_plate_v5_dark.png"))

    owner = {}
    for bdir in sorted(glob.glob(os.path.join(THEME, "dark*"))):
        if not os.path.isdir(bdir):
            continue
        mp_path = os.path.join(bdir, "_map.json")
        if not os.path.exists(mp_path):
            continue
        for item in json.load(open(mp_path, encoding="utf-8")):
            owner[item["slug"]] = bdir

    done, missing = 0, []
    for slug in sorted(slugs):
        if slug not in mp:
            missing.append(slug)
            continue
        path, direct = mp[slug]
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            missing.append(slug)
            continue
        if direct:
            logo = CI.trim(img)
        else:
            logo = R.key_out(img, thresh=196)
            bb = logo.getchannel("A").getbbox()
            if not bb:
                missing.append(slug)
                continue
            logo = logo.crop(bb)
        d_dir = owner.get(slug, os.path.join(THEME, "dark8"))
        out_d = compose(p_dark, logo, True)
        out_l = compose(p_light, logo, False)
        out_d.save(os.path.join(d_dir, slug + ".ico"), format="ICO", sizes=CI.ICO_SIZES)
        out_l.save(os.path.join(THEME, "light", slug + ".ico"), format="ICO", sizes=CI.ICO_SIZES)
        done += 1

    print("icons rebuilt:", done, "missing:", len(missing), "%.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
