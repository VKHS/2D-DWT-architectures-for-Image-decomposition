# ARCH 3 — Five-row line buffer

**Compute: 7*N*/4 clocks · working store: 160*W* bits (5*W* words) · 6.25 frame reads per pixel · 5 reads per clock**

![Line buffer](../../figures/diagrams/arch_line.svg)

## Principle

For each output row pair *oy*, LINE_FILL filters the five source rows 2*oy*−2 … 2*oy*+2 (wrapped) horizontally into `linebuf`. Slot *lr* holds the low half in columns 0 … *W*/2−1 and the high half in *W*/2 … *W*−1. LINE_EMIT then visits all *W* packed columns: it reads the five slots, applies the vertical pair and writes output rows *oy* and *oy* + *H*/2.

## RTL mapping (states LINE_FILL, LINE_EMIT)

- LINE_FILL: `linebuf[lr*W+ox] <= lo8(pix(2*oy+lr-2, 2*ox-2), …)` and `linebuf[lr*W+ox+WW] <= hi8(…)`; `ox` advances fastest, then `lr`.
- LINE_EMIT: `coeff[oy*W+col_idx] <= lo8(linebuf[col_idx], linebuf[W+col_idx], …)` and the high pair into row `oy + H/2`.
- After the last column, `oy` advances and the controller returns to LINE_FILL, or enters DRAIN after the last group.

## Schedule

| Stage (per output row pair) | Clocks |
|---|---:|
| fill 5 slots × *W*/2 pairs | 5*W*/2 |
| emit *W* columns | *W* |
| × *H*/2 groups | 7*N*/4 total |

## Memory and ports

The intermediate store shrinks from *N* to 5*W* words (10 KiB instead of 1 MiB at 512 × 512). The RTL refills all five slots for every group, though consecutive groups share three source rows: each source row is filtered 2.5 times on average, and frame traffic is 6.25 reads per pixel, the same as the direct engine ([fingerprints](../../figures/examples/09_rtl_schedules.png)).

## Rotating buffer: the measured improvement

Keep the three shared rows with a circular slot pointer and filter only the two new rows per group:

| | RTL as implemented | Rotating buffer |
|---|---:|---:|
| clocks per group | 5*W*/2 + *W* | *W* + *W* |
| compute clocks per frame | 7*N*/4 | about *N* |
| frame reads per pixel | 6.25 | about 2.5 |
| buffer | 5*W* words | 5*W* words |

With periodic boundaries, the first group needs rows *H*−2 and *H*−1 and the last group needs row 0 again, so a streaming version adds a short prologue and epilogue (or keeps a copy of row 0's filtered result). Overlapping fill and emission with dual-ported slots would hide the fill entirely.

[All chapters](README.md) · [Performance](../performance.md) · [Handbook](../README.md)
