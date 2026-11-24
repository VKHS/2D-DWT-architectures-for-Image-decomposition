"""Example 11 - the exact integer (Q6) arithmetic contract and its word lengths.

For 8-bit unsigned pixels the RTL computes numerators with no rounding:
first pass L8, H8 (scale 8), final coefficients C64 = 64 x C.  Exact worst-case
ranges follow from the positive and negative tap sums of each mask; the
observed ranges come from the six sample images and the six RTL test frames.
Every final band fits in signed 16 bits (HH: +/-32,640), first-pass values
in signed 13 bits.

Run:  python examples/ex11_fixed_point.py -> figures/examples/11_fixed_point.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hardware"))
import figstyle as fs  # noqa: E402
from golden import q6, LOW, HIGH  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

NAMES = ["cameraman", "coffee", "chelsea", "brick", "grass", "text"]


def signed_bits(lo, hi):
    b = 2
    while not (-(2 ** (b - 1)) <= lo and hi <= 2 ** (b - 1) - 1):
        b += 1
    return b


def pass1(x):
    """First (horizontal) pass numerators, packed [L8 | H8]."""
    w = x.shape[1]
    c = np.arange(0, w, 2)
    lo = sum(LOW[k] * x[:, (c + k - 2) % w] for k in range(5))
    hi = sum(HIGH[k] * x[:, (c + k - 2) % w] for k in range(5))
    return lo, hi


def test_frames(h=32, w=32):
    r, c = np.mgrid[:h, :w]
    imp = np.zeros((h, w), int)
    imp[-1, 0] = 255
    return [np.zeros((h, w), int), np.full((h, w), 255), imp, 255 * ((r + c) % 2), (17 * r + 31 * c) % 256,
            np.random.default_rng(53).integers(0, 256, size=(h, w))]


def main():
    fs.setup()
    frames = [fs.load_image_u8(n, 256) for n in NAMES] + test_frames()
    worst = {}
    for nm, t in (("L8", LOW), ("H8", HIGH)):
        worst[nm] = (255 * t[t < 0].sum(), 255 * t[t > 0].sum())
    for nm, (v, h) in {"LL": (LOW, LOW), "LH": (LOW, HIGH), "HL": (HIGH, LOW), "HH": (HIGH, HIGH)}.items():
        m = np.outer(v, h)
        worst[nm] = (255 * m[m < 0].sum(), 255 * m[m > 0].sum())
    obs = {k: [np.inf, -np.inf] for k in worst}
    for x in frames:
        lo, hi = pass1(x)
        y = q6(x)
        hh, ww = x.shape[0] // 2, x.shape[1] // 2
        parts = {"L8": lo, "H8": hi, "LL": y[:hh, :ww], "LH": y[:hh, ww:], "HL": y[hh:, :ww], "HH": y[hh:, ww:]}
        for k, v in parts.items():
            obs[k][0] = min(obs[k][0], v.min())
            obs[k][1] = max(obs[k][1], v.max())
    # Worst cases are attainable: build the extremal 5x5 window for HH.
    m = np.outer(HIGH, HIGH)
    win = np.where(m > 0, 255, 0)
    assert (m * win).sum() == worst["HH"][1]

    order = ["L8", "H8", "LL", "LH", "HL", "HH"]
    fig, ax = plt.subplots(figsize=(13.2, 4.6))
    fig.subplots_adjust(left=0.13, right=0.86, top=0.78, bottom=0.14)
    y = np.arange(len(order))[::-1]
    for i, k in enumerate(order):
        lo, hi = worst[k]
        ax.barh(y[i], hi - lo, left=lo, height=0.56, color=fs.BLUE[1])
        olo, ohi = obs[k]
        ax.barh(y[i], ohi - olo, left=olo, height=0.56, color=fs.BLUE[7])
        b = signed_bits(lo, hi)
        ax.text(1.005, y[i], f"{b}-bit signed", transform=ax.get_yaxis_transform(), va="center", ha="left",
                fontsize=9.5, color=fs.INK, fontweight="semibold")
        ax.text(1.115, y[i], f"[{lo:,}, {hi:,}]".replace("-", "−"), transform=ax.get_yaxis_transform(), va="center", ha="left",
                fontsize=8.5, color=fs.INK2)
    ax.axvline(0, color=fs.AXIS, lw=1)
    for v in (-32768, 32767):
        ax.axvline(v, color=fs.INK2, lw=1)
    ax.text(32767, len(order) - 0.35, "±2¹⁵", ha="center", va="bottom", fontsize=8.5, color=fs.INK2)
    ax.set_yticks(y, ["L8  first pass, low", "H8  first pass, high", "LL  final ×64", "LH  final ×64",
                      "HL  final ×64", "HH  final ×64"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-36000, 36000)
    ax.set_xticks([-32768, -16384, 0, 16384, 32767], ["−32,768", "−16,384", "0", "16,384", "32,767"])
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.set_xlabel("integer value of the RTL signal")
    handles = [plt.Rectangle((0, 0), 1, 1, color=fs.BLUE[1]), plt.Rectangle((0, 0), 1, 1, color=fs.BLUE[7])]
    ax.legend(handles, ["exact worst case (any 8-bit input)", "observed: 6 sample images + 6 RTL test frames"],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, borderaxespad=0.3)
    fs.title(fig, "Fixed-point contract: exact ranges and word lengths",
             "No rounding anywhere: the output port carries 64 × the floating-point coefficient. "
             "The reference RTL uses 32-bit words; 16 bits are sufficient for every band.")
    print("wrote", fs.save(fig, "11_fixed_point"))


if __name__ == "__main__":
    main()
