"""Every capture offered as a proof demo must actually certify."""
import json
from pathlib import Path

import pytest

from sanjaya.io import load
from sanjaya.proof import prove
from sanjaya.search import blind_search

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_proof_demo_recordings():
    manifest = SAMPLES / "manifest.json"
    if not manifest.exists():
        pytest.skip("sample recordings not built")
    items = json.loads(manifest.read_text(encoding="utf-8"))
    demos = [item for item in items if item.get("demo") and item["kind"] == "synthetic"]
    assert demos
    for item in demos:
        x, fs, _ = load(SAMPLES / item["file"])
        recipe, _ = blind_search(x, fs)
        assert all(layer.verdict == "pass" for layer in prove(x, recipe)), item["id"]
