"""L5 demodulation: constellations and soft demapping (the pulse/filter maths lives in ..dsp)."""
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


