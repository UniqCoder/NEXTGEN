"""Winning plan v2 for SIH 26147: audit of v1 + competitor evidence -> revised plan.
Run from inside _build/:  python make_plan_v2.py"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY, ACCENT, LIGHT = colors.HexColor("#14213d"), colors.HexColor("#c8553d"), colors.HexColor("#f4f1ea")
TEAL, GREEN, GOLD = colors.HexColor("#2a6f77"), colors.HexColor("#dcefe9"), colors.HexColor("#fbeee9")
GREY = colors.HexColor("#c9c2b2")
body = ParagraphStyle("b", fontName="Arial", fontSize=9.4, leading=13, spaceAfter=4)
small = ParagraphStyle("s", fontName="Arial", fontSize=7.8, leading=10.1)
tiny = ParagraphStyle("t", fontName="Arial", fontSize=7.1, leading=9)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=16, leading=20, textColor=NAVY, spaceBefore=2, spaceAfter=6)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=11.2, leading=14.5, textColor=ACCENT, spaceBefore=6, spaceAfter=3)
title = ParagraphStyle("ti", parent=body, fontName="Arial-Bold", fontSize=30, leading=36, textColor=NAVY)
bullet = ParagraphStyle("bl", parent=body, leftIndent=12, bulletIndent=3, spaceAfter=2)
W = 180 * mm

story = []
def P(t, s=body): story.append(Paragraph(t, s))
def B(items, s=bullet):
    for t in items: story.append(Paragraph(t, s, bulletText="\u2022"))
    story.append(Spacer(1, 3))
def table(rows, widths, head=True, zebra=True, extra=None, style=small):
    data = [[Paragraph(str(c), style) for c in r] for r in rows]
    if head: data[0] = [Paragraph(f'<font color="white"><b>{c}</b></font>', style) for c in rows[0]]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra: st.append(("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, LIGHT]))
    t.setStyle(TableStyle(st + (extra or []))); story.append(t); story.append(Spacer(1, 7))
def callout(text, bg=LIGHT, border=ACCENT):
    t = Table([[Paragraph(text, body)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t); story.append(Spacer(1, 7))

# ======================= COVER =======================
story.append(Spacer(1, 26 * mm))
P('<font color="#c8553d">SIH 2026 &middot; PS 26147 &middot; NTRO &middot; WINNING PLAN v2</font>', ParagraphStyle("k", parent=body, fontSize=12, fontName="Arial-Bold"))
P("Project SANJAYA", title)
P("From a recording nobody understands to a <b>proven</b> transmitter recipe and a <b>deployable receiver</b> - even when the data is short, "
  "noisy, and comes from different sensors.", ParagraphStyle("st", parent=body, fontSize=14, leading=19, textColor=TEAL))
story.append(Spacer(1, 7 * mm))
callout("<b>What v2 is.</b> An audit of <i>winning plan 147.pdf</i> (v1) against what the 43 public competing repositories actually claim "
        "(every README re-checked for each USP), then a rebuilt plan. v1's core idea survives. Four of its eight USPs turned out to be partly "
        "done already by other teams, and v1 did not answer the problem statement's own central complaint: <b>the data is insufficient and comes "
        "from different sensors</b>. v2 is built around that complaint.", bg=colors.white, border=TEAL)
P("<b>Sources used:</b> the PS text (<i>introduction to 147.pdf</i>), the 43-repo landscape (<i>repos.pdf</i> + the README snapshot in "
  "<i>_build/data.json</i>), v1's research list (2025-26 papers), and established theory (named where used). No new paper is cited "
  "that was not already in our list; new ideas are grounded in textbook methods and say so.")
P("<b>Reading guide:</b> Section 3 = the expected solution (100% of the PS). Section 4 = the USPs. <b>Section 5 = the High-Innovation Gap</b> "
  "(the page to show judges). Section 6 = how we beat insufficient data with <b>real</b> recordings, not demos.")
story.append(PageBreak())

# ======================= 0. EXECUTIVE SUMMARY =======================
P("0. Executive summary", h1)
P("Is v1 'goated'? Honest verdict", h2)
table([["", "Verdict"],
       ["Strong and unique (keep)", "<b>Proof-of-Decode</b> (waveform re-synthesis, 0 of 43 do it), <b>blind scrambler recovery</b> (0 of 43), "
        "<b>successive cancellation to reveal hidden signals</b> (0 of 43), the evidence-loop architecture, the demo script."],
       ["Weaker than it looked", "Signal Genome (yoganandasp15 already scores protocol profiles such as POCSAG vs Bell 202 and satellite formats); "
        "CRC discovery (2 repos already sweep CRC libraries); real over-the-air validation (ICHNOVA uses KiwiSDR, IQWAV and Venkata-Manoj use real captures); "
        "'honest confidence' (about 20 of 43 READMEs have UNKNOWN / provenance / abstain states)."],
       ["Missing entirely", "(1) The PS's central complaint - <i>'data is often insufficient'</i> - was answered only with a synthetic bench. "
        "(2) <i>'recorded from different sensors and different locations'</i> - v1 treats every file alone. "
        "(3) <i>'utilised for processing signals in the designated sensors'</i> - v1's output ends at a report. "
        "(4) No plan for how the system improves inside NTRO, where labels are scarce."]],
      [38 * mm, 142 * mm], extra=[("BACKGROUND", (0, 1), (0, 1), GREEN), ("BACKGROUND", (0, 3), (0, 3), GOLD)])
P("What v2 changes", h2)
B(["<b>Reframe:</b> SANJAYA is not a better classifier. It closes NTRO's whole loop: <b>sensor -> recording -> proven recipe -> deployable receiver back to the sensor</b>, "
   "and it tells the collector exactly what extra data would settle any open question.",
   "<b>Eight crown innovations</b> (Section 4A), each aimed at a sentence in the PS, each at 0 of 43 competitors. Five of them are new in v2.",
   "<b>A real-data engine</b> (Section 6): cabled hardware-in-the-loop truth, real public signals labelled by independent open-source decoders "
   "(including a satellite downlink that exercises the <i>entire</i> PS chain), and paired real IQ + audio from the same receiver.",
   "<b>GUI already exists</b> as a working front-end (React + three.js, 5-step flow). The idea-round deck can show a real product, not mock-ups."])
P("The pitch in one breath", h2)
callout("<i>\"Give SANJAYA any .IQ or .wav from any sensor. It recovers the complete transmitter recipe and <b>proves</b> it by rebuilding the "
        "signal and subtracting it until only noise is left. If the capture is too short, it says exactly how much more to record, or pools "
        "evidence from other captures and other sensors. Then it compiles the recipe into a <b>ready-to-run receiver</b> for NTRO's "
        "designated sensors - and every proven decode makes it smarter, on-premises, without a single hand-made label.\"</i>", bg=colors.white, border=ACCENT)
story.append(PageBreak())

# ======================= 1. AUDIT OF v1 USPs =======================
P("1. Audit: v1's eight USPs against the field", h1)
P("Each claim was re-checked against the 43 READMEs (keyword search plus reading the matching sentences). Counts are of repos that "
  "<i>claim</i> the capability; claims were not run.")
table([["v1 USP", "What competitors actually have", "Still unique?", "v2 action"],
       ["1. Proof-of-Decode (waveform re-synthesis)", "Bit-level checks only: CRC / re-encode BER (Gururaghavendra123, Venkata-Manoj, anshumanarchit 'L4 re-encode residual'). Nobody rebuilds and subtracts the waveform.",
        "<b>Yes, 0/43</b>", "Keep as the core; add the Decode Certificate and false-certificate KPI."],
       ["2. Soft joint code + interleaver ID, open-set LDPC", "Soft LLR demod in ~5; hard GF(2) rank in ~6 (ShantanuSomwanshi, NaidhruvK, WaghJagdish, Jagzz-Coder); ICHNOVA dual-code syndrome for conv x block. LDPC: catalogue or 'not identifiable' (RadioFry).",
        "Yes in depth, but judges may not see the difference", "Keep; sell it through <b>low-data performance</b> (Section 4A C2-C3) and the rank-profile visual."],
       ["3. Blind scrambler (LFSR) recovery", "Fixed descramblers only; 'Berlekamp' hits are Reed-Solomon, not scrambler ID.", "<b>Yes, 0/43</b>", "Keep as depth USP."],
       ["4. Signal Genome (named standards)", "yoganandasp15 scores protocol profiles (POCSAG, Bell 202, satellite formats) with AMBIGUOUS states.",
        "Partly taken", "Keep, but differentiate on <b>sample-rate + clock back-solving</b> and feed the Emitter Passport (C6)."],
       ["5. Bit-Lens (fields, CRC, schema)", "CRC library sweeps in 2 (yoganandasp15: 6 profiles; aayushkasurde: 4 algorithms); bit-constancy header finder (ShantanuSomwanshi). No counters, no schema export.",
        "Partly taken", "Upgrade: solve <b>any</b> CRC as GF(2) linear algebra (not a library), counters, length fields, Kaitai export, counter chronology (C6)."],
       ["6. Scene mode + successive cancellation", "CFAR / multi-signal detection in ~6 (WaghJagdish, aayushkasurde, Akshat030307, Devansh-567, ...). Nobody decodes-and-cancels.",
        "SIC: <b>yes</b>", "Keep; SIC is the differentiator."],
       ["7. HF robustness", "Equalisers in several; real HF only in ICHNOVA (time-signal stations, no coding chain).", "Partly taken",
        "Upgrade: real HF <b>with full coding chains</b> (STANAG 4285, HFDL) + fading on real hardware (Section 6)."],
       ["8. Conformal sets, open-set, few-shot", "Honesty / UNKNOWN / provenance labels in ~20; calibrated abstention (anshumanarchit, ECE); open-set wording in RadioFry. No conformal guarantee.",
        "Weak as a headline", "Demote to the trust layer; replace the headline with the <b>Proof-gated Learning Flywheel</b> (C8)."]],
      [33 * mm, 70 * mm, 27 * mm, 50 * mm],
      extra=[("BACKGROUND", (2, i), (2, i), GREEN if i in (1, 3, 6) else GOLD) for i in range(1, 9)])
P("What v1 never answered (the PS's own words)", h2)
table([["PS sentence", "Why it matters", "v1", "v2 answer"],
       ["\"This data is often insufficient for fine grain analysis\"", "Blind code/interleaver ID needs many codewords; short captures break every rank method in the field.", "Synthetic bench only", "C2 Data-Sufficiency Engine, C3 Evidence Stitching, Section 6"],
       ["\"recorded from different sensors and different locations, the parameters may vary\"", "Different Fs, clocks, filters, IQ imbalance: evidence from two sensors cannot simply be added.", "Per-file forensics", "C4 Sensor Twin, C3 cross-sensor pooling"],
       ["\"utilised for processing signals in the designated sensors\"", "The analyst's output is meant to configure operational receivers.", "Report / JSON", "C5 Recipe Compiler (deployable receiver + sub-noise detector)"],
       ["\"spectral relationship from training data containing both .IQ and .wav\"", "Many .wav files are receiver audio, not raw IQ.", "Accept both formats", "C7 WAV-Lifting with real paired IQ/audio"],
       ["\"reduces the accuracy and confidence of interpretation\"", "Confidence must be earned, and must improve with use.", "Conformal sets", "C1 Certificate + C8 Flywheel"]],
      [45 * mm, 55 * mm, 25 * mm, 55 * mm])
story.append(PageBreak())

# ======================= 2. THE FIELD =======================
P("2. What the 43 competitors have - and where they all stop", h1)
table([["Capability", "Repos (of 43)", "Best in field", "Common limitation"],
       ["IQ/WAV loader, PSD, waterfall, constellation", "~40", "sanket (C++ mmap 50 GB), harikesh (60 FPS WebGL)", "Table stakes; no differentiation left."],
       ["ML modulation classifier (RF / CNN / ResNet)", "~22", "RadioFry (RadioML-trained CNN)", "Trained on RadioML synthetic; unproven on real sensors."],
       ["PSK/QAM/FSK demodulation + timing/carrier loops", "~28", "NaidhruvK (lock-check, equaliser)", "AWGN-tuned; fading untested in most."],
       ["Fixed-catalogue FEC (K=7 Viterbi, RS(255,223), CCSDS sync)", "~25", "Gururaghavendra (96-hypothesis search + CRC gate)", "Blind only inside the catalogue; unknown codes fail."],
       ["GF(2) rank interleaver ID (hard bits)", "~6", "ShantanuSomwanshi (exact size, PN seed)", "Needs long captures; no soft info; no joint code ID."],
       ["Honesty states / provenance / abstain", "~20", "karurravishanker (6 provenance labels)", "Labels uncertainty, never reduces it."],
       ["Standard / protocol profiles", "1-2", "yoganandasp15", "No sample-rate or clock back-solving."],
       ["CRC library sweep", "2", "yoganandasp15, aayushkasurde", "Only known CRCs; no counters or field layout."],
       ["Real over-the-air validation", "3", "ICHNOVA (KiwiSDR time stations)", "No real signal with a full PHY + coding chain and independent truth."],
       ["C++ performance core", "3", "arachknight66 (C++20 + pybind11)", "Fast, but decoders configured, not blind."],
       ["Multi-signal detection", "~6", "aayushkasurde (MAD-CFAR channeliser)", "Detects; never cancels to reveal buried signals."]],
      [52 * mm, 20 * mm, 50 * mm, 58 * mm])
P("The ten walls every competitor hits", h2)
table([["#", "Wall", "Evidence"],
       ["1", "<b>One file at a time.</b> No pooling of evidence across captures.", "0 of 43 mention combining captures."],
       ["2", "<b>One sensor at a time.</b> Sensor differences are 'corrected' per file, never learned.", "3 READMEs merely restate the PS sentence."],
       ["3", "<b>No answer to 'is this enough data?'</b>", "0 of 43 estimate data needed; results are just printed."],
       ["4", "<b>Output dies in a report.</b> Nothing a sensor can run.", "0 of 43 generate a receiver; one repo keeps GNU Radio 'experiments'."],
       ["5", "<b>Truth comes from their own generator.</b>", "33 of 43 describe synthetic / generated test data; 3 show a verified real capture."],
       ["6", "<b>Catalogue-bound coding layer.</b>", "LDPC = pick from list or 'not identifiable'."],
       ["7", "<b>Scramblers ignored.</b> Real systems scramble; frames stay invisible.", "0 blind scrambler recovery."],
       ["8", "<b>.wav = stereo IQ or Hilbert of mono.</b> Receiver audio chains (SSB, FM de-emphasis) are not inverted.", "Hilbert-only in ashcodes1511, aayushkasurde."],
       ["9", "<b>Verification at bit level at best.</b>", "CRC / re-encode BER; nobody validates symbol rate, pulse shape and channel at once."],
       ["10", "<b>Static models.</b> Nothing gets better with use inside NTRO.", "Retrain scripts on synthetic data only."]],
      [8 * mm, 92 * mm, 80 * mm])
story.append(PageBreak())

# ======================= 3. EXPECTED SOLUTION =======================
P("3. Pillar A - The expected solution, 100% covered", h1)
callout("<b>PS, expected solution (verbatim):</b> <i>\"The expected system should improve feature visibility of signals with the help of GUI, enable automated "
        "signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall (time-frequency domain), demodulate "
        "signals, carry out de-interleaving and error correction. The output can then be used to carry out correlation of bit stream for identification "
        "of header and payload.\"</i>", bg=colors.white, border=NAVY)
P("Every clause, the module that delivers it, and the acceptance KPI. KPIs are <b>targets we commit to measure</b> on SANJAYA-Bench and the real-data "
  "tiers (Section 6), not results yet.")
table([["PS clause", "SANJAYA delivers", "KPI target"],
       ["GUI, improve feature visibility", "Built front-end (React + three.js, desktop via Tauri): 5-step flow Recording -> Signal -> Decoding -> Header & payload -> Proof; linked 2D waterfall, "
        "persistence PSD, phosphor constellation, eye, FSK view; 3D terrain with labelled axes; plain-language summary per step.", "Any clause reachable in &lt;= 2 clicks; 100 MB file interactive &lt; 2 s."],
       [".IQ or .wav input", "Forensics: WAV header parse (mono real / stereo IQ, 8-32 bit, float), raw IQ dtype + endianness + I/Q-order sniff with confidence, SigMF sidecar, "
        "DC / IQ-imbalance correction, manual override. <b>WAV-Lifting</b> (C7) for receiver-audio files.", "Correct dtype on 100% of bench formats; ambiguity always shown."],
       ["(i) Sampling frequency", "From header or SigMF; else <b>back-solved</b> from a recognised standard's symbol clock or the anti-alias edge; sensor clock ppm reported.", "Fs within 0.1% on standard-anchored files."],
       ["(i) Modulation", "3 experts fused (cumulants and power-law lines; compact IQ network; decode-fit EVM) -> calibrated probabilities + 95% prediction set + open-set 'novel'.", "&gt;= 98% top-1 at SNR &gt;= 10 dB; 95% set coverage."],
       ["(i) FEC", "Blind: conv (rate, K, generators) by soft rank + dual code; RS by GF Fourier spectra; LDPC by catalogue syndrome, then short-code H recovery; concatenation by recursive peeling.", "Conv / RS ID &gt;= 95% at channel BER 1e-2."],
       ["(i) Interleaving", "Block, convolutional, diagonal, pseudo-random: soft rank-profile scan, joint with code ID; PN via standard permutations + seed search.", "Period ID &gt;= 95% at BER 1e-2."],
       ["(ii) Demodulate FSK, QAM, PSK", "RRC matched filter, Oerder-Meyr + Gardner timing, M-th power + Costas / DD-PLL carrier, CMA -> DD-LMS equaliser, FSK filter bank; soft LLR output.", "BER within 0.5 dB of theory (AWGN)."],
       ["(iii) De-interleave: block, conv, diagonal, PN", "All four as invertible operators, parameterised by the identifier; manual override in Expert mode.", "Bit-exact round trip; blind recovery on bench."],
       ["(iv) FEC: short-K conv + Viterbi, RS, concatenated, LDPC", "C++ soft Viterbi (K 3-9, punctured rates); RS Berlekamp-Massey; concatenated chains; LDPC normalised min-sum (catalogue + recovered H).", "Coding gain within 0.5 dB of theory."],
       ["(v) Bit-stream correlation -> header &amp; payload", "Autocorrelation frame length, soft sync discovery, aligned raster, entropy map; fields labelled HEADER / PAYLOAD; CRC solved as GF(2) algebra; counters and length fields.", "Frame + sync found on 100% of framed bench files."],
       ["Spectral features: Fs, constellation, waterfall", "All three on the Signal step by default; 3D terrain optional.", "Visible on first load."],
       ["Automated", "Autopilot: one click from raw file to header / payload; Expert mode overrides any stage.", "Full chain on 1 M samples &lt; 10 s."],
       ["'GNU Radio, python, C++'", "Python orchestration; C++ (pybind11) kernels; GNU Radio used for the <b>Recipe Compiler</b> output and as a cross-check oracle.", "All three used for a real reason."],
       ["Output for designated sensors", "Decode Certificate (PDF/JSON), SigMF annotations, bits, header/payload CSV, <b>compiled receiver</b> (C5).", "Receiver runs live on a second SDR."]],
      [36 * mm, 100 * mm, 44 * mm])
story.append(PageBreak())

# ======================= 4A. CROWN INNOVATIONS =======================
P("4. Pillar B - The USPs", h1)
P("Two tiers. <b>4A Crown innovations</b> are what we pitch: each removes a limitation named in the PS, and none is claimed by any of the 43 "
  "competitors. <b>4B Depth USPs</b> make the coding layer the strongest in the field. Every card lists the limitation, the method, the evidence "
  "that it is new, the build cost, and the demo moment.")
P("4A. Crown innovations", h2)

crown = [
("C1 · Proof-of-Decode and the Decode Certificate",
 "\"This limitation reduces the accuracy and confidence of interpretation.\"",
 "After decoding, SANJAYA re-encodes the recovered bits through the discovered chain (code -> interleaver -> scrambler -> mapper -> pulse shape), applies the "
 "estimated channel (gain, CFO, phase, timing, equaliser taps) and <b>subtracts the rebuilt waveform from the recording</b>. It reports explained energy, "
 "residual-to-noise ratio and a whiteness test (Ljung-Box, kurtosis). White residual at the noise floor = the whole recipe is proven. Output: a signed "
 "certificate with file hash, every parameter, its evidence and its confidence set.",
 "0 of 43. The best competitors verify at bit level (CRC, re-encode BER), which cannot validate symbol rate, pulse shape and channel together and cannot catch "
 "'plausible but wrong' decodes.",
 "Analysis-by-synthesis and successive interference cancellation (receiver theory); Ljung and Box (1978) whiteness test.",
 "Medium. Reuses our own modulator. 1 person, ~1.5 weeks.",
 "Press Prove: the signal ridge sinks into the noise in the 3D waterfall; histogram becomes one bell curve; certificate prints. Wrong hypothesis: a red band of unexplained energy stays.",
 "False-certificate rate = 0 on the full bench."),
("C2 · Data-Sufficiency Engine: 'how much more data do we need?'",
 "\"This data is often insufficient for fine grain analysis for parameter extraction.\"",
 "Every parameter is a posterior over hypotheses, updated as evidence arrives (Bayesian model evidence; the re-synthesis in C1 gives an exact likelihood). "
 "A sequential test stops as soon as one hypothesis is decisive. When it is not, SANJAYA computes <b>how much more signal would settle it</b> - e.g. "
 "<i>\"interleaver period 48 vs 96 unresolved: need about 14 more codewords, about 2.3 s at this SNR\"</i> - and turns that into a "
 "<b>collection tasking note</b> for the sensor: frequency, bandwidth, minimum sample rate and duration to record.",
 "0 of 43 estimate the data a decision needs. Every competitor prints a result or an UNKNOWN label; none tells the collector what would remove the UNKNOWN.",
 "Wald's sequential probability ratio test (1945); Bayesian model comparison; Cramér-Rao bounds for estimator variance; data needs of rank-based code ID (subspace-coding, arXiv 2601.15903).",
 "Medium. Mostly bookkeeping over quantities we already compute. 1 person, ~1 week, after C1.",
 "Load a 0.4 s capture: the meter shows 'Interleaver: 2 hypotheses, need +2.3 s'. The tasking note prints.",
 "Predicted vs actual data needed within 30% on the bench."),
("C3 · Evidence Stitching across captures and sensors",
 "\"The data point are recorded from different sensors and different locations.\"",
 "A code's parity checks are the same in every capture. So once captures are normalised (C4) and aligned by sync or frame phase, SANJAYA "
 "<b>stacks codewords from many short captures, from different sensors, into one evidence matrix</b>; likelihoods for modulation, baud and "
 "recipe multiply across captures. Three 0.4 s bursts from two sensors can identify what no single burst can. Captures are associated to "
 "one emitter by recipe consistency and the Emitter Passport (C6).",
 "0 of 43 combine captures. The field is single-file by construction.",
 "Invariance of a linear code's dual space; Bayesian evidence accumulation; the same C2 machinery.",
 "Medium-high. Needs C2 + C4. 1-2 people, ~1.5 weeks.",
 "Drop a second capture from 'Sensor B' onto the first: the rank-profile dip sharpens and the UNKNOWN flips to a proven period.",
 "Identification success vs capture length: stitched curve reaches 95% with less than half the single-file data."),
("C4 · Sensor Twin: passive calibration from signals of opportunity",
 "\"The parameters may vary\" (different sensors, locations, recording settings).",
 "Every sensor hears signals whose true parameters are known: recognised standards with exact symbol clocks, steady carriers, empty bands. From ordinary "
 "recordings SANJAYA learns each sensor's <b>clock error (ppm), anti-alias response, noise-floor shape, IQ imbalance, DC, ADC depth and phase noise</b> - "
 "with no lab time. That twin (a) normalises its recordings so evidence can be stitched (C3), (b) separates <i>transmitter</i> clock error from "
 "<i>sensor</i> clock error when two sensors hear one emitter, (c) flags faulty metadata (\"header says 48 kHz, filter edge says 44.1 kHz\"), and "
 "(d) generates training data <b>through that sensor's measured front end</b>, closing the synthetic-to-real gap.",
 "0 of 43. Competitors correct DC and IQ imbalance per file; none build a persistent per-sensor model or use it to make training data.",
 "Calibration from signals of opportunity (standard in navigation and radio astronomy); domain-matched synthesis; DenoMAE (arXiv 2501.11538) as an optional denoising front end.",
 "Medium. Estimators already exist in the pipeline; the twin is persistence plus a generator hook. 1 person, ~1 week.",
 "Two sensors, one emitter: 'Sensor A +12 ppm, Sensor B -31 ppm, transmitter +4.2 ppm'. Header-lie alert on a mislabelled WAV.",
 "Sensor ppm within 1 ppm of a GPS-disciplined reference."),
("C5 · Recipe Compiler: from one recording to a deployable receiver",
 "\"The resultant data is then utilised for processing signals in the designated sensors.\"",
 "The proven recipe is compiled into <b>(a) a GNU Radio flowgraph</b> (tuner offset, RRC, symbol sync, Costas, demapper, descrambler, de-interleaver, "
 "FEC decoder, deframer, CRC check, sink) that runs live on an SDR, <b>(b) a sensor-agnostic recipe file</b> (SigMF-style JSON) for NTRO's own receivers, "
 "and <b>(c) a recipe-matched detector</b> that correlates against the known sync and frame structure to find the same emitter far below the noise floor, "
 "where a spectrum view shows nothing.",
 "0 of 43. Their output ends in a report or JSON. The PS says the output configures sensors; we hand the sensor a working receiver.",
 "GNU Radio gr-digital / gr-fec blocks; SigMF; matched-filter detection gain from known structure (textbook detection theory).",
 "Medium. Template generation over blocks that already exist, plus our de-interleaver as a custom block. 1 person, ~1.5 weeks.",
 "Click 'Compile receiver': a flowgraph opens and a <b>second SDR starts decoding the live stream</b> in front of the judges.",
 "Compiled receiver decodes 100% of frames that SANJAYA proved offline."),
("C6 · Emitter Passport and Counter Chronology",
 "Implicit: NTRO needs to know <i>who</i> transmits and <i>how often</i>, not only <i>what</i>.",
 "Each proven emitter gets a passport: the protocol recipe (modulation, baud, code, interleaver, scrambler seed, sync word, frame layout) plus physical traits "
 "(transmitter clock ppm after sensor correction, IQ image, phase noise, power-ramp transient). Captures from any sensor are matched to known passports. "
 "<b>Counter Chronology:</b> Bit-Lens finds frame counters; two captures with counters c1 and c2 prove the emitter sent (c2 - c1) frames in between - "
 "its activity while nobody was recording - and identical counters at two sensors mark the same instant.",
 "0 of 43 do protocol-level identity; 'fingerprints' in 3 repos are feature-vector similarity of one capture. Nobody reads counters.",
 "Specific-emitter identification from carrier offset and IQ traits (established literature); GF(2) field analysis (Bit-Lens).",
 "Medium. Mostly assembling outputs of C4 and Bit-Lens. 1 person, ~1 week.",
 "Capture from yesterday and today: 'Same emitter (passport match 0.97); sent 18 432 frames in between; duty cycle 71%.'",
 "Passport re-identification &gt;= 95% on bench emitters across sensors."),
("C7 · WAV-Lifting: inverting the receiver's audio chain",
 "\"The data saved as .IQ and .wav have different parameters ... The spectral relationship from training data containing both .IQ and .wav formats can be utilised.\"",
 "Many .wav recordings are the <b>audio output of a receiver</b> (SSB upper/lower sideband, FM with de-emphasis, AGC, 300-2700 Hz passband), not raw IQ. "
 "SANJAYA estimates the receiver chain that produced the file and inverts it to recover complex baseband, keeping sideband and inversion as hypotheses. "
 "It learns that 'spectral relationship' from <b>real paired data</b>: the same KiwiSDR signal recorded simultaneously on two channels, one in IQ mode and one in audio mode (Section 6).",
 "0 of 43. Competitors treat stereo WAV as IQ and apply a Hilbert transform to mono WAV; nobody models or inverts the receiver.",
 "SSB / FM receiver models; paired-domain learning; the PS's own hint about IQ + WAV training data.",
 "Medium. 1 person, ~1 week (chain estimator); data collection in parallel.",
 "Same STANAG 4285 transmission as USB audio .wav and as IQ: both give the same proven recipe.",
 "Recipe agreement IQ vs lifted-WAV &gt;= 95% on paired real recordings."),
("C8 · Proof-gated Learning Flywheel (on-premises)",
 "Implicit: NTRO has large unlabelled archives, few labels, and data that cannot leave the building.",
 "Every PASS certificate (C1) is a <b>machine-verified label</b>: the IQ segment plus its proven recipe. SANJAYA stores it locally and periodically "
 "fine-tunes its small models (modulation expert, detector, open-set prototypes), recalibrates the conformal sets, and grows the passport library. "
 "Because labels are admitted only after waveform proof, label noise stays near zero, which is what makes self-training safe. Nothing leaves the machine.",
 "0 of 43. Competitors ship models trained once on synthetic data, with retrain scripts on synthetic data.",
 "Wireless foundation models and few-shot adaptation from v1's list (IQFM 2506.06718, EMind 2508.18785, Radio-FM 2608.05793, RFPrompt 2605.03279); split conformal recalibration.",
 "Low-medium (orchestration + a small fine-tune job). 1 person, ~1 week.",
 "After 20 proven files the 'novel' chirp class and two new passports appear without anyone labelling anything.",
 "Accuracy on a held-out real set rises with each flywheel round; label error &lt; 0.5%."),
]
for name, lim, what, why, basis, effort, demo, kpi in crown:
    rows = [[Paragraph(f'<font color="white"><b>{name}</b></font>', small), ""],
            [Paragraph("<b>PS limitation</b>", small), Paragraph(f"<i>{lim}</i>", small)],
            [Paragraph("<b>What it does</b>", small), Paragraph(what, small)],
            [Paragraph("<b>Why it is new</b>", small), Paragraph(why, small)],
            [Paragraph("<b>Built on</b>", small), Paragraph(basis, small)],
            [Paragraph("<b>Effort</b>", small), Paragraph(effort, small)],
            [Paragraph("<b>Demo moment</b>", small), Paragraph(f"<i>{demo}</i>", small)],
            [Paragraph("<b>KPI</b>", small), Paragraph(kpi, small)]]
    t = Table(rows, colWidths=[27 * mm, 153 * mm])
    t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                           ("GRID", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 1), (0, -1), LIGHT), ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#eef2f7")),
                           ("BACKGROUND", (1, 6), (1, 6), GOLD)]))
    story.append(KeepTogether([t, Spacer(1, 6)]))

P("4B. Depth USPs (the strongest coding layer in the field)", h2)
table([["USP", "What", "Field status (of 43)"],
       ["D1 Soft joint coding-layer engine", "Interleaver + code identified jointly from soft LLRs; rank-profile plot; recursive peeling of concatenated codes; open-set LDPC for short codes (n &lt;= 1024). "
        "Works with fewer codewords than hard rank methods and pools across captures (C3).", "Hard rank ~6; soft joint 0; open-set LDPC 0"],
       ["D2 Blind scrambler recovery", "Additive and self-synchronising LFSRs by Berlekamp-Massey on idle runs + Walsh-Hadamard search; standard library (CCSDS, PRBS-15, 802.11, V.35).", "0 (fixed descramblers only)"],
       ["D3 Bit-Lens with CRC solving", "Aligned raster, entropy map, counters, length fields; <b>any</b> CRC polynomial solved as GF(2) linear algebra; Kaitai / Wireshark-style schema export.", "Library CRC sweep in 2; solving 0; counters 0"],
       ["D4 Scene + successive cancellation", "OS-CFAR scene; proven emitters subtracted; weaker emitters revealed and decoded.", "Detection ~6; cancellation 0"],
       ["D5 Signal Genome + back-solving", "~30 named standards; true sample rate and sensor ppm back-solved from a matched standard.", "Profiles in 1; back-solving 0"],
       ["D6 HF-grade robustness", "Watterson channel (ITU-R F.1487 profiles) in software <b>and on real hardware</b> (Section 6); fractionally-spaced equaliser.", "Equaliser several; real HF with coding chain 0"],
       ["D7 Trust layer", "Calibrated probabilities, 95% conformal sets, open-set 'novel', few-shot teach from ~5 examples.", "Honesty labels ~20; conformal 0"]],
      [40 * mm, 100 * mm, 40 * mm])
P("Deliberately not doing", h2)
B(["<b>LLM chatbot / copilot</b> (3 of the 43 have one): a liability for an air-gapped intelligence user; our explanations come from evidence.",
   "<b>Cloud, login, databases</b>: irrelevant offline; costs weeks.",
   "<b>Black-box-only deep learning</b>: DL is one of three experts and is gated by proof."])
story.append(PageBreak())

# ======================= 5. HIGH-INNOVATION GAP =======================
P("5. The High-Innovation Gap - where SANJAYA wins", h1)
P("The chart shows how crowded each capability is across the 43 competitors. Everything on the left is what thousands of teams will also "
  "build, with or without AI help. Everything at the bottom is ours alone.")

bars = [("Loader + PSD + waterfall + constellation", 40), ("PSK/QAM/FSK demodulation", 28), ("Fixed-catalogue Viterbi + RS", 25),
        ("ML modulation classifier", 22), ("Honesty / UNKNOWN / provenance labels", 20), ("GF(2) rank interleaver ID (hard)", 6), ("Multi-signal detection", 6),
        ("Real over-the-air capture", 3), ("CRC library sweep", 2), ("Standard / protocol profiles", 1)]
ours = ["C1 Proof-of-Decode", "C2 Data-Sufficiency Engine", "C3 Evidence Stitching", "C4 Sensor Twin", "C5 Recipe Compiler",
        "C6 Emitter Passport + Chronology", "C7 WAV-Lifting", "C8 Proof-gated Flywheel", "D2 Blind scrambler ID", "D4 Successive cancellation"]
rowh, top = 4.3 * mm, 6 * mm
dh = top + (len(bars) + len(ours) + 2) * rowh + 8 * mm
d = Drawing(W, dh)
x0, bw = 70 * mm, 100 * mm
y = dh - top
d.add(String(0, y + 2, "Crowded: many of 43 competitors claim it", fontName="Arial-Bold", fontSize=8, fillColor=NAVY))
y -= rowh
for name, n in bars:
    d.add(String(x0 - 3, y + 1.2, name, fontName="Arial", fontSize=7.2, fillColor=colors.HexColor("#333333"), textAnchor="end"))
    d.add(Rect(x0, y, bw * n / 43, rowh - 1.4, fillColor=colors.HexColor("#b9b2a3"), strokeColor=None))
    d.add(String(x0 + bw * n / 43 + 2, y + 1.2, f"{n}/43", fontName="Arial", fontSize=7, fillColor=colors.HexColor("#555555")))
    y -= rowh
y -= rowh * 0.4
d.add(Line(0, y + rowh * 0.7, W, y + rowh * 0.7, strokeColor=ACCENT, strokeWidth=0.8, strokeDashArray=[3, 2]))
d.add(String(0, y - 1, "Empty: 0 of 43 - SANJAYA only", fontName="Arial-Bold", fontSize=8, fillColor=ACCENT))
y -= rowh
for name in ours:
    d.add(String(x0 - 3, y + 1.2, name, fontName="Arial-Bold", fontSize=7.2, fillColor=TEAL, textAnchor="end"))
    d.add(Rect(x0, y, 1.2, rowh - 1.4, fillColor=ACCENT, strokeColor=None))
    d.add(String(x0 + 4, y + 1.2, "0/43", fontName="Arial-Bold", fontSize=7, fillColor=ACCENT))
    y -= rowh
d.add(Line(x0, 3 * mm, x0 + bw, 3 * mm, strokeColor=GREY))
for k in (0, 10, 20, 30, 40):
    d.add(String(x0 + bw * k / 43, 0, str(k), fontName="Arial", fontSize=6.5, fillColor=colors.grey, textAnchor="middle"))
story.append(d)
story.append(Spacer(1, 4))

table([["Innovation", "NTRO limitation removed", "Why teams (even AI-assisted) will not reach it", "Value to NTRO"],
       ["C1 Proof-of-Decode", "Low confidence in manual / heuristic answers", "Needs a full standards-accurate modulator and channel model wired back into the analyser. AI tools suggest 'add a confidence score'.", "An answer can be trusted and audited without ground truth."],
       ["C2 Data-Sufficiency", "Insufficient data", "Requires treating every stage as a likelihood, which catalogue pipelines are not built for.", "Collection tasking: record the right thing once."],
       ["C3 Evidence Stitching", "Insufficient data; many sensors", "Invisible from the single-file framing every repo uses; needs code-space invariance insight.", "Short intercepts from many sensors become decisive."],
       ["C4 Sensor Twin", "Parameters vary by sensor", "Needs a persistent model per sensor plus signals-of-opportunity reasoning.", "Fleet-wide calibration and cleaner training data with no lab time."],
       ["C5 Recipe Compiler", "Output must drive designated sensors", "Comes from reading the PS's workflow, not its task list; needs GNU Radio and a proven recipe.", "Hours of manual receiver setup become one click."],
       ["C6 Passport + Chronology", "Who and how often, not only what", "Needs counters (Bit-Lens) + sensor-corrected clock traits (C4) together.", "Emitter re-identification and activity estimates between intercepts."],
       ["C7 WAV-Lifting", "IQ and WAV differ", "Needs receiver modelling and real paired data (KiwiSDR IQ + audio).", "Legacy audio archives become analysable."],
       ["C8 Flywheel", "Few labels; data cannot leave", "Only safe because C1 makes labels trustworthy.", "Gets better every week, fully on-premises."]],
      [30 * mm, 38 * mm, 64 * mm, 48 * mm])
callout("<b>Why this gap is durable.</b> Each crown innovation depends on another one: Flywheel needs Proof; Stitching needs the Sensor Twin and the "
        "Data-Sufficiency maths; the Passport needs Bit-Lens counters and the Twin's clock separation; the Recipe Compiler needs a proven recipe. "
        "A team cannot copy one feature from our deck in 36 hours - the value is in the connected system.", bg=colors.white, border=TEAL)
story.append(PageBreak())

# ======================= 6. REAL DATA ENGINE =======================
P("6. Beating 'insufficient data' - real recordings, not demos", h1)
P("Two fronts. <b>Inside the algorithm</b>, SANJAYA needs less data (soft decisions, joint identification, sequential stopping) and can pool data "
  "(Stitching, Sensor Twin). <b>Outside</b>, we build a real-data engine in which every recording has independent truth. Four tiers, each "
  "more real than the one before:")

d = Drawing(W, 52 * mm)
tiers = [("Tier 1 - SANJAYA-Gen", "Synthetic, exact truth, every PS combination; generated through measured Sensor Twins (C4)."),
         ("Tier 2 - Cabled hardware-in-the-loop", "Our waveforms through a real SDR transmitter, coax and attenuators into real receivers: real DAC/ADC, clocks, IQ imbalance; exact truth."),
         ("Tier 3 - Real public signals + independent decoders", "Over-the-air HF/VHF/UHF signals; truth from established open-source decoders that are not ours."),
         ("Tier 4 - NTRO archives, on-premises", "After selection: the Proof-gated Flywheel (C8) labels real NTRO data with no data leaving the site.")]
for i, (a, b) in enumerate(tiers):
    yy = 2 * mm + i * 12.5 * mm
    xx = i * 8 * mm
    d.add(Rect(xx, yy, W - 12 * mm - xx, 10.5 * mm, fillColor=[LIGHT, GREEN, colors.HexColor("#d6e6ea"), GOLD][i], strokeColor=TEAL, strokeWidth=0.6))
    d.add(String(xx + 3 * mm, yy + 6.3 * mm, a, fontName="Arial-Bold", fontSize=8, fillColor=NAVY))
    d.add(String(xx + 3 * mm, yy + 2.2 * mm, b, fontName="Arial", fontSize=6.6, fillColor=colors.HexColor("#333333")))
d.add(Line(W - 4 * mm, 4 * mm, W - 4 * mm, 44 * mm, strokeColor=ACCENT, strokeWidth=1.2))
d.add(Polygon([W - 4 * mm, 49 * mm, W - 6.5 * mm, 44 * mm, W - 1.5 * mm, 44 * mm], fillColor=ACCENT, strokeColor=None))
d.add(String(W - 4 * mm, 0.5 * mm, "more real", fontName="Arial", fontSize=6.5, fillColor=ACCENT, textAnchor="middle"))
story.append(d)
story.append(Spacer(1, 4))

P("Tier 3 - real signals that exercise the actual PS chain", h2)
P("Chosen because each carries the layers the PS asks for, and because an independent open-source decoder gives truth we did not create. "
  "Only public, unencrypted broadcasts; SANJAYA analyses <b>structure</b>, never displays private content.")
table([["Signal (band)", "PS layers it exercises", "Independent truth", "How we receive it"],
       ["<b>Meteor-M LRPT weather satellite</b> (VHF, 137 MHz band)", "QPSK; K=7 r=1/2 convolutional + Viterbi; RS(255,223) with interleaving (concatenated); CCSDS randomiser (scrambler); CADU frames with sync word - <b>the entire PS chain in one real signal</b>",
        "SatDump decodes frames and images", "RTL-SDR + home-made V-dipole during passes over India"],
       ["<b>STANAG 4285</b> naval HF broadcasts (HF)", "8PSK 2400 Bd; convolutional code; <b>convolutional interleaver</b>; scrambling sequence; HF fading", "Standard specification; frame structure checks",
        "Public KiwiSDR receivers (IQ mode)"],
       ["<b>HFDL</b> aircraft data link (HF)", "PSK 1800 Bd; convolutional code; interleaving; frames with CRC", "dumphfdl decoder", "KiwiSDR"],
       ["<b>Amateur satellites with AO-40-style FEC</b> (UHF, 435-438 MHz)", "BPSK; concatenated RS + convolutional; block interleaver; scrambler; frames", "gr-satellites decoders", "RTL-SDR + small Yagi or V-dipole"],
       ["<b>NAVTEX / SITOR-B</b> (MF, 518 kHz)", "2-FSK 100 Bd; time-diversity FEC; framing", "multimon-ng / fldigi", "KiwiSDR"],
       ["<b>AIS</b> ship tracking (VHF, 162 MHz)", "GMSK 9600 bps; HDLC framing; bit stuffing; CRC-16", "AIS-catcher / rtl-ais", "RTL-SDR at a coastal or port location"],
       ["<b>RTTY weather / amateur</b> (HF)", "2-FSK, various shifts and rates", "fldigi", "KiwiSDR"]],
      [40 * mm, 67 * mm, 33 * mm, 40 * mm])
P("Tier 2 - cabled hardware-in-the-loop rig (real hardware, exact truth)", h2)
table([["Item", "Purpose", "Approx. cost"],
       ["ADALM-Pluto SDR (TX + RX)", "Transmits SANJAYA-Gen waveforms: any modulation, code, interleaver, scrambler, frame. HF fading applied digitally before TX.", "Rs 20-28k"],
       ["2 x RTL-SDR Blog V4", "Two <b>different</b> receivers = two 'sensors' with different clocks and filters (tests C3, C4).", "Rs 8-10k"],
       ["SMA attenuators (20 + 30 dB), splitter, coax", "Conducted path only - nothing is radiated; the splitter feeds both receivers at once.", "Rs 3-5k"],
       ["V-dipole (137 MHz), small UHF antenna", "Tier 3 satellite reception.", "Rs 1-2k"]],
      [45 * mm, 105 * mm, 30 * mm])
P("<i>Costs are approximate street prices. Transmission is cabled into attenuators only (no antenna). Confirm lab rules with the mentor or institute.</i>", tiny)
P("Paired IQ + WAV (for C7)", h2)
P("A KiwiSDR serves several receiver channels at once, so the same frequency can be recorded in <b>IQ mode on one channel and USB/LSB audio mode on another, simultaneously</b>. That gives real paired data - the "
  "exact 'training data containing both .IQ and .wav' the PS describes - for learning and validating the receiver-chain inversion.")
P("What we will publish in the pitch", h2)
table([["Metric", "Tier", "Why judges care"],
       ["Recipe recovery rate by tier (synthetic / HIL / real)", "1-3", "Shows the synthetic-to-real gap honestly - and how small we make it."],
       ["Identification success vs capture length, single vs stitched", "1-2", "Direct evidence that insufficient data is beaten."],
       ["False-certificate rate", "1-3", "Target 0: an answer marked proven is right."],
       ["Recipe agreement: SANJAYA vs independent decoders", "3", "Truth we did not create."],
       ["Sensor ppm vs GPS-disciplined reference", "2", "Sensor Twin is measurable, not a claim."]],
      [72 * mm, 18 * mm, 90 * mm])
story.append(PageBreak())

# ======================= 7. SYSTEM =======================
P("7. System and closed loop", h1)
d = Drawing(W, 60 * mm)
def box(text, x, y, w, dark=False):
    d.add(Rect(x * mm, y * mm, w * mm, 12 * mm, rx=3, ry=3, fillColor=NAVY if dark else colors.white, strokeColor=TEAL))
    d.add(String((x + w / 2) * mm, (y + 4.6) * mm, text, fontName="Arial-Bold", fontSize=7, fillColor=colors.white if dark else NAVY, textAnchor="middle"))
def arrow(x1, y1, x2, y2):
    import math
    d.add(Line(x1 * mm, y1 * mm, x2 * mm, y2 * mm, strokeColor=ACCENT, strokeWidth=1.1))
    a = math.atan2(y2 - y1, x2 - x1); L = 2.4
    d.add(Polygon([x2 * mm, y2 * mm, (x2 - L * math.cos(a - 0.45)) * mm, (y2 - L * math.sin(a - 0.45)) * mm,
                   (x2 - L * math.cos(a + 0.45)) * mm, (y2 - L * math.sin(a + 0.45)) * mm], fillColor=ACCENT, strokeColor=None))
box("Sensors A, B, ...", 0, 44, 36); box("Recordings (.IQ / .wav)", 46, 44, 40); box("SANJAYA engine", 96, 44, 36, dark=True); box("Proven recipe + certificate", 142, 44, 38)
box("Collection tasking note", 0, 6, 40); box("Designated sensors: live receiver", 62, 6, 52); box("Recipe Compiler", 142, 6, 38)
arrow(36, 50, 46, 50); arrow(86, 50, 96, 50); arrow(132, 50, 142, 50)
arrow(161, 44, 161, 18); arrow(142, 12, 114, 12)
arrow(104, 44, 30, 18); arrow(14, 18, 14, 44)
for k, ln in enumerate(["Inside the engine: Proof (C1),", "Stitching (C3), Sensor Twin (C4),", "Passport (C6), Flywheel (C8)"]):
    d.add(String(112 * mm, (38 - 4.2 * k) * mm, ln, fontName="Arial-Italic", fontSize=7, fillColor=TEAL))
d.add(String(64 * mm, 26 * mm, "C2: what to record next", fontName="Arial-Italic", fontSize=6.8, fillColor=ACCENT))
d.add(String(W / 2, 0.5 * mm, "C5 turns the proven answer into something a sensor can run; C2 closes the loop back to collection.",
             fontName="Arial-Italic", fontSize=7, fillColor=ACCENT, textAnchor="middle"))
story.append(d)
table([["Layer", "Technology", "Why"],
       ["Engine", "Python 3.11 + NumPy/SciPy; C++17 (pybind11) for Viterbi, LDPC min-sum, bit-packed GF(2) elimination, stitched rank; <i>galois</i> for GF(2^m)", "Speed where it matters"],
       ["Verification", "AFF3CT, liquid-dsp, GNU Radio blocks as cross-check oracles; SatDump, gr-satellites, dumphfdl, AIS-catcher, fldigi as Tier-3 truth", "Our numbers are checked by tools we did not write"],
       ["ML", "PyTorch small encoders (&lt; 5 M parameters, CPU); split conformal; on-prem fine-tune job for C8", "Laptop-class, offline"],
       ["GUI", "React + three.js front-end (built), shipped as a Tauri desktop app; engine on localhost", "Air-gapped desktop, no cloud"],
       ["Outputs", "Certificate PDF/JSON, SigMF, bits, CSV, Kaitai schema, <b>GNU Radio flowgraph</b>, recipe file, tasking note", "Directly usable by analysts and sensors"],
       ["Packaging", "Single offline installer; no network at runtime", "Deployable inside NTRO"]],
      [24 * mm, 110 * mm, 46 * mm])
story.append(PageBreak())

# ======================= 8. BUILD PLAN =======================
P("8. Build plan", h1)
P("Ten weeks after the idea round; the main branch is demo-able at the end of every phase. The front-end already exists, which buys roughly one week.")
table([["Phase", "Build", "Exit criterion"],
       ["P0 Idea round (days 1-4)", "Deck from this plan; <b>screenshots and a clip of the working UI</b>; a clip of Proof-of-Decode on a synthetic file; HIL rig ordered; first Meteor and KiwiSDR recordings.",
        "Deck shows a real product and a real satellite recording."],
       ["P1 Spine (W1-2)", "Forensics; SANJAYA-Gen v1; measurements; BPSK/QPSK/FSK receiver; engine wired to the UI; bench + CI; HIL rig working.", "Synthetic and cabled files decode end to end in the UI."],
       ["P2 Coding core + Proof (W3-4)", "C++ Viterbi; RS; block/conv interleavers with rank ID; scrambler recovery; Bit-Lens v1; <b>C1 Proof-of-Decode</b>; OS-CFAR scene.", "Blind QPSK + scrambler + interleaver + K=7 proven by residual."],
       ["P3 Full PS coverage (W5-6)", "8PSK, 16/64QAM, GMSK, 4/8-FSK; equaliser; diagonal + PN; concatenated; LDPC; 3-expert AMC + conformal; Watterson on HIL; <b>Meteor LRPT full chain</b>.", "Compliance matrix 100% green; Meteor recipe matches SatDump."],
       ["P4 Crown innovations (W7-8)", "<b>C2</b> sufficiency + tasking; <b>C4</b> Sensor Twin; <b>C3</b> Stitching; <b>C5</b> Recipe Compiler; <b>C6</b> Passport + chronology; <b>C7</b> WAV-Lifting; <b>C8</b> flywheel; D4 SIC.",
        "Each crown innovation has a 30-second demo that works 10/10 times."],
       ["P5 Hardening (W9)", "10k synthetic + 500 HIL + &gt;= 50 real files; per-tier KPIs; performance; cut anything under 90% reliability.", "KPI table filled with measured numbers."],
       ["P6 Showtime (W10)", "Mystery-signal challenge; live Recipe Compiler on a second SDR; deck with real curves; Q&amp;A drills; 2 laptops + USB backup.", "Full demo rehearsed 5x under 7 minutes."]],
      [34 * mm, 100 * mm, 46 * mm])
P("Team of six", h2)
table([["Role", "Owns"],
       ["1. DSP and receiver lead", "Forensics, measurements, demodulators, equaliser, HF, C7 WAV-Lifting"],
       ["2. Coding-theory lead", "D1 joint soft engine, Viterbi/RS/LDPC, stitched rank maths (C3)"],
       ["3. Protocol and intelligence lead", "D2 scramblers, D3 Bit-Lens + CRC solving, C6 Passport + chronology"],
       ["4. ML and data-efficiency lead", "AMC experts, D7 trust layer, C2 sufficiency + tasking, C8 flywheel"],
       ["5. Product and integration lead", "UI wiring (Tauri), C5 Recipe Compiler (GNU Radio), installer"],
       ["6. Data engine and pitch lead (team lead)", "SANJAYA-Gen, HIL rig, Tier-3 recordings + truth, C4 Sensor Twin, bench, deck"]],
      [60 * mm, 120 * mm])
P("Cut-lines (drop in this order if late)", h2)
B(["C8 flywheel shown on bench only -> C7 limited to USB/LSB -> C6 chronology without physical traits -> open-set LDPC as 'research mode'.",
   "<b>Never cut:</b> 100% PS coverage, C1 Proof, C2 + C3 (our answer to insufficient data), C5 Recipe Compiler, Meteor full-chain real result."])
story.append(PageBreak())

# ======================= 9. DEMO + Q&A =======================
P("9. How we win the room", h1)
P("Seven-minute demo", h2)
table([["Time", "Beat", "What judges see"],
       ["0:00", "The problem", "A real satellite recording: a noisy waterfall. 'An analyst spends hours here.'"],
       ["0:30", "Autopilot on real data", "Meteor LRPT: QPSK, K=7, RS, interleaving, randomiser - every layer recovered; matches SatDump."],
       ["1:40", "Proof", "Press Prove: the ridge sinks into the noise in 3D; certificate prints."],
       ["2:30", "Insufficient data", "A 0.4 s capture: 'need +2.3 s'. Drop a capture from a second receiver: stitched, proven."],
       ["3:30", "Mystery-signal challenge", "A judge sets modulation, interleaver, code, scrambler on our HIL transmitter; SANJAYA recovers all of them."],
       ["4:40", "Recipe Compiler", "One click: a GNU Radio receiver is generated and <b>decodes the live stream on a second SDR</b>."],
       ["5:40", "Passport + hidden signal", "Same emitter re-identified across sensors with frames counted in between; a weak signal revealed by cancellation."],
       ["6:30", "Numbers", "Per-tier recovery, stitched vs single curve, false-certificate rate 0. Close on the pitch sentence."]],
      [12 * mm, 38 * mm, 130 * mm])
P("Questions we must answer cold", h2)
table([["Question", "Answer"],
       ["How do you know it is right on real data?", "Waveform proof (C1), CRC and syndromes, and agreement with independent decoders on real signals (Tier 3)."],
       ["What if our captures are short?", "C2 tells you exactly how much more to record; C3 pools the captures you already have, across sensors."],
       ["Our sensors differ.", "C4 learns each sensor from signals it already hears; no lab time."],
       ["How does this reach our operational systems?", "C5 compiles a receiver and a recipe file; SigMF out; offline installer."],
       ["Blind LDPC is impossible.", "For long codes, in general, yes: we match catalogue codes by syndrome and recover short codes (n &lt;= 1024), and we state the limit."],
       ["Encrypted payloads?", "We recover the full transmission recipe and frame structure and flag high-entropy payloads. Decryption is out of scope by design."],
       ["Will it improve after deployment?", "Yes - C8 learns from every proven decode, on-premises, without manual labels."]],
      [52 * mm, 128 * mm])

# ======================= 10. RISKS =======================
P("10. Risks and honest limits", h1)
table([["Risk", "Mitigation", "Fallback"],
       ["Meteor passes / reception weak", "Record in week 1; several passes per day; RTL-SDR V4 + V-dipole is a known-good setup", "Use best recording; STANAG / HFDL via KiwiSDR"],
       ["Stitching alignment across sensors", "Align on sync words first; Sensor Twin removes Fs and ppm differences", "Stitch captures from the same sensor only"],
       ["Recipe Compiler coverage", "Start with PSK + conv + RS + block interleaver (Meteor-class)", "Export recipe file only for exotic chains"],
       ["HIL legality / lab rules", "Cabled into attenuators, no antenna", "Tier 1 + Tier 3 only"],
       ["Open-set LDPC unstable", "Short codes only; catalogue path always available", "'Research mode' label"],
       ["Scope", "Crown list is final after W6", "Cut-lines in Section 8"]],
      [45 * mm, 85 * mm, 50 * mm])
P("<i>KPIs in this document are targets to be measured, not results. SIH 2026 dates and PS details should be confirmed on the official portal.</i>", tiny)
story.append(PageBreak())

# ======================= 11. REFERENCES =======================
P("11. References", h1)
P("Research papers (carried from v1's sweep, summarised from abstracts; module owners must read the full papers)", h2)
refs = [
    ("Blind Identification of Channel Codes: A Subspace-Coding Approach (arXiv 2601.15903, 2026)", "https://arxiv.org/abs/2601.15903"),
    ("Open-set blind recognition of non-binary LDPC codes (Digital Communications and Networks, 2025)", "https://www.sciencedirect.com/science/article/pii/S2352864825001506"),
    ("Joint Blind Identification of Cyclic Codes and Synchronization Scramblers with soft information (IET Communications, 2026)", "https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/cmu2.70192"),
    ("Blind identification of an unknown interleaved convolutional code (arXiv 1501.03715)", "https://arxiv.org/abs/1501.03715"),
    ("Blind Recognition of RS Codes Based on GFFT and Reliability Verification (IEEE, 2023)", "https://ieeexplore.ieee.org/document/10149421"),
    ("Blind Recognition of Frame Synchronization Based on Deep Learning (Sensors, 2024)", "https://doi.org/10.3390/s24206767"),
    ("IQFM: A Wireless Foundational Model for I/Q Streams (arXiv 2506.06718, 2025)", "https://arxiv.org/abs/2506.06718"),
    ("EMind: A Foundation Model for Multi-task Electromagnetic Signals Understanding (arXiv 2508.18785, 2025)", "https://arxiv.org/abs/2508.18785"),
    ("Radio-FM: A Foundation Model for Radio Signal Representation Learning (arXiv 2608.05793, 2026)", "https://arxiv.org/abs/2608.05793"),
    ("RFPrompt: Prompt-Based Expert Adaptation of the Large Wireless Model (arXiv 2605.03279, 2026)", "https://arxiv.org/abs/2605.03279"),
    ("Geometry-Aware Contrastive Learning for Few-Shot AMR (arXiv 2605.26600, 2026)", "https://arxiv.org/abs/2605.26600"),
    ("DenoMAE: A Multimodal Autoencoder for Denoising Modulation Signals (arXiv 2501.11538, 2025)", "https://arxiv.org/abs/2501.11538"),
    ("Conformal Shield: conformal prediction sets for AMC (arXiv 2402.17450)", "https://arxiv.org/abs/2402.17450"),
    ("CSRD2025: A Large-Scale Synthetic Radio Dataset for Spectrum Sensing (arXiv 2508.19552, 2025)", "https://arxiv.org/abs/2508.19552"),
    ("ZoomSpec: Physics-Guided Coarse-to-Fine Wideband Spectrum Sensing (arXiv 2604.13568, 2026)", "https://arxiv.org/abs/2604.13568"),
    ("Scalable hierarchical protocol format inference (Empirical Software Engineering, 2026)", "https://link.springer.com/article/10.1007/s10664-026-10814-6"),
]
table([["#", "Paper", "Link"]] + [[str(i), t, f'<link href="{u}"><font color="#2a6f77"><u>{u}</u></font></link>'] for i, (t, u) in enumerate(refs, 1)],
      [8 * mm, 100 * mm, 72 * mm])
P("Established theory and tools used by the new innovations", h2)
table([["Used in", "Foundation"],
       ["C2, C3", "A. Wald, 'Sequential tests of statistical hypotheses', Annals of Mathematical Statistics, 1945 (SPRT); Bayesian model comparison; Cramér-Rao bound."],
       ["C1", "G. M. Ljung and G. E. P. Box, 'On a measure of lack of fit in time series models', Biometrika, 1978 (whiteness test); successive interference cancellation."],
       ["D2", "J. L. Massey, 'Shift-register synthesis and BCH decoding', IEEE Trans. Information Theory, 1969 (Berlekamp-Massey)."],
       ["D6", "C. C. Watterson et al., 'Experimental confirmation of an HF channel model', IEEE Trans. Communication Technology, 1970; ITU-R F.1487."],
       ["C5", "GNU Radio (gr-digital, gr-fec); SigMF specification."],
       ["Tier 3 truth", "SatDump, gr-satellites, dumphfdl, AIS-catcher, multimon-ng, fldigi; KiwiSDR public receiver network."]],
      [22 * mm, 158 * mm])

def footer(c, doc):
    c.saveState(); c.setFont("Arial", 7.5); c.setFillColor(colors.grey)
    c.drawString(15 * mm, 9 * mm, "Project SANJAYA - winning plan v2 for SIH 26147 (NTRO) - internal team document")
    c.drawRightString(195 * mm, 9 * mm, f"Page {doc.page}"); c.restoreState()

doc = SimpleDocTemplate(r"D:\spacetech\winning plan 147 v2.pdf", pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                        topMargin=14 * mm, bottomMargin=16 * mm, title="Project SANJAYA - Winning Plan v2")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("ok")
