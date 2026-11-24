"""Example 6 - energy compaction and sparsity of the wavelet coefficients.

After removing the image mean, pixel magnitudes decay slowly when sorted;
wavelet coefficients (weighted by the norm of their synthesis basis image,
which makes magnitudes comparable across bands) decay by orders of magnitude.
More levels compact the energy further.  Detail coefficients are peaked at
zero with heavy tails (kurtosis far above the Gaussian value of 3), which is
what makes them cheap to code.

Run:  python examples/ex06_energy_compaction.py -> figures/examples/06_energy_compaction.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose  # noqa: E402
from analysis_tools import band_weights  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

LEVELS = (1, 3, 5)
LEVEL_COLOR = {1: fs.BLUE[3], 3: fs.BLUE[7], 5: fs.BLUE[11]}  # ordinal blue ramp
PIXEL_COLOR = fs.MUTED


def main():
    fs.setup()
    x = fs.load_image("cameraman", 512)
    x0 = x - x.mean()
    series = {"pixels (mean removed)": np.sort(np.abs(x0).ravel())[::-1]}
    for j in LEVELS:
        c = decompose(x0, j, "lifting") * band_weights(x.shape, j)
        series[f"{j}-level DWT"] = np.sort(np.abs(c).ravel())[::-1]
    colors = {"pixels (mean removed)": PIXEL_COLOR,
              **{f"{j}-level DWT": LEVEL_COLOR[j] for j in LEVELS}}

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3))
    fig.subplots_adjust(left=0.055, right=0.99, top=0.74, bottom=0.14, wspace=0.28)

    a = axes[0]
    rank = np.arange(1, x.size + 1) / x.size
    for name, v in series.items():
        a.loglog(rank, v / v[0], color=colors[name], label=name)
    a.set_xlim(1 / x.size, 1)
    a.set_ylim(1e-5, 1.5)
    a.grid(True, which="major")
    a.set_xlabel("fraction of coefficients (sorted)")
    a.set_ylabel("normalised magnitude")
    a.set_title("Sorted magnitudes decay faster", loc="left")
    a.legend(loc="lower left", fontsize=8.5, handlelength=1.3)

    b = axes[1]
    for name, v in series.items():
        e = np.cumsum(v ** 2) / np.sum(v ** 2)
        i = np.searchsorted(e, 0.99)
        lab = name if 100 * rank[i] > 20 else f"{name} · 99% at {100 * rank[i]:.1f}%"
        b.plot(100 * rank, 100 * e, color=colors[name], label=lab)
        if 100 * rank[i] <= 20:
            b.plot(100 * rank[i], 99, "o", ms=6, color=colors[name], mec=fs.SURFACE, mew=1.5)
    b.set_xlim(0, 20)
    b.set_ylim(40, 100.5)
    b.grid(True)
    b.set_xlabel("coefficients kept (%)")
    b.set_ylabel("weighted energy captured (%)")
    b.legend(loc="lower right", fontsize=8.5, handlelength=1.3)
    b.set_title("Energy is captured by few coefficients", loc="left")

    c = axes[2]
    d = decompose(x, 1, "lifting")
    h, w = d.shape[0] // 2, d.shape[1] // 2
    det = np.concatenate([d[:h, w:].ravel(), d[h:, :].ravel()])
    bins = np.linspace(-0.25, 0.25, 101)
    cnt, edges = np.histogram(det, bins=bins, density=True)
    mid = (edges[:-1] + edges[1:]) / 2
    c.bar(mid, cnt, width=(edges[1] - edges[0]) * 0.9, color=fs.CAT[0], label="level-1 details")
    sd = det.std()
    kurt = np.mean((det - det.mean()) ** 4) / sd ** 4
    c.plot(mid, np.exp(-0.5 * (mid / sd) ** 2) / (sd * np.sqrt(2 * np.pi)), color=fs.CAT[1], lw=2,
           label="Gaussian, same variance")
    c.set_yscale("log")
    c.set_ylim(1e-2, cnt.max() * 14)
    c.set_xlim(-0.25, 0.25)
    c.grid(True, axis="y")
    c.set_xlabel("coefficient value (pixel units)")
    c.set_ylabel("probability density")
    c.set_title("Detail coefficients are sparse", loc="left")
    c.legend(loc="upper left", fontsize=8.5, handlelength=1.3)
    zero_frac = np.mean(np.abs(det) < 1 / 255)
    c.text(0.98, 0.95, f"kurtosis {kurt:.0f} (Gaussian: 3)\n{100 * zero_frac:.0f}% of details\nbelow one gray level",
           transform=c.transAxes, ha="right", va="top", fontsize=9, color=fs.INK2)
    fs.title(fig, "Energy compaction: why decompose an image",
             "Cameraman 512 × 512 (CC0). Magnitudes weighted by synthesis-basis norm so bands are comparable; "
             "blue steps = 1, 3, 5 levels.")
    print("wrote", fs.save(fig, "06_energy_compaction"))


if __name__ == "__main__":
    main()
