"""L8 layered proof (PRD §4.2 C1): re-synthesise the recording from the decoded bits, then certify each
layer with a test that has power at that layer. PHY: T1-T4 against a measured noise reference.
Coding: K1 parity membership, K2 correction consistency. Structure: S1 sync, S2 CRC, S3 counters, S4 scrambler.
Thresholds are v0 defaults; the G2 calibration on Tiers 1-2 replaces them (calibration_id changes)."""
from dataclasses import dataclass
import numpy as np
from scipy.stats import binom, norm
from ..recipe import Recipe, LayerVerdict, NearMiss
from ..pipeline import FrontEnd, Unwrapped, frontend, unwrap
from ..chain import encode_frames, shape
from ..dsp import rotate
from ..coding import syndrome_rate_half, check_weight
from ..demod import BPS

CALIBRATION_ID = "v0-defaults"
TH = dict(eta_min=0.97, delta_db=0.5, tost_z=1.645, t3_gamma=13.8, t4_sigmas=5.0, t4_floor=0.01,
          kurt_floor=0.05, k1_null_z=8.0, k1_sigmas=6.0, k1_floor=0.002, k2_coverage=0.99, k2_snr_u_db=0.5,
          s1_min_frac=0.9, s2_max_p=1e-9, s3_min_frac=0.9, noise_win=1024, noise_min_windows=4, gain_block=2048,
          ldpc_max_unconverged_frac=0.05)


@dataclass
class Resynthesis:
    region: tuple[int, int]
    xhat: np.ndarray                 # re-synthesised recording over the region
    resid: np.ndarray                # x - xhat over the region
    noise: np.ndarray | None         # reference noise samples (None when no signal-free segment exists)
    sps: float                       # measured samples per symbol (cyclic frequency for T3)


def resynthesise(x: np.ndarray, recipe: Recipe, fe: FrontEnd, uw: Unwrapped) -> Resynthesis:
    fs, sps = recipe.sample_rate_hz, fe.sps
    frames = encode_frames(recipe, uw.info)["symbols"] * np.exp(1j * fe.rot)[:, None]
    n_sym = fe.theta.size
    est = np.zeros(n_sym, np.complex64)
    for s, fr in zip(fe.starts, frames):
        est[s: s + fe.period] = fr
    if fe.conj:
        est = np.conj(est)
    est = fe.amp * est * np.exp(1j * fe.theta)
    clean = shape(est, sps, recipe.modulation.rolloff, x.size, fe.t0)
    xhat = rotate(clean, fe.cfo_hz / fs)
    pad = int(6 * sps)
    a = max(0, int(fe.instants(fe.starts[0])) - pad)
    b = min(x.size, int(fe.instants(fe.starts[-1] + fe.period)) + pad)
    xr, hr = x[a:b], xhat[a:b]
    B = TH["gain_block"]                                           # piecewise complex gain (phase trajectory)
    for i in range(0, hr.size, B):
        s = hr[i: i + B]
        e = float(np.vdot(s, s).real)
        if e > 0:
            hr[i: i + B] = s * (np.vdot(s, xr[i: i + B]) / e)
    W = TH["noise_win"]
    nw = x.size // W
    p = (np.abs(x[: nw * W].reshape(nw, W)) ** 2).mean(1)
    idx = np.arange(nw)
    outside = ((idx + 1) * W <= a) | (idx * W >= b)
    noise = None
    if outside.sum() >= TH["noise_min_windows"]:
        floor = np.percentile(p[outside], 10)
        sel = outside & (p <= floor * 10 ** 0.1)
        if sel.sum() >= TH["noise_min_windows"]:
            noise = x[: nw * W].reshape(nw, W)[sel].ravel()
    return Resynthesis((a, b), hr, (xr - hr).astype(np.complex64), noise, sps)


def _acf(v: np.ndarray, lags: int = 8) -> np.ndarray:
    v = v - v.mean()
    p = np.vdot(v, v).real
    return np.array([abs(np.vdot(v[:-l], v[l:])) / p for l in range(1, lags + 1)])


def _kurt(v: np.ndarray) -> float:
    r = np.concatenate([v.real, v.imag]).astype(np.float64)
    r -= r.mean()
    return float(np.mean(r ** 4) / np.mean(r ** 2) ** 2 - 3)


