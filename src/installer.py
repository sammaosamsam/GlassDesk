# -*- coding: utf-8 -*-
"""
DarkGlass 桌面主题 一键安装器
用法：
  Setup.exe              安装（图标 / 系统图标 / 文件夹蒙版 / 隐藏小箭头 / 壁纸）
  Setup.exe --restore    还原
  Setup.exe --arrow-only 只处理“隐藏快捷方式小箭头”
"""
import os, sys, json, subprocess, shutil, ctypes, time, tempfile

PACK_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

# 绿色版：资源优先解压到 exe 同级目录（换机器不留痕）。
# exe 所在目录不可写（例如放在只读盘/Program Files）时才回退到 %LOCALAPPDATA%。
def _work_dir():
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) \
        else os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(exe_dir, "GlassDesk_data"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "GlassDesk")):
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".__w")
            with open(probe, "w") as f:
                f.write("1")
            os.remove(probe)
            return cand
        except Exception:
            continue
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "GlassDesk")

TARGET = _work_dir()
FLAG = os.path.join(TARGET, "_admin_done.flag")


def fix_console():
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def log(msg):
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode("utf-8", "ignore").decode("utf-8", "ignore"), flush=True)


def extract_assets():
    src = os.path.join(PACK_ROOT, "assets")
    if not os.path.isdir(src):
        log("！找不到 assets 目录，exe 可能损坏")
        return False
    if os.path.isdir(TARGET):
        shutil.rmtree(TARGET, ignore_errors=True)
    shutil.copytree(src, TARGET)
    log("资源已展开到 %s" % TARGET)
    return True


def load_cfg():
    p = os.path.join(TARGET, "install_config.json")
    return json.load(open(p, encoding="utf-8"))


PS_TEMPLATE = r"""
$ErrorActionPreference = 'Continue'
$PACK = '__PACK__'
$MODE = '__MODE__'
$FLAG = '__FLAG__'
$cfg  = Get-Content (Join-Path $PACK 'install_config.json') -Raw -Encoding UTF8 | ConvertFrom-Json

function Icon-Path([string]$f) {
    return ((Join-Path (Join-Path $PACK 'icons') $f) + ',0')
}

# ---------- 快捷方式图标 ----------
$ws = New-Object -ComObject WScript.Shell
foreach ($dir in @((Join-Path $env:USERPROFILE 'Desktop'), 'C:\Users\Public\Desktop')) {
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    Get-ChildItem -LiteralPath $dir -Filter *.lnk -Force -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $sc  = $ws.CreateShortcut($_.FullName)
            $exe = [System.IO.Path]::GetFileName($sc.TargetPath)
            if ($MODE -eq 'restore') {
                $sc.IconLocation = ',0'
                $sc.Save()
            } elseif ($exe -ne '' -and ($cfg.icons.PSObject.Properties.Name -contains $exe)) {
                $sc.IconLocation = (Icon-Path $cfg.icons.$exe)
                $sc.Save()
            }
        } catch { }
    }
}

# ---------- 系统图标 ----------
$sysmap = New-Object 'System.Collections.Hashtable'
$sysmap['{20D04FE0-3AEA-1069-A2D8-08002B30309D}'] = 'sys_pc.ico'
$sysmap['{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}'] = 'sys_network.ico'
$sysmap['{645FF040-5081-101B-9F08-00AA002F954E}'] = 'sys_bin.ico'
$sysmap['{59031A47-3F72-44A7-89C5-5595FE6B30EE}'] = 'sys_user.ico'
foreach ($g in $sysmap.Keys) {
    foreach ($base in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CLSID',
                       'HKCU:\Software\Classes\CLSID')) {
        $k = Join-Path (Join-Path $base $g) 'DefaultIcon'
        try {
            if ($MODE -eq 'restore') {
                if (Test-Path $k) { Remove-Item -Path $k -Recurse -Force -ErrorAction SilentlyContinue }
            } else {
                if (-not (Test-Path $k)) { New-Item -Path $k -Force | Out-Null }
                $v = Icon-Path $sysmap[$g]
                Set-ItemProperty -Path $k -Name '(default)' -Value $v
                if ($g -eq '{645FF040-5081-101B-9F08-00AA002F954E}') {
                    Set-ItemProperty -Path $k -Name 'Empty' -Value $v
                    Set-ItemProperty -Path $k -Name 'Full'  -Value $v
                }
            }
        } catch { }
    }
}

# ---------- 管理员部分：文件夹蒙版 + 隐藏小箭头 ----------
if ($MODE -eq 'admin' -or $MODE -eq 'restore-admin') {
    $si = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons'
    if (-not (Test-Path $si)) { New-Item -Path $si -Force | Out-Null }

    foreach ($p in @('HKLM:\SOFTWARE\Classes\Directory\DefaultIcon',
                     'HKLM:\SOFTWARE\Classes\Folder\DefaultIcon')) {
        if (Test-Path $p) {
            foreach ($n in (Get-Item $p).GetValueNames()) {
                Remove-ItemProperty -Path $p -Name $n -Force -ErrorAction SilentlyContinue
            }
        }
    }

    if ($MODE -eq 'restore-admin') {
        foreach ($n in @('3', '4', '29')) {
            Remove-ItemProperty -Path $si -Name $n -Force -ErrorAction SilentlyContinue
        }
    } else {
        Set-ItemProperty -Path $si -Name '3' -Value (Icon-Path $cfg.folder_icon)
        Set-ItemProperty -Path $si -Name '4' -Value (Icon-Path $cfg.folder_icon)
        if ($cfg.remove_shortcut_arrow) {
            Set-ItemProperty -Path $si -Name '29' -Value (Icon-Path $cfg.blank_icon)
        }
    }
}

if ($MODE -eq 'admin' -or $MODE -eq 'restore-admin') {
    'ok' | Set-Content -LiteralPath $FLAG -Encoding ASCII
}
"""


