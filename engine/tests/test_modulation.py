"""PS clause (ii)/(iii): known-recipe demod for every modulation scheme, and every interleaver kind,
decode bit-exact. Pins the BPSK/QPSK/8PSK/16QAM/64QAM generalisation and the diagonal/random interleavers."""
import pytest
from sanjaya.gen import gen0_recipe, generate
from sanjaya.recipe import Modulation, Interleaver
from sanjaya.pipeline import frontend, unwrap

SCHEME_ESN0 = {"bpsk": 8.0, "qpsk": 10.0, "8psk": 16.0, "16qam": 20.0, "64qam": 26.0}


@pytest.mark.parametrize("scheme,esn0_db", SCHEME_ESN0.items())
def test_modulation_scheme_decodes_bit_exact(scheme, esn0_db):
    base = gen0_recipe()
    recipe = base.model_copy(update={"modulation": Modulation(scheme=scheme, symbol_rate_hz=base.modulation.symbol_rate_hz,
                                                               rolloff=base.modulation.rolloff)})
    x, r, truth, taps = generate(recipe=recipe, esn0_db=esn0_db, n_frames=20)
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()


@pytest.mark.parametrize("kind,seed", [("block", None), ("diagonal", None), ("random", 1234)])
def test_interleaver_kind_decodes_bit_exact(kind, seed):
    base = gen0_recipe()
    il = base.interleaver
    recipe = base.model_copy(update={"interleaver": Interleaver(kind=kind, rows=il.rows, cols=il.cols, seed=seed)})
    x, r, truth, taps = generate(recipe=recipe, esn0_db=10.0, n_frames=20)
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()
