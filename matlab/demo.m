function demo(imagefile,levels)
if nargin<2, levels=3; end
if nargin<1 || isempty(imagefile)
    [j,i]=meshgrid(0:255);
    x=.15+.35*(j>100)+.3*((i-100).^2+(j-140).^2<55^2)+.12*sin(j*.6).*(i>150);
else
    raw=imread(imagefile); x=double(raw);
    if ndims(x)==3, x=mean(x,3); end
    if isinteger(raw), x=x/double(intmax(class(raw))); end
end
n=2^levels; x=x(1:floor(size(x,1)/n)*n,1:floor(size(x,2)/n)*n);
methods={'fir','lifting','direct2d','line','tile','folded'};
ref=dwt2_arch(x,'fir',levels);
if ~exist('outputs','dir'), mkdir('outputs'); end
f=fopen('outputs/matlab_metrics.csv','w'); fprintf(f,'architecture,median_ms,max_coeff_error,rmse\n');
figure; subplot(2,4,1); imagesc(x); axis image off; title('Input');
for k=1:6
    times=zeros(1,3);
    for t=1:3, tic; c=dwt2_arch(x,methods{k},levels); times(t)=toc; end
    z=idwt2_arch(c,levels);
    fprintf(f,'%s,%.9g,%.9g,%.9g\n',methods{k},1000*median(times),max(abs(c(:)-ref(:))),sqrt(mean((z(:)-x(:)).^2)));
    subplot(2,4,k+1); imagesc(sign(c).*log1p(20*abs(c)),[-3 3]); axis image off; title(methods{k});
end
fclose(f); subplot(2,4,8); imagesc(z); axis image off; title('Reconstruction'); colormap gray;
saveas(gcf,'outputs/matlab_comparison.png');
end
