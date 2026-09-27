"""Physics-expert PHY identification (classify.identify) on real off-air recordings and on Gen files.
Truth for the real files is their published standard (sigidwiki.com); nothing here was trained on them."""
from pathlib import Path

import numpy as np
import pytest

from sanjaya.classify import identify
from sanjaya.gen import generate
from sanjaya.io import load

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

REAL = [
    # file, modulation, rate (Bd), rate tolerance, standard that must be among the matches
    ("real-stanag4285-idle.wav", "PSK (order not separable)", 2400.0, 1.0, "STANAG 4285"),
    ("real-hfdl-1200.wav", "QPSK", 1800.0, 1.0, "HFDL"),
    ("real-psk31.wav", "BPSK", 31.25, 0.05, "PSK31"),
    ("real-sitor-b.wav", "2-FSK", 100.0, 1.0, "NAVTEX / SITOR-B"),
    ("real-ale-2g.wav", "8-FSK", 125.0, 1.0, "2G ALE (MIL-STD-188-141)"),
]


@pytest.mark.parametrize("fname,mod,rate,tol,std", REAL)
def test_real_recording_identified(fname, mod, rate, tol, std):
    path = SAMPLES / fname
    if not path.exists():
        pytest.skip("sample library not built (scripts/make_samples.py)")
    x, fs, _ = load(path)
    r = identify(x, fs)
    assert r["modulation"] == mod
    assert abs(r["rate_hz"] - rate) < tol
    assert std in [s["name"] for s in r["standards"]]


def test_stanag_idle_pattern_line_is_not_taken_for_the_symbol_rate():
    """The idle pattern puts a stronger |x|^2 line at ~1462 Hz than the 2400 Bd clock; only the band-edge
    line is the symbol clock."""
    path = SAMPLES / "real-stanag4285-idle.wav"
    if not path.exists():
        pytest.skip("sample library not built")
    x, fs, _ = load(path)
    r = identify(x, fs)
    assert r["rate_strength"] > 2 * r["rate_runner_up"]


@pytest.mark.parametrize("esn0", [12.0, 7.0])
def test_gen_qpsk_identified(esn0):
    x, recipe, truth, _ = generate(seed=5, esn0_db=esn0)
    r = identify(x, recipe.sample_rate_hz)
    assert r["modulation"] == "QPSK"
    assert abs(r["rate_hz"] - recipe.modulation.symbol_rate_hz) < 0.5
    assert r["standards"] == []                        # no named standard is claimed for a private format
    assert r["symbols"].size > 1000


def test_noise_is_not_an_emission():
    rng = np.random.default_rng(1)
    x = (rng.standard_normal(200_000) + 1j * rng.standard_normal(200_000)).astype(np.complex64)
    assert identify(x, 76_800.0) is None


def test_short_weak_capture_makes_no_false_order_claim():
    """0.66 s at 7 dB: the rate is still right, but the expert must not claim an order it cannot see."""
    x, recipe, truth, _ = generate(seed=149, esn0_db=7.0, n_frames=7)
    r = identify(x, recipe.sample_rate_hz)
    assert abs(r["rate_hz"] - 9600) < 1 and r["order"] in (None, 4)
