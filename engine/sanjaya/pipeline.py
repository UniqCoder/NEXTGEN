"""Decode with a given recipe: PHY front-end (feedforward, vectorised) then unwrap (coding + structure).
The hypothesis-tree search (WP20) calls these same two functions for every branch it expands."""
from dataclasses import dataclass, field
import numpy as np
from .recipe import Recipe
from .chain import sps_of, asm_symbols, scrambler_seq, check_geometry, tail_bits, encode_frames
from .demod import rrc_taps, filt0, frac_shift, rotate, llr_qpsk
from .coding import block_deinterleave
from .kernels import viterbi_soft
from .bits import crc_bits, from_bits

ASM_ACCEPT = 0.5          # normalised ASM correlation needed to accept a frame (chance level ~ 1/sqrt(16) = 0.25)
VV_BLOCK = 256            # symbols per Viterbi-Viterbi phase block


@dataclass
class FrontEnd:
    sps: int
    cfo_hz: float
    advance: float                  # fractional samples the recording was advanced by before sampling
    k0: int                         # sample index (in the advanced domain) of symbol 0 of the stream
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


def _cfo_4th(x: np.ndarray, fs: float) -> float:
    v = x.astype(np.complex128) ** 4
    nfft = 1 << int(np.ceil(np.log2(4 * v.size)))
    P = np.abs(np.fft.fft(v, nfft))
    k = int(P.argmax())
    a, b, c = np.log(P[(k - 1) % nfft] + 1e-30), np.log(P[k] + 1e-30), np.log(P[(k + 1) % nfft] + 1e-30)
    k_ref = k + 0.5 * (a - c) / (a - 2 * b + c)
    f4 = np.fft.fftfreq(nfft)[k] + (k_ref - k) / nfft
    return float(f4 * fs / 4)


def frontend(x: np.ndarray, recipe: Recipe) -> FrontEnd:
    fs, sps = recipe.sample_rate_hz, sps_of(recipe)
    h = rrc_taps(sps, recipe.modulation.rolloff)
    cfo = _cfo_4th(x, fs)
    y = filt0(rotate(x, -cfo / fs), h)
    # Oerder-Meyr: symbol instants at n0 + m*sps
    n0 = (-np.angle(np.sum(np.abs(y) ** 2 * np.exp(-2j * np.pi * np.arange(y.size) / sps))) / (2 * np.pi) * sps) % sps
    adv = n0 - np.floor(n0)
    k0 = int(np.floor(n0))
    ys = frac_shift(y, -adv)[k0::sps]                               # advance by `adv`, then decimate
    # Viterbi-Viterbi 4th-power phase, per block, unwrapped, interpolated per symbol (pi/2 ambiguity remains)
    nb = max(1, ys.size // VV_BLOCK)
    blk = ys[: nb * VV_BLOCK].reshape(nb, VV_BLOCK)
    th4 = np.unwrap(np.angle(-np.sum(blk.astype(np.complex128) ** 4, 1)))
    centres = (np.arange(nb) + 0.5) * VV_BLOCK
    theta = np.interp(np.arange(ys.size), centres, th4 / 4)
    ys = (ys * np.exp(-1j * theta)).astype(np.complex64)

    asm = asm_symbols(recipe)
    check_geometry(recipe)
    period = asm.size + recipe.interleaver.rows * recipe.interleaver.cols // 2
    best = None
    for conj in (False, True):
        z = np.conj(ys) if conj else ys
        c = np.correlate(z, asm, "valid")                            # sum z[n+k] conj(asm[k])
        energy = np.sqrt(np.convolve(np.abs(z) ** 2, np.ones(asm.size), "valid")) * np.linalg.norm(asm)
        cn = np.abs(c) / np.maximum(energy, 1e-12)
        nfold = cn.size // period
        fold = cn[: nfold * period].reshape(nfold, period).sum(0)
        off = int(fold.argmax())
        if best is None or fold[off] > best[0]:
            best = (fold[off], conj, off, c, cn)
    _, conj, off, c, cn = best
    z = np.conj(ys) if conj else ys
    cand = np.arange(off, z.size - period + 1, period)
    ok = cn[cand] > ASM_ACCEPT
    starts = cand[ok]
    if starts.size == 0:
        raise RuntimeError("no frame sync found under this recipe")
    rot = np.round(np.angle(c[starts]) / (np.pi / 2)) * (np.pi / 2)
    frames = np.stack([z[s: s + period] for s in starts]) * np.exp(-1j * rot)[:, None]
    body = frames[:, asm.size:].ravel()
    dec = (np.sign(body.real) + 1j * np.sign(body.imag)) * np.float32(np.sqrt(0.5))
    amp = float(np.real(np.vdot(dec, body)) / dec.size)
    sigma2 = float(np.mean(np.abs(body - amp * dec) ** 2))
    return FrontEnd(sps, cfo, adv, k0, conj, period, starts, cn[starts], rot, theta, frames.astype(np.complex64), amp, sigma2)


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
    llr = llr_qpsk(body, fe.amp, fe.sigma2)
    llr *= (1.0 - 2.0 * scrambler_seq(recipe, llr.shape[1]))[None].astype(np.float32)
    il, fec = recipe.interleaver, recipe.fec
    llr = block_deinterleave(llr, il.rows, il.cols)
    u = viterbi_soft(llr, fec.K, tuple(fec.generators_octal), fec.terminated)
    info = u[:, : u.shape[1] - tail_bits(recipe)]
    reenc = block_deinterleave(encode_frames(recipe, info)["interleaved"], il.rows, il.cols)
    fields, crc_ok = [], []
    cr = recipe.framing.crc
    for row in info:
        pos, vals, ok = 0, {}, False
        for f in recipe.framing.fields:
            seg = row[pos: pos + f.bits]
            if f.kind == "crc":
                ok = from_bits(seg) == crc_bits(row[:pos], cr.width, cr.poly, cr.init, cr.refin, cr.refout, cr.xorout)
            vals[f.name] = np.packbits(seg).tobytes().hex() if f.kind == "payload" else from_bits(seg)
            pos += f.bits
        fields.append(vals)
        crc_ok.append(ok)
    return Unwrapped(llr, (llr < 0).astype(np.uint8), info, reenc, fields, np.array(crc_ok))