def _cyclic_stat(v: np.ndarray, alpha_norm: float) -> float:
    z = np.abs(v.astype(np.complex128)) ** 2
    F = np.abs(np.fft.fft(z - z.mean())) ** 2
    k = int(round(alpha_norm * z.size))
    ring = np.r_[F[max(1, k - 200): k - 3], F[k + 4: k + 201]]
    return float(F[k - 1: k + 2].max() / (np.median(ring) / np.log(2)))


def phy_layer(x: np.ndarray, recipe: Recipe, rs: Resynthesis) -> LayerVerdict:
    a, b = rs.region
    r, xr = rs.resid, x[a:b]
    Pr, Px = float(np.mean(np.abs(r) ** 2)), float(np.mean(np.abs(xr) ** 2))
    t3 = _cyclic_stat(r, 1 / rs.sps)
    stats = {"P_resid": Pr, "P_x": Px, "T3_cyclic": t3, "T3_cyclic_recording": _cyclic_stat(xr, 1 / rs.sps),
             "symbol_rate_measured_hz": recipe.sample_rate_hz / rs.sps}
    th = {"eta_min": TH["eta_min"], "delta_db": TH["delta_db"], "t3_gamma": TH["t3_gamma"]}
    fails, nd = [], []
    if not t3 < TH["t3_gamma"]:
        fails.append("T3 residual is cyclostationary at the symbol rate")
    if rs.noise is None:
        nd.append("no independent noise reference: T1, T2 not determinable; T4 vs ideal")
        rho_n, k_n, Nn = np.zeros(8), 0.0, np.inf
    else:
        n = rs.noise
        Pn, Nn = float(np.mean(np.abs(n) ** 2)), n.size
        rho_n, k_n = _acf(n), _kurt(n)
        eta = 1 - (Pr - Pn) / (Px - Pn)
        L = 10 * np.log10(Pr / Pn)
        neff = 1 + 2 * float((rho_n ** 2).sum())
        se = 10 / np.log(10) * np.sqrt(neff / r.size + neff / Nn)
        lo, hi = L - TH["tost_z"] * se, L + TH["tost_z"] * se
        stats.update(P_noise=Pn, T1_eta=eta, T2_resid_to_noise_db=L, T2_ci90_lo_db=lo, T2_ci90_hi_db=hi, N_noise=float(Nn))
        if eta < TH["eta_min"]:
            fails.append("T1 explained energy below threshold")
        if not (lo > -TH["delta_db"] and hi < TH["delta_db"]):
            fails.append("T2 residual not equivalent to the noise floor")
    d_acf = float(np.max(np.abs(_acf(r) - rho_n)))
    d_kurt = abs(_kurt(r) - k_n)
    lim_acf = TH["t4_sigmas"] * np.sqrt(1 / r.size + 1 / Nn) + TH["t4_floor"]
    lim_k = TH["t4_sigmas"] * np.sqrt(24 / r.size + 24 / Nn) + TH["kurt_floor"]
    stats.update(T4_acf_diff=d_acf, T4_kurt_diff=d_kurt)
    th.update(T4_acf_limit=float(lim_acf), T4_kurt_limit=float(lim_k))
    if d_acf > lim_acf or d_kurt > lim_k:
        fails.append("T4 residual not white/Gaussian like the reference noise")
    verdict = "fail" if fails else "pass"
    return LayerVerdict(layer="phy", verdict=verdict, reason="; ".join(fails + nd) or None, stats=stats,
                        thresholds=th, calibration_id=CALIBRATION_ID)


