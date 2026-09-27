import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY, ACCENT, LIGHT = colors.HexColor("#1b2a4a"), colors.HexColor("#2f6fb3"), colors.HexColor("#eef3fa")
body = ParagraphStyle("b", fontName="Arial", fontSize=9.5, leading=13, spaceAfter=4)
small = ParagraphStyle("s", fontName="Arial", fontSize=7.3, leading=9.2)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=6, spaceAfter=6)
title = ParagraphStyle("t", parent=body, fontName="Arial-Bold", fontSize=24, leading=30, textColor=NAVY)
bullet = ParagraphStyle("bl", parent=body, leftIndent=12, bulletIndent=3, spaceAfter=2)

meta = {d["name"]: d for d in json.load(open("data.json", encoding="utf-8"))}
meta["NaidhruvK/wavSIH26"] = {"commits": "100+", "created": "2026-09 (pushed 09-14)"}
meta["Muizzahmed786/SIH26147"] = {"commits": "?", "created": "2026-09 (pushed 09-18)"}

# (repo, USP, features, solution vs PS / coverage, score, strength note)
# Coverage keys: G=GUI P=params D=demod I=de-interleave F=FEC C=bit correlation ; Y=yes P=partial N=no
R = [
("ShantanuSomwanshi/SIH-Rf-Signal-Intelligence",
 "Cleanest 1:1 mapping of every PS clause to a source file. Blindly identifies interleaver <b>including exact size / PN seed</b> and FEC type; 7 ground-truth sample files cover every combo.",
 "WAV (stereo IQ / mono real), raw IQ cf32/ci16/ci8/cu8; BPSK, QPSK, 8PSK, 16QAM, 2/4/8-FSK; conv K=3/5/7 soft Viterbi, RS, RS+conv concatenated, LDPC min-sum; block/diagonal/convolutional/PN de-interleave; sync-word + blind bit-constancy header finder; GUI: spectrum, waterfall, constellation, eye, symbol-rate line.",
 "Full chain file -> params -> demod -> de-interleave -> FEC -> header/payload. Offline pure Python. Fs for headerless IQ from filename hint or analyst.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 9.0, "Most complete coverage of i-v with ground-truth samples; compact codebase (17 files, few commits)."),
("NaidhruvK/wavSIH26",
 "Most rigorous team engineering: staged pipeline S0-S6 with contracts, a seeded signal 'zoo' corpus with truth JSON, and an eval harness that found and fixed real estimator biases.",
 "Ranked-hypothesis raw IQ dtype sniffer; PSD/SNR/burst detect; receiver with carrier, timing, equaliser, lock-check, soft demap; GF(2) rank-collapse interleaver recovery, PN interleavers, phase-rotation search; conv/RS/LDPC catalogue decoders; descrambler, CCSDS framing, payload extraction; ML classifier; Docker.",
 "Blind recovery chain down to CCSDS frames, validated against its own corpus with measured metrics. README is empty - no GUI evident.",
 "G:N? P:Y D:Y I:Y F:Y C:Y", 8.8, "Deepest verified DSP + coding work (100 commits); weak on GUI/docs."),
("Gururaghavendra123/sihps2-2026",
 "Answers are <b>verified by hard ground truth</b> (CRC-16, sync correlation, re-encode BER) instead of heuristic %; adaptive coarse-to-fine candidate search gives 4-5x speedup over brute force; says 'unknown' rather than false positives.",
 "Oerder-Meyr symbol rate, cumulants C20/C40/C42; BPSK, QPSK, 8PSK, 16QAM, 2/4-FSK; M&M timing, Costas; block/conv/diagonal/PN; Viterbi K=7, RS(255,223), concatenated, LDPC BP; PyQt6 desktop + FastAPI web dashboard; DEEPDIVE.md math doc.",
 "Catalogue-bounded blind identification (6 mod x 4 FEC x 4 interleavers = 96 hypotheses) with verification gate, then payload extraction.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 8.6, "Complete and honest; blind only within a fixed catalogue."),
("WaghJagdish/PS147",
 "Hypothesis-driven <b>beam search</b> with composite confidence (AMC margin, GF(2) rank drop, FEC syndrome ratio) and aleatoric-vs-epistemic uncertainty labels; self-verifying payload states.",
 "Raw IQ dtype selector with ambiguity warning; CFAR emission band overlay; PSD, waterfall, I/Q scope, constellation; HOC + ML classifier; block & conv de-interleavers via GF(2) rank; conv, RS, LDPC, FEC estimator; descrambler, frame sync; hex/ASCII payload viewer; in-UI synthetic generator; FastAPI + React.",
 "End-to-end blind search over modulation/interleaver/FEC with explicit uncertainty; web workstation GUI.",
 "G:Y P:Y D:Y I:P F:Y C:Y", 8.5, "Strong design & explainability; single bulk commit, diagonal/PN not evident."),
("yoganandasp15/SIH_2026_Signal-Analyser",
 "'Physics first' epistemic engine: measure -> hypothesise -> search for contradictions -> validation gates; six explicit verdict states (VALIDATED, ...). Argues against black-box DL for SIGINT.",
 "Preprocessing (DC, IQ imbalance, AGC, resampler); cumulant, cyclostationary, phase, spectral features; PSK/QAM/FSK demod with LLR soft output; block/conv/diagonal/PN de-interleave engine; concatenated, Viterbi, RS, LDPC; GUI app + CLI.",
 "Autonomous blind parameter engine + candidate ranker + contradiction analyzer feeding full decode chain.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 8.4, "Very broad and well argued (104 code files); only 2 commits, claims untested by us."),
("The-4Script/RadioFry",
 "Heaviest <b>ML</b> story: trained CNN modulation model (RadioML 2018 + augmentation) plus separate trained <b>interleaver and FEC classifiers</b>; GNU Radio integration; 13-page Streamlit app.",
 "Pages: upload, parameters, modulation, demod, de-interleaving, FEC, correlation, report, 'time machine', cyclostationary, capability, fusion landscape, 'signal DNA'; RadioML 2016/2018 + real-world multipath loaders; de-interleave search; bit-structure analysis.",
 "Hybrid ML + DSP pipeline; missing model artefacts reported as unavailable instead of faked.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 8.2, "Most mature ML (100 commits). forge-script/RadioFry is a copy of this repo."),
("Venkata-Manoj/RF-signal-analysis",
 "FEC + interleaver reported <b>only when proven by a CRC check</b>; three interfaces (desktop, web, CLI); tested on real over-the-air recordings and benchmarked vs SNR.",
 "BPSK, QPSK, 8PSK, 16/64-QAM, 2/4-FSK with confidence; Fs, BW, symbol rate, CFO, SNR, EVM/MER; sync-word header position; decoded text/hex/ASCII; 8-tab GUI (time, spectrum, waterfall, constellation, eye...); batch analysis; OTA eval + performance benchmarks.",
 "Full pipeline with conservative 'verified' semantics and batch mode.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 8.0, "Polished and user-friendly (51 commits); repo also carries unrelated UI-tooling scripts."),
("SomeNobody21112/ICHNOVA",
 "Only repo <b>validated on real government transmissions</b> (WWV, DCF77, MSF, JJY, DDH47 RTTY, All India Radio via KiwiSDR) with GPS-checked results; statistical significance corrected for number of hypotheses tried.",
 "Blind CFO, symbol rate, BPSK/QPSK, phase search; conv codes K=3/5/7 r=1/2 x block interleaver with dual-code syndrome test; outcomes DECODED / SIGNAL_NO_CODE / UNKNOWN; bench suites, null set, performance reports; React dashboard.",
 "Narrow but deep: blind code+interleaver recovery with false-positive control and real-signal proof.",
 "G:Y P:Y D:P I:P F:P C:Y", 7.8, "Best scientific credibility (75 commits); limited modulation/FEC range."),
("Rohanbhandari9703/SignalIQ",
 "Classic analyst desktop tool: PySide6 + pyqtgraph 12-stage pipeline with a <b>brute-force FEC x de-interleaver grid search</b>; builds a standalone .exe.",
 "WAV, raw IQ (cf32/cf64/ci16/ci8), SigMF; Welch PSD, spectrogram, BW; M2M4 SNR; CFO power-of-N; cyclostationary symbol rate; Random Forest AMC (92.5% CV) BPSK/QPSK/8PSK/16QAM/2FSK/4FSK; Costas, Gardner; Viterbi K=7, RS(255,223); CCSDS ASM / Barker sync; eye diagram, bit viewer; JSON report, session save.",
 "Automatic 'Run Pipeline (F5)' from file to frames.",
 "G:Y P:Y D:Y I:P F:P C:Y", 7.6, "Solid, focused; no LDPC, 1 commit."),
("EDM-Fan/Nova-Signum---Signal-Analyzer-",
 "Explicit <b>phase-ambiguity resolution</b> (0/90/180/270) during frame sync plus blind FEC auto-detection across RS/LDPC/concat/conv with 4 de-interleaver architectures.",
 "Random Forest on cumulants/kurtosis (BPSK, QPSK, 16QAM, 2FSK); CFO, Gardner/M&M; sync words 0xEB902A3C / CCSDS; RS(64,48)/(32,24), LDPC(128,64), K=7 conv; PDF/JSON/CSV report; cyclostationary baud on load; PySide6 GUI; many demo generators.",
 "Full chain with re-encode match metric and ground-truth BER on synthetic files.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 7.5, "Complete but only 4 modulations; 1 commit."),
("rabishankar21/SignalSight",
 "Desktop suite covering <b>every listed item</b> including 64QAM and LDPC(256,128) min-sum, with separate validation scripts per stage.",
 "IQ/WAV ingest, preprocessing, PSD, waterfall, constellation, SNR, BW, symbol rate, CFO; BPSK/QPSK/8PSK/2FSK/16QAM/64QAM; Viterbi, RS, concat, LDPC; block/conv/diagonal/PN; interleaver & FEC detectors; bitstream correlation, frame-boundary detection.",
 "Full chain in a desktop GUI.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 7.4, "Feature-complete; many UI-patch scripts suggest GUI churn."),
("arachknight66/SIH26147",
 "Only repo with a real <b>C++20 core + pybind11</b> (soft Viterbi K=7, RS, LDPC, correlation, CRC, PSD/STFT, receivers) and chunked streaming for big files.",
 "6-layer forensic pipeline (ingest, stats, blind AMC, sync, de-interleave+FEC, frame recovery); epistemic gating; headless CLI + PySide6 GUI; C++ unit tests & benchmarks.",
 "Performance-oriented pipeline; README admits native decoders are configured, not blind.",
 "G:Y P:Y D:Y I:P F:Y C:Y", 7.4, "Best performance engineering (40 commits); blind coding-layer weak."),
("Krezmitent/SigNull",
 "Same 'Signal Analysis MVP' 6-layer architecture as arachknight66 (shared origin) in pure Python, adding <b>OFDM</b> and vectorised CRC search.",
 "Loaders, rate estimation, sync, demod, de-interleaving, conv/RS/LDPC/concat FEC, hypotheses, framing, correlation; CLI JSON + PySide6 GUI; stereo WAV real-vs-IQ prompt.",
 "Full chain with explicit certainty gating.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 7.2, "Broad (40 commits); overlaps heavily with arachknight66."),
("Alekhkr/PS2",
 "Scientific-instrument style desktop app with <b>per-parameter provenance</b> (ParameterEvidence) and C++ fast kernels.",
 "Canonical SignalBuffer ingest; DC/IQ-imbalance conditioning; synced time/PSD/waterfall/constellation; carrier, BW, SNR, symbol-rate candidates; hybrid classifier; FSK/BPSK/QPSK/8PSK/QAM16/64 demod; Viterbi, RS, LDPC, concat hypothesis engines; correlator.",
 "Full chain in PySide6 + PyQtGraph.",
 "G:Y P:Y D:Y I:P F:Y C:Y", 7.0, "Good structure; thin README, 4 commits."),
("harikesh2709-creator/spectra-signal-analyzer",
 "Most <b>presentation-ready</b>: 5-min narrated demo video, decks, infographic; 60 FPS WebGL waterfall; team FUTURISTICS.",
 "DDC, RRC, Gardner/Costas sync, AMC + trained model, baud & SNR estimators, blind interleaver detector, de-interleaver, Viterbi, RS, LDPC, concatenated, correlator, frame parser, generator; FastAPI + web UI.",
 "Full chain claimed in an 'air-gapped SIGINT terminal' UI.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 7.0, "Code covers everything but claims are marketing-heavy; 4 commits."),
("ashcodes1511/SIH-2026-Chroma-Code",
 "Adds <b>cyber-forensics</b>: Shannon entropy to tell plaintext vs encrypted payload, plus a 1D-CNN modulation classifier.",
 "Multi-SDR binary parser (RTL-SDR, HackRF, BladeRF, USRP); Hilbert for mono WAV; normaliser; heuristic + CNN AMC; RRC, Costas, M&M; PSK/QAM/FSK; de-interleaver; Viterbi, RS; sync detector; FastAPI dashboard.",
 "Pipeline extends past the PS into payload forensics.",
 "G:Y P:Y D:Y I:P F:P C:Y", 6.9, "Good breadth; no LDPC; 9 commits."),
("Devansh-567/hackathon",
 "Most <b>honestly documented</b> backend: 188/188 tests, 5-state honesty vocabulary, 'what's not built yet' list; handles huge files via memory-mapped chunking.",
 "WAV + raw IQ + full SigMF datatype parser; synthetic generator (7 mods, impairments); rule-based explainable classifier (M-th power); PSK/QAM/FSK demod with EVM/lock; conv+Viterbi (commpy), RS (reedsolo) with syndrome self-check; interleavers; JSON/CSV/PDF/SigMF reports; React UI with batch, compare, similar-signal fingerprinting; pitch deck.",
 "Tested foundation; LDPC and some coding layers not complete.",
 "G:Y P:Y D:Y I:P F:P C:P", 6.9, "High engineering quality, incomplete scope."),
("karurravishankermohit-stack/-SignalX",
 "Strict <b>provenance labels</b> on every value (METADATA / USER / DSP_ESTIMATED / AUTO_CLASSIFIED / DEMO / UNAVAILABLE); 17-stage pipeline.",
 "Parser, preprocessing, spectrum, waterfall, constellation, parameter estimator, modulation classifier, demod, interleave detector, FEC codec/detector (Viterbi, RS, concat, LDPC check), frame detector, correlation; FastAPI + React/Plotly; SQLite sessions; Firebase auth.",
 "Full workstation with case management.",
 "G:Y P:Y D:Y I:Y F:P C:Y", 6.8, "Broad (32 commits); web/auth overhead."),
("arunkumarmeda27/SpectraSync",
 "Enterprise infra: auth, RBAC, Docker, Postgres/Redis, <b>WebSocket live stage progress</b>, forensic PDF reports, 6 golden demo vectors.",
 "13-stage DSP pipeline; cumulant (C40/C42/C63) + Random Forest AMC incl AM/FM; carrier/clock recovery; de-interleave; FEC; bitstream analysis; cross-correlation; 8-panel neon dashboard; files up to 2 GB.",
 "Full pipeline wrapped in production web stack.",
 "G:Y P:Y D:Y I:P F:P C:Y", 6.6, "Infra outweighs DSP depth; no LDPC evident."),
("Andro-HM/IQWAV",
 "Research-grade <b>experiment log</b>: head-to-head symbol-rate and timing benchmarks, held-out validation, blind occupied-band detection on real IQ, notebooks. (Mirror: iamsayandas2-blip/IQWAV.)",
 "WAV / stereo-IQ / raw IQ ingest; activity & band extraction; PSD, spectrogram; BW, CFO, noise, symbol rate; rule-based AMC with dataset/eval; auto/cross-correlation; analog FM demod; impairments model.",
 "Parameter estimation done carefully; FEC/de-interleaving still future work.",
 "G:P P:Y D:P I:N F:N C:P", 6.4, "Best research discipline (39 commits); coding layer missing."),
("aayushkasurde112-cell/RF_MVP",
 "Strong DSP fundamentals: <b>raw-IQ dtype auto-guess</b> by file-size modulo + float plausibility probe, multi-signal CFAR channelisation, Farrow interpolator.",
 "SigMF sidecar writer; Welch PSD + median/MAD CFAR; burst channelisation; delay-multiply/envelope baud lines; HOC C40/C42/C63 decision tree; M-th power CFO, Gardner+Farrow, Costas, FSK discriminator; later phases: demod, interleaver, FEC, bitstream, FastAPI server.",
 "Stateless library pipeline designed to run per-chunk in a streaming backend.",
 "G:N P:Y D:Y I:P F:P C:P", 6.3, "Good core; GUI not built."),
("Jagzz-Coder/sigscope",
 "Runs <b>100% in the browser</b> (pure JS, no backend): blind convolutional-code identification + Viterbi and GF(2) rank-sweep structure detection.",
 "Symbol rate, CFO, 7 modulations, demod, sync-word/frame correlation, outer block code; 38 passing Node tests over a full concatenated chain.",
 "Blind chain in a single JS core file.",
 "G:Y P:Y D:Y I:P F:P C:Y", 6.2, "Clever and tested; tiny codebase, no LDPC."),
("Priyanshugrawal/AutoSIG",
 "Guided 8-stage Streamlit dashboard with a <b>recovery validation</b> stage (CRC/parity, overall recovery score).",
 "Validation, DC/IQ correction, burst detection, PSD/waterfall/constellation, BW/SNR/symbol rate/CFO; ML AMC (FSK..64QAM) + ranked FEC/interleaver hypotheses; demod, de-interleave, Viterbi/RS/concat/LDPC-heuristic; header/payload parse; report.",
 "Full chain, hypothesis chosen from ML ranking.",
 "G:Y P:Y D:Y I:Y F:P C:Y", 6.0, "Covers list; LDPC heuristic; 1 commit, 14 files."),
("tejaswi-jain2007/SIGNEX",
 "<b>ResNet-18 AMC</b> over 10+ classes incl 16/32APSK and OFDM; air-gapped design, audit logs, batch queue.",
 "FastAPI + React; time/spectrum/spectrogram/constellation; hex/ASCII bitstream; interleaver, FEC, correlator, text decoder modules; PDF/JSON dossiers.",
 "DL-first classification with decode modules attached.",
 "G:Y P:Y D:Y I:P F:P C:Y", 5.9, "Depth of coding layer unclear."),
("RohithvijayR/SIGNALX",
 "Only repo doing <b>IQ + WAV multi-modal fusion</b> (paired files, IQ-only vs WAV-only vs fused predictions) - directly echoes the PS line about training data 'containing both .IQ and .wav'.",
 "Parsers for IQ (several dtypes), WAV, SigMF; time/FFT/Welch/STFT/constellation; SNR/BW; ML classifier; FEC and interleaver <i>detectors</i>; ground-truth comparison table; React dashboard; history DB.",
 "Profiles the signal; decoding not evident.",
 "G:Y P:Y D:N I:P F:P C:N", 5.8, "Unique fusion idea; no demod/decoding."),
("GaurangJagtap/Radio-Frequency-Signal-Analyzer",
 "Explainable-RF 'math trace' and cascade gate; even a voice controller.",
 "Cyclostationary, multi-domain features, ML classifier, demodulators, de-interleavers, FEC decoders incl LDPC & concatenated, bitstream correlator, payload extractor; SDR-style dark GUI.",
 "README still says 'prototype with mock data' while code tree has real modules.",
 "G:Y P:Y D:Y I:Y F:Y C:Y", 5.6, "Inconsistent docs vs code; 1 commit."),
("anshumanarchit-crypto/machine-learning-SIH",
 "Evidence-first <b>decision layer</b>: rule vs ML (Random Forest) consensus, calibrated abstention to UNKNOWN, evidence ledger, replay engine.",
 "Cumulants C20..C80, M2M4 SNR, EVM, cluster metrics; threshold sweeps & calibration; Streamlit GUI reading result.json.",
 "One member's slice of a team pipeline; demod/FEC in other repos.",
 "G:Y P:Y D:N I:N F:N C:N", 5.4, "Good confidence engineering, partial by design."),
("VASANTH-Balaji/signal-analyzer-webapp",
 "Streamlit <b>public web deployment</b> of a desktop analyzer's backend.",
 "Blind detect, symbol-rate estimate, modulation classifier, BPSK + general demod, FEC core, RS, LDPC, bitstream correlation; sample .iq files.",
 "Full-ish chain exposed via web.",
 "G:Y P:Y D:Y I:N F:P C:Y", 5.3, "Thin docs, 13 files."),
("NirmitSingh-main/SYNAPS",
 "Heavy AI: CNN, Transformer and <b>self-supervised MAE</b> models, unknown-signal detection, LLM 'copilot'. (Forks: SiddhantMenon14, pratyushh2.)",
 "IQ/WAV loaders, spectrogram/constellation, training & eval, confidence, analysis/report APIs, React frontend, Supabase.",
 "Classification + assistant; coding layer limited.",
 "G:Y P:Y D:P I:P F:N C:P", 5.0, "Ambitious ML, minimal README (38 commits)."),
("pranshu1141-sharma/Pinpoint",
 "Exceptional documentation: requirement-by-requirement status, <b>judge-defense answers</b>, 1 GiB processing evidence.",
 "Time/frequency region detection, pulse timing, isolation layers, coarse envelope + BPSK/QPSK classification, symbol rate, SigMF, calibration corpus; React dashboard.",
 "Explicitly <b>no demodulation or decoding</b>.",
 "G:Y P:Y D:N I:N F:N C:N", 4.9, "Honest but covers only task (i) partly."),
("gourabde7/Spectra",
 "Smallest end-to-end demo: one GUI with 6 tabs + 'Run Full Pipeline' button.",
 "Loader (cf32/ci16/cu8); spectrum, waterfall, constellation; BPSK/QPSK/16QAM/FSK; 4 de-interleavers; Viterbi K=7, RS, LDPC, concat; preamble search; demo signal generator; architecture slide.",
 "Self-described ideation-round prototype using heuristics.",
 "G:Y P:P D:Y I:Y F:P C:Y", 4.8, "Breadth with shallow depth (8 files)."),
("sautiksamui-tech/SIH2026",
 "Simple PySide6 app with demo mode.",
 "WAV/raw IQ; PSD, OBW, SNR, CFO; evidence-based modulation candidates; Costas BPSK/QPSK; interleaver search + basic FEC framework; tests.",
 "Timing/FEC partly stubs.",
 "G:Y P:Y D:P I:P F:P C:N", 4.3, "Early-stage."),
("Akshat030307/SIH",
 "Focus on <b>multi-signal captures</b>: per-signal boxes on spectrogram, SigMF annotations, broad classes (AM/FM/SSB/CW/FSK/PSK/QAM/OFDM/chirp).",
 "RadioML 2016 loader, file I/O with dtype guesser and filename parsers; spectrogram, noise floor, detector (WIP); CNN planned.",
 "Phase 3 of 8 in progress; no demod/FEC yet.",
 "G:N P:P D:N I:N F:N C:N", 4.2, "Good plan, early."),
("PradhanaService/sanket",
 "<b>C++20 / Qt6</b> high-performance viewer: zero-copy mmap of 50 GB+ files, AVX2 SIMD, FFTW waterfall; GNU Radio C++ signal generator.",
 "IQ/WAV readers, waterfall, constellation, time plot, feature extractor, playback controls.",
 "Visualisation layer only.",
 "G:Y P:P D:N I:N F:N C:N", 4.1, "Great performance, tiny scope."),
("hn260/signalscope",
 "Offline Streamlit analyzer with an explicit <b>honesty policy</b> (relative vs absolute frequency, two BW methods).",
 "IQ/WAV ingest, waveform/spectrum/spectrogram, params with confidence, statistical modulation classifier, JSON/CSV reports, tests.",
 "Parameters + classification only.",
 "G:Y P:Y D:N I:N F:N C:N", 3.8, "Clean but narrow."),
("kunal-shetty/SIH2026_Signal_Intelligence_Recognition_Engine",
 "'<b>Shazam for radio signals</b>': RadioML 2016 CNN, 11 classes, < 2 s per file, batch of 50.",
 "IQ/WAV parse, centre freq/BW/SNR/symbol rate, spectrogram/PSD/waveform, FastAPI + React, Docker, synthetic test endpoint.",
 "Classification + parameters only.",
 "G:Y P:Y D:N I:N F:N C:N", 3.8, "Covers only task (i) partly."),
("DevWithShubham18/SAGE-RF",
 "Actually <b>deployed</b> (Vercel + Render) with Firebase auth and an LLM RF assistant.",
 "Spectral analysis, waterfall, signal detection, modulation estimation, Fourier/Laplace views, history, PDF reports.",
 "General RF workstation; no demod/FEC.",
 "G:Y P:P D:N I:N F:N C:N", 3.6, "Off the PS core."),
("vedantpanchal77/Team-Overflow",
 "DSP metrics + <b>Gemini-generated</b> diagnostic reports with heuristic fallback.",
 "IQ (cf32/cs16/cu8) and WAV; time, frequency and RF metrics (IQ imbalance, OBW, spectral flatness); candidate modulation; Plotly quad view.",
 "Measurement dashboard only.",
 "G:Y P:Y D:N I:N F:N C:N", 3.4, "Narrow; LLM reliance."),
("Selvamurugan-hub/SpectraSense-AI",
 "Signal <b>fingerprinting</b>, historical baseline comparison and anomaly detection.",
 "IQ/WAV loader, segmentation, parameter extraction, health score, 'what changed' table, PDF reports, React UI.",
 "Reframes PS as monitoring/anomaly - misses demod/FEC.",
 "G:Y P:P D:N I:N F:N C:N", 3.3, "Misaligned with PS asks."),
("SrishtiPriya27/signalscope",
 "Polished React/Vite <b>frontend-only</b> workstation (Vercel-ready).",
 "Pages for every stage (spectrum, constellation, demod, de-interleave, FEC, correlation, report) but results come from a MockSignalProcessingClient.",
 "UI mock-up; processing is simulated.",
 "G:Y P:N D:N I:N F:N C:N", 2.8, "Good UI reference only."),
("adityabisoyee28-cpu/SignalLens-AI",
 "Supabase-backed web app with Random Forest over 6 toy classes (sine, AM, FM, PM...).",
 "WAV/IQ (RTL-SDR uint8, complex64); time/FFT/PSD/spectrogram/constellation; 11-dim features.",
 "Classifies analog toy signals - not the digital mods the PS needs.",
 "G:Y P:P D:N I:N F:N C:N", 2.6, "Weak fit."),
("Muizzahmed786/SIH26147",
 "Planning only: 'PROJECT_BRAIN' markdown set (architecture, DSP, FEC & interleaving, ML, MVP scope, phases).",
 "Documentation, no code.", "Design notes.", "G:N P:N D:N I:N F:N C:N", 1.8, "Useful reading, nothing built."),
("xarjunpatil/SIH26147-Automated-model-for-analysis-of-IQ-and-wav-files-along-with-signal",
 "Repo named after the PS with full PS text in README.",
 "Single app.py + test, Dockerfile.", "Skeleton.", "G:P P:N D:N I:N F:N C:N", 1.5, "Placeholder."),
]

EXCLUDED = [
    ("forge-script/RadioFry", "Copy of The-4Script/RadioFry (same README/code, 1 commit)."),
    ("SiddhantMenon14/SYNAPS, pratyushh2/SYNAPS", "Forks of NirmitSingh-main/SYNAPS."),
    ("iamsayandas2-blip/IQWAV", "Mirror of Andro-HM/IQWAV (same project/README)."),
    ("harikesh2709-creator/FUTURISTICS", "Different problem (ocean freight forecasting), despite search hits."),
    ("harshgounder/sih-2026", "Different problem (SIH26166)."),
    ("mks-Roald/ps26147_toolkit, iparayush/SignalLens-AI-", "Indexed on the web but now 404 (deleted or private)."),
    ("harideskzone-hue/SIH26147-Border", "Empty repository."),
    ("AryanSahu321/sih, jeevansai-hub/SIH-2026-, Vigneshrdy/sih-ps-archive, Rajkumar-Porandla/SIH-2026-Problem-Statements, "
     "NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements, Abhinav-Prabhakar/SIH2026, Ardcode12/SIH26soft",
     "Lists / archives of all SIH problem statements, not solutions."),
]

story = []
P = lambda t, s=body: story.append(Paragraph(t, s))

P("Repos - SIH 26147 on GitHub", title)
P("Public GitHub repositories attempting <i>Automated model for analysis of .IQ and .wav files along with signal parameter "
  "extraction</i> (NTRO, SIH 2026), ranked strongest to weakest.", ParagraphStyle("st", parent=body, fontSize=12, leading=16, textColor=ACCENT))
story.append(Spacer(1, 6))
P("How this was built", h1)
for t in [
    "Searched GitHub (repo name, description, README and code search) for 26147 / SIH26147 / PS26147, the PS title, and topic "
    "keywords (IQ, wav, demodulation, de-interleaving, Viterbi, NTRO, SIH 2026), plus a web search. ~150 hits filtered to "
    f"<b>{len(R)} relevant repos</b>; {sum(len(e[0].split(',')) for e in EXCLUDED)} more listed in the appendix as excluded.",
    "Nothing was cloned or run. Each repo was judged from its README, full file tree, languages and commit count via the GitHub API "
    "(snapshot 26 Sep 2026). Features are <b>as claimed</b> by the team; many READMEs are AI-written and optimistic.",
    "<b>Coverage</b> column maps to the PS: G = GUI, P = parameter identification (i), D = demodulation FSK/PSK/QAM (ii), "
    "I = de-interleaving block/conv/diagonal/PN (iii), F = FEC Viterbi/RS/concat/LDPC (iv), C = bit-stream correlation / header-payload (v). "
    "Y = present, P = partial, N = not evident.",
    "<b>Strength /10</b> weighs: coverage of i-v + GUI (50%), evidence it works - tests, ground-truth samples, real signals, commit "
    "history (30%), and depth of blind analysis vs. configured decoding (20%)."]:
    story.append(Paragraph(t, bullet, bulletText="\u2022"))

P("Landscape at a glance", h1)
strong = sum(r[5] >= 7 for r in R); mid = sum(5 <= r[5] < 7 for r in R); weak = sum(r[5] < 5 for r in R)
for t in [
    f"<b>{strong}</b> repos score 7+ (claim the full i-v chain with real code), <b>{mid}</b> are mid (5-7), <b>{weak}</b> are early, narrow or off-target.",
    "Almost everyone does: file loader, PSD/waterfall/constellation, cumulant or ML modulation classifier, PSK/QAM/FSK demod, "
    "K=7 Viterbi + RS(255,223), CCSDS sync-word search. This is now <b>table stakes</b>.",
    "Rare (real differentiators): validation on <b>real over-the-air signals</b> (only ICHNOVA, Venkata-Manoj), <b>truly blind</b> "
    "interleaver size / PN-seed recovery via GF(2) rank (ShantanuSomwanshi, NaidhruvK, WaghJagdish), verification by CRC/re-encode "
    "instead of fake confidence (SIG-ID, Venkata-Manoj), <b>C++ performance</b> (arachknight66, Alekhkr, sanket), IQ+WAV fusion (SIGNALX).",
    "Weak spots across the field: blind LDPC (everyone uses a fixed catalogue), HF fading/equalisation, multi-signal captures, "
    "scramblers, and most GUIs are web dashboards rather than analyst desktop tools.",
    "Common style trend: 'epistemic honesty' - explicit UNKNOWN states, provenance labels, confidence gates. Judges will likely see this in many entries."]:
    story.append(Paragraph(t, bullet, bulletText="\u2022"))

story.append(PageBreak())
P("Ranked repositories", h1)
hdr = ["#", "Repository", "USP", "Features", "Solution vs PS (coverage)", "Strength"]
rows = [[Paragraph(f'<font color="white"><b>{h}</b></font>', small) for h in hdr]]
for i, (name, usp, feat, sol, cov, score, note) in enumerate(R, 1):
    m = meta.get(name, {})
    url = f"https://github.com/{name}"
    info = f"{m.get('commits', '?')} commits, created {m.get('created', '?')}" if m else ""
    rows.append([Paragraph(str(i), small),
                 Paragraph(f'<link href="{url}"><font color="#2f6fb3"><u>{name}</u></font></link><br/><font color="grey">{info}</font>', small),
                 Paragraph(usp, small), Paragraph(feat, small),
                 Paragraph(f"{sol}<br/><b>{cov}</b>", small),
                 Paragraph(f"<b>{score:.1f}/10</b><br/>{note}", small)])
t = Table(rows, colWidths=[7 * mm, 42 * mm, 58 * mm, 88 * mm, 46 * mm, 36 * mm], repeatRows=1)
st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d6")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
      ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
      ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
for i, r in enumerate(R, 1):
    c = "#d7f0dc" if r[5] >= 7 else "#fff1cc" if r[5] >= 5 else "#f8dada"
    st.append(("BACKGROUND", (5, i), (5, i), colors.HexColor(c)))
t.setStyle(TableStyle(st))
story.append(t)

story.append(PageBreak())
P("Appendix - found but excluded", h1)
ex = [[Paragraph('<font color="white"><b>Repository</b></font>', small), Paragraph('<font color="white"><b>Why excluded</b></font>', small)]]
for n, why in EXCLUDED:
    links = ", ".join(f'<link href="https://github.com/{x.strip()}"><font color="#2f6fb3"><u>{x.strip()}</u></font></link>' for x in n.split(","))
    ex.append([Paragraph(links, small), Paragraph(why, small)])
et = Table(ex, colWidths=[150 * mm, 127 * mm])
et.setStyle(TableStyle(st[:5]))
story.append(et)
story.append(Spacer(1, 8))
P("<i>Search limits: GitHub search only indexes public repos and some READMEs lag; private or newly-created repos, or ones without the PS "
  "number/title in name, description or README, can be missed. Scores are a desk judgement from READMEs and file trees, not from running the code.</i>")

def footer(c, d):
    c.saveState(); c.setFont("Arial", 7.5); c.setFillColor(colors.grey)
    c.drawString(12 * mm, 7 * mm, "Repos - SIH 26147 (NTRO) - GitHub landscape, snapshot 26 Sep 2026")
    c.drawRightString(285 * mm, 7 * mm, f"Page {d.page}"); c.restoreState()

doc = SimpleDocTemplate(r"D:\spacetech\repos.pdf", pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm,
                        topMargin=10 * mm, bottomMargin=12 * mm, title="Repos - SIH 26147")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("ok", len(R))
