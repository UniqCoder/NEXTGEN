import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY, ACCENT, LIGHT = colors.HexColor("#14213d"), colors.HexColor("#c8553d"), colors.HexColor("#f4f1ea")
TEAL = colors.HexColor("#2a6f77")
body = ParagraphStyle("b", fontName="Arial", fontSize=9.6, leading=13.4, spaceAfter=4)
small = ParagraphStyle("s", fontName="Arial", fontSize=7.9, leading=10.2)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=16, leading=20, textColor=NAVY, spaceBefore=4, spaceAfter=7)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=11.5, leading=15, textColor=ACCENT, spaceBefore=7, spaceAfter=3)
title = ParagraphStyle("t", parent=body, fontName="Arial-Bold", fontSize=30, leading=36, textColor=NAVY)
bullet = ParagraphStyle("bl", parent=body, leftIndent=12, bulletIndent=3, spaceAfter=2)
W = 180 * mm

story = []
def P(t, s=body): story.append(Paragraph(t, s))
def B(items):
    for t in items: story.append(Paragraph(t, bullet, bulletText="\u2022"))
    story.append(Spacer(1, 3))
def table(rows, widths, head=True, zebra=True, extra=None):
    data = [[Paragraph(str(c), small) for c in r] for r in rows]
    if head: data[0] = [Paragraph(f'<font color="white"><b>{c}</b></font>', small) for c in rows[0]]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9c2b2")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
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
story.append(Spacer(1, 30 * mm))
P('<font color="#c8553d">SIH 2026 &middot; PS 26147 &middot; NTRO</font>', ParagraphStyle("k", parent=body, fontSize=12, fontName="Arial-Bold"))
P("Project SANJAYA", title)
P("The winning plan: a blind-signal forensics workbench that <b>proves</b> every answer it gives", ParagraphStyle("st", parent=body, fontSize=14, leading=19, textColor=TEAL))
story.append(Spacer(1, 8 * mm))
callout("<b>Why the name.</b> In the Mahabharata, Sanjaya sees a distant battlefield he is not present at and reports it "
        "truthfully to the king. That is exactly the job: look at a recording from a sensor far away, with no cooperation "
        "from the transmitter, and report what it really is - with evidence. (Working name; team can change it.)", bg=colors.white, border=TEAL)
story.append(Spacer(1, 4 * mm))
P("<b>Built from:</b> <i>introduction to 147.pdf</i> (what the PS asks) + <i>repos.pdf</i> (what 43 competing public repos already do) "
  "+ a literature sweep of 2025-26 research on blind code/interleaver/scrambler identification, RF foundation models, "
  "open-set & conformal recognition, and wideband multi-signal detection.")
P("<b>Rule of this document:</b> every feature is either (a) demanded by the PS, or (b) something the competing field does not do. "
  "Anything generic that 20+ teams already have is treated as table stakes, not as a USP.")
story.append(PageBreak())

# ======================= 1. THESIS =======================
P("1. The winning thesis", h1)
P("After reading 43 competing repos, the pattern is clear. Nearly every team builds the same <b>forward pipeline</b>: "
  "load file -> classify modulation -> demodulate -> try a fixed catalogue of decoders (K=7 Viterbi, RS(255,223), one LDPC) "
  "-> search for CCSDS sync word -> show a confidence %. The best ones add honesty labels ('UNKNOWN', 'VALIDATED').")
callout("<b>Everyone else answers: \"what do we think this signal is?\"</b><br/>"
        "<b>SANJAYA answers: \"here is the signal rebuilt from our decoded bits - subtract it from your recording and only noise is left.\"</b><br/><br/>"
        "We turn signal analysis from <i>classification</i> into <i>analysis-by-synthesis with proof</i>. Every hypothesis "
        "(modulation, symbol rate, interleaver, code, scrambler, frame) is only accepted when re-synthesising the waveform "
        "from the recovered bits explains the recorded energy down to the noise floor. Nothing is guessed; ambiguity is "
        "carried forward as a hypothesis and killed by evidence.")
P("Three pillars, in priority order (exactly your criteria):", h2)
table([["Pillar", "What it means", "Why it wins"],
       ["A. Expected solution, 100%", "Every clause of the PS (i-v + spectral features + GUI + header/payload) implemented, benchmarked, and traceable to a module.",
        "Judges first tick the checklist. Missing one item loses to average teams. We make coverage visible with a live compliance matrix."],
       ["B. USPs nobody has", "8 capabilities that 0-2 of the 43 repos attempt, each backed by 2025-26 research (Section 4).",
        "Differentiation at the level of a professional COMINT tool, not a student dashboard."],
       ["C. Provable accuracy", "SANJAYA-Bench: 10k+ ground-truth files, real over-the-air recordings, BER curves overlaid on theory, published KPIs.",
        "'Most accurate' becomes a measured claim, not an adjective. NTRO engineers trust curves, not slogans."]],
      [35 * mm, 72 * mm, 73 * mm])
P("One-line pitch", h2)
P("<i>\"Drop in any .IQ or .wav from any sensor. SANJAYA blindly recovers the complete transmitter recipe - modulation, symbol "
  "rate, interleaver, code, scrambler, frame format - names the standard if it knows it, reveals hidden signals underneath, "
  "and issues a Decode Certificate proving every parameter.\"</i>")

