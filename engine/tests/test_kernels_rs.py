"""Reed-Solomon kernel (GF(2^m), Berlekamp-Massey + Chien + Forney): round-trip with up to t errors."""
import numpy as np
import pytest
from sanjaya.kernels.rs import rs_encode, rs_decode


@pytest.mark.parametrize("m,n,k", [(4, 15, 9), (6, 63, 51), (8, 255, 223)])
def test_corrects_up_to_t_errors(m, n, k):
    rng = np.random.default_rng(0)
    t = (n - k) // 2
    msg = rng.integers(0, 1 << m, (30, k))
    cw = rs_encode(msg, n, k, m)
    recv = cw.copy()
    for row in recv:
        ne = rng.integers(0, t + 1)
        pos = rng.choice(n, size=ne, replace=False)
        row[pos] = (row[pos] + rng.integers(1, 1 << m, ne)) % (1 << m)
    dec, ok = rs_decode(recv, n, k, m)
    assert ok.all()
    assert (dec == msg).all()


def test_flags_uncorrectable():
    m, n, k = 4, 15, 9
    rng = np.random.default_rng(1)
    t = (n - k) // 2
    msg = rng.integers(0, 1 << m, (20, k))
    cw = rs_encode(msg, n, k, m)
    recv = cw.copy()
    for row in recv:                          # t+2 errors: beyond the guaranteed correction radius
        pos = rng.choice(n, size=t + 2, replace=False)
        row[pos] = (row[pos] + rng.integers(1, 1 << m, t + 2)) % (1 << m)
    dec, ok = rs_decode(recv, n, k, m)
    assert not ok.all()                       # at least some frames correctly flagged as uncorrectable
