"""Example 3 - how the subbands partition the 2-D frequency plane.

A zone plate x = 1/2 + 1/2 cos(pi r^2 / N) has local frequency proportional
to the distance from its centre, so space doubles as a frequency axis.  After
one level, LL keeps the low-frequency centre, LH the rings at the left/right
edges (high horizontal frequency), HL the top/bottom and HH the corners.  The
right panel is the ideal two-level tiling of the (wx, wy) plane; the real
5/3 filters overlap at the boundaries, which shows up as faint leakage.

Run:  python examples/ex03_zone_plate.py  ->  figures/examples/03_zone_plate.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402


def zone_plate(n: int = 256) -> np.ndarray:
    r, c = np.mgrid[:n, :n] - n / 2 + 0.5
    return 0.5 + 0.5 * np.cos(np.pi * (r ** 2 + c ** 2) / n)


TINT = {"LL": "#e8e7e2", "LH": "#cde2fb", "HL": "#fbd9cb", "HH": "#c9ede0"}


def tiling(ax, levels: int = 2):
    ax.set_xlim(-np.pi, np.pi)
    ax.set_ylim(-np.pi, np.pi)
    ax.set_aspect("equal")
    lab = {}
    for j in range(1, levels + 1):
        b = np.pi / 2 ** j
        a = 2 * b
        # HH corners, LH left/right, HL top/bottom
        for sx in (-1, 1):
            for sy in (-1, 1):
                ax.add_patch(Rectangle((sx * a if sx < 0 else b, sy * a if sy < 0 else b),
                                       a - b, a - b, fc=TINT["HH"], ec=fs.SURFACE, lw=1.5))
            ax.add_patch(Rectangle((-a if sx < 0 else b, -b), a - b, 2 * b,
                                   fc=TINT["LH"], ec=fs.SURFACE, lw=1.5))
            ax.add_patch(Rectangle((-b, -a if sx < 0 else b), 2 * b, a - b,
                                   fc=TINT["HL"], ec=fs.SURFACE, lw=1.5))
        lab[j] = (a, b)
    b = np.pi / 2 ** levels
    ax.add_patch(Rectangle((-b, -b), 2 * b, 2 * b, fc=TINT["LL"], ec=fs.SURFACE, lw=1.5))
    for j, (a, b) in lab.items():
        m = (a + b) / 2
        fsz = 10 if j == 1 else 8
        for txt, (px, py) in ((f"LH{j}", (m, 0)), (f"LH{j}", (-m, 0)), (f"HL{j}", (0, m)),
                              (f"HL{j}", (0, -m)), (f"HH{j}", (m, m)), (f"HH{j}", (-m, -m)),
                              (f"HH{j}", (m, -m)), (f"HH{j}", (-m, m))):
            ax.text(px, py, txt, ha="center", va="center", fontsize=fsz, color=fs.INK)
    ax.text(0, 0, f"LL{levels}", ha="center", va="center", fontsize=8, color=fs.INK)
    ticks = [-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi]
    names = ["−π", "−π/2", "0", "π/2", "π"]
    ax.set_xticks(ticks, names)
    ax.set_yticks(ticks, names)
    ax.set_xlabel("horizontal frequency ωx")
    ax.set_ylabel("vertical frequency ωy")
    for s in ("left", "bottom"):
        ax.spines[s].set_color(fs.AXIS)


def main():
    fs.setup()
    x = zone_plate(256)
    fig = plt.figure(figsize=(13.2, 3.95))
    gs = fig.add_gridspec(1, 4, left=0.005, right=0.985, top=0.79, bottom=0.12, wspace=0.12)
    axes = [fig.add_subplot(gs[0, k]) for k in range(4)]
    axes[0].imshow(x, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Zone plate  ·  frequency grows with radius", loc="left", fontsize=10.5)
    for j in (1, 2):
        c = decompose(x, j, "lifting")
        axes[j].imshow(fs.pyramid_rgb(c, j, pct=99.5, ll_range=(0, 1)))
        fs.draw_band_grid(axes[j], c.shape, j, fontsize=8.5)
        axes[j].set_title(f"{j}-level decomposition", loc="left", fontsize=10.5)
    for ax in axes[:3]:
        fs.image_axis(ax)
    tiling(axes[3], 2)
    axes[3].set_title("Ideal 2-level frequency tiling", loc="left", fontsize=10.5)
    fs.title(fig, "Subbands are a tiling of the 2-D frequency plane",
             "Each band keeps the zone-plate rings whose local frequency falls in its tile; "
             "the decimated band shows them folded to lower frequency.")
    print("wrote", fs.save(fig, "03_zone_plate"))


if __name__ == "__main__":
    main()
