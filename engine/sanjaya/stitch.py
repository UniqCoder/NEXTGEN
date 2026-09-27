"""USP 3b, Evidence Stitching + Sensor Twin v0 (PRD C3): several captures of one emitter, from different sensors
and locations, each with its own sample rate, clock error, tuning offset, gain, noise floor and possibly an
inverted spectrum. Each may be too short to be decoded on its own; pooled, they are.

1. Each capture is measured by its own front-end (its own CFO, clock, phase), normalised to unit power.
2. The capture with the clearest frame structure is the reference; its sync marker locates the frames in every
   other capture (both spectral orientations) and fixes each frame's residual quarter-turn rotation.
3. Whole frames of every capture are concatenated into one symbol stream and searched blind as one recording.
   Frame slots step negative at each capture boundary: the time gap between captures is unknown.
4. The recipe found is then proven on EACH capture separately (a known recipe needs far fewer frames than
   finding it), which is also what catches a capture wrongly attributed to this emitter.
5. Sensor Twin: per capture, sample rate, clock offset relative to the other sensors, tuning offset, SNR,
   gain, noise floor and spectral inversion, all measured against the one emitter they share."""
import numpy as np
from .search import blind_search, measure_phy, search_structure, discover_frames, SearchError, Step
from .sufficiency import Ledger
from .pipeline import frontend, unwrap, frame_sync
from .proof import prove

GAP = 10 ** 6                     # slot offset between captures (any value that makes the step negative)


def _alone(x, fs):
    try:
        _, log = blind_search(x, fs)
        return {"verdict": "decoded", "headline": log[-1].finding}
    except SearchError as e:
        return {"verdict": "undecided", "headline": (e.ledger or {}).get("headline", str(e)), "reason": str(e)}


