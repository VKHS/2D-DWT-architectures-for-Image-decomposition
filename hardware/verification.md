# Verification and deployment

**Author: Abdolvahab Khalili Sadaghiani** · ORCID [0000-0003-4870-2768](https://orcid.org/0000-0003-4870-2768)

## Four independent checks

| Check | Command | What it compares |
|---|---|---|
| Software schedules | `python python/test_dwt.py` | all six methods against the row-column FIR (random, constant and impulse arrays, 2 × 2 to 64 × 64, 1–3 levels, tile size 3) and perfect reconstruction |
| Integer oracle | `python hardware/golden.py` | independent outer-product Q6 masks against 64 × each software method on six test frames |
| RTL schedules | `python python/rtl_model.py --check` | a clock-by-clock replay of every RTL state: bit-exact against the oracle and clock counts against the formulas (9 sizes, all ARCH, all valid TILE) |
| RTL simulation | `make test` | Icarus Verilog runs `tb/tb_dwt53.v` for ARCH 0–5 |

The testbench drives six frames per architecture: zero, full scale, a border impulse, a checkerboard, a ramp, and random pixels (or your image with `IMAGE=`). It inserts an idle input cycle every seventh pixel and holds `out_ready` low every fifth output cycle. It checks every coefficient, every `out_index` and `out_last`, prints the compute clocks per frame, and fails on any mismatch or timeout.

```sh
make test                                   # 8 x 12, TILE 2
make test H=4 W=4 TILE=1                    # the worked example size
make test H=16 W=16 TILE=4
make test H=32 W=32 TILE=4 IMAGE=benchmarks/Cameraman.png
```

The [CI workflow](../.github/workflows/ci.yml) runs the software checks, the RTL model sweep, the RTL regression at three frame sizes and the MATLAB `test_all` (under Octave) on every push.

## Simulation results

Icarus Verilog, six frames per architecture and size, every coefficient, index and `out_last` compared with the integer oracle. Compute clocks as printed by the testbench:

| Frame, TILE | ARCH 0 | ARCH 1 | ARCH 2 | ARCH 3 | ARCH 4 | ARCH 5 |
|---|---:|---:|---:|---:|---:|---:|
| 8 × 12, 2 | 96 | 96 | 24 | 168 | 318 | 288 |
| 4 × 4, 1 | 16 | 16 | 4 | 28 | 104 | 48 |
| 16 × 16, 4 | 256 | 256 | 64 | 448 | 548 | 768 |

All 18 configurations pass bit-exact, and every count equals the closed-form schedule and the cycle-accurate model ([`python/rtl_model.py`](../python/rtl_model.py)).

## Synthesis

```sh
vivado -mode batch -source scripts/synth_vivado.tcl \
  -tclargs xcve2302-sfva784-1LP-e-S 0 16 16 4 5.0
```

The arguments are part, ARCH, H, W, TILE and the clock period in ns. The script writes post-synthesis utilisation and timing reports to `build/vivado_arch_<ARCH>/`. Start with small frames: the reference arrays have several reads per clock, which synthesis maps to distributed memory or replicated RAM.

## Gates before hardware deployment

1. Software, model and RTL regressions pass for the target dimensions.
2. Mid-frame reset, long back-pressure and back-to-back frames are simulated.
3. Inferred memories and arithmetic are inspected per ARCH at identical parameters.
4. Banked memories and registered stages are added where timing or area requires it, and the full regression is repeated after every change.
5. Post-route timing, utilisation, throughput and power are measured under a common workload on the board.

Benchmark images: [examples/README.md](../examples/README.md#your-own-images-and-the-classic-benchmark-suite).
