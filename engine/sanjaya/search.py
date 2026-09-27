"""Blind recipe search, v1 (fast path). Stages follow the hypothesis tree of PRD §6.5; each stage records
what it found, how (blind / library), and the evidence, and hands ranked alternatives downstream.
Scope v1: single-carrier QPSK, PHY sync marker, frame-aligned block interleaver, rate-1/2 conv code,
frame-synchronous additive scrambler, CRC framing. Anything outside raises SearchError with the reason."""
from dataclasses import dataclass, field
import numpy as np
from .recipe import Recipe, Modulation, ConvCode, Interleaver, Scrambler, Crc, Field, Framing
from .measure import symbol_rate_blind, cfo_power, rolloff_psd
from .classify import identify
from .pipeline import symbols, frontend, unwrap
from .coding.blind import identify_code, solve_scrambler, edge_violations, CodeHypothesis
from .bits.lens import find_counter, find_crc, constant_runs

CONST_FRAC = 1 / 3            # a folded column is "constant" if |sum| ^ 2 / (m P) exceeds this fraction of m
MIN_SYNC = 8                  # minimum sync-marker length in symbols


class SearchError(RuntimeError):
    phy: dict | None = None            # the classify result, so an undecided job still reports what was identified


@dataclass
class Step:
    stage: str
    finding: str
    method: str                   # blind | library | measured
    evidence: dict = field(default_factory=dict)


def _qpsk_bits(s: np.ndarray) -> np.ndarray:
    b = np.empty((*s.shape[:-1], 2 * s.shape[-1]), np.uint8)
    b[..., 0::2], b[..., 1::2] = s.real < 0, s.imag < 0
    return b


