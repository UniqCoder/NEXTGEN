"""Blind coding-layer identification (D1 v0, hard decisions).

Frame differences d = r_i xor r_j cancel a frame-synchronous additive scrambler, the fill and the constant
header, and every symbol-level phase ambiguity except the I/Q-bit swap (90 / 270 degrees). Under the right
de-interleaver, windows of the difference stream satisfy the code's parity checks, so the Walsh-Hadamard
transform of the window-pattern histogram peaks at the check vector h = (g1, g0) (dual-code recovery).
The scrambler is then solved in GF(2): the frame-majority syndrome equals syndrome(deinterleave(p)),
which is linear in the LFSR seed for each candidate polynomial."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from ..kernels.viterbi import gen_taps
from . import block_deinterleave, lfsr_sequence, syndrome_rate_half

K_MAX = 9
# Common additive scramblers (polynomial exponents), tried before the exhaustive low-degree search.
SCRAMBLER_LIBRARY = {
    "CCSDS TM randomiser": [8, 7, 5, 3, 0],
    "IEEE 802.11": [7, 4, 0],
    "DVB PRBS-15": [15, 14, 0],
    "ITU-T V.29 / O.151 PRBS-23": [23, 18, 0],
    "PRBS-9": [9, 5, 0],
    "PRBS-7": [7, 6, 0],
    "PRBS-11": [11, 9, 0],
}


def fwht(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float64).copy()
    n, h = a.size, 1
    while h < n:
        v = a.reshape(-1, 2, h)
        a = np.concatenate([v[:, 0] + v[:, 1], v[:, 0] - v[:, 1]], 1).reshape(n)
        h *= 2
    return a


def swap_pairs(bits: np.ndarray) -> np.ndarray:
    return bits.reshape(*bits.shape[:-1], -1, 2)[..., ::-1].reshape(bits.shape)


def dual_spectrum(rows: np.ndarray, W: int) -> tuple[np.ndarray, int]:
    """Bias E[(-1)^(h.x)] of every 2W-bit window pattern (windows start on code-bit pairs)."""
    R, n = rows.shape
    T = n // 2
    pairs = rows[:, : 2 * T].reshape(R, T, 2).astype(np.int64)
    acc = np.zeros((R, T - W + 1), np.int64)
    for s in range(W):
        for b in range(2):
            acc = (acc << 1) | pairs[:, s: s + T - W + 1, b]
    hist = np.bincount(acc.ravel(), minlength=1 << (2 * W))
    return fwht(hist) / acc.size, acc.size


@dataclass
class CodeHypothesis:
    swap: bool
    rows: int
    cols: int
    K: int
    generators_octal: list[str]
    bias: float                     # parity-check bias of the recovered check (1 = error-free)
    noise_level: float              # expected max |bias| of a random check at this data size
    runner_up: float                # best bias among all other interleaver hypotheses


def check_to_code(h: int, W: int):
    """Check vector over 2W bits -> (K, [g0 octal, g1 octal]); None if it is not a rate-1/2 conv check."""
    bit = lambda s, b: (h >> (2 * W - 1 - (2 * s + b))) & 1
    steps = [s for s in range(W) if bit(s, 0) or bit(s, 1)]
    if not steps:
        return None
    s0, s1 = steps[0], steps[-1]
    K = s1 - s0 + 1
    if K < 3:
        return None
    g0 = [bit(s1 - i, 1) for i in range(K)]                        # coefficient of c1[n-i] is g0[i]
    g1 = [bit(s1 - i, 0) for i in range(K)]                        # coefficient of c0[n-i] is g1[i]
    if not (g0[0] or g1[0]) or not (g0[-1] or g1[-1]) or sum(g0) == 0 or sum(g1) == 0:
        return None
    to_oct = lambda g: format(int("".join(map(str, g)), 2), "o")
    return K, [to_oct(g0), to_oct(g1)]


def divisors(n: int) -> list[int]:
    return [d for d in range(1, n + 1) if n % d == 0]


def _minimal_code(dd: np.ndarray, best: float):
    """The shortest window that still shows a check at (near) full bias -> (K, gens) or None."""
    for W in range(3, K_MAX + 1):
        spec, _ = dual_spectrum(dd, W)
        spec[0] = -1
        hw = int(spec.argmax())
        if spec[hw] >= 0.9 * best and (code := check_to_code(hw, W)) is not None:
            return code
    return None


def identify_code(frames_bits: np.ndarray) -> list[CodeHypothesis]:
    """frames_bits (F, Nc) hard channel bits of frame-aligned coded blocks (any scrambler, any rotation).
    Tries every block-interleaver geometry rows x cols = Nc (rows = 1 is 'no interleaver') and both
    I/Q-bit orders. Returns the best rate-1/2 conv hypothesis, plus its I/Q-swap twin when the twin is
    equally strong (e.g. no interleaver: (171,133) and (133,171) both fit); the scrambler stage decides."""
    F, Nc = frames_bits.shape
    if F < 3:
        return []
    d = frames_bits[1:] ^ frames_bits[:-1]
    scores = []
    for swap in (False, True):
        ds = swap_pairs(d) if swap else d
        for rows in divisors(Nc):
            spec, nwin = dual_spectrum(block_deinterleave(ds, rows, Nc // rows), K_MAX)
            spec[0] = -1
            scores.append((float(spec.max()), swap, rows, nwin))
    scores.sort(key=lambda t: -t[0])
    best, swap, rows, nwin = scores[0]
    noise = float(np.sqrt(2 * np.log(1 << (2 * K_MAX)) / nwin))
    same = {rows, Nc // rows} if rows in (1, Nc) else {rows}           # identity geometry has two spellings
    runner = next((t[0] for t in scores[1:] if t[2] not in same), 0.0)  # the I/Q-swap twin is a phase question
    out = []
    for sw in (swap, not swap):
        twin = max((t for t in scores if t[1] == sw and t[2] in same), key=lambda t: t[0])
        if sw != swap and twin[0] < 0.9 * best:
            continue
        dd = block_deinterleave(swap_pairs(d) if sw else d, rows, Nc // rows)
        code = _minimal_code(dd, twin[0])
        if code:
            out.append(CodeHypothesis(sw, rows, Nc // rows, code[0], code[1], twin[0], noise, runner))
    return out


# --- scrambler --------------------------------------------------------------------------------------------
def _gf2_solve(A: np.ndarray, b: np.ndarray):
    """Least-inconsistency solution of A s = b over GF(2) via elimination; returns (s, n_inconsistent)."""
    M = np.concatenate([A, b[:, None]], 1).astype(np.uint8)
    m, n = A.shape
    piv, r = [], 0
    for c in range(n):
        hit = np.nonzero(M[r:, c])[0]
        if hit.size == 0:
            continue
        p = r + hit[0]
        M[[r, p]] = M[[p, r]]
        mask = M[:, c].astype(bool)
        mask[r] = False
        M[mask] ^= M[r]
        piv.append(c)
        r += 1
        if r == m:
            break
    s = np.zeros(n, np.uint8)
    for i, c in enumerate(piv):
        s[c] = M[i, -1]
    return s, int((A @ s % 2 != b).sum())


@lru_cache(maxsize=4096)
def _lfsr_basis(exps: tuple[int, ...], n: int) -> np.ndarray:
    D = max(exps)
    return np.stack([lfsr_sequence(list(exps), 1 << (D - 1 - j), n) for j in range(D)])


def solve_scrambler(frames_bits: np.ndarray, code: CodeHypothesis, max_exhaustive_degree: int = 8,
                    polys: list[tuple[str, list[int]]] | None = None, library: bool = True):
    """Returns (name, poly_exponents, seed, inconsistent_checks) for the lowest-degree additive LFSR
    consistent with every frame, ('none', [], 0, 0) if the stream is unscrambled, or None."""
    F, Nc = frames_bits.shape
    gens = tuple(code.generators_octal)
    syn = syndrome_rate_half(block_deinterleave(frames_bits, code.rows, code.cols), code.K, gens)
    S = (syn.sum(0) * 2 > F).astype(np.uint8)                      # frame-majority syndrome = syndrome of p
    tol = max(2, int(0.01 * S.size))
    if S.sum() <= tol:
        return "none", [], 0, int(S.sum())

    def try_poly(exps):
        basis = _lfsr_basis(tuple(exps), Nc)
        A = syndrome_rate_half(block_deinterleave(basis, code.rows, code.cols), code.K, gens).T
        s, bad = _gf2_solve(A, S)
        if bad <= tol and s.any():
            return int("".join(map(str, s)), 2), bad
        return None

    cands = list(polys or []) + ([(name, e) for name, e in SCRAMBLER_LIBRARY.items()] if library else [])
    for D in range(2, max_exhaustive_degree + 1):
        for mid in range(1 << (D - 1)):
            exps = [D] + [i for i in range(D - 1, 0, -1) if (mid >> (i - 1)) & 1] + [0]
            cands.append((f"blind degree {D}", exps))
    found = []
    for name, exps in cands:
        r = try_poly(exps)
        if r:
            found.append((max(exps), name, exps, r[0], r[1]))
            if not name.startswith("blind degree"):
                break
    if not found:
        return None
    D, name, exps, seed, bad = min(found, key=lambda t: t[0])
    return name, exps, seed, bad


def edge_violations(frames_bits: np.ndarray, code: CodeHypothesis, exps: list[int], seed: int) -> int:
    """Parity checks at the block edges, assuming the encoder starts (and, if flushed, ends) in state 0:
    pad K-1 zero steps on both sides of each descrambled, de-interleaved block and count the violated
    edge checks (frame majority). The true block boundary gives 0; a shifted boundary starts mid-trellis."""
    F, Nc = frames_bits.shape
    p = lfsr_sequence(exps, seed, Nc) if exps else np.zeros(Nc, np.uint8)
    c = block_deinterleave(frames_bits ^ p[None], code.rows, code.cols)
    z = np.zeros((F, 2 * (code.K - 1)), np.uint8)
    full = syndrome_rate_half(np.concatenate([z, c, z], 1), code.K, tuple(code.generators_octal))
    edge = np.concatenate([full[:, : code.K - 1], full[:, -(code.K - 1):]], 1)
    return int((edge.sum(0) * 2 > F).sum())
