"""Example 12 - showcase figures for the first page.

* ``00_banner.png``      colour rocket launch and its three-level pyramid
* ``12_test_images.png`` eight test images and their pyramids, with the share
                         of coefficients that carries 99 % of the energy
* ``13_progressive.png`` coarse-to-fine synthesis: LL3 only, then adding the
                         detail bands of levels 3, 2 and 1 (exact)

Colour images are decomposed per RGB channel (the transform is linear and
separable, so each channel is an independent image). Detail bands are drawn
as light on black: brightness is the coefficient magnitude per channel
(gamma 0.55, one robust scale per level), so edges glow in the colour of the
intensity change they encode. The photographs are scikit-image samples that
are public domain, CC0 or free of known copyright restrictions; the
Shepp-Logan phantom and the Siemens star are synthetic.

Run:  python examples/ex12_showcase.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import METHODS, decompose  # noqa: E402
from analysis_tools import band_weights  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ORCID = "0000-0003-4870-2768"
AUTHOR = "Abdolvahab Khalili Sadaghiani"


def luminance(x):
    return x @ np.array([0.299, 0.587, 0.114]) if x.ndim == 3 else x


def coeff_share_99(x, levels):
    """Fraction of (synthesis-weighted) coefficients holding 99 % of the energy."""
    y = luminance(x)
    c = (decompose(y - y.mean(), levels, "lifting") * band_weights(y.shape, levels)).ravel()
    e = np.sort(c ** 2)[::-1]
    return (np.searchsorted(np.cumsum(e) / e.sum(), 0.99) + 1) / e.size


def banner():
    x = fs.load_color("rocket", crop=(3, 0, 424, 640))
    c = fs.decompose_rgb(x, 3)
    # every schedule gives the same pyramid (checked on the luminance channel)
    y = luminance(x)
    ref = decompose(y, 3, "fir")
    for m in METHODS:
        assert np.allclose(decompose(y, 3, m), ref, atol=1e-12)
    assert np.allclose(fs.reconstruct_rgb(c, 3), x, atol=1e-12)

    fw, fh = 15.0, 7.0
    pw = 0.42                                   # panel width (figure fraction)
    ph = pw * fw / (x.shape[1] / x.shape[0]) / fh
    top = 0.80
    fig = plt.figure(figsize=(fw, fh), facecolor=fs.DARK)
    a0 = fig.add_axes([0.035, top - ph, pw, ph])
    a1 = fig.add_axes([0.965 - pw, top - ph, pw, ph])
    a0.imshow(x, aspect="auto")
    a1.imshow(fs.glow_pyramid(c, 3), aspect="auto")
    fs.dark_band_grid(a1, c.shape, 3, fontsize=9)
    for a in (a0, a1):
        a.set_axis_off()
    fig.text(0.035, 0.955, "2-D DWT architectures for image decomposition", color=fs.DARK_INK,
             fontsize=24, fontweight="bold", ha="left", va="top")
    fig.text(0.035, 0.885, "CDF 5/3 wavelet  ·  six hardware schedules  ·  bit-identical integer output  ·  "
             "Python, MATLAB and Verilog", color=fs.DARK_INK2, fontsize=12.5, ha="left", va="top")
    fig.text(0.965, 0.952, AUTHOR, color=fs.DARK_INK, fontsize=13, fontweight="semibold", ha="right", va="top")
    fig.text(0.965, 0.902, f"ORCID {ORCID}", color=fs.DARK_INK2, fontsize=11, ha="right", va="top")
    ymid = top - ph / 2
    fig.add_artist(FancyArrowPatch((0.035 + pw + 0.012, ymid), (0.965 - pw - 0.012, ymid),
                                   transform=fig.transFigure, arrowstyle="-|>", mutation_scale=22, lw=2.2,
                                   color=fs.DARK_INK2))
    fig.text(0.5, ymid + 0.03, "2-D DWT\n3 levels", color=fs.DARK_INK2, fontsize=10.5, ha="center",
             va="bottom", linespacing=1.25)
    fig.text(0.035, top - ph - 0.022, "Rocket launch, 424 × 640, RGB (public domain)", color=fs.DARK_INK2,
             fontsize=10, ha="left", va="top")
    fig.text(0.965 - pw, top - ph - 0.022, "Packed pyramid: LL3 in colour, detail magnitude as light",
             color=fs.DARK_INK2, fontsize=10, ha="left", va="top")
    names = ["row-column FIR", "fused lifting", "direct 2-D", "line buffer", "halo tiles", "folded lifting"]
    yp = 0.065
    lead = fig.text(0.035, yp, "Same coefficients from", color=fs.DARK_INK2, fontsize=10.5, ha="left",
                    va="center")
    bb = lead.get_window_extent(fig.canvas.get_renderer())
    fs.pill_row(fig, (bb.x1 + 12) / (fw * fig.dpi), yp, names, fs.CAT[:6])
    fig.savefig(fs.OUT / "00_banner.png", dpi=160, facecolor=fs.DARK)
    plt.close(fig)
    _optimize(fs.OUT / "00_banner.png")


def test_images():
    def retina():
        # square inscribed in the fundus disc (no black corners), optic disc on the left
        return fs.load_color("retina", shape=(256, 256), crop=(233, 234, 940, 940))
    tiles = [
        (lambda: fs.load_color("coffee", shape=(256, 256)), "Coffee"),
        (retina, "Retina (fundus photograph)"),
        (lambda: fs.load_color("coins", shape=(256, 256))[..., 0], "Greek coins"),
        (lambda: fs.load_color("camera", shape=(256, 256))[..., 0], "Cameraman"),
        (lambda: fs.load_color("chelsea", shape=(256, 256)), "Cat (Chelsea)"),
        (lambda: fs.load_color("brick", shape=(256, 256))[..., 0], "Brick texture"),
        (lambda: fs.load_color("phantom", shape=(256, 256))[..., 0], "Shepp–Logan phantom"),
        (lambda: fs.siemens_star(256, 36), "Siemens star"),
    ]
    fw = 13.2
    ax_w = 0.976 * fw / (4 + 3 * 0.035)          # square axis side (inches)
    cell_h = 2 * ax_w + 0.05 * ax_w
    gap_o = 0.62
    top_m, bot_m = 1.2, 0.42
    fh = 2 * cell_h + gap_o + top_m + bot_m
    fig = plt.figure(figsize=(fw, fh), facecolor=fs.DARK)
    outer = fig.add_gridspec(2, 4, left=0.012, right=0.988, top=1 - top_m / fh, bottom=bot_m / fh,
                             hspace=gap_o / cell_h, wspace=0.035)
    for k, (load, label) in enumerate(tiles):
        x = load()
        c = fs.decompose_rgb(x, 3) if x.ndim == 3 else decompose(x, 3, "lifting")
        share = coeff_share_99(x, 3)
        cell = outer[k // 4, k % 4].subgridspec(2, 1, hspace=0.05)
        ai = fig.add_subplot(cell[0])
        ap = fig.add_subplot(cell[1])
        ai.imshow(x, cmap="gray" if x.ndim == 2 else None, vmin=0, vmax=1)
        ap.imshow(fs.glow_pyramid(c, 3))
        fs.dark_band_grid(ap, c.shape, 3, labels=False, lw=0.8)
        for a in (ai, ap):
            a.set_axis_off()
        ai.set_title(label, loc="left", color=fs.DARK_INK, fontsize=11.5, fontweight="semibold", pad=6)
        ap.text(0.0, -0.03, f"99 % of the energy in {100 * share:.1f} % of the coefficients",
                transform=ap.transAxes, ha="left", va="top", color=fs.DARK_INK2, fontsize=9)
    fig.text(0.012, 1 - 0.28 / fh, "Test images and their three-level pyramids", color=fs.DARK_INK,
             fontsize=17, fontweight="bold", ha="left", va="top")
    fig.text(0.012, 1 - 0.62 / fh, "Photographs, a fundus image, a museum scan, a texture, a CT phantom and a "
             "resolution chart. Detail bands glow where the image changes.",
             color=fs.DARK_INK2, fontsize=11, ha="left", va="top")
    fig.savefig(fs.OUT / "12_test_images.png", dpi=140, facecolor=fs.DARK)
    plt.close(fig)
    _optimize(fs.OUT / "12_test_images.png")


def progressive():
    x = fs.load_color("chelsea", crop=(2, 1, 296, 448))
    c = fs.decompose_rgb(x, 3)
    h, w = x.shape[:2]
    steps = [(3, "LL3 only"), (2, "+ level 3 details"), (1, "+ level 2 details"), (0, "+ level 1 details  =  exact")]
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.65), facecolor=fs.DARK)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.73, bottom=0.12, wspace=0.04)
    for ax, (keep, label) in zip(axes, steps):
        hk, wk = h >> keep, w >> keep            # keep the top-left LL_keep block (all coarser bands)
        cc = np.zeros_like(c)
        cc[:hk, :wk] = c[:hk, :wk]
        z = np.clip(fs.reconstruct_rgb(cc, 3), 0, 1)
        p = fs.psnr(x, z)
        ax.imshow(z)
        ax.set_axis_off()
        ax.set_title(label, loc="left", color=fs.DARK_INK, fontsize=11.5, fontweight="semibold", pad=6)
        frac = hk * wk / (h * w)
        ptxt = "lossless" if not np.isfinite(p) or p > 200 else f"PSNR {p:.1f} dB"
        ax.text(0.0, -0.04, f"{100 * frac:.2f} % of the coefficients  ·  {ptxt}", transform=ax.transAxes,
                ha="left", va="top", color=fs.DARK_INK2, fontsize=9.5)
    fig.text(0.01, 0.975, "Coarse to fine: every level adds the detail that the one before could not hold",
             color=fs.DARK_INK, fontsize=15, fontweight="bold", ha="left", va="top")
    fig.text(0.01, 0.875, "Inverse transform of a 296 × 448 colour image with the finer detail bands set to zero; "
             "the final step restores it exactly.", color=fs.DARK_INK2, fontsize=10.5, ha="left", va="top")
    fig.savefig(fs.OUT / "13_progressive.png", dpi=150, facecolor=fs.DARK)
    plt.close(fig)
    _optimize(fs.OUT / "13_progressive.png")


def _optimize(path):
    from PIL import Image
    with Image.open(path) as im:
        im.convert("RGB").save(path, optimize=True)
    print("wrote", path)


def main():
    fs.setup()
    fs.OUT.mkdir(parents=True, exist_ok=True)
    banner()
    test_images()
    progressive()


if __name__ == "__main__":
    main()
