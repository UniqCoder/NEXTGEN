"""USP 4, the Recipe Compiler v0: a certified recipe becomes a receiver, not a report (answers PS P4: "the
resultant data is then utilised for processing signals in the designated sensors").

Package: receiver.py (standalone, NumPy only, the certified recipe embedded), recipe.sigmf-meta (the recipe as a
SigMF-compatible annotation), sanjaya_receiver.grc (a GNU Radio flowgraph that runs the same receiver as an
embedded Python block), README.txt. Release gate: receiver.py runs as a separate process on the source recording
and must reproduce SANJAYA's information bits exactly, frame by frame; no package is released otherwise."""
import io
import json
import pprint
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np

from ..recipe import Recipe
from ..pipeline import frontend, unwrap

TEMPLATE = Path(__file__).with_name("receiver.py")
MARK = "RECIPE = None  # @@RECIPE@@  (the compiler replaces this line with the certified recipe)"


def receiver_source(recipe: Recipe, cert_id: str) -> str:
    src = TEMPLATE.read_text(encoding="utf-8")
    if MARK not in src:
        raise RuntimeError("receiver template has lost its recipe marker")
    body = pprint.pformat(recipe.model_dump(mode="json"), width=110, sort_dicts=False)     # a Python literal
    return src.replace(MARK, f"CERTIFICATE = {cert_id!r}\nRECIPE = {body}")


def sigmf_meta(recipe: Recipe, cert: dict, cert_id: str, sha256: str) -> dict:
    mo = recipe.modulation
    return {"global": {"core:version": "1.0.0", "core:datatype": "cf32_le", "core:sample_rate": recipe.sample_rate_hz,
                       "core:description": f"SANJAYA certified recipe: {mo.scheme.upper()} {mo.symbol_rate_hz:.3f} Bd, "
                                           f"conv K={recipe.fec.K} ({','.join(recipe.fec.generators_octal)})",
                       "sanjaya:recipe": recipe.model_dump(mode="json"),
                       "sanjaya:certificate": {"id": cert_id,
                                               "verdict": cert.get("body", {}).get("verdict"), "key_id": cert.get("key_id"),
                                               "signature": cert.get("signature"), "source_sha256": sha256}},
            "captures": [{"core:sample_start": 0}], "annotations": []}


def grc(recipe: Recipe, src: str) -> str:
    """GNU Radio Companion flowgraph (3.9+ YAML): file source -> embedded Python block running the receiver."""
    block = (src.replace('if __name__ == "__main__":\n    main(sys.argv[1:])\n', "")
             + '''

from gnuradio import gr


class blk(gr.sync_block):
    """SANJAYA receiver: buffers the stream and decodes it at stop(); frames are written as JSON lines."""
    def __init__(self, samp_rate=%r, out_path="frames.jsonl"):
        gr.sync_block.__init__(self, name="SANJAYA receiver", in_sig=[np.complex64], out_sig=None)
        self.samp_rate, self.out_path, self.buf = samp_rate, out_path, []

    def work(self, input_items, output_items):
        self.buf.append(np.array(input_items[0]))
        return len(input_items[0])

    def stop(self):
        frames, summary = decode(np.concatenate(self.buf), self.samp_rate)
        with open(self.out_path, "w") as f:
            f.writelines(json.dumps(fr) + "\\n" for fr in frames)
        print(json.dumps(summary))
        return True
''' % recipe.sample_rate_hz)
    q = json.dumps                                               # a JSON string is a valid YAML double-quoted scalar
    return f"""options:
  parameters: {{id: sanjaya_receiver, title: SANJAYA compiled receiver, generate_options: no_gui, output_language: python}}
  states: {{coordinate: [8, 8], rotation: 0, state: enabled}}
blocks:
- name: samp_rate
  id: variable
  parameters: {{value: '{recipe.sample_rate_hz!r}'}}
  states: {{coordinate: [200, 12], rotation: 0, state: enabled}}
- name: recording
  id: blocks_file_source
  parameters: {{file: recording.cf32, type: complex, repeat: 'False', vlen: '1', begin_tag: pmt.PMT_NIL, length: '0', offset: '0'}}
  states: {{coordinate: [16, 120], rotation: 0, state: enabled}}
- name: sanjaya
  id: epy_block
  parameters: {{_source_code: {q(block)}, samp_rate: samp_rate, out_path: "'frames.jsonl'"}}
  states: {{coordinate: [320, 120], rotation: 0, state: enabled}}
connections:
- [recording, '0', sanjaya, '0']
metadata: {{file_format: 1}}
"""


