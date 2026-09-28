"""The transmit-chain model: information bits -> code -> interleaver -> scrambler -> mapper -> pulse.
Used by the generator AND by the proof's re-synthesis, so every hypothesis is rebuilt by the same model."""
from functools import lru_cache
import numpy as np
from .recipe import Recipe
from .kernels import conv_encode, rs_encode, bits_to_symbols, symbols_to_bits, systematic_generator, ldpc_encode
from .coding import interleave, lfsr_sequence
from .demod import map_qpsk, map_symbols, BPS, fsk_tones, gray_decode
from .dsp import synth_at


def sps_of(recipe: Recipe) -> float:
    """Nominal samples per symbol (any real value; the receiver measures the actual one)."""
    return recipe.sample_rate_hz / recipe.modulation.symbol_rate_hz


@lru_cache(maxsize=16)
def _scr(poly: tuple[int, ...], seed: int, n: int) -> np.ndarray:
    return lfsr_sequence(list(poly), seed, n)


def scrambler_seq(recipe: Recipe, n: int) -> np.ndarray:
    s = recipe.scrambler
    return np.zeros(n, np.uint8) if s is None else _scr(tuple(s.poly_exponents), s.seed, n)


def asm_bits(recipe: Recipe) -> np.ndarray:
    h = recipe.framing.asm_hex
    return np.unpackbits(np.frombuffer(bytes.fromhex(h), np.uint8))


def asm_symbols(recipe: Recipe) -> np.ndarray:
    return map_qpsk(asm_bits(recipe))


def tail_bits(recipe: Recipe) -> int:
    fec = recipe.fec
    if fec.family in ("rs", "ldpc"):
        return 0
    inner = fec.inner if fec.family == "concat" else fec
    return inner.K - 1 if inner.terminated else 0


def coded_len(recipe: Recipe) -> int:
    fec = recipe.fec
    if fec.family == "rs":
        return fec.n * fec.m
    if fec.family == "ldpc":
        return fec.n
    if fec.family == "concat":
        return (fec.outer.n * fec.outer.m + tail_bits(recipe)) * len(fec.inner.generators_octal)
    return (recipe.framing.info_bits + tail_bits(recipe)) * len(fec.generators_octal)


@lru_cache(maxsize=8)
def _ldpc_gen(h_rows: tuple[int, ...], n: int, m: int):
    H = np.zeros((m, n), np.uint8)
    for i, row in enumerate(h_rows):
        for j in range(n):
            H[i, j] = (row >> j) & 1
    G, colperm = systematic_generator(H)
    return G, colperm, H


