"""L5 demodulation primitives: constellations, RRC pulses, zero-delay filtering, fractional shifts."""
from functools import lru_cache
import numpy as np
from scipy.signal import fftconvolve

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


@lru_cache(maxsize=32)
def rrc_taps(sps: int, rolloff: float, span: int = 12) -> np.ndarray:
    """Root-raised-cosine, unit energy, length span*sps + 1 (symmetric, zero delay when centred)."""
    t = np.arange(-span * sps // 2, span * sps // 2 + 1) / sps
    b = rolloff
    h = np.empty_like(t)
    for i, ti in enumerate(t):
        if abs(ti) < 1e-12:
            h[i] = 1 - b + 4 * b / np.pi
        elif b > 0 and abs(abs(4 * b * ti) - 1) < 1e-9:
            h[i] = b / np.sqrt(2) * ((1 + 2 / np.pi) * np.sin(np.pi / (4 * b)) + (1 - 2 / np.pi) * np.cos(np.pi / (4 * b)))
        else:
            h[i] = (np.sin(np.pi * ti * (1 - b)) + 4 * b * ti * np.cos(np.pi * ti * (1 + b))) / (np.pi * ti * (1 - (4 * b * ti) ** 2))
    return (h / np.sqrt((h ** 2).sum())).astype(np.float32)


def filt0(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Zero-delay filtering with a symmetric odd-length FIR (output aligned with the input)."""
    d = (h.size - 1) // 2
    return fftconvolve(x, h)[d: d + x.size].astype(np.complex64)


def frac_shift(x: np.ndarray, delay: float) -> np.ndarray:
    """Delay x by `delay` samples (may be fractional or negative) via an FFT phase ramp."""
    n = x.size
    k = np.fft.fftfreq(n)
    return np.fft.ifft(np.fft.fft(x) * np.exp(-2j * np.pi * k * delay)).astype(np.complex64)


def rotate(x: np.ndarray, f_norm: float, phase: float = 0.0) -> np.ndarray:
    """Multiply by exp(j(2 pi f_norm n + phase)); f_norm in cycles per sample."""
    n = np.arange(x.size)
    return (x * np.exp(1j * (2 * np.pi * f_norm * n + phase))).astype(np.complex64)
