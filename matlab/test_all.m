function test_all
rng(17);
methods={'fir','lifting','direct2d','line','tile','folded'};
for shape={[2 2],[8 12],[32 48],[64 64]}
    sz=shape{1};
    for x={randn(sz),ones(sz),eye(sz)}
        for L=1:3
            if any(mod(sz,2^L)), continue; end
            ref=dwt2_arch(x{1},'fir',L);
            for m=methods
                c=dwt2_arch(x{1},m{1},L,3);
                assert(max(abs(c(:)-ref(:)))<1e-12);
                z=idwt2_arch(c,L);
                assert(max(abs(z(:)-x{1}(:)))<1e-12);
            end
        end
    end
end
disp('All tests passed');
end
