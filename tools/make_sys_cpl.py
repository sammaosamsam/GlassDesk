import os, sys
from PIL import Image
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\DesktopIconTheme")
import retheme_v5 as R
import rebuild4c as RB
import compose_icons as CI

SRC = os.path.join(os.environ["TEMP"], "cpl_raw.png")
OUT = r"C:\Users\Administrator\AppData\Local\DesktopIconTheme"
raw = Image.open(SRC).convert("RGB")
logo = RB.key_out(raw, thresh=200, sat_max=26, kill_holes=False)
logo = CI.trim(logo)

p_light = R.plate_light()
p_dark = R.plate_dark()

out_light = R.compose(p_light, logo.copy(), False)
out_dark = R.compose(p_dark, logo.copy(), True)

out_light.save(os.path.join(OUT, "png_light", "_cpl_light.png"))
out_dark.save(os.path.join(OUT, "png", "_cpl_dark.png"))
print("composed", out_light.size, out_dark.size)
