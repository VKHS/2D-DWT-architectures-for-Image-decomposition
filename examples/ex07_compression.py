"""Example 7 - nonlinear approximation: keep only the largest coefficients.

Zeroing all but the k% largest weighted coefficients of a five-level
decomposition and inverting shows how much of each image the transform packs
into a few numbers.  This is the mechanism behind wavelet image coding
(JPEG 2000 adds quantisation and entropy coding on top of it).

Run:  python examples/ex07_compression.py -> figures/examples/07_compression.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from analysis_tools import band_weights, keep_largest  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

FRACTIONS = np.array([0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2])
NAMES = ["cameraman", "coffee", "chelsea", "brick", "grass", "text"]


def main():
    fs.setup()
    size, levels = 256, 5
    wts = band_weights((size, size), levels)
    x = fs.load_image("cameraman", size)
    fig = plt.figure(figsize=(13.2, 8.6))
    gs = fig.add_gridspec(2, 4, left=0.05, right=0.99, top=0.865, bottom=0.075, hspace=0.42, wspace=0.18,
                          height_ratios=[1.0, 0.95])
    show = [(None, "Original"), (0.10, "Keep 10%"), (0.03, "Keep 3%"), (0.01, "Keep 1%")]
    for k, (frac, lab) in enumerate(show):
        ax = fig.add_subplot(gs[0, k])
        y = x if frac is None else np.clip(keep_largest(x, levels, frac, wts), 0, 1)
        ax.imshow(y, cmap="gray", vmin=0, vmax=1)
        fs.image_axis(ax)
        ttl = lab if frac is None else f"{lab}  ·  PSNR {fs.psnr(x, y):.1f} dB"
        ax.set_title(ttl, loc="left", fontsize=10.5)

    a = fig.add_subplot(gs[1, :2])
    for i, name in enumerate(NAMES):
        img = fs.load_image(name, size)
        p = [fs.psnr(img, keep_largest(img, levels, f, wts)) for f in FRACTIONS]
        a.plot(100 * FRACTIONS, p, color=fs.CAT[i], marker="o", ms=4.5, mec=fs.SURFACE, mew=1.2,
               label=fs.SAMPLE_IMAGES[name][1])
    a.set_xlim(0, 20.5)
    a.grid(True)
    a.set_xlabel("coefficients kept (%)")
    a.set_ylabel("PSNR (dB)")
    a.set_title("Six images, five levels", loc="left", pad=8)
    a.legend(loc="upper left", ncols=2, fontsize=8.5)

    b = fig.add_subplot(gs[1, 2:])
    ramp = {1: fs.BLUE[2], 2: fs.BLUE[4], 3: fs.BLUE[6], 4: fs.BLUE[9], 5: fs.BLUE[12]}
    for j in (1, 2, 3, 4, 5):
        wj = band_weights((size, size), j)
        p = [fs.psnr(x, keep_largest(x, j, f, wj)) for f in FRACTIONS]
        b.plot(100 * FRACTIONS, p, color=ramp[j], marker="o", ms=4.5, mec=fs.SURFACE, mew=1.2,
               label=f"{j} level{'s' if j > 1 else ''}")
    b.set_xlim(0, 20.5)
    b.grid(True)
    b.set_xlabel("coefficients kept (%)")
    b.set_ylabel("PSNR (dB)")
    b.set_title("Cameraman: deeper pyramids compact more", loc="left", pad=8)
    b.legend(loc="lower right", ncols=2, fontsize=8.5)
    b.text(0.02, 0.97, "J = 1 cannot keep all of LL1 (25% of the coefficients)",
           transform=b.transAxes, ha="left", va="top", fontsize=8.5, color=fs.INK2)
    fs.title(fig, "Keeping only the largest coefficients",
             "Five-level CDF 5/3, coefficients ranked by |c| × synthesis-basis norm; all others set to zero "
             "before the inverse transform. No quantisation or entropy coding.")
    print("wrote", fs.save(fig, "07_compression"))


if __name__ == "__main__":
    main()
