"""PS clause (iv): LDPC FEC (systematic encode + min-sum belief propagation) through the known-recipe chain
and the layered proof."""
import numpy as np
import pytest
from sanjaya.recipe import Recipe, Modulation, LDPCCode, Interleaver, Scrambler, Crc, Field, Framing
from sanjaya.gen import generate
from sanjaya.pipeline import frontend, unwrap
from sanjaya.proof import prove

N, M = 200, 100                                          # rate 1/2, k = 100 info bits


def _h_rows() -> list[int]:
    rng = np.random.default_rng(42)
    H = np.zeros((M, N), np.uint8)
    for j in range(N):
        H[rng.choice(M, size=3, replace=False), j] = 1
    return [int(sum(int(b) << j for j, b in enumerate(row))) for row in H]


H_ROWS = _h_rows()


def ldpc_recipe() -> Recipe:
    fields = [Field(name="counter", bits=16, kind="counter"), Field(name="length", bits=8, kind="length"),
              Field(name="payload", bits=52, kind="payload"), Field(name="crc", bits=16, kind="crc"),
              Field(name="fill", bits=8, kind="fill")]      # 100 = k
    fec = LDPCCode(n=N, m=M, h_rows=H_ROWS, max_iters=30)
    return Recipe(sample_rate_hz=9600.0 * 8, modulation=Modulation(scheme="qpsk", symbol_rate_hz=9600.0, rolloff=0.35),
                  fec=fec, interleaver=Interleaver(rows=10, cols=20),
                  scrambler=Scrambler(poly_exponents=[8, 7, 5, 3, 0], seed=0xFF),
                  framing=Framing(asm_hex="1ACFFC1D", fields=fields, crc=Crc(width=16, poly=0x1021, init=0xFFFF)))


def test_ldpc_decodes_bit_exact_with_channel_noise():
    x, r, truth, taps = generate(recipe=ldpc_recipe(), esn0_db=8.0, n_frames=15)
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()
    assert uw.fec_ok is not None and uw.fec_ok.all()


def test_ldpc_passes_every_proof_layer():
    x, r, *_ = generate(recipe=ldpc_recipe(), esn0_db=8.0, n_frames=15)
    assert [v.verdict for v in prove(x, r)] == ["pass", "pass", "pass"]


def test_ldpc_wrong_scrambler_fails():
    x, r, *_ = generate(recipe=ldpc_recipe(), esn0_db=8.0, n_frames=15)
    wrong = r.model_copy(update={"scrambler": r.scrambler.model_copy(update={"seed": 0xFE})})
    assert any(v.verdict == "fail" for v in prove(x, wrong))
