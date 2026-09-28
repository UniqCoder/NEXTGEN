"""L5 demodulation: constellations and soft demapping (the pulse/filter maths lives in ..dsp)."""
from functools import lru_cache
import numpy as np

SQ2 = np.float32(np.sqrt(0.5))


def map_qpsk(bits: np.ndarray) -> np.ndarray:
    """Gray QPSK: (b0, b1) -> ((1-2 b0) + j(1-2 b1)) / sqrt(2). bits (..., 2m) -> (..., m)."""
    b = np.asarray(bits, np.float32)
    return ((1 - 2 * b[..., 0::2]) + 1j * (1 - 2 * b[..., 1::2])).astype(np.complex64) * SQ2


def llr_qpsk(y: np.ndarray, amp: float, sigma2: float) -> np.ndarray:
    """Exact per-bit LLRs for Gray QPSK in AWGN; y (..., m) -> (..., 2m), positive favours 0."""
    s = np.float32(2 * np.sqrt(2) * amp / sigma2)
    out = np.empty((*y.shape[:-1], 2 * y.shape[-1]), np.float32)
    out[..., 0::2], out[..., 1::2] = s * y.real, s * y.imag
    return out




# ---------------------------------------------------------------------------------------------------------
# Generic Gray-labelled M-PSK / M-QAM constellations, for the known-recipe demod chain (PS clause (ii):
# demodulate FSK, QAM, PSK). 'qpsk' keeps the exact legacy table (also used unconditionally for the PHY
# ASM, sent robustly regardless of the data modulation). The blind coding search (search.py) is still
# QPSK-only: it is built on a rate-1/2-over-2-bit-symbols model and generalising it is separate work.
BPS = {"bpsk": 1, "qpsk": 2, "8psk": 3, "16qam": 4, "64qam": 6, "fsk2": 1, "fsk4": 2, "fsk8": 3}
# Rotational symmetry order used for the M-th-power CFO/phase trick: BPSK is 2-fold, QPSK 4-fold, 8PSK
# 8-fold; square Gray QAM (any order) has only 4-fold symmetry, not its bit count. FSK is non-coherent
# (no phase-symmetry trick applies) and never goes through this table.
ROT_ORDER = {"bpsk": 2, "qpsk": 4, "8psk": 8, "16qam": 4, "64qam": 4}


def fsk_tones(scheme: str, spacing_hz: float) -> np.ndarray:
    """M equally spaced baseband tone frequencies, centred on 0 Hz, low to high."""
    m = 1 << BPS[scheme]
    return spacing_hz * (np.arange(m, dtype=np.float64) - (m - 1) / 2)


def gray_decode(bits: np.ndarray) -> np.ndarray:
    """Inverse of k -> k ^ (k>>1): bits (..., bps) MSB-first Gray codeword -> (...) tone index."""
    b = np.asarray(bits, np.int64)
    val = np.zeros(b.shape[:-1], np.int64)
    for i in range(b.shape[-1]):
        val = (val << 1) | b[..., i]
    k = val
    shift = 1
    while shift < b.shape[-1] + 1:
        k ^= k >> shift
        shift <<= 1
    return k


def _gray_pam(bits_per_axis: int) -> np.ndarray:
    """L-level Gray PAM, indexed by the Gray codeword's integer value; levels -(L-1)..(L-1) step 2."""
    L = 1 << bits_per_axis
    levels = np.arange(-(L - 1), L, 2, dtype=np.float64)
    table = np.empty(L)
    for n in range(L):
        table[n ^ (n >> 1)] = levels[n]
    return table


def _psk_table(bps: int) -> np.ndarray:
    M = 1 << bps
    table = np.empty(M, np.complex128)
    for p in range(M):
        table[p ^ (p >> 1)] = np.exp(2j * np.pi * p / M)
    return table


def _qam_table(bits_per_axis: int) -> np.ndarray:
    pam = _gray_pam(bits_per_axis)
    norm = np.sqrt(2 * np.mean(pam ** 2))
    L = 1 << bits_per_axis
    table = np.empty(L * L, np.complex128)
    for gi in range(L):
        for gq in range(L):
            table[(gi << bits_per_axis) | gq] = complex(pam[gi], pam[gq]) / norm
    return table


