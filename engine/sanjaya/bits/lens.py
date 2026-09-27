"""Bit-Lens (D3): discover frame fields from decoded frames. Counters by increment tests, constant fields
by column constancy, and any CRC by GF(2) algebra: for two frames of equal length, the CRC difference
satisfies d_crc(x) = d_msg(x) * x^r mod g(x), so g divides T(x) = d_msg(x) * x^r + d_crc(x) and
g = gcd over frame pairs. The init follows from CRC = (M x^r + I x^L) mod g (checked in tests)."""
import numpy as np
from . import from_bits

WIDTHS = (32, 16, 8)


# --- GF(2)[x] with Python ints (bit i = coefficient of x^i) ---------------------------------------------
def pdeg(a: int) -> int:
    return a.bit_length() - 1


def pmod(a: int, g: int) -> int:
    dg = pdeg(g)
    while a and pdeg(a) >= dg:
        a ^= g << (pdeg(a) - dg)
    return a


def pgcd(a: int, b: int) -> int:
    while b:
        a, b = b, pmod(a, b)
    return a


def pmulmod(a: int, b: int, g: int) -> int:
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a = pmod(a << 1, g)
    return pmod(r, g)


def pinv(a: int, g: int) -> int | None:
    """Inverse of a modulo g (extended Euclid), None if not invertible."""
    r0, r1, s0, s1 = g, pmod(a, g), 0, 1
    while r1:
        q, r = 0, r0
        while r and pdeg(r) >= pdeg(r1):
            sh = pdeg(r) - pdeg(r1)
            q ^= 1 << sh
            r ^= r1 << sh
        r0, r1 = r1, r
        prod, t, qq = 0, s1, q
        while qq:
            if qq & 1:
                prod ^= t
            qq >>= 1
            t <<= 1
        s0, s1 = s1, s0 ^ prod
    return pmod(s0, g) if r0 == 1 else None


# --- field discovery ---------------------------------------------------------------------------------------
def find_counter(info: np.ndarray, slots: np.ndarray, min_frac: float = 0.9):
    """Rightmost-LSB span whose value increments with the frame slot. Returns (start, width) or None."""
    F, n = info.shape
    if F < 4:
        return None
    ds = np.diff(slots)
    best = None
    for e in range(n):
        if (info[:, e] == info[0, e]).all():
            continue                                               # an LSB must toggle
        for w in (32, 24, 16, 8):
            s = e - w + 1
            if s < 0:
                continue
            v = np.array([from_bits(r[s: e + 1]) for r in info], dtype=object)
            ok = [((b - a) % (1 << w)) == d % (1 << w) for a, b, d in zip(v, v[1:], ds)]
            if np.mean(ok) >= min_frac:
                best = (s, w)
                break
        if best:
            return best
    return None


def find_crc(info: np.ndarray, start: int = 0, pairs: int = 3):
    """Search every (position, width) for a CRC over info[start:pos] stored at info[pos:pos+w].
    Returns (pos, width, poly_normal, init) or None. Needs >= pairs+1 frames with distinct messages."""
    F, n = info.shape
    if F < pairs + 1:
        return None
    rows = [from_bits(r) for r in info]                          # whole frame as one integer, MSB = bit 0
    for w in WIDTHS:
        for pos in range(start + w, n - w + 1):
            L = pos - start
            g = 0
            for i in range(F - 1):                               # fold pairs until only degree w can remain
                d = (rows[i] ^ rows[i + 1]) >> (n - pos - w)     # bits [0, pos + w)
                dmsg, dcrc = (d >> w) & ((1 << L) - 1), d & ((1 << w) - 1)
                g = pgcd(g, (dmsg << w) ^ dcrc)
                if pdeg(g) <= w and i + 1 >= pairs:
                    break
            if pdeg(g) != w or not (g & 1):
                continue
            ok = True
            for i in range(pairs, F - 1):                        # confirm on every remaining pair
                d = (rows[i] ^ rows[i + 1]) >> (n - pos - w)
                dmsg, dcrc = (d >> w) & ((1 << L) - 1), d & ((1 << w) - 1)
                if pmod(dmsg << w, g) != dcrc:
                    ok = False
                    break
            if not ok:
                continue
            m0 = (rows[0] >> (n - pos)) & ((1 << L) - 1)
            c0 = (rows[0] >> (n - pos - w)) & ((1 << w) - 1)
            K = c0 ^ pmod(m0 << w, g)
            inv = pinv(pmod(1 << L, g), g)
            init = pmulmod(K, inv, g) if inv is not None else None
            if init is not None:
                return pos, w, g ^ (1 << w), init
    return None


def constant_runs(info: np.ndarray, exclude: set[int]) -> list[tuple[int, int, int]]:
    """Maximal runs of columns identical across all frames: (start, width, value)."""
    const = (info == info[0]).all(0)
    runs, s = [], None
    for i in range(info.shape[1] + 1):
        c = i < info.shape[1] and const[i] and i not in exclude
        if c and s is None:
            s = i
        elif not c and s is not None:
            runs.append((s, i - s, from_bits(info[0, s:i])))
            s = None
    return runs
