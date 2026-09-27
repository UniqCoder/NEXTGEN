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
    if not a.recipe:
        sys.exit("blind search (hypothesis-tree orchestrator) arrives at G2; for now pass --recipe RECIPE.json")
    x, fs, data = load(a.file, a.fs, a.dtype)
    recipe = Recipe.model_validate_json(Path(a.recipe).read_text())
    if abs(recipe.sample_rate_hz - fs) > 1e-6 * fs:
        sys.exit(f"recipe sample rate {recipe.sample_rate_hz} != file sample rate {fs}")
    t = time.perf_counter()
    body = build_body(x, recipe, sha256_file(data))
    cert = sign(body)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
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
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
