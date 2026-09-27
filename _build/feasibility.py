"""Feasibility evidence for PRD v3 (§16). Throwaway analysis, NOT prototype code.
Measures the compute-budget assumptions and checks the statistical claims behind the layered proof.
Run from anywhere:  python _build/feasibility.py"""
import cmath, math, time
import numpy as np

rng = np.random.default_rng(147)
T = lambda: time.perf_counter()
out = {}

# 1. LOD spectrogram tiles for a 100 MB int16 IQ file (25 M complex samples), 1024 bins
raw = rng.integers(-2000, 2000, size=2 * 25_000_000, dtype=np.int16)
t = T()
x = raw.astype(np.float32).view(np.complex64)
frames = x[: (x.size // 1024) * 1024].reshape(-1, 1024)
p = np.abs(np.fft.fft(frames * np.hanning(1024).astype(np.float32), axis=1)) ** 2
rows = p[: (p.shape[0] // 64) * 64].reshape(-1, 64, 1024).mean(axis=1)   # 64-frame averaging -> LOD 0
db = 10 * np.log10(rows + 1e-12)
out["tiles_100MB_s"] = T() - t
del raw, x, frames, p

# 2. Pure-Python per-sample feedback loop (2nd-order Costas-style PLL), 1e6 samples
sig = (np.exp(1j * (0.001 * np.arange(1_000_000))) * np.exp(1j * np.pi / 4)).astype(np.complex64).tolist()
t = T()
ph = fr = 0.0
for s in sig:
    y = s * cmath.exp(-1j * ph)
    e = y.real * y.imag
    fr += 1e-4 * e
    ph += fr + 1e-2 * e
out["python_loop_1e6_s"] = T() - t

# 3. Feedforward Oerder-Meyr timing estimate, 1e6 samples at 4 samples/symbol (vectorised)
x = (rng.standard_normal(1_048_576) + 1j * rng.standard_normal(1_048_576)).astype(np.complex64)
t = T()
blk = np.abs(x.reshape(-1, 4096)) ** 2
tau = -np.angle((blk * np.exp(-2j * np.pi * np.arange(4096) / 4)).sum(axis=1)) / (2 * np.pi)
out["oerder_meyr_1e6_s"] = T() - t

# 4. K=7 (171,133) conv code: encoder, syndrome former, NumPy soft Viterbi (fallback-path speed)
G1, G2 = [1, 1, 1, 1, 0, 0, 1], [1, 0, 1, 1, 0, 1, 1]
def encode(u):
    return np.convolve(u, G1)[: u.size] % 2, np.convolve(u, G2)[: u.size] % 2

nxt = np.zeros((64, 2), int); obit = np.zeros((64, 2, 2), int)
for st in range(64):
    for b in range(2):
        reg = [b] + [(st >> (5 - i)) & 1 for i in range(6)]          # newest first
        obit[st, b] = [sum(r * g for r, g in zip(reg, G1)) % 2, sum(r * g for r, g in zip(reg, G2)) % 2]
        nxt[st, b] = (b << 5) | (st >> 1)
prev = [[] for _ in range(64)]
for st in range(64):
    for b in range(2):
        prev[nxt[st, b]].append((st, b))
P_ST = np.array([[a[0] for a in prev[s]] for s in range(64)]); P_B = np.array([[a[1] for a in prev[s]] for s in range(64)])
P_O = obit[P_ST, P_B]                                                   # (64, 2 preds, 2 out bits)

def viterbi(l1, l2):                                                    # LLR>0 favours bit 0
    n = l1.size; pm = np.full(64, -1e9); pm[0] = 0; dec = np.zeros((n, 64), np.uint8)
    s1, s2 = 1 - 2 * P_O[..., 0], 1 - 2 * P_O[..., 1]
    for k in range(n):
        m = pm[P_ST] + s1 * l1[k] + s2 * l2[k]
        c = m.argmax(axis=1); dec[k] = c; pm = m[np.arange(64), c]
    st, u = int(pm.argmax()), np.zeros(n, np.uint8)
    for k in range(n - 1, -1, -1):
        c = dec[k, st]; u[k] = P_B[st, c]; st = P_ST[st, c]
    return u

def qpsk_rx(c1, c2, esn0_db):
    s = ((1 - 2 * c1) + 1j * (1 - 2 * c2)) / np.sqrt(2)
    n0 = 10 ** (-esn0_db / 10)
    r = s + np.sqrt(n0 / 2) * (rng.standard_normal(s.size) + 1j * rng.standard_normal(s.size))
    return s, r, n0

u = rng.integers(0, 2, 20_000)
c1, c2 = encode(u)
_, r, n0 = qpsk_rx(c1, c2, 6.0)
t = T(); uh = viterbi(r.real * 4 / n0, r.imag * 4 / n0); out["viterbi_numpy_bits_per_s"] = u.size / (T() - t)
out["viterbi_post_fec_errors_6dB"] = int((uh[:-10] != u[:-10]).sum())

# 5. PR-01: the waveform test cannot see the coding layer at high SNR; the parity test K1 can
def syndrome_fail(h1, h2):
    s = (np.convolve(h1, G2) + np.convolve(h2, G1))[7 : h1.size] % 2
    return s.mean()

for esn0 in (6.0, 12.0):
    s, r, n0 = qpsk_rx(c1, c2, esn0)
    hard = (np.sign(r.real) + 1j * np.sign(r.imag)) / np.sqrt(2)
    rho_right = 10 * np.log10(np.mean(np.abs(r - s) ** 2) / n0)              # re-synthesised from true (decoded) bits
    rho_uncoded = 10 * np.log10(np.mean(np.abs(r - hard) ** 2) / n0)         # "uncoded" hypothesis: hard decisions
    h1, h2 = (r.real < 0).astype(int), (r.imag < 0).astype(int)
    pb = np.mean(np.r_[h1 != c1, h2 != c2])
    f = syndrome_fail(h1, h2); f0 = (1 - (1 - 2 * pb) ** 10) / 2
    rb1, rb2 = rng.integers(0, 2, u.size), rng.integers(0, 2, u.size)
    out[f"PR01_{int(esn0)}dB"] = dict(rho_right_dB=round(rho_right, 3), rho_uncoded_dB=round(rho_uncoded, 3),
                                      pre_fec_ber=float(pb), K1_f=round(float(f), 4), K1_f0=round(float(f0), 4),
                                      K1_f_random=round(float(syndrome_fail(rb1, rb2)), 4))

# 6. GF(2) rank, bit-packed NumPy elimination (fallback path); fit n^3 and extrapolate
def gf2_rank(M):
    W = np.packbits(M, axis=1, bitorder="little").view(np.uint64) if M.shape[1] % 64 == 0 else None
    A = W.copy(); r = 0; rows, words = A.shape
    for col in range(words * 64):
        w, b = divmod(col, 64); bit = np.uint64(1) << np.uint64(b)
        hit = np.nonzero(A[r:, w] & bit)[0]
        if hit.size == 0: continue
        p = r + hit[0]; A[[r, p]] = A[[p, r]]
        mask = (A[:, w] & bit).astype(bool); mask[r] = False
        A[mask] ^= A[r]; r += 1
        if r == rows: break
    return r

times = {}
for n in (256, 512, 1024):
    M = rng.integers(0, 2, (2 * n, n), dtype=np.uint8)
    t = T(); gf2_rank(M); times[n] = T() - t
out["gf2_rank_numpy_s"] = {k: round(v, 3) for k, v in times.items()}
k = np.polyfit(np.log(list(times)), np.log(list(times.values())), 1)[0]
per = lambda n: times[1024] * (n / 1024) ** k
out["gf2_scaling_exponent"] = round(float(k), 2)
out["exhaustive_period_search_to_4096_numpy_h"] = round(sum(per(n) for n in range(8, 4097)) / 3600, 1)

# 7. Schedule confidence (JCL) by Monte Carlo on WP three-point estimates
BASE = [1.2, 2.4, 3.2, 1.7, 3.1, 3.7, 1.0, 1.2, 2.0, 1.1, 1.4, 0.8, 2.1, 1.8, 2.1, 2.1, 1.0, 1.0, 0.4, 0.4, 0.2, 0.45]
LADDER = 2.70                                     # threshold configuration = baseline minus the §11.6 ladder (rungs 1-8)
def jcl(total_pw, n=200_000):
    shares = np.array(BASE) / sum(BASE) * total_pw
    wp = rng.triangular(0.8, 1.0, 1.5, (n, shares.size)) * shares      # per-WP: -20 % / most likely / +50 %
    common = rng.triangular(0.9, 1.0, 1.2, n)                          # team-wide factor (correlation)
    tot = wp.sum(axis=1) * common
    return float((tot <= 37.5).mean()), float(np.percentile(tot, 70))
b, t_ = sum(BASE), sum(BASE) - LADDER
out["baseline_pw"], out["threshold_pw"] = round(b, 2), round(t_, 2)
out["JCL_baseline"], out["JCL_threshold"] = jcl(b), jcl(t_)

for k_, v in out.items():
    print(f"{k_}: {v}")
