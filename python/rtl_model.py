"""Cycle-accurate, bit-true software model of ``rtl/dwt53_frame.v``.

The model replays the compute phase of the RTL controller clock by clock for
each of the six ``ARCH`` schedules.  Every clock reads exactly the logical
memory locations that the corresponding ``case(state)`` branch of the Verilog
reads, evaluates the same shift-add expressions (``lo8``, ``hi8``, ``pred2``)
and writes the same packed addresses.  It therefore provides

* the exact signed Q6 coefficients (``64 x`` the floating-point transform),
* the number of compute clocks between the last input handshake and the
  first ``out_valid`` (the value printed by ``tb/tb_dwt53.v``),
* the clock at which every output coefficient is written (dataflow order),
* logical access counts for every storage array (memory traffic).

It is an executable specification used to cross-check the RTL schedules, the
cycle formulas in the hardware handbook and the figures in ``figures/``.

Example
-------
>>> import numpy as np
>>> from rtl_model import simulate
>>> x = np.arange(64, dtype=np.int64).reshape(8, 8)
>>> trace = simulate(x, arch=3)
>>> trace.clocks          # 7N/4 for the five-row line buffer
112
"""
from __future__ import annotations

from dataclasses import dataclass, field
import argparse

import numpy as np

ARCH_NAMES = {
    0: "Row-column FIR",
    1: "Fused lifting",
    2: "Direct 2-D FIR",
    3: "Five-row line buffer",
    4: "Halo-tiled 2-D FIR",
    5: "Folded lifting",
}

# Numerator taps at offsets -2..+2 (scale 8 per 1-D pass).
LOW = (-1, 2, 6, 2, -1)
HIGH = (0, 0, -4, 8, -4)


def lo8(a, b, c, d, e):
    """Low-pass numerator: 8 x (-a/8 + b/4 + 3c/4 + d/4 - e/8)."""
    return -a + (b << 1) + (c << 2) + (c << 1) + (d << 1) - e


def hi8(c, d, e):
    """High-pass numerator: 8 x (d - (c + e)/2)."""
    return ((d << 1) - c - e) << 2


def pred2(e0, o0, e1):
    """Twice the lifting prediction residual, 2*o0 - e0 - e1."""
    return (o0 << 1) - e0 - e1


def wrap(k: int, n: int) -> int:
    """Periodic index, identical to the RTL ``wrap`` function."""
    return k % n


@dataclass
class Trace:
    """Result of one simulated frame."""

    arch: int
    coeff: np.ndarray                 # (H, W) signed Q6 packed output
    clocks: int                       # compute clocks
    write_clock: np.ndarray           # (H, W) clock that wrote each coefficient
    frame_reads: np.ndarray           # (H, W) logical reads of each pixel
    accesses: dict = field(default_factory=dict)  # store -> {"reads","writes"}
    peak_reads_per_clock: int = 0     # max distinct reads issued in one clock
    mid_write_clock: np.ndarray = None  # (H, W) clock that wrote each mid word (-1: never)
    states: list = field(default_factory=list)  # controller state of every compute clock

    @property
    def name(self) -> str:
        return ARCH_NAMES[self.arch]


class _Machine:
    """Shared state: storage arrays, clock counter and access bookkeeping."""

    def __init__(self, x: np.ndarray, arch: int):
        self.x = np.asarray(x, dtype=np.int64)
        self.h, self.w = self.x.shape
        self.arch = arch
        self.mid = np.zeros_like(self.x)
        self.coeff = np.zeros_like(self.x)
        self.write_clock = np.full(self.x.shape, -1, dtype=np.int64)
        self.mid_write_clock = np.full(self.x.shape, -1, dtype=np.int64)
        self.frame_reads = np.zeros(self.x.shape, dtype=np.int64)
        self.state = "SEP"
        self.states = []
        self.clock = 0
        self.acc = {}
        self.peak = 0
        self._reads_this_clock: set = set()

    # Bookkeeping -----------------------------------------------------------
    def _count(self, store: str, kind: str, n: int = 1):
        self.acc.setdefault(store, {"reads": 0, "writes": 0})[kind] += n

    def tick(self):
        """Close the current clock: count distinct reads, advance the clock."""
        self.peak = max(self.peak, len(self._reads_this_clock))
        for store, _ in self._reads_this_clock:
            self._count(store, "reads")
        self._reads_this_clock = set()
        self.states.append(self.state)
        self.clock += 1

    def read(self, store: str, addr, value):
        key = (store, addr)
        if key not in self._reads_this_clock:
            self._reads_this_clock.add(key)
            if store == "frame":
                self.frame_reads[addr] += 1
        return int(value)

    # Storage accessors -----------------------------------------------------
    def pix(self, r: int, c: int) -> int:
        rr, cc = wrap(r, self.h), wrap(c, self.w)
        return self.read("frame", (rr, cc), self.x[rr, cc])

    def axis_sample(self, vertical: bool, src: int, o: int, k: int) -> int:
        if vertical:
            r, c = wrap(k, self.h), o
        else:
            r, c = o, wrap(k, self.w)
        if src == 0:
            return self.read("frame", (r, c), self.x[r, c])
        return self.read("mid", (r, c), self.mid[r, c])

    def write(self, store: str, r: int, c: int, value: int):
        self._count(store, "writes")
        if store == "mid":
            self.mid[r, c] = value
            self.mid_write_clock[r, c] = self.clock + 1
        elif store == "coeff":
            self.coeff[r, c] = value
            self.write_clock[r, c] = self.clock + 1  # 1-based compute clock

    def trace(self) -> Trace:
        return Trace(self.arch, self.coeff, self.clock, self.write_clock,
                     self.frame_reads, self.acc, self.peak, self.mid_write_clock, self.states)