def build_ps(mode):
    return (PS_TEMPLATE.replace("__PACK__", TARGET)
                         .replace("__MODE__", mode)
                         .replace("__FLAG__", FLAG))


def run_ps_file(mode, elevated=False):
    path = os.path.join(tempfile.gettempdir(), "darkglass_%s.ps1" % mode)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(build_ps(mode))
    if not elevated:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", path], capture_output=True, text=True, encoding="utf-8",
                           errors="ignore")
        if r.returncode != 0 and (r.stderr or "").strip():
            log("！PowerShell 提示：%s" % (r.stderr.strip()[:300]))
        return True

    params = '-NoProfile -ExecutionPolicy Bypass -File "%s"' % path
    if os.path.exists(FLAG):
        os.remove(FLAG)
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", params, None, 1)
    if rc <= 0:
        log("！管理员授权被取消（返回值 %s）" % rc)
        return False
    for _ in range(180):
        if os.path.exists(FLAG):
            time.sleep(0.4)
            try:
                os.remove(FLAG)
            except Exception:
                pass
            return True
        time.sleep(0.4)
    log("！等待管理员步骤超时")
    return False


def set_wallpaper(path):
    import winreg
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(k, "WallpaperStyle", 0, winreg.REG_SZ, "10")
    winreg.SetValueEx(k, "TileWallpaper", 0, winreg.REG_SZ, "0")
    winreg.SetValueEx(k, "Wallpaper", 0, winreg.REG_SZ, path)
    winreg.CloseKey(k)
    ok = ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0x01 | 0x02)
    log("壁纸已设置：%s" % os.path.basename(path))
    return ok


def _get_icon_size():
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Bags\1\Desktop", 0, winreg.KEY_READ)
        v, _ = winreg.QueryValueEx(k, "IconSize")
        winreg.CloseKey(k)
        return int(v)
    except Exception:
        return None


def _set_icon_size(size):
    import winreg
    if not size:
        return
    try:
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Bags\1\Desktop", 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(k, "IconSize", 0, winreg.REG_DWORD, size)
        winreg.CloseKey(k)
    except Exception:
        pass


def restart_explorer():
    size = _get_icon_size()
    subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
    time.sleep(1.5)
    cache = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Explorer")
    if os.path.isdir(cache):
        for f in os.listdir(cache):
            if "cache" in f.lower() and f.lower().endswith(".db"):
                try:
                    os.remove(os.path.join(cache, f))
                except Exception:
                    pass
    subprocess.Popen(["explorer.exe"])
    # 重启后 Windows 偶尔把桌面图标重置成大图标，这里把原尺寸写回
    if size:
        time.sleep(4)
        _set_icon_size(size)
    log("资源管理器已重启（图标尺寸保持 %s）" % (size or "默认"))


def main():
    fix_console()
    args = [a.lower() for a in sys.argv[1:]]
    log("=" * 46)
    log(" DarkGlass 深色玻璃桌面主题")
    log("=" * 46)

    if "--restore" in args:
        if not os.path.isdir(TARGET):
            log("！未找到已安装的主题资源，无需还原")
            return
        run_ps_file("restore")
        run_ps_file("restore-admin", elevated=True)
        restart_explorer()
        log("已还原（图标恢复为程序默认图标）")
        return

    if not extract_assets():
        return
    cfg = load_cfg()

    if "--arrow-only" in args:
        run_ps_file("admin", elevated=True)
        restart_explorer()
        log("快捷方式小箭头已隐藏")
        return

    run_ps_file("user")
    log("快捷方式与系统图标已更新")
    if not run_ps_file("admin", elevated=True):
        log("跳过文件夹蒙版（需要管理员权限）")
    else:
        log("文件夹蒙版 + 隐藏小箭头 已生效")

    wp = os.path.join(TARGET, "wallpapers", cfg.get("default_wallpaper", "wall1.png"))
    if os.path.exists(wp):
        set_wallpaper(wp)

    restart_explorer()
    log("")
    log("全部完成！  图标数：%d  壁纸：%d 张" % (len(cfg["icons"]), len(cfg["wallpapers"])))
    log("提示：新装的软件如无对应图标，会保持原图标不动。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("！出错：%s" % e)
    if len(sys.argv) <= 1:
        try:
            input("\n按回车键退出…")
        except Exception:
            pass
