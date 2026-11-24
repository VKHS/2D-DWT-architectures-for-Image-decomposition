function y = dwt2_arch(x, method, levels, tile)
%DWT2_ARCH  Multilevel 2-D CDF 5/3 DWT with a selectable schedule.
%   Y = DWT2_ARCH(X, METHOD, LEVELS, TILE) decomposes the image X (even
%   dimensions divisible by 2^LEVELS) with periodic boundaries and returns
%   the packed coefficients [LL LH; HL HH], band names in (vertical,
%   horizontal) order, LL in pixel units. Each level re-decomposes LL.
%
%   METHOD  'fir'      row-column 5/3 FIR pairs            (RTL ARCH 0)
%           'lifting'  row-column predict/update lifting   (RTL ARCH 1)
%           'direct2d' four 5x5 outer-product masks        (RTL ARCH 2)
%           'line'     five cached filtered rows           (RTL ARCH 3)
%           'tile'     local patch with global halo, TILE  (RTL ARCH 4)
%           'folded'   one 1-D lifting worker, columns first (RTL ARCH 5)
%   All methods return the same coefficients. Defaults: 'lifting', 1, 16.
%   Inverse: IDWT2_ARCH. Author: Abdolvahab Khalili Sadaghiani.
if nargin<2, method='lifting'; end
if nargin<3, levels=1; end
if nargin<4, tile=16; end
assert(ismatrix(x) && levels>=1 && fix(levels)==levels && all(size(x)>=2^levels) && all(mod(size(x),2^levels)==0));
y=double(x); [h,w]=size(y);
for k=1:levels
    y(1:h,1:w)=one(y(1:h,1:w),method,tile);
    h=h/2; w=w/2;
end
end

function y=one(x,method,tile)
[h,w]=size(x); H=h/2; W=w/2;
ks={-2:2,0:2}; cs={[-.125 .25 .75 .25 -.125],[-.5 1 -.5]};
y=zeros(h,w);
switch method
case 'fir'
    y=fir1(fir1(x).').';
case 'lifting'
    y=lift1(lift1(x).').';
case 'folded'
    for j=1:w, y(:,j)=lift1(x(:,j).').'; end
    for i=1:h, y(i,:)=lift1(y(i,:)); end
case 'line'
    % Five-slot tagged row cache, slot = row mod 5; periodic random-access
    % input. Where the periodic wrap maps two needed rows to one slot, the
    % tag check simply refills it, so results are unaffected.
    cache=zeros(5,w); tags=zeros(1,5);
    for i=0:H-1
        for b=1:2
            acc=zeros(1,w);
            for p=1:numel(ks{b})
                idx=mod(2*i+ks{b}(p),h)+1; slot=mod(idx-1,5)+1;
                if tags(slot)~=idx, cache(slot,:)=fir1(x(idx,:)); tags(slot)=idx; end
                acc=acc+cs{b}(p)*cache(slot,:);
            end
            y((b-1)*H+i+1,:)=acc;
        end
    end
case {'direct2d','tile'}
    if strcmp(method,'direct2d'), tile=max(H,W); end
    assert(tile>=1 && fix(tile)==tile);
    for i=0:tile:H-1
        for j=0:tile:W-1
            ii=2*(i:min(i+tile-1,H-1)); jj=2*(j:min(j+tile-1,W-1));
            if strcmp(method,'tile')
                patch=x(mod(ii(1)-2:ii(end)+2,h)+1,mod(jj(1)-2:jj(end)+2,w)+1);
            end
            for b=1:2
                for a=1:2
                    acc=zeros(numel(ii),numel(jj));
                    for p=1:numel(ks{b})
                        for q=1:numel(ks{a})
                            if strcmp(method,'tile')
                                z=patch(ii-ii(1)+3+ks{b}(p),jj-jj(1)+3+ks{a}(q));
                            else
                                z=x(mod(ii+ks{b}(p),h)+1,mod(jj+ks{a}(q),w)+1);
                            end
                            acc=acc+cs{b}(p)*cs{a}(q)*z;
                        end
                    end
                    y((b-1)*H+i+(1:numel(ii)),(a-1)*W+j+(1:numel(jj)))=acc;
                end
            end
        end
    end
otherwise
    error('Unknown architecture');
end
end

function y=fir1(x)
n=size(x,2); i=0:2:n-1;
s=zeros(size(x,1),n/2); d=s;
ks=-2:2; cs=[-.125 .25 .75 .25 -.125];
for p=1:5, s=s+cs(p)*x(:,mod(i+ks(p),n)+1); end
d=x(:,i+2)-.5*(x(:,i+1)+x(:,mod(i+2,n)+1));
y=[s d];
end

function y=lift1(x)
e=x(:,1:2:end); o=x(:,2:2:end);
d=o-.5*(e+circshift(e,[0 -1]));
s=e+.25*(d+circshift(d,[0 1]));
y=[s d];
end