def _separable(m: _Machine):
    """ARCH 0, 1 and 5: state SEP with pass_no/outer_idx/inner_idx counters."""
    h, w, arch = m.h, m.w, m.arch
    hh, ww = h // 2, w // 2
    for pass_no in (0, 1):
        vertical = (pass_no == 0) if arch == 5 else (pass_no == 1)
        outer_n, inner_n = (w, hh) if vertical else (h, ww)
        dest = "mid" if pass_no == 0 else "coeff"
        for outer in range(outer_n):
            for inner in range(inner_n):
                def s(k):
                    return m.axis_sample(vertical, pass_no, outer, 2 * inner + k)
                if arch == 5:
                    saved_d = pred2(s(0), s(1), s(2))          # phase 0
                    m.tick()
                    saved_prev = pred2(s(-2), s(-1), s(0))     # phase 1
                    m.tick()
                    low, high = (s(0) << 3) + saved_d + saved_prev, saved_d << 2
                elif arch == 1:
                    dp = pred2(s(0), s(1), s(2))
                    low, high = (s(0) << 3) + pred2(s(-2), s(-1), s(0)) + dp, dp << 2
                else:
                    low = lo8(s(-2), s(-1), s(0), s(1), s(2))
                    high = hi8(s(0), s(1), s(2))
                if vertical:
                    (lr, lc), (hr, hc) = (inner, outer), (inner + hh, outer)
                else:
                    (lr, lc), (hr, hc) = (outer, inner), (outer, inner + ww)
                m.write(dest, lr, lc, low)
                m.write(dest, hr, hc, high)
                m.tick()


def _direct_band(get, r: int, c: int, vb: int, hb: int) -> int:
    vt, ht = (LOW, HIGH)[vb], (LOW, HIGH)[hb]
    acc = 0
    for k in range(-2, 3):
        for l in range(-2, 3):
            wgt = vt[k + 2] * ht[l + 2]
            if wgt:
                acc += wgt * get(r + k, c + l)
    return acc


def _emit_quartet(m: _Machine, y: int, xcol: int, get, pr: int, pc: int):
    hh, ww = m.h // 2, m.w // 2
    for vb in (0, 1):
        for hb in (0, 1):
            m.write("coeff", y + vb * hh, xcol + hb * ww,
                    _direct_band(get, pr, pc, vb, hb))


