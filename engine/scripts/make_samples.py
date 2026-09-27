"""Build the demo sample library in engine/samples (manifest.json + files).
Synthetic recordings are regenerated from seeds (not committed); real recordings are converted from the
public MP3s in samples/src (Signal Identification Wiki, sigidwiki.com) to 12 kHz mono 16-bit WAV.
Usage: python scripts/make_samples.py"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sanjaya.gen import generate, gen0_recipe                                  # noqa: E402
from sanjaya.io import write_sigmf                                             # noqa: E402
from sanjaya.recipe import ConvCode, Interleaver, Scrambler                    # noqa: E402

OUT = ROOT / "samples"
SRC = OUT / "src"
WIKI = "https://www.sigidwiki.com/wiki/"


def variant(K, gens, rows, cols, scr, sps=8.0):
    r = gen0_recipe(sps=sps)
    fields = r.framing.fields
    fill = rows * cols // 2 - (K - 1) - sum(f.bits for f in fields if f.kind != "fill")
    fields = [f if f.kind != "fill" else f.model_copy(update={"bits": fill}) for f in fields]
    return r.model_copy(update={"fec": ConvCode(K=K, generators_octal=gens), "interleaver": Interleaver(rows=rows, cols=cols),
                                "scrambler": scr, "framing": r.framing.model_copy(update={"fields": fields})})


SYNTH = [
    ("syn-qpsk-k7-48x32-12db", "QPSK · CC K=7 · block 48×32 · CCSDS scrambler · CRC-16 · 12 dB",
     "The full chain, decoded blind and proven.", dict(seed=147, esn0_db=12.0)),
    ("syn-qpsk-k7-48x32-7db", "Same recipe at 7 dB",
     "Low SNR: the PHY tests lose power, the coding layer carries the proof.", dict(seed=148, esn0_db=7.0)),
    ("syn-qpsk-k5-24x64-prbs9", "QPSK · CC K=5 · block 24×64 · PRBS-9 · clock −12 ppm",
     "A different code and interleaver geometry; the recorder's clock error is measured.",
     dict(seed=11, esn0_db=10.0, clock_ppm=-12, recipe=variant(5, ["23", "35"], 24, 64, Scrambler(poly_exponents=[9, 5, 0], seed=0x1AB)))),
    ("syn-qpsk-k7-noil-blindscr", "QPSK · CC K=7 · no interleaver · degree-6 scrambler",
     "The scrambler is in no library; its polynomial and seed are solved blind.",
     dict(seed=11, esn0_db=10.0, clock_ppm=5, recipe=variant(7, ["171", "133"], 1, 1536, Scrambler(poly_exponents=[6, 5, 0], seed=0x2D)))),
    ("syn-qpsk-k9-6p37sps", "QPSK · CC K=9 · no scrambler · 6.37 samples/symbol",
     "Non-integer oversampling and a long code.",
     dict(seed=11, esn0_db=12.0, recipe=variant(9, ["753", "561"], 48, 32, None, sps=6.37))),
]

REAL = [
    ("real-stanag4285-idle", "STANAG4285_IDLE.mp3", "STANAG 4285 · idle (HF, 8PSK, 2400 Bd)", "STANAG_4285",
     "NATO HF serial modem, 1800 Hz carrier in the receiver audio."),
    ("real-mil188-110a-2400", "MIL188-110A_2400S.mp3", "MIL-STD-188-110A · 2400 bps serial (HF, 8PSK)", "MIL-STD-188-110_Serial",
     "US military HF serial-tone modem; a 1.4 s burst."),
    ("real-hfdl-1200", "HFDL-1200bps.mp3", "HFDL · 1200 bps (HF aircraft data link, PSK bursts)", "HFDL",
     "Bursty PSK at 1800 Bd, 1440 Hz carrier."),
    ("real-psk31", "BPSK31a.mp3", "PSK31 (HF amateur, BPSK 31.25 Bd)", "PSK31",
     "A very narrow BPSK signal, about 60 Hz wide."),
    ("real-sitor-b", "SITOR-B.mp3", "SITOR-B / NAVTEX (HF maritime, FSK 100 Bd)", "NAVTEX",
     "Two-tone FSK, 170 Hz shift; first 60 s of the recording."),
    ("real-ale-2g", "2G_ALEaudio.mp3", "2G ALE (HF link establishment, 8-FSK 125 Bd)", "Automatic_Link_Establishment_(ALE)",
     "Eight-tone FSK, MIL-STD-188-141."),
]


def main():
    OUT.mkdir(exist_ok=True)
    items = []
    for sid, name, what, kw in SYNTH:
        x, recipe, truth, _ = generate(**kw)
        data = write_sigmf(OUT / sid, x, recipe.sample_rate_hz, {"sanjaya:generator": truth["generator"]})
        items.append({"id": sid, "name": name, "kind": "synthetic", "file": data.name, "what": what,
                      "truth": {k: truth[k] for k in ("esn0_db", "cfo_hz", "clock_ppm")}, "source": "SANJAYA-Gen (seeded)"})
    rng = np.random.default_rng(0)
    noise = (rng.standard_normal(250_000) + 1j * rng.standard_normal(250_000)).astype(np.complex64) * 0.05
    data = write_sigmf(OUT / "syn-noise-only", noise, 76_800.0, {"sanjaya:generator": "noise"})
    items.append({"id": "syn-noise-only", "name": "Pure noise", "kind": "synthetic", "file": data.name,
                  "what": "Nothing to find: the answer must be 'undecided', never a fabricated recipe.", "source": "SANJAYA-Gen (seeded)"})

    import soundfile as sf                                          # build-time only (MP3 decoding)
    for sid, src, name, page, what in REAL:
        d, fs = sf.read(SRC / src)
        if d.ndim == 2:
            d = d[:, 0]
        d = d[: int(60 * fs)]
        up, down = (40, 147) if fs == 44100 else (1, 2) if fs == 24000 else (1, 1)
        y = resample_poly(d, up, down)
        y = (y / (np.max(np.abs(y)) + 1e-12) * 0.7 * 32767).astype(np.int16)
        out = OUT / f"{sid}.wav"
        wavfile.write(out, 12000, y)
        items.append({"id": sid, "name": name, "kind": "real", "file": out.name, "what": what,
                      "source": WIKI + page, "duration_s": round(len(y) / 12000, 1)})
    (OUT / "manifest.json").write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(items)} samples written to {OUT}")


if __name__ == "__main__":
    main()
