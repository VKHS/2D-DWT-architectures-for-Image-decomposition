"""Analysis helpers used by the examples (not part of the hardware contract).

* synthesis-norm subband weights, so that coefficient magnitudes can be
  ranked fairly in this non-orthonormal (DC-gain-1) normalisation;
* nonlinear approximation: keep the k largest weighted coefficients;
* a whole-sample symmetric-extension variant of the CDF 5/3 lifting steps
  (the JPEG 2000 boundary rule), used only to compare boundary handling.
"""
from __future__ import annotations

import numpy as np

from dwt import decompose, reconstruct


def band_weights(shape, levels: int) -> np.ndarray:
    """Per-coefficient L2 norm of its synthesis basis image.

    Computed by reconstructing a unit impulse placed in the centre of every
    band (periodic boundaries make all positions within a band equivalent).
    """
    h, w = shape
    wts = np.zeros(shape)
    regions = []
    for j in range(1, levels + 1):
        hh, ww = h >> j, w >> j
        regions += [(slice(0, hh), slice(ww, 2 * ww)), (slice(hh, 2 * hh), slice(0, ww)),
                    (slice(hh, 2 * hh), slice(ww, 2 * ww))]
    regions.append((slice(0, h >> levels), slice(0, w >> levels)))
    for rs, cs in regions:
        c = np.zeros(shape)
        c[(rs.start + rs.stop) // 2, (cs.start + cs.stop) // 2] = 1.0
        wts[rs, cs] = np.linalg.norm(reconstruct(c, levels))
    return wts


def keep_largest(x: np.ndarray, levels: int, fraction: float, weights=None,
                 transform=None, inverse=None) -> np.ndarray:
    """Reconstruct from the largest ``fraction`` of weighted coefficients."""
    transform = transform or (lambda v: decompose(v, levels, "lifting"))
    inverse = inverse or (lambda v: reconstruct(v, levels))
    c = transform(x)
    wts = band_weights(x.shape, levels) if weights is None else weights
    score = np.abs(c) * wts
    k = max(1, int(round(fraction * c.size)))
    thr = np.partition(score.ravel(), -k)[-k]
    return inverse(np.where(score >= thr, c, 0.0))


# Whole-sample symmetric extension (x[-k] = x[k], x[n-1+k] = x[n-1-k]) -------
def lift_sym(x: np.ndarray) -> np.ndarray:
    e, o = x[..., ::2], x[..., 1::2]
    e_next = np.concatenate((e[..., 1:], e[..., -1:]), axis=-1)       # e[N/2] = e[N/2-1]
    d = o - 0.5 * (e + e_next)
    d_prev = np.concatenate((d[..., :1], d[..., :-1]), axis=-1)       # d[-1] = d[0]
    s = e + 0.25 * (d_prev + d)
    return np.concatenate((s, d), axis=-1)


def inverse_sym(c: np.ndarray) -> np.ndarray:
    s, d = np.split(c, 2, axis=-1)
    d_prev = np.concatenate((d[..., :1], d[..., :-1]), axis=-1)
    e = s - 0.25 * (d_prev + d)
    e_next = np.concatenate((e[..., 1:], e[..., -1:]), axis=-1)
    o = d + 0.5 * (e + e_next)
    y = np.empty_like(c)
    y[..., ::2], y[..., 1::2] = e, o
    return y


def decompose_sym(x: np.ndarray, levels: int) -> np.ndarray:
    y = np.array(x, dtype=float, copy=True)
    h, w = y.shape
    for _ in range(levels):
        y[:h, :w] = lift_sym(lift_sym(y[:h, :w]).T).T
        h //= 2
        w //= 2
    return y


def reconstruct_sym(c: np.ndarray, levels: int) -> np.ndarray:
    y = np.array(c, dtype=float, copy=True)
    for k in reversed(range(levels)):
        h, w = (n // 2 ** k for n in y.shape)
        y[:h, :w] = inverse_sym(inverse_sym(y[:h, :w].T).T)
    return y


def _check():
    """Symmetric lifting equals FIR on a reflect-padded signal; PR holds."""
    rng = np.random.default_rng(5)
    x = rng.normal(size=(6, 16))
    lo = np.array([-1, 2, 6, 2, -1]) / 8
    hi = np.array([-1, 2, -1]) / 2
    xp = np.pad(x, ((0, 0), (2, 2)), mode="reflect")
    s = sum(lo[k] * xp[:, k:k + 16:2] for k in range(5))
    d = sum(hi[k] * xp[:, 2 + k:2 + k + 16:2] for k in range(3))
    assert np.allclose(lift_sym(x), np.concatenate((s, d), axis=1))
    img = rng.normal(size=(32, 48))
    assert np.allclose(reconstruct_sym(decompose_sym(img, 3), 3), img)
    print("symmetric-extension lifting: FIR-equivalent and perfectly reconstructing")


if __name__ == "__main__":
    _check()