def _coding_layer_rs(recipe: Recipe, fe: FrontEnd, uw: Unwrapped) -> LayerVerdict:
    """RS analogue of K1/K2: RS1 checks the uncorrectable-frame rate against the channel's implied symbol
    error rate (a wrong n/k/m or generator gives far more, or far fewer, uncorrectable frames than the
    channel explains); RS2 is the same corrections-consistency check as conv's K2, reused verbatim."""
    fec = recipe.fec
    esn0 = 10 ** (fe.esn0_db / 10)
    p = float(norm.sf(np.sqrt(2 * esn0 / BPS[recipe.modulation.scheme])))     # per-bit hard-decision error probability
    p_sym = 1 - (1 - p) ** fec.m
    t = (fec.n - fec.k) // 2
    F = uw.fec_ok.size
    p_bad = float(binom.sf(t, fec.n, p_sym))
    n_bad = int((~uw.fec_ok).sum())
    q = (1 - TH["k2_coverage"]) / 2
    pb = min(max(p_bad, 1e-12), 1 - 1e-12)
    bad_lo, bad_hi = float(binom.ppf(q, F, pb)), float(binom.ppf(1 - q, F, pb))
    nc, nb = int((uw.hard != uw.reencoded).sum()), uw.hard.size
    u = TH["k2_snr_u_db"]
    bps = BPS[recipe.modulation.scheme]
    p_lo = norm.sf(np.sqrt(2 * esn0 * 10 ** (u / 10) / bps))
    p_hi = norm.sf(np.sqrt(2 * esn0 * 10 ** (-u / 10) / bps))
    c_lo, c_hi = float(binom.ppf(q, nb, p_lo)), float(binom.ppf(1 - q, nb, p_hi))
    fails = []
    if not (bad_lo <= n_bad <= bad_hi):
        fails.append("RS1 uncorrectable-frame rate inconsistent with the channel's symbol error rate")
    if not c_lo <= nc <= c_hi:
        fails.append("RS2 decoder corrections inconsistent with the channel error rate")
    return LayerVerdict(layer="coding", verdict="fail" if fails else "pass", reason="; ".join(fails) or None,
                        stats={"RS1_uncorrectable": float(n_bad), "RS1_expected_p": p_bad, "RS1_frames": float(F),
                               "pre_fec_ber_hat": p, "RS2_corrections": float(nc), "RS2_lo": c_lo, "RS2_hi": c_hi},
                        thresholds={"RS1_lo": bad_lo, "RS1_hi": bad_hi, "K2_coverage": TH["k2_coverage"]},
                        calibration_id=CALIBRATION_ID)


def _coding_layer_ldpc(recipe: Recipe, fe: FrontEnd, uw: Unwrapped) -> LayerVerdict:
    """LDPC analogue: LDPC1 is K2's corrections-consistency check (hard vs reencoded bits, channel-BER based -
    code-family-agnostic); LDPC2 is a coarse, uncalibrated cap on the fraction of frames whose min-sum BP
    never converged to a valid codeword (belief propagation has no simple closed-form 'corrects up to t errors'
    guarantee the way RS/conv do, so this is a first-cut gate, not a calibrated statistical test)."""
    esn0 = 10 ** (fe.esn0_db / 10)
    bps = BPS[recipe.modulation.scheme]
    nc, nb = int((uw.hard != uw.reencoded).sum()), uw.hard.size
    u = TH["k2_snr_u_db"]
    p_lo = norm.sf(np.sqrt(2 * esn0 * 10 ** (u / 10) / bps))
    p_hi = norm.sf(np.sqrt(2 * esn0 * 10 ** (-u / 10) / bps))
    q = (1 - TH["k2_coverage"]) / 2
    c_lo, c_hi = float(binom.ppf(q, nb, p_lo)), float(binom.ppf(1 - q, nb, p_hi))
    F = uw.fec_ok.size
    n_bad = int((~uw.fec_ok).sum())
    fails = []
    if not c_lo <= nc <= c_hi:
        fails.append("LDPC1 decoder corrections inconsistent with the channel error rate")
    if n_bad / F > TH["ldpc_max_unconverged_frac"]:
        fails.append("LDPC2 too many frames failed to converge to a valid codeword")
    return LayerVerdict(layer="coding", verdict="fail" if fails else "pass", reason="; ".join(fails) or None,
                        stats={"LDPC1_corrections": float(nc), "LDPC1_lo": c_lo, "LDPC1_hi": c_hi,
                               "LDPC2_unconverged": float(n_bad), "LDPC2_frames": float(F)},
                        thresholds={"K2_coverage": TH["k2_coverage"], "LDPC2_max_frac": TH["ldpc_max_unconverged_frac"]},
                        calibration_id=CALIBRATION_ID)


