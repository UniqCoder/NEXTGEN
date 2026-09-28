"""LDPC over GF(2): systematic encode from a parity-check matrix H, log-domain min-sum belief-propagation
decode. Reference implementation (small/medium block lengths; no optimised sparse message-passing)."""
import numpy as np


def systematic_generator(H: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """H (m, n), full row rank -> (G (k, n), colperm), both in H's ORIGINAL column order: G@H.T == 0 mod 2,
    and info bit i of a codeword sits at codeword[colperm[i]] for i < k = n - m."""
    A = (H.copy() % 2).astype(np.uint8)
    m, n = A.shape
    k = n - m
    pivot_cols = []
    row = 0
    for col in range(n):                            # standard forward elimination, pivot columns wherever found
        if row == m:
            break
        piv = next((r for r in range(row, m) if A[r, col]), None)
        if piv is None:
            continue
        A[[row, piv]] = A[[piv, row]]
        for r in range(m):
            if r != row and A[r, col]:
                A[r] ^= A[row]
        pivot_cols.append(col)
        row += 1
    if row < m:
        raise ValueError("H is not full row rank")
    free_cols = [c for c in range(n) if c not in pivot_cols]
    colperm = np.array(free_cols + pivot_cols)       # one permutation, applied once: free (info) cols, then pivots
    P = A[:, colperm][:, :k]
    G_perm = np.concatenate([np.eye(k, dtype=np.uint8), P.T % 2], axis=1)     # k x n, in PERMUTED column order
    G = np.zeros((k, n), np.uint8)
    G[:, colperm] = G_perm
    return G, colperm


def ldpc_encode(info: np.ndarray, G: np.ndarray) -> np.ndarray:
    """info (..., k) bits -> codeword (..., n) bits, G (k, n) from systematic_generator."""
    return (info.astype(np.uint8) @ G) % 2


def _min_excl_self(vals: np.ndarray) -> np.ndarray:
    """abs(vals) -> per-position min of every OTHER entry (the min-sum check-node update)."""
    a = np.abs(vals)
    if a.size == 1:
        return np.zeros_like(a)
    i1 = int(np.argmin(a))
    v1 = a[i1]
    rest = np.delete(a, i1)
    v2 = rest.min()
    out = np.full(a.size, v1)
    out[i1] = v2
    return out


def ldpc_decode(llr: np.ndarray, H: np.ndarray, max_iters: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """llr (F, n) channel LLRs (positive favours 0) -> (hard bits (F, n), converged (F,) all parity checks
    satisfied). Log-domain min-sum, normalised (0.75) to offset min-sum's magnitude overestimate."""
    Hb = (H % 2).astype(bool)
    m, n = Hb.shape
    F = llr.shape[0]
    rows = [np.nonzero(Hb[i])[0] for i in range(m)]
    cols = [np.nonzero(Hb[:, j])[0] for j in range(n)]
    out = np.empty((F, n), np.uint8)
    ok = np.zeros(F, bool)
    for f in range(F):
        Q = np.zeros((m, n))
        Q[Hb] = np.broadcast_to(llr[f], (m, n))[Hb]              # variable -> check messages, init = channel LLR
        R = np.zeros((m, n))
        hard = (llr[f] < 0).astype(np.uint8)
        for _ in range(max_iters):
            for i in range(m):
                js = rows[i]
                vals = Q[i, js]
                sign = np.sign(np.where(vals == 0, 1.0, vals))
                mag = _min_excl_self(vals)
                R[i, js] = 0.75 * np.prod(sign) / sign * mag
            total = llr[f] + R.sum(0)
            hard = (total < 0).astype(np.uint8)
            if np.all((Hb @ hard) % 2 == 0):
                ok[f] = True
                break
            for j in range(n):
                iis = cols[j]
                Q[iis, j] = total[j] - R[iis, j]
        out[f] = hard
    return out, ok
