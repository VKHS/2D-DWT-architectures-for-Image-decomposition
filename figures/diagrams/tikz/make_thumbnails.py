"""Thumbnails embedded in separable_2d.tex (Cameraman, CC0, via scikit-image)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "python"))
import figstyle as fs  # noqa: E402
from dwt import lift  # noqa: E402

out = Path(__file__).resolve().parent / "img"
out.mkdir(exist_ok=True)
x = fs.load_image("cameraman", 256)
rows = lift(x)                       # horizontal pass: [L | H]
both = lift(rows.T).T                # vertical pass: [LL LH; HL HH]


def to_rgb(a, kind):
    if kind == "gray":
        g = np.clip(a, 0, 1)
        return np.repeat(g[..., None], 3, axis=2)
    lim = np.percentile(np.abs(a), 99.5)
    return fs.DIV((np.clip(a / lim, -1, 1) + 1) / 2)[..., :3]


def save(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)) \
        .save(out / f"{name}.png", optimize=True)


save(to_rgb(x, "gray"), "input")
r = np.zeros((256, 256, 3))
r[:, :128] = to_rgb(rows[:, :128], "gray")
r[:, 128:] = to_rgb(rows[:, 128:], "div")
save(r, "rows")
p = np.zeros((256, 256, 3))
p[:128, :128] = to_rgb(both[:128, :128], "gray")
det = np.concatenate([both[:128, 128:].ravel(), both[128:, :].ravel()])
lim = np.percentile(np.abs(det), 99.5)
for sl in ((slice(0, 128), slice(128, 256)), (slice(128, 256), slice(0, 128)), (slice(128, 256), slice(128, 256))):
    p[sl] = fs.DIV((np.clip(both[sl] / lim, -1, 1) + 1) / 2)[..., :3]
save(p, "packed")
print("thumbnails written to", out)
