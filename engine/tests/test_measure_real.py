"""Real HF recordings (samples/real-*.wav) against their published parameters (sigidwiki.com).
occupied_band + band_measure are best-effort spectral estimators, not the certified blind search;
this only checks they land in the right ballpark, so a regression like the old floor-estimation bug
(band collapsing to one bin, or picking up the empty analytic mirror as "noise") gets caught."""
from pathlib import Path

import pytest

from sanjaya.io import read_wav
from sanjaya.measure import band_measure, occupied_band

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

CASES = [
    # (file, published centre Hz, published rate Bd, rate tolerance)
    ("real-stanag4285-idle.wav", 1800, None, None),
    ("real-mil188-110a-2400.wav", 1800, None, None),
    ("real-hfdl-1200.wav", 1440, None, None),
    ("real-psk31.wav", None, 31.25, 0.5),
    ("real-sitor-b.wav", None, 100, 5),
]


@pytest.mark.parametrize("fname,centre_hz,rate_hz,rate_tol", CASES)
def test_band_centre_and_rate(fname, centre_hz, rate_hz, rate_tol):
    path = SAMPLES / fname
    if not path.exists():
        pytest.skip("sample library not built (scripts/make_samples.py)")
    x, fs = read_wav(path)
    lo, hi, centre, snr, _floor = occupied_band(x, fs)
    assert hi > lo                                    # never collapses to a single bin
    assert snr > 10                                    # real signal, not noise
    if centre_hz is not None:
        assert abs(centre - centre_hz) < 250            # occupied-band centre within ~1/8 of an HF audio channel
    if rate_hz is not None:
        m = band_measure(x, fs, lo, hi)
        assert abs(m["rate_hz"] - rate_hz) < rate_tol    # symbol-clock line, where the family is single-tone/FSK


def test_sitor_b_tone_pair():
    """SITOR-B/NAVTEX is 2-tone FSK, 170 Hz shift: tone detection must not report the PSK-style sideband
    clutter the old low-prominence threshold picked up."""
    path = SAMPLES / "real-sitor-b.wav"
    if not path.exists():
        pytest.skip("sample library not built (scripts/make_samples.py)")
    x, fs = read_wav(path)
    lo, hi, *_ = occupied_band(x, fs)
    tones = band_measure(x, fs, lo, hi)["tones_hz"]
    assert len(tones) == 2
    assert abs(abs(tones[1] - tones[0]) - 170) < 40


def test_ale_eight_tone_set():
    """MIL-STD-188-141 ALE: 8 tones spaced ~250 Hz apart."""
    path = SAMPLES / "real-ale-2g.wav"
    if not path.exists():
        pytest.skip("sample library not built (scripts/make_samples.py)")
    x, fs = read_wav(path)
    lo, hi, *_ = occupied_band(x, fs)
    tones = sorted(band_measure(x, fs, lo, hi)["tones_hz"])
    assert len(tones) == 8
    spacings = [b - a for a, b in zip(tones, tones[1:])]
    assert all(abs(s - 250) < 30 for s in spacings)
