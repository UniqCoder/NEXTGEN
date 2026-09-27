"""Engine API: security rules (PRD §6.8, §12.2) and a full blind job producing UI-shaped data."""
import time
import numpy as np
from fastapi.testclient import TestClient
from sanjaya.api import create_app
from sanjaya.gen import generate
from sanjaya.io import write_sigmf

TOKEN, PORT = "t0k", 8765
H = {"host": f"127.0.0.1:{PORT}", "x-sanjaya-token": TOKEN}


def client(tmp_path):
    return TestClient(create_app(TOKEN, PORT, tmp_path / "jobs"), base_url=f"http://127.0.0.1:{PORT}")


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
    for _ in range(600):
        st = c.get(f"/v1/jobs/{jid}", headers=H).json()
        if st["state"] not in ("queued", "running"):
            break
        time.sleep(0.1)
    assert st["state"] == "done", st
    assert st["stages"][:6] == ["done"] * 6 and st["verdict"] == "pass"
    sc = c.get(f"/v1/jobs/{jid}/scenario", headers=H).json()
    assert sc["scenario"]["params"]["fec"]["value"].startswith("CC K=7")
    assert sc["frame"]["len"] == len(sc["bits"]) // truth["n_frames"] and sc["crc"][0]["ok"] == truth["n_frames"]
    sp = c.get(f"/v1/jobs/{jid}/spectrogram/full", headers=H)
    assert int(sp.headers["x-rows"]) * int(sp.headers["x-bins"]) * 4 == len(sp.content)
    assert c.get(f"/v1/jobs/{jid}/certificate.json", headers=H).json()["body"]["verdict"] == "pass"
