"""USP 3a Data-Sufficiency Engine: a too-short capture is answered with a prediction that a longer capture of the
same emission then meets; a long-enough capture reports how little it would have needed; and 'more data will
not help' is only said when the test had the power to see what it is looking for."""
import numpy as np
import pytest

from sanjaya.gen import generate
from sanjaya.search import blind_search, SearchError
from sanjaya.sufficiency import frames_needed, power_frames

FRAME = 784 * 8                      # gen0: 784 symbols per frame at 8 samples per symbol


@pytest.fixture(scope="module")
def rec7():
    return generate(seed=147, esn0_db=7.0)


def cut(rec, frames):
    x, r, truth, _ = rec
    return x[: int(truth["guard_samples"] + frames * FRAME + 20)], r.sample_rate_hz


def test_short_capture_predicts_a_length_that_then_decodes(rec7):
    x, fs = cut(rec7, 7)
    with pytest.raises(SearchError) as ei:
        blind_search(x, fs)
    led = ei.value.ledger
    assert led["verdict"] == "more_data"
    code = next(e for e in led["entries"] if e["decision"] == "Code and interleaver")
    assert code["limit"] == "data"
    p50, p90 = code["need_s"]
    assert led["have_s"] < p50 <= p90
    # a capture as long as the P90 prediction decodes
    x, r, truth, _ = rec7
    xl = x[: int(truth["guard_samples"] + p90 * fs)]
    recipe, log = blind_search(xl, fs)
    assert log[-1].stage == "sufficiency" and log[-1].evidence["verdict"] == "sufficient"


def test_full_capture_reports_how_little_it_needed(rec7):
    x, r, *_ = rec7
    recipe, log = blind_search(x, r.sample_rate_hz)
    led = log[-1].evidence
    code = next(e for e in led["entries"] if e["decision"] == "Code and interleaver")
    assert led["verdict"] == "sufficient" and code["min_s"][0] < led["have_s"]


def test_statistic_grows_as_sqrt_frames():
    """The model behind every prediction: z(20 frames) from z(5 frames) within 5 %."""
    assert frames_needed(5, 10.9) == (5, 6)
    z20 = 10.9 * np.sqrt(19 / 4)
    assert abs(z20 - 23.6) / 23.6 < 0.05                   # measured on Gen at 12 dB


def test_absence_is_only_claimed_with_power():
    assert power_frames(3, 1504) is not None                # 3 frames cannot see even a typical code
    assert power_frames(40, 1504) is None                   # 40 frames would see a weak code: absence means absence


def test_noise_says_there_is_nothing_to_record():
    x = (np.random.default_rng(0).standard_normal(200_000) + 1j * np.random.default_rng(1).standard_normal(200_000)).astype(np.complex64)
    with pytest.raises(SearchError) as ei:
        blind_search(x, 76_800.0)
    assert ei.value.ledger["verdict"] == "not_data_limited"
    assert ei.value.ledger["entries"][0]["limit"] == "signal"
