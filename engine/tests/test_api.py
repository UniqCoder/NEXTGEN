"""Engine API: security rules (PRD §6.8, §12.2) and a full blind job producing UI-shaped data."""
import json
import time
from pathlib import Path
import numpy as np
from fastapi.testclient import TestClient
from sanjaya.api import create_app
from sanjaya.gen import generate
from sanjaya.io import write_sigmf, sha256_file
from sanjaya.search import blind_search
from sanjaya.proof.certificate import build_body, sign

TOKEN, PORT = "t0k", 8765
H = {"host": f"127.0.0.1:{PORT}", "x-sanjaya-token": TOKEN}
SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"


def client(tmp_path, samples_dir=None):
    return TestClient(create_app(TOKEN, PORT, tmp_path / "jobs", samples_dir=samples_dir), base_url=f"http://127.0.0.1:{PORT}")


def wait(c, jid):
    for _ in range(600):
        st = c.get(f"/v1/jobs/{jid}", headers=H).json()
        if st["state"] not in ("queued", "running"):
            return st
        time.sleep(0.1)
    raise TimeoutError(st)


def test_security_rules(tmp_path):
    c = client(tmp_path)
    assert c.get("/v1/health", headers=H).status_code == 200
    assert c.get("/v1/health", headers={**H, "host": "evil.example:8765"}).status_code == 403      # DNS rebinding
    assert c.get("/v1/health", headers={**H, "origin": "http://evil.example"}).status_code == 403  # foreign page
    assert c.get("/v1/health", headers={"host": H["host"]}).status_code == 401                     # no token
    assert c.get("/v1/health", headers={**H, "origin": "http://localhost:5173"}).status_code == 403  # dev origin off by default


def test_blind_job_end_to_end(tmp_path):
    x, r, truth, taps = generate(seed=3, esn0_db=11.0)
    data = write_sigmf(tmp_path / "rec", x, r.sample_rate_hz)
    c = client(tmp_path)
    jid = c.post(f"/v1/jobs?name=rec.sigmf-data&path={data}", headers=H).json()["id"]
    st = wait(c, jid)
    assert st["state"] == "done", st
    assert st["stages"][:6] == ["done"] * 6 and st["verdict"] == "pass"
    sc = c.get(f"/v1/jobs/{jid}/scenario", headers=H).json()
    assert sc["scenario"]["params"]["fec"]["value"].startswith("CC K=7")
    assert sc["frame"]["len"] == len(sc["bits"]) // truth["n_frames"] and sc["crc"][0]["ok"] == truth["n_frames"]
    sp = c.get(f"/v1/jobs/{jid}/spectrogram/full", headers=H)
    assert int(sp.headers["x-rows"]) * int(sp.headers["x-bins"]) * 4 == len(sp.content)
    assert c.get(f"/v1/jobs/{jid}/certificate.json", headers=H).json()["body"]["verdict"] == "pass"


def test_samples_endpoint_lists_the_demo_library(tmp_path):
    if not (SAMPLES_DIR / "manifest.json").is_file():
        import pytest
        pytest.skip("sample library not built (scripts/make_samples.py)")
    c = client(tmp_path, samples_dir=SAMPLES_DIR)
    items = c.get("/v1/samples", headers=H).json()
    assert any(s["id"] == "syn-qpsk-k7-48x32-12db" for s in items)
    assert c.post(f"/v1/jobs?name=x&sample=no-such-id", headers=H).status_code == 404


def test_sample_job_runs_end_to_end(tmp_path):
    if not (SAMPLES_DIR / "manifest.json").is_file():
        import pytest
        pytest.skip("sample library not built (scripts/make_samples.py)")
    c = client(tmp_path, samples_dir=SAMPLES_DIR)
    jid = c.post("/v1/jobs?name=x&sample=syn-qpsk-k7-48x32-12db", headers=H).json()["id"]
    st = wait(c, jid)
    assert st["state"] == "done" and st["verdict"] == "pass"


