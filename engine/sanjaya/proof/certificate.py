"""Decode Certificate: canonical JSON, Ed25519 signature, and the independent verifier (PRD §4.2 C1).
The body is deterministic for (engine version, file, configuration); issue time sits in the signed envelope.
Key: OS key store via keyring when installed, else a 0600 key file (PRD §6.9). No cryptography -> UNSIGNED."""
import base64, datetime, hashlib, json, os
from pathlib import Path
import numpy as np
from .. import __version__
from ..recipe import Recipe, CertificateBody
from ..pipeline import frontend, unwrap
from . import prove, near_miss_battery, TH, CALIBRATION_ID

SIG_DIGITS = 6
KEY_FILE = Path(os.environ.get("SANJAYA_HOME", Path.home() / ".sanjaya")) / "keys" / "site_ed25519.pem"


def _round(o):
    if isinstance(o, float):
        return float(f"{o:.{SIG_DIGITS}g}") if np.isfinite(o) else str(o)
    if isinstance(o, dict):
        return {k: _round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v) for v in o]
    return o


def canonical(obj) -> bytes:
    return json.dumps(_round(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def config_hash() -> str:
    return hashlib.sha256(canonical({"thresholds": TH, "calibration_id": CALIBRATION_ID})).hexdigest()


def _key():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization as ser
    except ImportError:
        return None
    if KEY_FILE.exists():
        return ser.load_pem_private_key(KEY_FILE.read_bytes(), None)
    k = Ed25519PrivateKey.generate()
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(k.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))
    os.chmod(KEY_FILE, 0o600)
    return k


def build_body(x: np.ndarray, recipe: Recipe, input_sha256: str, recipe_source: str = "supplied") -> CertificateBody:
    fe = frontend(x, recipe)
    uw = unwrap(fe, recipe)
    layers = prove(x, recipe, fe, uw)
    nm = near_miss_battery(x, recipe, fe)
    verdict = "pass" if all(l.verdict != "fail" for l in layers) else "fail"
    return CertificateBody(
        engine_version=__version__, config_hash=config_hash(), input_sha256=input_sha256, recipe=recipe,
        recipe_source=recipe_source, verdict=verdict, layers=layers, near_misses=nm,
        attempts_k=1, false_pass_bound=None,                          # set once the G5 campaign measures p-hat
        equivalences=[f"not separable from the certified recipe: {n.name}" for n in nm if not n.rejected],
        analyst_overrides=["recipe supplied by the analyst (known-recipe mode)"] if recipe_source == "supplied" else [])
    # attempts_k counts proof attempts that could have certified a different recipe: v1 search proves once


def sign(body: CertificateBody) -> dict:
    env = {"body": body.model_dump(mode="json"),
           "issued_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    k = _key()
    if k is None:
        return {**env, "signature": None, "key_id": None, "public_key": None, "status": "UNSIGNED"}
    from cryptography.hazmat.primitives import serialization as ser
    pub = k.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
    sig = k.sign(canonical(env))
    return {**env, "signature": base64.b64encode(sig).decode(), "public_key": base64.b64encode(pub).decode(),
            "key_id": hashlib.sha256(pub).hexdigest()[:16], "status": "SIGNED"}


def check_signature(cert: dict) -> str:
    if cert.get("signature") is None:
        return "unsigned"
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return "unchecked (cryptography missing)"
    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(cert["public_key"]))
    try:
        pub.verify(base64.b64decode(cert["signature"]), canonical({"body": cert["body"], "issued_utc": cert["issued_utc"]}))
        return "valid"
    except InvalidSignature:
        return "INVALID"


def verify(x: np.ndarray, input_sha256: str, cert: dict) -> list[str]:
    """Re-run synthesis and every test from the file and the certified recipe alone (no search).
    Returns the list of problems; empty means the certificate is reproduced."""
    problems = []
    sig = check_signature(cert)
    if sig == "INVALID":
        problems.append("signature does not match the certificate content")
    body = cert["body"]
    if body["input_sha256"] != input_sha256:
        problems.append("input file differs from the certified file (SHA-256 mismatch)")
    if body["config_hash"] != config_hash():
        problems.append("engine configuration differs from the certifying configuration")
    recipe = Recipe.model_validate(body["recipe"])
    again = json.loads(canonical(build_body(x, recipe, input_sha256, body["recipe_source"]).model_dump(mode="json")))
    orig = json.loads(canonical(body))
    for key in ("verdict", "equivalences"):
        if again[key] != orig[key]:
            problems.append(f"{key} not reproduced")
    for a, o in zip(again["layers"], orig["layers"]):
        if a["verdict"] != o["verdict"]:
            problems.append(f"{o['layer']} verdict not reproduced ({o['verdict']} -> {a['verdict']})")
        for k, v in o["stats"].items():
            w = a["stats"].get(k)
            if w is None or (isinstance(v, float) and abs(w - v) > 1e-3 * max(1.0, abs(v))):
                problems.append(f"{o['layer']}.{k} not reproduced ({v} -> {w})")
    if [n["rejected"] for n in again["near_misses"]] != [n["rejected"] for n in orig["near_misses"]]:
        problems.append("near-miss battery not reproduced")
    return problems
