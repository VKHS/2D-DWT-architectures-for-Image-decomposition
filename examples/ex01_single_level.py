"""Example 1 - one level of the 2-D CDF 5/3 DWT and what each subband sees.

A natural photograph (Cameraman, CC0) and a synthetic orientation test card
are split into LL, LH, HL and HH.  LH responds to horizontal intensity change
(vertical edges), HL to vertical change (horizontal edges), HH to diagonal
structure; LL is a half-resolution approximation.

Run:  python examples/ex01_single_level.py   ->  figures/examples/01_single_level.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import decompose, reconstruct  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def orientation_card(n: int = 256) -> np.ndarray:
    """Synthetic test card with vertical, horizontal and diagonal structure."""
    r, c = np.mgrid[:n, :n] / n
    x = np.full((n, n), 0.55)
    x[(c > 0.08) & (c < 0.22) & (r > 0.08) & (r < 0.92)] = 0.12        # vertical bar
    x[(r > 0.10) & (r < 0.24) & (c > 0.32) & (c < 0.92)] = 0.95        # horizontal bar
    x[np.abs((r - 0.35) - (c - 0.30)) < 0.045] = 0.12                  # diagonal stripe
    x[(r - 0.66) ** 2 + (c - 0.66) ** 2 < 0.18 ** 2] = 0.95            # disk: all orientations
    x[np.abs((r - 0.95) + (c - 0.33) - 0.0) < 0.035] = 0.85            # anti-diagonal stripe
    return np.clip(x, 0, 1)


def main():
    fs.setup()
    rows = [("Cameraman (CC0)", fs.load_image("cameraman", 256)),
            ("Orientation test card", orientation_card(256))]
    cols = ["Input  256 × 256", "LL  approximation", "LH  vertical edges",
            "HL  horizontal edges", "HH  diagonal detail"]
    fig, axes = plt.subplots(2, 5, figsize=(13.2, 6.3))
    fig.subplots_adjust(left=0.07, right=0.995, top=0.83, bottom=0.08, wspace=0.05, hspace=0.12)
    for i, (name, x) in enumerate(rows):
        c = decompose(x, 1, "lifting")
        assert np.allclose(reconstruct(c, 1), x, atol=1e-12)
        h, w = (n // 2 for n in x.shape)
        ll, lh, hl, hh = c[:h, :w], c[:h, w:], c[h:, :w], c[h:, w:]
        lim = np.percentile(np.abs(np.concatenate([lh.ravel(), hl.ravel(), hh.ravel()])), 99.5)
        axes[i, 0].imshow(x, cmap="gray", vmin=0, vmax=1)
        axes[i, 1].imshow(ll, cmap="gray", vmin=0, vmax=1)
        for k, b in enumerate((lh, hl, hh)):
            axes[i, 2 + k].imshow(b, cmap=fs.DIV, vmin=-lim, vmax=lim)
        axes[i, 0].set_ylabel(name, fontsize=10.5, color=fs.INK, fontweight="semibold", labelpad=8)
        for ax in axes[i]:
            fs.image_axis(ax)
    for ax, t in zip(axes[0], cols):
        ax.set_title(t, loc="left", fontsize=10.5)
    # Explanatory footers under the detail columns.
    notes = ["", "vertical low-pass · horizontal low-pass",
             "vertical low-pass · horizontal high-pass", "vertical high-pass · horizontal low-pass",
             "vertical high-pass · horizontal high-pass"]
    for ax, t in zip(axes[1], notes):
        ax.text(0.0, -0.06, t, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=fs.INK2)
    fs.title(fig, "One decomposition level: four half-resolution subbands",
             "Periodic CDF 5/3; band name = vertical filter then horizontal filter. "
             "Detail bands share one symmetric scale per image; red positive, blue negative.")
    cax = fig.add_axes([0.80, 0.905, 0.17, 0.018])
    fs.coeff_colorbar(fig, cax, label="")
    print("wrote", fs.save(fig, "01_single_level"))


if __name__ == "__main__":
    main()
