# HANDOFF: SIH 2026 PS 26147 (NTRO)

**Problem:** Automated model for analysis of .IQ and .wav files along with signal parameter extraction.
**Sponsor:** NTRO. **Theme:** Space Technology. **Category:** Software.
**Status (27 Sep 2026):** **Build started (user go-ahead).** `PRD.md` v2.4 is the build contract. Front-end built in `ui/` (demo data). **Engine G1 vertical slice works in `engine/`** (see "Engine state" below). Git repo initialised at the root (nothing committed yet).

## Files
| File | What it is |
|---|---|
| `PRD.md` | **Build contract v2.4.** Opens with a one-page summary; §1-17 cover the product, requirements, architecture, ML, data, accuracy, UI contract, programme, V&V, dependencies, feasibility evidence and glossary; Appendix A holds the review record (57 findings, all closed), deviations from v3 (V-1..V-14) and change logs. |
| `PRD v1.md` | Superseded first PRD (scored 6.2/10 in review). Kept for the record. |
| `_build/feasibility.py` | Throwaway analysis (not prototype): measures the PRD's compute and proof claims and runs the schedule Monte Carlo. Results are in PRD §16. |
| `winning plan 147 v3.pdf` | Governing plan. The PRD refines it; deviations are listed in PRD Appendix A.4. |
| `introduction to 147.pdf` | PS breakdown, concepts, traps, questions for the mentor. |
| `repos.pdf` | 43 competitor repos ranked (README claims only; snapshot in `_build/data.json`). |
| `UI_PROMPT.md` | UI design brief + PS-compliance rules. |
| `winning plan 147.pdf`, `... v2.pdf` | Superseded plans. `_build/make_*.py` regenerate the PDFs. |
| `ui/` | Front-end; `ui/README.md` has the run instructions and keys. |

## Key decisions (details in PRD)
- **Thesis:** analysis by synthesis with a **layered proof**: PHY by waveform tests (T1-T4, equivalence margins against measured reference noise), coding layer by the parity-membership test K1-K3, structure by S1-S4 (sync, CRC, counters, scrambler). A signed Decode Certificate that anyone can re-check with `sanjaya verify`. False-certificate bound ≤ 10⁻⁴ via a 2,000,000-attempt near-miss campaign.
- **USPs (15):** crown C1-C8 + depth D1-D7 (PRD §4). P1 = C1, C2, C3, C4-lite, C5 + D1, D3, D7 (partial D2, D4, D5, D6).
- **Requirements:** R-01..R-17 + NFR-01..13, fully traced (PRD §5.3). Outcome KPI in the nominal envelope: ≥ 90 % correct-certified, ≤ 10⁻⁴ wrong-certified.
- **ML (PRD §7):** propose and verify. E1 GBDT features + E2 small CNN (< 3 M parameters, ONNX) + E3 physics likelihood; calibration + conformal sets; triage GBDT. The coding layer is deliberately algebra, not ML.
- **Stack (team decision v2.2):** Python + NumPy/SciPy, C++17 kernels via pybind11, FastAPI/uvicorn + Pydantic → OpenAPI → TS types, WebSockets, ONNX Runtime, keyring; Tauri 2 shell (**offline WebView2**, per-user install); GNU Radio only as an optional compiler pack. **No runtime network calls** (air-gap). Every fragile dependency has a fallback proven by a nightly kill-matrix (PRD §15).
- **UI:** design frozen. Only a data-binding refactor is allowed (about 30 demo constants listed in PRD §10.2), gated by pixel-diff visual regression.
- **Real data:** Meteor-M N2-3/N2-4 LRPT (**OQPSK** per SatDump docs and reception guides; 72k/80k; confirm from our first capture), HFDL, STANAG 4285 (PHY only), NAVTEX, multi-site KiwiSDR, SGP4 Doppler; cabled rig Pluto → attenuators → RTL-SDR V4.
- **Programme:** 10 weeks from W1 = 28 Sep 2026; gates G0 (4 Oct, engineering baseline) → G1 (11 Oct) → G2 (25 Oct) → G3 (8 Nov) → G4 (22 Nov) → G5 (29 Nov). **Threshold configuration 31.65 pw committed at 73 % schedule confidence; baseline 34.35 pw is a goal (31 %)**; P2 unfunded. Cut ladder in PRD §11.6.
- **Not doing:** payload decryption, LLM chat, cloud/auth, black-box-only DL, speech content, OFDM (unless the SPOC asks).