def coding_layer(recipe: Recipe, fe: FrontEnd, uw: Unwrapped) -> LayerVerdict:
    fec = recipe.fec
    if fec.family == "rs":
        return _coding_layer_rs(recipe, fe, uw)
    if fec.family == "ldpc":
        return _coding_layer_ldpc(recipe, fe, uw)
    # concat: K1/K2 test the inner conv code (the code that actually shaped uw.hard/uw.reencoded); the outer
    # RS layer's own correctness shows up in uw.fec_ok / the CRC, not in a second statistical test here.
    inner = fec.inner if fec.family == "concat" else fec
    gens = tuple(inner.generators_octal)
    s = syndrome_rate_half(uw.hard, inner.K, gens)
    N, f = s.size, float(s.mean())
    w = check_weight(inner.K, gens)
    esn0 = 10 ** (fe.esn0_db / 10)
    # exact Gray-bit error probability for BPSK/QPSK (Q(sqrt(2 Eb/N0)), Eb/N0 = Es/N0 / bits-per-symbol); the
    # same formula is used as an approximation for 8PSK/16QAM/64QAM (not exact there - narrower scope than the
    # rest of the proof, unchanged from before this was made scheme-aware)
    p = float(norm.sf(np.sqrt(2 * esn0 / BPS[recipe.modulation.scheme])))
    f0 = (1 - (1 - 2 * p) ** w) / 2
    z_null = (0.5 - f) / np.sqrt(0.25 * w / N)
    lim = f0 + TH["k1_sigmas"] * np.sqrt(max(f0, 1 / N) * (1 - f0) * w / N) + TH["k1_floor"]
    nc, nb = int((uw.hard != uw.reencoded).sum()), uw.hard.size
    u = TH["k2_snr_u_db"]
    bps = BPS[recipe.modulation.scheme]
    p_lo = norm.sf(np.sqrt(2 * esn0 * 10 ** (u / 10) / bps))
    p_hi = norm.sf(np.sqrt(2 * esn0 * 10 ** (-u / 10) / bps))
    q = (1 - TH["k2_coverage"]) / 2
    c_lo, c_hi = float(binom.ppf(q, nb, p_lo)), float(binom.ppf(1 - q, nb, p_hi))
    fails = []
    if z_null < TH["k1_null_z"]:
        fails.append("K1 parity checks not distinguishable from random bits")
    elif f > lim:
        fails.append("K1 unsatisfied checks exceed what the channel explains")
    if not c_lo <= nc <= c_hi:
        fails.append("K2 decoder corrections inconsistent with the channel error rate")
    return LayerVerdict(layer="coding", verdict="fail" if fails else "pass", reason="; ".join(fails) or None,
                        stats={"K1_unsat_frac": f, "K1_expected_f0": f0, "K1_null_z": float(z_null), "K1_checks": float(N),
                               "pre_fec_ber_hat": p, "K2_corrections": float(nc), "K2_lo": c_lo, "K2_hi": c_hi},
                        thresholds={"K1_null_z": TH["k1_null_z"], "K1_limit": float(lim), "K2_coverage": TH["k2_coverage"]},
                        calibration_id=CALIBRATION_ID)


def structure_layer(recipe: Recipe, fe: FrontEnd, uw: Unwrapped) -> LayerVerdict:
    slots = (fe.starts - fe.starts[0]) // fe.period
    n_slots = int(slots[-1]) + 1
    s1 = len(fe.starts) / n_slots
    F, n_ok = len(uw.crc_ok), int(uw.crc_ok.sum())
    stats = {"S1_frames": float(F), "S1_slot_frac": s1}
    fails, nd = [], []
    if len(fe.starts) < 3 or s1 < TH["s1_min_frac"]:
        fails.append("S1 sync marker does not recur at the frame period")
    p_s2 = 1.0
    if recipe.framing.crc is None:
        nd.append("S2 no CRC field; S4 scrambler reported as an equivalence class")
    else:
        w = recipe.framing.crc.width
        p_s2 = float(binom.sf(n_ok - 1, F, 2.0 ** -w)) if n_ok else 1.0
        stats.update(S2_crc_pass=float(n_ok), S2_crc_frac=n_ok / F, S2_chance_p=p_s2)
        if p_s2 > TH["s2_max_p"]:
            fails.append("S2 CRC passes are at chance level")
    ctr = next((f for f in recipe.framing.fields if f.kind == "counter"), None)
    if ctr is None:
        nd.append("S3 no counter field")
    else:
        good = [(sl, fd[ctr.name]) for sl, fd, ok in zip(slots, uw.fields, uw.crc_ok) if ok]
        pairs = [((c2 - c1) % (1 << ctr.bits)) == (s2 - s1_) % (1 << ctr.bits) for (s1_, c1), (s2, c2) in zip(good, good[1:])]
        if len(pairs) < 2:
            nd.append("S3 too few CRC-valid frames for counters")
        else:
            stats["S3_counter_frac"] = float(np.mean(pairs))
            if stats["S3_counter_frac"] < TH["s3_min_frac"]:
                fails.append("S3 counters do not increment")
    stats["S4_scrambler_certified"] = float(not fails and p_s2 <= TH["s2_max_p"])
    return LayerVerdict(layer="structure", verdict="fail" if fails else "not_determinable" if nd else "pass", reason="; ".join(fails + nd) or None,
                        stats=stats, thresholds={"S1_min_frac": TH["s1_min_frac"], "S2_max_p": TH["s2_max_p"], "S3_min_frac": TH["s3_min_frac"]},
                        calibration_id=CALIBRATION_ID)


