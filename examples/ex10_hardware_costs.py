"""Example 10 - hardware cost model of the six RTL schedules.

Compute clocks, frame-RAM traffic and read-port pressure come from the
cycle-accurate model (python/rtl_model.py, which matches the closed-form
schedule for every size); working storage is the logical array size in the
RTL.  The tile sweep shows the ARCH 4 trade-off: larger tiles amortise the
halo (fewer clocks and re-reads) but need a larger local patch.

Run:  python examples/ex10_hardware_costs.py -> figures/examples/10_hardware_costs.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from rtl_model import simulate, compute_clocks, working_bits, ARCH_NAMES  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def hbar(ax, values, fmt, title, xlabel, log=False):
    y = np.arange(6)[::-1]
    for a in range(6):
        v = values[a]
        if v > 0:
            ax.barh(y[a], v, height=0.52, color=fs.ARCH_COLOR[a])
        xt = (v * 1.25 if v > 0 else 1.2) if log else v + max(values) * 0.02
        ax.text(xt, y[a], fmt(v), va="center", ha="left", fontsize=9, color=fs.INK)
    ax.set_yticks(y, [f"{a} · {fs.ARCH_SHORT[a]}" for a in range(6)])
    ax.tick_params(axis="y", length=0)
    if log:
        ax.set_xscale("log")
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.spines["left"].set_visible(False)


def main():
    fs.setup()
    # Ratios from the model on a 64 x 64 frame (scale invariant; TILE = 8).
    hs = ws = 64
    tile = 8
    x = np.random.default_rng(7).integers(0, 256, size=(hs, ws))
    tr = [simulate(x, a, tile) for a in range(6)]
    n = hs * ws
    clocks = [t.clocks / n for t in tr]
    reads = [t.accesses["frame"]["reads"] / n for t in tr]
    peak = [t.peak_reads_per_clock for t in tr]
    for a in range(6):
        assert tr[a].clocks == compute_clocks(hs, ws, a, tile)
    H = W = 512
    nbytes = [working_bits(H, W, a, tile) / 8 for a in range(6)]

    fig = plt.figure(figsize=(13.2, 7.7))
    gs = fig.add_gridspec(2, 3, left=0.135, right=0.985, top=0.855, bottom=0.08, hspace=0.55, wspace=0.75)
    hbar(fig.add_subplot(gs[0, 0]), clocks, lambda v: f"{v:.2f} N", "Compute clocks per frame",
         "clocks / N   (N = H·W)")
    hbar(fig.add_subplot(gs[0, 1]), reads, lambda v: f"{v:.2f}", "Frame-RAM reads per pixel",
         "logical reads / N")
    hbar(fig.add_subplot(gs[0, 2]), peak, lambda v: f"{v:d}", "Read ports needed",
         "distinct reads in one clock")
    def fmt_bytes(v):
        if v == 0:
            return "none"
        if v >= 1024 ** 2:
            return f"{v / 1024 ** 2:.0f} MiB"
        return f"{v / 1024:.0f} KiB" if v >= 1024 else f"{v:.0f} B"
    sax = fig.add_subplot(gs[1, 0])
    hbar(sax, nbytes, fmt_bytes, "Working storage, 512 × 512", "bytes beyond input and output frames (log)",
         log=True)
    sax.set_xlim(1, 2e7)

    # Tile sweep for ARCH 4 on 512 x 512.
    ts = np.array([1, 2, 4, 8, 16, 32, 64])
    cl = np.array([compute_clocks(H, W, 4, int(t)) / (H * W) for t in ts])
    rd = np.array([(2 * t + 3) ** 2 / (4 * t * t) for t in ts])   # P^2 reads per T^2 quartets
    pb = np.array([working_bits(H, W, 4, int(t)) for t in ts])
    # model check of the read formula at two tile sizes
    for t in (2, 4):
        trt = simulate(np.zeros((32, 32), int), 4, t)
        assert abs(trt.accesses["frame"]["reads"] / 1024 - (2 * t + 3) ** 2 / (4 * t * t)) < 1e-12

    a = fig.add_subplot(gs[1, 1])
    a.plot(ts, cl, color=fs.ARCH_COLOR[4], marker="o", ms=5.5, mec=fs.SURFACE, mew=1.5)
    a.axhline(1.25, color=fs.AXIS, lw=1)
    a.text(1.0, 1.32, "limit 1.25 N", ha="left", va="bottom", fontsize=8.5, color=fs.INK2)
    for t, v in zip(ts, cl):
        if t in (1, 4, 64):
            a.annotate(f"{v:.2f} N", (t, v), xytext=(6, 4), textcoords="offset points", fontsize=8.5,
                       color=fs.INK2)
    a.set_xscale("log", base=2)
    a.set_xticks(ts, [str(t) for t in ts])
    a.set_ylim(0, 7.2)
    a.grid(True)
    a.set_xlabel("TILE  T  (coefficients per tile side)")
    a.set_ylabel("compute clocks / N")
    a.set_title("ARCH 4: clocks fall as tiles grow", loc="left")

    b = fig.add_subplot(gs[1, 2])
    b.plot(pb, rd, color=fs.ARCH_COLOR[4], marker="o", ms=5.5, mec=fs.SURFACE, mew=1.5)
    for t, xx, yy in zip(ts, pb, rd):
        b.annotate(f"T={t}", (xx, yy), xytext=(5, 4), textcoords="offset points", fontsize=8.5,
                   color=fs.INK2)
    b.set_xscale("log")
    b.set_xlim(120, 4e5)
    b.set_ylim(0.8, 7.2)
    b.grid(True)
    b.set_xlabel("patch storage (bits, log)")
    b.set_ylabel("frame reads / pixel")
    b.set_title("ARCH 4: re-reads versus patch size", loc="left")
    fs.title(fig, "Hardware cost model of the six schedules",
             "From the cycle-accurate RTL model (TILE = 8 in the bar charts). Logical quantities of the "
             "reference RTL, before any memory banking or pipelining.")
    print("wrote", fs.save(fig, "10_hardware_costs"))


if __name__ == "__main__":
    main()
