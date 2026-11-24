function test_all
%TEST_ALL  All six schedules against the row-column FIR and perfect
%   reconstruction, on random, constant and identity arrays from 2x2 to
%   64x64 with 1-3 levels and tile size 3. Runs in MATLAB and Octave.
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
