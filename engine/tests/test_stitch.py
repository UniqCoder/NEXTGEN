"""USP 3b Evidence Stitching + Sensor Twin: one emitter seen by three sensors (different ADC rates, clocks, tuning,
gains, SNRs, one with an inverted spectrum). Each capture is too short alone; pooled, the recipe is found blind,
proven on every capture separately, and a capture of a different emitter is caught and left out."""
import numpy as np
import pytest

from sanjaya.gen import generate, gen0_recipe
from sanjaya.recipe import Scrambler
from sanjaya.stitch import stitch
from test_search import variant

SENSORS = [  # seed, samples/symbol, Es/N0, frames, clock ppm, gain, tuning offset Hz, inverted spectrum
    (201, 8.0, 7.5, 7, 0.0, 0.3, 120.0, False),
    (202, 6.37, 6.5, 6, -25.0, 0.05, -310.0, True),
    (203, 10.0, 7.0, 6, 40.0, 1.2, 55.0, False),
]


def capture(seed, sps, esn0, frames, ppm, gain, cfo, inverted, recipe=None):
    x, r, *_ = generate(seed=seed, esn0_db=esn0, n_frames=frames, recipe=recipe or gen0_recipe(sps=sps),
                        clock_ppm=ppm, gain=gain, cfo_hz=cfo)
    return (np.conj(x) if inverted else x), r.sample_rate_hz


@pytest.fixture(scope="module")
def three():
    return [capture(*s) + (f"sensor {n}",) for s, n in zip(SENSORS, "ABC")]


def test_pooled_captures_decode_and_each_is_proven(three):
    recipe, log, rep, ref = stitch(three)
    assert recipe.fec.K == 7 and recipe.fec.generators_octal == ["171", "133"]
    assert (recipe.interleaver.rows, recipe.interleaver.cols) == (48, 32) and recipe.framing.crc is not None
    for s in rep["sensors"]:
        assert s["alone"]["verdict"] == "undecided"                 # none of them is enough on its own
        assert s["proof"] == ["pass", "pass", "pass"] and s["crc_ok"] == s["crc_frames"] == s["frames"]


def test_sensor_twin_matches_each_sensor(three):
    _, _, rep, _ = stitch(three)
    by = {s["name"]: s for s in rep["sensors"]}
    ppm = {n: by[f"sensor {n}"]["clock_ppm"] for n in "ABC"}
    # clocks are only observable relative to each other: compare differences with the truth
    assert abs((ppm["B"] - ppm["A"]) - (-25.0)) < 8 and abs((ppm["C"] - ppm["A"]) - 40.0) < 8
    assert abs(by["sensor A"]["cfo_hz"] - 120.0) < 2 and abs(by["sensor C"]["cfo_hz"] - 55.0) < 2
    assert by["sensor B"]["inverted"] and not by["sensor A"]["inverted"]
    assert abs(by["sensor B"]["cfo_hz"] - 310.0) < 2                # the inverted spectrum mirrors the offset
    assert by["sensor C"]["gain_db"] - by["sensor B"]["gain_db"] > 25


def test_capture_of_another_emitter_is_caught(three):
    decoy = capture(204, 8.0, 8.0, 6, 0.0, 0.3, 0.0, False,
                    recipe=variant(5, ["23", "35"], 24, 64, Scrambler(poly_exponents=[9, 5, 0], seed=0x1AB)))
    recipe, _, rep, _ = stitch(three + [decoy + ("decoy",)])
    by = {s["name"]: s for s in rep["sensors"]}
    assert not by["decoy"]["consistent"] and by["decoy"].get("excluded")
    assert recipe.framing.crc is not None and all(by[f"sensor {n}"]["crc_ok"] == by[f"sensor {n}"]["frames"] for n in "ABC")
