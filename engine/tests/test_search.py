"""G2: the engine finds the recipe by itself (blind), and says 'undecided' when there is nothing to find."""
import numpy as np
import pytest
from sanjaya.gen import generate, gen0_recipe
from sanjaya.recipe import ConvCode, Interleaver, Scrambler
from sanjaya.search import blind_search, SearchError
from sanjaya.proof import prove


def variant(K, gens, rows, cols, scr, sps=8.0):
    r = gen0_recipe(sps=sps)
    fields = r.framing.fields
    fill = rows * cols // 2 - (K - 1) - sum(f.bits for f in fields if f.kind != "fill")
    fields = [f if f.kind != "fill" else f.model_copy(update={"bits": fill}) for f in fields]
    return r.model_copy(update={"fec": ConvCode(K=K, generators_octal=gens), "interleaver": Interleaver(rows=rows, cols=cols),
                                "scrambler": scr, "framing": r.framing.model_copy(update={"fields": fields})})


CASES = {
    "gen0 10dB -30ppm": (None, 10.0, 30),
    "K5 24x64 PRBS-9": (variant(5, ["23", "35"], 24, 64, Scrambler(poly_exponents=[9, 5, 0], seed=0x1AB)), 10.0, -12),
    "K9 no scrambler sps 6.37": (variant(9, ["753", "561"], 48, 32, None, sps=6.37), 12.0, 0),
    "K7 no interleaver, blind-degree scrambler": (variant(7, ["171", "133"], 1, 1536, Scrambler(poly_exponents=[6, 5, 0], seed=0x2D)), 10.0, 5),
}


@pytest.mark.parametrize("name", list(CASES))
def test_blind_search_recovers_recipe_and_proves(name):
    recipe, esn0, ppm = CASES[name]
    x, r, truth, taps = generate(seed=11, esn0_db=esn0, recipe=recipe, clock_ppm=ppm)
    found, log = blind_search(x, r.sample_rate_hz)
    assert found.fec.K == r.fec.K and found.fec.generators_octal == r.fec.generators_octal
    ident = lambda i: i.rows in (1, i.rows * i.cols)
    assert (found.interleaver.rows, found.interleaver.cols) == (r.interleaver.rows, r.interleaver.cols) or \
           (ident(found.interleaver) and ident(r.interleaver))
    assert found.scrambler == r.scrambler
    assert found.framing.asm_hex == r.framing.asm_hex and found.framing.crc == r.framing.crc
    assert abs(found.modulation.symbol_rate_hz / 9600 - 1 + ppm * 1e-6 / (1 + ppm * 1e-6)) < 5e-6
    assert [v.verdict for v in prove(x, found)] == ["pass", "pass", "pass"]


def test_noise_only_is_undecided_not_a_recipe():
    x = (np.random.default_rng(0).standard_normal(300_000) + 1j * np.random.default_rng(1).standard_normal(300_000)).astype(np.complex64)
    with pytest.raises(SearchError):
        blind_search(x, 76_800.0)
