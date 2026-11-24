# ARCH 0 — Row-column FIR

**Compute: *N* clocks · working store: 32*N* bits · 2.50 frame reads per pixel · 5 reads per clock**

![Two-pass datapath](../../figures/diagrams/arch_separable.svg)

## Principle

The textbook schedule. Pass 0 treats every row as a 1-D signal: for pair *j* it reads the five wrapped samples at columns 2*j*−2 … 2*j*+2, computes `low8` and `high8` in the [FIR element](../../figures/diagrams/pe_fir.svg) and writes them to the left and right halves of `mid`. Pass 1 filters every packed column of `mid` the same way and writes the top and bottom halves of `coeff`. The column pass walks `mid` with stride *W* through the address generator, so no transposed copy is made.

## RTL mapping (`rtl/dwt53_frame.v`, state SEP)

- `vertical = (pass_no == 1)`; `axis_sample()` selects `frame` or `mid` and row or column indexing, `sample_k(k)` adds the offset.
- One clock per pair: `write_pair(lo8(sample_k(-2), …, sample_k(2)), hi8(sample_k(0), sample_k(1), sample_k(2)))`.
- `advance_pair()` steps `inner_idx`, then `outer_idx`, then the pass, then enters DRAIN.

## Schedule

| Stage | Clocks |
|---|---:|
| pass 0, rows | *N*/2 |
| pass 1, columns | *N*/2 |
| total compute | *N* |

The [write-order fingerprint](../../figures/examples/09_rtl_schedules.png) shows the consequence: no output coefficient exists before the second half of the compute time, and the second pass writes column by column.

## Memory and ports

Each clock issues 5 reads and 2 writes. Consecutive pairs overlap by three samples, so a five-register sliding window would cut fresh reads to 2 per clock along a row. The column pass reads with stride *W*: a single-port block RAM cannot serve it at one pair per clock without banking, a transpose buffer or a two-row read pattern.

## Where it fits and how to improve it

Simplest control and the reference for the others. In production: a sliding sample window, a banked or transposed `mid`, registered adder trees, and a 13-bit `mid` (first-pass values need 13 bits, [theory §9](../../docs/theory.md#9-exact-integer-arithmetic-the-rtl-contract)), which saves 59 % of the intermediate storage.

[All chapters](README.md) · [Performance](../performance.md) · [Handbook](../README.md)
