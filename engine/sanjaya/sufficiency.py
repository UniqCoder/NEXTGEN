"""USP 3a, the Data-Sufficiency Engine v0: every decision of the blind search keeps an evidence ledger entry
(decided or not, the evidence, and what limits it), so a short capture is answered with "record N more
seconds" instead of silence or a guess, and "more data will not help" is said when that is the truth.

Prediction for the coding layer (the decision short captures lose first): frame differences cancel the
scrambler, so the dual-code check bias b is fixed by the code and the channel while the noise level of the
check search shrinks as 1/sqrt(F - 1). Hence z = b / noise grows as sqrt(F - 1) and the frames needed to
reach the acceptance level are 1 + (F - 1) (Z_CODE / z)^2. Verified on Gen truncation runs (z = 10.9 at 5
frames -> 23.6 at 20, predicted 23.7). The bias drifts ~5 % low as frames accumulate, so P90 assumes z 13 %
lower than measured."""
import numpy as np
from .measure import timing_fit
from .dsp import rotate

Z_CODE = 10.0          # the search accepts a code at bias > 10 x the random-check noise level
Z_REAL = 3.0           # below this the best check is indistinguishable from the random maximum (z ~ 1)
P90_Z = 0.87           # pessimistic z factor for P90 (bias drift observed on truncation runs)
RATE_PPM_TARGET = 1.0  # clock-offset precision a Sensor Twin needs


B_WEAK, B_TYPICAL = 0.3, 0.6   # check bias of a weak (low-SNR) and a typical real code; Gen runs: 0.59 at 7 dB, 0.98 at 12 dB
N_PATTERNS = 1 << 18           # window patterns the dual-code search scans (2 x K_MAX bits)


