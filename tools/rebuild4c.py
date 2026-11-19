# -*- coding: utf-8 -*-
"""第 4 批终修：换深色主体原稿 + 泛洪抠白 + 环形内部空洞清除"""
import os, sys, urllib.request
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
from PIL import Image, ImageFilter
import compose_icons as CI

AI = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\ai_raw4"
OUT_ICO = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\dark4"
OUT_PNG = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme\png4"

JOBS = [
    ("gta5", "GTA5.png", "https://aka.doubaocdn.com/s/kAawoufdtO", True),
    ("wuxia", "天涯明月刀.png", "https://aka.doubaocdn.com/s/thwq7dAHoV", False),
    ("overwatch", "守望先锋.png", "https://aka.doubaocdn.com/s/Cz6DrNAko9", True),
    ("jx3", "剑网3.png", "https://aka.doubaocdn.com/s/IKCWpXRUO5", False),
    ("capcut", "剪映.png", "https://aka.doubaocdn.com/s/tTbjjA3Gv7", False),
    ("hearthstone", "炉石传说.png", "https://aka.doubaocdn.com/s/wqPhjIZUAJ", False),
    ("nishuihan", "逆水寒.png", "https://aka.doubaocdn.com/s/GiGjsgAKDg", True),
]


def key_out(img, thresh=186, sat_max=30, kill_holes=False):
    im = img.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = bytearray(w * h)
    near_white = bytearray(w * h)
    stack = []

    def is_bg(x, y):
        r, g, b, a = px[x, y]
        return min(r, g, b) >= thresh and (max(r, g, b) - min(r, g, b)) <= sat_max

    for y in range(h):
        for x in range(w):
            if is_bg(x, y):
                near_white[y * w + x] = 1

    for x in range(w):
        for y in (0, h - 1):
            if near_white[y * w + x]:
                stack.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if near_white[y * w + x]:
                stack.append((x, y))

    while stack:
        x, y = stack.pop()
        i = y * w + x
        if bg[i] or not near_white[i]:
            continue
        bg[i] = 1
        if x > 0: stack.append((x - 1, y))
        if x + 1 < w: stack.append((x + 1, y))
        if y > 0: stack.append((x, y - 1))
        if y + 1 < h: stack.append((x, y + 1))

    if kill_holes:
        # 找出被主体包围的整片近白区域（戒指内圈），面积超过 2% 就一起挖空
        visited = bytearray(w * h)
        min_area = int(w * h * 0.02)
        for sy in range(h):
            for sx in range(w):
                i = sy * w + sx
                if near_white[i] and not bg[i] and not visited[i]:
                    comp = []
                    st = [(sx, sy)]
                    visited[i] = 1
                    while st:
                        x, y = st.pop()
                        comp.append((x, y))
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nx, ny = x + dx, y + dy
                            ni = ny * w + nx
                            if 0 <= nx < w and 0 <= ny < h and near_white[ni] and not bg[ni] and not visited[ni]:
                                visited[ni] = 1
                                st.append((nx, ny))
                    if len(comp) >= min_area:
                        for x, y in comp:
                            bg[y * w + x] = 1

    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    for y in range(h):
        base = y * w
        for x in range(w):
            if bg[base + x]:
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))

    out = im.copy()
    out.putalpha(mask)
    return out


def main():
    plate = CI.build_plate()
    for slug, fname, url, holes in JOBS:
        raw = os.path.join(AI, "v2_" + fname)
        if not os.path.exists(raw):
            urllib.request.urlretrieve(url, raw)
        cut = key_out(Image.open(raw), kill_holes=holes)
        bb = cut.getchannel("A").getbbox()
        if not bb:
            print("EMPTY", slug)
            continue
        cut = cut.crop(bb)
        out = CI.compose(plate, cut, full_tile=False)
        out.save(os.path.join(OUT_PNG, slug + ".png"))
        out.save(os.path.join(OUT_ICO, slug + ".ico"), format="ICO", sizes=CI.ICO_SIZES)
        print("OK", slug, cut.size)


if __name__ == "__main__":
    main()
