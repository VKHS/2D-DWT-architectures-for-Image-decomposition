# Usage: vivado -mode batch -source scripts/synth_vivado.tcl -tclargs <part> <arch> <H> <W> <TILE> <period_ns>
if {$argc != 6} { error "Expected part arch H W TILE period_ns" }
lassign $argv part arch h w tile period
if {$arch<0 || $arch>5 || $h<2 || $w<2 || $h%2 || $w%2 || $tile<1} { error "Invalid parameters" }
if {$arch==4 && (($h/2)%$tile || ($w/2)%$tile)} { error "Tile dimensions must divide subbands" }
file mkdir build/vivado_arch_$arch
read_verilog rtl/dwt53_frame.v
read_verilog rtl/dwt53_pair.v
synth_design -top dwt53_frame -part $part -generic "ARCH=$arch H=$h W=$w TILE=$tile"
create_clock -name clk -period $period [get_ports clk]
report_utilization -file build/vivado_arch_$arch/utilization_synth.rpt
report_timing_summary -file build/vivado_arch_$arch/timing_synth.rpt
write_checkpoint -force build/vivado_arch_$arch/post_synth.dcp
