"""Shared visual language for every computed figure in ``figures/examples``.

One sans typeface (Inter, falling back to DejaVu Sans), one light chart
surface, recessive hairline axes, a fixed categorical order for the six
architectures, a single-hue sequential ramp for magnitudes and a blue/red
diverging map with a neutral gray midpoint for signed wavelet coefficients
(blue = negative, red = positive).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "examples"

# Surfaces and ink --------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Categorical slots in fixed order: ARCH 0..5 always take slots 1..6.
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300",
       "#6250d6", "#e34948"]
ARCH_COLOR = {a: CAT[a] for a in range(6)}
ARCH_SHORT = {0: "Row-column FIR", 1: "Fused lifting", 2: "Direct 2-D",
              3: "Line buffer", 4: "Halo tiled", 5: "Folded lifting"}
METHOD_ARCH = {"fir": 0, "lifting": 1, "direct2d": 2, "line": 3, "tile": 4, "folded": 5}

# Sequential blue ramp (100 -> 700) and its matplotlib colormap.
BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
        "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#f4f8fd"] + BLUE)

# Diverging blue <-> red, neutral gray midpoint, equal steps per arm.
_NEG = ["#0d366b", "#1c5cab", "#3987e5", "#86b6ef", "#cde2fb"]
_POS = ["#f7d3d2", "#ef9493", "#e34948", "#b32e2d", "#7a1a19"]
DIV = LinearSegmentedColormap.from_list("div_blue_red", _NEG + ["#f0efec"] + _POS)


def setup() -> None:
    """Apply the house style to matplotlib."""
    fam = ["Inter", "DejaVu Sans"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": fam,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlecolor": INK,
        "axes.labelcolor": INK2,
        "axes.labelsize": 10,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.facecolor": SURFACE,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": matplotlib.cycler(color=CAT),
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "grid.linestyle": "-",
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "figure.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "image.interpolation": "nearest",
        "mathtext.fontset": "custom",
        "mathtext.rm": "Inter",
        "mathtext.it": "Inter:italic",
        "mathtext.bf": "Inter:bold",
    })


def save(fig, name: str, dpi: int = 160) -> Path:
    """Save to figures/examples/<name>.png (lossless, optimized) and close."""
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=dpi, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.save(path, optimize=True)
    return path


def title(fig, text: str, sub: str | None = None, y: float = 0.995) -> None:
    """Left-aligned figure title with an optional secondary line.

    The gap between the two lines is fixed in inches, so it does not depend
    on the figure height.
    """
    fig.text(0.01, y, text, ha="left", va="top", fontsize=14, fontweight="bold", color=INK)
    if sub:
        dy = 0.30 / fig.get_size_inches()[1]
        fig.text(0.01, y - dy, sub, ha="left", va="top", fontsize=10, color=INK2)


def image_axis(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# Image helpers ------------------------------------------------------------
SAMPLE_IMAGES = {
    # name: (loader attribute, caption)
    "cameraman": ("camera", "Cameraman"),
    "coffee": ("coffee", "Coffee"),
    "chelsea": ("chelsea", "Cat (Chelsea)"),
    "brick": ("brick", "Brick texture"),
    "grass": ("grass", "Grass texture"),
    "text": ("text", "Text"),
}


def load_image(name: str, size: int = 256) -> np.ndarray:
    """scikit-image sample (CC0 or public domain) as grayscale float in [0, 1].

    The image is center-cropped to a square (no aspect distortion) and
    box-resampled, the same preprocessing family as the repository scripts.
    """
    from PIL import Image
    from skimage import data
    attr = SAMPLE_IMAGES[name][0] if name in SAMPLE_IMAGES else name
    a = getattr(data, attr)()
    img = Image.fromarray(a).convert("L")
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    img = img.resize((size, size), Image.Resampling.BOX)
    return np.asarray(img, dtype=float) / 255.0


def load_image_u8(name: str, size: int = 256) -> np.ndarray:
    """Same as :func:`load_image` but as unsigned 8-bit integers."""
    return np.rint(load_image(name, size) * 255).astype(np.int64)


def band_slices(shape, levels: int):
    """Yield (name, level, (rows, cols)) for every band of a packed pyramid."""
    h, w = shape
    for j in range(1, levels + 1):
        hh, ww = h >> j, w >> j
        yield f"LH{j}", j, (slice(0, hh), slice(ww, 2 * ww))
        yield f"HL{j}", j, (slice(hh, 2 * hh), slice(0, ww))
        yield f"HH{j}", j, (slice(hh, 2 * hh), slice(ww, 2 * ww))
    hh, ww = h >> levels, w >> levels
    yield f"LL{levels}", levels, (slice(0, hh), slice(0, ww))


def pyramid_rgb(c: np.ndarray, levels: int, pct: float = 99.0, ll_range=(0.0, 1.0)) -> np.ndarray:
    """Render a packed coefficient array as an RGB image.

    LL is shown in grayscale; each level's three detail bands share one
    symmetric limit (the ``pct`` percentile of their magnitudes) on the
    blue/red diverging map, so orientations within a level stay comparable.
    """
    h, w = c.shape
    rgb = np.zeros((h, w, 3))
    for j in range(1, levels + 1):
        hh, ww = h >> j, w >> j
        det = np.concatenate([c[:hh, ww:2 * ww].ravel(), c[hh:2 * hh, :2 * ww].ravel()])
        lim = max(np.percentile(np.abs(det), pct), 1e-12)
        for sl in ((slice(0, hh), slice(ww, 2 * ww)), (slice(hh, 2 * hh), slice(0, ww)),
                   (slice(hh, 2 * hh), slice(ww, 2 * ww))):
            v = np.clip(c[sl] / lim, -1, 1)
            rgb[sl] = DIV((v + 1) / 2)[..., :3]
    hh, ww = h >> levels, w >> levels
    lo, hi = ll_range
    g = np.clip((c[:hh, :ww] - lo) / (hi - lo), 0, 1)
    rgb[:hh, :ww] = np.repeat(g[..., None], 3, axis=2)
    return rgb


def draw_band_grid(ax, shape, levels: int, labels: bool = True, color: str = SURFACE,
                   lw: float = 1.6, fontsize: float = 8.5, min_label_px: int = 18) -> None:
    """Separate the packed bands with surface-colored lines and name them."""
    h, w = shape
    for j in range(1, levels + 1):
        hh, ww = h >> j, w >> j
        ax.plot([ww - 0.5, ww - 0.5], [-0.5, 2 * hh - 0.5], color=color, lw=lw)
        ax.plot([-0.5, 2 * ww - 0.5], [hh - 0.5, hh - 0.5], color=color, lw=lw)
    if not labels:
        return
    for name, j, (rs, cs) in band_slices(shape, levels):
        size = rs.stop - rs.start
        if size < min_label_px:
            continue
        ax.text(cs.start + 0.04 * size + 1, rs.start + 0.04 * size + 1, name,
                ha="left", va="top", fontsize=fontsize, color=INK, fontweight="semibold",
                bbox=dict(boxstyle="round,pad=0.18", fc=SURFACE, ec="none", alpha=0.85))


def coeff_colorbar(fig, ax_or_cax, label="signed detail (per-level scale)", orientation="horizontal"):
    sm = matplotlib.cm.ScalarMappable(cmap=DIV, norm=matplotlib.colors.Normalize(-1, 1))
    cb = fig.colorbar(sm, cax=ax_or_cax, orientation=orientation)
    cb.set_ticks([-1, 0, 1])
    cb.set_ticklabels(["−", "0", "+"])
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=9)
    cb.set_label(label, color=INK2, fontsize=9)
    return cb


def psnr(x: np.ndarray, y: np.ndarray, peak: float = 1.0) -> float:
    mse = float(np.mean((x - y) ** 2))
    return float("inf") if mse == 0 else 10 * np.log10(peak ** 2 / mse)


def rgb_of(hex_color: str):
    return to_rgb(hex_color)


def segmented_bar(fig, rect, shares, colors, labels, height_px: float = 26, dpi: float = 160,
                  min_label_frac: float = 0.11):
    """Tall segmented bar (one whole split into parts).

    ``rect`` = (left, bottom, width) in figure fraction; the height is fixed
    in pixels.  Parts are separated by a 2 px surface gap, have 4 px corners
    and carry their label inside at the leading edge when it fits.
    """
    from matplotlib.patches import FancyBboxPatch
    left, bottom, width = rect
    fw, fh = fig.get_size_inches()
    hfrac = height_px / (fh * dpi)
    ax = fig.add_axes([left, bottom, width, hfrac])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    gap = 2.0 / (width * fw * dpi)
    rad_x = 4.0 / (width * fw * dpi)
    x = 0.0
    for share, col, lab in zip(shares, colors, labels):
        w = max(share - gap, 0)
        if w > 0:
            ax.add_patch(FancyBboxPatch((x, 0), w, 1, boxstyle=f"round,pad=0,rounding_size={rad_x}",
                                        mutation_aspect=(4.0 / height_px) / rad_x,
                                        fc=col, ec="none"))
            if share >= min_label_frac:
                ink = INK if col.lower() in ("#eda100", "#fab219") else "#ffffff"
                ax.text(x + 0.012, 0.5, lab, ha="left", va="center", fontsize=8.5, color=ink,
                        fontweight="semibold")
        x += share
    return ax
