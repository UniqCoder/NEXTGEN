"""L6 coding layer: interleavers, scramblers, code-membership (syndrome) statistics."""
import numpy as np
from ..kernels.viterbi import gen_taps


def block_interleave(x: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Write row by row, read column by column. Works on the last axis; bits or LLRs."""
    return x.reshape(*x.shape[:-1], rows, cols).swapaxes(-1, -2).reshape(x.shape)


def block_deinterleave(y: np.ndarray, rows: int, cols: int) -> np.ndarray:
    return block_interleave(y, cols, rows)


def diagonal_perm(rows: int, cols: int) -> np.ndarray:
    """Helical/cross interleaver: write row-major into a rows x cols matrix, read row r's c-th slot
    from column (c + r) mod cols (a per-row cyclic shift). Bijective on rows*cols by construction."""
    r, c = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    return (r * cols + (c + r) % cols).reshape(-1)


def random_perm(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).permutation(n)


def _perm(kind: str, rows: int, cols: int, seed: int | None) -> np.ndarray:
    if kind == "diagonal":
        return diagonal_perm(rows, cols)
    if kind == "random":
        return random_perm(rows * cols, seed)
    raise ValueError(f"unknown interleaver kind '{kind}'")


def interleave(x: np.ndarray, kind: str, rows: int, cols: int, seed: int | None = None) -> np.ndarray:
    """Write x row by row into the rows x cols geometry, read out per 'kind'. Works on the last axis."""
    if kind == "block":
        return block_interleave(x, rows, cols)
    return x[..., _perm(kind, rows, cols, seed)]


def deinterleave(y: np.ndarray, kind: str, rows: int, cols: int, seed: int | None = None) -> np.ndarray:
    if kind == "block":
        return block_deinterleave(y, rows, cols)
    perm = _perm(kind, rows, cols, seed)
    inv = np.empty_like(perm)
    inv[perm] = np.arange(perm.size)
    return y[..., inv]


def lfsr_sequence(poly_exponents: list[int], seed: int, n: int) -> np.ndarray:
    """Additive (Fibonacci) scrambler sequence. Polynomial as exponents, e.g. CCSDS [8, 7, 5, 3, 0]
    with seed 0xFF gives FF 48 0E C0 9A ... (checked in tests)."""
    deg = max(poly_exponents)
    taps = [deg - e for e in poly_exponents if e != deg]         # register positions, 1 = newest
    s = [(seed >> (deg - 1 - i)) & 1 for i in range(deg)]
    out = np.empty(n, np.uint8)
    for k in range(n):
        out[k] = s[-1]
        fb = 0
        for t in taps:
            fb ^= s[t - 1]
        s = [fb] + s[:-1]
    return out


def syndrome_rate_half(hard: np.ndarray, K: int, gens: tuple[str, str]) -> np.ndarray:
    """Parity checks of a rate-1/2 conv code on hard coded bits (..., 2T): s = h0*g1 + h1*g0 (mod 2).
    Returns the syndrome bits that are fully inside the block (drops the first K-1)."""
    h0, h1 = hard[..., 0::2], hard[..., 1::2]
    g0, g1 = gen_taps(gens[0], K), gen_taps(gens[1], K)
    s = np.zeros_like(h0)
    for i in range(K):
        if g1[i]:
            s[..., i:] ^= h0[..., : h0.shape[-1] - i]
        if g0[i]:
            s[..., i:] ^= h1[..., : h1.shape[-1] - i]
    return s[..., K - 1:]


def check_weight(K: int, gens: tuple[str, ...]) -> int:
    return int(sum(gen_taps(g, K).sum() for g in gens))
