# Architecture and cost model

For an H×W frame, a separable level produces four H/2×W/2 bands. For J levels, the processed pixel count is HW sum(4^-j, j=0..J-1), less than 4HW/3. All methods retain HW coefficients overall.

## Arithmetic
For each pair, the direct 1-D FIR computes five low and three high tap products (eight nominal multiplications, six additions); two separable passes therefore use approximately 8HW nominal products per level. Lifting uses two constant multiplications and four additions/subtractions per pair, or 2HW multiplications per level. Direct 2-D filtering uses 25+15+15+9=64 products per output quartet, or 16HW products. The tiled method shares this count plus halo movement. Powers-of-two constants permit shifts in fixed-point hardware; the numbers are mathematical counts, not DSP requirements. Signs, zero terms, symmetry and common subexpressions can reduce costs.

## Intermediate storage
Full row-column implementations retain HW intermediate samples. The line model caches at most 5W horizontal samples, excluding input/output and transient vectors. For a tile of B×B coefficient locations, the raw patch contains at most (2B+3)^2 samples, including halos; global periodic indices avoid seams. The folded implementation uses one logical 1-D worker with a frame-sized in-place store plus temporary vectors. The software arrays do not model physical ports, pipeline registers or exact allocation.

## Deployment considerations
Use separate banks or dual-port SRAM for row/column passes, and determine coefficient word length by worst-case range and reconstruction error. For streaming designs, explicitly specify start/end boundaries, backpressure and row validity. For FPGA claims report post-route Fmax, LUT, FF, BRAM, DSP, achieved initiation interval, latency and measured power. No such measurements are included here.

## Validation
Tests compare every coefficient to the row-column FIR, reconstruct random/constant/impulse-like arrays, test rectangular and tiny dimensions, and check tile boundaries. An independent implementation or standard test vectors should be added before claiming standards compliance.
