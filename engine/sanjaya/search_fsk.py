"""Blind FSK discovery: frame/sync/code/interleaver/scrambler/structure for an unknown FSK recording,
with no recipe supplied. Reuses the exact same dual-code search (coding/blind.py) and Bit-Lens field
discovery (bits/lens.py) that search.py's QPSK/BPSK blind path uses -- applied directly to non-coherent
tone-bank hard bits instead of complex symbols.

Why this is architecturally safer than extending blind search to 8PSK/16QAM/64QAM (which search.py's
module docstring explains is NOT attempted): those constellations have a rotation-to-bit-pattern
relationship that is not guaranteed data-independent past 2 points, so a wrong hypothesis there risks a
wrong blind decode. FSK has no such ambiguity -- a non-coherent tone-energy decision maps each symbol to
a Gray-labelled tone index directly (demod.fsk_llr), with no rotation, no phase, and no I/Q-swap concept
at all. The identify_code/solve_scrambler dual-code search itself is bit-stream algebra and does not
care what physical layer produced the bits.

Scope: rate-1/2 convolutional code + block interleaver + additive scrambler, same as the QPSK/BPSK path
-- diagonal/pseudo-random interleavers and RS/LDPC are not attempted here for the same reason they are
not attempted blind for PSK/QAM: no analogous structural test exists yet for them."""
import numpy as np
from .recipe import Recipe, Modulation, ConvCode, Interleaver, Scrambler, Field, Framing
from .demod import fsk_llr
from .coding.blind import identify_code, solve_scrambler, edge_violations
from .sufficiency import Z_CODE
from .fsk import unwrap_fsk, FskFrontEnd

MIN_SYNC = 8
CONST_FRAC = 0.85          # bit-agreement fraction for a "constant" (sync-marker) column
ALIGN = {1: 8, 2: 8, 3: 24}  # ASM bit-length alignment: lcm(8, bits/symbol) -- keeps hex packing and tone-symbol boundaries exact


class SearchErrorFSK(RuntimeError):
    pass


