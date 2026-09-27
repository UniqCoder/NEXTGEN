# PRD: Project SANJAYA · v2.4

**Automated analysis of .IQ and .wav recordings with signal parameter extraction, proven end to end**

| | |
|---|---|
| Problem statement | SIH 2026 PS 26147 · Sponsor NTRO · Theme Space Technology · Category Software |
| Document | PRD v2.4, 27 Sep 2026. Software scope only. Review history, deviations and change logs in Appendix A. Supersedes v1.0 (kept as `PRD v1.md` for the record) |
| Governing plan | `winning plan 147 v3.pdf`. Deviations from v3 are marked **[v3 deviation]** and listed in §A.4 |
| Status | UI built (React + three.js, demo data; no desktop shell yet). Engine not started. This PRD is the build contract |
| Conventions | SNR = E<sub>s</sub>/N<sub>0</sub> in the occupied bandwidth. KPIs are pre-registered **targets**, not results. pw = person-week (40 h). Competitor statements are README claims (snapshot 26 Sep 2026). Interface conventions in §6.2 are binding |

---

## At a glance

| | |
|---|---|
| **What** | SANJAYA: an offline tool that turns any .IQ or .wav recording into a **proven** transmitter recipe: sampling frequency, modulation, FEC, interleaving, scrambling, header and payload |
| **Why it wins** | (1) A layered proof and a signed certificate that anyone can re-check in seconds. (2) It says how much more data an open question needs. (3) It pools captures across sensors and locations. (4) It compiles a receiver for designated sensors. None of the 43 competitor READMEs claims any of these |
| **Scope** | 100 % of the PS clauses (R-01 to R-17), each traced to a test and a KPI (§5.3) |
| **Accuracy target** | Nominal envelope: ≥ 90 % of files correct-certified, ≤ 10<sup>−4</sup> wrong-certified, the rest honestly "undecided" with a data-needed note (§3.3) |
| **Intelligence** | Propose and verify: learned experts propose, physics and algebra verify, so a model error costs time, never correctness (§7) |
| **Data** | Four tiers, from exact-truth synthetic data to real signals checked by independent decoders; commit-reveal sealed test sets (§8) |
| **Architecture** | Python + C++ kernels + FastAPI engine on 127.0.0.1; the built React + three.js UI unchanged; Tauri desktop with browser fallback (§6) |
| **Readiness** | No runtime network calls; every fragile dependency has a fallback, tested nightly (§15) |
| **Plan** | 10 weeks from 28 Sep 2026, gates G0-G5. Threshold configuration committed at 73 % schedule confidence; full baseline as the goal (§11) |
| **Evidence** | Key compute and proof claims already measured (§16) |
| **Open** | SIH dates and finale rules (SPOC), Meteor variant (first capture), C++ kernel speed (G1) (§14) |

**Document control.** Owner: team lead. Approvers: all six members and the mentor. Any change to a requirement, KPI, gate or budget creates a new version with an entry in Appendix A. KPI definitions are frozen at G1 (pre-registration).

---

## Contents

