"""sanjaya gen | analyze | verify   (R-16; batch, serve and bench arrive with WP13/WP15)"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np


def _gen(a):
    from .gen import generate
    from .io import write_sigmf
    x, recipe, truth, taps = generate(seed=a.seed, esn0_db=a.esn0, n_frames=a.frames)
    base = Path(a.out) / f"gen0_s{a.seed}_{a.esn0:g}dB"
    data = write_sigmf(base, x, recipe.sample_rate_hz, {"sanjaya:generator": truth["generator"]})
    (base.parent / (base.name + ".recipe.json")).write_text(recipe.model_dump_json(indent=1))
    (base.parent / (base.name + ".truth.json")).write_text(json.dumps(truth, indent=1))
    np.savez_compressed(base.parent / (base.name + ".taps.npz"), **{k: v for k, v in taps.items()})
    print(f"wrote {data}\n      {base.name}.recipe.json  (truth recipe)\n      {base.name}.truth.json, {base.name}.taps.npz")


def _analyze(a):
    from .io import load, sha256_file
    from .recipe import Recipe
    from .pipeline import frontend, unwrap
    from .proof.certificate import build_body, sign
    x, fs, data = load(a.file, a.fs, a.dtype)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t = time.perf_counter()
    if a.recipe:
        recipe, source = Recipe.model_validate_json(Path(a.recipe).read_text()), "supplied"
        if abs(recipe.sample_rate_hz - fs) > 1e-6 * fs:
            sys.exit(f"recipe sample rate {recipe.sample_rate_hz} != file sample rate {fs}")
        if recipe.modulation.scheme.startswith("fsk"):
            return _analyze_fsk(recipe, x, out, t)
    else:
        from .search import blind_search, SearchError
        try:
            recipe, log = blind_search(x, fs)
        except SearchError as e:
            print(f"UNDECIDED: {e}")
            (out / "search.json").write_text(json.dumps({"undecided": str(e)}, indent=1))
            sys.exit(2)
        source = "search"
        (out / "search.json").write_text(json.dumps([s.__dict__ for s in log], indent=1, default=str))
        print(f"blind search ({time.perf_counter() - t:.1f} s):")
        for s in log:
            print(f"  {s.stage:10s} [{s.method}] {s.finding}")
        if recipe.modulation.scheme.startswith("fsk"):
            return _analyze_fsk(recipe, x, out, t)
    body = build_body(x, recipe, sha256_file(data), source)
    cert = sign(body)
    (out / "certificate.json").write_text(json.dumps(cert, indent=1))
    (out / "recipe.json").write_text(recipe.model_dump_json(indent=1))
    uw = unwrap(frontend(x, recipe), recipe)
    with open(out / "frames.csv", "w") as f:
        names = [fd.name for fd in recipe.framing.fields]
        f.write("frame,crc_ok," + ",".join(names) + "\n")
        for i, (fd, ok) in enumerate(zip(uw.fields, uw.crc_ok)):
            f.write(f"{i},{int(ok)}," + ",".join(str(fd[n]) for n in names) + "\n")
    print(f"verdict: {body.verdict.upper()}  ({time.perf_counter() - t:.1f} s, {cert['status']}, key {cert['key_id']})")
    for l in body.layers:
        print(f"  {l.layer:9s} {l.verdict:17s} {l.reason or ''}")
    for n in body.near_misses:
        print(f"  near-miss {n.name:32s} {'rejected' if n.rejected else 'NOT rejected (equivalence)'}")
    print(f"wrote {out / 'certificate.json'}, recipe.json, frames.csv")


def _analyze_fsk(recipe, x, out, t):
    """Known-recipe FSK: decode + CRC works (sanjaya.fsk); no certificate yet, honestly -- the layered
    proof's channel model (proof.certificate.coding_layer) is not FSK-aware. Same documented gap RS had
    before its own proof branch landed (HANDOFF, commit 147e84c)."""
    from .fsk import unwrap_fsk
    fe, uw = unwrap_fsk(x, recipe)
    (out / "recipe.json").write_text(recipe.model_dump_json(indent=1))
    with open(out / "frames.csv", "w") as f:
        names = [fd.name for fd in recipe.framing.fields]
        f.write("frame,crc_ok," + ",".join(names) + "\n")
        for i, (fd, ok) in enumerate(zip(uw.fields, uw.crc_ok)):
            f.write(f"{i},{int(ok)}," + ",".join(str(fd[n]) for n in names) + "\n")
    print(f"FSK decode ({time.perf_counter() - t:.1f} s): {uw.crc_ok.sum()}/{len(uw.crc_ok)} frames CRC-valid, "
          f"CFO {fe.cfo_hz:.1f} Hz")
    print("  no certificate: the layered proof is not FSK-aware yet (decode only, like RS before its proof branch)")
    print(f"wrote {out / 'recipe.json'}, frames.csv")


def _verify(a):
    from .io import load, sha256_file
    from .proof.certificate import verify, check_signature
    cert = json.loads(Path(a.cert).read_text())
    x, fs, data = load(a.file, a.fs, a.dtype)
    t = time.perf_counter()
    problems = verify(x, sha256_file(data), cert)
    print(f"signature: {check_signature(cert)}   re-check: {time.perf_counter() - t:.1f} s")
    if problems:
        print("NOT REPRODUCED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"REPRODUCED: verdict {cert['body']['verdict'].upper()}, every layer statistic within declared precision")


def _serve(a):
    import secrets, webbrowser
    import uvicorn
    from .api import create_app
    token = a.token or secrets.token_urlsafe(18)
    ui = Path(a.ui) if a.ui else Path(__file__).resolve().parents[2] / "ui" / "dist"
    samples = Path(__file__).resolve().parents[1] / "samples"
    app = create_app(token, a.port, Path(a.work), ui, dev=a.dev, samples_dir=samples if samples.is_dir() else None)
    url = f"http://127.0.0.1:{a.port}/?token={token}"
    print(f"SANJAYA engine on 127.0.0.1:{a.port} (UI: {ui if ui.is_dir() else 'not built'})")
    print(f"  open {url}")
    if a.open:
        webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")


def main(argv=None):
    p = argparse.ArgumentParser(prog="sanjaya")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen", help="write a SANJAYA-Gen v0 recording with truth and taps")
    g.add_argument("--out", default="work/gen")
    g.add_argument("--seed", type=int, default=147)
    g.add_argument("--esn0", type=float, default=12.0)
    g.add_argument("--frames", type=int, default=40)
    for name, fn in (("analyze", _analyze), ("verify", _verify)):
        s = sub.add_parser(name)
        s.add_argument("file")
        if name == "verify":
            s.add_argument("cert")
        else:
            s.add_argument("--recipe")
            s.add_argument("--out", default="work/job")
        s.add_argument("--fs", type=float)
        s.add_argument("--dtype")
        s.set_defaults(fn=fn)
    g.set_defaults(fn=_gen)
    v = sub.add_parser("serve", help="local engine API (+ the UI in browser mode) on 127.0.0.1")
    v.add_argument("--port", type=int, default=8765)
    v.add_argument("--work", default="work/jobs")
    v.add_argument("--ui")
    v.add_argument("--token", help="fixed token (default: random per launch)")
    v.add_argument("--dev", action="store_true", help="also allow the Vite dev origin http://localhost:5173")
    v.add_argument("--open", action="store_true")
    v.set_defaults(fn=_serve)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