@lru_cache(maxsize=8)
def constellation(scheme: str) -> np.ndarray:
    """Symbol table indexed by the bit-group's integer value (MSB-first); unit average energy."""
    if scheme == "qpsk":
        b = np.arange(4, dtype=np.float32)
        return (((1 - 2 * (b // 2)) + 1j * (1 - 2 * (b % 2))) * SQ2).astype(np.complex128)
    if scheme == "bpsk":
        return _psk_table(1)
    if scheme == "8psk":
        return _psk_table(3)
    if scheme == "16qam":
        return _qam_table(2)
    if scheme == "64qam":
        return _qam_table(3)
    raise ValueError(f"unknown / unsupported modulation scheme '{scheme}'")


def map_symbols(scheme: str, bits: np.ndarray) -> np.ndarray:
    """bits (..., n*bps) -> symbols (..., n), Gray-labelled, unit average energy."""
    bps = BPS[scheme]
    tab = constellation(scheme)
    b = np.asarray(bits).reshape(*bits.shape[:-1], -1, bps)
    idx = np.zeros(b.shape[:-1], np.int64)
    for i in range(bps):
        idx = (idx << 1) | b[..., i]
    return tab[idx].astype(np.complex64)


@lru_cache(maxsize=8)
def vv_ref_phase(scheme: str) -> float:
    """The phase that raising this scheme's constellation to the ROT_ORDER power leaves behind (the
    'legacy -sum trick' generalised): for QPSK's odd-multiples-of-pi/4 points this is pi (hence '-sum');
    for BPSK/8PSK's on-axis points it is 0; for QAM it is whatever the corner points average to."""
    tab = constellation(scheme)
    ref = np.mean(tab.astype(np.complex128) ** ROT_ORDER[scheme])
    return float(np.angle(ref))


def llr_symbols(scheme: str, y: np.ndarray, amp: float, sigma2: float) -> np.ndarray:
    """Max-log per-bit LLRs (positive favours 0); y (..., n) -> (..., n*bps). Exact for BPSK/QPSK
    (matches llr_qpsk); an approximation (standard, and the usual practical choice) for 8PSK/QAM."""
    bps = BPS[scheme]
    if scheme == "qpsk":
        return llr_qpsk(y, amp, sigma2)
    tab = amp * constellation(scheme)
    M = tab.size
    d2 = np.abs(y[..., None] - tab) ** 2 / sigma2                  # (..., n, M)
    out = np.empty((*y.shape, bps), np.float32)
    for i in range(bps):
        bit_i = ((np.arange(M) >> (bps - 1 - i)) & 1).astype(bool)
        m1 = np.where(bit_i, d2, np.inf).min(-1)
        m0 = np.where(bit_i, np.inf, d2).min(-1)
        out[..., i] = m1 - m0
    return out.reshape(*y.shape[:-1], y.shape[-1] * bps).astype(np.float32)


def fsk_llr(x: np.ndarray, sample_rate_hz: float, symbol_rate_hz: float,
            tones_hz: np.ndarray, start_sample: int = 0, noise_var: float = 1.0) -> np.ndarray:
    """Noncoherent 2/4/8-FSK tone-bank soft bits, Gray-labelled from low to high tone.

    Frequencies are relative to complex baseband. The caller supplies symbol timing and a
    noise variance measured per complex sample; phase may change between symbols.
    """
    tones = np.asarray(tones_hz, dtype=float)
    if (x.ndim != 1 or tones.ndim != 1 or tones.size not in (2, 4, 8)
            or not np.all(np.isfinite(tones)) or not np.all(np.diff(tones) > 0)
            or not np.isfinite([sample_rate_hz, symbol_rate_hz, noise_var]).all()
            or sample_rate_hz <= 0 or symbol_rate_hz <= 0 or noise_var <= 0
            or not isinstance(start_sample, (int, np.integer)) or start_sample < 0 or start_sample >= len(x)):
        raise ValueError("invalid FSK tones, rates, timing or noise variance")
    sps = sample_rate_hz / symbol_rate_hz
    if sps < 2 or len(x) - start_sample < sps or max(abs(tones)) >= sample_rate_hz / 2:
        raise ValueError("FSK tones must fit below Nyquist with at least two samples per symbol")
    count = int((len(x) - start_sample) / sps)
    edges = start_sample + np.rint(np.arange(count + 1) * sps).astype(int)
    scores = np.empty((count, tones.size), dtype=float)
    for k, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        t = np.arange(a, b) / sample_rate_hz
        scores[k] = np.abs(np.exp(-2j * np.pi * tones[:, None] * t) @ x[a:b]) ** 2 / ((b - a) * noise_var)
    bps = int(np.log2(tones.size))
    labels = np.arange(tones.size) ^ (np.arange(tones.size) >> 1)
    out = np.empty((count, bps), dtype=np.float32)
    for bit in range(bps):
        one = ((labels >> (bps - bit - 1)) & 1).astype(bool)
        out[:, bit] = scores[:, ~one].max(axis=1) - scores[:, one].max(axis=1)
    return out.ravel()
