"""Non-coherent MFSK front end (PS clause (ii): demodulate FSK). Fully separate from pipeline.py's
coherent PSK/QAM front end (frontend()/symbols()) — FSK has no phase-continuous constellation for the
CFO-power / Viterbi-Viterbi machinery to work on, so it gets its own CFO search and frame sync, both
in the tone-energy domain. Everything past the demapper (FEC, interleaving, scrambling, framing, CRC)
is shared via pipeline.decode_llr, exactly like the PSK/QAM path.

Known-recipe only: given the frame structure, this recovers and CRC-checks the bitstream. The layered
proof's statistical channel model (proof.certificate.coding_layer) is not yet FSK-aware, so an FSK
decode is not yet certified -- the same honest gap RS decode had before its own proof branch landed."""
from dataclasses import dataclass
import numpy as np
from .recipe import Recipe
from .chain import asm_bits, coded_len, check_geometry
from .demod import fsk_llr, fsk_tones, BPS
from .dsp import rotate
from .pipeline import decode_llr, Unwrapped

FSK_ASM_ACCEPT = 0.6   # normalised bit-correlation floor to accept a frame (chance level ~ 0)


@dataclass
class FskFrontEnd:
    cfo_hz: float
    sps: float
    start_sample: int
    starts_bits: np.ndarray     # bit index of each accepted frame's ASM
    corr: np.ndarray            # normalised bit correlation at each accepted frame
    n_frames: int


def _score(xr: np.ndarray, fs: float, symbol_rate_hz: float, tones: np.ndarray, start: int) -> float:
    return float(np.abs(fsk_llr(xr, fs, symbol_rate_hz, tones, start_sample=start)).sum())


def estimate_cfo(x: np.ndarray, fs: float, symbol_rate_hz: float, tones: np.ndarray,
                  coarse_span: float = 1000.0, coarse_step: float = 25.0,
                  fine_span: float = 30.0, fine_step: float = 2.0) -> float:
    """Coarse-then-fine grid search maximising total tone-bank confidence (sum|LLR|). Non-coherent
    detection has no M-th-power phase trick to fall back on, so this is a bounded brute force instead;
    the step sizes are the resolution ceiling (finer -> slower, not more correct)."""
    best_cfo, best_score = 0.0, -1.0
    for cfo in np.arange(-coarse_span, coarse_span + 1e-9, coarse_step):
        s = _score(rotate(x, -cfo / fs), fs, symbol_rate_hz, tones, 0)
        if s > best_score:
            best_score, best_cfo = s, float(cfo)
    c0 = best_cfo
    best_score = -1.0
    for cfo in np.arange(c0 - fine_span, c0 + fine_span + 1e-9, fine_step):
        s = _score(rotate(x, -cfo / fs), fs, symbol_rate_hz, tones, 0)
        if s > best_score:
            best_score, best_cfo = s, float(cfo)
    return best_cfo


def frame_sync_bits(hard: np.ndarray, asm: np.ndarray, period_bits: int):
    """Bit-domain analogue of pipeline.frame_sync: fold +-1 correlation against the known ASM bit
    pattern at the frame period. Returns (starts, normalised correlation at each)."""
    z = 1.0 - 2.0 * hard.astype(np.float64)
    a = 1.0 - 2.0 * asm.astype(np.float64)
    c = np.correlate(z, a, "valid")
    nfold = c.size // period_bits
    if nfold == 0:
        raise RuntimeError("recording shorter than one frame under this recipe")
    fold = c[: nfold * period_bits].reshape(nfold, period_bits).sum(0)
    off = int(fold.argmax())
    cand = np.arange(off, c.size, period_bits)
    norm = c[cand] / a.size
    keep = norm > FSK_ASM_ACCEPT
    return cand[keep], norm[keep]


def fsk_frontend(x: np.ndarray, recipe: Recipe) -> tuple[FskFrontEnd, np.ndarray]:
    """Returns (front end metadata, per-frame body-bit LLR array (F, coded_len))."""
    check_geometry(recipe)
    scheme = recipe.modulation.scheme
    if not scheme.startswith("fsk"):
        raise ValueError(f"fsk_frontend needs an fsk* modulation, got '{scheme}'")
    fs, symbol_rate = recipe.sample_rate_hz, recipe.modulation.symbol_rate_hz
    tones = fsk_tones(scheme, recipe.modulation.fsk_tone_spacing_hz)
    sps = fs / symbol_rate
    asm = asm_bits(recipe)
    if asm.size % BPS[scheme] != 0:
        raise ValueError(f"ASM bit length {asm.size} is not a multiple of {scheme}'s {BPS[scheme]} bits/symbol")
    period_bits = asm.size + coded_len(recipe)

    cfo = estimate_cfo(x, fs, symbol_rate, tones)
    xr = rotate(x, -cfo / fs)

    phase_candidates = np.unique(np.round(np.linspace(0, sps, 8, endpoint=False)).astype(int))
    best = None
    for start in phase_candidates:
        llr = fsk_llr(xr, fs, symbol_rate, tones, start_sample=int(start))
        hard = (llr < 0).astype(np.uint8)
        try:
            starts, corr = frame_sync_bits(hard, asm, period_bits)
        except RuntimeError:
            continue
        score = float(corr.sum())
        if starts.size and (best is None or score > best[0]):
            best = (score, int(start), llr, starts, corr)
    if best is None:
        raise RuntimeError("no frame sync found under this recipe")
    _, start, llr, starts, corr = best

    noise_var = float(np.var(xr))  # ponytail: proxy (signal+noise power); decision-directed is the accuracy upgrade path
    llr = fsk_llr(xr, fs, symbol_rate, tones, start_sample=start, noise_var=noise_var)
    body = np.stack([llr[s + asm.size: s + period_bits] for s in starts])
    fe = FskFrontEnd(cfo, sps, start, starts, corr, body.shape[0])
    return fe, body.astype(np.float32)


def unwrap_fsk(x: np.ndarray, recipe: Recipe) -> tuple[FskFrontEnd, Unwrapped]:
    fe, body_llr = fsk_frontend(x, recipe)
    return fe, decode_llr(recipe, body_llr)