## UI state (`ui/`)
- 5-step flow: Recording → Signal → Decoding → Header & payload → Proof (+ Certificate). Tools: Scene, Standards, Challenge, Compliance.
- Real in-browser work: WAV/SigMF parsing, raw-IQ dtype sniffing, triage (`src/lib/triage.ts`), bit autocorrelation / entropy / CRC search. Everything else is demo data (`src/lib/mock.ts`). No `src-tauri` yet.
- Run: `cd ui && npm install && npm run dev` (port 5173).

## Engine state (`engine/`, Python 3.10, NumPy/SciPy/Pydantic/cryptography)
- **Works end to end:** `python -m sanjaya gen` → `analyze FILE --recipe R.json` → `verify FILE certificate.json`. On the Gen v0 file (QPSK 9.6 kBd, CC K=7 (171,133), block 48×32, CCSDS additive scrambler post-FEC, PHY ASM 1ACFFC1D, CRC-16 frames): CFO error < 0.01 Hz, 40/40 frames, 0 info-bit errors at 12 and 8 dB; layered proof PASS (PHY T1-T4 vs measured noise reference, coding K1/K2, structure S1-S4); Ed25519-signed certificate; `verify` reproduces it from the file alone in ~1.7 s.
- **Measured limit (honest):** PHY resolution on roll-off shrinks with SNR (±0.2 rejected at 12 dB, ±0.3 at 8 dB); unrejected neighbours are listed as certificate equivalences.
- **Checks:** `python scripts/check.py` = layering rule (PRD §6.4) + 25 pytest tests (≈ 20 s), incl. wrong-recipe, tampered-certificate and wrong-file cases.
- **Schema 0.1 limits (explicit errors, not silent):** QPSK only; integer samples/symbol; SigMF cf32/ci16 + raw IQ with `--fs --dtype`; known-recipe mode only (`attempts_k = 1`, `false_pass_bound = null` until the G5 campaign); proof thresholds are `v0-defaults` until the G2 calibration.
- **C++ kernels blocked on toolchain:** this machine has only 32-bit MinGW GCC 6.3 (cannot build 64-bit Python extensions). Install MSVC Build Tools or mingw-w64 (x86_64) for WP05; the NumPy path is the PRD's mandated fallback and is what runs now.

## Next actions
1. **Remaining G1 items:** C++ Viterbi within 0.2 dB of oracle (needs toolchain above); Gen v1 taps (clock drift, more mods); FastAPI + UI adapter + visual-regression baseline; Tauri sidecar freeze spike; E1 + E3 v0; sealed-set seed hashes.
2. **G2 path (critical):** blind conv-code + block/conv interleaver ID (GF(2) rank from `_build/feasibility.py`), orchestrator v1, proof calibration on Tiers 1-2, QAM/OQPSK.
3. Record real data early: Meteor passes (confirm OQPSK and 72k/80k), KiwiSDR (HFDL, STANAG 4285, NAVTEX; multi-site).
4. Confirm with the SPOC: SIH finale date and format (reported: 36-hour finale in December), rules on pre-built code; get institute approval for the cabled rig.
5. Pending from earlier: the user asked for a standalone version of the 3D terrain model (`ui/src/components/Terrain.tsx`). It was interrupted; ask before resuming.

## Working preferences
- Never use subagents (saved in memory).
- **Software focus only:** no PPT, deck, video or pitch material anywhere.
- Keep the library stack as primary; keep fallbacks for readiness.
- Space-agency rigour: verify facts at source, derive and check numbers by script, no overclaiming.

## Caveats
- SIH dates, sponsor and theme come from secondary sources; confirm on sih.gov.in and with the SPOC.
- Competitor counts are README claims (snapshot 26 Sep 2026).
- All KPIs are pre-registered targets. Unmeasured so far: C++ kernel speed, recognition and proof stage times, real-signal behaviour.