# ======================= 2. GAP MAP =======================
P("2. Competitive gap map (from repos.pdf)", h1)
P("Approximate counts from the 43 README/file-tree reviews. Green rows are where SANJAYA plants its flag.")
gap = [
    ["Capability", "Repos doing it (of 43)", "SANJAYA"],
    ["File loader + PSD + waterfall + constellation", "~40", "Table stakes (done better, not sold as USP)"],
    ["ML modulation classifier (RF / CNN)", "~25", "Table stakes; we fuse 3 experts + conformal sets"],
    ["Fixed catalogue decoders (K=7 Viterbi, RS 255/223)", "~20", "Table stakes; we identify codes blindly"],
    ["GF(2) rank blind interleaver detection (hard bits)", "~5", "Upgraded to soft-decision + joint code/interleaver"],
    ["Soft-decision (LLR) code & interleaver identification", "0-1", "USP"],
    ["Open-set LDPC reconstruction (recover H, not pick from list)", "0", "USP"],
    ["Blind scrambler (LFSR) polynomial recovery", "~2 (fixed descramblers)", "USP"],
    ["Waveform-level re-synthesis residual verification", "0", "Core USP"],
    ["Named-standard recognition (STANAG, CCSDS, AIS, NAVTEX...)", "0", "USP"],
    ["Sample-rate back-solving + sensor clock-ppm forensics", "0", "USP"],
    ["Protocol field discovery: counters, CRC polynomial, schema export", "~1 (CRC search)", "USP"],
    ["Multi-signal scene + successive cancellation of decoded emitters", "~3 partial (detection only)", "USP"],
    ["HF channel realism (Watterson) + adaptive equaliser", "~1-2", "USP"],
    ["Validation on real over-the-air recordings", "2", "USP (broader, standards-rich)"],
    ["Statistical coverage guarantee on answers (conformal)", "0 (1 does multiple-test correction)", "USP"],
]
table(gap, [95 * mm, 40 * mm, 45 * mm],
      extra=[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#dcefe9")) for i in range(5, len(gap))])

# ======================= 3. PILLAR A =======================
story.append(PageBreak())
P("3. Pillar A - Expected solution: zero gaps", h1)
P("Each PS requirement, the module that delivers it, how we prove it, and the acceptance KPI. KPIs are <b>targets we commit to "
  "measure on SANJAYA-Bench</b>, not claims yet.")
cov = [
    ["PS requirement", "SANJAYA module & method", "Proof / KPI target"],
    [".IQ and .wav input (different formats, different sensors)", "<b>Recording Forensics</b>: WAV (mono real / stereo IQ / 8-32 bit / float), raw IQ dtype + endianness sniffer "
     "(u8, i8, i16, i32, f16, f32, f64; LE/BE), SigMF/sidecar/filename metadata, DC & IQ-imbalance correction; ambiguous choices (IQ swap / spectral inversion) kept as hypotheses.",
     "Correct dtype on 100% of bench formats; ambiguity always surfaced."],
    ["(i) Sampling frequency", "File Fs from header/metadata; if absent -> normalised analysis, then <b>back-solve true Fs</b> once a standard/baud is recognised; flag WAV files whose header Fs contradicts the anti-alias edge.",
     "Fs recovered within 0.1% on standard-anchored files."],
    ["(i) Other parameters (feasible extras)", "Centre/offset (M-th power FFT), occupied BW (99% & x-dB), SNR (M2M4 + spectral), symbol rate (cyclostationary lines + cyclic autocorr, refined in timing loop), roll-off, FSK tones/spacing/modulation index h, burst on/off times, sensor clock ppm.",
     "Symbol-rate error &lt; 0.05%; SNR +/- 1 dB above 0 dB."],
    ["(i) Modulation", "3-expert fusion: physics features (cumulants C40/C42/C63, power-law lines, envelope & inst-freq stats) + compact IQ network + decode-fit expert (EVM after trial demod). Output = conformal <b>prediction set</b> + open-set 'novel' flag.",
     "&gt;= 98% top-1 at SNR &gt;= 10 dB (BPSK..64QAM, 2/4/8-FSK, GMSK); 95% set coverage guaranteed."],
    ["(i) FEC", "Blind code ID: conv (n,k,K, generators) via soft rank + dual-code/GJETP; RS (n,k,m) via Galois-field Fourier spectra; LDPC via catalogue syndrome test, then open-set sparse-dual recovery; concatenation found by recursive peeling.",
     "Conv/RS ID &gt;= 95% at channel BER 1e-2."],
    ["(i) Interleaving", "Block (RxC), convolutional (B,J), diagonal, pseudo-random: soft rank-profile scan, joint with code ID; PN via standard permutations + LFSR seed search + parity-graph recovery.",
     "Block/conv period ID &gt;= 95% at BER 1e-2."],
    ["(ii) Demodulate FSK, QAM, PSK", "Universal linear receiver: RRC matched filter, feed-forward (Oerder-Meyr) + Gardner timing, M-th power + Costas/DD-PLL carrier, CMA->DD-LMS fractionally-spaced equaliser; FSK filter-bank / discriminator; differential modes; <b>soft LLR output</b>.",
     "BER within 0.5 dB of theory curve for each scheme (AWGN)."],
    ["(iii) De-interleaving: Block, Conv, Diagonal, PN", "All four implemented as invertible operators, parameterised by the identifier above; manual override in GUI.",
     "Bit-exact round-trip tests; blind recovery on bench."],
    ["(iv) FEC: short-K conv + Viterbi, RS, concatenated, LDPC", "C++ soft Viterbi (K 3-9, rates 1/2, 1/3, punctured 2/3, 3/4); RS Berlekamp-Massey (GF(2^m)); CCSDS-style concatenation; LDPC normalised min-sum (catalogue: CCSDS, 802.11n, DVB-S2 short, 5G NR BG2 + recovered H).",
     "Coding gain matches theory within 0.5 dB; &gt; 20 Mbit/s Viterbi."],
    ["(v) Bit-stream correlation, header & payload", "<b>Bit-Lens</b>: autocorrelation frame length, soft sync-word discovery, aligned-frame raster, per-bit entropy map, field segmentation (constant / counter / CRC / length / payload), encryption-likelihood flag.",
     "Frame length &amp; sync word found on 100% of framed bench files."],
    ["Spectral features: Fs, constellation, waterfall", "GUI: linked waterfall + PSD + constellation (time-animated) + eye + inst. frequency + cyclic spectrum + rank-profile plot.",
     "All views on 100 MB file &lt; 2 s."],
    ["GUI-based, automated", "Desktop PySide6 + pyqtgraph; <b>Autopilot</b> (one click, full chain) and <b>Expert</b> mode (override any stage, re-run downstream).",
     "Full chain on 1 M-sample file &lt; 10 s."],
    ["'GNU Radio, python, C++'", "Python orchestration; C++ (pybind11) hot kernels; GNU Radio OOT block exposing the analyser in flowgraphs.",
     "All three named technologies used for a real reason."],
]
table(cov, [38 * mm, 94 * mm, 48 * mm])

# ======================= 4. USPs =======================
story.append(PageBreak())
P("4. Pillar B - The eight USPs", h1)
P("Format for each: what it is, why nobody in the field has it, the research behind it, how we build it with realistic effort, "
  "and the moment it creates in the demo.")

usps = [
("USP 1 - Proof-of-Decode: re-synthesis residual verification (the core idea)",
 "After decoding, SANJAYA re-encodes the recovered bits through the discovered chain (code -> interleaver -> scrambler -> mapper -> pulse shape), "
 "applies the estimated channel (gain, CFO, phase, timing, equaliser taps), and <b>subtracts the rebuilt waveform from the recording</b>. "
 "It reports <i>explained energy %</i>, residual-to-noise ratio and a whiteness test. If the residual is white noise at the estimated noise floor, the "
 "whole recipe is proven. Output: a signed <b>Decode Certificate</b> (file hash, every parameter, its evidence, its confidence set).",
 "Best competitors verify at bit level (CRC / re-encode BER). Nobody verifies at the waveform level, which is the only check that also validates "
 "symbol rate, pulse shape, channel and modulation at once - and catches 'plausible but wrong' decodes.",
 "Analysis-by-synthesis and successive interference cancellation are standard receiver theory; we apply them as a forensic verifier.",
 "Medium. Reuses our own modulator (needed for the generator anyway). 1 person, ~1.5 weeks.",
 "Show the waterfall, press 'Prove': the signal vanishes from the waterfall, leaving only noise. Certificate prints."),
("USP 2 - Soft-decision, joint blind coding-layer engine",
 "Identifies interleaver + code <b>jointly</b> from soft LLRs instead of hard bits: rank-profile scans on soft matrices, dual-code / GJETP recovery of "
 "convolutional generators, Galois-field Fourier spectra for RS, recursive peeling for concatenated codes, and an <b>open-set LDPC mode</b> that reconstructs "
 "a sparse parity-check matrix for short codes instead of choosing from a list. The GUI shows the <b>rank-profile plot</b> - the visible dip at the true "
 "interleaver period - so the analyst sees why.",
 "~5 repos do hard-decision GF(2) rank on one layer; everyone else uses a fixed decoder list. Soft, joint and open-set identification: none.",
 "Subspace-coding blind code ID (arXiv 2601.15903, 2026); open-set non-binary LDPC recognition via GJCE + sparsification (Digital Comms &amp; Networks, 2025); "
 "CNN / ConvLSTM-TFN soft blind conv-code recognition (Int. J. Intelligent Systems 2025; Sensors 2025); dual-branch CNN channel-code recognition (Sci. Reports 2026); "
 "joint interleaved-conv-code recovery via parity-check graphs (arXiv 1501.03715); GFFT + reliability verification for RS (IEEE 2023).",
 "High, but staged: hard rank (week 3) -> soft rank (week 5) -> open-set LDPC for n &lt;= 1024 (week 7-8). 2 people. Bit-packed uint64 GF(2) elimination in C++.",
 "Judge picks interleaver size secretly; rank-profile dips exactly there in seconds."),
("USP 3 - Blind scrambler recovery",
 "Additive (synchronous) and self-synchronising LFSR scramblers identified blindly (Walsh-Hadamard / eigen-analysis, Berlekamp-Massey on idle or preamble runs), "
 "plus a library of standard polynomials (CCSDS, DVB PRBS-15, 802.11 x^7+x^4+1, V.35, ...). Descrambling is inserted into the chain automatically.",
 "Real systems scramble between FEC and modulation; the PS does not mention it, so almost every team will fail on real signals. ~2 repos have a fixed descrambler; none identify an unknown one.",
 "Joint blind identification of cyclic codes and synchronous scramblers with soft information (IET Communications, 2026); feedback-polynomial reconstruction in noise (IET Comms 2022-23).",
 "Medium. 1 person, ~1 week.",
 "'Other tools stop here - bits still look random. SANJAYA finds x^15+x^14+1 and the frames appear.'"),
("USP 4 - Signal Genome: named-standard recognition + sample-rate back-solving",
 "A descriptor library (~30 real standards to start: STANAG 4285/4529/4539, MIL-STD-188-110A/B serial, CCSDS TM, DVB-S, AIS, NAVTEX/SITOR-B, RTTY, POCSAG, "
 "ACARS, HFDL, DMR, dPMR, TETRA, NOAA-APT, APRS/AX.25, ...). Measured recipe vectors are matched to it: <i>\"91% consistent with STANAG 4285, 600 bps long interleave\"</i>. "
 "Once a standard is matched, its nominal baud gives the <b>true sample rate</b> of a headerless IQ file and the <b>sensor clock error in ppm</b>.",
 "0 of 43. Only commercial suites (PROCITEC, WAVECOM) do this - it is what makes analysts' output directly usable by 'designated sensors'.",
 "Public standards documents + Signal Identification Wiki descriptors; open-set recognition literature (Open-DS, IET RSN 2025) for 'close to X but not X'.",
 "Low-medium: data entry + scoring. 1 person part-time throughout. Generators for ~10 standards double as test data.",
 "Real HF recording loads -> 'STANAG 4285 detected, recorder clock +38 ppm fast'."),
("USP 5 - Bit-Lens: protocol structure discovery and schema export",
 "Beyond sync words: aligned-frame raster with adjustable width (the classic analyst view), per-bit entropy / constancy heat-map, automatic detection of "
 "<b>counters</b> (increment patterns), <b>length fields</b>, and <b>CRC fields including the polynomial</b> (bits that are a linear GF(2) function of others -> solve). "
 "High-entropy payload flagged as likely encrypted/compressed. Exports the discovered frame layout as a <b>Kaitai Struct / Wireshark-dissector</b> style schema.",
 "Everyone stops at 'sync word found at offset N'. The PS explicitly asks to identify header and payload - we hand back a dissector.",
 "Deep-learning blind frame-sync recognition (Sensors 2024); bitstream protocol format reverse-analysis and hierarchical format inference (Empirical SE 2026).",
 "Medium. 1 person, ~1.5 weeks. Pure GF(2) linear algebra + statistics; no ML needed.",
 "Bit raster snaps into columns; fields colour themselves: SYNC | COUNTER | LEN | PAYLOAD | CRC-16/CCITT."),
("USP 6 - Scene mode: multi-signal detection + successive cancellation",
 "Captures from real sensors hold many emitters. OS-CFAR on the spectrogram + connected components list every emitter (freq, BW, on/off time); each is "
 "channelised and analysed. After a strong signal is decoded and proven (USP 1), it is <b>subtracted</b> - revealing weaker signals hidden under it, "
 "which are then analysed in turn.",
 "~3 repos detect multiple signals; none decode-and-cancel to uncover buried ones.",
 "Wideband multi-signal detection (CSRD2025 dataset, arXiv 2508.19552; ZoomSpec physics-guided coarse-to-fine sensing, arXiv 2604.13568; dense multi-emitter "
 "blind detection, 2026); TorchSig WidebandSig53 benchmark.",
 "Medium. CFAR version first (week 4); optional YOLO-style detector trained on TorchSig later.",
 "Strong QPSK is removed, a 12 dB weaker FSK beacon 'appears' in the residual waterfall and gets decoded."),
("USP 7 - HF-grade robustness (the PS names HF first)",
 "Watterson/ITU-R F.1487 HF channel simulator (multipath delay + Doppler spread; good / moderate / poor profiles) in the generator and bench; fractionally-spaced "
 "adaptive equaliser; SSB-audio .wav handling (real pass-band at ~1-3 kHz, spectral inversion USB/LSB kept as a hypothesis). Validation on <b>real public HF recordings</b> "
 "(KiwiSDR/WebSDR: NAVTEX, RTTY weather, STANAG 4285, HFDL, ALE).",
 "Almost every repo tests on AWGN only. HF fading breaks naive timing/carrier loops - they will fail the moment a judge brings a real HF file.",
 "Standard HF channel models; DenoMAE multimodal denoising for low-SNR modulation signals (arXiv 2501.11538) as optional front-end.",
 "Medium. Simulator ~3 days; equaliser ~1 week; data collection ongoing.",
 "Same STANAG signal through 'poor' HF channel: competitor-style receiver fails live, SANJAYA locks."),
("USP 8 - Trust layer: conformal sets, open-set 'novel', few-shot teach",
 "Classifiers output <b>conformal prediction sets</b> with a guaranteed coverage (e.g. {QPSK, 8PSK} at 95%), not a naked %. An embedding-prototype head flags "
 "<b>novel</b> signals and lets an analyst <b>teach</b> a new class from ~5 examples; the lab's confirmed results become a local 'mission memory' "
 "that recognises previously seen emitters.",
 "Repos print arbitrary confidence percentages or ad-hoc 'epistemic states'. None give a statistical guarantee or learn from the analyst.",
 "Conformal prediction for wireless AI / AMC (Conformal Shield); RF foundation models &amp; few-shot adaptation: IQFM (arXiv 2506.06718, 2025), EMind (arXiv 2508.18785, 2025), "
 "Radio-FM (arXiv 2608.05793, 2026), RFPrompt (arXiv 2605.03279, 2026), geometry-aware contrastive few-shot AMR (arXiv 2605.26600, 2026).",
 "Low for conformal (split-CP is ~50 lines on a calibration set); medium for few-shot (small contrastive encoder trained on TorchSig + our generator).",
 "Unknown chirp signal -> 'NOVEL, closest: none'. Analyst labels 5 -> next file recognised."),
]
for name, what, why, research, effort, demo in usps:
    rows = [[Paragraph(f'<font color="white"><b>{name}</b></font>', small), ""],
            [Paragraph("<b>What</b>", small), Paragraph(what, small)],
            [Paragraph("<b>Why nobody has it</b>", small), Paragraph(why, small)],
            [Paragraph("<b>Research basis</b>", small), Paragraph(research, small)],
            [Paragraph("<b>Build / effort</b>", small), Paragraph(effort, small)],
            [Paragraph("<b>Demo moment</b>", small), Paragraph(f"<i>{demo}</i>", small)]]
    t = Table(rows, colWidths=[30 * mm, 150 * mm])
    t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9c2b2")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 1), (0, -1), LIGHT), ("BACKGROUND", (1, 5), (1, 5), colors.HexColor("#fbeee9"))]))
    story.append(KeepTogether([t, Spacer(1, 7)]))

P("Deliberately NOT doing (anti-generic list)", h2)
B(["<b>LLM chatbot / 'AI copilot'</b> - at least 4 repos have one; for an air-gapped intelligence user it is a liability, not a feature. Our explanations come from evidence, not generated text.",
   "<b>Cloud, login, RBAC, Firebase, Postgres</b> - irrelevant to NTRO's offline analyst; costs weeks.",
   "<b>Neon 'military-grade' dashboards and marketing adjectives</b> - judges from NTRO will discount them. Our UI is a quiet, dense analyst instrument.",
   "<b>Black-box-only deep learning</b> - DL is one of three experts, never the sole judge."])

# ======================= 5. ARCHITECTURE / CYCLE =======================
story.append(PageBreak())
P("5. The SANJAYA analysis cycle", h1)
P("The product itself is a loop, not a line. Each turn either proves a hypothesis or kills it; every stage can hand ambiguity forward.")

d = Drawing(W, 105 * mm)
cx, cy, r = W / 2, 52 * mm, 38 * mm
stages = [("1 OBSERVE", "forensics, scene"), ("2 MEASURE", "Fs, BW, SNR, baud"), ("3 HYPOTHESISE", "mod sets, standards"),
          ("4 DEMODULATE", "soft LLRs"), ("5 UNWRAP", "interleaver, code,\nscrambler"), ("6 STRUCTURE", "Bit-Lens fields"),
          ("7 PROVE", "re-synthesise,\nsubtract"), ("8 LEARN", "certificate, memory")]
n = len(stages)
pts = []
for i, (a, b) in enumerate(stages):
    ang = math.pi / 2 - 2 * math.pi * i / n
    x, y = cx + r * 1.55 * math.cos(ang), cy + r * math.sin(ang)
    pts.append((x, y))
for i in range(n):
    (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
    d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#c9c2b2"), strokeWidth=2))
d.add(Circle(cx, cy, 17 * mm, fillColor=NAVY, strokeColor=None))
d.add(String(cx, cy + 3, "EVIDENCE", fontName="Arial-Bold", fontSize=10, fillColor=colors.white, textAnchor="middle"))
d.add(String(cx, cy - 9, "hypotheses live here", fontName="Arial", fontSize=6.5, fillColor=colors.white, textAnchor="middle"))
for (x, y), (a, b) in zip(pts, stages):
    bw, bh = 36 * mm, 14 * mm
    d.add(Rect(x - bw / 2, y - bh / 2, bw, bh, rx=4, ry=4, fillColor=colors.white,
               strokeColor=ACCENT if a.startswith("7") else TEAL, strokeWidth=1.6 if a.startswith("7") else 1))
    d.add(String(x, y + 2, a, fontName="Arial-Bold", fontSize=8, fillColor=NAVY, textAnchor="middle"))
    for k, ln in enumerate(b.split("\n")):
        d.add(String(x, y - 6 - 7 * k, ln, fontName="Arial", fontSize=6.3, fillColor=colors.HexColor("#555555"), textAnchor="middle"))
d.add(String(cx, 2 * mm, "Failed proof at 7 -> back to 3 with the next-best hypothesis. Proven signal at 7 -> subtracted -> scene re-scanned for hidden emitters.",
             fontName="Arial-Italic", fontSize=7.2, fillColor=ACCENT, textAnchor="middle"))
story.append(d)
story.append(Spacer(1, 4))
table([["Stage", "Key algorithms", "Hand-off (what it passes on)"],
       ["1 Observe", "dtype/endianness sniff, SigMF/metadata, DC/IQ-imbalance, OS-CFAR scene detection, channelisation", "List of emitters + normalised complex baseband per emitter + unresolved format hypotheses"],
       ["2 Measure", "Welch PSD, 99% BW, M2M4 SNR, cyclostationary baud, M-th power CFO, inst-freq histogram, burst timing", "Parameter vector with uncertainty intervals"],
       ["3 Hypothesise", "Cumulant rules + IQ network + standards match -> conformal set", "Ranked, pruned hypothesis list (mod x baud x standard)"],
       ["4 Demodulate", "RRC MF, Oerder-Meyr/Gardner, Costas/DD-PLL, CMA->LMS FSE, FSK bank", "Soft LLR stream per hypothesis incl. phase rotations"],
       ["5 Unwrap", "Soft rank profile, joint interleaver+code ID, Viterbi/RS/LDPC, recursive peel, LFSR recovery", "Decoded bits + recipe + syndrome/CRC evidence"],
       ["6 Structure", "Autocorr frame length, sync discovery, counters, CRC polynomial solve, entropy", "Frame schema (Kaitai-style) + header/payload split"],
       ["7 Prove", "Re-encode -> remodulate -> apply channel -> subtract -> whiteness test", "PASS/FAIL + explained-energy % + residual for next scene pass"],
       ["8 Learn", "Certificate PDF/JSON, mission memory, few-shot prototype update", "Report for 'designated sensors'; faster recognition next time"]],
      [22 * mm, 88 * mm, 70 * mm])

P("Software layout (kept deliberately small)", h2)
table([["Layer", "Tech", "Why"],
       ["Core DSP & coding", "Python 3.11 + NumPy/SciPy; <b>C++17 via pybind11</b> for Viterbi, LDPC min-sum, bit-packed GF(2) elimination; <i>galois</i> for GF(2^m) RS math", "Speed where it matters; Python everywhere else for velocity"],
       ["Reference checks", "AFF3CT / liquid-dsp / GNU Radio blocks used as <b>cross-check oracles</b> in tests", "Proves our decoders match established implementations"],
       ["ML", "PyTorch small encoders (&lt; 5 M params, CPU inference), scikit-learn for feature expert, split conformal", "Runs offline on a laptop"],
       ["GUI", "PySide6 + pyqtgraph (OpenGL), one window, docked panels", "Handles 100 MB+ files interactively; true desktop tool"],
       ["Integration", "CLI for batch; <b>GNU Radio OOT Python block</b>; SigMF annotations out", "Fits NTRO's existing sensor chains - the PS names GNU Radio"],
       ["Packaging", "Single offline installer (PyInstaller) + wheels; no network access at runtime", "Air-gap ready"]],
      [30 * mm, 95 * mm, 55 * mm])

# ======================= 6. IMPLEMENTATION SEQUENCE =======================
story.append(PageBreak())
P("6. Implementation sequence (the build cycle)", h1)
P("Ten weeks, six phases. <b>Rule: main branch is demo-able at the end of every phase</b> - if time runs out, we present the last green phase, never a broken build. "
  "Every sprint ends with the SANJAYA-Bench run and a KPI diff.")
phases = [
    ["Phase / weeks", "Build", "Exit criterion (must be true to move on)"],
    ["P0 - Idea round<br/>(days 1-4)", "PPT with thesis, gap map, architecture, USPs; 2-minute prototype video: synthetic QPSK+conv+block file decoded and 'proved' (residual vanishes).",
     "Idea submitted with a <b>working</b> proof-of-decode clip - most idea decks will have only mockups."],
    ["P1 - Spine<br/>(W1-2)", "Recording Forensics; SANJAYA-Gen v1 (7 mods, RRC, CFO, timing, AWGN, truth JSON); measurement suite; linear receiver for BPSK/QPSK + FSK; GUI shell (waterfall, PSD, constellation); bench harness + CI.",
     "Synthetic BPSK/QPSK/2FSK -> bits end-to-end in GUI; bench prints KPIs automatically."],
    ["P2 - Coding core<br/>(W3-4)", "C++ soft Viterbi; RS (galois); block + conv interleavers with hard rank-profile ID; scrambler library + LFSR recovery; sync discovery; Bit-Lens v1 raster; <b>Proof-of-Decode v1</b>; OS-CFAR scene mode.",
     "Blind recovery of QPSK + scrambler + block interleaver + K=7 code, proven by residual."],
    ["P3 - Full PS coverage<br/>(W5-6)", "8PSK, 16/64-QAM, GMSK, 4/8-FSK; equaliser; diagonal + PN interleavers; concatenated RS+conv (recursive peel); LDPC catalogue + min-sum; 3-expert AMC + conformal sets; soft rank-profile; Watterson HF channel in bench.",
     "<b>Compliance matrix 100% green</b> on bench (every row in Section 3)."],
    ["P4 - USP depth<br/>(W7-8)", "Signal Genome (30 standards) + Fs/ppm back-solve; open-set LDPC (n &lt;= 1024); Bit-Lens v2 (counters, CRC polynomial, schema export); SIC hidden-signal reveal; few-shot teach; GNU Radio block; real OTA dataset (&gt;= 30 recordings).",
     "Each USP has a 30-second scripted demo that works 10/10 times."],
    ["P5 - Hardening<br/>(W9)", "10k-file bench; BER-vs-theory curves; failure triage; performance (C++ hot paths, mmap streaming); cut anything below 90% reliability.",
     "KPI table filled with measured numbers; no crash on 500 random files incl. garbage input."],
    ["P6 - Showtime<br/>(W10)", "Mystery-signal challenge app; Decode Certificate polish; pitch deck with real curves; judge Q&amp;A drills; offline installer on 2 laptops + USB backup.",
     "Full demo rehearsed 5 times under 7 minutes, including one live failure-recovery."],
]
table(phases, [30 * mm, 100 * mm, 50 * mm])

P("Team of six - ownership, not overlap", h2)
table([["Role", "Owns", "Phase peak"],
       ["1. DSP lead", "Forensics, measurements, receiver, equaliser, HF channel", "P1-P3"],
       ["2. Coding-theory lead", "Viterbi/RS/LDPC, rank engine, joint ID, open-set LDPC", "P2-P4"],
       ["3. Protocol & crypto-structure", "Scramblers, Bit-Lens, CRC solve, schema export, Signal Genome library", "P2-P4"],
       ["4. ML & trust", "3-expert AMC, conformal, open-set, few-shot, dataset pipelines (TorchSig/RadioML/own)", "P3-P4"],
       ["5. GUI & integration", "PySide6 app, Autopilot/Expert modes, GNU Radio block, installer", "P1, P4-P6"],
       ["6. Bench, data & pitch (team lead)", "SANJAYA-Gen, bench/CI, OTA recordings, KPIs, deck, demo script", "all"]],
      [45 * mm, 105 * mm, 30 * mm])

# ======================= 7. ACCURACY =======================
story.append(PageBreak())
P("7. Pillar C - The accuracy programme", h1)
P("'Most accurate system' is only believable with numbers nobody else shows. SANJAYA-Bench is built in week 1 and runs on every merge.")
table([["Component", "Content"],
       ["SANJAYA-Gen (synthetic)", "Standards-accurate generators; mods x baud x SNR (-5..30 dB) x CFO x clock drift x HF Watterson profiles x code x interleaver x scrambler x frame; "
        "sensor impairments (DC, IQ imbalance, dtype, sample-rate mismatch). Every file ships with truth JSON. Target 10k+ files."],
       ["Public ML datasets", "TorchSig Sig53 / WidebandSig53 (pre-training, multi-signal), RadioML 2018.01A (comparability with published AMC numbers), CSRD2025 (wideband sensing)."],
       ["Real over-the-air set", "&gt;= 30 recordings of public, unencrypted signals: HF via KiwiSDR/WebSDR (NAVTEX, weather RTTY, STANAG 4285 idle, HFDL, ALE); VHF/UHF via RTL-SDR (AIS GMSK, POCSAG, APRS AFSK, NOAA-APT). "
        "Only structure is analysed; no private content is decoded or shown."],
       ["Curves we will show", "BER vs Eb/N0 per modulation with theory overlay; coding gain vs theory for each code; AMC confusion matrix per SNR; interleaver/code ID accuracy vs channel BER; "
        "conformal coverage vs target; false-decode rate (should be ~0 thanks to Proof-of-Decode)."],
       ["Honesty metric", "<b>False-certificate rate</b>: how often a PASS certificate is wrong. Target 0 on the whole bench. This is the number that sells the system to NTRO."]],
      [40 * mm, 140 * mm])

# ======================= 8. DEMO =======================
P("8. How we win the room", h1)
P("Seven-minute demo script", h2)
table([["Min", "Beat", "What judges see"],
       ["0:00", "The problem, in one frame", "A raw HF recording: noise-like waterfall. 'An analyst spends hours on this. Watch.'"],
       ["0:40", "Autopilot on a real HF file", "Scene -> STANAG 4285 recognised -> sample rate &amp; clock ppm back-solved -> constellation locks through fading."],
       ["2:00", "The Mystery-Signal Challenge", "A judge picks modulation, interleaver size, code and scrambler on our generator tablet, blind to us. SANJAYA recovers all of them; rank-profile dip shown."],
       ["3:30", "Proof-of-Decode", "Press 'Prove': signal disappears from the waterfall, residual is white. Certificate prints."],
       ["4:30", "Hidden signal", "After cancellation, a weak FSK beacon emerges from under the strong carrier and is decoded."],
       ["5:30", "Bit-Lens", "Raster snaps into columns; fields auto-labelled SYNC | COUNTER | LEN | PAYLOAD | CRC-16 (polynomial shown); schema exported."],
       ["6:15", "Numbers", "One slide: bench size, BER-vs-theory, false-certificate rate 0, speed. Close on the one-line pitch."]],
      [12 * mm, 45 * mm, 123 * mm])
P("Judge questions we must answer cold", h2)
table([["Likely question", "Our answer (short)"],
       ["How do you know it's right on real data with no ground truth?", "Proof-of-Decode: the rebuilt waveform explains the recording to the noise floor; plus CRC/syndrome; plus real OTA set where standards are public."],
       ["Isn't blind LDPC impossible?", "For long codes, yes in general - we match catalogue codes by syndrome and reconstruct short codes (n &lt;= 1024) with the 2025 GJCE + sparsification method; we say exactly where the limit is."],
       ["What if the signal is encrypted?", "We still recover the full transmission recipe and frame structure; Bit-Lens flags the payload as high-entropy. Decryption is out of scope by design."],
       ["Why not just a deep-learning model?", "DL is one expert of three. DL cannot give a coding-layer proof; physics + algebra can. Conformal sets make the DL part honest."],
       ["Will it run on our machines?", "Offline installer, CPU-only, laptop-class; GNU Radio block drops into existing flowgraphs; SigMF in/out."],
       ["What happens with an unknown modulation?", "Open-set flag 'NOVEL', nearest known shown, analyst can teach it from ~5 examples."]],
      [60 * mm, 120 * mm])

# ======================= 9. RISKS =======================
P("9. Risks and cut-lines", h1)
table([["Risk", "Mitigation", "Cut-line if late"],
       ["Soft joint code/interleaver ID takes longer", "Hard-decision rank version lands first (P2) and already beats most of the field", "Ship hard-decision + catalogue; show soft as benchmark plot"],
       ["Open-set LDPC unstable", "Restrict to short codes; catalogue path always available", "Present as 'research mode' with honest limits"],
       ["Real OTA recordings noisy / scarce", "Start collecting in week 1; KiwiSDR is available 24x7", "Keep 5 best-quality files for demo"],
       ["HF equaliser convergence", "Start with CMA->LMS; test on Watterson from P3", "Limit to 'moderate' HF profile in claims"],
       ["GUI performance on big files", "pyqtgraph + decimated views + mmap from day 1", "Cap interactive view, full analysis via CLI"],
       ["Scope creep", "Section 4 is the whole USP list - nothing new after W7", "Drop USP 8 few-shot first, then USP 6 SIC"]],
      [50 * mm, 75 * mm, 55 * mm])

# ======================= 10. REFERENCES =======================
story.append(PageBreak())
P("10. Research references (2025-26 focus)", h1)
P("<i>Summarised from abstracts and publisher pages during the sweep; team members should read the full papers for the modules they own.</i>", small)
refs = [
    ("Blind Identification of Channel Codes: A Subspace-Coding Approach (arXiv 2601.15903, 2026)", "https://arxiv.org/abs/2601.15903"),
    ("Open-set blind recognition of non-binary LDPC codes (Digital Communications and Networks, 2025)", "https://www.sciencedirect.com/science/article/pii/S2352864825001506"),
    ("Blind Recognition Algorithm of Convolutional Code via CNN (Int. J. Intelligent Systems, 2025)", "https://onlinelibrary.wiley.com/doi/10.1155/int/3183819"),
    ("Blind Recognition of Convolutional Codes Based on ConvLSTM Temporal Feature Network (Sensors, 2025)", "https://doi.org/10.3390/s25041000"),
    ("Blind recognition of channel codes based on dual-branch feature fusion CNNs (Scientific Reports, 2026)", "https://www.nature.com/articles/s41598-026-35558-7"),
    ("Joint Blind Identification of Cyclic Codes and Synchronization Scramblers with soft information (IET Communications, 2026)", "https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/cmu2.70192"),
    ("Blind identification of an unknown interleaved convolutional code (arXiv 1501.03715) - parity-graph method", "https://arxiv.org/abs/1501.03715"),
    ("Blind Recognition of RS Codes Based on Galois Field Fourier Transform and Reliability Verification (IEEE, 2023)", "https://ieeexplore.ieee.org/document/10149421"),
    ("Blind Recognition of Frame Synchronization Based on Deep Learning (Sensors, 2024)", "https://doi.org/10.3390/s24206767"),
    ("IQFM: A Wireless Foundational Model for I/Q Streams in AI-Native 6G (arXiv 2506.06718, 2025)", "https://arxiv.org/abs/2506.06718"),
    ("EMind: A Foundation Model for Multi-task Electromagnetic Signals Understanding (arXiv 2508.18785, 2025)", "https://arxiv.org/abs/2508.18785"),
    ("Radio-FM: A Foundation Model for Radio Signal Representation Learning (arXiv 2608.05793, 2026)", "https://arxiv.org/abs/2608.05793"),
    ("RFPrompt: Prompt-Based Expert Adaptation of the Large Wireless Model for Modulation Classification (arXiv 2605.03279, 2026)", "https://arxiv.org/abs/2605.03279"),
    ("Geometry-Aware Contrastive Learning for Few-Shot Automatic Modulation Recognition (arXiv 2605.26600, 2026)", "https://arxiv.org/abs/2605.26600"),
    ("Wireless Foundation Models: State-of-the-Art and Open Challenges (arXiv 2609.04707, 2026)", "https://arxiv.org/abs/2609.04707"),
    ("DenoMAE: A Multimodal Autoencoder for Denoising Modulation Signals (arXiv 2501.11538, 2025)", "https://arxiv.org/abs/2501.11538"),
    ("Conformal Shield: conformal prediction sets for AMC (arXiv 2402.17450)", "https://arxiv.org/abs/2402.17450"),
    ("Open-DS: Open-Set Modulation Recognition based on Dictionary Similarity (IET Radar, Sonar &amp; Navigation, 2025)", "https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/rsn2.70007"),
    ("CSRD2025: A Large-Scale Synthetic Radio Dataset for Spectrum Sensing (arXiv 2508.19552, 2025)", "https://arxiv.org/abs/2508.19552"),
    ("ZoomSpec: Physics-Guided Coarse-to-Fine Framework for Wideband Spectrum Sensing (arXiv 2604.13568, 2026)", "https://arxiv.org/abs/2604.13568"),
    ("Blind Detection and Classification of RF Signals in Dense Multi-Emitter Environments (2026)", "https://journals.sagepub.com/doi/abs/10.1177/18758967251411395"),
    ("RadioLLM (arXiv 2501.17888, 2025) - reviewed; LLM route deliberately not adopted for the core", "https://arxiv.org/abs/2501.17888"),
    ("Scalable hierarchical protocol format inference (Empirical Software Engineering, 2026)", "https://link.springer.com/article/10.1007/s10664-026-10814-6"),
    ("Large Scale RF Signal Classification / Wideband Detection - TorchSig Sig53 &amp; WBSig53", "https://arxiv.org/abs/2211.10335"),
]
table([["#", "Paper", "Link"]] + [[str(i), t, f'<link href="{u}"><font color="#2a6f77"><u>{u}</u></font></link>'] for i, (t, u) in enumerate(refs, 1)],
      [8 * mm, 100 * mm, 72 * mm])

def footer(c, d):
    c.saveState(); c.setFont("Arial", 7.5); c.setFillColor(colors.grey)
    c.drawString(15 * mm, 9 * mm, "Project SANJAYA - winning plan for SIH 26147 (NTRO) - internal team document")
    c.drawRightString(195 * mm, 9 * mm, f"Page {d.page}"); c.restoreState()

doc = SimpleDocTemplate(r"D:\spacetech\winning plan 147.pdf", pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                        topMargin=14 * mm, bottomMargin=16 * mm, title="Project SANJAYA - Winning Plan")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("ok")
