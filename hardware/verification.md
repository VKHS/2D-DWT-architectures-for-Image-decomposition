# Verification and FPGA deployment guide

## Functional regression

From the repository root, install requirements and Icarus Verilog, then run:

```sh
make test
make test H=4 W=4 TILE=1
make test H=16 W=16 TILE=4
make test H=32 W=32 TILE=4 IMAGE=benchmarks/Lena.png
```

The Python golden model independently computes four outer-product masks and checks exact coefficient equality against all six software implementations. The testbench compares every RTL coefficient, index and final marker, exercises six frames and uses deterministic input gaps and output stalls. A mismatch or timeout is fatal. Test patterns include zero, maximum constant, boundary impulse, checkerboard, ramp and seeded random or a local image. The simulator must actually be run to establish RTL correctness.

## Physical implementation

The existing Vivado script synthesizes a selected architecture and reports estimated timing and utilization. Use a modest H/W at first: the reference arrays expose many asynchronous reads and multiple writes, so large frame dimensions can create large multiplexers and distributed storage rather than inferred BRAM.

```sh
vivado -mode batch -source scripts/synth_vivado.tcl \
  -tclargs xcve2302-sfva784-1LP-e-S 0 16 16 4 5.0
```

The 5 ns period is a requested constraint, not a measured frequency. For actual deployment add a board-specific clock/reset and memory interface, perform implementation, inspect WNS/TNS, verify clock-domain assumptions and run board-level coefficient checks. No post-route or board measurements are included.

## Recommended next validation gates

1. Run Python and RTL regression across the dimensions above; archive logs.
2. Verify reset mid-frame, prolonged backpressure and repeated frames.
3. Inspect inferred storage and arithmetic for each architecture; compare utilization at the same parameter values.
4. Add explicit banked memory and registered compute stages if the target frequency or area is missed.
5. Repeat bit-true testing after every microarchitectural change.
6. Compare post-route timing, throughput and measured power under common workloads.

Image input support is documented in [the benchmark guide](../examples/README.md).
