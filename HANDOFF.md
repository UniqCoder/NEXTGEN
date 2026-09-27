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
- **Real data (software only, no hardware — user decision 27 Sep):** no rig, no own captures. Tier 2 = SANJAYA-Gen with measured-style channel/front-end models; Tier 3 = public recordings fetched as files (KiwiSDR public receivers, SatNOGS / SatDump sample recordings incl. Meteor-M LRPT, sigidwiki samples), truth from independent decoders (SatDump, dumphfdl, fldigi).
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

## G2 progress (commit c864d79)
- **Blind search works** (`analyze FILE` with no recipe, `sanjaya/search.py`): symbol rate, roll-off, CFO, clock ppm, frame + sync marker, block-interleaver geometry, rate-1/2 conv code (K 3-9), additive frame-synchronous scrambler (library + exhaustive degree ≤ 8), phase ambiguity, termination, counter / constant fields / CRC (poly by GF(2) gcd, init by inverse). 2-13 s per file. Noise-only → UNDECIDED (exit 2).
- Ambiguity handling that mattered (keep): sync-marker extent decided by block-edge parity checks; I/Q-swap code twins carried as hypotheses; transparent-code complement twins broken by structure (counter direction, termination).
- 30 tests (`scripts/check.py`, ~80 s).

## Engine ↔ UI (commit e71e828)
- **Run the product:** `cd ui && npm run build`, then `cd engine && python -m sanjaya serve --open` → browser opens `http://127.0.0.1:8765/?token=…`; drop a .sigmf-data (+ .sigmf-meta) / .wav / raw IQ → Autopilot runs the engine → every page shows this recording's results; P = proof; certificate is the signed one.
- Without a token (or engine) the UI runs the demo scenario exactly as before.
- API: `/v1/health`, `POST /v1/jobs`, `/v1/jobs/{id}`, `/scenario`, `/spectrogram/{full|resid|fail|rowPower}`, `/certificate.json`. Token header, Host check, Origin allowlist (`--dev` adds the Vite origin).
- Verified in Chrome end to end (drop → blind decode → proof residual at noise floor → signed certificate).
- Known UI gaps: the in-browser triage heuristic (`triage.ts`) mislabels the Gen QPSK file as voice before the engine runs (R-15); Eye / FSK views are still demo drawings; Scene / Genome show engine emitters only (multi-emitter R-17 and genome D5 not built); job worker is a thread, not the PRD's per-job process with memory cap.

