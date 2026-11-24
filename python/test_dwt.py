import numpy as np
from dwt import METHODS, decompose, reconstruct, forward
def test_all():
    rng=np.random.default_rng(17)
    for shape in [(2,2),(8,12),(32,48),(64,64)]:
        for x in (rng.normal(size=shape),np.ones(shape),np.eye(*shape)):
            for level in range(1,4):
                if any(n%2**level for n in shape): continue
                ref=decompose(x,level,'fir')
                for method in METHODS:
                    c=decompose(x,level,method)
                    np.testing.assert_allclose(c,ref,atol=1e-12,rtol=1e-12)
                    np.testing.assert_allclose(reconstruct(c,level),x,atol=1e-12,rtol=1e-12)
            np.testing.assert_allclose(forward(x,'tile',3),forward(x,'fir'),atol=1e-12)
    x=np.ones((8,8)); c=forward(x)
    np.testing.assert_array_equal(c[:4,:4],1)
    assert np.count_nonzero(c)==16
if __name__=='__main__':
    test_all()
    print('All architecture equivalence and reconstruction tests passed')
