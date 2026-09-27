"""The transmit-chain model: information bits -> code -> interleaver -> scrambler -> mapper -> pulse.
Used by the generator AND by the proof's re-synthesis, so every hypothesis is rebuilt by the same model."""
from functools import lru_cache
import numpy as np
from .recipe import Recipe
from .kernels import conv_encode
from .coding import block_interleave, lfsr_sequence
from .demod import map_qpsk, rrc_taps, filt0


def sps_of(recipe: Recipe) -> int:
    sps = recipe.sample_rate_hz / recipe.modulation.symbol_rate_hz
    if abs(sps - round(sps)) > 1e-9:
        # ponytail: integer samples/symbol only; the polyphase resampler arrives with WP03 receivers
        raise NotImplementedError(f"non-integer samples/symbol ({sps:.4f}) not supported in schema 0.1")
    return int(round(sps))


@lru_cache(maxsize=16)
def _scr(poly: tuple[int, ...], seed: int, n: int) -> np.ndarray:
    return lfsr_sequence(list(poly), seed, n)


def scrambler_seq(recipe: Recipe, n: int) -> np.ndarray:
    s = recipe.scrambler
    return _scr(tuple(s.poly_exponents), s.seed, n)


def asm_symbols(recipe: Recipe) -> np.ndarray:
    h = recipe.framing.asm_hex
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(h), np.uint8))
    return map_qpsk(bits)


def tail_bits(recipe: Recipe) -> int:
    return recipe.fec.K - 1 if recipe.fec.terminated else 0


def coded_len(recipe: Recipe) -> int:
    return (recipe.framing.info_bits + tail_bits(recipe)) * len(recipe.fec.generators_octal)


def check_geometry(recipe: Recipe) -> None:
    il = recipe.interleaver
    if il.rows * il.cols != coded_len(recipe):
        raise ValueError(f"interleaver {il.rows}x{il.cols} != coded frame {coded_len(recipe)} bits")


def encode_frames(recipe: Recipe, info: np.ndarray) -> dict[str, np.ndarray]:
    """info (F, Ninfo) -> taps: coded, interleaved, scrambled (F, Nc) and symbols (F, P) incl. the PHY ASM."""
    check_geometry(recipe)
    fec, il = recipe.fec, recipe.interleaver
    u = np.concatenate([info, np.zeros((info.shape[0], tail_bits(recipe)), np.uint8)], 1)
    coded = conv_encode(u, fec.K, tuple(fec.generators_octal))
    inter = block_interleave(coded, il.rows, il.cols)
    scr = inter ^ scrambler_seq(recipe, inter.shape[1])[None]
    body = map_qpsk(scr)
    asm = np.broadcast_to(asm_symbols(recipe), (info.shape[0], asm_symbols(recipe).size))
    return {"coded": coded, "interleaved": inter, "scrambled": scr, "symbols": np.concatenate([asm, body], 1)}


def shape(symbols: np.ndarray, sps: int, rolloff: float, n_samples: int, first_center: int) -> np.ndarray:
    """Pulse-shape a symbol stream; symbol m is centred on sample first_center + m*sps."""
    s = np.zeros(n_samples, np.complex64)
    idx = first_center + sps * np.arange(symbols.size)
    ok = (idx >= 0) & (idx < n_samples)
    s[idx[ok]] = symbols[ok]
    return filt0(s, rrc_taps(sps, rolloff))