def stitch(captures: list[tuple[np.ndarray, float, str]], on_step=None):
    """captures: (samples, sample rate, name). Returns (recipe for the reference capture, log, report)."""
    log = _Log(on_step)
    emit = log.append
    meas = []
    for x, fs, name in captures:
        alone = _alone(x, fs)
        ys, sps, t0, cfo, theta, rs, beta = measure_phy(x, fs)
        ys = (ys / np.sqrt(np.mean(np.abs(ys) ** 2))).astype(np.complex64)
        meas.append({"name": name, "fs": fs, "seconds": x.size / fs, "alone": alone, "ys": ys, "sps": sps,
                     "cfo": cfo, "rs": rs, "beta": beta, "fr": discover_frames(ys)})
        emit(Step("capture", f"{name}: {x.size / fs:.2f} s at {fs:,.0f} Hz; alone: {alone['verdict']}", "measured",
                  {"alone": alone}))
    excluded: dict[int, dict] = {}                 # captures the proof rejected on the first pass, with that proof
    for attempt in (1, 2):
        framed = [i for i, m in enumerate(meas) if m["fr"] and i not in excluded]
        if not framed:
            raise SearchError("no capture shows a frame structure on its own, so there is nothing to align the others to")
        ref = max(framed, key=lambda i: meas[i]["ys"].size / meas[i]["fr"][0])
        P, _, L, tmpl = meas[ref]["fr"]
        segs, slots, members = [], [], []
        for i, m in enumerate(meas):
            if i in excluded:
                continue
            try:
                conj, starts, _, c = frame_sync(m["ys"], tmpl, P)
            except RuntimeError:
                starts = np.array([], int)
            m["associated"] = bool(starts.size)
            if not starts.size:
                continue
            z = np.conj(m["ys"]) if conj else m["ys"]
            rot = np.round(np.angle(c) / (np.pi / 2)) * (np.pi / 2)
            segs.append((np.stack([z[s: s + P] for s in starts]) * np.exp(-1j * rot)[:, None]).ravel())
            slots.extend(((starts - starts[0]) // P - len(members) * GAP).tolist())
            members.append(i)
            m["frames"] = int(starts.size)
        pooled = np.concatenate(segs).astype(np.complex64)
        slot_arr = np.array(slots)
        emit(Step("stitch", f"{len(members)} of {len(meas)} captures pooled on the reference sync marker "
                  f"({meas[ref]['name']}): {len(slots)} frames", "blind",
                  {"reference": meas[ref]["name"], "frames": [meas[i]["frames"] for i in members]}))
        r0 = meas[ref]
        led = Ledger(sum(meas[i]["seconds"] for i in members))
        try:
            recipe, _ = search_structure(None, r0["fs"], (pooled, r0["sps"], 0.0, r0["cfo"], np.zeros(pooled.size)),
                                         r0["rs"], r0["beta"], log, led, lambda st: slot_arr[st // P])
        except SearchError as e:
            e.ledger = led.to_dict()
            e.stitch = {"reference": r0["name"], "pooled_frames": len(slots), "pooled_seconds": round(led.have_s, 3),
                        "sensors": [_bare(m) for m in meas]}
            raise
        sensors = [_prove_one(x, fs, meas[i], recipe, float(np.median([meas[j]["rs"] for j in members])))
                   for i, (x, fs, _) in enumerate(captures)]
        bad = [i for i in members if not sensors[i]["consistent"]]
        if attempt == 1 and bad and len(bad) < len(members):
            excluded.update({i: sensors[i] for i in bad})
            emit(Step("stitch", "re-pooling without " + ", ".join(meas[i]["name"] for i in bad)
                      + ": the per-capture proof rejects them as this emitter", "blind", {}))
            continue
        break
    for i, e in excluded.items():
        sensors[i] = {**e, "excluded": True, "consistent": False}
    log.append(Step("sufficiency", led.headline()[1], "measured", led.to_dict()))
    ref_recipe = recipe.model_copy(update={"sample_rate_hz": r0["fs"]})
    report = {"reference": r0["name"], "pooled_frames": len(slots), "pooled_seconds": round(led.have_s, 3),
              "sensors": sensors, "sufficiency": led.to_dict()}
    return ref_recipe, log, report, ref


def _bare(m):
    return {"name": m["name"], "seconds": round(m["seconds"], 3), "fs_hz": m["fs"], "alone": m["alone"],
            "associated": m.get("associated", False), "frames": m.get("frames", 0)}


def _prove_one(x, fs, m, recipe, ref_rate):
    """The pooled recipe proven on one capture alone, plus that sensor's twin, measured against the emitter."""
    entry = _bare(m)
    if m.get("associated"):
        ri = recipe.model_copy(update={"sample_rate_hz": fs,
                                       "modulation": recipe.modulation.model_copy(update={"symbol_rate_hz": m["rs"]})})
        try:
            fe = frontend(x, ri)
            uw = unwrap(fe, ri)
            entry.update(proof=[v.verdict for v in prove(x, ri)], crc_ok=int(uw.crc_ok.sum()), crc_frames=len(uw.crc_ok),
                         # a fast sensor clock stretches every symbol over more samples, so it measures the rate LOW
                         clock_ppm=round((ref_rate / m["rs"] - 1) * 1e6, 1), cfo_hz=round(fe.cfo_hz, 1),
                         esn0_db=round(fe.esn0_db, 1), gain_db=round(20 * np.log10(fe.amp + 1e-30), 1),
                         noise_db=round(10 * np.log10(fe.sigma2 + 1e-30), 1), inverted=bool(fe.conj))
        except Exception as e:                                       # a capture the recipe does not explain
            entry.update(proof=["fail"], error=f"{type(e).__name__}: {e}")
    entry["consistent"] = bool(entry.get("proof")) and all(v != "fail" for v in entry["proof"])
    return entry


class _Log(list):
    def __init__(self, fn=None):
        super().__init__()
        self.fn = fn

    def append(self, s):
        super().append(s)
        if self.fn:
            self.fn(s)

    def extend(self, it):
        for s in it:
            self.append(s)