## IN PROGRESS (28 Sep) — resume here
User's latest asks: (1) stop emphasising offline mode; lead with problem → solution → how we beat limits nobody else did → **4 strongest USPs**, other innovations as features; (2) a proper plan to a fully working prototype; (3) **real demo recordings selectable in the UI** alongside upload.
- **Done (27 Sep):** `PROTOTYPE_PLAN.md` (problem, solution, 4 USPs = Proof-of-Decode+certificate · blind coding layer · data-sufficiency + multi-sensor stitching · recipe compiler; features table; phases A–E; sample table). `engine/scripts/make_samples.py` builds `engine/samples/` (manifest.json; 6 synthetic SigMF regenerated from seeds, not committed; 6 real HF WAVs converted from sigidwiki MP3s in `samples/src`: STANAG 4285, MIL-188-110A, HFDL, PSK31, SITOR-B, 2G ALE). Mono WAV now lifted to analytic signal (`io.read_wav`). New `measure.occupied_band`, `measure.band_measure` (band-limited rate line + FSK tones).
- **Done (28 Sep) — step 1, real-file measurements fixed:** `occupied_band` rewritten from a floor+rise-dB threshold (broken: on real audio the floor estimate landed inside the signal itself, so STANAG's band collapsed to one bin) to the classic **−20 dB bandwidth** (contiguous run within 20 dB of the peak); SNR/floor now measured only on the same side of Nyquist as the band (skips the analytic signal's empty mirror half, which is a Hilbert-transform artifact, not real noise). FSK tone-detection prominence raised (35th-pct floor, ×12) to drop PSK-sideband clutter. Result: band centres now land within ~150 Hz of every published carrier (STANAG/188-110A 1800 Hz, HFDL 1440 Hz); PSK31 rate 31.25 Bd exact; SITOR-B rate 100.2 Bd exact + clean 2-tone pair (170 Hz shift); ALE 8-tone set matches the MIL-STD-188-141 250 Hz-spaced plan almost exactly. Single-carrier PSK baud-rate line search (STANAG/188-110A/HFDL) still locks onto a sub-multiple on these idle/structured real captures — flagged as an honest limitation, not hidden; real cyclostationary/idle-pattern disambiguation is Phase B (blind modulation classification), not a quick fix. New `engine/tests/test_measure_real.py` (7 tests) pins the fixed cases and would catch a regression like the old one.
- **Done (28 Sep) — step 2, API partial results + sample library:** `GET /v1/samples` serves `engine/samples/manifest.json`; `POST /v1/jobs?sample=<id>` runs one of the built-in demo recordings (no upload needed). `_run()`'s `SearchError` branch now builds a **partial scenario** (`scenario.build_partial`) instead of leaving `job.result` empty: real spectrogram, occupied-band + candidate rate/tones when a band is found, `view.verdict = "undecided"` + `view.reason` + `view.measured`. `/v1/jobs/{id}/scenario` and `/spectrogram/{kind}` therefore now also work on undecided jobs (certificate.json still 409s — there is none). `engine/tests/test_api.py` +3 tests (samples listing, sample-driven job, undecided job → partial scenario incl. spectrogram bytes). 42/42 `scripts/check.py` tests pass.
- **Done (28 Sep) — step 3, UI wired to the sample library and partial results:** `ui/src/lib/engine.ts` gained `listSamples()`/`runSample()`; `ui/src/lib/store.ts` gained `loadSampleLibrary()`/`runSampleJob()` and now bumps `dataVersion` (triggering App.tsx's remount-on-data key) for `undecided` jobs too, not just `done`. `Ingest.tsx` fetches `GET /v1/samples` on mount (when an engine is reachable) and renders it as a clickable "Sample library" table in place of the static demo "Recent recordings"; clicking a row runs it and jumps to Signal. `apply()` in engine.ts now clears (not just skips) the decode-only state (`params`/`proof`/`cert`/`text`/frame/bits/crc/rankProfile/conv/etc.) before merging a job's result, so an undecided job shows "nothing decoded" instead of leftover demo data pretending to be real; `load()` falls back to the real spectrogram / a client-computed rowPower when the partial result has no resid/fail/rowPower to fetch. `Signal.tsx` shows the real measured band/rate/tones with an honest lede when undecided (no more "undefined · undefined Bd" on the waterfall overlay — that was a real bug caught by hand-testing, not just review). `Decoding.tsx`/`Frames.tsx`/`Proof.tsx` each split into a thin outer component (early-returns a `Step` with the shared `Undecided` banner, from `components/Step.tsx`, when `job==='undecided'`) plus an inner `*Ready` component that still assumes a full decode and now only mounts when there is one — needed because their un-split bodies read fields like `SCENARIO.text.chain.map(...)` or `SCENARIO.params.modulation.value` unconditionally and crashed on the smaller partial shape; verified by hand in Chrome (drove `sanjaya serve` and clicked through every step on both an undecided real sample and a normal full-decode sample) rather than just by inspection. `Certificate.tsx` gets the same `Undecided` banner via an early check on `job==='undecided'` ahead of its existing `proof!=='pass'` gate. Also dropped the offline-first copy (Ingest subtitle, status-bar "Offline" chip) per the standing ask. `npx tsc -b` and `npm run build` are clean.
- **Known rough edges left for later, not fixed this pass:** the "candidate tones" shown for a single-carrier PSK undecided job (e.g. STANAG) are spectral noise, not real tones — `build_partial` doesn't yet distinguish "this band looks like FSK" from "this band looks like PSK" before offering a tone list (Phase B classification territory, same root cause as the baud-rate mislock below). The Constellation view's "ACQUIRING · CARRIER SPINNING" demo animation still plays under an undecided job instead of an explicit "no constellation" state — cosmetic, not wrong, deferred.
- **Next steps, in order:**
  1. ~~Fix real-file measurements and add a test comparing them to the published values.~~ done above.
  2. ~~API: `GET /v1/samples` and `POST /v1/jobs?sample=<id>`; partial results when undecided.~~ done above.
  3. ~~UI: sample library + undecided/partial-results wiring on all 5 steps.~~ done above.
  4. PROTOTYPE_PLAN Phase B (more modulations + classification) — this is also where the STANAG/188-110A/HFDL baud-rate mislock and the PSK-vs-FSK tone question above get a real fix (decode-fit / cyclostationary work, not a band-measurement tweak).
- **C++ compiler still missing:** the admin-mode workload install did not complete from the session. User must open Visual Studio Installer → Modify Build Tools 2026 (D:\tools) → tick "Desktop development with C++". Not blocking (NumPy path).
- Browser testing: `sanjaya serve --port 8765 --token demo123`, open `http://127.0.0.1:8765/?token=demo123`; to drop a file from a script, copy it into `ui/dist/_test/` (git-ignored) and dispatch a DragEvent on `.drop`.

## Next actions
1. **Remaining G1 items:** C++ Viterbi within 0.2 dB of oracle (needs toolchain above); Gen v1 taps (clock drift, more mods); FastAPI + UI adapter + visual-regression baseline; Tauri sidecar freeze spike; E1 + E3 v0; sealed-set seed hashes.
2. **G2 path (critical):** blind conv-code + block/conv interleaver ID (GF(2) rank from `_build/feasibility.py`), orchestrator v1, proof calibration on Tiers 1-2, QAM/OQPSK.
3. Collect public recordings (no hardware): Meteor-M LRPT baseband samples (confirm OQPSK, 72k/80k), KiwiSDR HFDL / STANAG 4285 / NAVTEX (multi-site).
4. Confirm with the SPOC: SIH finale date and format (reported: 36-hour finale in December), rules on pre-built code; (no rig: software only).
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
