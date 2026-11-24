"""Example 9 - dataflow fingerprints of the six RTL schedules.

``python/rtl_model.py`` replays ``rtl/dwt53_frame.v`` clock by clock.  Top
row: the compute clock at which each packed output coefficient is written.
Bottom row: how many times each input pixel is read from the frame RAM.
Same coefficients, six very different orders and memory traffic patterns.

Run:  python examples/ex09_rtl_schedules.py -> figures/examples/09_rtl_schedules.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from rtl_model import simulate, ARCH_NAMES  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hardware"))
from golden import q6  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ORANGE = LinearSegmentedColormap.from_list(
    "seq_orange", ["#fdf3ee", "#f9d3c2", "#f4a988", "#eb6834", "#c4501f", "#8f3510"])


def main():
    fs.setup()
    h = w = 32
    tile = 4
    x = fs.load_image_u8("cameraman", 32)
    ref = q6(x)
    traces = [simulate(x, a, tile) for a in range(6)]
    for t in traces:
        assert np.array_equal(t.coeff, ref)
    n = h * w
    vmax_reads = max(int(t.frame_reads.max()) for t in traces)

    fig, axes = plt.subplots(2, 6, figsize=(13.2, 5.75))
    fig.subplots_adjust(left=0.035, right=0.995, top=0.80, bottom=0.12, wspace=0.08, hspace=0.42)
    for a, t in enumerate(traces):
        ax = axes[0, a]
        ax.imshow(t.write_clock / t.clocks, cmap=fs.SEQ, vmin=0, vmax=1)
        for v in (h // 2 - 0.5,):
            ax.axhline(v, color=fs.SURFACE, lw=1.2)
            ax.axvline(v, color=fs.SURFACE, lw=1.2)
        fs.image_axis(ax)
        ax.text(0, 1.17, f"ARCH {a}", transform=ax.transAxes, ha="left", va="bottom",
                fontsize=10, color=fs.INK2)
        ax.text(0, 1.035, ARCH_NAMES[a], transform=ax.transAxes, ha="left", va="bottom",
                fontsize=10.5, color=fs.INK, fontweight="semibold")
        ax.text(0, -0.05, f"{t.clocks / n:.2f} N compute clocks", transform=ax.transAxes, ha="left",
                va="top", fontsize=9, color=fs.INK2)
        ax2 = axes[1, a]
        ax2.imshow(t.frame_reads, cmap=ORANGE, vmin=0, vmax=vmax_reads)
        fs.image_axis(ax2)
        fr = t.accesses["frame"]["reads"]
        ax2.text(0, -0.05, f"{fr / n:.2f} reads/pixel · ≤ {t.peak_reads_per_clock}/clock",
                 transform=ax2.transAxes, ha="left", va="top", fontsize=9, color=fs.INK2)
    axes[0, 0].set_ylabel("write order", fontsize=10, color=fs.INK, labelpad=6)
    axes[1, 0].set_ylabel("frame-RAM reads", fontsize=10, color=fs.INK, labelpad=6)
    for ax in axes[:, 0]:
        ax.yaxis.label.set_visible(True)
    # Colour keys
    c1 = fig.add_axes([0.70, 0.925, 0.12, 0.016])
    sm = plt.cm.ScalarMappable(cmap=fs.SEQ, norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, cax=c1, orientation="horizontal")
    cb.set_ticks([0, 1], labels=["first clock", "last"])
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=8.5)
    c2 = fig.add_axes([0.86, 0.925, 0.12, 0.016])
    sm2 = plt.cm.ScalarMappable(cmap=ORANGE, norm=plt.Normalize(0, vmax_reads))
    cb2 = fig.colorbar(sm2, cax=c2, orientation="horizontal")
    cb2.set_ticks([0, vmax_reads], labels=["0 reads", f"{vmax_reads}"])
    cb2.outline.set_visible(False)
    cb2.ax.tick_params(length=0, labelsize=8.5)
    fs.title(fig, "Six schedules, one result: dataflow fingerprints from the RTL model",
             f"{h} × {w} Cameraman frame, TILE = {tile}. Top: when each packed coefficient "
             "[LL LH; HL HH] is written. Bottom: reads of each input pixel.")
    print("wrote", fs.save(fig, "09_rtl_schedules"))


if __name__ == "__main__":
    main()
