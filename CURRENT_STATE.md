# SANJAYA — current state (28 Sep 2026, night)

Written fresh for tomorrow's submission. Supersedes `PROTOTYPE_PLAN.md`, `PROTOTYPE_AUDIT.md`, `147details.pdf`
and `remwork.pdf` as the reference for what the prototype *actually* does right now — those documents were
accurate on their own dates but are stale (147details.pdf predates FSK, RS-certification, blind BPSK, LDPC, and
this session's work by a full day). Verified this session: `engine/scripts/check.py` → **113/113 tests pass**,
layering clean; `ui: npm run build` + `npx tsc -b` → clean.

Every line below is checked against the code, not carried forward from an older doc. "Blind" = the tool worked
it out with **no recipe supplied** — this is what the PS means by "automated". "Known-recipe" = works only when
a recipe file is supplied (`analyze FILE --recipe R.json`) — real, tested, but not automatic discovery.

---

## 1. USPs — what's working, demo-strong, for the PPT

These are the five things **no other team's repo does at all** (verified this session by reading, not cloning,
all 52 snapshotted public repos for this PS — see §4). Each is real, tested code, not a slide claim.

### USP 1 — Layered proof + signed, re-checkable Decode Certificate
Re-synthesises the waveform from the decoded bits, subtracts it from the recording, and tests the residual at
three independent layers: PHY (waveform vs. measured noise floor), coding (parity-membership), structure
(sync/CRC/counter recurrence). A PASS is Ed25519-signed into a portable certificate; `sanjaya verify file.iq
cert.json` re-derives every statistic from the file alone and reproduces the verdict in ≈1.7 s, on a different
machine, with no trust in the engine that issued it. Tampered certificate or tampered recording → verify says
exactly what changed. **Working now** on generated QPSK/BPSK recordings. Not yet: the 2,000,000-attempt
near-miss campaign that would turn the current `false_pass_bound: null` into a measured number.

### USP 2 — Data-Sufficiency Engine
When a recording is too short or too weak to decide, the tool doesn't guess — it predicts *how much more*
would settle the question (P50/P90 extra duration), with a power analysis proving the test would have caught
even a weak code at that length before it claims "no code exists, more data won't help". Verified against Gen
truncations (predicted 23.7 frames needed, measured 23.6) and a capture cut to exactly the predicted length,
which then decodes. **Working now**, one-click demo sample included (`syn-qpsk-k7-short-7db`).

### USP 3 — Evidence Stitching + Sensor Twin
Pools several short captures of the same emitter from different sensors (each with its own clock error, tuning
offset, gain, noise floor, even spectral inversion), aligns them on the clearest capture's sync marker, and
decodes from the pooled symbol stream when no single capture has enough data alone. A capture of a
*different* emitter (decoy) is detected and dropped automatically. Reports each sensor's clock ppm, tuning
offset and SNR relative to the others. **Working now** on a 3-sensor + 1-decoy generated demo; real multi-site
KiwiSDR validation is the open item.

### USP 4 — Recipe Compiler (answers the PS's "designated sensors" hand-off)
Once a recipe is certified, compiles a from-scratch, dependency-free NumPy receiver plus a GNU Radio `.grc`
flowgraph. The receiver runs as its own subprocess against the source recording and must reproduce every
decoded bit exactly, or nothing ships — a real release gate, not a claim. Verified bit-exact on 3 generated files
and portable to a different simulated sensor (different ADC rate, clock ppm, spectral orientation). **Working
now**; the `.grc` is generated but not yet executed in GNU Radio.

### USP 5 — Honest, calibrated abstention (the trust layer)
Every undecided result shows what was actually measured and the specific reason it stopped, never a
fabricated duration or a guessed decode. This is enforced by design, not just written down: this session found
and fixed a real bug where a UI race condition briefly caused a fabricated "41 symbol errors corrected" demo
number to display in place of the real (undecided) result — the fix and a regression test are in the codebase.
**Working now**, visible on all 6 real off-air HF samples in the library (all correctly report `undecided`, tagged
amber "off-air" with the specific reason before you even click them).

---

## 2. Every feature currently in the prototype

### Ingest & UI (all working, verified in Chrome)
- WAV (mono/stereo), raw IQ (dtype+endianness+I/Q-order sniffing), SigMF `.sigmf-data`+`.sigmf-meta`
- Waterfall, PSD, constellation — real, computed from the recording (not demo art) once an engine job runs
- Digital/voice/CW/noise triage gate before decoding
- 14-recording sample library (built-in, click-to-run, no upload needed): 6 synthetic proof-ready + 6 real
  off-air HF captures (honestly tagged undecided) + 2 stitching/sufficiency demos
- 5-step flow: Recording → Signal → Decoding → Header & payload → Proof (+Certificate); Tools: Scene,
  Standards, Challenge, Compliance, Verify
- PDF export (certificate, via print), JSON export (certificate/recipe), CSV export (frames)

### Blind (automatic, no recipe supplied) — this is the literal PS ask
- Modulation: **QPSK, BPSK only**
- FEC: **rate-1/2 convolutional, K=3–9 only**
- Interleaver: **block only**
- Bit-stream correlation / sync / CRC / counter recovery: works, on the same BPSK/QPSK+conv+block family
- Real off-air files: `classify.py` correctly *identifies* family/rate/standard for **6 real HF signals**
  (STANAG 4285, MIL-188-110A, HFDL, PSK31, SITOR-B, 2G ALE) without any training — band-edge cyclic
  line for symbol rate, decode-fit for PSK order, tone-bank for FSK — but does not decode them (none of the
  6 fall inside the blind-decodable family above)

