"""Decode with a given recipe: PHY front-end (feedforward, vectorised) then unwrap (coding + structure).
The hypothesis-tree search (search.py) calls these same functions for every branch it expands."""
from dataclasses import dataclass, field
import numpy as np
from .recipe import Recipe
from .chain import sps_of, asm_symbols, scrambler_seq, check_geometry, tail_bits, encode_frames, coded_len
from .demod import llr_symbols, constellation, vv_ref_phase, BPS, ROT_ORDER
from .dsp import rotate, sample_at
from .measure import cfo_power, timing_fit
from .coding import block_deinterleave
from .kernels import viterbi_soft
from .bits import crc_bits, from_bits

ASM_ACCEPT = 0.5          # normalised ASM correlation needed to accept a frame (chance level ~ 1/sqrt(16) = 0.25)
VV_BLOCK = 256            # symbols per Viterbi-Viterbi phase block


def symbols(x: np.ndarray, fs: float, sps_nom: float, rolloff: float, M: int = 4, ref_phase: float = np.pi):
    """PHY front-end up to derotated symbols: CFO (M-th power), timing (measured rate), matched filter at
    the fractional instants, Viterbi-Viterbi phase (2 pi / M ambiguity remains). ref_phase is the phase
    that raising the modulation's constellation to the M-th power leaves behind (demod.vv_ref_phase);
    the default pi matches QPSK's legacy odd-multiples-of-pi/4 points ('-sum').
    Returns (ys, sps, t0, cfo, theta); stream symbol k sits at sample t0 + k * sps."""
    cfo = cfo_power(x, fs, M)
    xc = rotate(x, -cfo / fs)
    sps, t0 = timing_fit(xc, sps_nom, rolloff)
    k = np.arange(int(np.floor((x.size - 1 - t0) / sps)) + 1)
    ys = sample_at(xc, t0 + sps * k, sps, rolloff)
    nb = max(1, ys.size // VV_BLOCK)
    blk = ys[: nb * VV_BLOCK].reshape(nb, VV_BLOCK).astype(np.complex128)
    thM = np.unwrap(np.angle(np.sum(blk ** M, 1) * np.exp(-1j * ref_phase)))
    theta = np.interp(np.arange(ys.size), (np.arange(nb) + 0.5) * VV_BLOCK, thM / M)
    return (ys * np.exp(-1j * theta)).astype(np.complex64), sps, t0, cfo, theta


@dataclass
class FrontEnd:
    sps: float                      # measured samples per symbol (includes the recorder's clock offset)
    sps_nominal: float              # from the recipe
    cfo_hz: float
    t0: float                       # fractional sample instant of stream symbol 0
    conj: bool
    period: int                     # symbols per frame incl. ASM
    starts: np.ndarray              # symbol index of each accepted frame's ASM
    asm_corr: np.ndarray            # normalised ASM correlation of each accepted frame
    rot: np.ndarray                 # per-frame residual rotation (multiple of pi/2)
    theta: np.ndarray               # per-symbol phase trajectory removed (radians)
    frames: np.ndarray              # (F, period) symbols, fully derotated
    amp: float
    sigma2: float
    notes: list[str] = field(default_factory=list)

    @property
    def esn0_db(self) -> float:
        return float(10 * np.log10(self.amp ** 2 / self.sigma2))

    @property
    def clock_ppm(self) -> float:
        return float((self.sps / self.sps_nominal - 1) * 1e6)

    def instants(self, k) -> np.ndarray:
        return self.t0 + self.sps * np.asarray(k, np.float64)


def frame_sync(ys: np.ndarray, asm: np.ndarray, period: int):
    """Locate PHY sync markers: fold normalised ASM correlation at the frame period, both conjugations.
    Returns (conj, starts, normalised corr at starts, complex corr at starts)."""
    best = None
    for conj in (False, True):
        z = np.conj(ys) if conj else ys
        c = np.correlate(z, asm, "valid")                            # sum z[n+k] conj(asm[k])
        energy = np.sqrt(np.convolve(np.abs(z) ** 2, np.ones(asm.size), "valid")) * np.linalg.norm(asm)
        cn = np.abs(c) / np.maximum(energy, 1e-12)
        nfold = cn.size // period
        if nfold == 0:
            raise RuntimeError("recording shorter than one frame under this recipe")
        fold = cn[: nfold * period].reshape(nfold, period).sum(0)
        off = int(fold.argmax())
        if best is None or fold[off] > best[0]:
            best = (fold[off], conj, off, c, cn)
    _, conj, off, c, cn = best
    cand = np.arange(off, cn.size, period)
    starts = cand[(cn[cand] > ASM_ACCEPT) & (cand + period <= ys.size)]
    return conj, starts, cn[starts], c[starts]


def frontend(x: np.ndarray, recipe: Recipe, pre=None) -> FrontEnd:
    """pre: an already computed symbols() tuple for the same PHY (lets the search reuse it)."""
    fs, sps_nom, beta = recipe.sample_rate_hz, sps_of(recipe), recipe.modulation.rolloff
    scheme = recipe.modulation.scheme
    ys, sps, t0, cfo, theta = pre if pre is not None else symbols(x, fs, sps_nom, beta, M=ROT_ORDER[scheme], ref_phase=vv_ref_phase(scheme))
    asm = asm_symbols(recipe)
    check_geometry(recipe)
    period = asm.size + coded_len(recipe) // BPS[scheme]
    conj, starts, cn, c = frame_sync(ys, asm, period)
    if starts.size == 0:
        raise RuntimeError("no frame sync found under this recipe")
    z = np.conj(ys) if conj else ys
    step = 2 * np.pi / ROT_ORDER[scheme]
    rot = np.round(np.angle(c) / step) * step
    frames = np.stack([z[s: s + period] for s in starts]) * np.exp(-1j * rot)[:, None]
    amp, sigma2 = decision_directed(scheme, frames[:, asm.size:].ravel())
    return FrontEnd(sps, sps_nom, cfo, t0, conj, period, starts, cn, rot, theta, frames.astype(np.complex64), amp, sigma2)


def decision_directed(scheme: str, body: np.ndarray, iters: int = 4) -> tuple[float, float]:
    """Decision-directed amplitude and complex noise variance against the scheme's (unit-energy)
    constellation. PSK decisions are scale-invariant (nearest phase); QAM needs the iteration to
    separate its amplitude rings, so the estimate is refined a few times."""
    tab = constellation(scheme)
    amp = float(np.sqrt(np.mean(np.abs(body) ** 2)))
    dec = tab[0]
    for _ in range(iters):
        dec = tab[np.abs(body[:, None] - amp * tab[None, :]).argmin(1)]
        amp = float(np.real(np.vdot(dec, body)) / np.real(np.vdot(dec, dec)))
    return amp, float(np.mean(np.abs(body - amp * dec) ** 2))


@dataclass
class Unwrapped:
    llr: np.ndarray                 # (F, Nc) descrambled, de-interleaved code-bit LLRs
    hard: np.ndarray                # (F, Nc) hard decisions of the same
    info: np.ndarray                # (F, Ninfo) decoded information bits
    reencoded: np.ndarray           # (F, Nc) re-encoded code bits (for corrections / K2)
    fields: list[dict]              # per frame: field name -> int value (payload as hex)
    crc_ok: np.ndarray              # (F,)


def unwrap(fe: FrontEnd, recipe: Recipe) -> Unwrapped:
    check_geometry(recipe)
    na = asm_symbols(recipe).size
    body = fe.frames[:, na:]
    llr = llr_symbols(recipe.modulation.scheme, body, fe.amp, fe.sigma2)
    llr *= (1.0 - 2.0 * scrambler_seq(recipe, llr.shape[1]))[None].astype(np.float32)
    il, fec = recipe.interleaver, recipe.fec
    llr = block_deinterleave(llr, il.rows, il.cols)
    u = viterbi_soft(llr, fec.K, tuple(fec.generators_octal), fec.terminated)
    info = u[:, : u.shape[1] - tail_bits(recipe)]
    reenc = block_deinterleave(encode_frames(recipe, info)["interleaved"], il.rows, il.cols)
    fields, crc_ok = parse_fields(recipe, info)
    return Unwrapped(llr, (llr < 0).astype(np.uint8), info, reenc, fields, crc_ok)


def parse_fields(recipe: Recipe, info: np.ndarray) -> tuple[list[dict], np.ndarray]:
    fields, crc_ok = [], []
    cr = recipe.framing.crc
    for row in info:
        pos, vals, ok = 0, {}, False
        for f in recipe.framing.fields:
            seg = row[pos: pos + f.bits]
            if f.kind == "crc" and cr is not None:
                ok = from_bits(seg) == crc_bits(row[:pos], cr.width, cr.poly, cr.init, cr.refin, cr.refout, cr.xorout)
            vals[f.name] = np.packbits(seg).tobytes().hex() if f.kind == "payload" else from_bits(seg)
            pos += f.bits
        fields.append(vals)
        crc_ok.append(ok)
    return fields, np.array(crc_ok)
