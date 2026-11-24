"""Decomposition galleries for synthetic patterns, scikit-image samples and local images.

Usage: python python/gallery.py [--natural] [--image FILE ...] [--size 256] [--out DIR]
"""
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

def draw(name, x, out):
    """Decomposition panel for one image: bands, 3-level pyramid, reconstruction.

    Asserts that all six schedules agree, then writes out/<name>.png.
    Detail bands share one robust symmetric scale (99.5th percentile);
    the pyramid uses a per-level scale with LL in gray.
    """
    import figstyle as fs
    fs.setup()
    c = decompose(x, 3, "fir")
    z = reconstruct(c, 3)
    for method in METHODS:
        np.testing.assert_allclose(decompose(x, 3, method), c, atol=1e-12)
    one = decompose(x, 1, "fir")
    h, w = np.array(x.shape) // 2
    bands = [one[:h, :w], one[:h, w:], one[h:, :w], one[h:, w:]]
    lim = max(1e-12, np.percentile(np.abs(np.concatenate([b.ravel() for b in bands[1:]])), 99.5))
    err = np.abs(z - x)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.9))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.06, hspace=0.16)
    panels = [(x, "Input", "gray", 0, 1), (bands[0], "LL  approximation", "gray", 0, 1),
              (bands[1], "LH  vertical edges", fs.DIV, -lim, lim), (bands[2], "HL  horizontal edges", fs.DIV, -lim, lim),
              (bands[3], "HH  diagonal detail", fs.DIV, -lim, lim)]
    for ax, (v, t, cm, lo, hi) in zip(axes.ravel(), panels):
        ax.imshow(v, cmap=cm, vmin=lo, vmax=hi)
        ax.set_title(t, loc="left", fontsize=10.5)
    ax = axes[1, 1]
    ax.imshow(fs.pyramid_rgb(c, 3))
    fs.draw_band_grid(ax, c.shape, 3, fontsize=7.5)
    ax.set_title("3-level pyramid", loc="left", fontsize=10.5)
    axes[1, 2].imshow(z, cmap="gray", vmin=0, vmax=1)
    axes[1, 2].set_title("Reconstruction", loc="left", fontsize=10.5)
    axes[1, 3].imshow(err, cmap=fs.SEQ, vmin=0, vmax=max(err.max(), 1e-15))
    axes[1, 3].set_title(f"|error|, max {err.max():.1e}", loc="left", fontsize=10.5)
    for a in axes.ravel():
        fs.image_axis(a)
    fs.title(fig, f"{name}: CDF 5/3 decomposition",
             "Six schedules checked equal; detail bands on one symmetric scale, red positive, blue negative.")
    fig.savefig(out / f"{name}.png", dpi=150, facecolor=fs.SURFACE)
    plt.close(fig)


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
