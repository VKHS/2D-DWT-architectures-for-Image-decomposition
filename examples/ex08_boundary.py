"""Example 8 - boundary handling: periodic wrap versus symmetric extension.

The repository (software and RTL) uses periodic indices, wrap(k, n) = k mod n:
simple address generation and exact equivalence of all six schedules.  At an
image border the filter then sees the opposite border, so a bright left edge
next to a dark right edge becomes an artificial step and produces a column
of large detail coefficients.  Whole-sample symmetric extension (the JPEG 2000
rule, x[-k] = x[k]) mirrors the image instead and removes that step.

Run:  python examples/ex08_boundary.py -> figures/examples/08_boundary.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose, reconstruct  # noqa: E402
from analysis_tools import band_weights, keep_largest, decompose_sym, reconstruct_sym  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def extension_panel(ax):
    n = 12
    x = np.linspace(0.15, 0.9, n)                    # a ramp: worst case for wrap-around
    idx = np.arange(-4, n + 4)
    per = x[idx % n]
    sym = x[np.where(idx < 0, -idx, np.where(idx >= n, 2 * (n - 1) - idx, idx))]
    off = 0.0
    for vals, lab, col, dy in ((per, "periodic  x[k mod n]", fs.CAT[1], 1.15), (sym, "symmetric  x[−k] = x[k]", fs.CAT[0], 0.0)):
        inside = (idx >= 0) & (idx < n)
        ax.vlines(idx, dy, dy + vals, color=np.where(inside, fs.INK2, col).tolist(), lw=1.6)
        ax.scatter(idx[inside], dy + vals[inside], s=26, color=fs.INK2, zorder=3, edgecolor=fs.SURFACE, lw=1.2)
        ax.scatter(idx[~inside], dy + vals[~inside], s=26, color=col, zorder=3, edgecolor=fs.SURFACE, lw=1.2)
        ax.text(-4.4, dy + 1.0, lab, ha="left", va="bottom", fontsize=9, color=fs.INK)
    for v in (-0.5, n - 0.5):
        ax.axvline(v, color=fs.AXIS, lw=1)
    ax.text(n / 2 - 0.5, -0.12, "image row  (n = 12)", ha="center", va="top", fontsize=8.5, color=fs.INK2)
    ax.text(-2.5, -0.12, "extension", ha="center", va="top", fontsize=8.5, color=fs.INK2)
    ax.text(n + 1.5, -0.12, "extension", ha="center", va="top", fontsize=8.5, color=fs.INK2)
    ax.set_xlim(-4.6, n + 3.6)
    ax.set_ylim(-0.3, 2.35)
    ax.axis("off")
    ax.set_title("How samples beyond the border are defined", loc="left")


def main():
    fs.setup()
    size, levels = 256, 5
    x = fs.load_image("cameraman", size)
    cp = decompose(x, 1, "lifting")
    cs = decompose_sym(x, 1)
    h, w = size // 2, size // 2
    lh_p, lh_s = cp[:h, w:], cs[:h, w:]
    lim = np.percentile(np.abs(np.concatenate([lh_p.ravel(), lh_s.ravel()])), 99.5)

    fig = plt.figure(figsize=(13.2, 4.6))
    gs = fig.add_gridspec(1, 4, left=0.01, right=0.99, top=0.76, bottom=0.12, wspace=0.26,
                          width_ratios=[1.25, 0.8, 0.8, 1.15])
    extension_panel(fig.add_subplot(gs[0, 0]))
    for k, (band, lab) in enumerate(((lh_p, "LH1, periodic"), (lh_s, "LH1, symmetric"))):
        ax = fig.add_subplot(gs[0, 1 + k])
        ax.imshow(band[:, -40:], cmap=fs.DIV, vmin=-lim, vmax=lim, aspect="auto")
        fs.image_axis(ax)
        edge = np.mean(np.abs(band[:, -1]))
        inner = np.mean(np.abs(band[:, :-4]))
        ax.set_title(f"{lab}", loc="left")
        ax.text(0, -0.04, f"right-most 40 columns\nlast column mean |c| = {edge / inner:.1f} × interior",
                transform=ax.transAxes, ha="left", va="top", fontsize=8.5, color=fs.INK2)
    a = fig.add_subplot(gs[0, 3])
    fr = np.array([0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2])
    wts = band_weights((size, size), levels)
    pp = [fs.psnr(x, keep_largest(x, levels, f, wts)) for f in fr]
    ps = [fs.psnr(x, keep_largest(x, levels, f, wts, transform=lambda v: decompose_sym(v, levels),
                                  inverse=lambda v: reconstruct_sym(v, levels))) for f in fr]
    a.plot(100 * fr, ps, color=fs.CAT[0], marker="o", ms=4.5, mec=fs.SURFACE, mew=1.2, label="symmetric")
    a.plot(100 * fr, pp, color=fs.CAT[1], marker="o", ms=4.5, mec=fs.SURFACE, mew=1.2, label="periodic")
    a.grid(True)
    a.set_xlabel("coefficients kept (%)")
    a.set_ylabel("PSNR (dB)")
    a.set_title("Cameraman, keep-largest, 5 levels", loc="left", pad=24)
    a.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, borderaxespad=0.2)
    gain = np.mean(np.array(ps) - np.array(pp))
    a.text(0.98, 0.05, f"symmetric: +{gain:.2f} dB on average", transform=a.transAxes, ha="right",
           va="bottom", fontsize=9, color=fs.INK2)
    assert np.allclose(reconstruct(cp, 1), x) and np.allclose(reconstruct_sym(cs, 1), x)
    fs.title(fig, "Boundary handling: the cost of periodic wrap",
             "The architectures here use periodic indices (one address rule, exact schedule equivalence); "
             "symmetric extension is the JPEG 2000 alternative.")
    print("wrote", fs.save(fig, "08_boundary"))


if __name__ == "__main__":
    main()
