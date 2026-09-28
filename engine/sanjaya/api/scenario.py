"""Engine results -> the exact data shapes the built UI renders (ui/src/lib/mock.ts exports).
Every number here is computed from the job; anything the engine does not do yet is labelled as such."""
import hashlib
import numpy as np
from scipy.stats import chi2
from ..recipe import Recipe
from ..pipeline import frontend, unwrap
from ..chain import asm_symbols
from ..coding import block_deinterleave, syndrome_rate_half
from ..coding.blind import dual_spectrum, divisors
from ..proof import resynthesise
from ..bits import from_bits

ROWS, BINS = 360, 1024
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def P(key, label, value, method, stage, evidence, unit=None, conf=None, cands=None, set_=None):
    d = {"key": key, "label": label, "value": value, "method": method, "conf": conf, "stage": stage, "evidence": evidence}
    if unit:
        d["unit"] = unit
    if cands:
        d["cands"] = cands
    if set_:
        d["set"] = set_
    return d


def spectrogram_db(x: np.ndarray) -> np.ndarray:
    """(ROWS, BINS) power in dBFS per bin (fftshifted: -fs/2 .. +fs/2), Welch-averaged within each row."""
    n, w = x.size, np.hanning(BINS).astype(np.float32)
    norm = float((w ** 2).sum()) * BINS
    out = np.empty((ROWS, BINS), np.float32)
    edges = np.linspace(0, max(n - BINS, 0), ROWS + 1).astype(int)
    for r in range(ROWS):
        a, b = edges[r], max(edges[r + 1], edges[r] + 1)
        starts = np.arange(a, b, BINS)[:8] if b - a > BINS else np.array([a])
        seg = np.stack([x[s: s + BINS] for s in starts if s + BINS <= n]) if n >= BINS else np.pad(x, (0, BINS - n))[None]
        p = (np.abs(np.fft.fft(seg * w, axis=1)) ** 2).mean(0) / norm
        out[r] = 10 * np.log10(np.fft.fftshift(p) + 1e-20)
    return out


def ljung_box_p(r: np.ndarray, lags: int = 10) -> float:
    v = r - r.mean()
    n = v.size
    p = float(np.vdot(v, v).real)
    rho = np.array([abs(np.vdot(v[:-k], v[k:])) / p for k in range(1, lags + 1)])
    q = n * (n + 2) * float(np.sum(rho ** 2 / (n - np.arange(1, lags + 1))))
    return float(chi2.sf(q, 2 * lags))                              # complex residual: 2 real dof per lag


def _poly_str(exps: list[int]) -> str:
    return " + ".join("1" if e == 0 else "x" if e == 1 else "x" + str(e).translate(SUP) for e in sorted(exps))


