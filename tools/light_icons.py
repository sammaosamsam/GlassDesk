# -*- coding: utf-8 -*-
"""生成「浅色背景」版本图标：浅灰白磨砂圆角底板 + 同一套玻璃徽标
   - 从各批 AI 原稿 / 原始图标重新取徽标，贴到浅色底板上
   - 文件夹图标 + 4 个系统图标用 AI 浅色版直接裁切
"""
import os, re, sys, json, glob
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import compose_icons as CI
import rebuild4c as R

THEME = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme"
OUT_ICO = os.path.join(THEME, "light")
OUT_PNG = os.path.join(THEME, "png_light")
S = 256


def build_plate_light():
    big = S * 4
    plate = Image.new("RGBA", (big, big))
    top, bot = (253, 254, 255), (203, 209, 220)
    px = plate.load()
    for y in range(big):
        t = (y / (big - 1)) ** 0.85
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(big):
            px[x, y] = c + (255,)

    # 顶部柔和高光
    hl = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(hl)
    d.rounded_rectangle([int(big * .02), int(big * .015), big - int(big * .02), int(big * .30)],
                        radius=int(big * .20), fill=64)
    hl = hl.filter(ImageFilter.GaussianBlur(big * .05))
    plate = Image.composite(Image.new("RGBA", (big, big), (255, 255, 255, 255)), plate, hl)

    # 底部轻微压暗，增强立体
    sh = Image.new("L", (big, big), 0)
    ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle([0, int(big * .55), big, big], radius=int(big * .22), fill=26)
    sh = sh.filter(ImageFilter.GaussianBlur(big * .06))
    plate = Image.composite(Image.new("RGBA", (big, big), (120, 128, 145, 255)), plate, sh)

    plate = plate.resize((S, S), Image.LANCZOS)
    m = CI.squircle_mask(S, CI.RADIUS_RATIO, inset=-1, feather=2.0)
    plate.putalpha(m)
    # 1px 亮边
    edge = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    de = ImageDraw.Draw(edge)
    de.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(CI.RADIUS_RATIO * S),
                         outline=(255, 255, 255, 230), width=1)
    plate = Image.alpha_composite(plate, edge)
    return plate


