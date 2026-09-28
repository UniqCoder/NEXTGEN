"""The transmit-chain model: information bits -> code -> interleaver -> scrambler -> mapper -> pulse.
Used by the generator AND by the proof's re-synthesis, so every hypothesis is rebuilt by the same model."""
from functools import lru_cache
import numpy as np
from .recipe import Recipe
from .kernels import conv_encode, rs_encode, bits_to_symbols, symbols_to_bits, systematic_generator, ldpc_encode
from .coding import interleave, lfsr_sequence
from .demod import map_qpsk, map_symbols, BPS
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


def asm_symbols(recipe: Recipe) -> np.ndarray:
    h = recipe.framing.asm_hex
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(h), np.uint8))
    return map_qpsk(bits)


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


def encode_frames(recipe: Recipe, info: np.ndarray) -> dict[str, np.ndarray]:
    """info (F, Ninfo) -> taps: coded, interleaved, scrambled (F, Nc) and symbols (F, P) incl. the PHY ASM."""
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
    body = map_symbols(recipe.modulation.scheme, scr)
    asm = np.broadcast_to(asm_symbols(recipe), (info.shape[0], asm_symbols(recipe).size))
    return {"coded": coded, "interleaved": inter, "scrambled": scr, "symbols": np.concatenate([asm, body], 1)}


def shape(symbols: np.ndarray, sps: float, rolloff: float, n_samples: int, first: float) -> np.ndarray:
    """Pulse-shape a symbol stream; symbol m is centred on (fractional) sample first + m*sps."""
    return synth_at(symbols, first + sps * np.arange(symbols.size), sps, rolloff, n_samples)
