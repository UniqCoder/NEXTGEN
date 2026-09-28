"""Reed-Solomon over GF(2^m): systematic encode, hard-decision decode (Berlekamp-Massey + Chien + Forney).
Narrow-sense, generator roots alpha^1..alpha^(n-k), corrects up to t = (n-k)//2 symbol errors. n = 2^m - 1,
or shortened (k < 2^m - 1 - (n-k)) by encoding with high-order zero symbols and dropping them.

Codeword convention: msg/codeword arrays are HIGH-degree-first (msg[0] is the x^(k-1) coefficient, matching
the encoder's polynomial-division view); array index i therefore corresponds to exponent j = n-1-i.
Internally Lambda/Omega/syndromes use the more standard LOW-degree-first (index = exponent) convention."""
from functools import lru_cache
import numpy as np

PRIM_POLY = {3: 0b1011, 4: 0b10011, 5: 0b100101, 6: 0b1000011, 7: 0b10001001,
             8: 0b100011101, 9: 0b1000010001, 10: 0b10000001001}


@lru_cache(maxsize=8)
def gf_tables(m: int):
    size = 1 << m
    prim = PRIM_POLY[m]
    exp = np.zeros(2 * size, np.int64)
    log = np.zeros(size, np.int64)
    x = 1
    for i in range(size - 1):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & size:
            x ^= prim
    exp[size - 1: 2 * size - 2] = exp[: size - 1]
    return exp, log


def gf_mul(a: int, b: int, exp, log) -> int:
    return 0 if a == 0 or b == 0 else int(exp[log[a] + log[b]])


def gf_inv(a: int, exp, log, size: int) -> int:
    return int(exp[(size - 1 - log[a]) % (size - 1)])


def gf_pow(a: int, p: int, exp, log, size: int) -> int:
    return 0 if a == 0 else int(exp[(log[a] * p) % (size - 1)])


def eval_high(p: np.ndarray, x: int, exp, log) -> int:
    """Horner, p high-degree-first: sum p[i] x^(len-1-i)."""
    y = 0
    for c in p:
        y = gf_mul(y, x, exp, log) ^ int(c)
    return y


def eval_low(p: np.ndarray, x: int, exp, log) -> int:
    """Horner, p low-degree-first (index = exponent): sum p[i] x^i."""
    y = 0
    for c in p[::-1]:
        y = gf_mul(y, x, exp, log) ^ int(c)
    return y


def poly_mul_high(a: np.ndarray, b: np.ndarray, exp, log) -> np.ndarray:
    out = np.zeros(a.size + b.size - 1, np.int64)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    out[i + j] ^= gf_mul(int(ai), int(bj), exp, log)
    return out


@lru_cache(maxsize=32)
def generator(m: int, nk: int) -> tuple:
    """g(x) = product_{i=1}^{nk} (x - alpha^i), high-degree-first."""
    exp, log = gf_tables(m)
    g = np.array([1], np.int64)
    for i in range(1, nk + 1):
        g = poly_mul_high(g, np.array([1, int(exp[i])], np.int64), exp, log)
    return tuple(int(c) for c in g)


def bits_to_symbols(bits: np.ndarray, m: int) -> np.ndarray:
    """bits (..., N*m) -> symbols (..., N), MSB-first per symbol."""
    b = bits.reshape(*bits.shape[:-1], -1, m)
    idx = np.zeros(b.shape[:-1], np.int64)
    for i in range(m):
        idx = (idx << 1) | b[..., i]
    return idx


def symbols_to_bits(syms: np.ndarray, m: int) -> np.ndarray:
    out = np.empty((*syms.shape, m), np.uint8)
    for i in range(m):
        out[..., i] = (syms >> (m - 1 - i)) & 1
    return out.reshape(*syms.shape[:-1], syms.shape[-1] * m)