def compose_light(plate, logo, full_tile):
    canvas = plate.copy()
    logo = CI.trim(logo)
    box = int(S * CI.LOGO_BOX)
    logo.thumbnail((box, box), Image.LANCZOS)
    lw, lh = logo.size
    cx, cy = S // 2, S // 2
    pos = (cx - lw // 2, cy - lh // 2)

    if not full_tile:
        logo = ImageEnhance.Color(logo).enhance(1.24)
        logo = ImageEnhance.Contrast(logo).enhance(1.06)
    else:
        r = int(min(lw, lh) * 0.22)
        ss = 3
        m = Image.new("L", (lw * ss, lh * ss), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, lw * ss - 1, lh * ss - 1], radius=r * ss, fill=255)
        m = m.resize((lw, lh), Image.LANCZOS)
        logo.putalpha(ImageChops.multiply(logo.getchannel("A"), m))

    # 徽标下方加一层淡灰垫，避免白色部件在浅底上糊掉
    vin = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vin)
    br = int(box * 0.66)
    dv.ellipse([cx - br, cy - br, cx + br, cy + br], fill=(96, 104, 122, 44))
    vin = vin.filter(ImageFilter.GaussianBlur(box * 0.20))
    canvas = Image.alpha_composite(canvas, vin)

    # 主色柔光（比深色版更收敛）
    col = CI.dominant_color(logo)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(box * 0.68)
    gd.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=col + (30,))
    glow = glow.filter(ImageFilter.GaussianBlur(box * 0.24))
    canvas = Image.alpha_composite(canvas, glow)

    # 投影
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((20, 26, 40, 70), pos, logo.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    canvas = Image.alpha_composite(canvas, sh)

    canvas.paste(logo, pos, logo)
    return canvas


def raw_index():
    idx = {}
    import glob as _gg
    for d in ["raw"] + [os.path.basename(x) for x in sorted(_gg.glob(os.path.join(THEME, "ai_raw*")))]:
        p = os.path.join(THEME, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if f.lower().endswith(".png") and not f.startswith("_"):
                idx.setdefault(f[:-4], os.path.join(p, f))
    return idx


def slug_set():
    """以各批 _map.json 的 slug 为准，外加 pack_build.EXISTING 里的 slug"""
    s = set()
    import glob as _g
    for mp in sorted(_g.glob(os.path.join(THEME, "dark*", "_map.json"))):
        if os.path.exists(mp):
            for item in json.load(open(mp, encoding="utf-8")):
                s.add(item["slug"])
    pb = os.path.join(THEME, "pack_build.py")
    for line in open(pb, encoding="utf-8"):
        toks = re.findall(r'"([^"]+)"', line)
        if len(toks) >= 3 and toks[2].endswith("ico"):
            s.add(toks[1])
    return s


def resolve(idx, slugs):
    """扫描脚本里的 (中文名, url, slug) 三种排列，建立 slug -> 原稿路径"""
    m = {}
    # 0) 手动覆盖：这几个专题图用过「深色重彩」重生成稿
    OVERRIDE = {"notion": ("ai_raw5", "Notion深色"), "kugou": ("ai_raw5", "酷狗深色"),
                "nz": ("ai_raw5", "逆战深色"), "tencentdocs": ("ai_raw5", "腾讯文档深")}
    for slug, (d, key) in OVERRIDE.items():
        p = os.path.join(THEME, d, key + ".png")
        if os.path.exists(p) and slug in slugs:
            m[slug] = (p, False)
    # 1) pack_build 的 EXISTING：exe, slug, ico文件名
    pb = os.path.join(THEME, "pack_build.py")
    for line in open(pb, encoding="utf-8"):
        toks = re.findall(r'"([^"]+)"', line)
        if len(toks) >= 3:
            slug = toks[1]
            src = toks[2]
            if slug in slugs and src.endswith("ico"):
                key = src[:-4]
                if key in idx:
                    m[slug] = (idx[key], True)   # True = 直接使用原图（自带 alpha）
    # 2) 第 2 批：build_new_icons.py 里的 MAP（"中文.png": ("slug", [...])）
    b2 = os.path.join(THEME, "build_new_icons.py")
    if os.path.exists(b2):
        for line in open(b2, encoding="utf-8"):
            toks = re.findall(r'"([^"]+)"', line)
            if len(toks) >= 2:
                cn = toks[0][:-4] if toks[0].endswith(".png") else toks[0]
                if cn in idx and toks[1] in slugs and toks[1] not in m:
                    m[toks[1]] = (idx[cn], False)
    # 3) 各批 build 脚本
    for f in glob.glob(os.path.join(THEME, "build_new_icons*.py")):
        for line in open(f, encoding="utf-8"):
            if "aka.doubaocdn.com" not in line:
                continue
            toks = re.findall(r'"([^"]+)"', line)
            cn = next((t for t in toks if t in idx), None)
            sg = next((t for t in toks if t in slugs), None)
            if cn and sg and sg not in m:
                m[sg] = (idx[cn], False)
    return m


def build_light_set():
    os.makedirs(OUT_ICO, exist_ok=True)
    os.makedirs(OUT_PNG, exist_ok=True)
    plate = build_plate_light()
    plate.save(os.path.join(OUT_PNG, "_plate_light.png"))

    idx = raw_index()
    slugs = slug_set()
    mp = resolve(idx, slugs)

    ok, miss = 0, []
    for slug in sorted(slugs):
        if slug not in mp:
            miss.append(slug)
            continue
        path, direct = mp[slug]
        img = Image.open(path).convert("RGBA")
        if direct:
            full = CI.is_full_tile(img)
            logo = img
        else:
            logo = R.key_out(img, thresh=196)
            bb = logo.getchannel("A").getbbox()
            if not bb:
                miss.append(slug)
                continue
            logo = logo.crop(bb)
            full = False
        out = compose_light(plate, logo, full)
        out.save(os.path.join(OUT_PNG, slug + ".png"))
        out.save(os.path.join(OUT_ICO, slug + ".ico"), format="ICO", sizes=CI.ICO_SIZES)
        ok += 1

    print("light ok:", ok, "missing:", len(miss))
    if miss:
        print("MISS:", ", ".join(miss))

    # ---- 文件夹 + 系统图标（AI 浅色版直接裁切）
    AI7 = os.path.join(THEME, "ai_raw7")
    SYSJOBS = [("l_folder", "浅文件夹.png"), ("l_sys_pc", "浅此电脑.png"),
               ("l_sys_network", "浅网络.png"), ("l_sys_bin", "浅回收站.png"),
               ("l_sys_user", "浅用户.png")]
    for name, fn in SYSJOBS:
        p = os.path.join(AI7, fn)
        if not os.path.exists(p):
            print("! missing", fn)
            continue
        img = Image.open(p).convert("RGBA")
        g = img.convert("L")
        mask = g.point(lambda v: 255 if v < 244 else 0)
        bb = mask.getbbox()
        if not bb:
            print("! empty", fn)
            continue
        x0, y0, x1, y1 = bb
        w, h = x1 - x0, y1 - y0
        pad_x, pad_y = int(w * 0.015), int(h * 0.015)
        img = img.crop((x0 + pad_x, y0 + pad_y, x1 - pad_x, y1 - pad_y))
        img = img.resize((S, S), Image.LANCZOS)
        img.putalpha(ImageChops.multiply(img.getchannel("A"),
                                         CI.squircle_mask(S, CI.RADIUS_RATIO, inset=-1, feather=2.0)))
        img.save(os.path.join(OUT_PNG, name + ".png"))
        img.save(os.path.join(OUT_ICO, name + ".ico"), format="ICO", sizes=CI.ICO_SIZES)
        print("sys light ok", name)


if __name__ == "__main__":
    build_light_set()
