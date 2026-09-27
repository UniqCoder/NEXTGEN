"""Rate-1/n convolutional codes: encoder and batched soft-decision Viterbi (NumPy reference)."""
from functools import lru_cache
import numpy as np


def gen_taps(octal: str, K: int) -> np.ndarray:
    """Octal generator -> K taps, index 0 = current input (MSB convention: 171 -> 1111001)."""
    v = int(octal, 8)
    if v >> K:
        raise ValueError(f"generator {octal} has more than K={K} taps")
    return np.array([(v >> (K - 1 - i)) & 1 for i in range(K)], np.uint8)


@lru_cache(maxsize=64)
def trellis(K: int, gens: tuple[str, ...]):
    """State = previous K-1 inputs, newest in the MSB. Returns (pred_state (S,2), pred_input (S,), out (S,2,n))."""
    S, n = 1 << (K - 1), len(gens)
    G = np.array([gen_taps(g, K) for g in gens])
    ns = np.arange(S)
    b = ns >> (K - 2)                                           # input that led into state ns
    pred = ((ns & ((1 << (K - 2)) - 1)) << 1)[:, None] | np.arange(2)[None, :]
    reg = np.empty((S, 2, K), np.uint8)                         # [b, u[k-1], ..., u[k-K+1]]
    reg[..., 0] = b[:, None]
    for i in range(K - 1):
        reg[..., i + 1] = (pred >> (K - 2 - i)) & 1
    out = (reg[:, :, None, :] & G[None, None]).sum(-1) % 2      # (S, 2, n)
    return pred, b.astype(np.uint8), out.astype(np.uint8)


def conv_encode(u: np.ndarray, K: int, gens: tuple[str, ...]) -> np.ndarray:
    """u (..., T) bits -> (..., T*n) coded bits, outputs of one step adjacent: c0[0], c1[0], c0[1], ..."""
    u = np.asarray(u, np.uint8)
    outs = []
    for g in gens:
        c = np.zeros_like(u)
        for i, t in enumerate(gen_taps(g, K)):
            if t:
                c[..., i:] ^= u[..., : u.shape[-1] - i]
        outs.append(c)
    return np.stack(outs, -1).reshape(*u.shape[:-1], -1)


def viterbi_soft(llr: np.ndarray, K: int, gens: tuple[str, ...], terminated: bool = True) -> np.ndarray:
    """llr (F, T*n) with LLR>0 favouring 0 -> decoded inputs (F, T), including any tail bits."""
    llr = np.atleast_2d(np.asarray(llr, np.float32))
    n = len(gens)
    Fr, T = llr.shape[0], llr.shape[1] // n
    L = llr[:, : T * n].reshape(Fr, T, n)
    pred, pin, out = trellis(K, tuple(gens))
    S = pred.shape[0]
    sgn = (1.0 - 2.0 * out).astype(np.float32)                  # (S, 2, n)
    pm = np.full((Fr, S), -1e30, np.float32)
    pm[:, 0] = 0.0
    dec = np.empty((T, Fr, S), np.uint8)
    for k in range(T):
        m = pm[:, pred] + np.einsum("sbj,fj->fsb", sgn, L[:, k])
        c = m.argmax(-1)
        dec[k] = c
        pm = np.take_along_axis(m, c[..., None], -1)[..., 0]
        pm -= pm.max(-1, keepdims=True)
    st = np.zeros(Fr, np.int64) if terminated else pm.argmax(-1)
    u = np.empty((Fr, T), np.uint8)
    rows = np.arange(Fr)
    for k in range(T - 1, -1, -1):
        c = dec[k, rows, st]
        u[:, k] = pin[st]
        st = pred[st, c]
    return u