def discover_frames(ys: np.ndarray, pmin: int = 16, pmax: int = 8192):
    """Smallest period whose fold shows a run of constant symbol columns (a PHY sync marker).
    Returns (period, sync start column, sync length, template symbols)."""
    pw = float(np.mean(np.abs(ys) ** 2))
    for P in range(pmin, min(pmax, ys.size // 4) + 1):
        m = ys.size // P
        col = ys[: m * P].reshape(m, P).sum(0)
        const = np.abs(col) ** 2 / (m * pw) > CONST_FRAC * m
        if const.sum() < MIN_SYNC:
            continue
        c2 = np.concatenate([const, const])                       # circular run search
        best, s, run = (0, 0), None, 0
        for i, v in enumerate(c2):
            run = run + 1 if v else 0
            if run > best[0]:
                best = (min(run, P), i - run + 1)
        if best[0] >= MIN_SYNC:
            L, st = best
            st %= P
            tmpl = np.take(col, np.arange(st, st + L) % P)
            tmpl = (np.sign(tmpl.real) + 1j * np.sign(tmpl.imag)) * np.sqrt(0.5)
            return P, st, L, tmpl.astype(np.complex64)
    return None


def blind_search(x: np.ndarray, fs: float, on_step=None) -> tuple[Recipe, list[Step]]:
    """on_step(step) is called as each stage completes (progress for the API / UI)."""
    log: list[Step] = []
    if on_step is not None:
        class _Log(list):
            def append(self, s):
                super().append(s)
                on_step(s)

            def extend(self, it):
                for s in it:
                    self.append(s)
        log = _Log()
    phy = identify(x, fs)
    try:
        return _search(x, fs, log, phy)
    except SearchError as e:
        if phy is not None and phy["family"] == "PSK" and not phy["order"]:
            e.args = (f"PSK order not separable (symbols smeared, e.g. HF multipath with no equalizer); "
                      f"under the QPSK hypothesis: {e.args[0]}",)
        e.phy = phy
        raise


def _search(x, fs, log, phy):
    # 0 CLASSIFY (physics expert) ----------------------------------------------------------------------------
    if phy is None:
        raise SearchError("no emission stands out from the noise floor")
    std = ", ".join(s["name"] for s in phy["standards"])
    log.append(Step("classify", f"{phy['modulation']} at {phy['rate_hz']:.2f} Bd" + (f", consistent with {std}" if std else ""),
                    "blind", {"family": phy["family"], "coherence": phy.get("coherence"), "candidates": phy.get("candidates"),
                              "standards": phy["standards"]}))
    if phy["family"] == "FSK" or phy["order"] not in (None, 4):
        raise SearchError(f"{phy['modulation']} at {phy['rate_hz']:.2f} Bd identified; the v1 blind coding layer covers "
                          f"QPSK with a convolutional code, so this family's coding is not in the hypothesis set yet")
    # 1-2 OBSERVE / MEASURE ---------------------------------------------------------------------------------
    rs0 = symbol_rate_blind(x, fs)
    cfo0 = cfo_power(x, fs, 4)
    beta = round(rolloff_psd(x, fs, rs0, cfo0), 2)
    ys, sps, t0, cfo, theta = symbols(x, fs, fs / rs0, beta)
    rs = fs / sps
    log.append(Step("measure", f"symbol rate {rs:.3f} Bd, roll-off {beta:.2f}, CFO {cfo:.2f} Hz", "measured",
                    {"cyclic_line_hz": rs0, "timing_fit_hz": rs, "rolloff_psd": beta, "cfo_hz": cfo}))
    # 3 FRAME / SYNC -------------------------------------------------------------------------------------------
    fr = discover_frames(ys)
    if fr is None:
        raise SearchError("no PHY sync marker found (coded-domain sync search arrives with the Meteor path, G3)")
    P, run_st, run_len, run_tmpl = fr

    def alignments():
        """Every byte-aligned (length, offset) of a sync marker inside the constant run, longest first."""
        for L in range(min(run_len, 64) // 4 * 4, MIN_SYNC - 1, -4):
            for o in range(run_len - L + 1):
                st, tmpl = (run_st + o) % P, run_tmpl[o: o + L]
                starts = np.arange(st, ys.size - P + 1, P)
                seg = np.stack([ys[s: s + L] for s in starts])
                c = seg @ np.conj(tmpl)
                keep = np.abs(c) / (np.linalg.norm(seg, axis=1) * np.linalg.norm(tmpl) + 1e-12) > 0.5
                if keep.sum() >= 3:
                    rot = np.round(np.angle(c[keep]) / (np.pi / 2)) * (np.pi / 2)
                    yield L, o, tmpl, (np.stack([ys[s: s + P] for s in starts[keep]]) * np.exp(-1j * rot)[:, None])[:, L:]

    def phase_hyps(h):
        for conj in (False, True):
            for k in range(4):
                if (k % 2 == 1) == h.swap:                         # chain model has no I/Q-bit swap
                    yield conj, k, (lambda cj, kk: lambda z: (np.conj(z) if cj else z) * np.exp(1j * kk * np.pi / 2))(conj, k)

    # Pass 1: find the code, geometry, scrambler polynomials and phase hypotheses at the first alignment where
    # everything fits (library scramblers in a first sweep, exhaustive low degree in a second).
    hs, polys, phases, codes = [], [], set(), {}
    for exhaustive in (0, 8):
        for L, o, tmpl, body in alignments():
            nc = 2 * body.shape[1]
            if nc not in codes:                                    # the code is ~shift-invariant: once per length
                ident = next((v for v in codes.values() if v and v[0].rows in (1, v[0].rows * v[0].cols)), None)
                codes[nc] = [CodeHypothesis(h.swap, 1, nc, h.K, h.generators_octal, h.bias, h.noise_level, h.runner_up)
                             for h in ident] if ident else                             [h for h in identify_code(_qpsk_bits(body)) if h.bias > 10 * h.noise_level and h.runner_up < 0.5 * h.bias]
            for h in codes[nc]:
                ch = CodeHypothesis(False, h.rows, h.cols, h.K, h.generators_octal, h.bias, h.noise_level, h.runner_up)
                for conj, k, tf in phase_hyps(h):
                    sc = solve_scrambler(_qpsk_bits(tf(body)), ch, exhaustive, library=not exhaustive)
                    if sc:
                        phases.add((conj, k))
                        if sc[1] and (sc[0], sc[1]) not in polys:
                            polys.append((sc[0], sc[1]))
            if phases:
                hs = codes[nc]
                break
        if phases:
            break
    if not any(codes.values()):
        raise SearchError("no rate-1/2 convolutional structure for any sync alignment")
    if not phases:
        raise SearchError("no additive scrambler of degree <= 8 (or in the library) fits the coded frames")
    # Constant columns hold the marker AND constant coded symbols next to it (fill, tail, fixed header bits);
    # interleaving makes the code nearly shift-invariant. Pass 2 fits code + scrambler at every alignment.
    viable = []
    for L, o, tmpl, body in alignments():
        for h in hs:
            nc = 2 * body.shape[1]
            if h.rows in (1, h.rows * h.cols):                    # identity geometry fits any block length
                h = CodeHypothesis(h.swap, 1, nc, h.K, h.generators_octal, h.bias, h.noise_level, h.runner_up)
            elif h.rows * h.cols != nc:
                continue
            ch = CodeHypothesis(False, h.rows, h.cols, h.K, h.generators_octal, h.bias, h.noise_level, h.runner_up)
            for conj, k, tf in phase_hyps(h):
                if (conj, k) not in phases:
                    continue                                       # phases are shared by every alignment
                bits = _qpsk_bits(tf(body))
                sc = solve_scrambler(bits, ch, 0, polys, library=False)
                if sc:
                    edge = edge_violations(bits, ch, sc[1], sc[2])
                    viable.append(((max(sc[1]) if sc[1] else 0, sc[3], edge, L), h, L, tmpl, body, conj, k, sc, tf))
    if not viable:
        raise SearchError("no additive scrambler of degree <= 8 (or in the library) fits the coded frames")
    viable.sort(key=lambda v: v[0])
    # rank: lowest scrambler degree, fewest inconsistent checks, fewest block-edge violations, shortest marker;
    # only the best few are decoded, and structure (CRC, counter, termination) breaks the remaining ties
    tied = [v for v in viable if v[0][:3] == viable[0][0][:3]][:8]
    # Codes transparent to inversion (e.g. K=7 (171,133)) leave a complement twin the coding layer cannot see;
    # structure decides (an inverted counter decrements), and the loser is recorded as an equivalence.
    scored = []
    for key, h, L, tmpl, body, conj, k, sc, tf in tied:
        recipe, info_log = _assemble(x, fs, ys, sps, t0, cfo, theta, rs, beta, P, L, tmpl, h, sc, tf)
        f = recipe.framing
        score = (f.crc is not None) + any(fd.kind == "counter" for fd in f.fields) + recipe.fec.terminated
        scored.append((score, -key[1], recipe, info_log, h, L, conj, k, sc))
    scored.sort(key=lambda t: -t[0])                            # stable: keeps the shortest-marker order
    score, _, recipe, info_log, code, L, conj, k, (sname, sexps, sseed, sbad) = scored[0]
    log.append(Step("frame", f"frame period {P} symbols, sync marker {L} symbols ({recipe.framing.asm_hex})", "blind",
                    {"period": P, "constant_run": run_len, "sync_len": L, "hypotheses_viable": len(viable)}))
    log.append(Step("code", f"conv K={code.K} ({','.join(code.generators_octal)}), block interleaver {code.rows}x{code.cols}"
                    + ("" if code.rows not in (1, code.rows * code.cols) else " (none)"),
                    "blind", {"bias": code.bias, "noise_level": code.noise_level, "runner_up_geometry": code.runner_up}))
    log.append(Step("scrambler", "none" if not sexps else f"{sname}: poly exponents {sexps}, seed 0x{sseed:X}",
                    "blind" if sname.startswith("blind") else "library",
                    {"inconsistent_checks": sbad, "phase_rot_deg": 90 * k, "conj": conj,
                     "equivalent_phase_hypotheses": len(tied), "structure_score": score}))
    log.extend(info_log)
    return recipe, log


def _assemble(x, fs, ys, sps, t0, cfo, theta, rs, beta, P, L, tmpl, code, sc, tf):
    """Build the recipe for one hypothesis: decode under a provisional framing, detect termination,
    then let Bit-Lens find the fields and the CRC."""
    sname, sexps, sseed, _ = sc
    scr = Scrambler(poly_exponents=sexps, seed=sseed) if sexps else None
    asm_hex = np.packbits(_qpsk_bits(tf(tmpl)[None])[0]).tobytes().hex().upper()
    T = P - L                                                      # symbols per coded block = code steps (rate 1/2)
    fec = ConvCode(K=code.K, generators_octal=code.generators_octal, terminated=False)
    base = Recipe(sample_rate_hz=fs, modulation=Modulation(scheme="qpsk", symbol_rate_hz=rs, rolloff=beta), fec=fec,
                  interleaver=Interleaver(rows=code.rows, cols=code.cols), scrambler=scr,
                  framing=Framing(asm_hex=asm_hex, fields=[Field(name="data", bits=T, kind="payload")]))
    pre = (ys, sps, t0, cfo, theta)
    info = unwrap(frontend(x, base, pre=pre), base).info
    term = bool((info[:, -(code.K - 1):] == 0).all(1).mean() >= 0.9)
    if term:
        base = base.model_copy(update={"fec": fec.model_copy(update={"terminated": True}),
                                       "framing": base.framing.model_copy(update={"fields": [Field(name="data", bits=T - code.K + 1, kind="payload")]})})
    fe = frontend(x, base, pre=pre)
    info = unwrap(fe, base).info
    fields, crc = lens_fields(info, (fe.starts - fe.starts[0]) // fe.period)
    recipe = base.model_copy(update={"framing": base.framing.model_copy(update={"fields": fields, "crc": crc})})
    return recipe, [Step("structure", ", ".join(f"{f.name}[{f.bits}]" for f in fields), "blind",
                         {"terminated": term, "crc": None if crc is None else f"width {crc.width} poly 0x{crc.poly:X} init 0x{crc.init:X}"})]


def lens_fields(info: np.ndarray, slots: np.ndarray) -> tuple[list[Field], Crc | None]:
    n = info.shape[1]
    spans = []                                                     # (start, bits, Field)
    cnt = find_counter(info, slots)
    if cnt:
        spans.append((cnt[0], cnt[1], Field(name="counter", bits=cnt[1], kind="counter")))
    cr = find_crc(info)
    crc = None
    if cr:
        pos, w, poly, init = cr
        crc = Crc(width=w, poly=poly, init=init)
        spans.append((pos, w, Field(name="crc", bits=w, kind="crc")))
    used = {i for s, b, _ in spans for i in range(s, s + b)}
    pay_bits = None
    for s, b, v in constant_runs(info, used):
        spans.append((s, b, Field(name=f"const_{s}", bits=b, kind="fill", value=v)))
    spans.sort(key=lambda t: t[0])
    fields, pos = [], 0
    for s, b, f in spans + [(n, 0, None)]:
        if s > pos:
            fields.append(Field(name=f"payload_{pos}", bits=s - pos, kind="payload"))
        if f is not None:
            fields.append(f)
        pos = max(pos, s + b)
    pay_bits = sum(f.bits for f in fields if f.kind == "payload")
    fields = [f.model_copy(update={"kind": "length", "name": "length", "value": None})
              if f.kind == "fill" and f.value == pay_bits // 8 and pay_bits % 8 == 0 else f for f in fields]
    if crc is not None:
        crc_start = sum(f.bits for f in fields[: [f.kind for f in fields].index("crc")])
        if crc_start != cr[0]:
            raise SearchError("internal: CRC position lost while assembling fields")
    return fields, crc
