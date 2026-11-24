"""Example 2 - recursive (Mallat) decomposition and exact reconstruction.

Each level re-decomposes only the LL band, so a J-level pyramid of an H x W
image still holds exactly H x W coefficients.  The figure shows levels 1-3 of
the 512 x 512 Cameraman image (CC0) and the README hero image: input,
three-level pyramid and the bit-exact inverse.

Run:  python examples/ex02_multilevel_pyramid.py
      -> figures/examples/02_multilevel_pyramid.png, figures/examples/00_hero.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose, reconstruct  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402


def progressive(x):
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 4.15))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.78, bottom=0.07, wspace=0.04)
    axes[0].imshow(x, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title(f"Input  {x.shape[0]} × {x.shape[1]}", loc="left")
    for j in (1, 2, 3):
        c = decompose(x, j, "lifting")
        ax = axes[j]
        ax.imshow(fs.pyramid_rgb(c, j))
        fs.draw_band_grid(ax, c.shape, j, fontsize=8)
        ax.set_title(f"Level {j}  ·  LL{j} is {x.shape[0] >> j} × {x.shape[1] >> j}", loc="left")
    for ax in axes:
        fs.image_axis(ax)
    notes = ["", "4 bands", "7 bands", "10 bands · 3·J + 1 in general"]
    for ax, t in zip(axes, notes):
        ax.text(0, -0.035, t, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=fs.INK2)
    fs.title(fig, "Multilevel decomposition: only LL is split again",
             "Coefficient count stays H × W at every depth; per-level detail scale, red positive, "
             "blue negative; LL in gray.")
    print("wrote", fs.save(fig, "02_multilevel_pyramid"))


def hero(x8):
    x = x8 / 255.0
    c = decompose(x8, 3, "lifting")
    z = reconstruct(c, 3)
    err = np.max(np.abs(z - x8))
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.9))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.80, bottom=0.03, wspace=0.24)
    axes[0].imshow(x, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Image  x[r, c]", loc="left")
    axes[1].imshow(fs.pyramid_rgb(c / 255.0, 3))
    fs.draw_band_grid(axes[1], c.shape, 3, fontsize=8.5)
    axes[1].set_title("Three-level CDF 5/3 pyramid", loc="left")
    axes[2].imshow(z / 255.0, cmap="gray", vmin=0, vmax=1)
    axes[2].set_title(f"Inverse transform  ·  max |error| = {err:g}", loc="left")
    for ax in axes:
        fs.image_axis(ax)
    for a, b, label in ((axes[0], axes[1], "forward\nDWT"), (axes[1], axes[2], "inverse\nDWT")):
        p0 = a.transAxes.transform((1.03, 0.5))
        p1 = b.transAxes.transform((-0.03, 0.5))
        inv = fig.transFigure.inverted()
        q0, q1 = inv.transform(p0), inv.transform(p1)
        fig.add_artist(FancyArrowPatch(q0, q1, transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=16, lw=1.6, color=fs.INK2))
        fig.text((q0[0] + q1[0]) / 2, q0[1] + 0.03, label, ha="center", va="bottom",
                 fontsize=9, color=fs.INK2, linespacing=1.2)
    fs.title(fig, "2-D discrete wavelet transform for image decomposition",
             "Six hardware schedules - row-column FIR, lifting, direct 2-D, line buffer, halo tiles, "
             "folded lifting - produce these identical coefficients.")
    print("wrote", fs.save(fig, "00_hero"))


def main():
    fs.setup()
    x8 = fs.load_image_u8("cameraman", 512)
    progressive(x8 / 255.0)
    hero(x8)


if __name__ == "__main__":
    main()
