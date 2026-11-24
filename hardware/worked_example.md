# Bit-true worked example

**Project author and maintainer: Abdolvahab Khalili Sadaghiani (VKHS).**

The following 4×4 unsigned image is small enough to trace every operation by hand. Values are computed from the numerator taps; they are not simulator output.

## Input
```
     10      20      30      40
     50      60      70      80
     90     100     110     120
    130     140     150     160
```

The first row at j=0 uses a=30, b=40, c=10, d=20, e=30 due to periodic wrapping. L8=−30+80+60+40−30=120. H8=4(40−10−30)=0. The lifting prediction dm=80−30−10=40, dp=40−10−30=0; L8=80+40+0=120. At j=1, the low numerator is 200 and the high numerator is 160.

## Horizontal intermediate (scale ×8)
```
    120     280       0     160
    440     600       0     160
    760     920       0     160
   1080    1240       0     160
```

For the first packed column, the five vertical inputs at i=0 are 760,1080,120,440,760. L8=2560; H8=0. The resulting scale is ×64.

## Final packed output (scale ×64)
```
   2240    3520       0    1280
   7360    8640       0    1280
      0       0       0       0
   5120    5120       0       0
```

## Normalized coefficients
```
     35      55       0      20
    115     135       0      20
      0       0       0       0
     80      80       0       0
```

LL is top-left, LH top-right, HL bottom-left and HH bottom-right. The output port emits the signed numerator in row-major order; output index 0 therefore holds 2240. Negative coefficients, if present, are represented in signed two's complement.

## Controller trace for all six

For N=16, T=1 (tile variant), ARCH 0 and 1 each execute 8 horizontal and 8 vertical pair clocks; ARCH 2 emits 4 quartets; ARCH 3 fills 10 pair clocks and emits 4 vertical pairs for each of two groups (28 clocks total); ARCH 4 fills 25 samples and emits one quartet per tile, repeating four times (104 clocks); ARCH 5 performs 8 vertical pairs and 8 horizontal pairs, each in three clocks (48 clocks). All add 16 input and 16 output handshakes in a stall-free frame.

The first row's two pairs demonstrate periodic boundary handling. The tile variant uses identical global boundary coordinates before copying a local patch. Run `make test H=4 W=4 TILE=1` to test the general 4×4 configuration; the existing testbench generates its own six input frames, not this particular worked matrix.
