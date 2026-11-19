# -*- coding: utf-8 -*-
"""Setup.exe 入口：展开资源，然后拉起 PowerShell WinForms 界面"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import installer as core


def main():
    core.fix_console()
    if not core.extract_assets():
        ctypes_msg = "资源展开失败，exe 可能损坏"
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, ctypes_msg, "GlassDesk", 0x10)
        except Exception:
            pass
        return

    ps = os.path.join(core.TARGET, "theme_ui.ps1")
    if not os.path.exists(ps):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "缺少界面脚本 theme_ui.ps1", "GlassDesk", 0x10)
        return

    # PowerShell 5.1 只有带 BOM 才正确识别 UTF-8 中文
    raw = open(ps, "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf"):
        txt = raw.decode("utf-8", "replace")
        open(ps, "wb").write(b"\xef\xbb\xbf" + txt.encode("utf-8"))

    # 用 CREATE_NO_WINDOW 拉起 PowerShell，避免弹出黑色控制台窗口
    # 不要依赖 PATH：直接拼系统目录里的 powershell.exe，避免 [WinError 2]
    CREATE_NO_WINDOW = 0x08000000
    root = os.environ.get("SystemRoot", r"C:\Windows")
    ps_exe = os.path.join(root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    if not os.path.exists(ps_exe):
        ps_exe = os.path.join(root, "SysWOW64", "WindowsPowerShell", "v1.0", "powershell.exe")
    subprocess.run([ps_exe, "-NoProfile", "-WindowStyle", "Hidden",
                    "-ExecutionPolicy", "Bypass", "-File", ps],
                   check=False, creationflags=CREATE_NO_WINDOW)


if __name__ == "__main__":
    main()

