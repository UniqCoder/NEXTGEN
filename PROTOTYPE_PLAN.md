# SANJAYA · Plan to a fully working prototype

SIH 2026 · PS 26147 · NTRO. Companion to `PRD.md` (the build contract). Status as of 27 Sep 2026.

---

## 1. The problem, in the PS's own words

Signals are recorded off the air (HF / VHF / UHF) as `.wav` or `.IQ` by **different sensors at different locations**. Today an analyst works out the signal parameters by hand, and the result is used to set up the **designated sensors**. The PS names four failures of that process:

| # | What the PS says | What it means in practice |
|---|---|---|
| P1 | Data "often insufficient for fine-grain analysis … sampling rate, modulation type, FEC, interleaving" | Short or noisy captures; nobody can say whether the answer is even decidable from them |
| P2 | Recorded "from different sensors and different locations, the parameters may vary" | Every sensor has its own clock error, noise floor and file format; captures cannot simply be combined |
| P3 | "Reduces the accuracy and confidence of interpretation" | A tool can print an answer, but nothing tells the analyst whether it is right |
| P4 | "The resultant data is then utilised for processing signals in the designated sensors" | The analysis ends in a report; someone still has to turn it into a working receiver |

It asks for a GUI tool that takes a recording and (i) identifies sampling frequency, modulation, FEC and interleaving, (ii) demodulates FSK / PSK / QAM, (iii) de-interleaves (block, convolutional, diagonal, pseudo-random), (iv) decodes FEC (convolutional + Viterbi, RS, concatenated, LDPC), and (v) correlates the bit stream to find header and payload.

## 2. How SANJAYA solves it

**Analysis by synthesis, with proof.** SANJAYA recovers the whole transmitter recipe from the recording alone, then **rebuilds the transmission from the decoded bits and subtracts it from the recording**. If what is left is the sensor's own noise, and the bits satisfy the code and the frame structure, the recipe is proven. That result is issued as a signed certificate.

```
Recording ─▶ measure ─▶ hypothesise ─▶ demodulate ─▶ unwrap (scrambler · interleaver · FEC)
                                                          │
            certificate ◀── PROVE: rebuild + subtract ◀── structure (sync · counters · CRC)
                              │  fail: next hypothesis
```

Every other stage proposes; the proof decides. A wrong guess costs time, never correctness.

## 3. Four USPs — where every other approach stops

43 public repositories attempt this PS (README review, `repos.pdf`). The walls they hit, and how SANJAYA gets past each one:

### USP 1 · Proof-of-Decode and a certificate anyone can re-check (answers P3)
- **Wall:** tools print a label and a confidence percentage that nobody can audit.
- **SANJAYA:** a layered proof, one test per layer, each with real power at that layer:
  - PHY: the re-synthesised residual equals the measured noise floor (equivalence test), carries no symbol-rate cyclostationarity, and is white and Gaussian like the reference noise.
  - Coding: the decoded stream satisfies the code's parity checks; the corrections match the channel error rate.
  - Structure: the sync marker recurs, the CRC passes far beyond chance, the counters increment.
- A **near-miss battery** proves that neighbouring recipes are rejected. The neighbours the data cannot separate are listed on the certificate as honest equivalences, not hidden.
- The certificate is Ed25519-signed. `sanjaya verify` re-derives every statistic from the file alone in seconds, without the search — and now also from the UI (Tools > Verify): drop a certificate and its recording, get REPRODUCED or the exact problem (signature invalid, which statistic differs, wrong file).
- **Status: working**, including the classifier (below) and modulation-order ranking shown as evidence on the certified `modulation` parameter, not just QPSK-by-default.

### USP 2 · A truly blind coding layer (answers the PS's core ask, (i) to (v))
- **Wall:** everyone else tries a fixed list (K=7 Viterbi, RS(255,223), one LDPC) and gives up outside it.
- **SANJAYA:** recovers the coding layer **by algebra, from the recording itself**:
  - interleaver geometry and the convolutional code (any K ≤ 9, any generators) from a Walsh–Hadamard dual-code search on frame differences, which cancel the scrambler;
  - the scrambler polynomial and seed, solved in GF(2);
  - the CRC polynomial by polynomial GCD over GF(2), and its init by modular inverse;
  - counters, length and constant fields.
- It also resolves the traps other tools do not model: the 8 phase / conjugation ambiguities, codes whose I/Q-swapped twin is also a valid code, codes blind to inversion, and sync markers sitting next to constant coded symbols.
- A physics-only classifier (`classify.py`, no training) runs before the coding search and identifies family, order and rate on **any** recording, including the 6 real off-air ones: symbol rate from the **band-edge** |x|² line (immune to in-band structure like an idle pattern, which is what made the rate wrong on real STANAG before this), PSK order by decode-fit coherence, FSK by tone regularity + keying rate. It reports "order not separable" rather than guessing when the channel (HF multipath) or the capture length won't support an answer.
- **Status: working** for the QPSK / block-interleaver / convolutional / additive-scrambler / CRC family; the classifier works on every family. Real recordings: STANAG 4285, MIL-188-110A, HFDL, PSK31, SITOR-B and 2G ALE all *identify* correctly (rate, order or tone plan, and consistent named standard with clock ppm); none of the FSK/BPSK/8PSK ones *decode* yet — that needs each real standard's own coding (RS, LDPC, convolutional/diagonal/PN interleavers), deliberately deferred (not a priority per the differentiation-first pivot; see HANDOFF 28 Sep evening).