def prove(x: np.ndarray, recipe: Recipe, fe: FrontEnd | None = None, uw: Unwrapped | None = None) -> list[LayerVerdict]:
    """Decode (if not given) and certify all three layers under `recipe`."""
    try:
        fe = fe or frontend(x, recipe)
    except RuntimeError as e:
        return [LayerVerdict(layer="phy", verdict="fail", reason=str(e), stats={}, thresholds={}, calibration_id=CALIBRATION_ID)]
    uw = uw or unwrap(fe, recipe)
    rs = resynthesise(x, recipe, fe, uw)
    return [phy_layer(x, recipe, rs), coding_layer(recipe, fe, uw), structure_layer(recipe, fe, uw)]


def near_miss_battery(x: np.ndarray, recipe: Recipe, fe: FrontEnd) -> list[NearMiss]:
    """PRD §9.3, v0 subset: each neighbour of the certified recipe must be rejected by some layer,
    or it is reported as an equivalence the data cannot separate."""
    m = recipe.model_copy(deep=True)
    fec, il, sc, cr, mo = m.fec, m.interleaver, m.scrambler, m.framing.crc, m.modulation
    cands = [
        ("phy", f"roll-off {mo.rolloff + 0.1:.2f}", {"modulation": mo.model_copy(update={"rolloff": round(mo.rolloff + 0.1, 3)})}),
        ("phy", f"roll-off {max(0.05, mo.rolloff - 0.1):.2f}", {"modulation": mo.model_copy(update={"rolloff": round(max(0.05, mo.rolloff - 0.1), 3)})}),
        ("coding", f"interleaver transposed {il.cols}x{il.rows}", {"interleaver": il.model_copy(update={"rows": il.cols, "cols": il.rows})}),
    ]
    if fec.family in ("conv", "concat"):
        target = fec.inner if fec.family == "concat" else fec
        g = target.generators_octal
        swapped = target.model_copy(update={"generators_octal": g[::-1]})
        neighbour = target.model_copy(update={"generators_octal": ["171", "135"] if g != ["171", "135"] else ["171", "133"]})
        wrap = (lambda t: {"fec": fec.model_copy(update={"inner": t})}) if fec.family == "concat" else (lambda t: {"fec": t})
        cands += [
            ("coding", "generators swapped", wrap(swapped)),
            ("coding", "generator neighbour (171,135)" if g != ["171", "135"] else "generator neighbour (171,133)", wrap(neighbour)),
        ]
    # RS-specific near-misses (wrong n/k/m) change coded_len and info_bits together, needing a framing rebuild
    # to stay geometry-consistent -- left for the RS calibration pass rather than risked here (applies to concat's
    # outer code too).
    if sc is not None:
        cands.append(("structure", "scrambler seed shifted", {"scrambler": sc.model_copy(update={"seed": sc.seed ^ 1})}))
    if cr is not None:
        cands.append(("structure", "CRC init variant", {"framing": m.framing.model_copy(update={"crc": cr.model_copy(update={"init": cr.init ^ ((1 << cr.width) - 1)})})}))
    out = []
    for layer, name, upd in cands:
        r2 = recipe.model_copy(update=upd)
        fe2 = fe if layer != "phy" else None
        verdicts = prove(x, r2, fe2)
        failed = [v.layer for v in verdicts if v.verdict == "fail"]
        out.append(NearMiss(name=name, layer=layer, rejected=bool(failed), failed=failed))
    return out
