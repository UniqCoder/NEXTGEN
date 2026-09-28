"""USP 4 Recipe Compiler: a certified recipe becomes a standalone receiver that reproduces SANJAYA's bits exactly
on the source recording (release gate), and decodes the same emitter as recorded by other sensors."""
import io
import json
import subprocess
import sys
import zipfile

import numpy as np

from sanjaya.compiler import compile_package, receiver_source
from sanjaya.gen import generate, gen0_recipe
from sanjaya.io import write_sigmf, sha256_file
from sanjaya.proof.certificate import build_body, sign
from sanjaya.search import blind_search


def test_compiled_receiver_is_bit_exact_and_portable(tmp_path):
    x, r, truth, taps = generate(seed=21, esn0_db=9.0)
    src = write_sigmf(tmp_path / "rec", x, r.sample_rate_hz)
    recipe, _ = blind_search(x, r.sample_rate_hz)
    sha = sha256_file(src)
    cert = sign(build_body(x, recipe, sha, "search"))
    z, gate = compile_package(recipe, cert, "SNJ-T", src, x, sha)
    assert gate["passed"] and gate["frames_equal"] == gate["frames"] == truth["n_frames"]
    assert compile_package(recipe, {**cert, "signature": None}, "SNJ-T", src, x, sha)[0] is None
    files = zipfile.ZipFile(io.BytesIO(z))
    assert set(files.namelist()) == {"receiver.py", "recipe.sigmf-meta", "sanjaya_receiver.grc", "README.txt"}
    assert json.loads(files.read("recipe.sigmf-meta"))["global"]["sanjaya:recipe"]["fec"]["K"] == 7
    rx = tmp_path / "receiver.py"
    rx.write_bytes(files.read("receiver.py"))
    assert "import sanjaya" not in rx.read_text() and "scipy" not in rx.read_text()
    # another sensor: 96 kHz ADC, +35 ppm clock, different tuning, inverted spectrum, new frames
    y, r2, *_ = generate(seed=22, esn0_db=8.0, n_frames=12, recipe=gen0_recipe(sps=10.0), clock_ppm=35, cfo_hz=-240.0)
    other = write_sigmf(tmp_path / "other", np.conj(y), r2.sample_rate_hz)
    run = subprocess.run([sys.executable, str(rx), str(other)], capture_output=True, text=True, timeout=300)
    frames = [json.loads(l) for l in run.stdout.splitlines()]
    assert len(frames) == 12 and all(f["crc_ok"] for f in frames)
    assert json.loads(run.stderr.strip().splitlines()[-1])["inverted"] is True


def test_gate_refuses_a_receiver_that_does_not_reproduce(tmp_path):
    x, r, *_ = generate(seed=23, esn0_db=10.0)
    src = write_sigmf(tmp_path / "rec", x, r.sample_rate_hz)
    recipe, _ = blind_search(x, r.sample_rate_hz)
    wrong = recipe.model_copy(update={"scrambler": recipe.scrambler.model_copy(update={"seed": recipe.scrambler.seed ^ 1})})
    from sanjaya import compiler
    gate = compiler.release_gate(src, x, recipe, receiver_source(wrong, "SNJ-T"))
    assert not gate["passed"]
