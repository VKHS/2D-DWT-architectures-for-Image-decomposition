"""Floating-point CDF 5/3, periodic boundaries, even dimensions."""
import numpy as np
METHODS = ('fir','lifting','direct2d','line','tile','folded')
TAPS = (([-2,-1,0,1,2],[-.125,.25,.75,.25,-.125]),([0,1,2],[-.5,1.,-.5]))

def fir(x):
    n=x.shape[-1]; i=np.arange(0,n,2)
    return np.concatenate([sum(c*x[..., (i+k)%n] for k,c in zip(ks,cs)) for ks,cs in TAPS],axis=-1)

def lift(x):
    e=x[...,::2]; o=x[...,1::2]
    d=o-.5*(e+np.roll(e,-1,axis=-1))
    s=e+.25*(d+np.roll(d,1,axis=-1))
    return np.concatenate((s,d),axis=-1)

def inverse1(x):
    s,d=np.split(x,2,axis=-1)
    e=s-.25*(d+np.roll(d,1,axis=-1))
    o=d+.5*(e+np.roll(e,-1,axis=-1))
    y=np.empty_like(x); y[...,::2]=e; y[...,1::2]=o
    return y

def forward(x,method='lifting',tile=16):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or min(x.shape)<2 or any(n%2 for n in x.shape):
        raise ValueError('Expected a nonempty even-sized 2-D image')
    h,w=x.shape; H,W=h//2,w//2
    if method in ('fir','lifting'):
        f=fir if method=='fir' else lift
        return f(f(x).T).T
    y=np.empty_like(x)
    if method=='direct2d':
        i=np.arange(0,h,2); j=np.arange(0,w,2)
        for b,(ks,cs) in enumerate(TAPS):
            for a,(ls,ds) in enumerate(TAPS):
                y[b*H:(b+1)*H,a*W:(a+1)*W]=sum(c*d*x[np.ix_((i+k)%h,(j+l)%w)] for k,c in zip(ks,cs) for l,d in zip(ls,ds))
    elif method=='line':
        from collections import OrderedDict
        cache=OrderedDict()
        def row(i):
            i%=h
            if i not in cache:
                cache[i]=fir(x[i])
                if len(cache)>5: cache.popitem(last=False)
            cache.move_to_end(i)
            return cache[i]
        for i in range(H):
            for b,(ks,cs) in enumerate(TAPS):
                y[b*H+i]=sum(c*row(2*i+k) for k,c in zip(ks,cs))
    elif method=='tile':
        if tile<1: raise ValueError('tile must be positive')
        for i in range(0,H,tile):
            for j in range(0,W,tile):
                ii=2*np.arange(i,min(i+tile,H)); jj=2*np.arange(j,min(j+tile,W))
                # Shared global halo; never extend at internal tile boundaries.
                patch=x[np.ix_((np.arange(ii[0]-2,ii[-1]+3))%h,(np.arange(jj[0]-2,jj[-1]+3))%w)]
                for b,(ks,cs) in enumerate(TAPS):
                    for a,(ls,ds) in enumerate(TAPS):
                        y[b*H+i:b*H+i+len(ii),a*W+j:a*W+j+len(jj)]=sum(c*d*patch[np.ix_(ii-ii[0]+2+k,jj-jj[0]+2+l)] for k,c in zip(ks,cs) for l,d in zip(ls,ds))
    elif method=='folded':
        # One logical 1-D worker reused serially, column-first.
        for j in range(w): y[:,j]=lift(x[:,j])
        for i in range(h): y[i]=lift(y[i])
    else: raise ValueError(method)
    return y

def decompose(x,levels=1,method='lifting'):
    y=np.array(x,dtype=float,copy=True)
    if y.ndim!=2 or not isinstance(levels,int) or levels<1 or min(y.shape)<2**levels or any(n%2**levels for n in y.shape):
        raise ValueError('Dimensions must be divisible by 2**levels')
    h,w=y.shape
    for _ in range(levels):
        y[:h,:w]=forward(y[:h,:w],method)
        h//=2; w//=2
    return y

def reconstruct(coeff,levels=1):
    y=np.array(coeff,dtype=float,copy=True)
    if y.ndim!=2 or not isinstance(levels,int) or levels<1 or min(y.shape)<2**levels or any(n%2**levels for n in y.shape): raise ValueError('Invalid dimensions/levels')
    for k in reversed(range(levels)):
        h,w=(n//2**k for n in y.shape)
        y[:h,:w]=inverse1(inverse1(y[:h,:w].T).T)
    return y