### USP 3 · "Is this enough data?" and pooling across sensors (answers P1, P2)
- **Wall:** a short capture either fails silently or produces a guess.
- **SANJAYA:**
  - **Data-Sufficiency Engine:** every search stage keeps an evidence ledger (decided / not, why, what would settle it). When a capture is too short, SANJAYA predicts how many more seconds are needed, P50 and P90 — modelled on how the coding-layer statistic grows (∝ √frames), verified against Gen truncations, and confirmed by actually decoding a capture cut to exactly the P90 length. "No code exists, more data won't help" is only said after a power analysis shows the search *could* have seen even a weak code at that length — otherwise it reports the prediction instead of a false negative.
  - **Evidence Stitching + Sensor Twin:** each sensor's capture is measured by its own front-end (its own clock error, tuning offset, gain, noise floor, spectral inversion), aligned on the clearest capture's sync marker, and pooled into one symbol stream — frame slots step negative across capture boundaries so no inter-capture gap is assumed. The recipe found from the pool is then **proven on each capture alone**, which is exactly what catches a capture that turns out to be a different emitter (dropped, pool re-searched).
- **Status: working.** Demo: three ~0.6–0.7 s captures at 6.5–7.5 dB (different ADC rates, ±0–40 ppm clocks, one with an inverted spectrum) — none decodes alone, pooled they decode with every CRC valid, sensor clocks come back correct to within a couple of ppm, and a decoy capture from another emitter is caught and excluded. Sufficiency demo: a 0.66 s / 7 dB capture predicts "record 0.90 s (P50) / 1.06 s (P90)"; a capture that long then decodes.

### USP 4 · Recipe Compiler: output a receiver, not a report (answers P4)
- **Wall:** analysis ends in a PDF; configuring the designated sensor is still manual.
- **SANJAYA:** compiles a **certified** recipe into:
  - a standalone `receiver.py` (NumPy only, no SANJAYA dependency, the recipe embedded) that measures the recording itself, so it decodes a *different* sensor's capture of the same emitter too — different sample rate, clock error, tuning, inverted spectrum and all;
  - a versioned recipe as a SigMF annotation (`recipe.sigmf-meta`);
  - a GNU Radio 3.9+ flowgraph (`.grc`) running the same receiver as an embedded block.
- **Release gate:** the compiled receiver runs as its own process on the source recording and must reproduce SANJAYA's information bits exactly, frame for frame — nothing is packaged if it does not.
- **Status: working.** Verified bit-exact on synthetic files (40/40 frames, 30 480 bits) and portable to a sensor with a different ADC rate, clock offset and an inverted spectrum. Every decoded job compiles and gates automatically; the certificate page has a "Compiled receiver" section and a Receiver (.zip) download, checked end to end in the browser. The `.grc` is generated but not executed here (GNU Radio stays optional per the dependency policy).

## 4. Other innovations, shipped as features

| Feature | What the analyst sees | Status |
|---|---|---|
| Measured symbol clock | Symbol rate to 10⁻⁶, recorder clock error in ppm, any samples-per-symbol | Working |
| Measured constellation | The actual decoded symbols with EVM / MER, not a drawing | Working |
| Bit-Lens | Frame raster that snaps to the frame length; fields labelled; schema export (Kaitai) | Working |
| Honest undecided | "Undecided, because …" with what was measured, instead of a guess | Working (see §6 for partial results) |
| Near-miss battery | Which neighbouring recipes were rejected, by which layer | Working |
| Signal-type triage | Digital / voice / CW / noise before decoding | Phase B |
| Blind modulation classification | BPSK … 64QAM, FSK, MSK; decode-fit expert + cumulants + calibrated confidence sets | Phase B |
| WAV lifting | Real-audio `.wav` from an SSB receiver turned into complex baseband | Phase B |
| Scene | Every emitter in a wideband file; decode-and-cancel reveals weaker ones underneath | Phase C / P2 |
| Signal Genome | "Consistent with STANAG 4285", and the file's true sample rate back-solved from the standard | Phase C |

Deployment note: the engine runs locally beside the UI and needs no network connection, which suits air-gapped sites. It is a property of the design, not a headline feature.

## 5. What "fully working prototype" means

A judge can pick any sample in the UI, or upload their own file. Every PS clause is then demonstrated on it end to end, with honest results:

- Synthetic files covering every PS combination decode and **prove**.
- Real recordings of public HF / VHF modes are **measured, classified and decoded** where the family is built, and **honestly undecided** (with the reason and the measured parameters) where it is not.
- The four USPs are each shown live on at least one sample.

## 6. Build sequence

Weeks from W1 = Mon 28 Sep 2026. Each phase ends with a demo-able build and green tests.

