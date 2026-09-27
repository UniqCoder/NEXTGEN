"""Low-level DSP primitives shared by every layer: a continuous-time RRC pulse, a fractional-instant
matched filter and synthesiser (any samples/symbol, any clock offset), zero-delay FIR, frequency shift."""
from functools import lru_cache
import numpy as np
from scipy.signal import fftconvolve

SPAN = 6                      # pulse half-span in symbols
CHUNK = 1 << 15               # symbols per vectorised chunk (bounds memory)


def rrc(t: np.ndarray, b: float) -> np.ndarray:
    """Continuous root-raised-cosine, t in symbol periods (unnormalised)."""
    t = np.asarray(t, np.float64)
    out = np.empty_like(t)
    z = np.abs(t) < 1e-9
    s = (np.abs(np.abs(4 * b * t) - 1) < 1e-9) if b > 0 else np.zeros_like(z)
    r = ~(z | s)
    tr = t[r]
    out[r] = (np.sin(np.pi * tr * (1 - b)) + 4 * b * tr * np.cos(np.pi * tr * (1 + b))) / (np.pi * tr * (1 - (4 * b * tr) ** 2))
    out[z] = 1 - b + 4 * b / np.pi
    if b > 0:
        out[s] = b / np.sqrt(2) * ((1 + 2 / np.pi) * np.sin(np.pi / (4 * b)) + (1 - 2 / np.pi) * np.cos(np.pi / (4 * b)))
    return out


@lru_cache(maxsize=64)
def _norm(sps: float, b: float) -> float:
    n = np.arange(-int(np.ceil(SPAN * sps)), int(np.ceil(SPAN * sps)) + 1)
    return float(1 / np.sqrt((rrc(n / sps, b) ** 2).sum()))


@lru_cache(maxsize=64)
def mf_taps(sps: float, b: float) -> np.ndarray:
    """Integer-grid RRC taps for sps samples/symbol (sps may be fractional), unit energy, odd length."""
    n = np.arange(-int(np.ceil(SPAN * sps)), int(np.ceil(SPAN * sps)) + 1)
    return (rrc(n / sps, b) * _norm(sps, b)).astype(np.float32)


def _windows(inst: np.ndarray, sps: float, b: float, n: int):
    L = 2 * int(np.ceil(SPAN * sps)) + 1
    base = np.ceil(inst - SPAN * sps).astype(np.int64)
    idx = base[:, None] + np.arange(L)[None]
    w = rrc((idx - inst[:, None]) / sps, b) * _norm(sps, b)
    ok = (idx >= 0) & (idx < n)
    return np.where(ok, idx, 0), np.where(ok, w, 0.0)


def sample_at(x: np.ndarray, inst: np.ndarray, sps: float, b: float) -> np.ndarray:
    """Matched-filter output at fractional sample instants (exact for the band-limited pulse)."""
    out = np.empty(inst.size, np.complex64)
    for i in range(0, inst.size, CHUNK):
        idx, w = _windows(inst[i: i + CHUNK], sps, b, x.size)
        out[i: i + CHUNK] = (x[idx] * w).sum(1)
    return out


def synth_at(sym: np.ndarray, inst: np.ndarray, sps: float, b: float, n: int) -> np.ndarray:
    """Pulse-shaped waveform with symbol k centred at fractional sample inst[k]."""
    re, im = np.zeros(n), np.zeros(n)
    for i in range(0, inst.size, CHUNK):
        idx, w = _windows(inst[i: i + CHUNK], sps, b, n)
        a = sym[i: i + CHUNK, None]
        re += np.bincount(idx.ravel(), (w * a.real).ravel(), n)
        im += np.bincount(idx.ravel(), (w * a.imag).ravel(), n)
    return (re + 1j * im).astype(np.complex64)


def filt0(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Zero-delay filtering with a symmetric odd-length FIR (output aligned with the input)."""
    d = (h.size - 1) // 2
    return fftconvolve(x, h)[d: d + x.size].astype(np.complex64)


def rotate(x: np.ndarray, f_norm: float, phase: float = 0.0) -> np.ndarray:
    """Multiply by exp(j(2 pi f_norm n + phase)); f_norm in cycles per sample."""
    n = np.arange(x.size)
    return (x * np.exp(1j * (2 * np.pi * f_norm * n + phase))).astype(np.complex64)
