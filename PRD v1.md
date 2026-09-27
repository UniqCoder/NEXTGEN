# PRD: Project SANJAYA

**Automated analysis of .IQ and .wav recordings with signal parameter extraction, proven end to end**

| | |
|---|---|
| Problem statement | SIH 2026 PS 26147 · Sponsor NTRO · Theme Space Technology · Category Software |
| Document | Product Requirements Document v1.0, 27 Sep 2026 |
| Governing plan | `winning plan 147 v3.pdf` (review-ready). Where this PRD and v3 disagree, v3 wins unless this PRD marks the change as **[PRD refinement]** |
| Status | UI built (React + three.js, demo data). Engine not started. This PRD is the build contract for the engine and for wiring it to the UI |
| Conventions | SNR = E<sub>s</sub>/N<sub>0</sub> in the occupied bandwidth. KPIs are pre-registered **targets**, not results. pw = person-week (40 h). Competitor statements are README claims (snapshot 26 Sep 2026) |

---

## Contents

1. [Product in one page](#1-product-in-one-page)
2. [The problem, the users, the jobs](#2-the-problem-the-users-the-jobs)
3. [Goals, non-goals, success metrics](#3-goals-non-goals-success-metrics)
4. [USPs: why SANJAYA wins](#4-usps-why-sanjaya-wins)
5. [Functional requirements (R-01 to R-15)](#5-functional-requirements-r-01-to-r-15)
6. [System architecture](#6-system-architecture)
7. [The intelligence: ML and inference design](#7-the-intelligence-ml-and-inference-design)
8. [Beating the data problem](#8-beating-the-data-problem)
9. [Accuracy engineering](#9-accuracy-engineering)
10. [UI integration contract (UI design is frozen)](#10-ui-integration-contract-ui-design-is-frozen)
11. [Implementation plan in phases](#11-implementation-plan-in-phases)
12. [Verification, assurance, risks, demo](#12-verification-assurance-risks-demo)
13. [Repository layout and engineering rules](#13-repository-layout-and-engineering-rules)
14. [Open items](#14-open-items)

---

## 1. Product in one page

**Mission.** Turn any recording from any NTRO sensor into a **proven** transmitter recipe (sampling frequency, modulation, interleaving, FEC, scrambling, frame structure, header and payload), automatically and offline. Say what the data can and cannot support, and hand the recipe back to designated sensors as something they can run.

**Thesis: analysis by synthesis, with proof.** Every other team stops once it has produced an answer. SANJAYA goes one step further and checks the answer:

1. Decode the recording to bits.
2. Re-encode those bits through the recovered chain and rebuild the waveform with the measured channel.
3. Subtract the rebuilt waveform from the recording.
4. Test what is left. If it passes four calibrated tests (the signal energy is explained, the residual sits at the noise floor, no cyclostationary line remains at the symbol rate, and the residual is white), SANJAYA issues a signed **Decode Certificate**.

If the test fails, the recipe is wrong, and the engine goes back and tries the next-best hypothesis. The proof is therefore both the product's selling point and the mechanism that makes its answers accurate (§9).

**The loop (the product's spine, already shown in the UI).**

```
1 OBSERVE → 2 MEASURE → 3 HYPOTHESISE → 4 DEMODULATE → 5 UNWRAP → 6 STRUCTURE → 7 PROVE → 8 LEARN
                              ▲                                                    │
                              └────────── proof FAIL: next-best hypothesis ────────┘
PASS → subtract the proven emitter → re-scan the scene for weaker hidden signals
```

**What ships at the finale, whatever happens (minimum winning configuration, P1).**
- 100 % of the PS: R-01 to R-15, on the bench and on real signals with independent truth.
- C1 Proof-of-Decode, C2 Data-Sufficiency, C3 Evidence Stitching with C4-lite Sensor Twin, C5 Recipe Compiler, and R-15 signal-type triage.
- One real signal decoded end to end with independent confirmation (Meteor-M N2-4 LRPT vs SatDump), plus real multi-site stitching (KiwiSDR).

---

## 2. The problem, the users, the jobs

### 2.1 PS text (verbatim, the acceptance baseline)

> The GUI based model will take .IQ or .wav file as input and: (i) identify signal parameters (Sampling frequency, Modulation, FEC, Interleaving); (ii) demodulate signals (FSK, QAM, PSK); (iii) de-interleave (Block, Convolution, Diagonal, Pseudo Random); (iv) FEC (short-constraint convolutional codes with Viterbi decoding, RS block codes, Concatenated codes, LDPC); (v) bit stream correlation.
>
> **Expected solution:** The expected system should improve feature visibility of signals with the help of GUI, enable automated signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall (time-frequency domain), demodulate signals, carry out de-interleaving and error correction. The output can then be used to carry out correlation of bit stream for identification of header and payload.

The PS background also contains the three complaints that the crown innovations answer:

| PS sentence (paraphrased) | Answered by |
|---|---|
| Recorded data "is often insufficient for fine grain analysis" | C2 Data-Sufficiency, C3 Stitching, D1 soft methods |
| Data points come "from different sensors and different locations, the parameters may vary" | C3 Stitching, C4 Sensor Twin |
| Limitation "reduces the accuracy and confidence of interpretation" | C1 Proof-of-Decode, D7 trust layer |
| Output "utilised for processing signals in the designated sensors" | C5 Recipe Compiler |

### 2.2 Users

| User | Context | What they need |
|---|---|---|
| **Signal analyst** (primary) | Air-gapped workstation, expert, handles files from many sensors | Speed, density, evidence behind every number, override any stage, never a silent guess |
| **Collection manager** | Decides what to record next | "Is this enough data? If not, what should we record, where, and for how long?" (C2 tasking note) |
| **Sensor engineer** | Runs designated receivers | A receiver or recipe file that runs on their equipment (C5) |
| **SIH judge** | Holds the PS text, has minutes | Every PS clause visible, in the PS's own words, within 2 clicks (UI Compliance view) |

### 2.3 Jobs to be done

1. *"Tell me everything about this unknown recording, and show me why you believe it."*
2. *"Tell me when you can't know, and what it would take to know."*
3. *"I have five short captures from three sites. Combine them."*
4. *"Give my sensor a receiver for this signal."*

---

## 3. Goals, non-goals, success metrics

### 3.1 Goals

| ID | Goal | Measured by |
|---|---|---|
| G-1 | Cover 100 % of the PS clauses with verified acceptance criteria | R-01 to R-15 pass (§5) |
| G-2 | Be right, or say you're unsure; never be confidently wrong | False-PASS bound, calibration, conformal coverage (§9) |
| G-3 | Work on real recordings, not only on our own generator | Tier 3 results with independent truth (§8) |
| G-4 | Answer the PS's three complaints with capabilities no competitor claims | C1 to C5 at P1 (§4) |
| G-5 | Keep the existing UI and its design exactly as it is, driven by real engine data | UI contract (§10) |
| G-6 | Deployable in an intelligence setting | Offline, zero-network proof, fuzzed parsers, SBOM (§12) |

### 3.2 Non-goals (by design)

Payload decryption · LLM chat interfaces · cloud, login or telemetry · black-box-only deep learning · speech content or speaker ID · OFDM (unless the SPOC asks; P2 at 1.5 pw) · live SDR control as a requirement (supported as a bonus through C5).

### 3.3 Headline KPIs (pre-registered targets, from v3)

| Area | KPI | Target |
|---|---|---|
| Proof (C1) | P(PASS \| wrong recipe) | ≤ 10<sup>−4</sup> (95 % upper bound: 0 false PASS in ≥ 30,000 near-miss trials) |
| Proof (C1) | P(PASS \| right recipe) | ≥ 95 % at SNR ≥ 6 dB with ≥ 10<sup>4</sup> symbols |
| Modulation (R-04) | Top-1 accuracy over 11 classes | ≥ 98 % at SNR ≥ 10 dB, ≥ 1,000 symbols; conformal set coverage 0.95 ± 0.01 (n ≥ 2,000) |
| Symbol rate (R-03) | Relative error | ≤ 10<sup>−4</sup> (≥ 1,000 symbols, SNR ≥ 10 dB) |
| Sampling frequency (R-02) | Error on standard-anchored captures ≥ 10 s | ≤ 10 ppm |
| FEC / interleaver (R-05, R-06) | P<sub>id</sub> | ≥ 95 % at BER ≤ 10<sup>−3</sup> within stated data lengths; curves to BER 10<sup>−2</sup> |
| Decoders (R-09) | Distance from reference implementations | ≤ 0.2 dB at FER 10<sup>−3</sup> |
| Frames (R-10) | Frame length + sync | 100 % on files with ≥ 20 frames at BER ≤ 10<sup>−3</sup>; field class ≥ 95 % |
| Triage (R-15) | Content class | ≥ 95 % on 400 labelled files; < 1 s per file |
| Data-sufficiency (C2) | Prediction error of extra duration needed | median ≤ 30 %, P90 ≤ 60 % |
| Stitching (C3) | Alignment loss vs one capture of equal total length | ≤ 10 %; false merge ≤ 1 % |
| Compiler (C5) | Compiled receiver on source recording | 100 % bit-exact; live FER within 1 dB |
| Performance (R-11, R-12) | Interactivity / full chain | 100 MB file interactive < 2 s; full chain < 10 s for 10<sup>6</sup> samples |

---

## 4. USPs: why SANJAYA wins

### 4.1 Where the field stops

Our survey of 43 public competitor repositories (README claims, 26 Sep 2026) found that every one of them hits at least one of these ten walls:

| # | Wall | SANJAYA's answer |
|---|---|---|
| 1 | One file at a time | C3 Evidence Stitching |
| 2 | One sensor at a time | C4 Sensor Twin + network clock solution |
| 3 | No answer to "is this enough data?" | C2 Data-Sufficiency Engine |
| 4 | Output ends in a report | C5 Recipe Compiler |
| 5 | Truth comes from their own generator (33 of 43) | Tier 2-3 real-data engine (§8) |
| 6 | Coding layer limited to a catalogue | D1 soft joint coding engine |
| 7 | Scramblers not identified | D2 blind scrambler recovery |
| 8 | .wav treated only as stereo IQ or Hilbert of mono | C7 WAV-Lifting |
| 9 | Bit-level verification at best | C1 waveform-level proof |
| 10 | Models never improve in use | C8 proof-gated flywheel |

**Why the gap lasts.** The innovations depend on each other. The flywheel needs the proof; stitching needs the Twin and the data-sufficiency maths; the passport needs Bit-Lens counters and the clock network; the compiler needs certified recipes. A competitor who copies one idea from a slide deck does not get the system.

### 4.2 Crown innovations (claimed by none of the 43 READMEs)

Each card gives the PS hook, what the feature does for the user, how it is built, **how it stays accurate**, its honest limits, and its priority class. P1 = ships at the finale regardless; P2 = built from the reserve after gate G3; P3 = bench prototype and roadmap.

#### C1 · Proof-of-Decode and the Decode Certificate · P1 · TRL 2→5 · 1.5 pw
- **PS hook:** "reduces the accuracy and confidence of interpretation".
- **User value:** A PASS means the recipe explains the recording down to the noise floor. The analyst can defend the result.
- **Build:** Re-encode the decoded bits (code → interleaver → scrambler → mapper → pulse shape). Apply the estimated channel (gain, CFO, phase trajectory, timing, equaliser taps), subtract, and test the residual r:
  - **T1 explained energy.** η = 1 − (P<sub>r</sub> − P<sub>n</sub>)/(P<sub>x</sub> − P<sub>n</sub>) ≥ η<sub>min</sub>. The noise power P<sub>n</sub> comes from the Sensor Twin (C4).
  - **T2 residual-to-noise.** ρ = P<sub>r</sub>/P<sub>n</sub> within ±0.2 dB.
  - **T3 no cyclostationarity.** Cyclic coherence at α = 1/T below threshold.
  - **T4 whiteness and Gaussianity.** Ljung-Box on the pre-whitened residual, plus kurtosis.
  - **Corroboration.** CRC pass rate and syndrome weight are recorded as independent bit-level evidence.
- **Certificate contents:** SHA-256 of the input, version and configuration hash, the full recipe, every statistic and threshold, and the **near-miss alternatives** that were tested (for example 8PSK instead of QPSK, a wrong roll-off, a wrong interleaver period), each marked rejected or not rejected. It is signed with Ed25519 using an offline per-site key and is deterministic: the same version, file and configuration always give the same recipe.
- **Accuracy mechanism:** Thresholds are calibrated on Tiers 1-2 and the false-PASS rate is measured on ≥ 30,000 deliberately wrong near-miss recipes.
- **Honest limits:** Recipes that produce identical waveforms (for example a scrambler folded into a random payload) cannot be told apart by the proof. Frame structure and CRC can separate them, and the certificate reports the equivalence. At low SNR, near-miss rejection weakens; the certificate lists the alternatives it could not rule out.
- **KPI:** see §3.3.

#### C2 · Data-Sufficiency Engine and collection tasking · P1 · TRL 2→4 · 1.0 pw
- **PS hook:** "data is often insufficient for fine grain analysis".
- **User value:** Instead of a bare "UNKNOWN", the analyst gets a number: *"record about 2.3 more minutes at ≥ 12 dB SNR on sensor B"*, delivered as a tasking note.
- **Build:** Each open decision is a set of hypotheses scored by log-evidence from calibrated likelihoods. The engine decides when the best posterior ≥ 1 − α (α = 10<sup>−3</sup>). Otherwise it measures the evidence growth rate D (nats per second of signal) and predicts the extra duration needed, ΔT ≈ [ln((1 − α)/α) − ln B] / D (Wald's approximation). The tasking note gives centre frequency, occupied bandwidth, minimum complex sample rate (≥ 1.25 × bandwidth), duration (ΔT × 1.3), minimum SNR, and the best sensor according to the Twin.
- **Why it matters (derived):** Hard-decision rank methods need ≈ 2N/(1 − p)<sup>N</sup> error-free rows for an interleaver period of N bits at bit error rate p. At p = 3 × 10<sup>−3</sup> and 4.8 kbit/s:
  - N = 96 needs **256 rows, 24.6 kbit, about 5.1 s** of signal.
  - N = 1,500 needs **2.7 × 10<sup>5</sup> rows, 4.1 × 10<sup>8</sup> bits, about 23.6 hours** of signal.

  This is why "insufficient data" is a real problem, and why the soft methods (D1) and stitching (C3) matter.
- **Honest limits:** Predictions assume the emitter stays in one mode. A mode change shows up as a collapsing evidence rate and is flagged, not extrapolated.

#### C3 · Evidence Stitching across captures, sensors and locations · P1 · TRL 2→5 · 1.5 pw
- **PS hook:** "recorded from different sensors and different locations".
- **Build:** A five-step process:
  1. **Associate** captures to one emitter only when their recipes agree and their passport distance is below threshold.
  2. **Normalise** each capture with its sensor's Twin (resample to a common symbol grid, remove CFO, match gain).
  3. **Align** exactly on a sync word, or search the phase per capture over the candidate period.
  4. **Pool.** A code's dual space is the same in every capture, so aligned soft rows stack and log-likelihoods add.
  5. **Safety.** C1 runs on each capture separately; a wrongly associated capture fails its own proof and is ejected.
- **Real validation:** One HF transmission recorded at the same time by ≥ 3 public KiwiSDRs in different countries, with GPS-timestamped IQ. This is literally the PS's scenario.
- **Honest limits:** Without a sync marker, the phase search grows with the period. Captures in different emitter modes are never pooled.

#### C4 · Sensor Twin and network clock solution · P1-lite / P2-full · 0.5 + 0.5 pw
- **Build:** A persistent per-sensor model: sample-clock error, LO error, anti-alias response, noise-floor shape, IQ imbalance, DC, clipping level, phase noise. The Twin is learned passively from signals the sensor already hears: atomic-referenced broadcasts, recognised standards (exact symbol clocks), empty bands and strong carriers.
- **Network clock solution:** Each observation gives δ<sub>es</sub> = ε<sub>e</sub> + ε<sub>s</sub> (emitter clock error plus sensor clock error), after removing Doppler (SGP4 for satellites). One reference, such as a GPS-disciplined KiwiSDR, fixes the gauge, and weighted least squares then solves every clock with its uncertainty.
- **Honest limits:** Without a reference, sensor and emitter clocks cannot be separated, and SANJAYA reports relative clocks only.
- **Also used for:** metadata-lie detection (the declared sample rate is checked against the anti-alias edge and symbol clocks), C3 normalisation, and Twin-conditioned training data (§8).

#### C5 · Recipe Compiler: from a recording to a deployable receiver · P1 · TRL 2→5 · 1.5 pw
- **PS hook:** "utilised for processing signals in the designated sensors".
- **Build:** Takes a **certified** recipe only (C1 PASS) and produces three outputs:
  - (a) A GNU Radio 3.10 flowgraph using gr-digital and gr-fec, plus SANJAYA out-of-tree blocks where the core has none (Reed-Solomon, generic de-interleaver, CRC-n, schema-driven frame parser).
  - (b) A versioned JSON recipe file (SigMF-compatible namespace).
  - (c) A recipe-matched detector. Its coherent gain is ≈ 10 log<sub>10</sub> L dB for L known symbols (≈ 15 dB for a 32-symbol sync word).
- **Release gate:** The compiled receiver, run on the source recording, must reproduce SANJAYA's bits exactly before it can be exported.

#### C6 · Emitter Passport and Counter Chronology · P2 · 1.0 pw
- **Passport:** The recipe (exact fields), plus physical traits (emitter clock error after sensor and Doppler correction, carrier offset, IQ image, phase noise, turn-on transient), plus protocol state (counters). Traits are matched by Mahalanobis distance, with an open-set threshold that flags a "new emitter".
- **Counter chronology:** For a b-bit counter and frame period T<sub>f</sub>, the number of frames between two captures is n = ((c<sub>2</sub> − c<sub>1</sub>) mod 2<sup>b</sup>) + k·2<sup>b</sup>, where k is chosen by the elapsed time between captures.
- **Real validation:** ADS-B, where every aircraft broadcasts its own 24-bit ICAO address. That gives thousands of transmitters with self-declared truth.

#### C7 · WAV-Lifting · P3 · 1.0 pw
Classifies a .wav as stereo IQ, real IF or receiver audio. For linear receiver chains (SSB, AM, CW audio), it inverts the chain back to complex baseband. For FM audio this is impossible (demodulation discards RF phase), so the engine analyses the demodulated message instead and says so.

#### C8 · Proof-gated learning flywheel · P3 · 1.0 pw
Only C1 PASS results with margin become training labels. It runs scheduled fine-tuning and conformal recalibration with safeguards: a frozen golden set that is never trained on, rollback if golden-set accuracy drops more than 1 point, per-class quotas, and no network access (§7.6).

### 4.3 Depth USPs: the strongest coding layer in the field

| USP | What it gives the analyst | Class |
|---|---|---|
| **D1 Soft joint coding engine** | Interleaver and code identified jointly from soft LLRs, needing far less data than hard-rank methods; rank-profile plot; concatenated codes peeled layer by layer; open-set LDPC for n ≤ 1,024 at P3 | P1 (open-set P3) |
| **D2 Blind scrambler recovery** | Additive and self-synchronising LFSRs recovered by Berlekamp-Massey on idle runs, plus a standard library | P1 |
| **D3 Bit-Lens with CRC solving** | Aligned raster, entropy map, counters, length fields; **any** CRC polynomial solved in GF(2), not just looked up; schema export | P1 |
| **D4 Scene + successive cancellation** | OS-CFAR scene; proven emitters subtracted; buried emitters revealed and decoded | P2 |
| **D5 Signal Genome + back-solving** | About 30 named standards; true sample rate and sensor clock derived from a matched standard | P2 |
| **D6 HF robustness** | Watterson channel (ITU-R F.1487) in software and on the rig; fractionally spaced equaliser; real HF via KiwiSDR | P2 |
| **D7 Trust layer** | Calibrated probabilities and split-conformal sets (P1); open-set detection and few-shot teach (P2) | P1 / P2 |

### 4.4 Head-to-head (README claims)

| Capability | ShantanuSomwanshi (9.0) | NaidhruvK (8.8) | Gururaghavendra123 (8.6) | **SANJAYA** |
|---|---|---|---|---|
| PS (i)-(v) chain | Yes | Yes | Yes | **Yes** |
| GUI | Yes | Not evident | Yes | **Yes (built)** |
| Blind interleaver size | Hard rank | Hard rank | Catalogue | **Soft, joint** |
| Waveform-level proof | No | No | CRC gate | **Yes** |
| Data needed for a decision | No | No | No | **Yes** |
| Pools captures and sensors | No | No | No | **Yes** |
| Receiver for sensors | No | No | No | **Yes** |
| Real signal, full chain, independent truth | No | No | No | **Yes** |
| Blind scrambler ID | No | Fixed | No | **Yes** |
| CRC solved (not looked up) | No | No | Known CRC | **Yes** |

---

## 5. Functional requirements (R-01 to R-15)

Verification methods: **T** test, **A** analysis, **I** inspection, **D** demonstration (NASA SP-2016-6105 Rev 2). The reference laptop is an 8-core x86-64 with 16 GB RAM, an integrated GPU and an SSD.

| ID | PS clause | Engine behaviour | Verify | Acceptance criterion |
|---|---|---|---|---|
| R-01 | .IQ or .wav input | WAV parse (mono real / stereo IQ, 8-32 bit, float). Raw-IQ sniff over dtype {u8, i8, i16, i32, f16, f32, f64} × endianness × I/Q order, each with a confidence. SigMF sidecar. Manual override. C7 for receiver audio | T | Correct format on 100 % of 200 bench files ≥ 64 kB at SNR ≥ 0 dB; every ambiguous case surfaced, never silent |
| R-02 | (i) Sampling frequency | From header or SigMF; otherwise back-solved from a recognised standard's symbol clock and the anti-alias edge; sensor clock error reported | T, A | ≤ 10 ppm on standard-anchored captures ≥ 10 s at SNR ≥ 10 dB; otherwise "Fs unknown" stated and normalised units used |
| R-03 | (i) Other parameters | Centre offset, occupied bandwidth, SNR, symbol rate, roll-off, FSK tones and index, burst timing | T | Symbol rate ≤ 10<sup>−4</sup> relative; SNR ±1 dB (SNR ≥ 0 dB); bandwidth ±5 % |
| R-04 | (i) Modulation | Three fused experts; calibrated probabilities; split-conformal 95 % set; open-set NOVEL | T | Top-1 ≥ 98 % at SNR ≥ 10 dB, ≥ 1,000 symbols, 11 classes (BPSK, QPSK, OQPSK, 8PSK, 16QAM, 64QAM, 2/4/8-FSK, MSK, GMSK); coverage 0.95 ± 0.01 |
| R-05 | (i) FEC | Blind convolutional (rate, K, generators), RS (n, k), LDPC (catalogue by syndrome), concatenation by peeling | T | ≥ 95 % at BER ≤ 10<sup>−3</sup> with ≤ 10<sup>5</sup> coded bits (conv, K ≤ 9) and ≤ 10<sup>6</sup> (RS, n ≤ 255); curves to BER 10<sup>−2</sup> |
| R-06 | (i) Interleaving | Block, convolutional, diagonal, pseudo-random; soft rank profile, identified jointly with the code; PN seed library | T | When C2 declares the data sufficient: P<sub>id</sub> ≥ 95 % (period ≤ 4,096 bits, BER ≤ 10<sup>−3</sup>); data-needed curves reported |
| R-07 | (ii) Demodulate FSK, QAM, PSK | RRC matched filter, Oerder-Meyr + Gardner timing, M-th power + Costas carrier, CMA → DD-LMS equaliser, FSK filter bank; soft LLR output | T | BER within 0.5 dB of theory at 10<sup>−4</sup> (AWGN) per scheme; HF (Watterson) curves reported |
| R-08 | (iii) De-interleave ×4 | Invertible operators parameterised by R-06; manual override | T | Bit-exact round trip on 10<sup>4</sup> random vectors per type |
| R-09 | (iv) FEC decode ×4 | C++ soft Viterbi (K 3-9, punctured), RS Berlekamp-Massey, concatenated, LDPC normalised min-sum | T | Within 0.2 dB at FER 10<sup>−3</sup> of liquid-dsp / gr-fec (conv, RS) and AFF3CT (LDPC) |
| R-10 | (v) Bit-stream correlation, header and payload | Autocorrelation frame length; soft sync discovery; aligned raster; counters and length fields; CRC solved by GF(2) algebra | T | Frame length and sync on 100 % of framed files (≥ 20 frames, BER ≤ 10<sup>−3</sup>); field class ≥ 95 % per column |
| R-11 | GUI, feature visibility | Existing UI (§10); waterfall, PSD and constellation shown on first view | D, I | All three visible on first load; any PS clause ≤ 2 clicks; 100 MB file interactive < 2 s |
| R-12 | Automated | Autopilot from raw file to header and payload; Expert mode overrides any stage | D, T | One click; full chain < 10 s for 10<sup>6</sup> samples |
| R-13 | GNU Radio, Python, C++ | Python orchestration; C++ kernels; GNU Radio for C5 output and as a test oracle | I | Each used for a stated reason |
| R-14 | Output for designated sensors | Certificate (PDF + JSON), SigMF annotations, bits (.bin / hex), header/payload map (CSV), recipe file, compiled receiver | T, D | Compiled receiver bit-exact on the source recording |
| R-15 | Signal-type triage | Classifies content as digital / voice / CW / noise before decoding; only digital enters the decode chain; mixed captures split by Scene | T | ≥ 95 % on 400 labelled files; < 1 s per file; files too short for a verdict say so |

---

## 6. System architecture

### 6.1 Principles

1. **One central object: the Recipe.** Every stage reads and writes a typed `Recipe`. Every field carries its `Evidence` (value, method, confidence, candidates, conformal set, evidence text, plot reference). The UI, the certificate, the compiler and the sensors all consume the same object. This mirrors the UI's existing `Param` type exactly (§10.2).
2. **Hypotheses, not answers.** Stages emit *ranked candidate sets with calibrated probabilities*, never a single guess. The orchestrator searches over combinations of candidates, and the proof picks the winner (§6.4).
3. **Pure numerical core, thin shell.** DSP, coding and proof are pure functions over NumPy arrays. They do no I/O, no global state and nothing random without a seed. The API, job management and storage live in a thin shell around them. This keeps every result reproducible and every module testable against oracles.
4. **Deterministic by construction.** Seeds, fixed thread counts, pinned numerical libraries, and a configuration hash stamped into every output.
5. **Offline and least-privilege.** The engine binds 127.0.0.1 only, has no outbound network code path, runs as a child process of the desktop shell, and requires a per-launch token.
6. **Classical where exact, learned where it pays.** Algebra does the coding layer (it is exact and provable). Learned models are used only where statistics beat closed form (modulation recognition at low SNR, triage), and even there a physics expert and the proof sit above them (§7).

### 6.2 Context

```
 ┌───────────────────────────── Operator workstation (air-gapped) ─────────────────────────────┐
 │                                                                                              │
 │  ┌──────────────────────┐   HTTP + WebSocket, 127.0.0.1, per-launch token  ┌──────────────┐ │
 │  │ Tauri desktop shell   │ ─────────────────────────────────────────────────▶│ SANJAYA      │ │
 │  │  └ React + three.js UI│ ◀───────── JSON + binary arrays (tiles, bits) ────│ engine       │ │
 │  │    (built, frozen)    │                                                   │ (Python 3.11 │ │
 │  └──────────────────────┘                                                   │  + C++17)    │ │
 │           ▲ spawns + supervises engine sidecar                              └──────┬───────┘ │
 │           │                                                                        │         │
 │  Recordings (.iq, .wav, .sigmf-meta)  ──────────────────────────────▶  Workspace store       │
 │                                                                        (jobs, SigMF, recipes,│
 │                                                                         certificates, twins) │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
         │ exports: certificate PDF/JSON, recipe JSON, SigMF, bits, CSV, GNU Radio flowgraph
         ▼
   Designated sensors (C5) · Collection planning (C2 tasking note)
```

### 6.3 Engine layers

| Layer | Package | Responsibility | Key tech |
|---|---|---|---|
| **L0 Kernels** | `kernels/` (C++17, pybind11) | Soft Viterbi (K 3-9, punctured), LDPC normalised min-sum, bit-packed GF(2) Gaussian elimination and rank, fast syndrome weights | C++17, SIMD where free, pybind11 |
| **L1 I/O and forensics** | `sanjaya.io` | WAV / raw IQ / SigMF readers (memory-mapped), dtype, endianness and I/Q-order sniffing, DC and IQ imbalance, hard size and type limits | NumPy memmap; fuzzed (§12) |
| **L2 Measurement** | `sanjaya.measure` | PSD (Welch), LOD spectrogram tiles, SNR (M2M4 + PSD), occupied bandwidth, symbol rate (cyclostationary), CFO, roll-off, FSK tones, bursts, Fs back-solve | SciPy |
| **L3 Triage and scene** | `sanjaya.triage`, `sanjaya.scene` | Digital / voice / CW / noise gate (R-15); OS-CFAR emitter detection; successive cancellation (D4) | NumPy, small GBDT |
| **L4 Recognition** | `sanjaya.classify` | Three-expert modulation recognition, fusion, calibration, conformal sets, open-set, few-shot teach (§7) | ONNX Runtime (inference), PyTorch (training only) |
| **L5 Demodulation** | `sanjaya.demod` | Matched filter, timing (Oerder-Meyr, Gardner), carrier (M-th power, Costas), CMA → DD-LMS equaliser, FSK / MSK / GMSK; soft LLRs | NumPy + Numba-free vectorised loops or C++ where hot |
| **L6 Unwrap (coding)** | `sanjaya.coding` | Blind interleaver ID (4 types), blind code ID (conv, RS, LDPC catalogue), concatenation peeling, scrambler recovery; decoders | L0 kernels, `galois` for GF(2<sup>m</sup>) |
| **L7 Structure** | `sanjaya.bits` | Autocorrelation, sync discovery, aligned raster, entropy, counters, length fields, CRC solving, HEADER / PAYLOAD labelling | NumPy |
| **L8 Proof** | `sanjaya.proof` | Re-synthesis, channel application, subtraction, tests T1-T4, near-miss battery, certificate + Ed25519 signature | `cryptography` (Ed25519) |
| **L9 Evidence engines** | `sanjaya.sufficiency`, `sanjaya.stitch`, `sanjaya.twin`, `sanjaya.passport` | C2, C3, C4, C6 | NumPy / SciPy |
| **L10 Outputs** | `sanjaya.compile`, `sanjaya.export` | C5 GNU Radio flowgraph + OOT blocks, recipe JSON, SigMF, CSV, bits, certificate PDF | GNU Radio 3.10 (compile target), ReportLab (PDF) |
| **Shell** | `sanjaya.api`, `sanjaya.jobs`, `sanjaya.store` | Local HTTP/WS API, job queue with cancel and progress, workspace store | FastAPI + uvicorn, stdlib `concurrent.futures` |

**Dependency rule:** a layer may import only from layers below it. The shell may import anything; nothing imports the shell. This is enforced with an import-linter check in CI.

### 6.4 The orchestrator: proof-driven hypothesis search

This is the core of the architecture, and it is what the UI's "7 → 3 loop back" shows.

```
Stage outputs are candidate sets:      mod ∈ {QPSK .91, 8PSK .07, OQPSK .02}
                                       baud ∈ {2400.02 ± 0.01}
                                       interleaver ∈ {Block 48×32 .94, Conv .03, ...}
                                       code ∈ {CC K7 (171,133) .97, ...}
Orchestrator:
  1. Build the joint hypothesis queue ordered by joint posterior (best-first, beam width k = 8).
  2. Pop the best hypothesis → demodulate → unwrap → structure → PROVE.
  3. PASS  → certify; run the near-miss battery; subtract; re-scan the scene.
     FAIL  → record why (which test failed, by how much) → down-weight the hypotheses that
             the failure implicates → pop the next one.  (UI: stage 7 fails, rail routes to 3)
  4. Budget exhausted with no PASS → report the best partial recipe honestly plus C2's
     "what more data is needed", never a fabricated answer.
```

- Downstream stages are re-run only when an upstream value changes. Stage outputs are memoised by the hash of (input, upstream recipe fields, stage configuration). This is also how an Expert-mode override reruns "only what comes after it".
- Each stage's work is cancellable and reports progress over the WebSocket.

### 6.5 Core data model

```python
Method = Literal["blind", "library", "manual"]

@dataclass(frozen=True)
class Evidence:
    key: str                      # "modulation", "baud", "fec", "interleaver", ...
    label: str                    # PS wording first: "Modulation", "Sampling frequency"
    value: str                    # display value
    unit: str | None
    raw: Any                      # machine value (float, dict, polynomial ...)
    method: Method                # Blind-recovered / Matched from library / Manually set
    conf: float | None            # calibrated probability; None where not applicable
    cands: list[tuple[str, float]] | None
    conformal_set: list[str] | None
    stage: int                    # 0..7, the loop stage that produced it
    text: str                     # human-readable evidence ("4th-power line at ...")
    plot: str | None              # id of the evidence plot the UI opens on click

@dataclass
class Recipe:
    schema_version: str           # semver
    input_sha256: str
    evidence: dict[str, Evidence]
    chain: list[dict]             # ordered transmitter chain: code → interleaver → scrambler → mapper → shape
    frame: FrameSchema | None     # fields: name, group (HEADER/PAYLOAD/TRAILER), start, len, kind, note
    sensor_id: str | None

@dataclass
class ProofResult:
    verdict: Literal["pass", "fail", "inconclusive"]
    eta: float; rho_db: float; cyclic_coherence: float; ljung_box_p: float; kurtosis: float
    crc_pass_rate: float | None
    near_misses: list[dict]       # {hypothesis, rejected: bool, statistic}
    thresholds: dict              # calibrated values used, with their calibration set id

@dataclass
class Certificate:
    id: str; issued_utc: str; engine_version: str; config_hash: str
    recipe: Recipe; proof: ProofResult; equivalences: list[str]
    signature: str; key_id: str   # Ed25519 over the canonical JSON
```

The **recipe JSON schema** is semantic-versioned and published with the certificate, the compiler and the sensors. A SigMF-compatible namespace (`sanjaya:`) carries it inside `.sigmf-meta` annotations.

### 6.6 Local API (v1)

All routes are on `127.0.0.1:<port>` and require the header `X-Sanjaya-Token` (a random value per launch, passed from Tauri to the UI). CORS allows only the Tauri origin. Large arrays travel as `application/octet-stream` with the shape and scaling in response headers.

| Method | Route | Purpose | UI consumer |
|---|---|---|---|
| POST | `/v1/jobs` | Open a file (path) with optional overrides (dtype, Fs, fc, endianness) | Ingest |
| GET | `/v1/jobs/{id}` | Job state: 8 stage statuses, loop-back flag, proof state | Stepper, stage rail |
| WS | `/v1/jobs/{id}/events` | Stage start / progress / done / fail events | Stepper, stage rail |
| GET | `/v1/jobs/{id}/forensics` | Container, dtype, endianness, I/Q order, DC, imbalance, SigMF: each with a confidence and a note | Ingest |
| GET | `/v1/jobs/{id}/triage` | `{label, conf, why}` (same shape as `triage.ts`) | Ingest, Signal |
| GET | `/v1/jobs/{id}/spectrogram?kind=full\|resid\|fail&lod=n` | Uint8 packed dB tiles (header: bins, rows, lo, range) | Waterfall, Terrain |
| GET | `/v1/jobs/{id}/psd`, `/constellation`, `/eye`, `/instfreq`, `/rowpower` | Linked-view data | Signal |
| GET | `/v1/jobs/{id}/params` | `Record<string, Param>` (§10.2) | Parameters panel |
| GET | `/v1/jobs/{id}/unwrap` | Rank profile, interleaver type scores, FEC family scores, conv candidates, scrambler | Decoding |
| GET | `/v1/jobs/{id}/bits` | Bit stream (binary), frame schema, CRC search result, autocorrelation | Header & payload |
| POST | `/v1/jobs/{id}/override` | `{key, value}`: Expert override; reruns downstream stages only | Expert mode |
| POST | `/v1/jobs/{id}/prove` | Runs C1; returns ProofResult; residual available as `kind=resid` | Proof |
| GET | `/v1/jobs/{id}/certificate.json` / `.pdf` | Signed certificate | Certificate |
| GET | `/v1/jobs/{id}/sufficiency` | C2 decision state, predicted ΔT, tasking note | Proof / Signal |
| GET | `/v1/jobs/{id}/scene` · POST `/scene/{emitter}/cancel` | Emitters; successive cancellation | Scene |
| POST | `/v1/stitch` | `{job_ids}` → pooled decision (C3) | Scene / Proof |
| POST | `/v1/jobs/{id}/compile` | C5 flowgraph + recipe file (only if certified) | Certificate |
| GET | `/v1/genome` · `/v1/jobs/{id}/genome` | Standards catalogue; match scores | Standards |
| GET | `/v1/jobs/{id}/export/{sigmf\|bits\|csv\|recipe}` | Exports (R-14) | Certificate, palette |

### 6.7 Process, performance and storage

- **Process model:** Tauri spawns the engine as a sidecar and watches its health. Heavy stages run in a process pool, since NumPy and C++ release the GIL. Only one job mutates a given workspace at a time.
- **Large files:** Files are memory-mapped and never fully loaded. Spectrogram tiles are precomputed at several levels of detail on ingest (the first tile in < 2 s for 100 MB). Analysis stages work on the selected emitter's channelised baseband, not the full band.
- **Workspace store:** A directory per job containing the input reference (path + SHA-256, never copied unless the user asks), `recipe.json`, the certificate, SigMF annotations, memoised stage caches and logs. Sensor Twins live in `twins/<sensor_id>.json`.
- **Packaging:** The engine is frozen into the Tauri bundle as a sidecar. All dependencies come from an offline wheelhouse pinned by hash, and each release gets a CycloneDX SBOM.

---

## 7. The intelligence: ML and inference design

### 7.1 Where the edge really is

The moat is not a secret network architecture; a small CNN anyone can train. The moat is the **system around the models**, and no competitor has it:

1. **A physics expert that cannot suffer the sim-to-real gap** (decode-fit likelihood), fused with the learned expert.
2. **A verifier above every model** (C1). A wrong classification is caught by the proof and corrected by the hypothesis search. The model only has to put the truth in its top-k, not at top-1.
3. **Canonicalised inputs.** Symbol rate and CFO are estimated classically *first*, so the network always sees the signal at a fixed number of samples per symbol. RadioML-style models trained at one oversampling rate break on real files; ours generalise across symbol rates by construction.
4. **Calibration and conformal sets as first-class outputs,** so the confidence numbers mean what they say.
5. **A data engine with independent truth,** plus proof-gated self-labelling (§8), so the models keep improving on real data without human labels.

### 7.2 Modulation recognition: three experts, fused (R-04, D7)

| Expert | Input | Model | Why it's there |
|---|---|---|---|
| **E1 Feature expert** | Higher-order cumulants (C<sub>40</sub>, C<sub>41</sub>, C<sub>42</sub>, C<sub>61</sub>, C<sub>63</sub>), M-th power spectral lines (M = 2, 4, 8), cyclic features at α = 1/T, amplitude and phase statistics, instantaneous-frequency histogram (FSK) | Gradient-boosted trees (< 1 MB) | Interpretable, robust at high SNR, cheap; these features feed the evidence text in the UI |
| **E2 Deep expert** | Rate-normalised baseband (after classical symbol rate + CFO estimation, resampled to 8 samples/symbol), 1,024-sample windows as I/Q + amplitude/phase channels; plus a 32 × 32 constellation density image after timing recovery | Dual-branch: 1-D ResNet on IQ + small 2-D CNN on density, late fusion, < 3 M parameters, CPU | Wins at low SNR and under impairments where closed-form features blur |
| **E3 Decode-fit expert** | For each candidate class: synchronise under that hypothesis and compute the log-likelihood of the received symbols under the class's constellation with the estimated SNR (Gaussian-mixture likelihood); for FSK, tone-bank likelihood | No training; pure physics | Immune to sim-to-real gap; separates look-alikes (QPSK vs OQPSK vs 8PSK) by how well each explains the data |

**Fusion and trust layer:**
1. Each expert gets per-expert temperature scaling on a held-out calibration split.
2. Stacking: a logistic-regression combiner over the three experts' log-probabilities, trained on a separate split.
3. Evidence is accumulated over windows by summing log-likelihoods across N windows. This gives C2 its evidence-growth rate D directly.
4. Split-conformal prediction sets (APS scores) at 95 % coverage, recalibrated per release.
5. Open-set: an energy score on E2's logits combined with class-conditional Mahalanobis distance in E2's embedding space. Above threshold, the signal is marked **NOVEL**.
6. Few-shot "Teach" (P2): about 5 examples become a prototype in the embedding space, and the conformal set is recalibrated.
7. **The final arbiter is C1.** The fused posterior orders the hypothesis queue (§6.4); the proof decides.

**Training recipe:**
- **Data:** SANJAYA-Gen with Twin-conditioned domain randomisation (§8.2). Class-balanced. SNR from −6 to +30 dB with a curriculum from high to low SNR.
- **Self-supervised pretraining** of the E2 encoder: masked IQ reconstruction plus contrastive views (two impairment draws of the same burst) on **unlabelled real recordings** (KiwiSDR hours, SatNOGS, rig captures). This adapts the representation to real front-ends before any labels are used.
- **Fine-tuning:** on labelled synthetic + HIL data, then on proof-gated real labels (C8).
- **Export:** to ONNX with a fixed opset and run with ONNX Runtime at inference **[PRD refinement: v3 says PyTorch CPU; training stays in PyTorch, shipping ONNX Runtime gives a smaller offline installer and deterministic inference]**.
- **Reporting:** a reliability diagram, ECE, and accuracy vs SNR, vs symbol count and vs impairment, each with Wilson intervals.

### 7.3 Signal-type triage (R-15)

- **Features:** occupied band, symbol-rate line strength, frame-to-frame level variation, spectral flux, single-line energy fraction, syllabic modulation (4 Hz envelope energy for voice), and on/off keying statistics for CW. The in-browser `triage.ts` heuristic is the baseline and is ported one-to-one.
- **Model:** a small gradient-boosted classifier over those features, trained on synthetic data plus real KiwiSDR voice/data and SatNOGS audio.
- **Abstain:** files too short for a verdict say so, and nothing is guessed.

### 7.4 Coding layer: algebra, deliberately not ML

Learned code recognisers only report the most likely class; algebra gives exact, checkable parameters. SANJAYA uses:
- **Interleaver and code, jointly (D1):** soft rank profile. Rows are reliability-weighted and the rank deficiency is scored by soft syndrome likelihood (Valembois; Sicot-Houcke-Barbier; Marazin-Gautier-Burel), searched over period and phase. Block, convolutional (staircase in rank vs delay), diagonal and PN (seed library) each have a dedicated detector.
- **Convolutional:** dual-code search for (n, k, K) and generator polynomials; puncturing patterns from the library.
- **RS:** Galois Field Fourier Transform root test over GF(2<sup>m</sup>) candidates, confirmed by decode success rate.
- **LDPC:** catalogue identification by syndrome weight across known parity-check matrices (DVB-S2, CCSDS, 802.11, 5G NR base graphs); open-set short-code recovery (n ≤ 1,024) at P3.
- **Concatenation:** peel the inner code first, decode, then identify the outer code on the inner decoder's output.
- **Scrambler (D2):** Berlekamp-Massey on runs of known idle or padding bits, followed by a seed search. Additive and self-synchronising variants are told apart by error propagation.

### 7.5 Data-sufficiency (C2) as Bayesian bookkeeping

Every open decision (modulation, interleaver period, code, frame length) keeps a log-evidence ledger that grows with each window. The rate D is the fitted slope of the top-two log Bayes factor. There is no separate model; C2 reads the ledgers the other stages already write.

### 7.6 Learning flywheel (C8, P3) safeguards

- Admission requires a C1 PASS with margin.
- A frozen golden set (Tier 1 seeds + sealed Tier 3 captures) is never trained on.
- Automatic rollback if golden accuracy drops by more than 1 point.
- Per-class quotas stop the model drifting toward easy signals.
- NOVEL and FAIL cases go to an active-learning queue for the analyst.
- Model files inherit the data's classification. No network access.

---

## 8. Beating the data problem

"Not enough data" means two different things here, and SANJAYA handles both.

### 8.1 Problem A: not enough *training* data (no public NTRO datasets)

| Lever | What we do | Why it works |
|---|---|---|
| **1. Generate with exact truth** | SANJAYA-Gen (§8.2) synthesises every PS combination with bit-exact ground truth | Unlimited labelled data for every class, code and interleaver, including LDPC, diagonal and PN, which don't exist in public datasets |
| **2. Make synthetic look real** | Impairments sampled from *measured* Sensor Twins (rig, KiwiSDRs, RTL-SDR, Pluto), not textbook defaults: clock ppm, IQ imbalance, phase noise, AA filter shape, ADC bits, AGC, Watterson HF fading | Closes most of the sim-to-real gap by training on the impairments our sensors actually have |
| **3. Real hardware, exact truth** | Tier 2 cabled rig: Pluto → attenuators → RTL-SDR V4 and Pluto RX. We transmit our own waveforms | Real DACs, ADCs and oscillators with truth known by construction |
| **4. Real signals, independent truth** | Tier 3: Meteor-M LRPT (SatDump), HFDL (dumphfdl), STANAG 4285 (public preamble/probes + C1), NAVTEX (fldigi), AO-40-FEC satellites (gr-satellites), ADS-B (ICAO), SGP4 Doppler, multi-site KiwiSDR with GPS timestamps | Truth we did not create; validates the whole chain and the estimators |
| **5. Learn from unlabelled audio and IQ** | Self-supervised pretraining on hours of unlabelled KiwiSDR, SatNOGS and rig recordings (§7.2) | Real-front-end representation without a single human label |
| **6. Let the proof label the data** | C8: only C1-PASS results become labels | Labels whose error rate is bounded by the false-PASS rate (≤ 10<sup>−4</sup> target) |
| **7. Physics where data is thin** | E3 decode-fit expert and the algebraic coding layer need no training | The riskiest parts of the chain do not depend on the dataset at all |
| **8. Measure the gap** | Every model is reported separately on synthetic, HIL and real test sets | The sim-to-real gap is a number we track, not a hope |

### 8.2 SANJAYA-Gen specification

Deterministic (seeded) and parameterised. It writes SigMF data plus a truth JSON holding the full recipe and the bits at every layer.

| Axis | Range |
|---|---|
| Modulation | BPSK, QPSK, OQPSK, 8PSK, 16QAM, 64QAM, 2/4/8-FSK, MSK, GMSK (+ π/4-DQPSK, AFSK for standards) |
| Symbol rate / oversampling | 50 Bd to 1 MBd; 2 to 20 samples/symbol, non-integer included |
| Pulse shape | RRC / RC roll-off 0.1-0.5; Gaussian BT 0.3-0.5; rectangular |
| Channel | AWGN SNR −6 to +30 dB; CFO ± 0.2 × Rs; timing offset; phase noise; Watterson HF (ITU-R F.1487 good / moderate / poor); multipath |
| Front-end (Twin-sampled) | Clock ±50 ppm; IQ gain/phase imbalance; DC; AA filter; 8/12/16-bit quantisation; clipping; AGC |
| FEC | Convolutional K 3-9, rates 1/2, 1/3, punctured 2/3 and 3/4; RS (n ≤ 255) over GF(2<sup>8</sup>) and smaller; concatenated RS ∘ CC; LDPC (DVB-S2 short, CCSDS, 802.11) |
| Interleaving | Block (periods up to 4,096 bits), convolutional (Forney), diagonal, pseudo-random (seeded) |
| Scrambling | Additive and self-synchronising LFSRs (degree ≤ 23), standard polynomials + random |
| Framing | Sync words (8-64 bits), counters, length and type fields, random or structured payloads, CRC-8/16/32 with arbitrary polynomial and init |
| File formats | Raw IQ in every R-01 dtype × endianness × I/Q order; WAV real / stereo; with and without SigMF |

**Sizing:** set by learning curves, not guessed. The target is to stop adding data when the validation curve has flattened within its Wilson interval.

### 8.3 Problem B: not enough data *in the recording* (the PS's complaint)

| Lever | Mechanism |
|---|---|
| Need less data | Soft-decision, joint interleaver + code ID (D1) instead of hard-rank methods that need error-free rows (compare the C2 derivation: 23.6 h vs our measured curve) |
| Use all of the data | Sequential evidence accumulation across windows; decode-fit likelihood uses every symbol |
| Pool data across files | C3 Evidence Stitching across captures, sensors and locations, with per-capture proof to eject mis-associations |
| Remove sensor differences before pooling | C4 Sensor Twin normalisation |
| Say exactly how much more is needed | C2: predicted ΔT and a tasking note |
| Never fake it | Below the decision threshold, the output is "undecided: top-2 with probabilities + ΔT needed", never a guess |

### 8.4 Data management

Every capture is stored as SigMF with metadata: UTC time, receiver, location, antenna, gain, sample rate, centre frequency and truth source. SHA-256 checksums go in a versioned manifest. Synthetic sets are regenerated from recorded seeds. Sealed test sets (Tier 1 seeds and Tier 2-3 captures) are held by the independent verifier and never shown to developers.

### 8.5 Legal and ethics (from v3)

- **Transmission:** conducted only (coax into ≥ 50 dB attenuation, no antenna). Where a test signal fits it, the licence-exempt 433.05-434.79 MHz band (WPC G.S.R. 347(E), 2022) is a second safeguard.
- **Reception:** public broadcasts only.
- **Payloads:** never decrypted or displayed. ICAO and MMSI identities are used only as truth labels.
- **KiwiSDR:** respect each operator's time limits and credit them.

---

## 9. Accuracy engineering

Accuracy is designed in at five levels, and each level catches the errors of the one below.

### 9.1 Level 1: every estimate has an independent cross-check

| Parameter | Primary estimator | Independent check | On disagreement |
|---|---|---|---|
| Sampling frequency | Header / SigMF | Anti-alias edge; standard's symbol clock (D5) | Flag "metadata lie" (C4); use the measured value with its uncertainty |
| Symbol rate | Cyclostationary line in \|x\|² | Timing-loop convergence; decode-fit peak | Confidence lowered; both values shown |
| CFO | M-th power spectral line | Costas-loop residual | Re-acquire with narrower search |
| SNR | M2M4 on matched-filter output | In-band vs out-of-band PSD | Report the range |
| Modulation | Fused E1/E2 | E3 decode-fit + C1 | The proof decides |
| Interleaver / code | Soft rank profile | Decode success (syndrome weight → 0, CRC pass rate) | Next hypothesis |
| Frame / CRC | Autocorrelation + sync search | CRC solved over all frames | Field confidence per column |

### 9.2 Level 2: never collapse early

Every stage keeps a ranked candidate set with calibrated probabilities. Downstream stages run on the best hypothesis, but the others stay in the queue. A wrong early choice costs time, not the answer.

### 9.3 Level 3: the whole recipe is checked at once (C1)

Any wrong parameter anywhere in the chain (roll-off, one generator polynomial, interleaver phase) leaves structured energy in the residual and fails T1-T4. The proof checks all the parameters jointly, which no single estimator can.

### 9.4 Level 4: confidence that means what it says

- **Calibration:** per-expert temperature scaling. Reliability diagrams and ECE are reported per release.
- **Conformal coverage:** 95 % sets must cover 0.95 ± 0.01 on sealed data.
- **Method tags:** every value is labelled Blind-recovered, Matched from library, or Manually set, and never overclaims (for example LDPC is catalogue-identified).
- **Abstention:** "Fs unknown", "undecided + ΔT", "high-entropy payload, likely encrypted; decryption is out of scope".

### 9.5 Level 5: measured, not asserted

- **Unit level:** every decoder is tested against oracles (liquid-dsp, gr-fec, AFF3CT) and must be within 0.2 dB.
- **Pre-registration:** metric definitions are frozen before measurement: SNR as E<sub>s</sub>/N<sub>0</sub>; P<sub>id</sub> with 95 % Wilson intervals and n ≥ 500 per condition; BER always labelled pre-FEC or post-FEC; false PASS bounded by the rule of three.
- **CI regression gate:** a fast suite runs on every merge and the full bench runs nightly. A merge is blocked if any KPI falls outside its previous confidence interval.
- **Independence:** a member who did not build a module runs the sealed sets for it.
- **Reproducibility:** every run records the code version, configuration hash, dataset manifest hash and seeds.

### 9.6 Error-propagation budget (where accuracy is lost and how it is recovered)

| Upstream error | Symptom downstream | Recovery |
|---|---|---|
| Symbol rate off by > 10<sup>−4</sup> | Timing drift, rising EVM over the file | Timing loop tracks; decode-fit peak refines; the proof fails if it is unresolved |
| Wrong modulation | High EVM, garbage bits, rank profile flat | Proof FAIL → next hypothesis |
| Wrong interleaver phase | Syndrome weight ≈ 0.5 | Phase search inside D1 |
| Wrong code polynomial | Viterbi path metric poor, CRC 0 % | Next candidate from the dual-code search |
| Scrambler missed | Frames never align; entropy uniform | D2 on idle runs; the proof flags the equivalence |
| Insufficient data | Posterior below 1 − α | C2 reports ΔT; C3 stitches |

---

## 10. UI integration contract (UI design is frozen)

### 10.1 Rules

1. **No design changes.** Tokens (`ui/src/styles/tokens.css`), layout, typography, colours, motion, the 5-step flow, the Tools menu and the three.js terrain stay exactly as built. Proof green appears only on proofs; there is one accent colour.
2. **Swap the data source, not the components.** Add one adapter, `ui/src/lib/engine.ts`, whose exports mirror `mock.ts`'s names and types. Pages switch imports from `mock` to `engine`. `mock.ts` stays as the offline demo fallback (demo beats in §12 rely on it).
3. **Store actions call the engine.** `runAutopilot()` and `prove()` in `store.ts` keep their signatures; their timers are replaced by WebSocket stage events. `stages`, `loopBack`, `proof` and `proofT` are driven by real engine state. The PROVE dissolve still animates `proofT` from 0 to 1 and ends on the engine's real verdict.
4. **New information uses existing components.** Tasking notes, near-miss lists and stitching results render in the existing panel, parameter and evidence patterns. No new visual language.
5. **The browser-side analysis stays.** WAV/SigMF parsing, dtype sniffing and triage in the browser give instant feedback on drop; the engine's answer then replaces them when ready.

### 10.2 Type contract (engine JSON = UI types)

`GET /v1/jobs/{id}/params` returns exactly the UI's `Param`:

```ts
interface Param {
  key: string; label: string; value: string; unit?: string
  method: 'blind' | 'library' | 'manual'
  conf: number | null
  stage: number
  cands?: { v: string; p: number }[]
  set?: string            // conformal set, e.g. "{QPSK}"
  evidence: string
}
```

The other shapes map one-to-one to existing exports:

| UI export (`mock.ts`) | Engine route |
|---|---|
| `SCENARIO.file`, `SCENARIO.forensics` | `/v1/jobs/{id}`, `/forensics` |
| `SCENARIO.emitters` | `/scene` |
| `SCENARIO.proof`, `SCENARIO.cert` | `/prove`, `/certificate.json` |
| `SPEC`, `spectrogram()` (`full`, `resid`, `fail`, `rowPower`) | `/spectrogram?kind=…`, `/rowpower` (Uint8 packing with lo = −110, range = 60 as `Terrain.tsx` expects; carried in headers) |
| `bitstream()`, `FRAME`, `crcSearch()`, `findSync()` | `/bits` |
| `rankProfile()`, `INTERLEAVER_TYPES`, `FEC_FAMILIES`, `CONV_CANDIDATES` | `/unwrap` |
| `GENOME` | `/v1/genome` |
| `triage()` result `{label, conf, why}` | `/triage` |

### 10.3 Page → engine map

| UI page | PS clauses shown | Engine data |
|---|---|---|
| Recording (Ingest) | Input .IQ / .wav, format path, overrides | jobs, forensics, triage |
| Signal | Sampling frequency, waterfall, PSD, constellation / FSK views, modulation | spectrogram, psd, constellation, eye, instfreq, params |
| Decoding | Demodulation, de-interleaving (4 types), FEC (4 families), scrambler | unwrap, params |
| Header & payload | Bit-stream correlation, HEADER / PAYLOAD | bits |
| Proof (+ Certificate) | Accuracy and confidence | prove, spectrogram `resid`/`fail`, sufficiency, certificate, compile |
| Scene · Standards · Challenge · Compliance | Extras | scene, genome, jobs; Compliance stays static |

---

## 11. Implementation plan in phases

**Capacity:** 6 members × 25 h/week × 10 weeks = **37.5 pw**. P1 is planned at **31.2 pw**, leaving **6.3 pw (17 %) reserve**. P2 draws on the reserve only after gate G3. Roles: DSP, Coding, Protocol, ML, Product, Data. Load per role is ≤ 6.25 pw; Coding (6.0) is the tightest, so it is paired with ML on WP06.

**Build order logic:** get one signal all the way through (a vertical slice) before widening anything. Each phase ends at a v3 gate with measurable exit criteria, and the UI is wired from Phase 1 so every phase can be demonstrated in the real product.

### Phase 0: Foundation and vertical slice (before and around idea submission) → gate G0

**Goal:** a synthetic QPSK + convolutional + block-interleaved file decoded and **proved** end to end. This produces the C1 clip for the idea-submission deck.

| Task | Detail | WP |
|---|---|---|
| Repo skeleton | `engine/` layout (§13), pyproject, pinned wheelhouse, pre-commit, import-linter, CI (fast suite) | WP13 |
| SANJAYA-Gen v0 | QPSK, RRC 0.35, CC K=7 (171,133), block interleaver 48 × 32, additive scrambler, framed with sync + counter + CRC-16; AWGN + CFO + timing offset; SigMF + truth JSON | WP13 |
| Known-recipe chain | Given the truth recipe: demodulate → de-interleave → Viterbi (Python reference first) → descramble → frames | WP03, WP05 |
| C1 minimum | Re-synthesis + subtraction + T1, T2, T4 (T3 in Phase 2) | WP09 |
| Recipe / Evidence types + JSON schema v0 | §6.5 | WP15 |
| Idea deck | From v3 + UI screenshots + C1 clip | WP18 |

**Exit (G0):** the vertical-slice file decodes bit-exact with the known recipe and the residual passes T1/T2/T4. The deck is submitted.

### Phase 1: The spine (W1-W2) → gate G1

**Goal:** real ingest, real measurements, real receivers, wired to the UI's Recording and Signal steps.

| Task | Detail | WP |
|---|---|---|
| Ingest and forensics | WAV / raw IQ / SigMF; dtype × endianness × I/Q sniff with confidence; DC, IQ imbalance; limits | WP01 |
| Measurements | PSD, LOD spectrogram tiles, SNR (M2M4 + PSD), bandwidth, symbol rate, CFO, roll-off, FSK tones | WP02 |
| Receivers | PSK / QAM timing + carrier + CMA → DD-LMS; FSK bank; MSK/GMSK; soft LLRs | WP03 |
| C++ kernels | Soft Viterbi (punctured), GF(2) rank; pybind11; oracle tests vs liquid-dsp / gr-fec | WP05 |
| Local API + jobs | FastAPI, token, WS events, jobs, forensics, spectrogram, psd, constellation, params | WP15 |
| UI adapter | `engine.ts`; Ingest + Signal pages on real data; `runAutopilot()` on WS events | WP15 |
| Bench + CI | KPI harness skeleton, Wilson intervals, nightly run | WP13 |
| Rig + first real data | Pluto → attenuators → RTL-SDR; first Meteor pass attempts; KiwiSDR recording script | WP14 |

**Exit (G1):** the spine decodes Tier 1 and Tier 2 files with known recipes in the UI; bench and CI running.

### Phase 2: Blind coding core + proof (W3-W4) → gate G2

**Goal:** the engine finds the recipe by itself, and C1 is complete.

| Task | Detail | WP |
|---|---|---|
| Blind coding layer | Hard rank first, then soft joint interleaver + code (D1); block and convolutional interleavers; conv code dual search; RS GFFT; concatenation peeling | WP06 |
| Decoders | RS Berlekamp-Massey (`galois`), concatenated chain | WP05 |
| Scrambler | Berlekamp-Massey + seed search; library | WP07 |
| Bit-Lens | Autocorrelation, sync discovery, raster, entropy, counters, length fields, CRC solving; HEADER / PAYLOAD | WP08 |
| C1 complete | T3 cyclic coherence; threshold calibration on Tiers 1-2; near-miss battery; certificate + Ed25519 + PDF | WP09 |
| AMC v1 | E1 feature expert + E3 decode-fit; temperature scaling; conformal sets | WP04 |
| Orchestrator | Hypothesis queue, memoised stages, proof-driven backtracking, Expert override | WP15 |
| UI | Decoding, Header & payload, Proof, Certificate on real data; PROVE ends on the real verdict | WP15 |
| Real data | First Meteor-M LRPT decode matched against SatDump | WP14 |

**Exit (G2):** blind coding core + C1 pass on Tiers 1-2; first Meteor decode matches SatDump.

### Phase 3: Full PS coverage and hardening (W5-W6) → gate G3

**Goal:** R-01 to R-15 all pass on the bench. Decide on P2.

| Task | Detail | WP |
|---|---|---|
| Remaining interleavers | Diagonal, pseudo-random (seed library) | WP06 |
| LDPC | Normalised min-sum kernel; catalogue ID by syndrome; oracle tests vs AFF3CT | WP05, WP06 |
| AMC v2 | E2 deep expert (self-supervised pretraining + fine-tune), 3-way stacking, open-set NOVEL | WP04 |
| Triage | R-15 model + abstain; 400-file labelled set | WP19 |
| Fs back-solve | Standard symbol clock + AA edge; metadata-lie check | WP02 |
| Tier 3 widening | HFDL (dumphfdl), STANAG 4285, NAVTEX (fldigi) via KiwiSDR; AO-40-FEC satellites if live | WP14 |
| Assurance start | Coverage-guided fuzzing of WAV / raw IQ / SigMF parsers | WP16 |
| Performance | 100 MB interactive < 2 s; full chain < 10 s for 10<sup>6</sup> samples | WP15 |

**Exit (G3):** R-01 to R-15 pass on the bench (measured, with intervals). **P2 activation is decided from the measured reserve.**

### Phase 4: Crown innovations (W7-W8) → gate G4

**Goal:** the PS's three complaints answered on real data.

| Task | Detail | WP |
|---|---|---|
| C2 Data-Sufficiency | Evidence ledgers, D fit, ΔT prediction, tasking note; validation on Tiers 1-2 | WP10 |
| C4-lite Sensor Twin | Clock, noise floor, IQ, AA response from signals of opportunity; GPS-reference gauge | WP11 |
| C3 Stitching | Associate → normalise → align → pool → per-capture proof; multi-site KiwiSDR (≥ 3 countries, GPS timestamps) | WP11 |
| C5 Recipe Compiler | GNU Radio 3.10 flowgraph + OOT blocks (RS, de-interleaver, CRC-n, frame parser); bit-exact release gate; live on rig | WP12 |
| P2 (if activated at G3) | Order: D4 scene + cancellation → D5 Genome back-solve → C6 passport (ADS-B) → C4-full → D6 real-HF tuning → D7 open-set / Teach | reserve |
| Demo | Script frozen; sealed mystery files generated | WP18 |

**Exit (G4):** C2, C3 (multi-site real) and C5 (bit-exact) complete; demo script frozen.

### Phase 5: Proof of performance and release (W9-W10) → gate G5

| Task | Detail | WP |
|---|---|---|
| Independent verification | Sealed Tier 1-3 sets run by non-builders; KPI report with Wilson intervals and rule-of-three bounds | WP17 |
| Assurance | ≥ 24 CPU-h fuzzing with zero crashes; network-isolation test with packet capture (zero outbound); SBOM; signed installer built from wheelhouse on a clean offline machine; licence register | WP16 |
| Release | Tauri bundle with engine sidecar; feature freeze end of W9 | WP15 |
| Rehearsal (W10) | Five full demo rehearsals, one with an injected failure; fallbacks exercised | WP18 |

**Exit (G5):** independent KPI report published internally; feature freeze; W10 is rehearsal only.

### 11.1 Work-package ledger (P1, from v3 §10)

| WP | Content | pw | Owner | Phase |
|---|---|---|---|---|
| WP01 | Ingest and forensics (R-01) | 1.0 | DSP | 1 |
| WP02 | Measurements, Fs back-solve (R-02, R-03) | 1.5 | DSP | 1, 3 |
| WP03 | Receivers PSK/QAM/FSK/GMSK + equaliser (R-07) | 3.0 | DSP | 0, 1 |
| WP04 | AMC experts, calibration, conformal (R-04, D7) | 1.5 | ML | 2, 3 |
| WP05 | FEC decoders in C++ (R-09) | 2.5 | Coding | 0-3 |
| WP06 | Blind coding layer, hard → soft (R-05, R-06, D1) | 3.5 | Coding (+ML) | 2, 3 |
| WP07 | Scrambler recovery (D2) | 1.0 | Protocol | 2 |
| WP08 | Bit-Lens + CRC solving (R-10, D3) | 1.5 | Protocol | 2 |
| WP09 | C1 Proof-of-Decode + certificate | 1.5 | ML | 0, 2 |
| WP10 | C2 Data-Sufficiency + tasking | 1.0 | ML | 4 |
| WP11 | C4-lite Twin + C3 Stitching | 2.0 | Data | 4 |
| WP12 | C5 Recipe Compiler + OOT blocks | 1.5 | Product | 4 |
| WP13 | SANJAYA-Gen, bench, CI | 2.0 | Protocol | 0, 1 |
| WP14 | Real-data engine: rig, Meteor, multi-site KiwiSDR, HFDL, truth pipelines | 2.0 | Data | 1-3 |
| WP15 | UI-engine integration (R-11, R-12) | 1.5 | Product | 0-5 |
| WP16 | Assurance: fuzzing, isolation test, SBOM, installer | 1.5 | Product | 3, 5 |
| WP17 | Independent verification runs + KPI report | 1.0 | Protocol* | 5 |
| WP18 | Pitch, demo, rehearsals | 1.0 | Data (lead) | 0, 4, 5 |
| WP19 | Signal-type triage (R-15) | 0.7 | ML | 3 |
| | **P1 total** | **31.2** | reserve 6.3 | |
| P2 | C4-full, C6, D4, D5, D6, D7 open-set | 4.0 | reserve after G3 | 4 |
| P3 | C7, C8, open-set LDPC, QO-100 real LDPC | 4.5 | bench / roadmap | — |

\* The protocol lead coordinates independent verification but never verifies WP07, WP08 or WP13, which they build.

**Descoping order if the schedule slips:** P3 → P2 (reverse of the activation order) → C3 real multi-site falls back to rig multi-sensor → C5 live falls back to bit-exact on file. P1 PS coverage and C1 are never cut.

---

## 12. Verification, assurance, risks, demo

### 12.1 V&V levels

| Level | What | Pass rule |
|---|---|---|
| Unit | Every estimator, decoder and parser vs oracles and analytic cases | Oracle agreement within tolerance |
| Integration | Full chain on Tier 1 | Recipe exact; bits exact |
| System | Tiers 1-3 incl. near-miss wrong hypotheses | §5 acceptance criteria |
| Independent | Sealed sets run by non-builders | Numbers reported as measured, with intervals |
| Operational | Frozen build, 5 rehearsals, one with an injected failure | Under 7 min; fallbacks exercised |

### 12.2 Assurance for an intelligence user

| Concern | Control | Verified by |
|---|---|---|
| Hostile input | Coverage-guided fuzzing of all parsers; strict limits; least-privilege engine isolated from the UI | ≥ 24 CPU-h fuzzing, zero crashes or hangs |
| Network leakage | No network code at runtime; 127.0.0.1 bind; per-launch token; strict CORS | Full demo in an isolated sandbox with packet capture: zero outbound packets |
| Supply chain | Offline wheelhouse pinned by hash; CycloneDX SBOM; signed installer | Clean offline build |
| Certificate integrity | Ed25519 key generated offline per site, never exported; version and config hashed in | Reproduce a certificate on a second machine |
| Licences | Register; copyleft tools only as test oracles; our GNU Radio blocks released with source | Inspection of the bundle |

### 12.3 Top risks (full register in v3 §11)

| ID | Risk | L×C | Mitigation | Trigger |
|---|---|---|---|---|
| K01 | Real signals need more data than captures hold | 16 | D1 soft methods, C3 sync-aided stitching, C2 honest reporting | Tier 3 P<sub>id</sub> < 80 % at G3 |
| K02 | Schedule overrun | 16 | WBS, 17 % reserve, gates, descoping order | Any WP > 25 % over at a gate |
| K03 | Demo failure at the venue | 12 | Frozen build, rehearsals, backup laptop, fallback per beat | Any rehearsal failure |
| K04 | False certificates | 10 | Four-test proof, calibration, near-miss testing, independent runs | Any false PASS on the bench |
| K07 | Coding lead overloaded | 9 | Pair with ML on WP06; open-set LDPC at P3 | WP06 late at G2 |
| **K13 [PRD]** | Sim-to-real gap in the deep expert | 9 | Twin-conditioned generation, self-supervised pretraining on real IQ, E3 physics expert, proof above the model | Real-vs-synthetic accuracy gap > 5 points at G3 |

### 12.4 Demo (7 minutes, a fallback for every beat)

| Time | Beat | Judges see | Fallback |
|---|---|---|---|
| 0:00 | The problem | Real Meteor-M recording, noisy waterfall | Screen video |
| 0:30 | Autopilot on real data | Every layer recovered; matches SatDump | Cached results, same UI |
| 1:40 | Proof | Ridge sinks into the noise; certificate prints; near-miss 8PSK rejected on screen | Offline |
| 2:30 | Insufficient data | 0.4 s capture → tasking note; multi-site KiwiSDR stitched → proven | Deterministic offline |
| 3:30 | Mystery signal | Judge picks modulation, interleaver, code, scrambler; rig transmits over cable; SANJAYA recovers all | Judge picks one of 20 sealed files |
| 4:40 | Recipe Compiler | One click: a GNU Radio receiver decodes the live cable stream | Throttled file replay |
| 5:40 | Passport + hidden signal | Only if P2 delivered | Skip |
| 6:30 | Numbers | Independent KPI table with intervals | Printed handout |

---

## 13. Repository layout and engineering rules

```
spacetech/
├── PRD.md                      ← this document
├── HANDOFF.md
├── ui/                         ← built front-end (design frozen); add src/lib/engine.ts only
├── engine/
│   ├── pyproject.toml          ← pinned; wheelhouse/ lock with hashes
│   ├── sanjaya/
│   │   ├── io/                 wav.py · rawiq.py · sigmf.py · sniff.py
│   │   ├── measure/            psd.py · tiles.py · snr.py · baud.py · cfo.py · bandwidth.py · fs.py
│   │   ├── triage/             features.py · model.py
│   │   ├── scene/              cfar.py · cancel.py
│   │   ├── classify/           features.py · deep.py · decodefit.py · fuse.py · conformal.py · openset.py
│   │   ├── demod/              sync.py · carrier.py · equalizer.py · psk_qam.py · fsk.py · msk.py · llr.py
│   │   ├── coding/             interleaver/ · conv/ · rs/ · ldpc/ · scrambler/ · joint.py · peel.py
│   │   ├── bits/               autocorr.py · sync.py · raster.py · crc.py · fields.py
│   │   ├── proof/              synth.py · residual.py · tests.py · nearmiss.py · certificate.py
│   │   ├── sufficiency/ · stitch/ · twin/ · passport/ · genome/
│   │   ├── compile/            grc.py · oot/ (C++ GNU Radio blocks)
│   │   ├── export/             sigmf.py · csv.py · bits.py · pdf.py
│   │   ├── recipe.py           Recipe · Evidence · ProofResult · Certificate + JSON schema
│   │   ├── pipeline.py         orchestrator: hypothesis queue, memoisation, backtracking
│   │   └── api/                server.py · jobs.py · store.py · schemas.py
│   ├── kernels/                C++17 + pybind11: viterbi · ldpc_minsum · gf2
│   ├── gen/                    SANJAYA-Gen (seeded, SigMF + truth JSON)
│   ├── bench/                  KPI harness, oracles (test-only), sealed-set runner, reports
│   └── tests/                  unit + integration; fast suite < 5 min
├── data/                       manifests only in git; captures on disk, SigMF + SHA-256
└── models/                     ONNX files + model cards (training data manifest hash, metrics)
```

**Engineering rules**
- The numerical core is pure: arrays in, arrays and dataclasses out, seeds explicit.
- Every non-trivial estimator ships with a test against an oracle or an analytic case in the same PR.
- No KPI claim goes in any deck unless the bench produced it, with its interval and reproduction hashes.
- Terms: PS words first in every label and API field description (Sampling frequency, Modulation, FEC, Interleaving, De-interleaving, Demodulation, Constellation, Waterfall, Bit stream correlation, Header, Payload).
- Oracles (AFF3CT, liquid-dsp, gr-fec, SatDump, dumphfdl, fldigi) live in `bench/` only and are never shipped.

---

## 14. Open items

| Item | Owner | Needed by |
|---|---|---|
| Confirm SIH 2026 dates, PS details, sponsor and theme on sih.gov.in / with the SPOC | Lead | G0 |
| Confirm assumptions A-01 to A-08 (v3 §2): files vs live, OFDM, finale data, hardware class | Lead | G0 |
| Institute approval for the cabled rig; procurement (Pluto, 2 × RTL-SDR V4, attenuators) | Data | W1 |
| Live status of FUNcube-family and Meteor satellites at recording time | Data | W2 |
| Measured KPIs (all targets in this PRD are pre-registered, not results) | Protocol (independent) | G5 |