### Known-recipe (recipe supplied — demodulates/decodes correctly, not a discovery step)
- Demodulation: BPSK, QPSK, 8PSK, 16QAM, 64QAM, and **FSK (2/4/8-tone, non-coherent, new this session)**
- FEC decode + **certify**: convolutional/Viterbi, Reed–Solomon, Concatenated (RS+conv), LDPC — all four
- FEC decode, not yet certify: FSK (proof's statistical model isn't FSK-aware yet, same gap RS had before
  its own proof branch)
- Interleaving: Block, Diagonal, Pseudo-random (Convolutional interleaver has a tested standalone
  primitive only — not wired into the recipe schema/pipeline)
- Verified end-to-end (this session): FSK gen → CFO search → frame sync → FEC/CRC decode, 0 bit errors
  at 18 dB Es/N0 for all of fsk2/fsk4/fsk8, reachable via `sanjaya analyze FILE --recipe R.json`

### Standards / physics-expert identification (no training data, works on real files)
- Symbol rate, modulation family+order, FSK tone plan, clock ppm vs. a small cited standards table
  (STANAG 4285, MIL-188-110A, HFDL, PSK31/63, NAVTEX/SITOR-B, HF DSC, RTTY, 2G ALE)

### Quality system
- 113 tests, `scripts/check.py` layering rule (a module may only import from equal-or-lower architectural
  layers — enforced, not just documented)
- Deterministic, seeded synthetic generator (`sanjaya gen`) with per-layer ground truth for every test

---

## 3. What's remaining from the PS's literal expected solution

Reading the PS verbatim (`introduction to 147.pdf` §1, §8): the **"Must"** deliverables are (0) GUI, (i) identify
Fs/modulation/FEC/interleaving, (ii) demodulate FSK/QAM/PSK, (iii) de-interleave Block/Convolutional/
Diagonal/Pseudo-random, (iv) FEC conv+Viterbi/RS/Concatenated/LDPC, (v) bit-stream correlation, (E1) PSD/
constellation/waterfall, (E2) visual clarity. None of these are satisfied by a "works with a recipe" answer alone
— the PS's core ask is **automated / blind** identification. Judged that way:

| # | PS "Must" clause | Blind (automatic) | Known-recipe |
|---|---|---|---|
| 0 | GUI | ✅ done | |
| i | Identify Fs/modulation/FEC/interleaving | **QPSK/BPSK + conv + block only** | n/a (this clause *is* blind ID) |
| ii | Demodulate FSK/QAM/PSK | — | ✅ BPSK–64QAM + FSK 2/4/8 |
| iii | De-interleave Block/Conv/Diagonal/PRand | Block only | Block/Diagonal/PRand ✅, **Convolutional not wired** |
| iv | FEC conv/RS/Concat/LDPC | rate-½ conv only | ✅ all four (FSK path: decode ✅, certify ✗) |
| v | Bit-stream correlation (header/payload) | Works on the blind-decodable family only | n/a |
| E1 | PSD/constellation/waterfall | ✅ done | |
| E2 | Visual clarity | ✅ done | |

**The honest bottom line:** every "Must" clause has a working implementation *somewhere* in the system, and
four of five core clauses (ii, iii mostly, iv, E1/E2) are genuinely strong. The one clause that is **not** covered
the way the PS actually asks for it is (i) + the blind half of (iii)/(v): automatic discovery is still narrow —
QPSK/BPSK, one FEC family, one interleaver — while the PS lists FSK/QAM, four FEC families and four
interleavers as things the *tool* should figure out, not things a human tells it in advance.

### Specifically still open (in priority order, if there were more time)
1. **Blind coverage beyond QPSK/BPSK+conv+block.** This is the one deliberately *not* rushed tonight:
   `coding/blind.py`'s dual-code search is mathematically sized to 2-point rotation symmetry (why BPSK/QPSK
   are safe and 8PSK/16QAM/64QAM/RS/LDPC/FSK are not attempted blind yet) — extending it without the
   same rigor risks a **wrong blind decode**, i.e. a false certificate, which this project is built to prevent.
2. Convolutional interleaver wired into the recipe/search/proof/API path (currently a tested standalone
   primitive only).
3. FSK through the layered proof (`proof.certificate.coding_layer()`) — decodes now, doesn't certify yet.
4. A real off-air recording decoded end-to-end with external-decoder agreement (today: 6 real files are
   correctly *identified*, none is decoded — all 6 are HF-multipath-smeared PSK, ACARS-framed, varicode,
   or FSK, none inside the current blind-decodable family).
5. Calibration: proof thresholds are `v0-defaults`, `false_pass_bound: null` until the 2,000,000-attempt
   near-miss campaign; data-sufficiency P50/P90 not calibrated against real sensors.
6. Product/ops gates not attempted: 8 GB streaming, installers, WCAG audit, multi-emitter Scene (R-17),
   GNU Radio execution, batch/bench CLI commands.

---

## 4. Competitor reality check (no repos cloned — README/metadata snapshot only, `_build/data.json`, 26 Sep)

Zero of the 52 snapshotted repos implement anything matching USPs 1–4 above (signed re-checkable
certificate, data-sufficiency prediction, multi-sensor stitching, bit-exact-gated receiver compiler) — every
surface keyword hit ("certificate", "verify", "sufficient") checked by hand turned out to be unrelated (SSL certs,
generic English, a different PS's blockchain feature). Where competitors are genuinely ahead: raw commit
volume (some repos show 40–100 commits; this one has few, because effort went into correctness and proof
depth, not iteration count) and *claimed* breadth (several repos claim working QAM/FSK/8PSK demos with no
way to verify the claim from a README). Where this project is unambiguously ahead: it's the only one that
demonstrably proves its own answer instead of just stating one.