def run_receiver(src: str, recording: Path, fs: float | None = None, dtype: str | None = None):
    """The compiled receiver as its own process: (frames, seconds, error or None)."""
    with tempfile.TemporaryDirectory() as d:
        rx = Path(d) / "receiver.py"
        rx.write_text(src, encoding="utf-8")
        cmd = [sys.executable, str(rx), str(recording)] + (["--fs", str(fs), "--dtype", dtype] if dtype else [])
        t = time.perf_counter()
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        dt = time.perf_counter() - t
    if run.returncode != 0:
        return [], dt, run.stderr.strip()[-400:]
    return [json.loads(line) for line in run.stdout.splitlines() if line.strip()], dt, None


def release_gate(recording: Path, x: np.ndarray, recipe: Recipe, src: str, fs: float | None = None,
                 dtype: str | None = None) -> dict:
    """Run the compiled receiver as its own process on the source recording; its bits must equal SANJAYA's."""
    engine = unwrap(frontend(x, recipe), recipe)
    ref = [np.packbits(r).tobytes().hex() for r in engine.info]
    got, dt, err = run_receiver(src, recording, fs, dtype)
    if err:
        return {"passed": False, "error": err, "frames": len(ref)}
    equal = sum(1 for a, b in zip(ref, got) if a == b["info_hex"])
    bits = int(engine.info.size)
    return {"passed": len(got) == len(ref) and equal == len(ref), "frames": len(ref), "frames_equal": equal,
            "bits_compared": bits, "receiver_crc_ok": sum(1 for g in got if g["crc_ok"]),
            "engine_crc_ok": int(engine.crc_ok.sum()), "receiver_seconds": round(dt, 2)}


def compile_package(recipe: Recipe, cert: dict, cert_id: str, recording: Path, x: np.ndarray, sha256: str,
                    fs: float | None = None, dtype: str | None = None) -> tuple[bytes | None, dict]:
    """(zip bytes, gate). The zip is None when the gate fails: nothing is released that does not reproduce."""
    from ..proof.certificate import check_signature
    body = cert.get("body") or {}
    if (body.get("verdict") != "pass" or body.get("recipe") != recipe.model_dump(mode="json")
            or body.get("input_sha256") != sha256 or check_signature(cert) != "valid"):
        return None, {"passed": False, "error": "recipe lacks a matching, valid signed proof"}
    src = receiver_source(recipe, cert_id)
    gate = release_gate(recording, x, recipe, src, fs, dtype)
    if not gate["passed"]:
        return None, gate
    readme = (f"SANJAYA compiled receiver (certificate {cert_id})\n\n"
              f"receiver.py            standalone receiver, NumPy only: python receiver.py RECORDING > frames.jsonl\n"
              f"recipe.sigmf-meta      the certified recipe as a SigMF annotation\n"
              f"sanjaya_receiver.grc   GNU Radio 3.9+ flowgraph: file source -> the same receiver as an embedded block\n\n"
              f"Release gate: on the source recording (SHA-256 {sha256}) receiver.py reproduced SANJAYA's information bits "
              f"exactly: {gate['frames_equal']}/{gate['frames']} frames, {gate['bits_compared']} bits, "
              f"{gate['receiver_crc_ok']} CRC-valid frames.\n"
              "The .grc is generated from the same code but was not executed here (GNU Radio is optional).\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("receiver.py", src)
        z.writestr("recipe.sigmf-meta", json.dumps(sigmf_meta(recipe, cert, cert_id, sha256), indent=1))
        z.writestr("sanjaya_receiver.grc", grc(recipe, src))
        z.writestr("README.txt", readme)
    return buf.getvalue(), gate
