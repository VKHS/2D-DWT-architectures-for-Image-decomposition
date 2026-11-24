"""Example 4 - the CDF 5/3 filters, their wavelets and the 2-D basis images.

Analysis (forward) filters, as implemented:
    h0 = [-1/8, 1/4, 3/4, 1/4, -1/8]  (offsets -2..2, DC gain 1)
    h1 = [-1/2, 1, -1/2]              (offsets 0..2,  Nyquist gain 2)
Synthesis (inverse) filters, measured from the inverse transform:
    g0 = [1/2, 1, 1/2]                (hat interpolator)
    g1 = [-1/8, -1/4, 3/4, -1/4, -1/8]

The synthesis scaling function is the linear B-spline (hat) and the synthesis
wavelet is piecewise linear.  The analysis scaling function lies in L2 but is
unbounded: the cascade iterates grow by 1/2 per refinement.  The 2-D atoms
are inverse transforms of a single coefficient placed in LL3, LH3, HL3, HH3.

Run:  python examples/ex04_filters_and_wavelets.py -> figures/examples/04_filters_and_wavelets.png
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import figstyle as fs  # noqa: E402
from dwt import inverse1, reconstruct  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

H0 = (np.array([-1, 2, 6, 2, -1]) / 8, np.arange(-2, 3))
H1 = (np.array([-1, 2, -1]) / 2, np.arange(0, 3))


def synthesis_taps():
    """Impulse responses of the 1-D inverse step (s- and d-channel)."""
    n = 32
    out = []
    for pos in (8, n // 2 + 8):
        c = np.zeros(n)
        c[pos] = 1
        x = inverse1(c)
        nz = np.nonzero(np.abs(x) > 1e-14)[0]
        out.append((x[nz], nz - (2 * 8 if pos == 8 else 2 * 8 + 1)))
    return out


def synthesis_function(kind: str, levels: int, n: int = 1024):
    """Sample the synthesis scaling function or wavelet on a 2**-levels grid.

    One coefficient (in the coarsest LL or detail band) is inverted through
    ``levels`` 1-D inverse steps of the implemented transform.
    """
    c = np.zeros(n)
    m = (n >> levels) // 2                    # centre position in the coarse band
    c[m if kind == "scaling" else (n >> levels) + m] = 1.0
    y = c.copy()
    for k in reversed(range(levels)):
        size = n >> k
        y[:size] = inverse1(y[:size])
    t = (np.arange(n) - m * 2 ** levels) / 2 ** levels
    return t, y


def response(taps, offs, w):
    return np.abs(sum(t * np.exp(-1j * w * k) for t, k in zip(taps, offs)))


def cascade(taps, iters):
    v = np.array([1.0])
    for _ in range(iters):
        u = np.zeros(2 * len(v) - 1)
        u[::2] = v
        v = np.convolve(u, taps)
    return v


def line_panel(ax, w, lo, hi, title, lo_lab, hi_lab):
    ax.plot(w, lo, color=fs.CAT[0], label=lo_lab)
    ax.plot(w, hi, color=fs.CAT[1], label=hi_lab)
    ax.set_xlim(0, np.pi)
    ax.set_xticks([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi], ["0", "π/4", "π/2", "3π/4", "π"])
    ax.grid(True, axis="y")
    ax.set_title(title, loc="left", fontsize=10.5, pad=24)
    ax.set_xlabel("frequency ω (rad/sample)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, handlelength=1.4, borderaxespad=0.2)


def main():
    fs.setup()
    (g0, g0o), (g1, g1o) = synthesis_taps()
    assert np.allclose(g0, [0.5, 1, 0.5]) and np.allclose(g1, [-1 / 8, -1 / 4, 3 / 4, -1 / 4, -1 / 8])
    w = np.linspace(0, np.pi, 512)
    fig = plt.figure(figsize=(13.2, 9.6))
    gs = fig.add_gridspec(3, 4, left=0.055, right=0.99, top=0.855, bottom=0.03,
                          hspace=0.52, wspace=0.28, height_ratios=[1.0, 1.0, 1.0])

    # Row 1: 1-D responses and functions ------------------------------------
    a = fig.add_subplot(gs[0, 0])
    line_panel(a, w, response(*H0, w), response(*H1, w), "Analysis filters |H(ω)|",
               "h0 low-pass", "h1 high-pass")
    a.set_ylim(0, 2.1)
    b = fig.add_subplot(gs[0, 1])
    line_panel(b, w, response(g0, g0o, w), response(g1, g1o, w), "Synthesis filters |G(ω)|",
               "g0 low-pass", "g1 high-pass")
    b.set_ylim(0, 2.1)

    c = fig.add_subplot(gs[0, 2])
    J = 7
    t, phi = synthesis_function("scaling", J)
    _, psi = synthesis_function("wavelet", J)
    c.plot(t, phi, color=fs.CAT[0], label="scaling φ (hat)")
    c.plot(t, psi, color=fs.CAT[1], label="wavelet ψ")
    c.axhline(0, color=fs.AXIS, lw=0.8)
    c.set_xlim(-1.5, 2.5)
    c.set_ylim(-0.45, 1.12)
    c.grid(True, axis="y")
    c.set_title("Synthesis scaling & wavelet", loc="left", fontsize=10.5, pad=24)
    c.set_xlabel("t")
    c.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, handlelength=1.4, borderaxespad=0.2)

    d = fig.add_subplot(gs[0, 3])
    k_ref = 8
    v = cascade(2 * H0[0], k_ref)
    tt = (np.arange(len(v)) - (len(v) - 1) / 2) / 2 ** k_ref
    d.plot(tt, v, color=fs.CAT[0], lw=1.3, label=f"cascade, {k_ref} refinements")
    d.axhline(0, color=fs.AXIS, lw=0.8)
    d.set_xlim(-2.1, 2.1)
    d.grid(True, axis="y")
    d.set_title("Analysis scaling φ: in L², unbounded", loc="left", fontsize=10.5, pad=24)
    d.set_xlabel("t")
    d.legend(loc="lower left", bbox_to_anchor=(0, 1.0), handlelength=1.4, borderaxespad=0.2)
    d.text(0.02, 0.97, f"peak after k refinements = 1 + k/2\n‖φ‖₂ ≈ {np.sqrt(np.sum(v ** 2) / 2 ** k_ref):.2f}",
           transform=d.transAxes, ha="left", va="top", fontsize=8.5, color=fs.INK2,
           bbox=dict(boxstyle="round,pad=0.25", fc=fs.SURFACE, ec="none"))

    # Row 2: 2-D analysis magnitude responses ---------------------------------
    wy, wx = np.meshgrid(np.linspace(-np.pi, np.pi, 257), np.linspace(-np.pi, np.pi, 257), indexing="ij")
    resp = {"L": lambda v: response(*H0, v), "H": lambda v: response(*H1, v)}
    for k, band in enumerate(("LL", "LH", "HL", "HH")):
        ax = fig.add_subplot(gs[1, k])
        mag = resp[band[0]](wy) * resp[band[1]](wx)
        im = ax.imshow(mag, cmap=fs.SEQ, origin="lower", extent=[-np.pi, np.pi, -np.pi, np.pi],
                       vmin=0, vmax=mag.max())
        for v in (-np.pi / 2, np.pi / 2):
            ax.axvline(v, color=fs.SURFACE, lw=1.0)
            ax.axhline(v, color=fs.SURFACE, lw=1.0)
        ax.set_xticks([-np.pi, 0, np.pi], ["−π", "0", "π"])
        ax.set_yticks([-np.pi, 0, np.pi], ["−π", "0", "π"])
        ax.set_xlabel("ωx")
        if k == 0:
            ax.set_ylabel("ωy")
        ax.set_title(f"{band} analysis response · peak {mag.max():.2f}", loc="left", fontsize=10.5)
        for s in ax.spines.values():
            s.set_visible(False)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=8, length=0)

    # Row 3: 2-D synthesis atoms -----------------------------------------------
    n, lev = 64, 3
    s = n >> lev
    pos = {"LL": (s // 2, s // 2), "LH": (s // 2, s + s // 2), "HL": (s + s // 2, s // 2),
           "HH": (s + s // 2, s + s // 2)}
    for k, band in enumerate(("LL", "LH", "HL", "HH")):
        coef = np.zeros((n, n))
        coef[pos[band]] = 1.0
        atom = reconstruct(coef, lev)
        rr, cc = np.nonzero(np.abs(atom) > 1e-12)
        cy, cx = int(round(rr.mean())), int(round(cx_ := cc.mean()))
        half = 16
        crop = atom[cy - half:cy + half, cx - half:cx + half]
        lim = np.abs(crop).max()
        ax = fig.add_subplot(gs[2, k])
        ax.imshow(crop, cmap=fs.DIV, vmin=-lim, vmax=lim)
        fs.image_axis(ax)
        sup = (rr.max() - rr.min() + 1, cc.max() - cc.min() + 1)
        ax.set_title(f"{band}3 synthesis atom · support {sup[0]} × {sup[1]}", loc="left", fontsize=10.5)
    fs.title(fig, "CDF 5/3: filters, wavelets and 2-D basis images",
             "Rows: 1-D frequency responses and functions · 2-D analysis responses "
             "(white lines = ideal ±π/2 cut-offs) · inverse transform of one level-3 coefficient.")
    print("wrote", fs.save(fig, "04_filters_and_wavelets"))


if __name__ == "__main__":
    main()
