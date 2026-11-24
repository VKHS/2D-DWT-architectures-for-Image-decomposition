# Performance

**Author: Abdolvahab Khalili Sadaghiani**

*N* = *H*·*W*, *T* = TILE, *P* = 2*T* + 3. Compute clocks run from the clock after the last input handshake to the first `out_valid`; LOAD and DRAIN add *N* handshakes each plus any stalls, and the three frame stages do not overlap. Every value below is reproduced clock by clock by [`python/rtl_model.py`](../python/rtl_model.py).

| ARCH | Compute clocks | Total, no stalls | Working bits | Frame reads / pixel | Reads / clock |
|---:|---:|---:|---:|---:|---:|
| 0 FIR | *N* | 3*N* | 32*N* | 2.50 | 5 |
| 1 lifting | *N* | 3*N* | 32*N* | 2.50 | 5 |
| 2 direct | *N*/4 | 9*N*/4 | 0 | 6.25 | 25 |
| 3 line | 7*N*/4 | 15*N*/4 | 160*W* | 6.25 | 5 |
| 4 tile | *N*(*P*² + *T*²)/(4*T*²) | 2*N* + compute | 8*P*² | *P*²/(4*T*²) | 25 |
| 5 folded | 3*N* | 5*N* | 32*N* + 64 | 3.50 | 3 |

For 256 × 256 and *T* = 8: 65,536, 65,536, 16,384, 114,688, 108,800 and 196,608 compute clocks. For tiles, 256 tiles × (361 + 64) = 108,800.

All architectures also hold the input frame (8*N* bits) and the output store (32*N* bits): 2,621,440 bits at 256 × 256. On top of that, the full intermediate adds 2,097,152 bits, the line buffer 40,960 and the tile patch 2,888.

Frame throughput at an achieved clock *f* is *f* / (2*N* + *C*) frames per second without stalls, where *C* is the compute-clock count above. Overlapping LOAD, compute and DRAIN across frames (double-buffered frame and output stores) would raise it to *f* / max(*N*, *C*).

![Cost model](../figures/examples/10_hardware_costs.png)

## Reading the trade-offs

- **Clock count and clock rate pull in opposite directions.** ARCH 2 needs a quarter of ARCH 0's clocks but evaluates 64 weighted terms with 25 reads in one clock.
- **Storage and traffic are different resources.** The line buffer cuts the intermediate from *N* to 5*W* words but, as implemented, reads the frame 6.25 times per pixel; tiles read it about once.
- **Folding trades time for ports.** ARCH 5 takes three times longer than ARCH 1 but never needs more than three reads in one clock.
- **Word length is a free win.** Final coefficients need 16 bits and first-pass values 13, against 32 in the reference.

The [cost model](../docs/architecture.md) collects these into concrete improvements with their measured effect. Synthesis and board results depend on the target device, clock constraint and memory mapping; [`scripts/synth_vivado.tcl`](../scripts/synth_vivado.tcl) produces them for a chosen part.
