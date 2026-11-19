# -*- coding: utf-8 -*-
"""组装可移植主题包 assets：统一按 exe 文件名建图标库 + 壁纸 + 配置"""
import os, json, shutil, re
from PIL import Image, ImageOps

THEME = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme"
PACK = r"C:\Users\Administrator\Doubao\chats\2026-11-18\new-chat-5\DesktopTheme_Portable"
ASSETS = os.path.join(PACK, "assets")
ICO_DIR = os.path.join(ASSETS, "icons")
WP_DIR = os.path.join(ASSETS, "wallpapers")

# 现有 21 个：exe -> 图标 slug（图标文件在 dark\<lnk名>.lnk.ico）
EXISTING = {
    "360se.exe":          ("360se",        "360安全浏览器.lnk.ico"),
    "Doubao.exe":         ("doubao",       "豆包.lnk.ico"),
    "短接图查看.exe":      ("duanjie",      "短接图查看.exe.lnk.ico"),
    "中飞刷机助手.exe":    ("zhongfei",     "中飞刷机助手.lnk.ico"),
    "finalshell.exe":     ("finalshell",   "FinalShell.lnk.ico"),
    "IDMan.exe":          ("idm",          "Internet Download Manager.lnk.ico"),
    "msedge.exe":         ("edge",         "Microsoft Edge.lnk.ico"),
    "selene.exe":         ("selene",       "selene.exe.lnk.ico"),
    "WorkBuddy.exe":      ("workbuddy",    "WorkBuddy.lnk.ico"),
    "wpspdf.exe":         ("wpspdf",       "WPS PDF.lnk.ico"),
    "Weixin.exe":         ("wechat",       "微信.lnk.ico"),
    "BBtools.exe":        ("bbtools",      "云助手.lnk.ico"),
    "mCloud.exe":         ("mcloud",       "中国移动云盘.lnk.ico"),
    "chrome.exe":         ("chrome",       "Google Chrome.lnk.ico"),
    "RustDesk.exe":       ("rustdesk",     "RustDesk.lnk.ico"),
    "hpqSSupply.exe":     ("hpsupplies",   "Shop for HP Supplies.lnk.ico"),
    "et.exe":             ("wps_et",       "WPS表格.lnk.ico"),
    "wps.exe":            ("wps_writer",   "WPS文字.lnk.ico"),
    "wpp.exe":            ("wps_show",     "WPS演示.lnk.ico"),
}

# 系统图标
SYS = {
    "{20D04FE0-3AEA-1069-A2D8-08002B30309D}": ("sys_pc.ico",      "sys_此电脑.ico"),
    "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}": ("sys_network.ico", "sys_网络.ico"),
    "{645FF040-5081-101B-9F08-00AA002F954E}": ("sys_bin.ico",     "sys_回收站.ico"),
    "{59031A47-3F72-44A7-89C5-5595FE6B30EE}": ("sys_user.ico",    "sys_用户文件夹.ico"),
}