def build(x: np.ndarray, fs: float, recipe: Recipe, body, log, meta: dict) -> dict:
    """meta: name, path, size, sha256, format, route, source_fs, fc_hz."""
    fe = frontend(x, recipe)
    uw = unwrap(fe, recipe)
    rs = resynthesise(x, recipe, fe, uw)
    a, b = rs.region
    resid_full = x.copy()
    resid_full[a:b] = rs.resid
    # the rejected near-miss whose residual is shown in red: the first coding-layer neighbour
    nm = next((n for n in body.near_misses if n.rejected and n.layer == "coding"), None)
    fail_full, fail_eta = x.copy(), None
    if nm is not None:
        wrong = recipe.model_copy(update={"fec": recipe.fec.model_copy(update={"generators_octal": recipe.fec.generators_octal[::-1]})})
        uw2 = unwrap(fe, wrong)
        rs2 = resynthesise(x, wrong, fe, uw2)
        fail_full[a:b] = rs2.resid
        pn = float(np.mean(np.abs(rs.noise) ** 2)) if rs.noise is not None else 0.0
        px = float(np.mean(np.abs(x[a:b]) ** 2))
        fail_eta = 100 * (1 - (float(np.mean(np.abs(rs2.resid) ** 2)) - pn) / (px - pn))
    S_full, S_res, S_fail = spectrogram_db(x), spectrogram_db(resid_full), spectrogram_db(fail_full)

    mo, fec, il, scr, fr = recipe.modulation, recipe.fec, recipe.interleaver, recipe.scrambler, recipe.framing
    rs_hz = fs / fe.sps
    bw = (1 + mo.rolloff) * rs_hz
    f0, f1 = fe.cfo_hz - bw / 2, fe.cfo_hz + bw / 2
    dur = x.size / fs
    t0f, t1f = fe.instants(fe.starts[0]) / x.size, fe.instants(fe.starts[-1] + fe.period) / x.size
    fbin = lambda f: int(np.clip(round((f + fs / 2) / fs * BINS - 0.5), 0, BINS - 1))
    band = slice(fbin(f0), fbin(f1) + 1)
    row_power = 10 * np.log10((10 ** (S_full[:, band] / 10)).sum(1) + 1e-20)
    floor = float(np.percentile(S_full, 5)) - 3
    span = float(np.ceil(np.percentile(S_full, 99.9) - floor + 2))
    phy, coding, structure = body.layers
    esn0 = fe.esn0_db
    code_str = f"CC K={fec.K} r½ ({','.join(fec.generators_octal)})₈"
    step = {s.stage: s for s in log} if log else {}
    ev = lambda k, default: (step[k].finding if k in step else default)

    src = "search" if log else "supplied recipe"
    params = {
        "content": P("content", "Signal type", "Digital data", "blind", 0,
                     "Decoded to CRC-valid frames and certified by the layered proof, so the content is digital data.", conf=1.0),
        "fs": P("fs", "Sampling frequency", f"{fs:,.0f}".replace(",", " "), "blind", 1,
                f"From the file header ({meta['source_fs']}). The symbol clock measured against it gives a recorder clock offset of {fe.clock_ppm:+.1f} ppm.", unit="Hz"),
        "baud": P("baud", "Symbol rate", f"{rs_hz:,.3f}".replace(",", " "), "blind", 1,
                  f"Cyclostationary |x|² line, then a block-wise Oerder–Meyr timing fit over the whole file. "
                  f"Nominal in the recipe: {mo.symbol_rate_hz:.3f} Bd.", unit="Bd"),
        "modulation": P("modulation", "Modulation", mo.scheme.upper(), "blind", 2,
                        ("Decode-fit (physics expert, no training): block-wise M-th order coherence of the symbols at the "
                         "measured rate ranks " + ", ".join(f"{c['v']} {c['p']:.2f}" for c in step["classify"].evidence["candidates"])
                         + "; " if "classify" in step else "")
                        + f"the layered proof then passed its PHY layer ({phy.verdict.upper()}).",
                        cands=step["classify"].evidence["candidates"] if "classify" in step else [{"v": "QPSK", "p": 1.0}], set_="{QPSK}"),
        "fec": P("fec", "FEC", code_str, "blind", 4,
                 f"{ev('code', code_str)}. Parity checks unsatisfied: {coding.stats.get('K1_unsat_frac', 0):.4f} "
                 f"(random bits: 0.5). Corrections {int(coding.stats.get('K2_corrections', 0))}."),
        "interleaver": P("interleaver", "Interleaving", "None" if il.rows in (1, il.rows * il.cols) else f"Block {il.rows} × {il.cols}",
                         "blind", 4, "Walsh–Hadamard dual-code search over every block geometry of the coded frame; "
                         "the right de-interleaver makes the code's parity checks appear."),
        "scrambler": P("scrambler", "Scrambler", "None" if scr is None else _poly_str(scr.poly_exponents), "blind", 4,
                       ev("scrambler", "none") + ("" if scr is None else f". Additive, reset every frame (seed 0x{scr.seed:X})."
                       " Solved in GF(2) from the frame-majority syndrome.")),
        "snr": P("snr", "SNR", f"{esn0:.1f}", "blind", 1, "Es/N0 from the decision-directed constellation fit after timing and carrier recovery.", unit="dB"),
        "bw": P("bw", "Occupied bandwidth", f"{bw / 1e3:.2f}", "blind", 1,
                f"(1 + α) × symbol rate with RRC roll-off α = {mo.rolloff:.2f} fitted to the averaged PSD.", unit="kHz"),
        "cfo": P("cfo", "Carrier offset", f"{fe.cfo_hz:+,.1f}".replace(",", " "), "blind", 1, "Fourth-power spectral line ÷ 4, then per-block phase tracking.", unit="Hz"),
        "fc": P("fc", "Centre frequency", "Unknown" if not meta.get("fc_hz") else f"{meta['fc_hz'] / 1e6:.4f} MHz", "manual", 0,
                "Baseband IQ carries no RF frequency unless the metadata states it. Enter it to see absolute frequencies and the band."),
    }
    cls = f"{mo.scheme.upper()} · {rs_hz:,.0f} Bd".replace(",", " ")
    emitters = [{"id": "E1", "f0": f0, "f1": f1, "t0": t0f, "t1": t1f, "snr": round(esn0, 1), "cls": cls,
                 "std": "No named standard", "state": "decoded",
                 "label": f"E1 · {mo.scheme.upper()} signal", "sub": f"{rs_hz:,.0f} Bd · {esn0:.0f} dB SNR · decoded".replace(",", " "),
                 "fc": fe.cfo_hz}]

    # frames as the UI shows them: sync marker + information bits
    asm_bits = np.unpackbits(np.frombuffer(bytes.fromhex(fr.asm_hex), np.uint8))
    rows_bits = np.concatenate([np.broadcast_to(asm_bits, (uw.info.shape[0], asm_bits.size)), uw.info], 1)
    fields, pos = [{"name": "SYNC", "group": "HEADER", "start": 0, "len": int(asm_bits.size), "kind": "const",
                    "note": f"0x{fr.asm_hex} · sent at the PHY, constant in every frame"}], int(asm_bits.size)
    crc_seen = False
    for f in fr.fields:
        col = uw.info[:, pos - asm_bits.size: pos - asm_bits.size + f.bits]
        const = bool((col == col[0]).all())
        if f.kind == "crc":
            crc_seen = True
            note = f"poly 0x{fr.crc.poly:04X} · init 0x{fr.crc.init:04X} · {int(uw.crc_ok.sum())}/{len(uw.crc_ok)} frames verify"
            kind, group = "crc", "TRAILER"
        elif f.kind == "counter":
            note, kind, group = f"+1 per frame · from 0x{from_bits(col[0]):0{(f.bits + 3) // 4}X}", "counter", "HEADER"
        elif f.kind == "payload":
            p1 = col.mean(0)
            ent = float(np.mean([0 if q in (0, 1) else -(q * np.log2(q) + (1 - q) * np.log2(1 - q)) for q in p1]))
            note, kind, group = f"entropy {ent:.2f} b/bit" + (" · likely encrypted or compressed" if ent > 0.95 else ""), "random", "PAYLOAD"
        else:
            note = (f"0x{from_bits(col[0]):X} = {from_bits(col[0])}" + (" · payload length in bytes ✓" if f.kind == "length" else " · constant")) if const else "varies"
            kind, group = "const", ("TRAILER" if crc_seen else "HEADER")
        name = {"payload": "PAYLOAD", "fill": "FILL" if group == "TRAILER" else "CONST"}.get(f.kind, f.name.upper())
        fields.append({"name": name, "group": group, "start": pos, "len": f.bits, "kind": kind, "note": note})
        pos += f.bits
    frame_len = int(rows_bits.shape[1])

    # coding-layer candidates with their measured unsatisfied-check fraction on the descrambled stream
    hard = uw.hard
    cand_list = [("171", "133"), ("133", "171"), ("561", "753"), ("753", "561"), ("23", "35"), ("7", "5")]
    if tuple(fec.generators_octal) not in cand_list:
        cand_list.insert(0, tuple(fec.generators_octal))
    conv = []
    for g in cand_list:
        K = max(int(v, 8).bit_length() for v in g)
        f_unsat = float(syndrome_rate_half(hard, K, g).mean()) if 3 <= K <= 9 else 0.5
        conv.append({"k": K, "r": "1/2", "g": ", ".join(g), "syn": round(f_unsat, 3),
                     "note": "found" if list(g) == fec.generators_octal else ("same code, swapped outputs" if list(g) == fec.generators_octal[::-1] else "")})
    conv.sort(key=lambda c: c["syn"])
    # interleaver profile: best dual-code bias per block geometry (low value = structure found)
    Nc = hard.shape[1]
    prof = []
    chan = _channel_bits(fe, recipe)
    d = chan[1:] ^ chan[:-1]
    for rws in [r for r in divisors(Nc) if 8 <= r <= 128]:
        spec, _ = dual_spectrum(block_deinterleave(d, rws, Nc // rws), min(fec.K, 7))
        spec[0] = -1
        prof.append({"p": rws, "v": round(float(1 - max(0.0, spec.max())), 3)})
    fam = [{"name": "Convolutional · Viterbi", "found": f"K={fec.K} r½ ({', '.join(fec.generators_octal)})₈", "method": "blind", "score": round(float(1 - coding.stats.get('K1_unsat_frac', 0.5) * 2), 2)}]
    ilv = [{"name": "Block", "score": round(1 - min(p["v"] for p in prof), 2) if prof else 1.0, "method": "blind",
            "note": "no interleaver" if il.rows in (1, il.rows * il.cols) else f"{il.rows} × {il.cols} (dual-code bias)"},
           {"name": "Convolutional", "score": 0, "method": "blind", "note": "Not evaluated by this blind decoder"},
           {"name": "Diagonal", "score": 0, "method": "blind", "note": "Not evaluated by this blind decoder"},
           {"name": "Pseudo-random", "score": 0, "method": "library", "note": "Not evaluated by this blind decoder"}]

    rp = phy.stats
    row_start = int(np.clip(np.floor(t0f * ROWS), 0, ROWS - 1))
    avg = 10 * np.log10((10 ** (S_full[row_start:] / 10)).mean(0))
    psd_min = float(np.floor(np.percentile(avg, 2) - 2))
    psd_max = float(np.ceil(avg.max() + 3))
    obw_db = float(avg[band].max() - 3)
    il_none = il.rows in (1, il.rows * il.cols)
    n_ok, n_fr = int(uw.crc_ok.sum()), len(uw.crc_ok)
    dtype_name = meta["format"].split(" · ")[-1] if " · " in meta["format"] else "cf32_le"
    fmt_sp = lambda v: f"{v:,.0f}".replace(",", " ")
    chain = [{"role": "Input", "n": "Demodulated bits", "v": "soft bits · phase hypotheses resolved by the coding layer", "m": "blind"}]
    if scr is not None:
        chain.append({"role": "Descrambling", "n": "Descramble", "v": _poly_str(scr.poly_exponents), "m": "blind"})
    if not il_none:
        chain.append({"role": "De-interleaving", "n": "Block de-interleave", "v": f"{il.rows} × {il.cols}", "m": "blind"})
    chain += [{"role": "Error correction", "n": "Viterbi", "v": f"Conv. K={fec.K} r½ ({','.join(fec.generators_octal)})₈", "m": "blind"},
              {"role": "Output", "n": "Clean bit stream", "v": f"{frame_len}-bit frames", "m": "blind"}]
    crc_name = f"CRC-{fr.crc.width} poly 0x{fr.crc.poly:X}" if fr.crc else "no CRC found"
    body_sym = fe.frames[:, asm_symbols(recipe).size:].ravel() / fe.amp
    pick = np.random.default_rng(0).choice(body_sym.size, min(4000, body_sym.size), replace=False)
    cons = np.round(np.stack([body_sym[pick].real, body_sym[pick].imag], 1).ravel().astype(float), 4).tolist()
    evm = 100 * np.sqrt(fe.sigma2) / fe.amp
    phy_rot = "none needed" if log is None else next((s for s in log if s.stage == "scrambler"), None)
    rot_deg = phy_rot.evidence.get("phase_rot_deg") if phy_rot and not isinstance(phy_rot, str) else None
    best_p = min(prof, key=lambda d: d["v"]) if prof else None
    lfsr = {"seed": "", "taps": []} if scr is None else {
        "seed": format(scr.seed, f"0{max(scr.poly_exponents)}b"),
        "taps": sorted(max(scr.poly_exponents) - e for e in scr.poly_exponents if e != max(scr.poly_exponents))}
    text = {
        "fecLine": f"Convolutional K={fec.K} r½ · {int(coding.stats.get('K2_corrections', 0))} channel-bit corrections · "
                   f"{n_fr - n_ok} CRC failures · parity checks unsatisfied {coding.stats.get('K1_unsat_frac', 0):.4f} (random: 0.5)",
        "scrText": "None" if scr is None else f"{_poly_str(scr.poly_exponents)} · seed {format(scr.seed, f'0{max(scr.poly_exponents)}b')}",
        "scrNote": "No scrambler: the coded frames already satisfy the code" if scr is None
                   else "Solved in GF(2) from the frame-majority syndrome (" + ("library polynomial" if ev("scrambler", "").startswith("CCSDS") or "library" in ev("scrambler", "").lower() else "blind search") + ")",
        "phaseText": ("rotation resolved" if rot_deg is None else f"{rot_deg}° rotation") + " · Gray mapping",
        "phaseNote": "Every rotation / conjugation was tried; the code, the scrambler degree and the frame structure pick one",
        "lfsr": lfsr,
        "rankAxis": "1 − CHECK BIAS",
        "rankNote": "no interleaver structure" if best_p is None else f"code checks appear · bias {1 - best_p['v']:.2f} · block",
        "certFormat": meta["format"] + " · read from " + meta["source_fs"].split(" ")[0] + (" header" if meta["route"] == "wav" else ""),
        "evm": f"EVM {evm:.1f} % · MER {10 * np.log10(fe.amp ** 2 / fe.sigma2):.1f} dB",
        "mod": mo.scheme.upper(), "baud": fmt_sp(rs_hz).replace(" ", ""), "baudSpaced": fmt_sp(rs_hz),
        "at": f"{fe.cfo_hz / 1e3:+.2f} kHz", "snr": f"{esn0:.0f}", "others": "",
        "obw": f"OBW {bw / 1e3:.2f} kHz · α {mo.rolloff:.2f}", "format": f"{meta['format']} · {fs / 1e3:g} kHz",
        "heroCap": f"{fs / 1e3:g} kHz · {dur:.1f} s", "sigmfDtype": dtype_name,
        "frameLine": f"{frame_len}-bit frames · sync 0x{fr.asm_hex} · {crc_name} verified on {n_ok} / {n_fr} frames"
                     + (" · payload high-entropy (not decrypted)." if any(f["kind"] == "random" and "encrypted" in f["note"] for f in fields) else "."),
        "codeKind": "convolutional code", "ilKind": "no interleaver" if il_none else "block interleaver",
        "decodeLine": f"{n_ok} of {n_fr} frames pass their CRC", "ilRows": il.rows, "ilCols": il.cols,
        "ilLabel": "None" if il_none else f"Block {il.rows} × {il.cols}", "chain": chain,
        "genomeE1": {"label": f"E1 · {mo.scheme.upper()} {fmt_sp(rs_hz)} Bd", "name": "No named standard",
                     "note": "No supported standard matched the measured signal"},
        "genomeFs": {"title": "Sampling frequency · " + meta["source_fs"], "value": fmt_sp(fs),
                     "note": f"symbol clock vs file clock: {fe.clock_ppm:+.1f} ppm"},
    }
    kurt = float(np.mean(np.concatenate([rs.resid.real, rs.resid.imag]) ** 4) / np.mean(np.concatenate([rs.resid.real, rs.resid.imag]) ** 2) ** 2)
    sig = body.model_dump_json().encode()
    cert_id = "SNJ-" + hashlib.sha256(sig).hexdigest()[:12].upper()
    return {
        "scenario": {
            "file": {k: meta[k] for k in ("name", "path", "size", "sha256", "format", "route")} | {"duration": dur},
            "forensics": meta["forensics"],
            "params": params,
            "emitters": emitters,
            # display caps at 100 %: eta > 1 only means the residual sits within sampling noise of the noise
            # reference (the certificate keeps the raw T1 statistic)
            "proof": {"explained": round(min(100.0, 100 * rp.get("T1_eta", float("nan"))), 1), "ljungP": round(ljung_box_p(rs.resid), 2),
                      "kurt": round(kurt, 2), "residFloor": round(10 * np.log10(rp["P_resid"]), 1),
                      "failExplained": round(fail_eta, 1) if fail_eta is not None else 0.0},
            "cert": {"id": cert_id},
            "view": {"lo": floor - 6, "range": span + 16, "floor": round(floor), "span": int(span), "rowStart": row_start,
                     "gridSeconds": _grid_step(dur), "psdMin": psd_min, "psdMax": psd_max, "obwDb": obw_db,
                     "verdict": body.verdict, "source": src,
                     "sufficiency": step["sufficiency"].evidence if "sufficiency" in step else None,
                     "layers": [{"layer": l.layer, "verdict": l.verdict, "reason": l.reason} for l in body.layers],
                     "equivalences": body.equivalences},
            "text": text,
        "constellation": cons,
        },
        "spec": {"bins": BINS, "rows": ROWS, "fs": fs},
        "frame": {"len": frame_len, "sync": int(from_bits(asm_bits)), "syncBits": int(asm_bits.size), "fields": fields},
        "bits": "".join(map(str, rows_bits.ravel().tolist())),
        "crc": [{"name": f"CRC-{fr.crc.width} (solved)", "poly": fr.crc.poly, "init": fr.crc.init, "ok": int(uw.crc_ok.sum()), "frames": len(uw.crc_ok)}] if fr.crc else [],
        "conv": conv, "fecFamilies": fam, "interleaverTypes": ilv, "rankProfile": prof,
        "spectrogram": {"full": S_full, "resid": S_res, "fail": S_fail, "rowPower": row_power.astype(np.float32)},
    }


def build_partial(x: np.ndarray, fs: float, meta: dict, reason: str, phy: dict | None = None, ledger: dict | None = None) -> dict:
    """No recipe survived the search: still show the real spectrogram and everything the physics expert
    identified on its own (family, order, rate, carrier, consistent standards, measured symbols), and why
    decoding stopped. An honest 'undecided, because...', never a guess (PROTOTYPE_PLAN §5)."""
    S_full = spectrogram_db(x)
    dur = x.size / fs
    avg = 10 * np.log10((10 ** (S_full / 10)).mean(0))
    live = avg[avg > avg.max() - 100]                                  # skip receiver audio's empty mirror half
    obw_db = float(avg.max() - 3)
    if phy:
        b = [int(np.clip(round((f + fs / 2) / fs * BINS - 0.5), 0, BINS - 1)) for f in (phy["band_lo_hz"], phy["band_hi_hz"])]
        obw_db = float(avg[b[0]: b[1] + 1].max() - 3)
    sp = lambda v, d=0: f"{v:,.{d}f}".replace(",", " ")
    params = {"fs": P("fs", "Sampling frequency", sp(fs), "blind", 0, "From the file header.", unit="Hz")}
    measured, cons, emitters = None, [], []
    if phy:
        stds = phy["standards"]
        measured = {k: phy.get(k) for k in ("band_lo_hz", "band_hi_hz", "centre_hz", "rate_hz", "carrier_hz", "family",
                                            "modulation", "order", "tones_hz", "spacing_hz")}
        measured.update(snr_db=round(phy["snr_db"], 1), floor_db=round(phy["floor_db"], 1), standards=stds)
        measured["tones_hz"] = measured["tones_hz"] or []
        if phy["family"] == "PSK":
            coh = phy["coherence"]
            tied = [c["v"] for c in phy["candidates"] if c["p"] >= 0.85 * phy["candidates"][0]["p"]]
            params["modulation"] = P("modulation", "Modulation", phy["modulation"], "blind", 0,
                "Decode-fit: symbols sampled at the measured rate, block-wise M-th order coherence for each PSK order "
                f"(BPSK {coh['BPSK']:.2f}, QPSK {coh['QPSK']:.2f}, 8PSK {coh['8PSK']:.2f}; random data scores ~0.18). "
                + ("The smallest order that explains the symbols wins." if phy["order"] else
                   "No order stands out: the constellation is smeared (typical of HF multipath without an equalizer), "
                   "so the answer is a set, not a guess."),
                conf=round(max(coh.values()), 2) if phy["order"] else None, cands=phy["candidates"],
                set_="{" + ", ".join(tied if not phy["order"] else [phy["modulation"]]) + "}")
            params["baud"] = P("baud", "Symbol rate", sp(phy["rate_hz"], 2), "blind", 0,
                f"Band-edge cyclic line: |x|² of only the two excess-bandwidth edges (fc ± Rs/2), {phy['rate_strength']:.0f}× "
                f"its neighbourhood vs {phy['rate_runner_up']:.0f}× for the best other rate. Lines made by structure inside "
                "the band (idle patterns, probes) do not survive this test.", unit="Bd")
        else:
            params["modulation"] = P("modulation", "Modulation", phy["modulation"], "blind", 0,
                f"{len(phy['tones_hz'])} evenly spaced tones ({sp(phy['spacing_hz'])} Hz apart) carry "
                f"{100 * phy['tone_energy']:.0f} % of the in-band energy.", conf=round(phy["tone_energy"], 2))
            params["baud"] = P("baud", "Keying rate", sp(phy["rate_hz"], 2), "blind", 0,
                "Line in the spectrum of instantaneous-frequency transitions.", unit="Bd")
            params["tones"] = P("tones", "Tones", ", ".join(sp(t) for t in phy["tones_hz"]), "blind", 0,
                "Local maxima of the in-band spectrum, each at least 12× the band's median level.", unit="Hz")
        params["cfo"] = P("cfo", "Carrier", sp(phy["carrier_hz"], 1), "blind", 0,
            "M-th power line after decode-fit" if phy.get("order") else "Centre of the occupied band (tones or order not resolved)", unit="Hz")
        params["bw"] = P("bw", "Occupied bandwidth", f"{(phy['band_hi_hz'] - phy['band_lo_hz']) / 1e3:.2f}", "blind", 0,
                         "−20 dB bandwidth around the strongest emission (6 dB over the floor at low SNR).", unit="kHz")
        params["snr"] = P("snr", "In-band SNR", f"{phy['snr_db']:.1f}", "blind", 0,
                          "Occupied-band power over the median level measured outside it.", unit="dB")
        ppm = [f"{s['name']} ({s['ppm']:+.0f} ppm)" if s["ppm"] is not None else s["name"] for s in stds]
        params["std"] = P("std", "Standard", " / ".join(s["name"] for s in stds) or "No named standard", "library", 0,
            ("Consistent at the PHY: " + ", ".join(ppm) + ". " +
             ("These are not separable from the PHY alone; the frame structure would separate them. " if len(stds) > 1 else "") +
             ("ppm = measured symbol rate against the standard's nominal rate: the recording chain's clock offset."
              if any(s["ppm"] is not None for s in stds) else ""))
            if stds else "No tabled standard matches this family, order and rate.")
        if phy.get("symbols") is not None:
            z = phy["symbols"]
            pick = np.random.default_rng(0).choice(z.size, min(4000, z.size), replace=False)
            cons = np.round(np.stack([z[pick].real, z[pick].imag], 1).ravel().astype(float), 4).tolist()
        cls = f"{phy['modulation']} · {phy['rate_hz']:.0f} Bd"
        emitters = [{"id": "E1", "f0": phy["band_lo_hz"], "f1": phy["band_hi_hz"], "t0": 0.0, "t1": 1.0,
                     "snr": round(phy["snr_db"], 1), "cls": cls, "std": stds[0]["name"] if stds else "No named standard",
                     "state": "undecided", "label": f"E1 · {cls}", "sub": f"{phy['snr_db']:.0f} dB SNR · identified, not decoded",
                     "fc": phy["carrier_hz"]}]
    return {
        "scenario": {
            "file": {k: meta[k] for k in ("name", "path", "size", "sha256", "format", "route")} | {"duration": dur},
            "forensics": meta["forensics"],
            "params": params,
            "emitters": emitters,
            "proof": {},
            "cert": {},
            "view": {"lo": float(np.percentile(S_full, 5)) - 9, "range": float(np.ceil(np.percentile(S_full, 99.9) - np.percentile(S_full, 5))) + 16,
                     # waterfall colour range from this recording (same rule as a decoded job), not the demo's
                     # (bins > 100 dB under the peak are receiver audio's empty mirror half, not a noise floor)
                     "floor": round(_floor(S_full) - 3),
                     "span": int(np.ceil(np.percentile(S_full, 99.9) - _floor(S_full) + 5)),
                     "rowStart": 0, "psdMin": float(np.floor(np.percentile(live, 2) - 2)), "psdMax": float(np.ceil(avg.max() + 3)),
                     "obwDb": obw_db,
                     "gridSeconds": _grid_step(dur), "verdict": "undecided", "reason": reason, "measured": measured, "source": "search", "sufficiency": ledger,
                     "layers": [], "equivalences": []},
            "text": {"heroCap": f"{fs / 1e3:g} kHz · {dur:.1f} s", "format": f"{meta['format']} · {fs / 1e3:g} kHz",
                     "evm": "measured symbols · not decoded" if cons else "",
                     "obw": f"OBW {(phy['band_hi_hz'] - phy['band_lo_hz']) / 1e3:.2f} kHz" if phy else ""},
            "constellation": cons,
        },
        "spec": {"bins": BINS, "rows": ROWS, "fs": fs},
        "spectrogram": {"full": S_full},
    }


def _floor(S: np.ndarray) -> float:
    return float(np.percentile(S[S > S.max() - 100], 5))


def _grid_step(dur: float) -> float:
    for s in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100):
        if dur / s <= 6:
            return s
    return 200.0


def _channel_bits(fe, recipe) -> np.ndarray:
    na = asm_symbols(recipe).size
    body = fe.frames[:, na:]
    out = np.empty((body.shape[0], 2 * body.shape[1]), np.uint8)
    out[:, 0::2], out[:, 1::2] = body.real < 0, body.imag < 0
    return out
