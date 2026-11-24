"""Independent exact outer-product CDF 5/3 reference and RTL test vectors."""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image

LOW=np.array([-1,2,6,2,-1],dtype=np.int64)
HIGH=np.array([0,0,-4,8,-4],dtype=np.int64)

def q6(x):
    x=np.asarray(x,dtype=np.int64)
    h,w=x.shape
    if h%2 or w%2 or min(h,w)<2:
        raise ValueError("even dimensions required")
    r=np.arange(0,h,2); c=np.arange(0,w,2)
    y=np.zeros_like(x)
    for v,vt in enumerate((LOW,HIGH)):
        for u,ut in enumerate((LOW,HIGH)):
            b=np.zeros((h//2,w//2),dtype=np.int64)
            for k in range(5):
                for l in range(5):
                    b+=vt[k]*ut[l]*x[np.ix_((r+k-2)%h,(c+l-2)%w)]
            y[v*h//2:(v+1)*h//2,u*w//2:(u+1)*w//2]=b
    return y

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--height",type=int,default=8)
    p.add_argument("--width",type=int,default=12)
    p.add_argument("--image",help="Optional grayscale test image, replaces random frame")
    p.add_argument("--out",default="build")
    a=p.parse_args()
    h,w=a.height,a.width
    if min(h,w)<2 or h%2 or w%2: p.error("even dimensions required")
    r,c=np.mgrid[:h,:w]
    impulse=np.zeros((h,w),dtype=np.int64); impulse[-1,0]=255
    rnd=np.random.default_rng(53).integers(0,256,size=(h,w),dtype=np.int64)
    if a.image: rnd=np.asarray(Image.open(a.image).convert("L").resize((w,h),Image.Resampling.BOX),dtype=np.int64)
    frames=[np.zeros((h,w),dtype=np.int64),np.full((h,w),255,dtype=np.int64),
            impulse,255*((r+c)%2),(17*r+31*c)%256,rnd]
    # Independent comparison with floating software reference.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"python"))
    from dwt import METHODS,forward
    for x in frames:
        y=q6(x)
        for m in METHODS:
            np.testing.assert_array_equal(y,64*forward(x,m))
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    (out/"pixels.hex").write_text("".join(f"{int(v):02x}\n" for x in frames for v in x.ravel()))
    (out/"golden.hex").write_text("".join(f"{int(v)&0xffffffff:08x}\n" for x in frames for v in q6(x).ravel()))
    print("Reference vectors generated; six software methods checked against Q6 oracle.")
if __name__=="__main__": main()