def main():
    for d in (ICO_DIR, WP_DIR):
        os.makedirs(d, exist_ok=True)

    icon_map = {}

    # 1) 现有图标
    for exe, (slug, src) in EXISTING.items():
        s = os.path.join(THEME, "dark", src)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(ICO_DIR, slug + ".ico"))
            icon_map[exe] = slug + ".ico"
        else:
            print("MISS existing", src)

    # 2) 新增 20 个 + 第三批 36 个 ...
    for batch in ("dark2", "dark3", "dark4", "dark5", "dark6", "dark7", "dark8"):
        d = os.path.join(THEME, batch)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".ico"):
                shutil.copy2(os.path.join(d, f), os.path.join(ICO_DIR, f))
        mp = os.path.join(d, "_map.json")
        if os.path.exists(mp):
            for item in json.load(open(mp, encoding="utf-8")):
                for exe in item["exes"]:
                    icon_map[exe] = item["slug"] + ".ico"

    # 2b) 浅色版图标（l_<slug>.ico）
    light_map = {}
    LDIR = os.path.join(THEME, "light")
    if os.path.isdir(LDIR):
        for f in sorted(os.listdir(LDIR)):
            if not f.endswith(".ico"):
                continue
            if f in ("l_folder.ico",) or f.startswith("l_sys_"):
                shutil.copy2(os.path.join(LDIR, f), os.path.join(ICO_DIR, f))
                continue
            src_slug = f[:-4]
            dst = "l_" + src_slug + ".ico"
            shutil.copy2(os.path.join(LDIR, f), os.path.join(ICO_DIR, dst))
            light_map[src_slug] = dst
        print("light icons:", len(light_map))

    # 2c) 浅色映射按 exe 名对齐深色映射（保证深/浅都是同一批 308 条）
    exe_light = {}
    seen_light = set()
    for exe, ico in icon_map.items():
        if exe.lower() in seen_light:
            continue
        slug = ico[:-4]
        f = "l_" + slug + ".ico"
        if os.path.exists(os.path.join(ICO_DIR, f)):
            exe_light[exe] = f
            seen_light.add(exe.lower())
    light_map_exe = exe_light

    # 3) 文件夹图标
    shutil.copy2(os.path.join(THEME, "dark", "folder.ico"), os.path.join(ICO_DIR, "folder.ico"))

    # 4) 系统图标
    for guid, (slug, src) in SYS.items():
        s = os.path.join(THEME, "dark", src)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(ICO_DIR, slug))

    # 5) 壁纸：统一裁成 1920x1080，另出 2560x1440
    def natkey(p):
        import re
        s = os.path.basename(p)
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]

    wps = []
    srcs = [(os.path.join(THEME, "wallpaper_dark.png"), "wall1")]
    wdir = os.path.join(THEME, "wallpapers")
    if os.path.isdir(wdir):
        files = sorted([os.path.join(wdir, f) for f in os.listdir(wdir)
                        if f.lower().endswith(".png")], key=natkey)
        for i, p in enumerate(files):
            srcs.append((p, "wall%d" % (i + 2)))
    for path, name in srcs:
        if not os.path.exists(path):
            print("MISS wall", path)
            continue
        im = Image.open(path).convert("RGB")
        for w, h, tag in ((1920, 1080, ""), (2560, 1440, "_2k")):
            out = ImageOps.fit(im, (w, h), method=Image.LANCZOS)
            p = os.path.join(WP_DIR, name + tag + ".png")
            out.save(p)
        wps.append(name + ".png")
        print("wall", name, im.size)

    # 6) 浅色壁纸
    wps_light = []
    ldir = os.path.join(THEME, "wallpapers_light")
    if os.path.isdir(ldir):
        for i, f in enumerate(sorted([f for f in os.listdir(ldir) if f.lower().endswith(".png")], key=natkey)):
            if not f.lower().endswith(".png"):
                continue
            name = "wallL%d" % (i + 1)
            im = Image.open(os.path.join(ldir, f)).convert("RGB")
            for w, h, tag in ((1920, 1080, ""), (2560, 1440, "_2k")):
                out = ImageOps.fit(im, (w, h), method=Image.LANCZOS)
                out.save(os.path.join(WP_DIR, name + tag + ".png"))
            wps_light.append(name + ".png")
            print("wall light", name, im.size)

    # 7) 常见真实 exe 名别名（原映射表里没有这些名字，会导致快捷方式切主题时被跳过）
    ALIAS = {
        "chrome.exe": "chrome.ico", "weixin.exe": "wechat.ico", "wechat.exe": "wechat.ico",
        "doubao.exe": "doubao.ico", "msedge.exe": "edge.ico", "microsoftedge.exe": "edge.ico",
        "wps.exe": "wps_writer.ico", "et.exe": "wps_et.ico", "wpp.exe": "wps_show.ico",
        "wpspdf.exe": "wpspdf.ico", "idman.exe": "idm.ico", "bbtools.exe": "bbtools.ico",
        "mcloud.exe": "mcloud.ico", "rustdesk.exe": "rustdesk.ico", "hpqssupply.exe": "hpsupplies.ico",
        "finalshell.exe": "finalshell.ico", "workbuddy.exe": "workbuddy.ico", "selene.exe": "selene.ico",
        "360se.exe": "360chrome.ico", "360se6.exe": "360chrome.ico",
        "短接图查看.exe": "duanjie.ico", "中飞刷机助手.exe": "zhongfei.ico",
    }
    for exe, ico in ALIAS.items():
        if os.path.exists(os.path.join(ICO_DIR, ico)) and exe.lower() not in {k.lower() for k in icon_map}:
            icon_map[exe] = ico

    # 7b) 别名补齐后，按新的完整 exe 表重建浅色映射，保证深浅条数一致
    exe_light = {}
    seen_light = set()
    for exe, ico in icon_map.items():
        if exe.lower() in seen_light:
            continue
        f = "l_" + ico
        if os.path.exists(os.path.join(ICO_DIR, f)):
            exe_light[exe] = f
            seen_light.add(exe.lower())
    light_map_exe = exe_light

    # 8) 大小写去重（PowerShell 的 ConvertFrom-Json 不接受仅大小写不同的重复键）
    seen = {}
    clean = {}
    for exe, ico in icon_map.items():
        low = exe.lower()
        if low in seen:
            continue
        seen[low] = True
        clean[exe] = ico
    icon_map = clean

    # 8) 透明小图标（用于隐藏快捷方式小箭头）
    #    必须用系统那份 Blank.ico —— 用 PIL 自制的透明 ICO 在叠加层会被渲染成黑方块
    src_blank = r"C:\Windows\Blank.ico"
    dst_blank = os.path.join(ICO_DIR, "_blank.ico")
    if os.path.exists(src_blank):
        shutil.copy2(src_blank, dst_blank)
        print("blank.ico <- C:\\Windows\\Blank.ico")
    else:
        Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(dst_blank, format="ICO",
                                                        sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
        print("！未找到系统 Blank.ico，已用内置透明图标（可能显示黑方块）")

    config = {
        "version": 2,
        "theme_name": "DarkGlass",
        "icons": icon_map,
        "folder_icon": "folder.ico",
        "system_icons": {g: v[0] for g, v in SYS.items()},
        "wallpapers": wps,
        "default_wallpaper": wps[0] if wps else "wall1.png",
        "remove_shortcut_arrow": True,
        "blank_icon": "_blank.ico",
        # ---- 浅色主题 ----
        "icons_light": light_map_exe,
        "folder_icon_light": "l_folder.ico",
        "system_icons_light": {g: "l_" + v[0] for g, v in SYS.items()},
        "wallpapers_light": wps_light,
        "default_wallpaper_light": wps_light[0] if wps_light else (wps[0] if wps else "wall1.png"),
    }
    json.dump(config, open(os.path.join(ASSETS, "install_config.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("icons:", len(icon_map), "wallpapers:", len(wps))
    print("PACK:", PACK)


if __name__ == "__main__":
    main()