1. [Product in one page](#1-product-in-one-page)
2. [Problem, users, jobs, assumptions](#2-problem-users-jobs)
3. [Goals, operating envelope, KPIs](#3-goals-operating-envelope-kpis)
4. [USPs](#4-usps)
5. [Requirements, NFRs, traceability](#5-requirements-nfrs-traceability)
6. [System architecture](#6-system-architecture)
7. [The intelligence: propose and verify](#7-the-intelligence-propose-and-verify)
8. [Beating the data problem](#8-beating-the-data-problem)
9. [Accuracy engineering](#9-accuracy-engineering)
10. [UI integration contract](#10-ui-integration-contract)
11. [Programme: rebaselined plan](#11-programme-rebaselined-plan)
12. [Verification, assurance, risks, demo](#12-verification-assurance-risks-demo)
13. [Repository layout](#13-repository-layout)
14. [Open items and references](#14-open-items-and-references-added-in-v2)
15. [Dependencies and readiness for everything](#15-dependencies-and-readiness-for-everything)
16. [Feasibility evidence](#16-feasibility-evidence-measured-not-prototype)
17. [Glossary](#17-glossary)
- [Appendix A. Review record](#appendix-a-review-record)

---

## 1. Product in one page

**Mission.** Turn any recording from any NTRO sensor into a **proven** transmitter recipe (sampling frequency, modulation, interleaving, FEC, scrambling, frame structure, header and payload), automatically and offline. State what the data can and cannot support, and deliver the recipe to designated sensors as something they can run.

**Thesis: analysis by synthesis, with a layered proof.**

1. Decode the recording to bits.
2. Rebuild the waveform from the decoded bits and subtract it from the recording.
3. Certify each layer with a test that actually has power at that layer:
   - **PHY:** the residual is the noise floor.
   - **Coding:** the demodulated bits satisfy the identified code's parity checks.
   - **Structure:** sync, CRC and counters hold.

   Only then is a signed **Decode Certificate** issued. It lists anything the data could not decide.

**Finding is hard; checking is cheap.** Discovering a recipe may take minutes of search. Verifying a certificate takes seconds (`sanjaya verify file cert.json`), and anyone with the file and the public key can do it, independently of the search. None of the 43 competitor READMEs claims waveform-level verification.

**The loop (already shown in the UI):**

```
1 OBSERVE → 2 MEASURE → 3 HYPOTHESISE → 4 DEMODULATE → 5 UNWRAP → 6 STRUCTURE → 7 PROVE → 8 LEARN
                              ▲                                                    │
                              └────── proof FAIL: next branch of the hypothesis tree ┘
PASS → certificate · (P2: subtract the proven emitter and re-scan for hidden signals)
```

**Minimum winning configuration (P1; committed at the threshold level with 73 % schedule confidence, §11.7):**
- 100 % of the PS: R-01 to R-17, on the bench and on real signals with independent truth.
- C1 layered proof, C2 Data-Sufficiency, C3 Stitching with C4-lite, C5 Recipe Compiler, and R-15 triage.
- A real signal decoded blind end to end and matched against an independent decoder (Meteor-M LRPT vs SatDump).
- Real multi-site stitching (KiwiSDR).

---

## 2. Problem, users, jobs

### 2.1 PS text (verbatim, the acceptance baseline)

> The GUI based model will take .IQ or .wav file as input and: (i) identify signal parameters (Sampling frequency, Modulation, FEC, Interleaving); (ii) demodulate signals (FSK, QAM, PSK); (iii) de-interleave (Block, Convolution, Diagonal, Pseudo Random); (iv) FEC (short-constraint convolutional codes with Viterbi decoding, RS block codes, Concatenated codes, LDPC); (v) bit stream correlation.
>
> **Expected solution:** The expected system should improve feature visibility of signals with the help of GUI, enable automated signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall (time-frequency domain), demodulate signals, carry out de-interleaving and error correction. The output can then be used to carry out correlation of bit stream for identification of header and payload.

| PS complaint (paraphrased) | Answered by |
|---|---|
| Data "often insufficient for fine grain analysis" | C2 Data-Sufficiency, C3 Stitching, D1 soft methods |
| Data "from different sensors and different locations" | C3 Stitching, C4 Sensor Twin |
| Limitation "reduces the accuracy and confidence" | C1 layered proof, D7 trust layer, uncertainty on every value |
| Output "utilised ... in the designated sensors" | C5 Recipe Compiler |

### 2.2 Users and jobs

| User | Context | Job to be done |
|---|---|---|
| Signal analyst (primary) | Air-gapped workstation; expert | "Tell me everything about this recording and show me why you believe it. Tell me when you can't know." |
| Collection manager | Plans recordings | "Is this enough data? If not, what should I record, where and for how long?" |
| Sensor engineer | Runs designated receivers | "Give my sensor a receiver for this signal." |
| Independent checker | Another analyst or site | "Let me check this certificate without trusting your search." |
| SIH judge | Holds the PS text | "Show me every PS clause, in the PS's own words, within 2 clicks." |

### 2.3 Assumptions (confirm with the SPOC; each has a fallback)

| ID | Assumption | If wrong |
|---|---|---|
| A-01 | Analysis of recorded files is the requirement; live reception is a bonus | C5 already produces live receivers; add a live-input path (1 pw from reserve) |
| A-02 | Recordings may lack metadata; the sampling frequency may be unknown | None: both cases are designed for |
| A-03 | Signals of interest are single-carrier; OFDM is not required | OFDM parameter estimation as P2 (1.5 pw) |
| A-04 | Payload decryption is out of scope | Out of scope regardless; structure only |
| A-05 | The finale may use NTRO-provided files of unknown content | Designed for; C2 reports when a file cannot support a decision |
| A-06 | Target hardware is a laptop-class machine with no GPU requirement | GPU path optional; nothing depends on it |
| A-07 | About ten build weeks from now to the finale (reported: 36-hour finale in December) | Ladder (§11.6) down to the threshold configuration |
| A-08 | Six members at about 25 h per week each (37.5 pw) | Re-run the confidence analysis (§11.7); apply the ladder |
| A-09 | Code built before the finale may be shown and extended at the finale | Keep full build history as provenance; the finale's 36 hours go to integration and demo hardening (K21) |
| A-10 | The team's development laptops meet the reference spec (NFR-02) | Heavy jobs (E2 training, false-PASS campaign) run on the institute machine or a GPU (§8.6) |

---

## 3. Goals, operating envelope, KPIs

### 3.1 Goals

| ID | Goal | Measured by |
|---|---|---|
| G-1 | 100 % of PS clauses with verified acceptance | R-01 to R-17 (§5) |
| G-2 | Be right, or say you're unsure; never confidently wrong | Outcome KPI (§3.3), per-certificate false-PASS bound |
| G-3 | Work on real recordings, not only on our own generator | Tier 3 KPIs with independent truth |
| G-4 | Answer the PS's three complaints with capabilities no competitor claims | C1 to C5 at P1 |
| G-5 | Keep the existing UI design unchanged, driven by real data | Visual regression gate (§10) |
| G-6 | Deployable in an intelligence setting | Zero-network proof, fuzzing, SBOM, offline installer |

### 3.2 Non-goals

Payload decryption · LLM chat · cloud, login, telemetry · black-box-only deep learning · speech content or speaker ID · OFDM (P2 on SPOC request, 1.5 pw) · live SDR control as a requirement.

### 3.3 Operating envelope and outcome KPI

| Region | Conditions | Required behaviour |
|---|---|---|
| **Nominal** | Single-carrier; E<sub>s</sub>/N<sub>0</sub> ≥ 10 dB; AWGN or mild multipath; interleaver period N ≤ 1,024 bits; convolutional K ≤ 9; RS n ≤ 255; LDPC from the catalogue; **enough data: ≥ max(10<sup>4</sup> symbols, 3N² coded bits)**, i.e. ≥ 3N interleaver rows (§3.4, D1) | **Correct-certified ≥ 90 %** of files; **wrong-certified ≤ 10<sup>−4</sup>** per certificate (95 % upper bound); the rest "undecided" with a C2 note |
| **Extended** | 6-10 dB, or 10<sup>3</sup>-10<sup>4</sup> symbols, or period ≤ 4,096, or Watterson HF "moderate" | Curves characterised and published; wrong-certified bound unchanged |
| **Outside** | Anything else (OFDM, spread spectrum, unknown long LDPC, ...) | Never certified; honest "undecided" or "out of envelope" with reason |

The **outcome KPI** is the one number an analyst experiences. The proof-driven search (§6.5) is what lifts it above the product of the stage accuracies.

### 3.4 Headline KPIs (pre-registered targets)

| Area | KPI | Target | Rule (§3.5) |
|---|---|---|---|
| Outcome | Correct-certified / wrong-certified, nominal envelope, Tier 1-2 sealed | ≥ 90 % / ≤ 10<sup>−4</sup> | P / S |
| Proof (C1) | False PASS per proof attempt | ≤ 1.5 × 10<sup>−6</sup> (0 in ≥ 2,000,000 near-miss attempts, stratified by layer) | S |
| Proof (C1) | False PASS per certificate (≤ 64 attempts on the deep path, Bonferroni; ≤ 8 on the fast path) | ≤ 10<sup>−4</sup> on both paths (64 × 1.5 × 10<sup>−6</sup> = 9.6 × 10<sup>−5</sup>) | S |
| Proof (C1) | P(PASS \| right recipe) | ≥ 95 % Tier 1-2 nominal; ≥ 80 % Tier 3 real | P |
| Modulation (R-04) | Top-1, 10 classes, ≥ 10 dB, ≥ 1,000 symbols | ≥ 98 % | P |
| Modulation (R-04) | 95 % conformal set coverage, per tier | 95 % CI within [0.93, 0.97], n ≥ 8,000 | C |
| Calibration | Expected calibration error per 2-dB SNR bin | ≤ 0.03 | P |
| Continuous values (R-02, R-03) | Coverage of reported 95 % intervals | 0.95 ± 0.03 | C |
| Sampling frequency (R-02) | P95 error, standard-anchored captures ≥ 10 s | ≤ 10 ppm | E |
| Symbol rate (R-03) | P95 relative error | ≤ 10<sup>−4</sup> | E |
| FEC / interleaver (R-05, R-06) | P<sub>id</sub> at BER ≤ 10<sup>−3</sup> within stated data lengths | ≥ 95 % | P |
| Soft joint ID (R-06, D1) | Interleaver rows needed at BER ≤ 3 × 10<sup>−3</sup>, periods 96-1,024 | ≤ 3N rows (hard rank needs 2N/(1 − p)<sup>N</sup>: at N = 1,024 that is 44,411 rows, so 3N = 6.9 %; the gain is ≤ 10 % whenever N·p ≥ 2.7, and none at N = 96, where hard rank already needs only 256) | E |
| Decoders (R-09) | Gap to reference implementation at FER 10<sup>−3</sup> | ≤ 0.2 dB | E |
| Frames (R-10) | Frame length + sync; field class | 100 % (≥ 20 frames); ≥ 95 % | P |
| Triage (R-15) | Content class, 400 labelled files | ≥ 95 %, < 1 s per file | P |
| Data-sufficiency (C2) | Coverage of the 80 % ΔT interval; median error of P50 | 0.80 ± 0.05; ≤ 30 % | C / E |
| Stitching (C3) | Alignment loss; false merge | ≤ 10 %; ≤ 1 % | E / S |
| Compiler (C5) | Compiled receiver on the source recording | 100 % bit-exact | S |
| Speed (R-12a) | Fast path per 10<sup>6</sup> samples, nominal envelope, reference laptop | < 10 s (P95) | E |
| Interactivity (R-11) | 100 MB file interactive | < 2 s | E |

### 3.5 Acceptance decision rules

| Class | Applies to | Pass if |
|---|---|---|
| **S** safety | False PASS, wrong-certified, false merge, bit-exact | The 95 % upper bound ≤ target (rule of three when 0 events are observed) |
| **P** performance proportion | Accuracies, P<sub>id</sub> | Point estimate ≥ target **and** 95 % Wilson lower bound ≥ target − 2 points; n ≥ 1,000 per condition (half-width ≤ 1.4 points at 0.95) |
| **C** coverage | Conformal sets, intervals | The 95 % CI of empirical coverage lies inside the stated band |
| **E** estimation | Errors in ppm, dB, time | The stated percentile of \|error\| ≤ target over n ≥ 200 runs |

---

## 4. USPs

### 4.1 Where the field stops (README claims, 43 repositories)

| # | Wall | SANJAYA |
|---|---|---|
| 1 | One file at a time | C3 Evidence Stitching |
| 2 | One sensor at a time | C4 Sensor Twin + network clock solution |
| 3 | No answer to "is this enough data?" | C2 Data-Sufficiency Engine |
| 4 | Output ends in a report | C5 Recipe Compiler |
| 5 | Truth from their own generator (33 of 43) | Tier 2-3 real data with independent truth |
| 6 | Coding layer limited to a catalogue | D1 soft joint coding engine |
| 7 | Scramblers not identified | D2 blind scrambler recovery, incl. post-FEC cosets |
| 8 | .wav = stereo IQ or Hilbert of mono | C7 WAV-Lifting (P3) |
| 9 | Bit-level verification at best | C1 layered proof |
| 10 | Models never improve in use | C8 proof-gated flywheel (P3) |

**Why the gap lasts:** the innovations depend on each other (the flywheel needs the proof, stitching needs the Twin and the sufficiency maths, the compiler needs certified recipes). Copying one idea does not reproduce the system.

### 4.2 Crown innovations

#### C1 · Layered Proof-of-Decode and the Decode Certificate · P1 · TRL 2→5 · 2.0 pw

**PS hook:** "reduces the accuracy and confidence of interpretation".

**Design.** Re-encode the decoded information bits through the recovered chain (code → interleaver → scrambler → mapper → pulse shape) and apply the estimated channel (gain, CFO and phase trajectory, timing drift, equaliser taps, and a bounded memoryless PA model with ≤ 6 real parameters when the EVM floor shows compression). Subtract to get the residual r. Near-miss hypotheses get exactly the same model, so the added freedom cannot favour the winning recipe.

| Layer | Test | Statistic and rule |
|---|---|---|
| **PHY** (waveform) | T1 explained energy | η = 1 − (P<sub>r</sub> − P<sub>n</sub>)/(P<sub>x</sub> − P<sub>n</sub>) ≥ η<sub>min</sub> (calibrated) |
| | T2 residual at noise floor | **Equivalence test** (TOST): \|10 log<sub>10</sub>(P<sub>r</sub>/P<sub>n</sub>)\| < δ, δ calibrated (default 0.5 dB) |
| | T3 no cyclostationarity | Cyclic coherence of r at α = 1/T below γ |
| | T4 whiteness, Gaussianity | Residual PSD flatness and first-L autocorrelations, and kurtosis, **compared with the reference noise** within margins, not with an ideal |
| **Coding** | K1 code membership | Unsatisfied-parity-check fraction f on hard decisions vs f<sub>0</sub> = (1 − (1 − 2p̂)<sup>w</sup>)/2 expected under the code (w = check weight, p̂ = pre-FEC BER from the PHY). Under the null f ≈ 0.5; a binomial test over thousands of checks |
| | K2 correction consistency | Corrections made by the decoder lie inside the binomial 99 % interval of N·p̂ (catches a wrong code "correcting" non-errors) |
| | K3 likelihood ratio | Against the uncoded hypothesis and each near-miss code |
| **Structure** | S1-S3 | Sync-word recurrence at a fixed period (chance 2<sup>−L</sup> per frame); CRC pass fraction (chance 2<sup>−r</sup> per frame; 20 of 20 CRC-16 passes by chance: 2<sup>−320</sup>); counters modulo 2<sup>b</sup> |
| | S4 scrambler | Certified only if the descrambled stream passes S2 or matches known fill; otherwise reported as an equivalence class |

**Noise reference, in order of preference:** signal-free time segments in the same file, then guard bands, then the Sensor Twin. If none exists, T1 and T2 are marked "no independent noise reference" and the PHY verdict rests on T3, T4 and K3.

**Verdict.** Each layer is PASS, FAIL or NOT DETERMINABLE (with a reason). The certificate is PASS only when every determinable layer passes, and it lists the undeterminable ones.

**Multiple testing.** The fast path allows at most K = 8 proof attempts per emitter and the deep path at most 64. The per-attempt bound p̂ = 1.5 × 10<sup>−6</sup> (0 false PASS in ≥ 2,000,000 near-miss attempts) keeps every certificate at ≤ 10<sup>−4</sup> on either path. The certificate records K and its own bound K × p̂.

**Certificate contents:**
- Input SHA-256, engine version and configuration hash.
- The recipe, per-layer verdicts, every statistic with its threshold and calibration-set ID.
- The near-miss battery (§9.3) with rejected / not rejected for each.
- K and the resulting bound.
- Analyst overrides, if any, marked **analyst-assisted**.

It is canonical JSON with statistics rounded to declared precision, signed with Ed25519 using an offline per-site key stored in the OS key store. The recipe is bit-exact across machines; statistics agree to the declared precision.

**Verification.** `sanjaya verify` re-runs synthesis and all tests from the file and the recipe in seconds, without the search.

**Honest limits.** Recipes that produce identical waveforms and identical structure cannot be separated, and the certificate says so. At low SNR the coding-layer tests gain power (more corrections to check) while the PHY tests lose it; the per-layer verdicts show which is which.

**Validation.** PASS on Meteor-M LRPT and HFDL must agree with SatDump and dumphfdl.

#### C2 · Data-Sufficiency Engine and collection tasking · P1 · TRL 2→4 · 1.1 pw

**PS hook:** "data is often insufficient".

**Design.** Every open decision keeps a log-evidence ledger over windows. Likelihoods are **tempered** (power τ ≤ 1, fitted on Tiers 1-2 so that the realised decision error matches α), which corrects the overconfidence of misspecified models. The engine decides when the posterior ≥ 1 − α (α = 10<sup>−3</sup>). Otherwise:

- The ledger increments form a random walk with drift D and variance σ² per second of signal.
- ΔT is reported as a **predictive distribution**. P50 ≈ [ln((1 − α)/α) − ln B]/D (Wald); P90 comes from simulating the walk.
- The **tasking note** uses P90 (this replaces v3's ×1.3 margin). It gives centre frequency, occupied bandwidth, minimum complex sample rate (≥ 1.25 × bandwidth), duration, minimum SNR, and the best sensor per the Twin.

**Why it matters (derived).** Hard-decision rank methods need ≈ 2N/(1 − p)<sup>N</sup> error-free rows for an interleaver period of N bits. At p = 3 × 10<sup>−3</sup> and 4.8 kbit/s:
- N = 96 needs **256 rows, 24.6 kbit, 5.1 s** of signal.
- N = 1,500 needs **2.7 × 10<sup>5</sup> rows, 4.1 × 10<sup>8</sup> bits, ~23.6 h** of signal.

This is why D1's target is ≤ 3N rows. Hard rank's cost grows as e<sup>Np</sup>, so the soft method's advantage appears exactly where the data problem bites: large periods and noisy channels (§3.4).

**KPIs:** see §3.4. The companion **decision-rate** KPI is the fraction of nominal-envelope files decided within their length, which must be ≥ 90 %.

#### C3 · Evidence Stitching across captures, sensors and locations · P1 · TRL 2→5 · (WP11)

The same five steps as v3: associate → normalise (Twin) → align → pool log-likelihoods → per-capture proof ejects mis-associations.

**[v3 deviation] P1 covers signals with a sync marker only.** Every P1 real stitching source has one: HFDL, STANAG 4285 and NAVTEX. The unsynchronised phase search is P2.

**Validation:** one HF transmission recorded simultaneously by ≥ 3 KiwiSDRs in different countries, GPS-timestamped.

#### C4 · Sensor Twin and network clock solution · P1-lite / P2-full

- **P1-lite:** sample-clock error and noise floor (level and shape), the two quantities C1 and C3 consume. Learned from signals of opportunity; one GPS-disciplined reference fixes the clock gauge; weighted least squares gives every clock with its uncertainty.
- **P2-full:** IQ imbalance, anti-alias response, phase noise, clipping, and Twin-conditioned training data.
- **Honest limit:** without a reference, only relative clocks are reported.

#### C5 · Recipe Compiler · P1 · TRL 2→5 · 0.8 pw

Takes a **certified** recipe only. Outputs:
- **(a)** A self-contained GNU Radio 3.10 `.grc`: stock gr-digital blocks for the PHY (symbol sync, Costas, constellation decoder, access-code correlator) and **embedded Python blocks** for de-interleaving, RS, CRC and schema-driven framing. Nothing needs compiling and there is no ABI coupling.
- **(b)** A versioned recipe JSON (SigMF-compatible `sanjaya:` namespace).
- **(c)** A recipe-matched detector (coherent gain ≈ 10 log<sub>10</sub> L dB; ≈ 15 dB for a 32-symbol sync word).

**Release gate:** the flowgraph, run on the source recording inside the optional offline **compiler pack** (a pinned GNU Radio 3.10 environment), must reproduce SANJAYA's bits exactly. **P2:** C++ blocks for throughput and the live-rig FER KPI.

#### C6 Emitter Passport (P2) · C7 WAV-Lifting (P3) · C8 Proof-gated Flywheel (P3)

As in v3 §5. C8's label error is restated correctly in §7.6.

### 4.3 Depth USPs

| USP | P1 | Later |
|---|---|---|
| D1 Soft joint coding engine | Soft rank profile; joint interleaver + code; peeling; ambiguity set; coset (post-FEC scrambler) handling; RS basis and depth | Open-set LDPC n ≤ 1,024 (P3) |
| D2 Blind scrambler recovery | Additive, pre-FEC and post-FEC; Berlekamp-Massey + seed search | Self-synchronising (P2) |
| D3 Bit-Lens with CRC solving | Ported from `ui/src/lib/mock.ts`; any CRC solved in GF(2); schema export | — |
| D4 Scene | Detection + channelisation (R-17) | Successive cancellation (P2) |
| D5 Signal Genome | Minimal standards table for Fs back-solve (Tier 3 standards) | ~30 standards (P2) |
| D6 HF robustness | Watterson curves from the generator | Rig emulation, real-HF tuning (P2) |
| D7 Trust layer | Calibration, conformal sets, NOVEL by empty set, uncertainty on every value | Energy + Mahalanobis open-set, Teach, weighted conformal (P2) |

### 4.4 Head-to-head (README claims)

| Capability | ShantanuSomwanshi (9.0) | NaidhruvK (8.8) | Gururaghavendra123 (8.6) | **SANJAYA** |
|---|---|---|---|---|
| PS (i)-(v) chain | Yes | Yes | Yes | **Yes** |
| GUI | Yes | Not evident | Yes | **Yes (built)** |
| Blind interleaver size | Hard rank | Hard rank | Catalogue | **Soft, joint** |
| Proof beyond bit level | No | No | CRC gate | **Layered proof** |
| Third party can re-check the result | No | No | No | **Yes (`verify`)** |
| Data needed for a decision | No | No | No | **Yes** |
| Pools captures and sensors | No | No | No | **Yes** |
| Receiver for sensors | No | No | No | **Yes** |
| Real signal, full chain, independent truth | No | No | No | **Yes** |
| Blind scrambler ID incl. post-FEC | No | Fixed | No | **Yes** |

---

## 5. Requirements, NFRs, traceability

### 5.1 Functional requirements

Verification methods: T test, A analysis, I inspection, D demonstration. Rule classes as in §3.5.

| ID | PS clause | Engine behaviour | Verify | Acceptance |
|---|---|---|---|---|
| R-01 | .IQ or .wav input | WAV (mono real / stereo IQ, 8-32 bit int, float; **WAVE_FORMAT_EXTENSIBLE; RF64/BW64 > 4 GB; `auxi` chunk (fc, start time); KiwiSDR `kiwi` chunk (GPS timestamps)**). Raw IQ sniff over dtype {u8, i8, i16, i32, f16, f32, f64} × endianness × I/Q order, each with a confidence. SigMF 1.x. Manual override. Range-checked headers; files up to 8 GB | T | Correct format on 100 % of 200 bench files ≥ 64 kB at SNR ≥ 0 dB; every ambiguity surfaced; fuzzing clean |
| R-02 | (i) Sampling frequency | Header / SigMF / `auxi`; otherwise back-solved from a standard's symbol clock and the anti-alias edge; declared-vs-measured check | T, A | P95 ≤ 10 ppm (standard-anchored, ≥ 10 s, ≥ 10 dB); otherwise "Fs unknown" and normalised units |
| R-03 | (i) Other parameters | Centre offset, bandwidth, SNR, roll-off, FSK tones and index, burst timing. Symbol rate by **family-specific estimators** (§6.4). **Every continuous value has u and a 95 % interval** | T | Symbol rate P95 ≤ 10<sup>−4</sup> relative; SNR P95 ≤ 1 dB; bandwidth ±5 %; interval coverage 0.95 ± 0.03 |
| R-04 | (i) Modulation | E1 + E2 + E3 fused, calibrated, split-conformal set; NOVEL on an empty set. **P1: BPSK, QPSK, OQPSK, 8PSK, 16QAM, 64QAM, 2/4/8-FSK, MSK** (GMSK P2) | T | Top-1 ≥ 98 % (≥ 10 dB, ≥ 1,000 symbols); coverage and ECE per §3.4 |
| R-05 | (i) FEC | Blind convolutional (rate, K, generators, puncturing), RS (n, k, basis, interleave depth), LDPC catalogue by syndrome, concatenation by peeling; phase-ambiguity aware | T | ≥ 95 % at BER ≤ 10<sup>−3</sup> with ≤ 10<sup>5</sup> coded bits (conv K ≤ 9) and ≤ 10<sup>6</sup> (RS); curves to 10<sup>−2</sup> |
| R-06 | (i) Interleaving | Block, convolutional, diagonal, PN; soft rank profile joint with the code; period pre-screen | T | P<sub>id</sub> ≥ 95 % for periods ≤ 1,024 given ≥ 3N² coded bits (P1), ≤ 4,096 characterised; **decision rate ≥ 90 %** in the nominal envelope; rows needed ≤ 3N |
| R-07 | (ii) Demodulate FSK, QAM, PSK | Feedforward block sync (Oerder-Meyr timing, Viterbi-Viterbi phase) + C++ tracking loops; CMA → DD-LMS equaliser; OQPSK; FSK bank; MSK; **burst mode** (detection, preamble correlation, per-burst acquisition); outputs soft LLRs **plus the ambiguity set** | T | BER within 0.5 dB of theory at 10<sup>−4</sup> (AWGN) per scheme; HF (Watterson) curves; ≥ 99 % burst detection at ≥ 10 dB |
| R-08 | (iii) De-interleave ×4 | Invertible operators from R-06; manual override | T | Bit-exact round trip on 10<sup>4</sup> vectors per type |
| R-09 | (iv) FEC decode ×4 | C++ soft Viterbi (K 3-9, punctured), RS (Berlekamp-Massey, Chien, Forney; dual basis), concatenated, LDPC normalised min-sum | T | ≤ 0.2 dB from liquid-dsp / gr-fec (conv, RS) and AFF3CT (LDPC) at FER 10<sup>−3</sup> |
| R-10 | (v) Bit-stream correlation, header and payload | Autocorrelation, soft sync discovery, raster, entropy, counters, length fields, CRC solved in GF(2); HEADER / PAYLOAD labels | T | Frame length + sync 100 % (≥ 20 frames, BER ≤ 10<sup>−3</sup>); field class ≥ 95 % |
| R-11 | GUI, feature visibility | Existing UI, design unchanged (§10); waterfall, PSD, constellation on first view | D, I | First-load visibility; any clause ≤ 2 clicks; 100 MB interactive < 2 s; visual-regression gate green |
| R-12a | Automated (fast path) | One click to header/payload; tree search with ≤ 8 proof attempts | D, T | P95 < 10 s per 10<sup>6</sup> samples, nominal envelope |
| R-12b | Automated (deep path) | Exhaustive periods to 4,096, LDPC catalogue, scrambler degrees ≤ 23; anytime results with progress | D, T | Best-so-far recipe always available; default cap 10 min, configurable |
| R-13 | GNU Radio, Python, C++ | Python orchestration; C++ kernels; GNU Radio as C5 target and oracle | I | Each used for a stated reason |
| R-14 | Output for designated sensors | Certificate (PDF + JSON), SigMF annotations, bits, header/payload CSV, recipe JSON, `.grc`; certificate verifier | T, D | Bit-exact gate; `verify` reproduces the verdict on a second machine |
| R-15 | Signal-type triage | Digital / voice / CW / noise gate before decoding; abstains on too-short files | T | ≥ 95 % on 400 labelled files; < 1 s |
| R-16 | Headless use and batch | `sanjaya analyze \| verify \| batch \| gen \| bench` on the same pipeline as the API | T | Identical recipe from CLI and API on the bench set |
| R-17 | Detection and channelisation | OS-CFAR on the PSD / spectrogram; per-emitter polyphase down-conversion and decimation; burst segmentation | T | ≥ 95 % of emitters ≥ 6 dB detected; channelised SNR loss ≤ 0.3 dB |

### 5.2 Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Platforms: Windows 10/11 x64, Ubuntu 22.04 / 24.04 x64 |
| NFR-02 | Reference laptop: 8-core x86-64, 16 GB RAM, no discrete GPU; nothing depends on a GPU |
| NFR-03 | Files up to 8 GB, memory-mapped; engine RAM ≤ 4 GB for any file (job memory cap enforced by the OS) |
| NFR-04 | Engine ready ≤ 5 s after app launch; the UI survives engine restart (reconnects, resumes job state) |
| NFR-05 | Zero outbound network packets (packet-capture test); API bound to 127.0.0.1 only |
| NFR-06 | Determinism: same version + file + configuration → identical recipe and canonical certificate body |
| NFR-07 | One offline installer per OS, ≤ 600 MB without the compiler pack, **including the offline WebView2 runtime on Windows**; per-user install without admin rights; compiler pack separate |
| NFR-08 | No crash or hang on any input (fuzzed); every job has cancel and a wall-clock watchdog |
| NFR-09 | Local structured logs with rotation; "support bundle" export to a file; no network |
| NFR-10 | UI: WCAG AA, reduced motion respected, design unchanged (UI_PROMPT.md) |
| NFR-11 | No copyleft code in the shipped engine; copyleft tools used only as test oracles or as separate processes (GNU Radio compiler pack); licence register |
| NFR-12 | Every runtime dependency is pinned by hash, listed in the SBOM with its licence, and loads offline; none makes a network call at runtime (§15.3) |
| NFR-13 | Every dependency that can fail on a target machine has a degraded mode that preserves every verdict; proven nightly by the kill-matrix (§15.5) |

### 5.3 Traceability matrix

| PS clause | Req | Module | WP | Verification | KPI | Scenario step (§12.4) |
|---|---|---|---|---|---|---|
| Input .IQ / .wav | R-01 | `io` | WP01 | T: 200 bench files, fuzzing | Format accuracy | 0:30 |
| (i) Sampling frequency | R-02 | `measure.fs` | WP02 | T, A | P95 ppm | 0:30 |
| (i) Modulation | R-04 | `classify` | WP04 | T | Top-1, coverage, ECE | 0:30, 1:40 |
| (i) FEC | R-05 | `coding` | WP06 | T | P<sub>id</sub> | 0:30 |
| (i) Interleaving | R-06 | `coding.interleaver` | WP06 | T | P<sub>id</sub>, decision rate, rows ≤ 3N | 0:30 |
| (ii) Demodulate | R-07 | `demod` | WP03 | T | BER vs theory | 0:30 |
| (iii) De-interleave | R-08 | `coding.interleaver` | WP05, WP06 | T | Bit-exact | 0:30 |
| (iv) FEC decode | R-09 | `kernels`, `coding` | WP05 | T | dB vs oracle | 0:30 |
| (v) Correlation, header, payload | R-10 | `bits` | WP08 | T | Frame, field | 0:30 |
| GUI, spectral features | R-11 | `ui` | WP15 | D, I | First load, visual regression | 0:00 |
| Automated | R-12a/b | `pipeline` | WP20 | D, T | Fast-path time | 0:30 |
| GNU Radio, Python, C++ | R-13 | all | — | I | — | — |
| Designated sensors | R-14 | `compile`, `export` | WP12, WP21 | T, D | Bit-exact, verify | 4:40 |
| Accuracy and confidence | C1 | `proof` | WP09 | T | False PASS, P(PASS\|right) | 1:40 |
| Insufficient data | C2 | `sufficiency` | WP10 | T | Interval coverage | 2:30 |
| Different sensors and locations | C3, C4 | `stitch`, `twin` | WP11 | T, D | Alignment loss | 2:30 |
| (triage, derived) | R-15 | `triage` | WP19 | T | Accuracy | — |
| (headless, derived) | R-16 | `cli` | WP13 | T | CLI = API | — |
| (multi-signal, derived) | R-17 | `scene` | WP02 | T | Detection, SNR loss | 0:30 |

---

## 6. System architecture

### 6.1 Principles

1. **One central object, the Recipe.** Every field carries its evidence, and the UI, certificate, compiler and sensors all consume it.
2. **Hypotheses, never single answers.** Stages emit ranked candidate sets; a tree search explores them; the layered proof decides.
3. **Pure numerical core, thin shell.** Arrays in, arrays and typed records out; no I/O or hidden state; seeds explicit.
4. **Feedforward first.** Block estimators vectorise, parallelise and reproduce exactly. Recursive loops exist only where tracking needs them, and those are in C++.
5. **Deterministic, offline, least-privilege.**
6. **Classical where exact, learned where it pays, verified always.**
7. **One schema source.** Pydantic models generate OpenAPI and the UI's TypeScript types.
8. **Use proven libraries; stay ready.** Libraries are used wherever they save effort or add performance. Anything that can fail on a target machine has a fallback, and no verdict depends on it (§15).

### 6.2 Interface conventions (binding)

| Item | Convention |
|---|---|
| Complex baseband | `complex64`, normalised so that full scale = 1.0; ingest records the original dtype |
| Frequency | Hz, positive = above centre; spectral inversion is a recorded hypothesis, never silently flipped |
| Time | Sample index as the primary base; UTC (ISO 8601, `Z`) when known; durations in seconds |
| Power | dBFS for levels; dB for ratios; SNR = E<sub>s</sub>/N<sub>0</sub> in the occupied bandwidth |
| Bits | `uint8` 0/1 arrays in the engine; MSB-first for field values; packed only at export |
| Soft bits | LLR = ln P(b = 0)/P(b = 1) (positive favours 0), `float32` |
| Symbols | Gray-mapped constellations per a named mapping table; the rotation and conjugation hypothesis is carried with every symbol stream |
| Polynomials | Octal for convolutional generators (e.g. 171, 133); hexadecimal "normal" form + init + reflect-in/out + xor-out for CRCs; LFSR as a tap list + seed |
| Uncertainty | u = standard uncertainty (k = 1); intervals are 95 % unless stated |

### 6.3 Context

```
 ┌──────────────────────────── Operator workstation (air-gapped) ────────────────────────────┐
 │  ┌───────────────────────┐   HTTP + WS on 127.0.0.1 · token header · Host/Origin checked  │
 │  │ Tauri shell (to build) │ ─────────────────────────────────────────▶ ┌────────────────┐ │
 │  │  or any browser        │   (browser mode: `sanjaya serve` hosts ui/dist itself)      │ │
 │  │  └ React + three.js UI │ ◀──────── JSON + binary tiles/bits ─────── │ Engine API      │ │
 │  │    (built, frozen)     │                                            │  └ job worker   │ │
 │  └───────────────────────┘   spawns + supervises the engine sidecar    │    process(es) │ │
 │                                                                         └───────┬────────┘ │
 │  Recordings (.iq, .wav, .sigmf-meta) ─────────────────────────▶ Workspace store (jobs,     │
 │                                                                   recipes, certificates,   │
 │  CLI: sanjaya analyze | verify | batch | gen | bench ─────────▶   twins, caches, logs)      │
 └────────────────────────────────────────────────────────────────────────────────────────────┘
        │ certificate, recipe JSON, SigMF, bits, CSV, .grc  → designated sensors · tasking note (C2)
```

### 6.4 Engine layers (a layer may import only from layers below it; checked by import-linter in CI)

| Layer | Package | Responsibility |
|---|---|---|
| L0 Kernels (C++17, pybind11) | `kernels` | Soft Viterbi (K 3-9, punctured); LDPC normalised min-sum; bit-packed GF(2) rank and elimination; RS over GF(2<sup>m</sup>) (BM, Chien, Forney, dual-basis maps); tracking loops (DD-LMS, Costas, polyphase interpolator) |
| L1 I/O and forensics | `io` | WAV family, raw IQ, SigMF; sniffing; DC and IQ imbalance; range checks and limits |
| L2 Measurement | `measure` | Welch PSD, LOD spectrogram tiles, SNR (M2M4 + PSD), bandwidth, CFO, roll-off, FSK tones; **family-specific symbol rate** (\|x\|² for linear with α ≥ 0.15; x²/x⁴ lines for MSK-type; phase-derivative transition spectrum for FSK; decode-fit refinement); Fs back-solve; **u and intervals** (segment jackknife, checked against the Cramér-Rao bound on Tier 1) |
| L3 Triage and scene | `triage`, `scene` | R-15 gate; **R-17** OS-CFAR detection, polyphase channelisation, burst segmentation; (P2) cancellation |
| L4 Recognition | `classify` | E1 / E2 / E3 experts, fusion, calibration, conformal sets, NOVEL (§7.2) |
| L5 Demodulation | `demod` | Feedforward block sync + C++ tracking; equaliser; PSK / OQPSK / QAM / FSK / MSK; burst acquisition; soft LLRs + ambiguity set |
| L6 Unwrap (coding) | `coding` | Interleaver ID (4 types, period pre-screen), code ID (conv, RS basis/depth, LDPC catalogue), peeling, scrambler position and recovery, ambiguity resolution; decoders |
| L7 Structure | `bits` | Ported from `ui/src/lib/mock.ts` + CRC solving and field classes |
| L8 Proof | `proof` | Re-synthesis, layered tests, near-miss battery, certificate, signature, verifier |
| L9 Evidence engines | `sufficiency`, `stitch`, `twin`, (P2) `passport` | C2, C3, C4 |
| L10 Outputs | `compile`, `export` | `.grc` with embedded Python blocks; recipe JSON; SigMF; CSV; PDF |
| Shell | `api`, `jobs`, `store`, `cli` | API, job worker processes, workspace store, CLI |

`galois`, AFF3CT, liquid-dsp, gr-fec, SatDump, dumphfdl and fldigi are **test oracles only** and never ship.

### 6.5 Orchestrator: best-first hypothesis-tree search

```
root (file)
 └ emitter e (R-17)                         prune: triage ≠ digital → stop, report
    └ modulation m (+ ambiguity a ∈ rot×conj)  score: fused log-posterior; prune: E3 EVM/likelihood
       └ demodulated LLRs (conditional on m, a)
          └ interleaver (type, period, phase)  candidates from autocorrelation pre-screen
             └ code (family, params, basis)    prune: K1 syndrome weight ≈ 0.5 → drop
                └ scrambler (position, poly, seed)
                   └ structure (frame, sync, CRC)  prune: S1/S2 fail → drop
                      └ PROVE (layered)       ≤ 8 attempts on the fast path
```

- **Expansion order:** accumulated log-posterior plus a cheap optimistic bound for the unexpanded layers (A*-style). Every node is memoised by hash(input slice, upstream recipe fields, stage config), so an Expert override re-runs only its subtree.
- **Pruning tests** are cheap (EVM, syndrome weight, CRC) and are calibrated so that the right branch is pruned in < 10<sup>−3</sup> of cases (measured on Tier 1).
- **Budgets:**
  - Fast path: ≤ 8 proofs, ≤ 2,000 nodes, < 10 s per 10<sup>6</sup> samples.
  - Deep path: ≤ 64 proofs, capped at 10 min, anytime.

  Every proof attempt counts toward the certificate's K.
- **FAIL feedback:** the failing test and layer down-weight the implicated subtree. This is the UI's 7 → 3 loop.
- **Exhausted budget:** report the best partial recipe with per-layer status and C2's ΔT. Never a fabricated answer.

### 6.6 Compute budget (reference laptop, per 10<sup>6</sup> samples, fast path)

The allocations are design targets. The "measured" column comes from the feasibility script (§16) on the team laptop (Intel Raptor Lake, 16 threads, NumPy 2.2). Any stage exceeding 150 % of its allocation is treated as a design issue.

| Stage | Method | Allocation | Measured evidence (§16) |
|---|---|---|---|
| Ingest + LOD tiles | memmap, FFT | 0.8 s | **0.62 s for a whole 100 MB file** (25 M samples, 1,024 bins) |
| Detection + channelisation | OS-CFAR, polyphase DDC | 0.5 s | — |
| Measurement | Welch, cyclic lines, jackknife | 0.7 s | Feedforward timing estimate: **0.011 s per 10<sup>6</sup>** |
| Recognition (top-3 hypotheses) | E1 + E3; E2 on 32 windows (ONNX) | 1.5 s | — |
| Demodulation | Feedforward, vectorised; loops | 1.0 s | Simple feedback loop in pure Python: **0.25 s per 10<sup>6</sup>**; only multi-tap LMS goes to C++ |
| Coding (fast) | ≤ 16 period candidates; rank on ≤ 2k × 2k; C++ Viterbi and RS | 3.0 s | GF(2) rank 2,048 × 1,024 in NumPy: **0.069 s**. NumPy Viterbi fallback: **0.15 Mbit/s**, 0 errors at 6 dB |
| Structure | FFT autocorrelation; GF(2) CRC solve | 0.5 s | — |
| Proof (≤ 8 attempts) | Re-synthesis + tests | 1.5 s | — |
| **Total** | | **9.5 s** | |

Exhaustive rank search to period 4,096 with the NumPy fallback, extrapolated from the measured n<sup>1.72</sup> fit (256-1,024): **≈ 0.3 h**. That is why the deep path is anytime and capped, and why the C++ GF(2) kernel must be ≥ 2× faster than NumPy for the 10-minute cap (checked at G1).

### 6.7 Data model

```python
# Pydantic models → OpenAPI → ui/src/lib/engine.types.ts (openapi-typescript)
Method = Literal["blind", "library", "manual"]
Raw = float | int | str | list[int] | dict[str, float | int | str]      # typed, schema-validated

class Evidence(BaseModel):
    key: str; label: str                      # PS wording first
    value: str; unit: str | None; raw: Raw
    u: float | None                           # standard uncertainty (continuous values)
    interval95: tuple[float, float] | None
    method: Method
    conf: float | None                        # calibrated probability (categorical values only)
    cands: list[tuple[str, float]] | None
    conformal_set: list[str] | None
    stage: int; text: str; plot: str | None

class LayerVerdict(BaseModel):
    layer: Literal["phy", "coding", "structure"]
    verdict: Literal["pass", "fail", "not_determinable"]
    reason: str | None; stats: dict[str, float]; thresholds: dict[str, float]; calibration_id: str

class Certificate(BaseModel):
    id: str; issued_utc: str; engine_version: str; config_hash: str; input_sha256: str
    recipe: Recipe; layers: list[LayerVerdict]; near_misses: list[NearMiss]
    attempts_k: int; false_pass_bound: float; equivalences: list[str]
    analyst_overrides: list[Override]; signature: str; key_id: str
```

The recipe JSON schema is semantic-versioned. Canonical JSON uses sorted keys and fixed decimal precision per statistic, and the signature covers the canonical body.

### 6.8 API and security

| Method | Route | Purpose |
|---|---|---|
| POST | `/v1/jobs` | Open by path (desktop) or upload (dev); overrides |
| GET / WS | `/v1/jobs/{id}`, `/v1/jobs/{id}/events` | 8 stage statuses, loop-back, proof state; progress events over WebSocket (token in the first message, Origin checked) |
| GET | `/forensics`, `/triage`, `/scene`, `/params`, `/unwrap`, `/bits`, `/sufficiency`, `/genome` | Page data (§10.3) |
| GET | `/spectrogram?kind=full\|resid\|fail&lod=n`, `/psd`, `/constellation`, `/eye`, `/instfreq`, `/rowpower` | Binary tiles; shape, dB window and axes in headers |
| POST | `/override`, `/prove`, `/compile`, `/v1/stitch`, `/v1/verify` | Actions |
| GET | `/certificate.json\|.pdf`, `/export/{sigmf\|bits\|csv\|recipe\|grc}` | Outputs |

- **Security:** bound to 127.0.0.1. The **Host** header must equal `127.0.0.1:<port>`, which blocks DNS rebinding. **Origin** must be on an allowlist (the Tauri origins; `http://localhost:5173` in dev only). A per-launch token travels in the `X-Sanjaya-Token` header (never a cookie). No CORS wildcard. All four are tested in acceptance.
- **Server:** FastAPI on uvicorn, bound to 127.0.0.1. Request validation, OpenAPI docs and WebSockets come built in. Binary tiles are streamed from memory maps.
- **Contract:** Pydantic models → OpenAPI → `ui/src/lib/engine.types.ts` (generated with openapi-typescript). A CI contract test validates live responses against the OpenAPI schema.

### 6.9 Process, storage, packaging

- **Processes:** the API process plus one **worker process per job**, killable on cancel or timeout, with a memory cap (Windows Job Object via `ctypes`; Linux `resource.RLIMIT_AS`; both stdlib) and a wall-clock watchdog. Inside a worker, a thread pool runs GIL-releasing kernels over shared memory maps.
- **Workspace:** one folder per job holding an input reference (path + SHA-256), `recipe.json`, the certificate, SigMF annotations, stage caches and logs. Stage caches on disk let a job resume after a crash or power loss. Twins live in `twins/<sensor>.json`. The signing key lives in the OS key store via `keyring` (Windows Credential Manager, Linux Secret Service); fallback is a 0600 key file.
- **Packaging:** the Tauri 2 shell (to be created in `ui/src-tauri`) runs a PyInstaller one-folder engine as an `externalBin` sidecar, with an offline wheelhouse pinned by hash, a CycloneDX SBOM and signed installers.
  - On Windows the installer uses Tauri's **offline WebView2 mode** (the default downloads a bootstrapper from the internet) and a per-user install mode (no admin rights).
  - The compiler pack is a separate optional installer.
  - A **freeze spike in Phase 1** proves the sidecar builds on both OSs before any feature depends on it.
  - Fallbacks: a **browser mode** (`sanjaya serve` hosts `ui/dist` on 127.0.0.1 and opens any local browser), a portable folder, and running from source (`python -m sanjaya`). See §15.6.

---

## 7. The intelligence: propose and verify

### 7.1 Where the edge is

SANJAYA is a **propose-and-verify** system: learned models propose, and physics and algebra verify. The proposers make the search fast; the verifiers make it right. A proposer can reorder the search but never decide the outcome, so a model error costs time, not correctness. What no competitor has:

1. **A physics expert immune to the sim-to-real gap** (E3 decode-fit likelihood). At the P1 KPI operating point (≥ 10 dB, ≥ 1,000 symbols), the likelihood-based classifier is the optimal approach when the channel model holds (Dobre et al. 2007). Cumulant features alone separate 16QAM from 64QAM poorly (C<sub>42</sub> ≈ −0.68 vs −0.62; Swami and Sadler 2000); the likelihood uses the full constellation shape.
2. **A layered verifier above every model** (C1).
3. **Rate-normalised inputs:** symbol rate and CFO are estimated classically first, so the network always sees a fixed samples-per-symbol.
4. **Calibration, conformal sets and continuous uncertainties** as first-class outputs, validated on real data.
5. **Proof-gated self-labelling** (C8), so the models keep improving on real data without human labels.

### 7.2 Modulation recognition

| Expert | Input | Model | Class |
|---|---|---|---|
| E1 feature | Cumulants C<sub>40</sub>, C<sub>41</sub>, C<sub>42</sub>, C<sub>61</sub>, C<sub>63</sub>; M-th power lines (M = 2, 4, 8); cyclic features; amplitude and phase statistics; instantaneous-frequency histogram | Gradient-boosted trees → ONNX | P1 |
| E2 deep | Rate-normalised baseband (8 samples/symbol, 1,024-sample windows; I/Q + amplitude/phase) + 32 × 32 constellation density after timing recovery; trained with ±1 % rate and ±0.05·Rs CFO errors | 1-D ResNet + 2-D CNN, late fusion, < 3 M parameters → ONNX (if ONNX Runtime fails to load, classification falls back to E3, §15) | P1 supervised; self-supervised pretraining P2 (first activated) |
| E3 decode-fit | Per candidate: synchronise under the hypothesis; Gaussian-mixture log-likelihood of the symbols at the estimated SNR; FSK tone-bank likelihood | None (physics) | P1 |

**Trust layer:**
- Per-expert temperature scaling.
- Logistic stacking on a separate split.
- Windows summed as log-likelihoods, which feed C2's ledger.
- Split-conformal (APS) sets **calibrated on Tier 2 + truth-labelled Tier 3**, with class-conditional (Mondrian) and SNR-binned coverage reported per tier.
- **P1 NOVEL** = an empty set, or the top probability < 0.5 inside a 95 % set larger than 3.
- **P2:** energy + Mahalanobis open-set, few-shot Teach (~5 examples → prototype), and weighted conformal under covariate shift (Tibshirani et al. 2019).

**Training:**
- SANJAYA-Gen with impairments sampled from **measured** Twins; SNR curriculum from −6 to +30 dB.
- Fine-tune on HIL rig data, then on proof-gated real labels (P3 flywheel).
- Self-supervised data (P2) is biased toward KiwiSDR HF and SatNOGS audio. That bias is stated, and it is countered with rig UHF and RTL-SDR VHF captures.
- Reports: reliability diagrams, ECE per SNR bin, and accuracy vs SNR, symbols and impairment, all with Wilson intervals, separately per tier.

### 7.3 Triage (R-15)

The in-browser `triage.ts` is ported one-to-one as the baseline. Its features (symbol-rate line, frame-to-frame level variation, spectral flux, single-line energy, 4 Hz syllabic envelope, on/off keying) feed a small GBDT exported to ONNX; the ported rule-based `triage.ts` remains as the fallback. It abstains on files too short for a verdict.

### 7.4 Coding layer: algebra with the hard cases handled

- **Ambiguity set (PR-04).** Every demodulated stream carries {rotation k·2π/M} × {conjugation}. The code test K1 resolves it when the code is not transparent to the rotation. Transparent cases, such as K=7 (171,133)<sub>8</sub> under inversion (both generators have odd weight), are resolved by sync word, CRC, or differential-coding detection.
- **Joint interleaver + code (D1).** Soft rank profile with reliability-weighted rows and soft syndrome likelihood (Valembois; Sicot-Houcke-Barbier; Marazin-Gautier-Burel). The period is pre-screened by bit autocorrelation. There are dedicated detectors for block, convolutional (staircase), diagonal, and PN (seed library).
- **Scrambler position (PR-07).**
  - *Pre-FEC:* codewords stay codewords.
  - *Post-FEC, frame-synchronous:* received rows are c<sub>i</sub> ⊕ p, so rank analysis runs on **row differences** (which lie in the code), and p is then recovered by Berlekamp-Massey.
  - *Post-FEC, free-running:* joint cyclic-code + scrambler identification (Ding et al., IET Communications 2026).
  - *PHY scrambling:* handled at the symbol level.
- **Convolutional:** dual-code search for (n, k, K), generators and puncturing.
- **RS:** Galois Field Fourier Transform root test over GF(2<sup>m</sup>) with **basis ∈ {conventional, CCSDS dual}** and **interleave depth I ∈ {1..8}**, confirmed by decode rate. Meteor LRPT uses CCSDS-style RS(255,223), I = 4, with the randomiser after RS encoding; to be confirmed against SatDump's implementation.
- **LDPC:** catalogue identification by syndrome weight (DVB-S2, CCSDS, 802.11, 5G NR base graphs); open-set short codes at P3.
- **Concatenated codes:** peel the inner code first, then identify the outer code.

### 7.5 C2 as tempered Bayesian bookkeeping

See §4.2 C2. C2 reads the ledgers the other stages already write; it is not a separate model.

### 7.6 Flywheel label error (C8, P3)

The admitted-label error is P(wrong | PASS) = P(PASS | wrong)·P(wrong)/P(PASS). This is bounded by the per-certificate false-PASS bound divided by the observed PASS rate (≈ 10<sup>−4</sup>/0.9 at nominal). The safeguards from v3 stand: a frozen golden set, rollback on a > 1-point drop, class quotas, an active-learning queue, and no network.

---

## 8. Beating the data problem

### 8.1 Problem A: not enough training data

| Lever | What | Why it works |
|---|---|---|
| 1 Generate with exact truth | SANJAYA-Gen (§8.2) | Every PS combination, incl. LDPC, diagonal and PN, which public datasets lack |
| 2 Make synthetic look real | Impairments sampled from **measured** Twins (rig, KiwiSDR, RTL-SDR, Pluto) | The sim-to-real gap narrows to impairments we have measured |
| 3 Real hardware, exact truth | Tier 2 cabled rig | Real DACs, ADCs and oscillators |
| 4 Real signals, independent truth | Tier 3 (§8.3) | Truth we did not create |
| 5 Physics where data is thin | E3 and the algebraic coding layer need no training | The riskiest decisions do not depend on the dataset |
| 6 Let the proof label | C8 (P3) | Label error bounded (§7.6) |
| 7 Unlabelled real data | Self-supervised pretraining (P2, first activated) | Representation adapted to real front-ends |
| 8 Measure the gap | Every KPI reported per tier; out-of-distribution splits (§8.5) | The gap is a tracked number |

### 8.2 SANJAYA-Gen

Deterministic and seeded. It writes SigMF plus a truth JSON and **taps at every layer**: information bits, framed bits, scrambled bits, coded bits, interleaved bits, symbols, clean baseband, impaired baseband, and ideal-sync LLRs. The taps let every work package develop against its own input without waiting for the stage upstream (§11.5).

| Axis | Range |
|---|---|
| Modulation | BPSK, QPSK, OQPSK, 8PSK, 16QAM, 64QAM, 2/4/8-FSK, MSK (GMSK, π/4-DQPSK, AFSK in Gen v2) |
| Rates | 50 Bd - 1 MBd; 1.25-20 samples/symbol incl. non-integer |
| Shaping | RRC / RC α 0.05-0.5; Gaussian BT 0.3-0.5; rectangular |
| Channel | SNR −6 to +30 dB; CFO ±0.2·Rs; timing; phase noise; Watterson (ITU-R F.1487); multipath; bursts with preambles |
| Front-end | Twin-sampled clock ±50 ppm, IQ imbalance, DC, AA filter, 8/12/16-bit, clipping, AGC, spectral inversion, I/Q swap |
| FEC | Conv K 3-9, rates 1/2, 1/3, punctured 2/3 and 3/4; RS n ≤ 255 (both bases, I 1-8); RS ∘ CC; LDPC (DVB-S2 short, CCSDS, 802.11) |
| Interleaving | Block ≤ 4,096, convolutional, diagonal, PN |
| Scrambling | Additive pre-FEC and post-FEC (frame-synchronous and free-running); self-synchronising (Gen v2) |
| Framing | Sync 8-64 bits, counters, length and type fields, CRC-8/16/32 with any polynomial and init |
| Formats | Every R-01 dtype × endianness × I/Q order; WAV variants incl. RF64, `auxi`; with and without SigMF |

### 8.3 Real data and truth rules

| Signal | Use | Truth | Rule |
|---|---|---|---|
| **Meteor-M N2-3 / N2-4 LRPT**, 137.9 MHz | Full chain: OQPSK (reported; confirm), conv r = 1/2 K = 7, CCSDS randomiser, RS(255,223) I = 4, framing | SatDump decode | Headline real signal; variant confirmed from our first capture |
| HFDL | PSK ×3, FEC, interleaving, **bursts** | dumphfdl | Full chain |
| STANAG 4285 | PHY: 8PSK/QPSK/BPSK, equaliser, HF fading | Known preamble and probe symbols | **PHY KPIs only** (payloads usually encrypted; no coding truth) |
| NAVTEX / SITOR-B | FSK, framing | fldigi | Full chain |
| Multi-site KiwiSDR | C3, C4 | GPS timestamps | Same transmission, ≥ 3 countries |
| SGP4 Doppler | C4, R-02, R-03 | Public TLEs | Physical truth for estimators |
| ADS-B | C6 (P2) | ICAO address | Traits only |
| AO-40-FEC satellites, QO-100 | P2 / stretch | gr-satellites; beacon parameters | — |

**Legal and ethics (from v3):** conducted transmission only; public broadcasts only; payloads never decrypted or displayed; identities used only as truth labels; KiwiSDR operators' limits respected and credited.

### 8.4 Problem B: not enough data in the recording

Need less data (D1 soft joint ID, ≤ 3N rows) · use all of it (sequential evidence, decode-fit) · pool across files (C3) · remove sensor differences first (C4) · state how much more is needed (C2, P90) · never fake a decision (outcome KPI).

### 8.5 Test integrity

- **Commit-reveal.** At G1 the verifier publishes the SHA-256 of the sealed-set seeds and of each Tier 2-3 sealed capture as it is recorded; the content is revealed at G5. This proves no tuning on test data.
- **Out-of-distribution splits:**
  - Held-out parameter regions (roll-off, SNR, impairments not seen in training).
  - Held-out sensors (at least one rig receiver and one KiwiSDR site never used for training).
  - A held-out real-signal family.
- **Independence:** a member who did not build a module runs its sealed sets.
- **Reproducibility:** every run records the code version, configuration hash, manifest hash and seeds.

### 8.6 Storage and training compute

| Item | Size or cost (derived) | Decision |
|---|---|---|
| Meteor pass, 12 min at 288 ksps (4 samples/symbol at 72k), complex int16 | 288,000 × 4 B × 720 s ≈ **0.83 GB** per pass | Keep ~20 passes (~17 GB) |
| KiwiSDR IQ, 12 kHz, 16-bit complex | 48 kB/s ≈ **173 MB per hour** | Keep all |
| Rig captures (Tier 2), 1 Msps complex int16, 60 s | ≈ **240 MB** each | Keep ~100 (~24 GB) |
| Synthetic training data for E2 | 2 M windows × 1,024 × 8 B ≈ 16 GB if stored | **Not stored:** generated on the fly from recorded seeds (Gen is deterministic); only manifests are kept |
| Sealed test sets | ~1,000 files × ~10 MB ≈ 10 GB | Held by the verifier; SHA-256 committed at G1 |
| **Total** | **≈ 60-80 GB** | One 1 TB external SSD plus a second copy |
| Training E2 (< 3 M parameters) | ≈ 0.75 GFLOP per window (forward + backward) × 2 M windows × 10 epochs ≈ 1.5 × 10<sup>16</sup> FLOP. That is **~1 h on one consumer GPU**, or ~40 h on CPU | Institute or team GPU; CPU fallback over two nights on a halved dataset |
| Trees (E1, triage) | Minutes on CPU | Any laptop |

---

## 9. Accuracy engineering

### 9.1 Level 1: independent cross-checks

| Parameter | Primary | Independent check | On disagreement |
|---|---|---|---|
| Sampling frequency | Header / SigMF / `auxi` | Anti-alias edge; standard's symbol clock | Flag "metadata mismatch"; use the measured value with u |
| Symbol rate | Family-specific cyclic line | Timing-loop convergence; decode-fit peak | Wider u; both shown |
| CFO | M-th power line | Tracking residual | Re-acquire narrower |
| SNR | M2M4 | In-band vs out-of-band PSD | Report the range |
| Modulation | E1 + E2 | E3 + layered proof | The proof decides |
| Code / interleaver | Soft rank | K1 syndrome, CRC | Next branch |
| Frame / CRC | Autocorrelation + sync | CRC over all frames | Per-column confidence |

### 9.2 Level 2: never collapse early

The tree search keeps every calibrated alternative. A wrong early choice costs time, not the answer.

### 9.3 Level 3: layered proof and near-miss battery

Each layer is certified by a test with power at that layer (§4.2 C1). The near-miss battery generated for every certificate is:

| Layer | Near-misses |
|---|---|
| PHY | Neighbouring modulations (QPSK ↔ OQPSK ↔ 8PSK ↔ π/4-QPSK); roll-off ±0.1; symbol rate ±10<sup>−3</sup>; rotated / conjugated symbol maps |
| Coding | Uncoded; same K with other generators; K ± 2; rate and puncturing variants; interleaver period ±1, ×2, ÷2, and phase shifts; RS (n, k), basis and depth neighbours |
| Structure | Scrambler polynomial neighbours and seed shifts; CRC variants; frame length ±8 bits |

### 9.4 Level 4: confidence that means what it says

- Calibration (ECE per SNR bin) and conformal coverage per tier on real data.
- **u and 95 % intervals** on every continuous value, with interval coverage as a KPI.
- Method tags on every value (Blind-recovered / Matched from library / Manually set).
- Abstention: "Fs unknown", "undecided + ΔT", "high-entropy payload, likely encrypted; decryption is out of scope".

### 9.5 Level 5: measured, not asserted

- Oracle unit tests.
- Pre-registered metrics and decision rules (§3.5).
- A CI regression gate that blocks a merge if a KPI leaves its previous interval.
- Independent runs on commit-revealed sealed sets.
- Reproduction hashes on every number.

### 9.6 Error-propagation budget

| Upstream error | Symptom | Recovery |
|---|---|---|
| Symbol rate off | Timing drift, EVM rising through the file | Tracking; decode-fit refinement; PHY proof fails if unresolved |
| Wrong modulation | High EVM, K1 ≈ 0.5 | Pruned or proof FAIL → next branch |
| Wrong ambiguity branch | K1 fails (non-transparent) or S1/S2 fail (transparent) | Next ambiguity branch |
| Wrong interleaver phase or period | K1 ≈ 0.5 | Phase / period search |
| Wrong code | K1 ≈ 0.5 or K2 inconsistent | Next candidate |
| Post-FEC scrambler not modelled | Rank analysis finds nothing on raw rows; succeeds on row differences | Scrambler-position branch |
| Scrambler wrong | S2 fails; waveform still passes | Next scrambler; otherwise report the equivalence |
| Insufficient data | Posterior below 1 − α | C2 ΔT (P90); C3 stitching |

---

## 10. UI integration contract

### 10.1 Rules

1. **The design is frozen.** Tokens, layout, typography, colours, motion, the 5-step flow, the Tools menu and the terrain stay as built.
2. **Permitted change class: data binding with zero visual change.** Scenario constants become values read from engine metadata. Nothing else changes.
3. **Acceptance: visual regression.** Playwright screenshots of every page on the demo scenario, both themes, three viewport sizes, before and after the refactor. At most 0.1 % of pixels may differ (anti-aliasing tolerance). This runs in CI.
4. `mock.ts` stays as the offline demo data source behind the same adapter (demo fallback beats rely on it).
5. The browser-side analysis stays for instant feedback on drop; the engine's answer replaces it and is never shown next to it.

### 10.2 Hard-code inventory (to bind to engine metadata)

| File | Scenario-bound constants |
|---|---|
| `components/Terrain.tsx` | dB window `LO = −110`, `RANGE = 60` compiled into GLSL (→ uniforms); `(f + 24000)/48000` frequency mapping; duration-based time ticks (`SCENARIO.file.duration`); defaults floor −104 / span 44; emitter labels and `y >= 24` start row |
| `components/Waterfall.tsx` | `SPEC.bins/rows/fs`, duration |
| `components/Plots.tsx` | `SPEC` grid; `(f + 24000)/48000` mapping; `y >= 24` start row |
| `components/Palette.tsx` | SigMF export hard-codes `ci16_le` and 48,000 Hz (→ the engine's `/export/sigmf`) |
| `lib/store.ts` | `prove()` decides the verdict from `SCENARIO`; `runAutopilot()` uses timers (→ WS events and the engine verdict) |
| Frequency axis (all plots) | Assumes complex ±fs/2; a real-valued WAV needs 0 to fs/2 |
| 15 files | `import ... from '../lib/mock'` (→ `engine.ts` with identical export names and types) |

### 10.3 Page → engine map

| Page | PS clauses | Engine data |
|---|---|---|
| Recording | Input, format path, overrides | jobs, forensics, triage |
| Signal | Sampling frequency, waterfall, PSD, constellation / FSK views, modulation | spectrogram, psd, constellation, eye, instfreq, params |
| Decoding | Demodulation, de-interleaving ×4, FEC ×4, scrambler | unwrap, params |
| Header & payload | Correlation, HEADER / PAYLOAD | bits |
| Proof + Certificate | Accuracy and confidence | prove (layer verdicts), spectrogram `resid`/`fail`, sufficiency, certificate, compile, verify |
| Scene · Standards · Challenge · Compliance | Extras | scene, genome, jobs; Compliance static |

---

## 11. Programme: rebaselined plan

**Capacity:** 6 members × 25 h/week × 10 weeks = 37.5 pw; per role 0.625 pw/week, which is **1.25 pw per two-week phase**.

### 11.1 Rebaselined WBS (P1)

| WP | Content | v3 pw | Δ | v2 pw | Owner |
|---|---|---|---|---|---|
| WP01 | Ingest + forensics + WAV variants | 1.0 | +0.2 | 1.2 | Data (from DSP) |
| WP02 | Measurements, family-specific rate, u/intervals, Fs back-solve, **R-17 detection/channelisation** | 1.5 | +0.9 | 2.4 | DSP |
| WP03 | Receivers PSK/OQPSK/QAM/FSK/MSK, feedforward sync, equaliser, **bursts** (GMSK → P2) | 3.0 | +0.2 | 3.2 | DSP |
| WP04 | E1/E2/E3, calibration, conformal on real data (GMSK → P2) | 1.5 | +0.2 | 1.7 | ML |
| WP05 | C++ kernels: Viterbi, GF(2), **RS (runtime)**, LDPC, **tracking loops**; NumPy reference path selectable as fallback | 2.5 | +0.6 | 3.1 | Coding |
| WP06 | Blind coding: interleavers ×4, codes, peeling, **ambiguity set** | 3.5 | +0.2 | 3.7 | Coding 2.7 + ML 1.0 |
| WP07 | Scrambler: additive pre/post-FEC (**coset**); self-sync → P2 | 1.0 | 0.0 | 1.0 | Protocol |
| WP08 | Bit-Lens + CRC solving (**port from TS**) | 1.5 | −0.3 | 1.2 | Protocol |
| WP09 | C1 **layered** proof + certificate | 1.5 | +0.5 | 2.0 | ML |
| WP10 | C2 tempered, predictive ΔT | 1.0 | +0.1 | 1.1 | ML |
| WP11 | C4-lite (clock, noise) + C3 (sync-marker signals) | 2.0 | −0.6 | 1.4 | Data |
| WP12 | C5 `.grc` + embedded Python + compiler pack + gate (C++ blocks, live FER → P2) | 1.5 | −0.7 | 0.8 | Product |
| WP13 | Gen with taps, bench, CI, CLI | 2.0 | +0.1 | 2.1 | Protocol |
| WP14 | Real data (AO-40 → P2) | 2.0 | −0.2 | 1.8 | Data |
| WP15 | UI adapter, **data-binding refactor, visual regression**, schema codegen | 1.5 | +0.6 | 2.1 | Product |
| WP16 | Assurance + **Tauri shell, sidecar, installers**, Host/Origin | 1.5 | +0.6 | 2.1 | Product |
| WP17 | Independent verification (commit-reveal) | 1.0 | 0.0 | 1.0 | Protocol* |
| WP18 | **Operational acceptance testing** (end-to-end runs on the frozen build, §12.4) + analyst guide and in-app help | 1.0 | 0.0 | 1.0 | Data |
| WP19 | Triage (**port `triage.ts`**) | 0.7 | −0.3 | 0.4 | Data (from ML) |
| WP20 | **Orchestrator** (tree search, memoisation, budgets) | — | +0.4 | 0.4 | Protocol |
| WP21 | **Canonical certificate + verifier** | — | +0.2 | 0.2 | Product |
| WP22 | **Readiness and degraded modes** (v2.2): offline WebView2 + browser mode 0.15; portable / source fallback 0.1; kill-matrix CI 0.2 | — | +0.45 | 0.45 | Product |
| | **P1 total** | **31.2** | **+3.15** | **34.35** | reserve **3.15 pw (8.4 %)** |

\* The protocol lead coordinates independent verification but never verifies WP07, WP08, WP13 or WP20, which they build.

**Arithmetic:**
- v2.0: gross additions 5.6 pw − reuse and descoping 3.0 pw = +2.6 pw (33.8 pw, 9.9 % reserve). Without the descoping, P1 would have been 36.8 pw with a 1.9 % reserve, which is not a plan.
- v2.2 adds 0.55 pw of readiness (§15.7): WP22 0.45 + WP05 fallback wiring 0.1. That gives 34.35 pw and a 3.15 pw (8.4 %) reserve, above the 2.0 pw floor. The added work retires scored risks K03, K12 and K20.

**P2 is an unfunded stretch.** A P2 item starts only if, at G3, the schedule performance index is ≥ 1.0 **and** ≥ 2.0 pw of reserve stays untouched for P1 risk until G5. Activation order: GMSK → self-supervised pretraining → coding-layer learned proposer → D4 cancellation → C4-full → C6 → self-synchronising scramblers → C3 unsynchronised → C5 C++ blocks and live FER.

### 11.2 Role × phase loading (pw; ≤ 1.25 per cell)

| Role | Ph1 W1-2 | Ph2 W3-4 | Ph3 W5-6 | Ph4 W7-8 | Ph5 W9-10 | Total |
|---|---|---|---|---|---|---|
| DSP | 1.25 | 1.25 | 1.25 | 1.25 | 0.60 | 5.60 |
| Coding | 1.25 | 1.25 | 1.25 | 1.25 | 0.80 | 5.80 |
| Protocol | 1.25 | 1.25 | 1.25 | 1.20 | 0.75 | 5.70 |
| ML | 1.25 | 1.25 | 1.25 | 1.25 | 0.80 | 5.80 |
| Product | 1.25 | 1.00 | 1.25 | 1.20 | 0.95 | 5.65 |
| Data | 1.25 | 1.25 | 1.25 | 1.25 | 0.80 | 5.80 |
| **Planned** | **7.50** | **7.25** | **7.50** | **7.40** | **4.70** | **34.35** |
| Capacity | 7.50 | 7.50 | 7.50 | 7.50 | 7.50 | 37.50 |
| Reserve | 0.00 | 0.25 | 0.00 | 0.10 | 2.80 | 3.15 |

**Reading:** Phases 1-4 run at 99-100 % load, and the reserve is held as schedule margin in Phase 5, before the final gate. Any slip consumes verification and acceptance-test time first. That is why the descoping triggers in §11.6 are mechanical rather than discretionary.

**Cell content:**

| Role | Ph1 | Ph2 | Ph3 | Ph4 | Ph5 |
|---|---|---|---|---|---|
| DSP | WP02 PSD/SNR/rate/CFO 0.75; WP03 PSK feedforward 0.5 | WP03 QAM/OQPSK + equaliser 0.85; WP02 R-17 0.4 | WP03 FSK/MSK 0.6; WP02 constant-envelope rate + Fs back-solve 0.65 | WP03 bursts + HF + Tier 3 tuning 1.0; WP02 u/intervals 0.25 | WP03 0.25 + WP02 0.35: performance to budget, fixes |
| Coding | WP05 Viterbi, GF(2), tracking loops 1.25 | WP06 block/conv interleavers + conv ID 1.0; WP05 RS 0.25 | WP06 RS ID (basis, depth), peel, ambiguity 0.85; WP05 RS/concat 0.4 | WP05 LDPC min-sum 0.75; WP06 LDPC catalogue 0.5 | WP05 0.45 (incl. NumPy fallback wiring 0.1) + WP06 0.35: performance to budget, fixes |
| Protocol | WP13 Gen v1 (taps), bench, CI, CLI 1.25 | WP08 port + CRC solve 0.6; WP07 additive 0.25; WP20 orchestrator 0.4 | WP07 post-FEC coset 0.75; WP08 fields 0.5 | WP13 Gen v2 0.85; WP08 0.1; WP17 prep 0.25 | WP17 independent runs 0.75 |
| ML | WP09 slice proof 0.5; WP04 E1 + E3 0.75 | WP09 layered proof + near-miss + calibration 0.85; WP06 soft-rank stats 0.4 | WP04 E2 + fusion + conformal 0.95; WP06 diagonal/PN 0.3 | WP10 C2 1.1; WP06 0.15 | WP09 false-PASS campaign 0.65; WP06 0.15 |
| Product | WP15 API + adapter + binding + visual baseline 1.0; WP16 freeze spike 0.25 | WP15 pages + codegen 0.7; WP21 0.2; WP16 Host/Origin 0.1 | WP16 fuzzing 0.6; WP15 LOD/perf 0.4; WP22 offline WebView2 + browser mode 0.15, kill-matrix harness 0.1 | WP12 C5 0.8; WP16 installers + SBOM 0.4 | WP16 isolation test, clean build, signing 0.75; WP22 portable fallback 0.1, kill-matrix final 0.1 |
| Data | WP01 0.8; WP18 acceptance-test plan 0.2; WP14 rig approval + first passes 0.25 | WP01 0.4; WP14 Meteor truth + multi-site trial 0.6; WP19 0.25 | WP14 HFDL/STANAG/NAVTEX 0.6; WP19 0.15; WP11 C4-lite 0.5 | WP11 C3 0.9; WP14 0.35 | WP18 acceptance runs + analyst guide 0.8 |

### 11.3 Calendar and gates

The clock starts **now** (W1 = Mon 28 Sep 2026). Secondary sources report SIH 2026 screening in October-November and a **36-hour Grand Finale in December** (§14.2). The official portal shows its dates only as an image, so the finale date is confirmed with the SPOC (K17). The software build runs from W1 regardless of the selection timeline. If the finale falls before W10, the ladder in §11.6 applies.

| Gate | Date (end of) | Exit criteria |
|---|---|---|
| G0 | W1 · 4 Oct | **Engineering baseline:** interface conventions (§6.2) frozen; repo skeleton, CI and `scripts/check.py` running; Gen v0 specification; recipe schema v0; team three-point estimates collected to re-run the confidence analysis (§11.7); KPI definitions drafted for freeze at G1; rig approval requested |
| G1 | W2 · 11 Oct | **Vertical slice:** Gen v0 file (QPSK + CC K=7 + block 48 × 32 + additive scrambler + CRC frames) decoded with the known recipe; layered proof (PHY + K1 + S2) passes on it. Ingest, measurement, PSK receiver on Tier 1; C++ Viterbi within 0.2 dB of oracle; Gen v1 taps; API + adapter + **visual-regression baseline green**; **sidecar freeze spike passes on Windows and Linux**; E1 + E3 v0; sealed-set seed hashes published; rig approval requested |
| G2 | W4 · 25 Oct | Blind conv + block/conv interleavers (Tier 1-2); additive scrambler; Bit-Lens + CRC solving; **layered proof calibrated** on Tiers 1-2; orchestrator v1; QAM/OQPSK; **first Meteor capture: OQPSK/QPSK and 72k/80k confirmed; ASM found after Viterbi, matching SatDump** |
| G3 | W6 · 8 Nov | RS (basis, depth) + concatenation + post-FEC coset → **Meteor fully blind, frames equal to SatDump**; FSK/MSK; Fs back-solve; E2 + fusion + conformal; diagonal/PN; triage; fuzzing running; HFDL/STANAG/NAVTEX captures in hand. **R-01 to R-17 pass on the bench except the LDPC parts of R-05/R-09 and R-07's HF curves.** P2 decision (§11.1 rule) |
| G4 | W8 · 22 Nov | LDPC; HF curves; bursts (HFDL vs dumphfdl); C2; C4-lite + C3 multi-site; C5 bit-exact gate; installers (offline WebView2, per-user); **kill-matrix green except the final portable-mode row**; **all requirements pass**; demo script frozen |
| G5 | W9 · 29 Nov | Independent KPI report on revealed sealed sets; false-PASS campaign complete; zero-network test; feature freeze |
| — | W10 · 30 Nov-6 Dec | Five end-to-end operational acceptance runs on the frozen build (one with an injected failure); buffer |

### 11.4 Phase goals

| Phase | Goal | Headline deliverable |
|---|---|---|
| Ph1 (W1-2) | Freeze interfaces (G0); retire the integration risks; prove the spine | Engineering baseline; vertical slice + sidecar freeze + visual-regression baseline + C++ Viterbi |
| Ph2 (W3-4) | The engine finds recipes by itself on synthetic data | Blind conv / interleaver + layered proof + orchestrator; first Meteor PHY |
| Ph3 (W5-6) | Full PS coverage on real data | Meteor fully blind; R-01 to R-17 minus LDPC |
| Ph4 (W7-8) | Crown innovations on real data | C2, C3 multi-site, C5; LDPC; installers |
| Ph5 (W9-10) | Prove it independently; accept | KPI report, zero-network test, acceptance runs, analyst guide |

### 11.5 Critical path and decoupling

**Critical path:** WP13 Gen v1 (taps) → WP05 Viterbi/GF(2) → WP06 conv + interleaver → WP09 layered proof → WP06 RS + WP07 coset → **G3 Meteor fully blind** → WP11 C3 and WP12 C5 → WP17 independent verification. Coding and ML have zero float in Phases 1-4.

**Near-critical externals:** WP14 (satellite passes, weather, KiwiSDR availability, rig approval) and WP16 (sidecar freeze; retired in Ph1).

**Decoupling:** each WP develops against its own Gen tap (§8.2) and the interface conventions frozen at G0 (§6.2), so no WP waits for the WP upstream of it. Integration happens continuously through the orchestrator on Tier 1.

### 11.6 Tracking and descoping

- **Weekly earned value:** each WP owner reports percent complete against planned pw. SPI = earned / planned per WP and per role.
- **Triggers:** SPI < 0.9 at any gate, or any role above 110 % for two weeks → apply the next descoping step, with no debate.
- **Descoping ladder** (baseline → threshold, applied top-down; P1 PS coverage and C1 are never cut):

  | Rung | Change | Saves (pw) |
  |---|---|---|
  | 1 | Portable-folder fallback and low-priority kill-matrix rows dropped (source run stays) | 0.20 |
  | 2 | C3 real multi-site → rig two-sensor stitching | 0.50 |
  | 3 | C2 validated on Tiers 1-2 only (Tier 3 reported) | 0.20 |
  | 4 | Watterson / real-HF tuning → AWGN curves plus one HF real-signal result | 0.40 |
  | 5 | R-12b deep path minimal | 0.10 |
  | 6 | C5 gate on synthetic data only (no compiler pack) | 0.30 |
  | 7 | Free-running post-FEC scrambler ID → P2 (frame-synchronous, the Meteor case, stays) | 0.25 |
  | 8 | E2 deep expert and Twin-conditioned generation → P2 (E1 + E3 carry R-04 in the nominal envelope) | 0.75 |
  | | **Baseline 34.35 → threshold 31.65 pw** | **2.70** |

### 11.7 Commitment levels and schedule confidence

The plan distinguishes what is **committed** from what is **planned**, as NASA does with threshold and baseline requirements:

| Configuration | Content | pw | Completion confidence (JCL) | Status |
|---|---|---|---|---|
| **Threshold** | Everything in §5, with ladder rungs 1-8 applied | 31.65 | **73 %** | **Committed** |
| **Baseline** | Full P1 as planned in §11.1-11.2 | 34.35 | 31 % | Planned goal; the team works to it, and the ladder protects the threshold |
| P2 | §11.1 list | +4.0 | — | Unfunded stretch |

**Method** (script in `_build/feasibility.py`, 200,000 Monte Carlo runs):
- Each WP's effort is triangular (−20 % / most likely / +50 %), which captures the usual overrun skew of new software.
- A team-wide common factor, triangular (0.9 / 1.0 / 1.2), models correlated slips such as exams or shared learning curves.
- The result is compared against the 37.5 pw capacity.
- NASA commits projects at a 70 % joint confidence level (JCL). The threshold configuration meets it; the baseline does not, which is why it is a goal and not a commitment.
- At G0 each owner gives their own three-point estimates, which replace the uniform assumption, and the analysis is re-run at every gate.

### 11.8 Definition of done (every WP)

A WP is done when all of the following hold:
1. Code merged with tests.
2. Oracle or analytic agreement shown for every estimator or decoder.
3. Interface conventions (§6.2) checked at its boundaries.
4. Its KPI rows run in the bench, with intervals.
5. A second member has reviewed it.
6. Its user-facing output is visible in the UI or CLI.
7. Its degraded mode, if any, has a kill-matrix row.
8. The WP owner has updated its line in `HANDOFF.md`.

---

## 12. Verification, assurance, risks, demo

### 12.1 V&V levels

| Level | What | Pass rule |
|---|---|---|
| Unit | Estimators, decoders, parsers vs oracles and analytic cases | Oracle tolerance |
| Integration | Full chain on Tier 1 via the orchestrator | Recipe and bits exact |
| System | Tiers 1-3 incl. the near-miss battery | §5 criteria with §3.5 rules |
| Independent | Commit-revealed sealed sets run by non-builders | Reported as measured, with intervals |
| Operational | Frozen build; 5 end-to-end acceptance runs (§12.4), one with an injected failure | Every run completes within its time; fallbacks exercised |

**False-PASS campaign:** ≥ 2,000,000 near-miss proof attempts stratified by layer. Each is one decode plus one re-synthesis of about 10<sup>4</sup> symbols. The measured NumPy Viterbi speed puts each at ≤ 0.07 s (much less with C++), so the campaign is ≤ 39 CPU-hours, about 2.5 h on the 16-thread laptop. It runs nightly from Ph3 in slices, with the final campaign in Ph5.

### 12.2 Assurance

| Concern | Control | Verified by |
|---|---|---|
| Hostile input | Range-checked parsers, size and type limits, per-job worker with memory cap and watchdog, coverage-guided fuzzing | ≥ 24 CPU-h fuzzing, zero crashes or hangs |
| Localhost exposure | 127.0.0.1 bind; Host check (anti-rebinding); Origin allowlist; header token; no CORS wildcard | Acceptance tests with forged Host / Origin |
| Network leakage | No network code at runtime | Full demo under packet capture: zero outbound |
| Supply chain | Every dependency pinned by hash in an offline wheelhouse (NFR-12); CycloneDX SBOM with licences; signed installers | Clean offline build on both OSs; SBOM inspection |
| Dependency failure or ban | Every dependency that can fail on a target machine has a degraded mode that keeps every verdict (NFR-13) | Nightly kill-matrix (§15.5) |
| Certificate integrity | Ed25519 per-site key in the OS key store; canonical JSON; `verify` | Second-machine verification |
| Model integrity | Every ONNX model and threshold-calibration file listed with its SHA-256 in a signed manifest, checked at load; a mismatch refuses to certify | Tampered-model test |
| Licences | Register; copyleft only in the test harness | Bundle inspection |

### 12.3 Risk register (top risks; v3 K01-K12 stand)

| ID | Risk | L | C | Score | Mitigation | Trigger |
|---|---|---|---|---|---|---|
| K01 | Real signals need more data than captures hold | 4 | 4 | 16 | D1 soft methods, C3 stitching, C2 | Tier 3 P<sub>id</sub> < 80 % at G3 |
| K02 | Schedule overrun | 4 | 4 | 16 | Rebaselined WBS, EV triggers, descoping order | SPI < 0.9 |
| K13 | Sim-to-real gap in E2 | 3 | 3 | 9 | Twin-conditioned Gen; E3 physics; proof above; real-data conformal | Real vs synthetic gap > 5 points at G3 |
| **K14** | False certificate through multiple testing | 2 | 5 | 10 | ≤ 8 / 64 attempts; per-attempt bound from 2,000,000 trials; K on certificate | Any false PASS in the campaign |
| **K15** | Right recipes fail the proof on real signals | 3 | 4 | 12 | Equivalence margins; reference noise; bounded impairment model | Tier 3 P(PASS\|right) < 80 % at G3 |
| **K16** | Meteor variant (OQPSK, 80k) or pass quality | 3 | 3 | 9 | OQPSK in P1; several passes per day; HFDL as second full-chain signal | Variant unconfirmed by G2 |
| **K17** | SIH calendar differs from the reported one (screening Oct-Nov; 36-hour finale in December) | 3 | 5 | 15 | Build starts now; threshold configuration committed at 73 % confidence | Official dates from the SPOC |
| **K18** | Team at 99-100 % load in Ph1-4; baseline has only 31 % completion confidence | 4 | 4 | 16 | Commit to the threshold configuration (73 %); baseline as goal; mechanical ladder (§11.6) | SPI < 0.9, or any role > 110 % for 2 weeks |
| **K21** | Finale rules restrict pre-built code, or the finale round is shorter than the 7-minute demo | 2 | 4 | 8 | Confirm the rules with the SPOC; keep a 3-minute cut of the demo; build history (git, bench reports) shows provenance | SPOC answer |
| **K19** | 64QAM carrier recovery at 10 dB | 3 | 2 | 6 | Blind 4th-power phase with π/2 resolution; E3 on phase-robust statistics; early Ph1 study | Top-1 on 64QAM < 95 % at G2 |
| **K20** | A dependency fails to load, is quarantined by antivirus, or is disallowed on the target machine | 3 | 3 | 9 | Pinned offline wheelhouse; degraded modes; browser, portable and source fallbacks (§15) | Any kill-matrix row red |

### 12.4 End-to-end acceptance scenario

One scripted run of the frozen build, used for operational acceptance (§12.1) and for the finale evaluation. Every step has a software fallback.

| Time | Step | What the software shows | Fallback |
|---|---|---|---|
| 0:00 | Load | Real Meteor recording, noisy waterfall | — |
| 0:30 | Autopilot, blind | Every layer recovered; frames equal SatDump's | Cached results, same UI |
| 1:40 | Layered proof | Ridge sinks into the noise; per-layer verdicts; near-miss 8PSK rejected; `verify` re-checks the certificate in seconds | Offline |
| 2:30 | Insufficient data | 0.4 s capture → tasking note with P90 duration; multi-site KiwiSDR captures stitched → proven | Deterministic offline |
| 3:30 | Mystery signal | Recipe chosen by the evaluator from those with **P95 recovery < 45 s** on the evaluation laptop; the rig transmits over cable | One of 20 sealed files |
| 4:40 | Recipe Compiler | `.grc` reproduces the bits exactly | File replay |
| 5:40 | Hidden signal | Only if P2 delivered | Skip |
| 6:30 | Numbers | In-app KPI report: independent results with intervals and commit-reveal hashes | — |

A short run (autopilot → proof → insufficient data) completes in under 3 minutes for time-boxed evaluations.

---

## 13. Repository layout

```
spacetech/
├── PRD.md · PRD v1.md · HANDOFF.md
├── ui/                       built front-end (design frozen)
│   ├── src/lib/engine.ts     adapter (same exports as mock.ts)
│   ├── src/lib/engine.types.ts   generated from OpenAPI (openapi-typescript)
│   ├── src-tauri/            desktop shell (to create)
│   └── tests/visual/         Playwright visual regression
├── engine/
│   ├── pyproject.toml        pinned; wheelhouse with hashes
│   ├── sanjaya/
│   │   ├── io/ measure/ triage/ scene/ classify/ demod/ coding/ bits/ proof/
│   │   ├── sufficiency/ stitch/ twin/ compile/ export/
│   │   ├── recipe.py         Pydantic models (single schema source)
│   │   ├── pipeline.py       hypothesis-tree orchestrator
│   │   ├── api/              FastAPI server, jobs (worker processes), store
│   │   ├── deps.py           dependency probe + SANJAYA_DISABLE switch (§15.5)
│   │   └── cli.py            analyze · verify · batch · serve · gen · bench
│   ├── scripts/              check.py (runs every CI check locally, offline)
│   ├── kernels/              C++17: viterbi · ldpc · gf2 · rs · loops
│   ├── gen/                  SANJAYA-Gen with taps
│   ├── bench/                KPI harness, oracles (test-only), sealed-set runner, near-miss campaign
│   └── tests/                unit + integration (fast suite < 5 min)
├── data/                     manifests + commit hashes in git; captures on disk (SigMF + SHA-256)
└── models/                   ONNX + model cards (data manifest hash, metrics per tier)
```

**Engineering rules:**
- The numerical core is pure.
- Every estimator ships with an oracle or analytic test in the same change.
- Interface conventions (§6.2) are checked by tests at every module boundary.
- No number is reported in the UI, documentation or reports unless the bench produced it, with its interval and reproduction hashes.
- PS wording comes first in every label and API field description.

---

## 14. Open items and references added in v2

### 14.1 Open items

| Item | Owner | Needed by |
|---|---|---|
| SIH 2026 finale date and format (reported: screening Oct-Nov, 36-hour finale in December), PS details, sponsor and theme: confirm on sih.gov.in and with the SPOC | Lead | Now |
| Finale rules: is pre-built code allowed or expected; length of judging rounds (K21) | Lead | G1 |
| Assumptions A-01 to A-10 (§2.3) | Lead | G0 |
| Team three-point estimates per WP (§11.7) | All | G0 |
| Rig approval and procurement | Data | W1 |
| Meteor-M N2-3 / N2-4: OQPSK (reported, §14.2) and 72k / 80k per pass; RS basis and depth; randomiser: confirm from our capture | Data + Coding | G2 |
| Compute budget stages not yet measured (detection, recognition, structure, proof) and C++ kernel speed (§6.6, §16) | All | G1 |
| Measured KPIs (all targets here are pre-registered, not results) | Protocol (independent) | G5 |

### 14.2 References and facts verified for v2 (27 Sep 2026)

| Item | Source | Used in |
|---|---|---|
| Swami and Sadler, "Hierarchical digital modulation classification using cumulants", IEEE Trans. Communications 48(3):416-429, 2000 | doi:10.1109/26.837045 (Crossref) | §7.1 |
| Dobre, Abdi, Bar-Ness, Su, "Survey of automatic modulation classification techniques: classical approaches and new trends", IET Communications 1(2):137-156, 2007 | doi:10.1049/iet-com:20050176 (Crossref) | §7.1 |
| Schuirmann, "A comparison of the Two One-Sided Tests Procedure and the Power Approach for assessing the equivalence of average bioavailability", J. Pharmacokinetics and Biopharmaceutics 15(6):657-680, 1987 | doi:10.1007/BF01068419 (Crossref) | §4.2 C1 |
| Tibshirani, Barber, Candès, Ramdas, "Conformal Prediction Under Covariate Shift", 2019 | arXiv:1904.06019 | §7.2 |
| Meteor-M LRPT: "QPSK for METEOR-M N2 and OQPSK for later satellites", 137.9 MHz | a-centauri.com Meteor reception guide; consistent with meteor_demod offering `qpsk` and `oqpsk` modes | §8.3, V-1 (to confirm from our own capture) |
| SatDump has separate pipelines `meteor_m2-x_lrpt` (72k, with `rs_usecheck`) and `meteor_m2-x_lrpt_80k` | docs.satdump.org, Pipelines page; DeepWiki summary of SatDump's source: M2-x uses OQPSK at 72k / 80k | §8.3 |
| Tauri 2 Windows installer: `webviewInstallMode` default `downloadBootstrapper` ("Requires an internet connection"); offline options `offlineInstaller`, `fixedVersion`; NSIS `installMode` default `currentUser` | v2.tauri.app, "Windows Installer" | §6.9, §15 |
| SIH 2026 calendar: screening Oct-Nov; 36-hour Grand Finale in December | Secondary sources (reskilll.com, techpathdaily.com); sih.gov.in shows the flow as an image only | §11.3 (confirm with the SPOC) |
| K=7 (171,133)<sub>8</sub> transparency | Derived: 171<sub>8</sub> = 1111001<sub>2</sub>, 133<sub>8</sub> = 1011011<sub>2</sub>, both weight 5 (odd), so complementing the input complements the output | §7.4 |
| CCSDS randomiser after RS encoding; RS(255,223) in dual basis | CCSDS 131.0-B (already in v3's standards list) | §7.4 |

All v3 references (§13 of v3) stand.

---

## 15. Dependencies and readiness for everything

### 15.1 The rules

1. **Use proven libraries and APIs wherever they save effort or add performance.** Building our own is reserved for SANJAYA's differentiators (proof, blind coding, orchestrator), not for plumbing.
2. **The deployed tool makes no runtime network calls** (NFR-05). This is an NTRO air-gap requirement, not a preference. External web APIs are used by the team for development and data collection (§15.4).
3. **Everything that can fail on a target machine has a fallback, and no verdict depends on it.** The proof, coding algebra, CRC solving and certificate content produce identical answers in every degraded mode.
4. **Fallbacks are exercised, not just written.** The nightly kill-matrix (§15.5) runs the bench with each fallback forced.

### 15.2 What if a dependency is missing on the target machine?

| Missing or failing | Still valid? | Effect | Fallback |
|---|---|---|---|
| Internet | **Yes** | None at runtime | Nothing at runtime depends on it |
| ONNX Runtime | **Yes** | Nominal envelope expected unchanged (E3 is the near-optimal classifier there). Below 10 dB accuracy drops, and the search is slower | E3 classification + rule-based triage (`triage.ts` port) |
| Our C++ kernels (e.g. a missing C++ runtime DLL) | **Yes**: identical bits | Decoders roughly 10-50× slower (estimate); R-12a waived | NumPy reference implementations; kernels built with a static C++ runtime to prevent this |
| cryptography | **Yes**: content identical, verifiable by `verify` | Certificate marked **UNSIGNED** | Sign later on a machine that has it |
| ReportLab | **Yes** | No headless PDF | HTML certificate + OS "print to PDF" |
| GNU Radio | **Yes** | `.grc` exported, marked **ungated** | Gate runs later with the compiler pack |
| Tauri shell / WebView2 | **Yes** | None | Offline WebView2 in the installer; browser mode (`sanjaya serve`) |
| Frozen sidecar blocked (antivirus) | **Yes** | Start-up time | Portable folder; `python -m sanjaya` from source |
| keyring back-end | **Yes** | None | 0600 key file |
| FastAPI / uvicorn / Pydantic | Core, pinned in the wheelhouse | — | Any failure is caught by the clean offline build test (§12.2) before release |

### 15.3 Dependency ledger

| Dependency | Class | Licence | Purpose |
|---|---|---|---|
| CPython 3.11 (frozen) | Core runtime | PSF | Engine |
| NumPy, SciPy | Core runtime | BSD-3 | Arrays, FFT, BLAS, filters, resampling, statistics |
| FastAPI + uvicorn + Pydantic | Core runtime | MIT / BSD-3 | Local API, validation, OpenAPI, WebSockets |
| cryptography | Core runtime | Apache-2.0 / BSD | Ed25519 signatures |
| ONNX Runtime | Core runtime (fallback defined) | MIT | Inference for E1, E2 and triage |
| keyring | Runtime (fallback defined) | MIT | OS key store for the signing key |
| ReportLab | Runtime (fallback defined) | BSD | Certificate PDF |
| SANJAYA kernels (own C++) | Core runtime (fallback defined) | own | Viterbi, LDPC, GF(2), RS, tracking loops |
| GNU Radio 3.10 | Optional external tool (separate process) | GPL-3.0 | C5 release gate |
| Tauri 2 + WebView2 / WebKitGTK | Shell | MIT / Apache-2.0 | Desktop app |
| React, three.js, R3F, postprocessing, motion, fontsource (35 packages, static bundle) | UI build | MIT / OFL | Existing UI (design frozen); no runtime fetch |
| pybind11, PyInstaller, Rust + Tauri CLI, Node + Vite + TypeScript, openapi-typescript | Build | BSD / GPL-2.0 with bootloader exception / MIT / Apache-2.0 | Building |
| PyTorch, LightGBM or scikit-learn | Dev (training) | BSD / MIT | Training models; never shipped |
| pytest, Atheris, Playwright, import-linter | Dev / test | MIT / Apache-2.0 / BSD | Tests; never shipped |
| galois, AFF3CT, liquid-dsp | Oracle | MIT | Unit-test references; never shipped |
| SatDump, dumphfdl, fldigi, gr-satellites, dump1090 | Oracle | GPL (test only) | Real-data truth; never shipped |

Every runtime package is pinned by hash in the offline wheelhouse and listed in the SBOM (NFR-12). None is copyleft (NFR-11); GNU Radio runs only as a separate optional process.

### 15.4 External web APIs and services (development and data collection)

| Service / API | Used for | If unavailable |
|---|---|---|
| KiwiSDR network (kiwirecorder) | HF captures; multi-site C3; GPS-timestamped reference for C4 | Own RTL-SDR V4 receivers (HF via built-in upconverter) at ≥ 2 team sites. C3 aligns on sync markers, so it does not need GPS. C4 reference from a GPS-disciplined oscillator or a locally receivable atomic-referenced broadcast |
| TLE source (e.g. CelesTrak) | SGP4 Doppler truth | The TLE is saved in each capture's SigMF metadata at recording time, so validation replays offline |
| SatNOGS network API | P3 (C7, C8), extra labelled audio | Own recordings; P1 unaffected |
| SatDump | Meteor truth | A second independent decoder (e.g. meteor_demod + meteor_decode); both are used when available, because two-decoder agreement is stronger truth |
| dumphfdl | HFDL truth | HFDL falls back to PHY-level KPIs from its known preamble |
| fldigi | NAVTEX truth | Any second NAVTEX decoder |
| PyPI, npm, GitHub | Build and CI | Offline wheelhouse and npm tarball cache archived per release; `scripts/check.py` runs every CI check locally |

**Runtime online features** (for example, fetching fresh TLEs) are not in scope. If the SPOC confirms a networked deployment, they can be added behind an explicit "online" switch that is off by default and never needed for a verdict.

### 15.5 Kill-matrix (nightly CI, WP22)

`SANJAYA_DISABLE=<name>[,<name>]` forces a fallback path, and `sanjaya/deps.py` reports at start-up what is available. Each row runs the Tier 1 regression bench plus the three Meteor reference captures.

| Configuration | Must hold (else red) | Allowed and reported |
|---|---|---|
| Full | All KPIs | — |
| − ONNX Runtime | Nominal outcome KPI, false-PASS bound, every bit-exact check | Extended-envelope accuracy; fast-path time (≤ 1.5×) |
| − C++ kernels | Every recipe, bit and verdict identical | Run time (R-12a waived) |
| − ReportLab | Certificate JSON identical; HTML certificate produced | No headless PDF |
| − GNU Radio | `.grc` and recipe produced, marked ungated | No gate |
| − cryptography | Certificate body identical, marked UNSIGNED; `verify` checks content | No signature |
| − keyring | Signing works from the 0600 key file | — |
| Browser mode (no Tauri) | Visual regression green in Chromium and Firefox | — |
| Portable folder / source run | Bench identical to the installer build | Start-up time |
| No network (always) | Zero outbound packets | — |

### 15.6 Readiness matrix (operational contingencies)

| Situation | Response | Prepared in |
|---|---|---|
| No internet at venue or at NTRO | Nothing changes | NFR-05 |
| RF transmission not allowed | File replay of sealed recordings | §12.4 |
| No admin rights | Per-user installer; portable folder | WP16, WP22 |
| Windows without WebView2 | Offline WebView2 bundled in the installer; browser mode | WP22 |
| No WebGL or GPU | 2D views (3D is optional by design) | Built |
| Antivirus quarantines the frozen sidecar | Signed binaries; portable folder; `python -m sanjaya` from source | WP16, WP22 |
| 8 GB RAM machine | Memory maps, LOD tiles, 4 GB job cap | NFR-03 |
| Unknown file format from judges | Sniffing with confidence + manual override + re-run | R-01 |
| Engine crash mid-job | Worker process dies alone; API survives; UI reconnects; stage cache resumes | §6.9 |
| Power loss | Stage caches on disk; job resumes | §6.9 |
| Demo laptop fails | Second laptop with the identical frozen build and data | K03 |
| A dependency is banned or has a CVE | SBOM shows the exposure; the pinned version is swapped or the fallback path is used; the kill-matrix proves the verdicts are unchanged | NFR-12, NFR-13 |
| Licence objection | No copyleft in the shipped engine; GNU Radio only as a separate optional tool | NFR-11 |

### 15.7 Cost

| Item | pw | Owner / WP |
|---|---|---|
| Offline WebView2 + browser mode | 0.15 | Product / WP22 |
| Portable folder / source-run fallback | 0.10 | Product / WP22 |
| Kill-matrix CI | 0.20 | Product / WP22 |
| NumPy fallback wiring for kernels | 0.10 | Coding / WP05 |
| **Total** | **0.55** | P1 34.35 pw; reserve 3.15 pw (8.4 %) |

If the schedule slips, the portable fallback and the lower-priority kill-matrix rows (keyring, ReportLab) are cut before any feature (ladder rung 1, §11.6).

---

## 16. Feasibility evidence (measured, not prototype)

`_build/feasibility.py` is throwaway analysis code, not part of the engine. It was run on 27 Sep 2026 on the team laptop (Intel Raptor Lake, 16 threads, Python 3.10, NumPy 2.2, SciPy 1.15), seed 147. It turns the PRD's key assumptions into measurements.

### 16.1 Compute

| Claim in the PRD | Measured | Verdict |
|---|---|---|
| A 100 MB file is interactive in < 2 s (R-11) | All LOD tiles for 25 M complex samples, 1,024 bins: **0.62 s** | Holds, with 3× margin |
| Feedforward synchronisers are cheap | Oerder-Meyr timing estimate over 10<sup>6</sup> samples: **0.011 s** | Holds |
| Pure-Python feedback loops cost ~20 s per 10<sup>6</sup> samples (v2 finding PR-09) | Second-order loop: **0.25 s per 10<sup>6</sup>** | **v2 was wrong by ~80×; corrected.** Simple loops may stay in Python; multi-tap LMS and Viterbi remain C++ |
| The NumPy fallback decodes correctly (kill-matrix "− C++ kernels") | K=7 soft Viterbi in NumPy: **0.15 Mbit/s, 0 post-FEC errors** on 20,000 bits at E<sub>s</sub>/N<sub>0</sub> = 6 dB | Holds; the fallback is correct but too slow for R-12a, as the PRD states |
| The exhaustive interleaver search takes minutes, not seconds | GF(2) rank (2n × n, NumPy): 0.006 / 0.018 / 0.069 s at n = 256 / 512 / 1,024; scaling n<sup>1.72</sup>; exhaustive search to 4,096 ≈ **0.3 h** | Holds: the deep path must be anytime and capped |

### 16.2 The layered proof (PR-01)

QPSK with the K=7 (171,133) code, 20,000 symbols. "Right" re-synthesises from the true (decoded) bits; "uncoded" re-synthesises from hard decisions.

| E<sub>s</sub>/N<sub>0</sub> | Residual vs noise, right recipe | Residual vs noise, uncoded hypothesis | Unsatisfied parity checks K1: measured / predicted f<sub>0</sub> / random bits |
|---|---|---|---|
| 12 dB | 0.002 dB | **0.001 dB** | **0.0003** / 0.0002 / 0.494 |
| 6 dB | 0.043 dB | −0.304 dB | **0.190** / 0.193 / 0.497 |

**What this proves:**
- At 12 dB, the waveform cannot tell "right" from "uncoded" (0.002 vs 0.001 dB), and neither can a 0.5 dB equivalence margin at 6 dB. The waveform tests certify the PHY only, exactly as the layered design says.
- The parity test K1 separates coded from random bits decisively at both SNRs (0.0003 vs 0.494; 0.190 vs 0.497, about 88 standard deviations). It also matches the formula f<sub>0</sub> = (1 − (1 − 2p)<sup>w</sup>)/2 to within 0.003.

### 16.3 Statistics and schedule

| Quantity | Value | Where used |
|---|---|---|
| Rule of three, 2,000,000 attempts | p̂ ≤ 1.5 × 10<sup>−6</sup>; × 64 = 9.6 × 10<sup>−5</sup> | §3.4, §4.2 C1 |
| Coverage 95 % CI half-width at n = 2,000 / 8,000 | 0.0096 / 0.0048 | §3.4 (why n ≥ 8,000) |
| Wilson half-width at p = 0.95 and 0.98, n = 1,000 | 0.0135 / 0.0087 | §3.5 |
| Hard-rank rows 2N/(1 − p)<sup>N</sup> vs the 3N target | N = 96: 256 vs 288 (no gain); N = 512: 4,768 vs 1,536 (32 %); N = 1,024: 44,411 vs 3,072 (6.9 %) | §3.4 (KPI corrected) |
| Schedule confidence, 200,000 runs | Baseline 34.35 pw: **31 %** (P70 = 40.4 pw). Threshold 31.65 pw: **73 %** (P70 = 37.2 pw) | §11.7 |

### 16.4 What is still unmeasured

- The C++ kernels' speed, the recognition and proof stage times, and real-signal behaviour.
- These are measured at G1 and G2 with the same script extended. They are the only budget lines without evidence today, and each has an allocation and a 150 % trip-wire (§6.6).

---

## 17. Glossary

| Term | Meaning |
|---|---|
| AMC | Automatic modulation classification |
| APS | Adaptive prediction sets (a conformal scoring rule) |
| ASM | Attached sync marker (frame start word in CCSDS-style links) |
| BER / FER | Bit / frame error rate (pre-FEC or post-FEC always stated) |
| CFAR / OS-CFAR | Constant false-alarm rate detection / ordered-statistic variant |
| CFO | Carrier frequency offset |
| Conformal set | A set of classes guaranteed to contain the truth with a stated probability, under stated conditions |
| CRLB | Cramér-Rao lower bound on the variance of an unbiased estimator |
| ECE | Expected calibration error |
| E<sub>s</sub>/N<sub>0</sub> | Energy per symbol over noise density: this PRD's SNR |
| EV / SPI | Earned value / schedule performance index (earned ÷ planned) |
| EVM | Error vector magnitude |
| GBDT | Gradient-boosted decision trees |
| HIL | Hardware in the loop (our cabled rig) |
| JCL | Joint confidence level: the probability that the plan completes within its capacity |
| K1, K2, K3 | Coding-layer proof tests: parity membership, correction consistency, likelihood ratio |
| LLR | Log-likelihood ratio, ln P(b = 0)/P(b = 1) |
| LOD | Level of detail (pre-computed spectrogram tiles) |
| P<sub>id</sub> | Probability of correct identification |
| pw | Person-week, 40 hours |
| S1-S4 | Structure-layer proof tests: sync, CRC, counters, scrambler |
| SBOM | Software bill of materials |
| SigMF | Signal Metadata Format (recording + JSON metadata) |
| T1-T4 | PHY-layer proof tests: explained energy, residual at noise floor, no cyclostationarity, whiteness |
| TOST | Two one-sided tests, a statistical equivalence test |
| TRL | Technology readiness level (NASA NPR 7123.1) |
| Twin | Sensor Twin: a persistent model of one receiver's clock, noise and front end |
| WBS / WP | Work breakdown structure / work package |

---

## Appendix A. Review record

### A.1 Method

v1 was reviewed the way a preliminary design review board would review it:

- Every sentence was read against the PS text, v3, and the UI source code in `ui/src`.
- Every number was recomputed and every statistical claim was checked for validity.
- Every interface assumption was checked against the code it names.
- New external facts were verified at source on 27 Sep 2026 (§14.2).

**Result:** **44 findings** (5 critical, 26 major, 13 minor). All are dispositioned in this edition.

**Severity:** **C** critical means it would make the product wrong or the plan infeasible. **M** major means an expert reviewer would catch it and it would cost credibility or performance. **m** minor.

### A.2 Scorecard of v1

| Criterion | Weight | v1 | Why |
|---|---|---|---|
| Technical correctness | 15 % | 4/10 | Proof claimed power it does not have (PR-01, PR-03); no phase-ambiguity handling (PR-04); wrong symbol-rate estimator for constant-envelope signals (PR-06); coset codes (PR-07); Meteor modulation (PR-08) |
| Coverage of the PS | 15 % | 8/10 | All clauses mapped; bursts and channelisation missing from P1 |
| Innovation | 15 % | 9/10 | Strong and defensible |
| Quantitative rigour | 10 % | 5/10 | Multiple testing ignored; coverage KPI inside sampling noise; no decision rules; probabilities attached to continuous values |
| Feasibility and schedule | 10 % | 3/10 | ~5.6 pw of necessary work unbudgeted; phases not resource-levelled; calendar unanchored |
| Verification and validation | 10 % | 6/10 | No traceability matrix; sealed sets rely on trust |
| Architecture and interfaces | 10 % | 6/10 | Infeasible orchestrator; no compute budget; UI contract infeasible; no interface conventions |
| Data and ML strategy | 5 % | 7/10 | Good levers; conformal validity under shift ignored; circular truth for STANAG 4285 |
| Security and deployment | 5 % | 5/10 | DNS rebinding; desktop shell missing; heavy JIT dependency |
| Clarity | 5 % | 8/10 | Clear; two overclaims |
| **Weighted total** | 100 % | **6.2/10** | A strong concept, but it would not pass a design review with these findings open |

### A.3 What v1 got right (kept)

- The Recipe as the single central object.
- Hypotheses instead of single answers.
- The proof as the final arbiter.
- Algebra for the coding layer.
- A physics expert alongside the learned one.
- Rate-normalised network inputs.
- The four-tier data engine.
- The frozen UI design.
- The phase-and-gate structure from v3.

### A.4 Deviations from v3 introduced by this edition

| # | v3 says | v2 says | Why |
|---|---|---|---|
| V-1 | Meteor-M LRPT: QPSK 72 kBd | Reception guides report **OQPSK** for the satellites after N2 (72k and 80k variants). The OQPSK receiver is in P1; the variant is confirmed from our first capture and SatDump's pipeline before any claim | PR-08 |
| V-2 | C1: four tests on the waveform; KPI "P(PASS \| wrong) ≤ 10<sup>−4</sup> from 30,000 trials" | A **layered** proof (PHY, coding, structure) with equivalence margins. The KPI becomes per certificate: ≤ 10<sup>−4</sup> through ≥ 2,000,000 near-miss attempts and ≤ 8 (fast) / 64 (deep) proof attempts per certificate | PR-01 to PR-03 |
| V-3 | R-04: 11 classes incl. GMSK | 10 classes in P1; GMSK in P2 (first item to restore) | PR-05 capacity |
| V-4 | D2: additive and self-synchronising scramblers | Additive (pre-FEC and post-FEC) in P1; self-synchronising in P2 | PR-05, PR-07 |
| V-5 | C5: C++ out-of-tree GNU Radio blocks; live FER KPI | Stock blocks + embedded Python blocks; bit-exact gate in P1; C++ blocks and live FER in P2 | PR-23 |
| V-6 | C3: phase search without sync marker | P1 limited to signals with sync markers (every P1 real source has one); unsynchronised search in P2 | PR-05 |
| V-7 | C4-lite: full Twin parameter list | P1 Twin = sample-clock error + noise floor level and shape (what C1 and C3 need) | PR-05 |
| V-8 | AO-40-FEC satellites in Tier 3 | P2; Meteor already covers concatenated RS + convolutional | PR-05 |
| V-9 | P1 31.2 pw, reserve 17 % | Baseline P1 **34.35 pw** (schedule confidence 31 %) planned as the goal; **threshold 31.65 pw committed at 73 %** confidence (§11.7); P2 unfunded | PR-05, PR-48 |
| V-10 | R-12: full chain < 10 s | R-12a fast path < 10 s; R-12b deep search anytime, capped | PR-09 *v2.3 measurement:* simple Python loops cost 0.25 s per 10<sup>6</sup>, not ~20 s (§16.1); only multi-tap LMS and Viterbi need C++ |
| V-11 | R-01 to R-15 | + R-16 CLI and batch, + R-17 emitter detection and channelisation | PR-18, PR-37 |
| V-14 | G0 tied to a non-software submission | G0 = engineering baseline; the PRD covers the software only (team decision, v2.4) | PR-49 |
| V-12 | PyTorch CPU at runtime | PyTorch for training; ONNX Runtime at runtime for every model (smaller installer, deterministic inference); if it fails to load, classification falls back to E3 + rule-based triage | PR-41, §15 |

### A.5 Findings register

| ID | Sev | Where (v1) | Finding | Disposition (v2) |
|---|---|---|---|---|
| PR-01 | C | §4.2 C1, §9.3 | v1 claims "any wrong parameter anywhere fails T1-T4". **False.** (a) At high SNR, re-modulated *hard decisions* already explain the waveform, so the "uncoded" hypothesis passes the waveform tests: the tests have no power over the coding layer when there are few channel errors. (b) A wrong scrambler is invisible: re-scrambling with the same wrong scrambler restores the same channel bits. | **Layered proof:** PHY certified by the waveform tests, coding layer by a code-membership parity test plus correction consistency, framing and scrambler by structure tests (sync, CRC, counters). Each layer gets a verdict; undeterminable layers are listed as equivalence classes. §4.2 C1, §9.3 |
| PR-02 | C | §3.3, §8.1 | **Multiple testing.** The search runs the proof on many hypotheses per file, so the chance that *some* wrong hypothesis passes is up to K times the per-trial bound. v1 also bounded label error by P(PASS\|wrong), but the quantity that matters is P(wrong\|PASS). | At most K = 8 proof attempts per certificate, and K is recorded on the certificate. *v2.3:* per-attempt bound 1.5 × 10<sup>−6</sup> (0 false PASS in ≥ 2,000,000 near-miss attempts) gives per-certificate ≤ 10<sup>−4</sup> on both the fast path (8) and the deep path (64) (PR-47). Label error restated by Bayes. §3.4, §4.2 C1, §7.6 |
| PR-03 | C | §4.2 C1 T2/T4 | Point-null significance tests on ≥ 10<sup>4</sup> samples reject *every* real recording, because real signals carry PA non-linearity, phase noise, spurs, adjacent signals and impulsive HF noise. "Kurtosis = 3" fails on HF atmospheric noise. P(PASS\|right) would collapse on Tier 3. | **Equivalence tests** with calibrated effect-size margins (TOST, Schuirmann 1987). Noise is modelled from a reference (signal-free segments, guard bands, or the Twin) instead of an ideal. Bounded impairment modelling in re-synthesis, applied equally to near-misses. Tier 3 P(PASS\|right) is its own KPI. §4.2 C1 |
| PR-04 | C | §5 R-07, §7.4 | **Phase ambiguity and spectral inversion are not handled.** Blind carrier recovery leaves an M-fold rotation, and I/Q swap or spectral inversion adds conjugation: 8 cases for QPSK. The K=7 (171,133)<sub>8</sub> code is transparent to bit inversion (both generators have odd weight, 5), so the code test cannot resolve a 180° ambiguity. Without this, blind decoding fails in most cases. | The ambiguity set {rotation k·2π/M} × {conjugation} is carried as hypotheses into the coding layer. It is resolved by the syndrome where the code is not transparent, otherwise by sync word, CRC or differential-coding detection. §6.5, §7.4 |
| PR-05 | C | §11 | **Plan under-scoped and not resource-levelled.** P1 omitted ~5.6 pw of work it cannot function without (ambiguity, channelisation, bursts, orchestrator, desktop shell and sidecar, UI data binding, layered proof, coset scramblers, C++ loops). True P1 was 36.8 pw, a 1.9 % reserve. v1 Phase 1 put all 5.5 pw of DSP-owned work (WP01-03) into W1-W2, where one role can deliver at most 1.25 pw. WP06 (3.5 pw) in W3-W6 needed 0.875 pw/week from a role that has 0.625. | Rebaselined WBS: 33.8 pw after 3.0 pw of reuse and descoping, reserve 3.7 pw (9.9 %). A role × phase loading table with no role over 1.25 pw per phase. Gates redefined and dated; critical path identified; P2 declared an unfunded stretch. §11 |
| PR-06 | M | §5 R-03, §6.3 | The symbol-rate estimator relies on the \|x\|² line, which **does not exist** for constant-envelope signals (FSK, MSK, GMSK, CPFSK) and is weak at low roll-off (its strength scales with excess bandwidth). | Family-specific estimators fused: \|x\|² for linear signals with α ≥ 0.15; x² and x⁴ lines for MSK-type; the transition spectrum of the phase derivative for FSK; decode-fit refinement. E2 trained with ±1 % rate error. §6.4, R-03 |
| PR-07 | M | §7.4 | **Post-FEC scramblers turn codewords into cosets**, and rank or dual-space methods fail on cosets. The CCSDS pseudo-randomiser (used on Meteor LRPT) is applied *after* RS encoding. CCSDS RS(255,223) is specified in **dual-basis** representation, and Meteor interleaves RS at depth 4. None of this was in v1, so blind RS identification on the headline real signal would fail. | Scrambler-position hypotheses {pre-FEC, post-FEC, PHY}. Affine rank via row differences for frame-synchronous PN. Joint cyclic-code + scrambler ID (Ding et al. 2026, in v3's references). RS hypotheses include basis {conventional, dual} and interleave depth I ∈ {1..8}. §7.4 |
| PR-08 | M | v3 §7, v1 §8 | **Meteor-M N2-3 and N2-4 LRPT are reported as OQPSK**, not QPSK (two independent reception guides, §14.2). The 72k and 80k variants are unconfirmed per pass. | OQPSK receiver in P1. The variant is confirmed from our own first capture (half-symbol I/Q offset) and SatDump's pipeline before anything is claimed. §8.3, K16 |
| PR-09 | M | §6.3, §6.7, R-12 | **No compute budget.** An exhaustive GF(2) rank search up to period 4,096 costs about 10<sup>12</sup> word operations (minutes, not seconds). Pure-Python feedback loops (Costas, timing, LMS) cost on the order of 20 s per 10<sup>6</sup> samples. Both break R-12's 10 s. | Per-stage budget table (§6.6). Fast path / deep path split (R-12a / R-12b). Period candidates pre-screened by bit autocorrelation. Feedforward block synchronisers (Oerder-Meyr, Viterbi-Viterbi) vectorised; unavoidable recursive loops in C++. §6.4, §6.6 |
| PR-10 | M | §6.4 | The orchestrator was specified as a flat joint queue over stage candidates. That is **impossible**: interleaver candidates only exist after demodulating under a particular modulation hypothesis. | Best-first **hypothesis-tree search** with stage-conditional expansion, cheap pruning tests between stages, budgets, and anytime output. §6.5 |
| PR-11 | M | §7.2, §3.3 | Conformal coverage is guaranteed only under exchangeability. Calibrating on synthetic data and deploying on real data voids it. Marginal 95 % coverage can hide very poor coverage at low SNR. The KPI "0.95 ± 0.01 at n ≥ 2,000" sits *inside* its own sampling noise (95 % CI half-width ≈ 0.0096). | Calibrate on Tier 2 + truth-labelled Tier 3. Class-conditional (Mondrian) and SNR-binned coverage reported. n ≥ 8,000 per tier (half-width 0.0048). Weighted conformal under covariate shift (Tibshirani et al. 2019) in P2. §3.4, §7.2 |
| PR-12 | M | §3.3 | **No end-to-end outcome KPI and no single operating envelope.** Stage KPIs multiply (0.98 × 0.95 × 0.95 × 0.95 ≈ 0.84), so users experience a figure nobody targeted. | Operating envelope (nominal / extended / outside) and an outcome KPI with three results: correct-certified, honestly undecided, wrong-certified. §3.3 |
| PR-13 | M | §3.3, §5 | No acceptance decision rule (point estimate or confidence bound?). R-06's KPI, conditioned on C2's own "sufficient" verdict, can be gamed: never declaring sufficiency passes it. | Decision rules per KPI class (§3.5). A decision-rate KPI paired with R-06 and C2. §3.4, R-06 |
| PR-14 | M | §4.2 C2 | Evidence from misspecified likelihoods grows too fast, so ΔT is underestimated and the α = 10<sup>−3</sup> decision is overconfident. ΔT<sub>actual</sub> is itself a random stopping time, so a point-error KPI is dominated by noise. | Tempered likelihoods fitted on Tiers 1-2. ΔT given as a predictive distribution (P50 / P90), and tasking uses P90. KPI = coverage of the 80 % interval plus median error. §4.2 C2 |
| PR-15 | M | §6.5 | Continuous parameters (Fs, symbol rate, CFO, SNR, bandwidth) carried a *probability*. A probability is meaningless for a continuous estimate. | Standard uncertainty u (k = 1) and a 95 % interval for every continuous value, from segment jackknife and checked against the Cramér-Rao bound on Tier 1. Interval coverage is a KPI. §6.7, R-03 |
| PR-16 | M | §10 | "Add `engine.ts` only" is **infeasible**. About 30 scenario-bound constants sit in UI components: the dB window compiled into GLSL in `Terrain.tsx`, ±24 kHz axis mapping, 48 kHz, 251.2 s duration, the 1024 × 360 grid, floor −104 / span 44, the SigMF export's `ci16_le` and 48 kHz. 15 files import `mock.ts`. | A permitted change class, "data binding with zero visual change", with the hard-codes enumerated. Acceptance is a pixel-diff visual regression on the demo scenario. §10 |
| PR-17 | M | §6.2, §6.7 | **The desktop shell does not exist** (`ui/` has no `src-tauri`). Freezing Python + NumPy + SciPy + ONNX Runtime as a sidecar and building Windows and Linux installers was unbudgeted. | In WP16 (+0.5 pw), with a freeze spike in Phase 1 to retire the risk early. §6.9, §11 |
| PR-18 | M | §5, P1 | P1 had **no emitter detection or channelisation** (Scene was P2), yet real files carry several signals (the demo scenario itself has four) and R-15 depends on splitting them. | R-17: OS-CFAR detection + channel extraction in P1. Only cancellation stays in P2. |
| PR-19 | M | R-07 | **No burst-mode acquisition**, yet HFDL (a P1 real signal) is bursty. | Burst detection, preamble correlation and per-burst acquisition in P1. R-07 |
| PR-20 | M | §8.1 | STANAG 4285 "truth" came from C1 itself, which is **circular**. | STANAG 4285 is used for PHY KPIs only (its known preamble and probe symbols give symbol-level truth) and excluded from coding-layer KPIs. §8.3 |
| PR-21 | M | §6.6, §12.2 | A localhost HTTP server is exposed to **DNS rebinding** and cross-origin requests from any web page open on the machine. | Host header must equal 127.0.0.1:port; Origin allowlist; token sent in a header, not a cookie; no CORS wildcard; all tested in acceptance. §6.8 |
| PR-22 | M | §6.3 | `galois` depends on numba/llvmlite: large, JIT-compiled on first call, and fragile to freeze into an installer. | `galois` used only in test oracles; production GF(2<sup>m</sup>) and RS go in the C++ kernel module. §6.4 |
| PR-23 | M | §4.2 C5 | The bit-exact gate needs GNU Radio on the analyst's machine, and C++ out-of-tree blocks tie the output to one GNU Radio ABI. | The C5 output is a self-contained `.grc` file: stock gr-digital blocks for the PHY and **embedded Python blocks** for de-interleaving, RS, CRC and framing, so nothing needs compiling. The gate runs in an optional offline "compiler pack". §4.2 C5 |
| PR-24 | M | §4.2 C1 | "Identical certificate on a second machine" fails for floating-point statistics (BLAS and SIMD change the reduction order). | Discrete recipe exact; statistics in canonical JSON rounded to a declared precision; deterministic reductions; `sanjaya verify` re-checks a certificate from the file and the recipe alone. §4.2 C1, §6.7 |
| PR-25 | M | §11 | Weeks were not anchored to dates. If building waits for selection, past SIH editions left only a few weeks between shortlist and finale. | The clock starts now: W1 = 28 Sep 2026. SIH dates are treated as external constraints to confirm. §11.3 |
| PR-26 | M | §6.5, §10.2 | Python and TypeScript types were maintained by hand, a guaranteed drift. | One source of truth: Pydantic → OpenAPI → generated TS types (openapi-typescript); contract test in CI. §6.8 |
| PR-27 | M | §11 | No dependency network or critical path. | Critical path identified; work decoupled through generator "taps" at every layer. §11.5 |
| PR-28 | M | §8.4 | "Sealed" test sets relied on trust inside a six-person team; no out-of-distribution splits. | **Commit-reveal:** SHA-256 of sealed manifests and seeds published at G1, revealed at G5. Held-out parameter regions and held-out sensors. §8.5 |
| PR-29 | M | §5 | No traceability matrix (PS clause → requirement → module → WP → test → KPI → demo beat). | Added. §5.3 |
| PR-30 | M | §5 | No non-functional requirements (memory, file size, platforms, start-up, installer, logs). | NFR-01 to NFR-11. §5.2 |
| PR-31 | M | whole | **No interface conventions**: LLR sign, bit order, frequency sign, dB reference, time base, complex normalisation. Unit and sign mismatches between modules are a classic failure mode. | An interface convention sheet, binding on every module and on the API. §6.2 |
| PR-32 | m | §1 | "Every other team stops once it has produced an answer" overclaims. | Qualified as README claims. §1 |
| PR-33 | m | §1 | The P1 loop showed "subtract and re-scan", but cancellation (D4) is P2. | Marked as P2. §1 |
| PR-34 | m | §6.7 | "Process pool because NumPy releases the GIL" contradicts itself. | Threads for GIL-releasing kernels; one worker process per job for kill, timeout and memory cap. §6.9 |
| PR-35 | m | R-01 | WAV variants missing. | RF64/BW64 (> 4 GB), WAVE_FORMAT_EXTENSIBLE, `auxi` chunk (centre frequency and start time, as written by HDSDR/SDRuno-style tools), KiwiSDR `kiwi` chunk (GPS timestamps). R-01 |
| PR-36 | m | §11 | Energy + Mahalanobis open-set was placed in P1, contrary to v3 (D7 open-set is P2). | P1 NOVEL = empty or low-confidence conformal set; full open-set in P2. §7.2 |
| PR-37 | m | §5 | No headless interface, although the bench, batch processing and the independent verifier all need one. | R-16 CLI and batch on the same code path as the API. |
| PR-38 | m | §6.5 | `raw: Any` leaves the schema unspecified. | Typed union. §6.7 |
| PR-39 | m | §4.2 C1 | Analyst overrides were not reflected in certification. | Certificates mark "analyst-assisted" and list the overrides. §4.2 C1 |
| PR-40 | m | §12.4 | Demo beat timing was never checked against compute time. | Challenge choices restricted to recipes with P95 recovery < 45 s on the demo laptop, measured in rehearsal. §12.4 |
| PR-41 | m | §7.2 | The GBDT expert implied a second ML runtime. | Every model exported to ONNX; one runtime, with an E3 + rule-based fallback if it fails to load. §7.2, §15 |
| PR-42 | m | §11 | The TypeScript already in `ui/src/lib` (autocorrelation, entropy, CRC search, sync search, triage) was not reused. | Ported to Python; saves 0.6 pw. §11.1 |
| PR-43 | m | §12.3 | The risk register missed multiple-testing false certificates, real-residual non-Gaussianity, the Meteor variant, calendar compression and 100 % loading. | K14 to K19. §12.3 |
| PR-44 | m | §7.2 | Self-supervised data is biased: KiwiSDR is HF and narrowband, SatNOGS is mostly audio. | Stated as a limitation; rig UHF and RTL-SDR VHF captures added to the unlabelled pool. §7.2 |

**Totals:** 44 findings: 5 critical, 26 major, 13 minor. All dispositioned.

### A.6 v2.1 → v2.2 change log: dependencies

**v2.1** ran a dependency review and cut the runtime to three third-party packages. **v2.2 (team decision)** keeps the full library stack as the primary build: FastAPI + uvicorn, Pydantic + OpenAPI code generation, WebSocket progress, ONNX Runtime for every model, keyring. Libraries that save build effort and are proven in production are an asset, not a liability.

From the review, v2.2 keeps what makes the product ready for any deployment:

- **Offline WebView2.** Tauri's default Windows installer downloads WebView2 from the internet, which fails on an air-gapped machine.
- **Per-user install,** so no admin rights are needed.
- **Browser mode** (`sanjaya serve`) and a **portable folder / run-from-source** fallback.
- **Degraded modes** for the dependencies that can fail on a target machine: ONNX Runtime, the C++ kernels, ReportLab, GNU Radio, cryptography, the Tauri shell.
- **The nightly kill-matrix** that proves no verdict changes when any of them is missing.
- **The deployed tool makes no runtime network calls,** because NTRO machines are air-gapped (NFR-05). External web APIs are used in development and data collection (§15.4).

**Cost:** +0.55 pw, giving P1 = 34.35 pw and a reserve of 3.15 pw (8.4 %). Full treatment in §15.

**Considered and not adopted.** Running file parsers in a separate sandbox process was rejected. The parsers are pure Python and NumPy (memory-safe), so the realistic threats are resource exhaustion and logic bugs. Limits, timeouts, the per-job worker process and fuzzing address those at a fraction of the cost.

### A.7 v2.2 → v2.3 change log: the 10/10 pass

A further strict pass over v2.2. The key assumptions were measured (§16), and the calendar, Meteor and Tauri facts were checked at source. **13 new findings (5 major, 8 minor), all closed:**

| ID | Sev | Where (v2.2) | Finding | Disposition (v2.3) |
|---|---|---|---|---|
| PR-45 | M | §3.4, R-06 | KPI "soft ID needs ≤ 10 % of the hard-rank data for periods 96-1,024" is **mathematically false** at small periods: at N = 96 and p = 3 × 10<sup>−3</sup>, hard rank needs only 256 rows, and 3N soft rows would be 112 % of that | KPI restated as ≤ 3N rows; the gain is given as a function of N·p (≤ 10 % when N·p ≥ 2.7). §3.4, §4.2 C2, §16.3 |
| PR-46 | M | §3.3 | The nominal envelope's "≥ 10<sup>4</sup> symbols" contradicted "period ≤ 1,024": a 1,024-bit interleaver needs ~3N² ≈ 3.1 Mbit | Envelope data condition ≥ max(10<sup>4</sup> symbols, 3N² coded bits). §3.3, R-06 |
| PR-47 | M | §3.4, §4.2 C1 | The deep path allowed 64 proof attempts, but the false-PASS campaign bounded only 8, so a deep-path certificate carried ≤ 8 × 10<sup>−4</sup> | Campaign raised to ≥ 2,000,000 attempts (≤ 2.5 h on the laptop, §12.1): ≤ 10<sup>−4</sup> on both paths |
| PR-48 | M | §11 | No schedule-confidence analysis. Monte Carlo shows the baseline completes within capacity with only **31 %** probability | Threshold / baseline commitment levels; threshold committed at 73 % (≥ NASA's 70 % JCL practice); ladder with pw per rung. §11.6, §11.7 |
| PR-49 | M | §11.3 | G0 was tied to a non-software deliverable and required an engine slice within days | *v2.4:* G0 is an engineering-baseline gate (interfaces, CI, schema, estimates); the vertical slice is at G1. Presentation material is outside this PRD's scope. §11.3 |
| PR-50 | m | A.5 PR-09 | v2's "pure-Python loops ~20 s per 10<sup>6</sup> samples" was wrong by ~80× (measured 0.25 s) | Corrected; only multi-tap LMS and Viterbi stay C++. §6.6, §16.1 |
| PR-51 | m | §2 | The PRD pointed to v3 for its assumptions instead of stating them | A-01 to A-10 in the PRD, each with a fallback. §2.3 |
| PR-52 | m | §8 | No storage or training-compute budget | §8.6: ≈ 60-80 GB total; E2 trains in ~1 GPU-hour; synthetic data generated from seeds, not stored |
| PR-53 | m | §11 | No definition of done | §11.8 |
| PR-54 | m | §12.2 | Model and calibration files not integrity-checked, although they decide certificates | Signed SHA-256 manifest checked at load. §12.2 |
| PR-55 | m | whole | No executive summary; review history before the product; no glossary | "At a glance" up front; review moved to this appendix; §17 glossary |
| PR-56 | m | §12 | Only one long end-to-end run was defined | Scripted acceptance scenario plus a < 3-minute short run (§12.4). *v2.4:* judge Q&A removed (software focus) |
| PR-57 | m | §2, §12 | Finale format (reported 36-hour hackathon) and rules on pre-built code unaddressed | A-09, K21, open item. §2.3, §12.3, §14.1 |

**Totals across all passes:** 57 findings (5 critical, 31 major, 21 minor), all dispositioned.

### A.8 Scorecard of v2.3 (same criteria as A.2)

| Criterion | Weight | v1 | v2.3 | Evidence |
|---|---|---|---|---|
| Technical correctness | 15 % | 4 | 10 | Layered proof shown by measurement (§16.2); ambiguity, coset, constant-envelope and Meteor findings closed; KPI maths re-derived and checked by script |
| Coverage of the PS | 15 % | 8 | 10 | R-01 to R-17 + NFRs, each traced to a module, WP, test, KPI and demo beat (§5.3) |
| Innovation | 15 % | 9 | 10 | Crown innovations with honest limits; third-party-verifiable certificates; propose-and-verify ML |
| Quantitative rigour | 10 % | 5 | 10 | Decision rules; sample sizes derived; multiple testing controlled on both paths; uncertainties on every value |
| Feasibility and schedule | 10 % | 3 | 10 | Resource-levelled; measured compute; threshold committed at 73 % confidence; mechanical ladder with pw |
| Verification and validation | 10 % | 6 | 10 | Layered V&V; commit-reveal sealed sets; out-of-distribution splits; 2 M-attempt campaign; definition of done |
| Architecture and interfaces | 10 % | 6 | 10 | Tree-search orchestrator; interface conventions; compute budget with trip-wires; UI binding contract with a visual gate |
| Data and ML strategy | 5 % | 7 | 10 | Four tiers with truth rules; storage and training budgets; conformal validity on real data |
| Security and deployment | 5 % | 5 | 10 | Anti-rebinding; model integrity; offline WebView2 (verified at source); fallbacks tested nightly |
| Clarity | 5 % | 8 | 10 | One-page summary, glossary, review history in an appendix |
| **Weighted total** | | **6.2** | **10** | |

**What 10/10 means here.** It is the score of the document as a pre-build requirements baseline: every finding is closed, every number is derived or measured, and every fact is verified at source or explicitly flagged with an owner and a date.

A PRD cannot contain results that only the build can produce. Those are pre-registered as targets, with the gate that measures them:
- SIH dates and finale rules: SPOC, now.
- Meteor variant: first capture, G2.
- C++ kernel speed: G1.
- Real-signal KPIs: G5.
