"""Local engine API (PRD §6.8): FastAPI on 127.0.0.1 only. Every /v1 request needs the per-launch token in
X-Sanjaya-Token; the Host header must be 127.0.0.1:<port> or localhost:<port> (anti DNS-rebinding); an Origin,
when sent, must be on the allowlist; no CORS wildcard. `sanjaya serve` also hosts ui/dist (browser mode)."""
import json, threading, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from .. import __version__
from ..kernels import BACKEND

STAGE_OF = {"capture": (0,), "stitch": (0, 1), "classify": (0,), "measure": (0, 1), "frame": (2, 3), "code": (4,), "scrambler": (4,), "structure": (5,)}
DEV_ORIGIN = "http://localhost:5173"


@dataclass
class Job:
    id: str
    name: str
    path: Path
    state: str = "queued"                    # queued | running | done | undecided | error
    stages: list[str] = field(default_factory=lambda: ["pending"] * 8)
    error: str | None = None
    log: list[dict] = field(default_factory=list)
    result: dict | None = None
    cert: dict | None = None
    package: bytes | None = None             # the Recipe Compiler's zip, released only if its gate passed
    started: float = field(default_factory=time.time)


def _meta(name: str, path: Path, x, fs_: float, sha: str, dtype: str | None, fc_hz: float | None) -> dict:
    suffix = path.suffix.lower()
    return {"name": name, "path": str(path), "size": path.stat().st_size, "sha256": sha,
            "format": {".wav": "WAV", ".sigmf-data": "SigMF"}.get(suffix, "Raw IQ") + (f" · {dtype}" if dtype else ""),
            "route": "wav" if suffix == ".wav" else "iq",
            "source_fs": "WAV header" if suffix == ".wav" else ("SigMF core:sample_rate" if suffix == ".sigmf-data" else "analyst entry"),
            "fc_hz": fc_hz,
            "forensics": [
                {"k": "Container", "v": "WAV (RIFF)" if suffix == ".wav" else "SigMF" if suffix == ".sigmf-data" else "None (headerless)",
                 "conf": 1, "method": "blind", "note": ""},
                {"k": "Sample rate", "v": f"{fs_:,.0f} Hz".replace(",", " "), "conf": 1, "method": "blind", "note": "from the header"},
                {"k": "Samples", "v": f"{x.size:,}".replace(",", " "), "conf": None, "method": "blind", "note": f"{x.size / fs_:.2f} s"},
                {"k": "SHA-256", "v": sha[:16] + "…", "conf": None, "method": "blind", "note": "recorded in the certificate"},
            ]}


def _run(job: Job, fs: float | None, dtype: str | None, fc_hz: float | None, members: list[tuple[Path, str]] | None = None):
    """One recording (blind search), or several captures of one emitter (members: evidence stitching)."""
    from ..io import load, sha256_file
    from ..search import blind_search, SearchError
    from ..proof.certificate import build_body, sign
    from .scenario import build, build_partial
    job.state = "running"
    job.stages[0] = "running"

    def on_step(s):
        job.log.append({"stage": s.stage, "finding": s.finding, "method": s.method})
        for i in STAGE_OF.get(s.stage, ()):
            job.stages[i] = "done"
        nxt = next((i for i, v in enumerate(job.stages[:6]) if v == "pending"), None)
        if nxt is not None:
            job.stages[nxt] = "running"
    try:
        extra, source = {}, "search"
        if members:
            from ..stitch import stitch
            caps = [load(p) for p, _ in members]
            try:
                recipe, log, report, ref = stitch([(x, f, label) for (x, f, _), (_, label) in zip(caps, members)], on_step)
            except SearchError as e:
                x, fs_, data = caps[0]
                meta = _meta(members[0][1], members[0][0], x, fs_, sha256_file(data), dtype, fc_hz)
                job.result = build_partial(x, fs_, meta, str(e), None, e.ledger)
                job.result["scenario"]["view"]["stitch"] = getattr(e, "stitch", None)
                job.state, job.error = "undecided", str(e)
                job.stages = ["failed" if v == "running" else v for v in job.stages]
                return
            (x, fs_, data), (path, name) = caps[ref], members[ref]
            extra, source = {"stitch": report}, "stitch"
        else:
            x, fs_, data = load(job.path, fs, dtype)
            path, name = job.path, job.name
            try:
                recipe, log = blind_search(x, fs_, on_step)
            except SearchError as e:
                job.result = build_partial(x, fs_, _meta(name, path, x, fs_, sha256_file(data), dtype, fc_hz), str(e), e.phy, e.ledger)
                job.state, job.error = "undecided", str(e)
                job.stages = ["failed" if v == "running" else v for v in job.stages]
                return
        sha = sha256_file(data)
        body = build_body(x, recipe, sha, source)
        job.cert = sign(body)
        res = build(x, fs_, recipe, body, log, _meta(name, path, x, fs_, sha, dtype, fc_hz))
        res["scenario"]["view"].update(extra)
        res["scenario"]["cert"].update({"key": f"ed25519:{job.cert.get('key_id')}", "sig": (job.cert.get("signature") or "UNSIGNED")[:12] + "…",
                                        "issued": job.cert["issued_utc"]})
        # Recipe Compiler: a receiver for the designated sensors, released only if it reproduces our bits exactly
        from ..compiler import compile_package, receiver_source, run_receiver
        raw = path.suffix.lower() not in (".wav", ".sigmf-data")
        job.package, gate = compile_package(recipe, job.cert, res["scenario"]["cert"]["id"], path, x, sha,
                                            fs_ if raw else None, dtype if raw else None)
        if members and job.package:                                  # the same receiver on the other sensors' files
            src = receiver_source(recipe, res["scenario"]["cert"]["id"])
            gate["other_sensors"] = []
            for (p_i, label), s_i in zip(members, extra["stitch"]["sensors"]):
                if p_i != path and s_i.get("consistent"):
                    got, _, err = run_receiver(src, p_i)
                    gate["other_sensors"].append({"name": label, "frames": len(got), "crc_ok": sum(1 for g in got if g["crc_ok"]),
                                                  "error": err})
        res["scenario"]["view"]["compiler"] = gate
        job.result = res
        job.stages[:6] = ["done"] * 6
        job.state = "done"
    except Exception as e:                                          # the API survives; the job reports why
        job.state, job.error = "error", f"{type(e).__name__}: {e}"
        job.stages = ["failed" if v == "running" else v for v in job.stages]


