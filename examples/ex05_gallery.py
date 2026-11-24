"""Example 5 - decomposition gallery on six openly licensed images.

Each row shows the input, its three-level pyramid and the share of detail
energy per orientation (LH = vertical edges, HL = horizontal edges,
HH = diagonals).  Brick and text are strongly oriented; grass and the cat's
fur are close to isotropic.  All images are scikit-image samples: five are
CC0 and the text image is in the public domain.

Run:  python examples/ex05_gallery.py  ->  figures/examples/05_gallery.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose, reconstruct, METHODS  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

NAMES = ["cameraman", "coffee", "chelsea", "brick", "grass", "text"]
ORIENT = [("LH", "vertical edges"), ("HL", "horizontal edges"), ("HH", "diagonal")]
ORIENT_COLOR = [fs.CAT[0], fs.CAT[1], fs.CAT[2]]


def orientation_shares(c, levels):
    h, w = c.shape
    e = np.zeros(3)
    for j in range(1, levels + 1):
        hh, ww = h >> j, w >> j
        e += [np.sum(c[:hh, ww:2 * ww] ** 2), np.sum(c[hh:2 * hh, :ww] ** 2),
              np.sum(c[hh:2 * hh, ww:2 * ww] ** 2)]
    return e / e.sum()


def main():
    fs.setup()
    size, levels = 256, 3
    fig = plt.figure(figsize=(13.2, 7.4))
    outer = fig.add_gridspec(2, 3, left=0.01, right=0.99, top=0.85, bottom=0.09, hspace=0.36, wspace=0.07)
    for k, name in enumerate(NAMES):
        x8 = fs.load_image_u8(name, size)
        x = x8 / 255.0
        c = decompose(x, levels, "lifting")
        for m in METHODS:                         # all six schedules agree
            assert np.allclose(decompose(x, levels, m), c, atol=1e-12)
        assert np.array_equal(reconstruct(decompose(x8, levels), levels), x8)
        sh = orientation_shares(c, levels)
        cell = outer[k // 3, k % 3].subgridspec(1, 2, wspace=0.04)
        a0 = fig.add_subplot(cell[0, 0])
        a1 = fig.add_subplot(cell[0, 1])
        a0.imshow(x, cmap="gray", vmin=0, vmax=1)
        a1.imshow(fs.pyramid_rgb(c, levels))
        fs.draw_band_grid(a1, c.shape, levels, labels=False, lw=1.2)
        a0.set_title(fs.SAMPLE_IMAGES[name][1], loc="left", fontsize=10.5)
        a1.set_title("3-level pyramid", loc="left", fontsize=10.5, color=fs.INK2, fontweight="normal")
        fs.image_axis(a0)
        fs.image_axis(a1)
        a0.apply_aspect()
        a1.apply_aspect()
        p0, p1 = a0.get_position(), a1.get_position()
        fs.segmented_bar(fig, (p0.x0, p0.y0 - 0.052, p1.x1 - p0.x0), sh, ORIENT_COLOR,
                         [f"{o} {100 * v:.0f}%" for (o, _), v in zip(ORIENT, sh)])
    # Legend for the orientation bars.
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ORIENT_COLOR]
    fig.legend(handles, [f"{a} · {b}" for a, b in ORIENT], loc="upper right", ncols=3,
               bbox_to_anchor=(0.99, 0.935), handlelength=1.0, columnspacing=1.4)
    fs.title(fig, "Gallery: six openly licensed images, one transform",
             "Bars: share of detail-coefficient energy by orientation, summed over three levels. "
             "Reconstruction from integer pixels is bit-exact for every image.")
    print("wrote", fs.save(fig, "05_gallery"))


if __name__ == "__main__":
    main()
