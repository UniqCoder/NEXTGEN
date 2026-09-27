"""G1 vertical slice (PRD §11.3): Gen v0 file decoded with the known recipe; layered proof passes;
certificate signed and independently re-checked; wrong recipes and tampering are caught."""
import json
import numpy as np
import pytest
from sanjaya.gen import generate
from sanjaya.pipeline import frontend, unwrap
from sanjaya.proof import prove
from sanjaya.proof import certificate as C


@pytest.fixture(scope="module", params=[12.0, 8.0])
def rec(request):
    return generate(seed=147, esn0_db=request.param)


@pytest.fixture(autouse=True)
def key_home(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "KEY_FILE", tmp_path / "k.pem")


def test_decode_is_bit_exact(rec):
    x, r, truth, taps = rec
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert abs(fe.cfo_hz - truth["cfo_hz"]) < 1.0
    assert abs(fe.esn0_db - truth["esn0_db"]) < 0.5
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()


def test_right_recipe_passes_every_layer(rec):
    x, r, *_ = rec
    assert [v.verdict for v in prove(x, r)] == ["pass", "pass", "pass"]


@pytest.mark.parametrize("change", [
    {"fec": {"generators_octal": ["133", "171"]}},
    {"interleaver": {"rows": 32, "cols": 48}},
    {"scrambler": {"seed": 0xFE}},
    {"modulation": {"rolloff": 0.05}},     # PHY resolution shrinks with SNR: +-0.2 caught at 12 dB, +-0.3 at 8 dB
])
def test_wrong_recipe_fails(rec, change):
    x, r, *_ = rec
    (sect, upd), = change.items()
    wrong = r.model_copy(update={sect: getattr(r, sect).model_copy(update=upd)})
    assert any(v.verdict == "fail" for v in prove(x, wrong))


def test_certificate_signed_verified_and_deterministic(rec):
    x, r, *_ = rec
    b1 = C.build_body(x, r, "abc")
    b2 = C.build_body(x, r, "abc")
    assert C.canonical(b1.model_dump(mode="json")) == C.canonical(b2.model_dump(mode="json"))    # NFR-06
    cert = json.loads(json.dumps(C.sign(b1)))
    assert cert["status"] == "SIGNED" and C.check_signature(cert) == "valid"
    assert C.verify(x, "abc", cert) == []
    assert any("SHA-256" in p for p in C.verify(x, "other-file", cert))
    cert["body"]["layers"][0]["stats"]["T2_resid_to_noise_db"] = 0.0
    assert C.check_signature(cert) == "INVALID"


def test_certificate_lists_undecidable_neighbours(rec):
    x, r, *_ = rec
    body = C.build_body(x, r, "abc")
    assert body.verdict == "pass" and body.attempts_k == 1 and body.false_pass_bound is None
    coding_structure = [n for n in body.near_misses if n.layer != "phy"]
    assert coding_structure and all(n.rejected for n in coding_structure)
    assert all(e.startswith("not separable") for e in body.equivalences)