def create_app(token: str, port: int, workdir: Path, ui_dist: Path | None = None, dev: bool = False,
               samples_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="SANJAYA engine", version=__version__, docs_url=None, redoc_url=None)
    jobs: dict[str, Job] = {}
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"} | ({DEV_ORIGIN} if dev else set())

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.headers.get("host") not in hosts:
            return JSONResponse({"detail": "host not allowed"}, 403)
        origin = request.headers.get("origin")
        if origin is not None and origin not in origins:
            return JSONResponse({"detail": "origin not allowed"}, 403)
        if request.method == "OPTIONS" and origin:
            return Response(status_code=204, headers={"Access-Control-Allow-Origin": origin, "Vary": "Origin",
                                                      "Access-Control-Allow-Headers": "X-Sanjaya-Token, Content-Type",
                                                      "Access-Control-Allow-Methods": "GET, POST"})
        if request.url.path.startswith("/v1/") and request.headers.get("x-sanjaya-token") != token:
            return JSONResponse({"detail": "missing or wrong X-Sanjaya-Token"}, 401)
        resp = await call_next(request)
        if request.url.path in ("/", "/index.html"):
            resp.headers["Cache-Control"] = "no-cache"               # a rebuilt UI is never masked by a stale page
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Expose-Headers"] = "X-Rows, X-Bins"
            resp.headers["Vary"] = "Origin"
        return resp

    def job_or_404(jid: str) -> Job:
        if jid not in jobs:
            raise HTTPException(404, "no such job")
        return jobs[jid]

    @app.get("/v1/health")
    def health():
        return {"engine_version": __version__, "kernels": BACKEND, "jobs": len(jobs)}

    @app.get("/v1/samples")
    def samples():
        manifest = samples_dir / "manifest.json" if samples_dir else None
        if not manifest or not manifest.is_file():
            return []
        return json.loads(manifest.read_text(encoding="utf-8"))

    @app.post("/v1/verify")
    async def verify_certificate(certificate: UploadFile, recording: UploadFile, sigmf: str | None = Form(None),
                                 fs: float | None = Form(None), dtype: str | None = Form(None)):
        """Independent re-check (PRD 'sanjaya verify'): the certificate and its recording, no search, no job.
        Re-derives every statistic from the file and the certified recipe alone. sigmf: the .sigmf-meta
        sidecar's text, when the recording is a bare .sigmf-data upload."""
        import hashlib
        from ..io import load, sha256_file
        from ..proof.certificate import verify as verify_cert, check_signature
        cert = json.loads(await certificate.read())
        d = workdir / ("verify-" + uuid.uuid4().hex[:12])
        d.mkdir(parents=True, exist_ok=True)
        src = d / (recording.filename or "recording")
        with open(src, "wb") as f:
            f.write(await recording.read())
        if sigmf:
            src.with_suffix(".sigmf-meta").write_text(sigmf)
            src = src.with_suffix(".sigmf-data") if src.suffix != ".sigmf-data" else src
        try:
            x, fs_, data = load(src, fs, dtype)
        except ValueError as e:
            raise HTTPException(400, str(e))
        try:
            problems = verify_cert(x, sha256_file(data), cert)
        except Exception as e:                                       # the certified recipe does not fit this file at all
            problems = [f"the certified recipe could not be re-applied to this file ({type(e).__name__}: {e})"]
        cert_id = "SNJ-" + hashlib.sha256(json.dumps(cert["body"], separators=(",", ":")).encode()).hexdigest()[:12].upper()
        return {"reproduced": not problems, "problems": problems, "certificate_id": cert_id,
                "verdict": cert.get("body", {}).get("verdict"), "signature": check_signature(cert)}

    @app.post("/v1/jobs")
    async def create_job(request: Request, name: str, fs: float | None = None, dtype: str | None = None,
                         fc_hz: float | None = None, path: str | None = None, sigmf: str | None = None,
                         sample: str | None = None):
        """Browser mode uploads the bytes (body); desktop mode passes ?path= to a local file;
        ?sample= runs one of the built-in demo recordings (engine/samples/manifest.json)."""
        jid = uuid.uuid4().hex[:12]
        if sample:
            if not samples_dir:
                raise HTTPException(404, "no sample library configured")
            manifest = json.loads((samples_dir / "manifest.json").read_text(encoding="utf-8"))
            item = next((s for s in manifest if s["id"] == sample), None)
            if item is None:
                raise HTTPException(404, "no such sample")
            if item["kind"] == "stitch":                          # several captures of one emitter
                members = [(samples_dir / m["file"], m["label"]) for m in item["members"]]
                job = Job(jid, item["name"], members[0][0])
                jobs[jid] = job
                threading.Thread(target=_run, args=(job, None, None, None, members), daemon=True).start()
                return {"id": jid}
            src, name = samples_dir / item["file"], item["name"]
        elif path:
            src = Path(path)
            if not src.is_file():
                raise HTTPException(400, "path is not a file")
        else:
            d = workdir / jid
            d.mkdir(parents=True, exist_ok=True)
            src = d / Path(name).name
            with open(src, "wb") as f:
                async for chunk in request.stream():
                    f.write(chunk)
            if sigmf:                                              # sidecar forwarded by the UI: validated JSON only
                try:
                    meta = json.loads(sigmf)
                    assert isinstance(meta.get("global"), dict)
                except (ValueError, AssertionError):
                    raise HTTPException(400, "sigmf is not a SigMF metadata object")
                src.with_suffix(".sigmf-meta").write_text(json.dumps(meta))
                src = src.with_suffix(".sigmf-data") if src.suffix != ".sigmf-data" else src
        job = Job(jid, Path(name).name, src)
        jobs[jid] = job
        threading.Thread(target=_run, args=(job, fs, dtype, fc_hz), daemon=True).start()
        return {"id": jid}

    @app.get("/v1/jobs/{jid}")
    def job_status(jid: str):
        j = job_or_404(jid)
        v = j.result["scenario"]["view"]["verdict"] if j.result else None
        return {"id": j.id, "name": j.name, "state": j.state, "stages": j.stages, "error": j.error, "log": j.log, "verdict": v}

    @app.get("/v1/jobs/{jid}/scenario")
    def scenario(jid: str):
        j = job_or_404(jid)
        if not j.result:
            raise HTTPException(409, f"job is {j.state}")
        return {k: v for k, v in j.result.items() if k != "spectrogram"}

    @app.get("/v1/jobs/{jid}/spectrogram/{kind}")
    def spectrogram(jid: str, kind: str):
        j = job_or_404(jid)
        if not j.result or kind not in j.result["spectrogram"]:
            raise HTTPException(404, "not available")
        a = np.ascontiguousarray(j.result["spectrogram"][kind], np.float32)
        return Response(a.tobytes(), media_type="application/octet-stream",
                        headers={"X-Rows": str(a.shape[0]), "X-Bins": str(a.shape[-1] if a.ndim == 2 else 1)})

    @app.get("/v1/jobs/{jid}/receiver.zip")
    def receiver_zip(jid: str):
        j = job_or_404(jid)
        if not j.package:
            raise HTTPException(409, "no receiver released for this job (not decoded, or the release gate failed)")
        return Response(j.package, media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="sanjaya-receiver-{jid}.zip"'})

    @app.get("/v1/jobs/{jid}/certificate.json")
    def certificate(jid: str):
        j = job_or_404(jid)
        if not j.cert:
            raise HTTPException(409, f"job is {j.state}")
        return JSONResponse(j.cert)

    if ui_dist is not None and ui_dist.is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=ui_dist, html=True), name="ui")
    return app