def check_noise(F: int, coded_bits: int) -> float:
    """Expected maximum |bias| of a random check after F frames (the search's noise level)."""
    return float(np.sqrt(2 * np.log(N_PATTERNS) / max(1, (F - 1) * (coded_bits // 2 - 8))))


def power_frames(F: int, coded_bits: int) -> tuple[int, int] | None:
    """When no code was seen: None if the test had the power to see even a weak code (so absence means absence);
    else the (P50, P90) frames at which a typical / weak code would be accepted."""
    noise = check_noise(max(F, 2), coded_bits)
    if B_WEAK / noise >= Z_CODE:
        return None
    need = lambda b: int(np.ceil(1 + max(F - 1, 1) * (Z_CODE * noise / b) ** 2))
    return max(4, need(B_TYPICAL)), max(4, need(B_WEAK))


def frames_needed(F: int, z: float) -> tuple[int, int]:
    """(P50, P90) total frames for the coding layer to accept, from F frames at statistic z."""
    need = lambda zz: int(np.ceil(1 + (F - 1) * (Z_CODE / zz) ** 2))
    return max(3, need(z)), max(3, need(P90_Z * z))


def rate_precision(y: np.ndarray, fs: float, rate: float, rolloff: float = 0.35) -> dict | None:
    """Symbol-rate precision from four independent quarter-file timing fits (whole-file sigma scales as T^-1.5),
    and the recording length that would reach RATE_PPM_TARGET."""
    sps = fs / rate
    q = y.size // 4
    if q / sps < 64:
        return None
    rates = []
    for i in range(4):
        seg = y[i * q: (i + 1) * q]
        try:
            s, _ = timing_fit(seg, sps, rolloff, int(min(512, max(16, q / sps // 8))))
        except Exception:
            return None
        rates.append(fs / s)
    sigma_ppm = float(np.std(rates, ddof=1) / 4 ** 1.5 / rate * 1e6)
    T = y.size / fs
    need = T * (sigma_ppm / RATE_PPM_TARGET) ** (2 / 3) if sigma_ppm > RATE_PPM_TARGET else None
    return {"sigma_ppm": round(max(sigma_ppm, 0.01), 2), "seconds_for_target": None if need is None else round(need, 1),
            "target_ppm": RATE_PPM_TARGET}


class Ledger:
    """Evidence ledger of one search. limit: None (decided), 'data' (more recording helps, with need_s),
    'channel', 'scope' (outside the v1 hypothesis set), 'structure' (no evidence the structure exists), 'signal'."""

    def __init__(self, seconds: float):
        self.have_s = seconds
        self.entries: list[dict] = []

    def add(self, decision: str, status: str, evidence: str, limit: str | None = None, need_s=None, **extra):
        self.entries.append({"decision": decision, "status": status, "evidence": evidence, "limit": limit,
                             "need_s": None if need_s is None else [round(float(v), 2) for v in need_s], **extra})

    def resolve(self, decision: str, evidence: str):
        """A later stage settled an earlier open decision (e.g. the proof confirms the PSK order)."""
        for e in self.entries:
            if e["decision"] == decision and e["status"] != "decided":
                e.update(status="decided", limit=None, evidence=evidence)

    def headline(self) -> tuple[str, str]:
        """(verdict, sentence): verdict in sufficient | more_data | not_data_limited."""
        open_ = [e for e in self.entries if e["status"] != "decided" and e.get("blocking", True)]
        if not open_:
            code = next((e for e in self.entries if e.get("min_s")), None)
            tail = (f"; the coding layer alone would have decided from {code['min_s'][0]:.2f} s (P50) / "
                    f"{code['min_s'][1]:.2f} s (P90)") if code else ""
            return "sufficient", f"Sufficient: every decision made from {self.have_s:.2f} s{tail}."
        data = [e for e in open_ if e["limit"] == "data" and e["need_s"]]
        if data:                                               # more recording is predicted to settle it
            first = max(data, key=lambda e: e["need_s"][0])
            p50, p90 = first["need_s"]
            return "more_data", (f"Too short for the {first['decision'].lower()}: record at least {p50:.2f} s (P50) / "
                                 f"{p90:.2f} s (P90) of this emission; this capture has {self.have_s:.2f} s.")
        first = open_[0]
        why = {"channel": "the channel limits it, not the length", "scope": "the family is outside the v1 hypothesis set",
               "structure": "there is no evidence the structure exists at all", "signal": "no emission to measure",
               "data": "the capture is too short for this stage to run"}.get(first["limit"], "undetermined")
        return "not_data_limited", f"{first['decision']} undecided: {why}. More of the same recording is not predicted to help."

    def to_dict(self) -> dict:
        verdict, sentence = self.headline()
        return {"verdict": verdict, "headline": sentence, "have_s": round(self.have_s, 2), "entries": self.entries}


def phy_entries(led: Ledger, x: np.ndarray, fs: float, phy: dict | None):
    """Ledger entries for the physics stage (emission, rate and its precision, modulation)."""
    if phy is None:
        led.add("Emission", "undecided", "nothing stands 3 dB above the noise floor", "signal")
        return
    led.add("Emission", "decided", f"{phy['snr_db']:.0f} dB in-band SNR, {phy['band_hi_hz'] - phy['band_lo_hz']:.0f} Hz wide")
    if phy["family"] == "FSK":
        led.add("Modulation and rate", "decided", f"{phy['modulation']}, {phy['rate_hz']:.2f} Bd keying, "
                f"{100 * phy['tone_energy']:.0f} % of the energy on the tones")
        return
    ev = f"band-edge line {phy['rate_strength']:.0f}x its neighbourhood (next rate {phy['rate_runner_up']:.0f}x)"
    y = rotate(x, -phy["carrier_hz"] / fs)
    prec = rate_precision(y, fs, phy["rate_hz"]) if phy["order"] else None
    if prec:
        ev += f"; rate known to +-{prec['sigma_ppm']:.2f} ppm (1 sigma)"
        if prec["seconds_for_target"]:
            ev += f", +-{prec['target_ppm']:.0f} ppm needs {prec['seconds_for_target']:.1f} s"
    led.add("Symbol rate", "decided", ev, precision=prec)
    if phy["order"]:
        led.add("Modulation order", "decided", f"{phy['modulation']} by decode-fit (coherence "
                + ", ".join(f"{k} {v:.2f}" for k, v in phy["coherence"].items()) + ")")
    else:
        nsym = x.size / fs * phy["rate_hz"]
        led.add("Modulation order", "undecided", "no PSK order explains the symbols (coherence "
                + ", ".join(f"{k} {v:.2f}" for k, v in phy["coherence"].items()) + ")"
                + ("; smeared constellation" if nsym >= 2000 else f"; only {nsym:.0f} symbols"),
                "channel" if nsym >= 2000 else "data", blocking=False,
                note="not blocking: the search continues under the QPSK hypothesis and the coding layer and proof decide")
