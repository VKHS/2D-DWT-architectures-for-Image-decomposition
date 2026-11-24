import argparse, time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from dwt import METHODS,decompose,reconstruct

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--image'); p.add_argument('--levels',type=int,default=3)
    p.add_argument('--out',default='outputs')
    a=p.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if a.image:
        x=np.asarray(Image.open(a.image).convert('L'),dtype=float)/255
    else:
        i,j=np.mgrid[:256,:256]; x=.15+.35*(j>100)+.3*((i-100)**2+(j-140)**2<55**2)+.12*np.sin(j*.6)*(i>150)
    n=2**a.levels; x=x[:x.shape[0]//n*n,:x.shape[1]//n*n]
    ref=decompose(x,a.levels,'fir')
    fig,ax=plt.subplots(2,4,figsize=(14,7)); ax=ax.ravel()
    ax[0].imshow(x,cmap='gray'); ax[0].set_title('Input')
    rows=['architecture,median_ms,max_coeff_error,rmse']
    for k,m in enumerate(METHODS):
        times=[]
        for _ in range(3):
            t=time.perf_counter(); c=decompose(x,a.levels,m); times.append(time.perf_counter()-t)
        z=reconstruct(c,a.levels)
        rows.append(f'{m},{1000*np.median(times):.6g},{np.max(abs(c-ref)):.6g},{np.sqrt(np.mean((z-x)**2)):.6g}')
        ax[k+1].imshow(np.sign(c)*np.log1p(20*abs(c)),cmap='coolwarm',vmin=-3,vmax=3); ax[k+1].set_title(m)
    ax[7].imshow(z,cmap='gray'); ax[7].set_title('Reconstruction')
    for b in ax: b.axis('off')
    fig.tight_layout(); fig.savefig(out/'comparison.png',dpi=180); plt.close(fig)
    (out/'metrics.csv').write_text('\n'.join(rows)+'\n')
    c=decompose(x,1); h,w=np.array(x.shape)//2
    fig,axs=plt.subplots(1,4,figsize=(12,3))
    for ax,band,name in zip(axs,[c[:h,:w],c[:h,w:],c[h:,:w],c[h:,w:]],['LL','LH','HL','HH']):
        ax.imshow(band,cmap='gray' if name=='LL' else 'coolwarm'); ax.set_title(name); ax.axis('off')
    fig.tight_layout(); fig.savefig(out/'subbands.png',dpi=180)
if __name__=='__main__': main()