def discover_frames_bits(hard: np.ndarray, pmin: int = 16, pmax: int = 8192):
    """Bit-domain analogue of search.discover_frames: smallest period whose fold shows a run of
    majority-constant bit columns (a PHY sync marker). Returns (period, start col, length, template bits)."""
    for P in range(pmin, min(pmax, hard.size // 4) + 1):
        m = hard.size // P
        cols = hard[: m * P].reshape(m, P)
        ones = cols.sum(0)
        agree = np.maximum(ones, m - ones) / m
        const = agree > CONST_FRAC
        if const.sum() < MIN_SYNC:
            continue
        c2 = np.concatenate([const, const])
        best, s, run = (0, 0), None, 0
        for i, v in enumerate(c2):
            run = run + 1 if v else 0
            if run > best[0]:
                best = (min(run, P), i - run + 1)
        if best[0] >= MIN_SYNC:
            L, st = best
            st %= P
            cols_run = np.take(cols, np.arange(st, st + L) % P, axis=1)
            tmpl = (cols_run.sum(0) * 2 > m).astype(np.uint8)
            return P, st, L, tmpl
    return None


def blind_fsk_search(x: np.ndarray, fs: float, phy: dict, log, led) -> tuple[Recipe, list]:
    """phy: classify.identify()'s FSK result (tones_hz, rate_hz). Raises SearchErrorFSK if nothing fits."""
    from .search import Step, lens_fields  # local import: search.py imports this module's blind path

    tones = np.asarray(phy["tones_hz"], dtype=float)
    bps = int(np.log2(tones.size))
    rate = float(phy["rate_hz"])
    sps = fs / rate
    align = ALIGN[bps]

    phase_candidates = np.unique(np.round(np.linspace(0, sps, 8, endpoint=False)).astype(int))
    best_fr, best_hard = None, None
    for start in phase_candidates:
        if start < 0 or start >= x.size:
            continue
        try:
            llr = fsk_llr(x, fs, rate, tones, start_sample=int(start))
        except ValueError:
            continue
        hard = (llr < 0).astype(np.uint8)
        fr = discover_frames_bits(hard)
        if fr and (best_fr is None or fr[2] > best_fr[2]):
            best_fr, best_hard = fr, hard
    if best_fr is None:
        led.add("Frame period and sync", "undecided", "no repeating constant bit run for any FSK symbol phase", "structure")
        raise SearchErrorFSK("No supported repeating sync marker was found under the FSK hypothesis")
    P, st, run_len, run_tmpl = best_fr
    hard = best_hard
    frame_s = P / (rate * bps)
    led.add("Frame period and sync", "decided", f"period {P} bits ({1e3 * frame_s:.1f} ms), constant run {run_len} bits")

    viable = []
    for L in range(min(run_len, 64) // align * align, MIN_SYNC - 1, -align):
        if L <= 0 or (P - L) % 2 != 0:      # rate-1/2 coded length must be even
            continue
        for o in range(run_len - L + 1):
            so = (st + o) % P
            tmpl = run_tmpl[o: o + L]
            starts = np.arange(so, hard.size - P + 1, P)
            if starts.size < 3:
                continue
            seg = np.stack([hard[s: s + L] for s in starts])
            agree = (seg == tmpl[None]).mean(1)
            keep = agree > 0.8
            if keep.sum() < 3:
                continue
            body = np.stack([hard[s: s + P] for s in starts[keep]])[:, L:]
            for h in identify_code(body):
                if not (h.bias > Z_CODE * h.noise_level and h.runner_up < 0.5 * h.bias):
                    continue
                for exhaustive in (0, 8):
                    sc = solve_scrambler(body, h, exhaustive)
                    if sc:
                        edge = edge_violations(body, h, sc[1], sc[2])
                        viable.append(((max(sc[1]) if sc[1] else 0, sc[3], edge, L), h, L, tmpl, body, sc))
                        break
    if not viable:
        led.add("Code and interleaver", "undecided", "no rate-1/2 convolutional structure at any sync alignment", "structure")
        raise SearchErrorFSK("no rate-1/2 convolutional structure for any sync alignment under the FSK hypothesis")
    viable.sort(key=lambda v: v[0])
    tied = [v for v in viable if v[0][:3] == viable[0][0][:3]][:8]

    scored = []
    for key, h, L, tmpl, body, sc in tied:
        recipe, info_log = _assemble_fsk(x, fs, tones, rate, P, L, tmpl, h, sc)
        if recipe is None:
            continue
        f = recipe.framing
        score = (f.crc is not None) + any(fd.kind == "counter" for fd in f.fields) + recipe.fec.terminated
        scored.append((score, -key[1], recipe, info_log, h, L, sc))
    if not scored:
        led.add("Structure", "undecided", "no scored hypothesis reached a decodable frame", "structure")
        raise SearchErrorFSK("no FSK hypothesis reached a decodable frame")
    scored.sort(key=lambda t: -t[0])
    score, _, recipe, info_log, code, L, (sname, sexps, sseed, sbad) = scored[0]
    log.append(Step("frame", f"frame period {P} bits, sync marker {L} bits ({recipe.framing.asm_hex})", "blind",
                    {"period": P, "constant_run": run_len, "sync_len": L, "hypotheses_viable": len(viable)}))
    log.append(Step("code", f"conv K={code.K} ({','.join(code.generators_octal)}), block interleaver {code.rows}x{code.cols}",
                    "blind", {"bias": code.bias, "noise_level": code.noise_level}))
    log.append(Step("scrambler", "none" if not sexps else f"{sname}: poly exponents {sexps}, seed 0x{sseed:X}",
                    "blind" if sname.startswith("blind") else "library", {"inconsistent_checks": sbad}))
    log.extend(info_log)
    led.add("Code and interleaver", "decided", f"K={code.K} ({','.join(code.generators_octal)}), {code.rows}x{code.cols}")
    led.add("Scrambler", "decided", "none" if not sexps else f"{sname}, seed 0x{sseed:X}")
    led.add("Frame structure", "decided", ", ".join(f.name for f in recipe.framing.fields))
    return recipe, log


def _assemble_fsk(x, fs, tones, rate, P, L, tmpl, code, sc):
    from .search import Step, lens_fields

    sname, sexps, sseed, _ = sc
    scr = Scrambler(poly_exponents=sexps, seed=sseed) if sexps else None
    asm_hex = np.packbits(tmpl).tobytes().hex().upper()
    coded_len_bits = P - L
    raw_bits = coded_len_bits // 2
    fec = ConvCode(K=code.K, generators_octal=code.generators_octal, terminated=False)
    scheme = f"fsk{tones.size}"
    spacing = float(np.median(np.diff(tones)))
    base = Recipe(sample_rate_hz=fs, modulation=Modulation(scheme=scheme, symbol_rate_hz=rate, rolloff=0.0,
                  fsk_tone_spacing_hz=spacing), fec=fec, interleaver=Interleaver(rows=code.rows, cols=code.cols),
                  scrambler=scr, framing=Framing(asm_hex=asm_hex, fields=[Field(name="data", bits=raw_bits, kind="payload")]))
    try:
        fe, uw = unwrap_fsk(x, base)
    except RuntimeError:
        return None, []
    if uw.info.shape[0] < 2:
        return None, []
    term = bool((uw.info[:, -(code.K - 1):] == 0).all(1).mean() >= 0.9)
    if term:
        base = base.model_copy(update={"fec": fec.model_copy(update={"terminated": True}),
                                       "framing": base.framing.model_copy(update={"fields": [Field(name="data", bits=raw_bits - code.K + 1, kind="payload")]})})
        try:
            fe, uw = unwrap_fsk(x, base)
        except RuntimeError:
            return None, []
    info = uw.info
    slots = (fe.starts_bits - fe.starts_bits[0]) // P
    fields, crc = lens_fields(info, slots)
    recipe = base.model_copy(update={"framing": base.framing.model_copy(update={"fields": fields, "crc": crc})})
    return recipe, [Step("structure", ", ".join(f"{f.name}[{f.bits}]" for f in fields), "blind",
                         {"terminated": term, "crc": None if crc is None else f"width {crc.width} poly 0x{crc.poly:X} init 0x{crc.init:X}"})]