### Phase A · Spine (done, 27 Sep)
- Blind recipe search (QPSK · block interleaver · conv K 3-9 · additive scrambler · CRC frames)
- Layered proof, near-miss battery, signed certificate, independent `verify`
- Engine API; UI wired to real engine results; checked in a browser end to end
- 32 tests

### Phase B · Every modulation, real audio, partial results (W1-W2)
1. **Sample library in the UI:** synthetic recordings of every built recipe plus real public HF recordings, selectable with one click next to upload *(started now)*
2. **Partial results:** an undecided job still shows the real waterfall, spectrum and every measured parameter, and says where decoding stopped and why
3. **WAV lifting v0:** mono audio → analytic complex baseband (real SSB recordings)
4. **Receivers:** BPSK, 8PSK, 16/64QAM (4th-power phase, π/2 resolution), OQPSK, 2/4/8-FSK (tone bank), MSK
5. **Blind modulation classification:**
   - E3 decode-fit likelihood per hypothesis, plus cumulants
   - calibrated confidence and a conformal set in the UI
6. **Triage** (digital / voice / CW / noise) replacing the browser heuristic
- **Acceptance:** each modulation decodes blind on Gen files at ≥ 10 dB; real STANAG 4285 / PSK31 / SITOR-B files show correct family and symbol rate

### Phase C · Coding breadth (W3-W5)
1. Convolutional, diagonal and pseudo-random interleavers (identification + inverse)
2. Rate 1/3 and punctured convolutional codes
3. Reed-Solomon (conventional and CCSDS dual basis, interleave depth 1-8) and concatenated RS ∘ CC
4. Post-FEC scrambler cosets; sync marker inside the coded stream (CCSDS / Meteor-M style)
5. LDPC from a catalogue (DVB-S2 short, CCSDS, 802.11), min-sum decoder
6. Signal Genome v0 (~15 standards) with sample-rate back-solving
- **Acceptance:** PS clauses (iii) and (iv) complete on Gen files; a public Meteor-M LRPT recording decoded blind and matched against SatDump

### Phase D · The remaining USPs (W6-W7)
1. Data-Sufficiency Engine: evidence ledger, predicted extra seconds (P50 / P90), "record this" note in the UI
2. Evidence Stitching across several files of the same emitter; Sensor Twin (clock + noise floor)
3. Recipe Compiler: `.grc` + recipe JSON + detector; bit-exact gate
4. Verify-in-UI: drop a certificate and its file, get "reproduced"
- **Acceptance:** each USP demonstrated on a sample in the library

### Phase E · Hardening (W8-W10)
- C++ kernels (Viterbi, GF(2), LDPC); needs the MSVC C++ workload installed
- Per-job worker process with memory cap and watchdog
- Proof thresholds calibrated on the bench; 2 M near-miss campaign (false-certificate bound)
- Multi-emitter scene detection; bench KPIs published with intervals
- Desktop shell (Tauri) and installer

## 7. Demo samples (engine/samples)

| Sample | Kind | Shows |
|---|---|---|
| QPSK · CC K=7 · block 48×32 · CCSDS scrambler · CRC-16 (12 dB) | Synthetic | Full chain + proof + certificate |
| Same at 7 dB | Synthetic | Proof at low SNR; coding layer carries it |
| QPSK · CC K=5 · block 24×64 · PRBS-9 (−12 ppm clock) | Synthetic | Different code and geometry, clock error measured |
| QPSK · CC K=7 · no interleaver · blind degree-6 scrambler | Synthetic | Scrambler not in any library, solved blind |
| QPSK · CC K=9 · no scrambler · 6.37 samples/symbol | Synthetic | Non-integer oversampling, long code |
| Same recipe, a 0.66 s capture at 7 dB | Synthetic | Data-Sufficiency Engine predicts the recording length needed |
| One emitter, three sensors (+1 decoy) | Synthetic | Evidence Stitching: each too short alone, pooled they decode, decoy caught |
| Pure noise | Synthetic | Honest "undecided", never a fabricated recipe |
| STANAG 4285 idle (8PSK, 2400 Bd, HF) | Real | Identified: rate, order-not-separable (HF multipath), consistent standard |
| MIL-STD-188-110A 2400 bps serial | Real | Identified: real HF PSK |
| HFDL 1200 bps (bursty PSK) | Real | Identified: QPSK, real bursts |
| PSK31 (BPSK, 31.25 Bd) | Real | Identified exactly: BPSK, 31.25 Bd |
| SITOR-B / NAVTEX (FSK, 100 Bd) | Real | Identified exactly: 2-FSK, 100.2 Bd |
| 2G ALE (8-FSK, 125 Bd) | Real | Identified exactly: 8-FSK, 125.0 Bd, matches the MIL-STD-188-141 tone plan |

Real recordings come from the Signal Identification Wiki (sigidwiki.com), with the source URL kept beside each file. All six are identified (family, rate/order or tone plan, consistent named standard) by the physics-only classifier; none decode yet — each real standard's own coding (not the Gen family's conv+block+CRC) is out of scope for now (see HANDOFF, 28 Sep pivot).