def test_undecided_job_returns_partial_scenario(tmp_path):
    """No recipe survives on pure noise: the job must still hand back a real spectrogram and measured
    band/SNR instead of a bare error (PROTOTYPE_PLAN §5, 'honest undecided')."""
    rng = np.random.default_rng(0)
    noise = (rng.standard_normal(200_000) + 1j * rng.standard_normal(200_000)).astype(np.complex64) * 0.05
    data = write_sigmf(tmp_path / "noise", noise, 76_800.0)
    c = client(tmp_path)
    jid = c.post(f"/v1/jobs?name=noise.sigmf-data&path={data}", headers=H).json()["id"]
    st = wait(c, jid)
    assert st["state"] == "undecided" and st["verdict"] == "undecided"
    sc = c.get(f"/v1/jobs/{jid}/scenario", headers=H).json()
    assert sc["scenario"]["view"]["verdict"] == "undecided"
    assert sc["scenario"]["view"]["reason"]
    sp = c.get(f"/v1/jobs/{jid}/spectrogram/full", headers=H)
    assert int(sp.headers["x-rows"]) * int(sp.headers["x-bins"]) * 4 == len(sp.content)
    assert c.get(f"/v1/jobs/{jid}/certificate.json", headers=H).status_code == 409


def test_decoded_job_releases_a_gated_receiver(tmp_path):
    x, r, truth, _ = generate(seed=3, esn0_db=11.0)
    data = write_sigmf(tmp_path / "rec", x, r.sample_rate_hz)
    c = client(tmp_path)
    jid = c.post(f"/v1/jobs?name=rec.sigmf-data&path={data}", headers=H).json()["id"]
    assert wait(c, jid)["state"] == "done"
    gate = c.get(f"/v1/jobs/{jid}/scenario", headers=H).json()["scenario"]["view"]["compiler"]
    assert gate["passed"] and gate["frames_equal"] == truth["n_frames"]
    z = c.get(f"/v1/jobs/{jid}/receiver.zip", headers=H)
    assert z.status_code == 200 and z.content[:2] == b"PK"


def test_verify_endpoint_reproduces_tamper_and_wrong_file(tmp_path):
    x, r, truth, _ = generate(seed=5, esn0_db=11.0)
    data = write_sigmf(tmp_path / "rec", x, r.sample_rate_hz)
    meta_text = data.with_suffix(".sigmf-meta").read_text()
    recipe, _ = blind_search(x, r.sample_rate_hz)
    sha = sha256_file(data)
    cert = sign(build_body(x, recipe, sha, "search"))
    c = client(tmp_path)

    def post(cert_obj, fname, fbytes, **form):
        files = {"certificate": ("cert.json", json.dumps(cert_obj), "application/json"),
                "recording": (fname, fbytes, "application/octet-stream")}
        return c.post("/v1/verify", headers=H, files=files, data=form)

    ok = post(cert, "rec.sigmf-data", open(data, "rb").read(), sigmf=meta_text)
    assert ok.status_code == 200 and ok.json() == {"reproduced": True, "problems": [], "certificate_id": ok.json()["certificate_id"],
                                                    "verdict": "pass", "signature": "valid"}

    bad = json.loads(json.dumps(cert))
    bad["body"]["layers"][0]["stats"]["T2_resid_to_noise_db"] = 0.0
    tampered = post(bad, "rec.sigmf-data", open(data, "rb").read(), sigmf=meta_text)
    r2 = tampered.json()
    assert not r2["reproduced"] and r2["signature"] == "INVALID"

    noise = (np.random.default_rng(0).standard_normal(50_000)).astype("float32").tobytes()
    wrong = post(cert, "wrong.sigmf-data", noise, fs=str(r.sample_rate_hz), dtype="cf32_le")
    r3 = wrong.json()
    assert not r3["reproduced"] and "could not be re-applied" in r3["problems"][0]
