# -*- coding: utf-8 -*-
"""在 retheme_v5 的底板参数上，改为优先使用 AI 玻璃原稿（ai_raw*）重做全套"""
import os, sys, json, glob, time
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
from PIL import Image
import compose_icons as CI
import rebuild4c as R
import light_icons as LI
import retheme_v5 as V5

THEME = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme"
S = 256


def idx_prefer_ai():
    idx = {}
    dirs = sorted(glob.glob(os.path.join(THEME, "ai_raw*")), reverse=True)
    for p in dirs:
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if f.lower().endswith(".png") and not f.startswith("_"):
                idx.setdefault(f[:-4], os.path.join(p, f))
    # raw 目录（扁平原稿）仅在没有 AI 稿时兜底
    p = os.path.join(THEME, "raw")
    if os.path.isdir(p):
        for f in os.listdir(p):
            if f.lower().endswith(".png") and not f.startswith("_"):
                idx.setdefault(f[:-4], os.path.join(p, f))
    return idx


def main():
    t0 = time.time()
    idx = idx_prefer_ai()
    slugs = LI.slug_set()
    mp = LI.resolve(idx, slugs)
    # AI 原稿都是白底，必须抠图
    mp = {k: (v[0], False if "ai_raw" in v[0] else v[1]) for k, v in mp.items()}
    print("slugs", len(slugs), "resolved", len(mp))

    p_light = V5.plate_light()
    p_dark = V5.plate_dark()
    p_light.save(os.path.join(THEME, "png_light", "_plate_v6_light.png"))
    p_dark.save(os.path.join(THEME, "png", "_plate_v6_dark.png"))

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
        V5.compose(p_dark, logo, True).save(os.path.join(d_dir, slug + ".ico"),
                                            format="ICO", sizes=CI.ICO_SIZES)
        V5.compose(p_light, logo, False).save(os.path.join(THEME, "light", slug + ".ico"),
                                              format="ICO", sizes=CI.ICO_SIZES)
        done += 1

    print("icons rebuilt:", done, "missing:", len(missing), "%.0fs" % (time.time() - t0))
    print("missing list:", missing)


if __name__ == "__main__":
    main()