def ldpc_matrices(fec) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(G, colperm, H) for an LDPCCode, cached: G@H.T == 0, info bit i sits at codeword[colperm[i]]."""
    return _ldpc_gen(tuple(fec.h_rows), fec.n, fec.m)


def check_geometry(recipe: Recipe) -> None:
    il = recipe.interleaver
    if il.rows * il.cols != coded_len(recipe):
        raise ValueError(f"interleaver {il.rows}x{il.cols} != coded frame {coded_len(recipe)} bits")


def encode_frames_fsk(recipe: Recipe, info: np.ndarray) -> dict[str, np.ndarray]:
    """FSK variant of encode_frames: non-coherent tone bank, no pulse shaping. Returns the same coded/
    interleaved/scrambled taps plus 'tone_idx' (F, P) tone indices (ASM + body) in place of 'symbols'."""
    body_taps = encode_frames(recipe, info, _fsk_body_only=True)
    scheme = recipe.modulation.scheme
    bps = BPS[scheme]
    scr = body_taps["scrambled"]
    body_idx = gray_decode(scr.reshape(*scr.shape[:-1], -1, bps))
    asm_idx = gray_decode(asm_bits(recipe).reshape(-1, bps))
    asm_idx = np.broadcast_to(asm_idx, (info.shape[0], asm_idx.size))
    body_taps["tone_idx"] = np.concatenate([asm_idx, body_idx], 1).astype(np.int64)
    return body_taps


def encode_frames(recipe: Recipe, info: np.ndarray, _fsk_body_only: bool = False) -> dict[str, np.ndarray]:
    """info (F, Ninfo) -> taps: coded, interleaved, scrambled (F, Nc) and symbols (F, P) incl. the PHY ASM.
    FSK recipes: call encode_frames_fsk instead (this still supplies coded/interleaved/scrambled taps
    for it, via _fsk_body_only, which skips the constellation-mapping 'symbols'/'asm' step)."""
    check_geometry(recipe)
    fec, il = recipe.fec, recipe.interleaver
    if fec.family == "rs":
        if info.shape[1] != fec.k * fec.m:
            raise ValueError(f"RS({fec.n},{fec.k}) needs {fec.k * fec.m} info bits, frame has {info.shape[1]}")
        cw = rs_encode(bits_to_symbols(info, fec.m), fec.n, fec.k, fec.m)
        coded = symbols_to_bits(cw, fec.m)
    elif fec.family == "concat":
        o = fec.outer
        if info.shape[1] != o.k * o.m:
            raise ValueError(f"RS({o.n},{o.k}) outer needs {o.k * o.m} info bits, frame has {info.shape[1]}")
        outer_bits = symbols_to_bits(rs_encode(bits_to_symbols(info, o.m), o.n, o.k, o.m), o.m)
        u = np.concatenate([outer_bits, np.zeros((info.shape[0], tail_bits(recipe)), np.uint8)], 1)
        coded = conv_encode(u, fec.inner.K, tuple(fec.inner.generators_octal))
    elif fec.family == "ldpc":
        G, colperm, H = ldpc_matrices(fec)
        k = fec.n - fec.m
        if info.shape[1] != k:
            raise ValueError(f"LDPC({fec.n},{fec.m}) needs {k} info bits, frame has {info.shape[1]}")
        coded = ldpc_encode(info, G)
    else:
        u = np.concatenate([info, np.zeros((info.shape[0], tail_bits(recipe)), np.uint8)], 1)
        coded = conv_encode(u, fec.K, tuple(fec.generators_octal))
    inter = interleave(coded, il.kind, il.rows, il.cols, il.seed)
    scr = inter ^ scrambler_seq(recipe, inter.shape[1])[None]
    if _fsk_body_only:
        return {"coded": coded, "interleaved": inter, "scrambled": scr}
    body = map_symbols(recipe.modulation.scheme, scr)
    asm = np.broadcast_to(asm_symbols(recipe), (info.shape[0], asm_symbols(recipe).size))
    return {"coded": coded, "interleaved": inter, "scrambled": scr, "symbols": np.concatenate([asm, body], 1)}


def shape(symbols: np.ndarray, sps: float, rolloff: float, n_samples: int, first: float) -> np.ndarray:
    """Pulse-shape a symbol stream; symbol m is centred on (fractional) sample first + m*sps."""
    return synth_at(symbols, first + sps * np.arange(symbols.size), sps, rolloff, n_samples)


def synth_fsk(tone_idx: np.ndarray, tones_hz: np.ndarray, sps: float, fs: float, n_samples: int, first: float) -> np.ndarray:
    """Continuous-phase non-coherent MFSK: tone_idx[k] selects tones_hz[tone_idx[k]] for symbol k's
    duration; phase accumulates across symbol boundaries (avoids a click at every tone switch)."""
    out = np.zeros(n_samples, np.complex64)
    edges = first + sps * np.arange(tone_idx.size + 1)
    phase = 0.0
    for k, idx in enumerate(tone_idx):
        a, b = int(np.ceil(edges[k])), int(np.ceil(edges[k + 1]))
        a, b = max(a, 0), min(b, n_samples)
        if b <= a:
            continue
        t = (np.arange(a, b) - a) / fs
        f = float(tones_hz[idx])
        out[a:b] = np.exp(1j * (2 * np.pi * f * t + phase))
        phase = (phase + 2 * np.pi * f * (b - a) / fs) % (2 * np.pi)
    return out