def _direct(m: _Machine):
    """ARCH 2: state DIRECT, one quartet per clock, ox fastest."""
    m.state = "DIRECT"
    for oy in range(m.h // 2):
        for ox in range(m.w // 2):
            # Every 5x5 position is fetched once per clock, as in the RTL.
            for k in range(-2, 3):
                for l in range(-2, 3):
                    m.pix(2 * oy + k, 2 * ox + l)
            _emit_quartet(m, oy, ox, m.pix, 2 * oy, 2 * ox)
            m.tick()


def _line(m: _Machine):
    """ARCH 3: LINE_FILL (5 rows x W/2 pairs) then LINE_EMIT (W columns)."""
    h, w = m.h, m.w
    hh, ww = h // 2, w // 2
    linebuf = np.zeros((5, w), dtype=np.int64)
    for oy in range(hh):
        m.state = "LINE_FILL"
        for lr in range(5):
            r = 2 * oy + lr - 2
            for ox in range(ww):
                v = [m.pix(r, 2 * ox + k) for k in range(-2, 3)]
                linebuf[lr, ox] = lo8(*v)
                linebuf[lr, ox + ww] = hi8(v[2], v[3], v[4])
                m._count("linebuf", "writes", 2)
                m.tick()
        m.state = "LINE_EMIT"
        for col in range(w):
            v = [m.read("linebuf", (lr, col), linebuf[lr, col]) for lr in range(5)]
            m.write("coeff", oy, col, lo8(*v))
            m.write("coeff", oy + hh, col, hi8(v[2], v[3], v[4]))
            m.tick()


def _tile(m: _Machine, tile: int):
    """ARCH 4: TILE_FILL (P x P pixels) then TILE_EMIT (T x T quartets)."""
    hh, ww = m.h // 2, m.w // 2
    if tile < 1 or hh % tile or ww % tile:
        raise ValueError("ARCH 4 requires H/2 and W/2 divisible by TILE")
    p = 2 * tile + 3
    patch = np.zeros((p, p), dtype=np.int64)
    for ty in range(0, hh, tile):
        for tx in range(0, ww, tile):
            m.state = "TILE_FILL"
            for py in range(p):
                for px in range(p):
                    patch[py, px] = m.pix(2 * ty + py - 2, 2 * tx + px - 2)
                    m._count("patch", "writes")
                    m.tick()

            def get(r, c):
                return m.read("patch", (r, c), patch[r, c])
            m.state = "TILE_EMIT"
            for py in range(tile):
                for px in range(tile):
                    for k in range(-2, 3):
                        for l in range(-2, 3):
                            get(2 * py + 2 + k, 2 * px + 2 + l)
                    _emit_quartet(m, ty + py, tx + px, get, 2 * py + 2, 2 * px + 2)
                    m.tick()


def simulate(x, arch: int, tile: int = 2) -> Trace:
    """Replay the compute phase of ``dwt53_frame`` for one frame.

    Parameters
    ----------
    x : array_like of int, shape (H, W)
        Unsigned 8-bit pixels; H and W even.
    arch : int
        RTL ``ARCH`` parameter, 0..5.
    tile : int
        RTL ``TILE`` parameter (used by ARCH 4).
    """
    x = np.asarray(x, dtype=np.int64)
    if x.ndim != 2 or min(x.shape) < 2 or x.shape[0] % 2 or x.shape[1] % 2:
        raise ValueError("even H, W >= 2 required")
    if arch not in ARCH_NAMES:
        raise ValueError("arch must be 0..5")
    m = _Machine(x, arch)
    if arch in (0, 1, 5):
        _separable(m)
    elif arch == 2:
        _direct(m)
    elif arch == 3:
        _line(m)
    else:
        _tile(m, tile)
    return m.trace()


def compute_clocks(h: int, w: int, arch: int, tile: int = 2) -> int:
    """Closed-form compute clocks from the hardware handbook."""
    n = h * w
    p = 2 * tile + 3
    return {0: n, 1: n, 2: n // 4, 3: 7 * n // 4,
            4: (n // (4 * tile * tile)) * (p * p + tile * tile), 5: 3 * n}[arch]


def working_bits(h: int, w: int, arch: int, tile: int = 2) -> int:
    """Logical working-store bits beyond the input frame and output store."""
    p = 2 * tile + 3
    return {0: 32 * h * w, 1: 32 * h * w, 2: 0, 3: 32 * 5 * w,
            4: 8 * p * p, 5: 32 * h * w + 64}[arch]


def _self_check(verbose: bool = True) -> None:
    """Sweep sizes and tiles; compare with the integer oracle and formulas."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hardware"))
    from golden import q6

    rng = np.random.default_rng(2026)
    shapes = [(2, 2), (2, 4), (4, 4), (4, 6), (6, 4), (8, 12), (12, 8), (16, 16), (24, 32)]
    checked = 0
    for h, w in shapes:
        frames = [rng.integers(0, 256, size=(h, w)), np.full((h, w), 255), np.zeros((h, w), int)]
        for x in frames:
            ref = q6(x)
            for arch in range(6):
                tiles = [t for t in (1, 2, 3, 4) if (h // 2) % t == 0 and (w // 2) % t == 0] if arch == 4 else [2]
                for t in tiles:
                    tr = simulate(x, arch, t)
                    assert np.array_equal(tr.coeff, ref), (h, w, arch, t)
                    assert tr.clocks == compute_clocks(h, w, arch, t), (h, w, arch, t, tr.clocks)
                    assert (tr.write_clock > 0).all(), (h, w, arch, t)
                    checked += 1
    if verbose:
        print(f"RTL model: {checked} frame/architecture/tile runs bit-exact with the Q6 oracle;"
              " all compute-clock counts match the closed-form schedule.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--height", type=int, default=16)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--tile", type=int, default=2)
    ap.add_argument("--check", action="store_true", help="run the full self-check sweep")
    a = ap.parse_args()
    if a.check:
        _self_check()
        return
    rng = np.random.default_rng(53)
    x = rng.integers(0, 256, size=(a.height, a.width))
    n = a.height * a.width
    print(f"{a.height}x{a.width} frame, N={n}, TILE={a.tile}")
    print(f"{'ARCH':>4}  {'architecture':22s} {'clocks':>8} {'clocks/N':>8} {'frame reads/N':>13} {'peak reads/clk':>14}")
    for arch in range(6):
        tr = simulate(x, arch, a.tile)
        fr = tr.accesses.get("frame", {}).get("reads", 0)
        print(f"{arch:>4}  {tr.name:22s} {tr.clocks:>8} {tr.clocks / n:>8.3f} {fr / n:>13.3f} {tr.peak_reads_per_clock:>14}")


if __name__ == "__main__":
    main()
