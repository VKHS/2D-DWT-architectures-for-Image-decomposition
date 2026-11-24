# Build and verification targets.  Variables: H, W, TILE, IMAGE (RTL frame).
PYTHON   ?= python3
IVERILOG ?= iverilog
VVP      ?= vvp
H        ?= 8
W        ?= 12
TILE     ?= 2
IMAGE    ?=
ARCHS    := 0 1 2 3 4 5
EXAMPLES := $(sort $(wildcard examples/ex*.py))

.PHONY: all test software model vectors rtl figures thumbnails diagrams clean

all: test

## software: six schedules, reconstruction, symmetric-extension helper
software:
	$(PYTHON) python/test_dwt.py
	$(PYTHON) python/analysis_tools.py

## model: cycle-accurate RTL model against the integer oracle and the clock formulas
model:
	$(PYTHON) python/rtl_model.py --check

## vectors: test frames and Q6 reference for the testbench (build/)
vectors:
	$(PYTHON) hardware/golden.py --height $(H) --width $(W) $(if $(IMAGE),--image "$(IMAGE)")

## rtl: Icarus Verilog regression of all six ARCH values
rtl: vectors
	@set -e; mkdir -p build; for a in $(ARCHS); do \
	  $(IVERILOG) -g2012 -s tb_dwt53 -Ptb_dwt53.ARCH=$$a -Ptb_dwt53.H=$(H) -Ptb_dwt53.W=$(W) \
	    -Ptb_dwt53.TILE=$(TILE) -o build/sim_$$a rtl/dwt53_frame.v rtl/dwt53_pair.v tb/tb_dwt53.v; \
	  $(VVP) build/sim_$$a; \
	done

## test: everything that can be checked automatically
test: software model rtl

## figures: regenerate every computed figure (needs scikit-image)
figures:
	@set -e; for f in $(EXAMPLES); do echo "== $$f"; $(PYTHON) $$f; done

## diagrams: rebuild the TikZ block diagrams (needs XeLaTeX, Inter, pdftocairo)
thumbnails:
	$(PYTHON) figures/diagrams/tikz/make_thumbnails.py
diagrams: thumbnails
	figures/diagrams/build.sh

clean:
	rm -rf build outputs
