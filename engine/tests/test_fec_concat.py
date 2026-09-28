"""PS clause (iv): Concatenated FEC (RS outer + convolutional inner) through the known-recipe chain
and the layered proof."""
import pytest
from sanjaya.recipe import Recipe, Modulation, ConvCode, RSCode, ConcatCode, Interleaver, Scrambler, Crc, Field, Framing
from sanjaya.gen import generate
from sanjaya.pipeline import frontend, unwrap
from sanjaya.proof import prove


def concat_recipe() -> Recipe:
    m, n, k = 6, 63, 51                                  # RS outer: t=6 symbol errors
    K = 7
    outer_bits = n * m                                   # 378 bits into the conv inner code
    tail = K - 1
    coded = (outer_bits + tail) * 2                       # rate-1/2 inner -> 768 bits
    fields = [Field(name="counter", bits=16, kind="counter"), Field(name="length", bits=8, kind="length"),
              Field(name="payload", bits=254, kind="payload"), Field(name="crc", bits=16, kind="crc"),
              Field(name="fill", bits=12, kind="fill")]     # 306 = k * m
    fec = ConcatCode(outer=RSCode(n=n, k=k, m=m), inner=ConvCode(K=K, generators_octal=["171", "133"]))
    return Recipe(sample_rate_hz=9600.0 * 8, modulation=Modulation(scheme="qpsk", symbol_rate_hz=9600.0, rolloff=0.35),
                  fec=fec, interleaver=Interleaver(rows=24, cols=coded // 24),
                  scrambler=Scrambler(poly_exponents=[8, 7, 5, 3, 0], seed=0xFF),
                  framing=Framing(asm_hex="1ACFFC1D", fields=fields, crc=Crc(width=16, poly=0x1021, init=0xFFFF)))


def test_concat_decodes_bit_exact_with_channel_noise():
    x, r, truth, taps = generate(recipe=concat_recipe(), esn0_db=6.0, n_frames=20)
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()
    assert uw.fec_ok is not None and uw.fec_ok.all()


def test_concat_passes_every_proof_layer():
    x, r, *_ = generate(recipe=concat_recipe(), esn0_db=6.0, n_frames=20)
    assert [v.verdict for v in prove(x, r)] == ["pass", "pass", "pass"]


def test_concat_wrong_scrambler_fails():
    x, r, *_ = generate(recipe=concat_recipe(), esn0_db=6.0, n_frames=20)
    wrong = r.model_copy(update={"scrambler": r.scrambler.model_copy(update={"seed": 0xFE})})
    assert any(v.verdict == "fail" for v in prove(x, wrong))
