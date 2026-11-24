"""Generate natural-image and synthetic decomposition galleries, no network required for local input."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dwt import METHODS,decompose,reconstruct

def synthetic(n):
    r,c=np.mgrid[:n,:n]
    return {
        "edges": np.clip(.18+.35*(c>n*.45)+.3*((r-n*.45)**2+(c-n*.65)**2<(n*.19)**2),0,1),
        "texture": .5+.35*np.sin(c*.65)*np.cos(r*.18),
        "checkerboard": ((r//8+c//8)%2).astype(float)
    }

def draw(name,x,out):
    c=decompose(x,3,"fir"); z=reconstruct(c,3)
    for method in METHODS:
        np.testing.assert_allclose(decompose(x,3,method),c,atol=1e-12)
    one=decompose(x,1,"fir"); h,w=np.array(x.shape)//2
    bands=[one[:h,:w],one[:h,w:],one[h:,:w],one[h:,w:]]
    lim=max(1e-12,max(np.max(abs(b)) for b in bands[1:]))
    fig,axes=plt.subplots(2,4,figsize=(13,6.5),layout="constrained")
    entries=[(x,"Input","gray",0,1),(bands[0],"LL","gray",0,1)]
    entries.extend((b,t,"RdBu_r",-lim,lim) for b,t in zip(bands[1:],["LH","HL","HH"]))
    entries.extend([(np.sign(c)*np.log1p(20*abs(c)),"3-level pyramid","RdBu_r",-3,3),
                    (z,"Reconstruction","gray",0,1),
                    (abs(z-x),"Absolute error","magma",0,1e-12)])
    for ax,(v,t,cm,lo,hi) in zip(axes.ravel(),entries):
        ax.imshow(v,cmap=cm,vmin=lo,vmax=hi); ax.set_title(t); ax.axis("off")
    fig.suptitle(f"{name}: CDF 5/3 | max reconstruction error {np.max(abs(z-x)):.2e}")
    fig.savefig(out/f"{name}.png",dpi=180); plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--image",action="append",default=[],help="Repeat for local files, e.g. Lena")
    p.add_argument("--natural",action="store_true",help="Use scikit-image benchmark images")
    p.add_argument("--size",type=int,default=256)
    p.add_argument("--out",default="outputs/gallery")
    a=p.parse_args()
    if a.size<8 or a.size%8: p.error("size must be divisible by 8")
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    images=synthetic(a.size)
    def convert(img):
        return np.asarray(img.convert("L").resize((a.size,a.size),Image.Resampling.BOX),dtype=float)/255
    if a.natural:
        from skimage import data
        for name,fn in [("camera",data.camera),("astronaut",data.astronaut),("cat",data.chelsea)]:
            images[name]=convert(Image.fromarray(fn()))
    for path in a.image:
        images["local_"+Path(path).stem]=convert(Image.open(path))
    for name,x in images.items(): draw(name,x,out)
    print(f"Wrote {len(images)} galleries to {out}")
if __name__=="__main__": main()