def rs_encode(msg: np.ndarray, n: int, k: int, m: int) -> np.ndarray:
    """msg (..., k) symbols -> codeword (..., n) symbols = msg || parity."""
    exp, log = gf_tables(m)
    g = np.array(generator(m, n - k), np.int64)
    shifted = np.concatenate([msg, np.zeros((*msg.shape[:-1], n - k), msg.dtype)], -1)

    def remainder(row):
        r = row.astype(np.int64).copy()
        for i in range(row.size - (n - k)):
            c = int(r[i])
            if c:
                r[i: i + g.size] ^= np.array([gf_mul(c, int(gc), exp, log) for gc in g])
        return r[-(n - k):]

    flat = shifted.reshape(-1, shifted.shape[-1])
    par = np.stack([remainder(row) for row in flat]).reshape(*msg.shape[:-1], n - k)
    return np.concatenate([msg, par], -1)


def _berlekamp_massey(synd: np.ndarray, exp, log) -> np.ndarray:
    """synd[i] = S_{i+1}, low-degree-first. Returns Lambda(x), low-degree-first (Lambda[0] = 1)."""
    C, B = np.array([1], np.int64), np.array([1], np.int64)
    L, m_, b = 0, 1, 1
    for i in range(synd.size):
        delta = int(synd[i])
        for j in range(1, L + 1):
            delta ^= gf_mul(int(C[j]), int(synd[i - j]), exp, log)
        if delta == 0:
            m_ += 1
            continue
        coef = gf_mul(delta, gf_inv(b, exp, log, exp.size // 2), exp, log)
        shiftB = np.concatenate([np.zeros(m_, np.int64), B])
        add = np.array([gf_mul(coef, int(c), exp, log) for c in shiftB])
        T = np.zeros(max(C.size, add.size), np.int64)
        T[: C.size] ^= C
        T[: add.size] ^= add
        if 2 * L <= i:
            L, B, b, m_ = i + 1 - L, C, delta, 1
        else:
            m_ += 1
        C = T
    return C


def rs_decode(recv: np.ndarray, n: int, k: int, m: int) -> tuple[np.ndarray, np.ndarray]:
    """recv (F, n) symbols, high-degree-first -> (decoded msg (F, k), ok (F,)). ok is False when the frame
    has more than t = (n-k)//2 errors (or an inconsistent locator); those frames are returned uncorrected."""
    exp, log = gf_tables(m)
    size = 1 << m
    nk = n - k
    t = nk // 2
    F = recv.shape[0]
    out = recv.copy()
    ok = np.zeros(F, bool)
    for f in range(F):
        r = recv[f]
        synd = np.array([eval_high(r, int(exp[j]), exp, log) for j in range(1, nk + 1)], np.int64)
        if not synd.any():
            ok[f] = True
            continue
        Lam = _berlekamp_massey(synd, exp, log)
        deg = int(np.nonzero(Lam)[0].max()) if Lam.any() else 0
        if deg > t or deg == 0:
            continue
        err_i = [i for i in range(n) if eval_low(Lam, gf_pow(int(exp[1]), -(n - 1 - i) % (size - 1), exp, log, size), exp, log) == 0]
        if len(err_i) != deg:
            continue
        # Omega(x) = Lambda(x) * S(x) mod x^nk, both low-degree-first.
        Om_full = poly_mul_high(Lam[::-1], synd[::-1], exp, log)[::-1]      # reuse high-degree mul then flip
        Om = Om_full[:nk]
        Lam_deriv = np.array([Lam[i] if i % 2 == 1 else 0 for i in range(1, Lam.size)], np.int64)
        corrected = r.copy()
        good = True
        for i in err_i:
            j = (n - 1 - i) % (size - 1)
            Xroot = gf_pow(int(exp[1]), -j, exp, log, size)          # the Chien-search root alpha^-i_l itself
            num = eval_low(Om, Xroot, exp, log)
            den = eval_low(Lam_deriv, Xroot, exp, log)
            if den == 0:
                good = False
                break
            corrected[i] ^= gf_mul(num, gf_inv(den, exp, log, size), exp, log)
        if not good:
            continue
        synd2 = np.array([eval_high(corrected, int(exp[j]), exp, log) for j in range(1, nk + 1)], np.int64)
        if not synd2.any():
            out[f], ok[f] = corrected, True
    return out[:, :k], ok
