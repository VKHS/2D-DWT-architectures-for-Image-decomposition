# Six hardware architecture chapters

**Project author and maintainer: Abdolvahab Khalili Sadaghiani (VKHS).**

Each chapter describes the implemented RTL, memory accesses, scheduling, arithmetic, controller signals, worked example, scaling implications and what would need to change for a production FPGA design.

| ARCH | Chapter | Schematic | Analytical summary |
|---:|---|---|---|
| 0 | [Row-column FIR](arch0.md) | [Full datapath](../../figures/hardware/arch0_row_column.svg) | Compute: N clocks · working store: 32N bits |
| 1 | [Fused predict–update lifting](arch1.md) | [Full datapath](../../figures/hardware/arch1_lifting.svg) | Compute: N clocks · working store: 32N bits |
| 2 | [Direct four-band 2-D FIR](arch2.md) | [Full datapath](../../figures/hardware/arch2_direct_2d.svg) | Compute: N/4 clocks · no full intermediate store |
| 3 | [Five-row buffered FIR](arch3.md) | [Full datapath](../../figures/hardware/arch3_line_buffered.svg) | Compute: 7N/4 clocks · working store: 160W bits |
| 4 | [Halo-tiled direct 2-D FIR](arch4.md) | [Full datapath](../../figures/hardware/arch4_halo_tiled.svg) | Compute: N(P²+T²)/(4T²) clocks · working store: 8P² bits |
| 5 | [Folded lifting with three-phase control](arch5.md) | [Full datapath](../../figures/hardware/arch5_folded_lifting.svg) | Compute: 3N clocks · working store: 32N bits + two 32-bit regs |

[Hardware handbook](../README.md) · [Common datapath and interface](../datapath.md) · [Cycle and memory analysis](../performance.md) · [Bit-true worked example](../worked_example.md) · [Verification and FPGA deployment](../verification.md).
