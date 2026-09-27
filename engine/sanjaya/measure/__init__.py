"""L2 measurement: carrier offset, symbol rate (blind and refined), timing, roll-off, SNR.
Every estimator here is feedforward and vectorised (PRD §6.1 principle 4)."""
import numpy as np
from ..dsp import filt0, mf_taps, rrc, rotate


def _peak(P: np.ndarray, k: int) -> float:
    """Parabolic interpolation of a spectral peak on log magnitude; returns the fractional bin."""
    n = P.size
    a, b, c = np.log(P[(k - 1) % n] + 1e-30), np.log(P[k] + 1e-30), np.log(P[(k + 1) % n] + 1e-30)
    den = a - 2 * b + c
    return k + (0.5 * (a - c) / den if den != 0 else 0.0)


def cfo_power(x: np.ndarray, fs: float, M: int = 4) -> float:
    """Carrier offset from the M-th power line (M = 4 for QPSK). Unambiguous for |cfo| < fs/(2M)."""
    v = x.astype(np.complex128) ** M
    nfft = 1 << int(np.ceil(np.log2(4 * v.size)))
    P = np.abs(np.fft.fft(v, nfft))
    f = _peak(P, int(P.argmax())) / nfft
    return float((f - 1 if f >= 0.5 else f) * fs / M)


def symbol_rate_blind(x: np.ndarray, fs: float, lo_frac: float = 1 / 256) -> float:
    """Strongest non-DC cyclic line of |x|^2 (the symbol clock of a linearly modulated signal with
    roll-off >= ~0.15; PRD §6.4 family-specific estimators add MSK/FSK lines later)."""
    p = np.abs(x.astype(np.complex128)) ** 2
    nfft = 1 << int(np.ceil(np.log2(4 * p.size)))
    F = np.abs(np.fft.rfft(p - p.mean(), nfft))
    lo = max(2, int(lo_frac * nfft))
    k = lo + int(F[lo:].argmax())
    return float(_peak(F, k) / nfft * fs)


def timing_fit(x: np.ndarray, sps_nom: float, rolloff: float, block_symbols: int = 512, iters: int = 3):
    """Block-wise Oerder-Meyr phases, unwrapped and fitted linearly: returns (sps_actual, t0) with the
    symbol instants at t0 + m * sps_actual. Measures the recorder's clock offset relative to nominal."""
    y = filt0(x, mf_taps(sps_nom, rolloff))
    p = np.abs(y.astype(np.complex128)) ** 2
    n = np.arange(p.size)
    P = sps_nom
    for _ in range(iters):
        B = int(round(block_symbols * P))
        nb = p.size // B
        s = (p[: nb * B] * np.exp(-2j * np.pi * n[: nb * B] / P)).reshape(nb, B).sum(1)
        w = np.abs(s)
        good = w > 0.3 * w.max()
        if good.sum() >= 3:
            c = (np.arange(nb)[good] + 0.5) * B
            slope = np.polyfit(c, np.unwrap(np.angle(s[good])), 1, w=w[good])[0]
            P = 1.0 / (1.0 / P + slope / (2 * np.pi))
    B = int(round(block_symbols * P))
    nb = p.size // B
    s = (p[: nb * B] * np.exp(-2j * np.pi * n[: nb * B] / P)).reshape(nb, B).sum(1)
    good = np.abs(s) > 0.3 * np.abs(s).max()
    t0 = (-np.angle(s[good].sum()) / (2 * np.pi) * P) % P
    return float(P), float(t0)


def rolloff_psd(x: np.ndarray, fs: float, symbol_rate: float, cfo_hz: float, grid=np.arange(0.05, 1.001, 0.01)) -> float:
    """Least-squares fit of the raised-cosine PSD shape (|RRC|^2 = RC spectrum) to the measured PSD."""
    xc = rotate(x, -cfo_hz / fs)
    nper = 4096
    seg = xc[: xc.size // nper * nper].reshape(-1, nper) * np.hanning(nper)
    psd = np.fft.fftshift((np.abs(np.fft.fft(seg, axis=1)) ** 2).mean(0))
    f = np.fft.fftshift(np.fft.fftfreq(nper, 1 / fs)) / symbol_rate
    floor = np.percentile(psd, 5)
    band = np.abs(f) < 1.0
    best, err_best = None, np.inf
    for b in grid:
        H = np.clip(np.where(np.abs(f) <= (1 - b) / 2, 1.0,
                             0.5 * (1 + np.cos(np.pi / b * (np.abs(f) - (1 - b) / 2)))) * (np.abs(f) <= (1 + b) / 2), 0, 1)
        A = np.vstack([H[band], np.ones(band.sum())]).T
        coef, *_ = np.linalg.lstsq(A, psd[band] - floor, rcond=None)
        err = np.sum((A @ coef - (psd[band] - floor)) ** 2)
        if err < err_best:
            best, err_best = float(b), err
    return best


__all__ = ["cfo_power", "symbol_rate_blind", "timing_fit", "rolloff_psd", "rrc"]
