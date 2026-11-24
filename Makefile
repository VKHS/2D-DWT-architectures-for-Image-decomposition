PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp
H ?= 8
W ?= 12
TILE ?= 2
IMAGE ?=
ARCHS := 0 1 2 3 4 5
.PHONY: test vectors software clean
software:
	$(PYTHON) python/test_dwt.py
vectors:
	$(PYTHON) hardware/golden.py --height $(H) --width $(W) $(if $(IMAGE),--image "$(IMAGE)")
test: software vectors
	@set -e; for a in $(ARCHS); do \
	  $(IVERILOG) -g2012 -s tb_dwt53 -Ptb_dwt53.ARCH=$$a -Ptb_dwt53.H=$(H) -Ptb_dwt53.W=$(W) -Ptb_dwt53.TILE=$(TILE) -o build/sim_$$a rtl/dwt53_frame.v rtl/dwt53_pair.v tb/tb_dwt53.v; \
	  $(VVP) build/sim_$$a; \
	done
clean:
	rm -rf build
