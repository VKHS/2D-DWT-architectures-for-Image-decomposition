function y=idwt2_arch(c,levels)
%IDWT2_ARCH  Inverse of DWT2_ARCH (any method; they share the coefficients).
%   X = IDWT2_ARCH(C, LEVELS) undoes LEVELS levels of the packed periodic
%   CDF 5/3 decomposition C by inverse lifting (undo update, undo predict).
if nargin<2, levels=1; end
assert(ismatrix(c) && levels>=1 && fix(levels)==levels && all(size(c)>=2^levels) && all(mod(size(c),2^levels)==0));
y=double(c); [h,w]=size(y);
for k=levels-1:-1:0
    H=h/2^k; W=w/2^k;
    z=inv1(y(1:H,1:W).').';
    y(1:H,1:W)=inv1(z);
end
end
function y=inv1(x)
n=size(x,2)/2; s=x(:,1:n); d=x(:,n+1:end);
e=s-.25*(d+circshift(d,[0 1]));
o=d+.5*(e+circshift(e,[0 -1]));
y=zeros(size(x)); y(:,1:2:end)=e; y(:,2:2:end)=o;
end
