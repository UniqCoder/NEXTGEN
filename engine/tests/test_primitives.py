import numpy as np
import pytest
from scipy.stats import norm
from sanjaya.kernels import conv_encode, viterbi_soft
from sanjaya.coding import block_interleave, block_deinterleave, lfsr_sequence, syndrome_rate_half
from sanjaya.bits import crc_bits


def test_ccsds_randomiser_reference_bytes():
    assert bytes(np.packbits(lfsr_sequence([8, 7, 5, 3, 0], 0xFF, 40))).hex() == "ff480ec09a"


def test_crc16_ccitt_false_check_value():
    assert crc_bits(np.unpackbits(np.frombuffer(b"123456789", np.uint8)), 16, 0x1021, 0xFFFF) == 0x29B1


def test_crc32_check_value():
    bits = np.unpackbits(np.frombuffer(b"123456789", np.uint8))
    assert crc_bits(bits, 32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF) == 0xCBF43926


def test_block_interleaver_round_trip_and_mapping():
    x = np.arange(48 * 32)
    y = block_interleave(x, 48, 32)
    assert y[1] == 32 and (block_deinterleave(y, 48, 32) == x).all()


@pytest.mark.parametrize("K,gens", [(3, ("7", "5")), (5, ("23", "35")), (7, ("171", "133")), (9, ("753", "561"))])
def test_viterbi_clean_round_trip_and_syndrome(K, gens):
    u = np.random.default_rng(K).integers(0, 2, (4, 300)).astype(np.uint8)
    u[:, -(K - 1):] = 0
    c = conv_encode(u, K, gens)
    assert syndrome_rate_half(c, K, gens).max() == 0
    assert (viterbi_soft(2 * (1 - 2 * c.astype(np.float32)), K, gens) == u).all()


def test_viterbi_matches_theory_at_3db():
    """K=7 soft Viterbi, QPSK Es/N0 = 3 dB (Eb/N0 = 3 dB at rate 1/2): post-FEC BER well below the
    uncoded 2.3e-2; union-bound territory is ~1e-3 or lower."""
    rng = np.random.default_rng(3)
    u = rng.integers(0, 2, (50, 1000)).astype(np.uint8)
    u[:, -6:] = 0
    c = conv_encode(u, 7, ("171", "133")).astype(np.float32)
    esn0 = 10 ** 0.3
    sigma = np.sqrt(1 / (2 * esn0))                              # per real dimension, unit-energy QPSK
    y = (1 - 2 * c) / np.sqrt(2) + sigma * rng.standard_normal(c.shape)
    uh = viterbi_soft(2 * np.sqrt(2) * y / (2 * sigma ** 2), 7, ("171", "133"))
    ber = (uh != u).mean()
    assert ber < 3e-3 < norm.sf(np.sqrt(esn0))
