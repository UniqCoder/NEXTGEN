from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY = colors.HexColor("#1b2a4a")
ACCENT = colors.HexColor("#2f6fb3")
LIGHT = colors.HexColor("#eef3fa")
WARN = colors.HexColor("#fff4e0")

ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Arial", fontSize=10, leading=14, spaceAfter=5)
small = ParagraphStyle("s", parent=body, fontSize=8.5, leading=11, spaceAfter=0)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=16, leading=20, textColor=NAVY, spaceBefore=10, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=12, leading=16, textColor=ACCENT, spaceBefore=8, spaceAfter=4)
title = ParagraphStyle("t", parent=body, fontName="Arial-Bold", fontSize=26, leading=32, textColor=NAVY, spaceAfter=10)
sub = ParagraphStyle("st", parent=body, fontSize=13, leading=18, textColor=ACCENT)
bullet = ParagraphStyle("bl", parent=body, leftIndent=14, bulletIndent=4, spaceAfter=2)

story = []
P = lambda t, s=body: story.append(Paragraph(t, s))
def B(items):
    for t in items:
        story.append(Paragraph(t, bullet, bulletText="\u2022"))
    story.append(Spacer(1, 4))

def table(rows, widths, head=True, bg=None):
    data = [[Paragraph(str(c), small) for c in r] for r in rows]
    if head:
        data[0] = [Paragraph(f'<font color="white"><b>{c}</b></font>', small) for c in rows[0]]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d6")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if head:
        st += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
        st += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]
    if bg:
        st += [("BACKGROUND", (0, 0), (-1, -1), bg)]
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 8))

def callout(text, bg=LIGHT):
    t = Table([[Paragraph(text, body)]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                           ("BOX", (0, 0), (-1, -1), 0.8, ACCENT),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)
    story.append(Spacer(1, 8))

W = 170 * mm

# ---------------- Cover ----------------
story.append(Spacer(1, 40 * mm))
P("Introduction to SIH 26147", title)
P("Automated model for analysis of .IQ and .wav files along with signal parameter extraction", sub)
story.append(Spacer(1, 10 * mm))
table([["Field", "Value"],
       ["Problem Statement ID", "SIH26147 (Smart India Hackathon 2026)"],
       ["Sponsoring organisation", "National Technical Research Organisation (NTRO), Government of India"],
       ["Theme / category", "Space Technology (as listed in the SIH 2026 problem-statement set)"],
       ["Domain in plain words", "Radio signal analysis / Digital Signal Processing (DSP) / Communications engineering"],
       ["One-line goal", "A GUI tool: load a recorded radio signal (.IQ or .wav) -&gt; automatically find out what it is "
        "-&gt; demodulate it -&gt; undo interleaving and error-correction -&gt; get clean bits -&gt; find header and payload."]],
      [45 * mm, 125 * mm])
story.append(Spacer(1, 10 * mm))
P("<i>Purpose of this document: understand the problem A to Z before writing a single line of code - who is asking, "
  "why, what every technical word means, what already exists, and exactly what we are expected to deliver.</i>")
story.append(PageBreak())

# ---------------- Contents ----------------
P("Contents", h1)
for i, s in enumerate([
    "The problem statement (verbatim)", "Who is the organisation - NTRO", "The story in plain language",
    "Background concepts you must know", "Word-by-word analysis of the statement",
    "The full processing chain (what our software actually does)", "Existing solutions and their gaps",
    "The expected solution - deliverables checklist", "Hidden difficulties, traps and ambiguities",
    "Questions to clarify / assumptions to state", "Suggested scope: MVP, strong, stretch",
    "Glossary", "Sources"], 1):
    P(f"{i}. {s}")
story.append(PageBreak())

# ---------------- 1. Verbatim ----------------
P("1. The problem statement (verbatim)", h1)
P("<b>Title:</b> Automated model for analysis of .IQ and .wav files along with signal parameter extraction")
P("<b>Background.</b> The raw data for analysis of signal collected off the air typically range from few Khz to Ghz bands. "
  "The analysis is being carried out manually to identify the signal parameters and the resultant data is then utilised "
  "for processing signals in the designated sensors. This data is often insufficient for fine grain analysis for parameter "
  "extraction such as modulation type, sampling rate, FEC, interleaving, etc. This creates a need for advanced data "
  "processing to extract the observation data.")
P("<b>Description.</b> The terrestrial signals received from various sources includes data in HF, VHF and UHF bands. The raw "
  "data collected in the form of .wav or .IQ format to retain the characteristics of wave form. The analysis of signals is "
  "primarily dependent on the basic characteristics of data points selected during recording of these signals. Since the "
  "data point are recorded from different sensors and different locations, the parameters may vary. Therefore, the data "
  "available for analysis is often insufficient to clearly identify fine details such as sampling rate, modulation type, "
  "interleaving, FEC etc. This limitation reduces the accuracy and confidence of interpretation and data analysis that "
  "require detailed information. The data saved as .IQ and .wav have different parameters and therefore they store the raw "
  "information in different format. These files have to be processed in different ways for signal analysis to extract "
  "signal parameters. The problem can be addressed using advanced models such as GNU Radio, python, C++ to enhance the "
  "parameter extraction capability and more information rich inputs. The spectral relationship from training data "
  "containing both .IQ and .wav formats can be utilised for identifying signal parameters and carry out deeper analysis. "
  "The expected solution should be able to demodulate signals.")
P("The GUI based model will have features to take .IQ or .wav file as input data and perform following tasks:")
B(["i. Identify signal parameters (Sampling frequency, Modulation, FEC, Interleaving). Additional features if feasible may be included.",
   "ii. Demodulate signals (FSK, QAM, PSK)",
   "iii. Carry out de-interleaving (Block, Convolution, Diagonal, Pseudo Random).",
   "iv. FEC (short-constrained convolution codes with Viterbi decoding, RS block codes, Concatenated codes, LDPC).",
   "v. Bit stream correlation."])
P("<b>Expected Solution.</b> The expected system should improve feature visibility of signals with the help of GUI, enable "
  "automated signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall "
  "(time-frequency domain), demodulate signals, carry out de-interleaving and error correction. The output can then be "
  "used to carry out correlation of bit stream for identification of header and payload.")

# ---------------- 2. NTRO ----------------
P("2. Who is the organisation - NTRO", h1)
P("The <b>National Technical Research Organisation (NTRO)</b> is India's technical intelligence agency. It was set up in 2004 "
  "(after the Kargil Review Committee recommendations) and works under the National Security Advisor / Prime Minister's Office. "
  "Its work covers technical intelligence gathering - including <b>signals intelligence (SIGINT)</b>, satellite and imagery "
  "intelligence, and cyber security (the National Critical Information Infrastructure Protection Centre, NCIIPC, sits under it).")
P("<b>Why this matters for us:</b>")
B(["When NTRO says <i>\"signals collected off the air\"</i> and <i>\"designated sensors\"</i>, think: receiving stations that "
   "record radio transmissions from HF to UHF, where the <b>transmitter is not cooperating</b> - nobody tells the analyst "
   "what modulation, baud rate, code or frame format was used. This is called <b>blind / non-cooperative signal analysis</b>.",
   "They will never share real recordings. Expect to build and demo with <b>synthetic signals we generate ourselves</b> "
   "(and public datasets such as RadioML), and to show that the pipeline is robust to noise, frequency offset and unknown parameters.",
   "Offline / air-gapped operation, speed, reliability and explainability (why the tool thinks it is QPSK) matter more "
   "than flashy cloud features. Everything should run locally.",
   "Judges will likely be DSP / communications engineers. Hand-wavy \"AI does it\" answers will not pass; correct signal "
   "processing fundamentals will."])

# ---------------- 3. Story ----------------
P("3. The story in plain language", h1)
P("Imagine an analyst at a monitoring station. A receiver has recorded a few seconds of an unknown radio transmission and "
  "saved it as a file. Today the analyst opens it in some tool, stares at the spectrum and waterfall, guesses the bandwidth, "
  "guesses the modulation, tries different baud rates by hand, and so on. This is <b>slow, expert-dependent and inconsistent</b>. "
  "And the recordings come from different sensors at different places, so sample rates, centre frequencies, gains and "
  "formats all differ.")
P("Even after demodulating, the bits are not readable, because real systems add two protective layers before transmitting:")
B(["<b>FEC (Forward Error Correction)</b> - extra redundant bits so the receiver can fix errors (convolutional, Reed-Solomon, LDPC...).",
   "<b>Interleaving</b> - shuffling bit order so a burst of noise becomes scattered single errors that FEC can fix."])
P("To get the actual message you must identify and undo both - without being told which ones were used. Finally, once you "
  "have clean bits, you look for <b>repeating patterns</b> (sync words, headers) across frames to separate header from payload. "
  "That is exactly the job the problem statement wants automated, behind a GUI.")
callout("<b>In one sentence:</b> Build a \"signal X-ray\" desktop tool - drop in a recording, and it shows the spectrum, "
        "waterfall and constellation, tells you the sample rate / symbol rate / modulation / FEC / interleaver, demodulates, "
        "de-interleaves, decodes, and highlights the frame header and payload in the final bit stream.")

# ---------------- 4. Concepts ----------------
story.append(PageBreak())
P("4. Background concepts you must know", h1)

P("4.1 Frequency bands mentioned", h2)
table([["Band", "Range", "Typical signals"],
       ["HF (High Frequency)", "3 - 30 MHz", "Long-range skywave comms, military HF modems (MIL-STD-188-110, STANAG 4285), "
        "RTTY / FSK, ham radio, ALE. Channel has fading, multipath, Doppler spread."],
       ["VHF (Very High Frequency)", "30 - 300 MHz", "FM broadcast, air-band AM, marine AIS (GMSK), APRS (AFSK), "
        "land-mobile radio, some satellite downlinks (NOAA APT at 137 MHz)."],
       ["UHF (Ultra High Frequency)", "300 MHz - 3 GHz", "DMR/P25/TETRA, GSM, LTE, Wi-Fi 2.4 GHz, satellite links, "
        "telemetry. Wider bandwidths, higher-order QAM/PSK."]],
      [38 * mm, 28 * mm, 104 * mm])
P("\"Few kHz to GHz\" in the statement refers to the range of signal frequencies/bandwidths collected - from narrow HF "
  "channels a few kHz wide up to GHz-band carriers.")

P("4.2 .wav vs .IQ - the two input formats", h2)
table([["Aspect", ".wav", ".IQ"],
       ["What it is", "Standard audio container (RIFF). Has a header with sample rate, bit depth, channel count.",
        "Usually a raw binary dump of complex baseband samples (I = in-phase, Q = quadrature). Often <b>no header at all</b>."],
       ["Real or complex", "Mono = real audio (e.g. output of an SSB/FM receiver, or an audio-frequency modem tone). "
        "Stereo is often I on left, Q on right (SDR# / HDSDR style).", "Complex: pairs of I,Q values interleaved I0 Q0 I1 Q1..."],
       ["Sample format", "Declared in header (8/16/24/32-bit int, 32-bit float).",
        "Must be guessed or given: int8 / uint8 (RTL-SDR), int16 (HackRF/USRP sc16), float32 (GNU Radio complex64). "
        "Byte order (endianness) also unknown."],
       ["Sample rate", "Read directly from header.", "Unknown unless provided in filename, sidecar file (e.g. SigMF .sigmf-meta) or user input."],
       ["Implication", "Easy to load; signal may be real-valued and need Hilbert transform / down-conversion.",
        "Need a <b>format auto-detector</b> (try dtypes, check statistics / spectrum sanity) plus manual override."]],
      [28 * mm, 66 * mm, 76 * mm])
callout("<b>Key insight:</b> the statement says the two formats \"store the raw information in different format\" and "
        "\"have to be processed in different ways\". This is literally asking for a smart <b>ingestion layer</b> that "
        "normalises both into one internal representation: complex baseband samples + sample rate + centre frequency.")

P("4.3 Sampling frequency vs symbol rate", h2)
P("<b>Sampling frequency (Fs)</b> = how many samples per second the recorder captured (e.g. 48 kHz audio, 2.4 MS/s SDR). "
  "<b>Symbol rate / baud rate (Rs)</b> = how many symbols per second the transmitter sends (e.g. 2400 baud). The tool must "
  "estimate Rs blindly (cyclostationary analysis, squaring/envelope spectrum lines, zero-crossing statistics) and then "
  "resample so that there is an integer number of samples per symbol. When the problem statement says \"identify sampling "
  "frequency\" it very likely means <b>both</b>: the file's Fs (if unknown) and the signal's symbol rate.")

P("4.4 Modulation types to demodulate", h2)
table([["Family", "How information is carried", "Examples", "Tell-tale sign"],
       ["FSK", "Carrier frequency switches between M tones", "2-FSK, 4-FSK, GFSK, GMSK, MSK, AFSK", "Several peaks in spectrum; "
        "constant envelope; instantaneous frequency shows discrete levels"],
       ["PSK", "Carrier phase takes M values", "BPSK, QPSK, OQPSK, 8PSK, DBPSK/DQPSK", "Constellation points on a circle; "
        "raising signal to M-th power creates a spectral line at M x carrier offset"],
       ["QAM", "Both amplitude and phase vary (grid)", "16-QAM, 32-QAM, 64-QAM, 256-QAM", "Square grid constellation; "
        "non-constant envelope; higher-order cumulant values"]],
      [18 * mm, 42 * mm, 45 * mm, 65 * mm])
P("<b>Automatic Modulation Classification (AMC)</b> = figuring out the modulation automatically. Two schools: "
  "(a) feature/likelihood-based (higher-order cumulants C40/C42, spectral lines, envelope variance) - explainable; "
  "(b) deep-learning (CNN / ResNet / Transformer on raw IQ or constellation images, e.g. trained on RadioML). "
  "A hybrid is the strongest pitch.")

P("4.5 Demodulation chain (what must happen before bits appear)", h2)
B(["<b>Channel detection</b>: find where in the spectrum the signal sits and its bandwidth.",
   "<b>Down-conversion and filtering</b>: shift signal to 0 Hz, low-pass filter out neighbours.",
   "<b>Coarse frequency correction</b>: remove carrier offset (FFT of M-th power, etc.).",
   "<b>Symbol timing recovery</b>: find the right instant to sample each symbol (Gardner, Mueller-Muller, polyphase clock sync).",
   "<b>Fine carrier / phase recovery</b>: Costas loop / decision-directed PLL.",
   "<b>Equalisation</b> (especially HF): undo multipath (CMA, LMS).",
   "<b>Symbol decision and mapping</b>: symbols -&gt; bits (Gray coding, differential decoding). <b>Phase ambiguity</b> "
   "(e.g. QPSK can lock at 0/90/180/270 deg) must be resolved later using sync words or FEC."])

P("4.6 Interleaving types", h2)
table([["Type", "How it works", "How to blindly identify"],
       ["Block", "Write bits row-by-row into an R x C matrix, read column-by-column.",
        "Try candidate sizes; reshape bit stream into matrix and compute GF(2) rank - correct period drops rank "
        "(because FEC redundancy becomes linearly dependent)."],
       ["Convolutional", "Bits go through B branches with increasing delays (0, J, 2J ...). Used in DVB, CCSDS.",
        "Estimate branch count B and delay J by rank / correlation analysis over candidate (B, J)."],
       ["Diagonal", "Bits are written/read along diagonals of a matrix (spreads adjacent bits across rows and columns).",
        "Similar matrix-rank search, with diagonal read-out permutations."],
       ["Pseudo-random", "Permutation defined by a PN/LFSR generator or a lookup table (e.g. turbo code interleavers, 3GPP).",
        "Hardest: generally needs knowledge of the generator/seed, or known-standard library matching. Blindly, only "
        "period can often be recovered."]],
      [26 * mm, 62 * mm, 82 * mm])

P("4.7 FEC (Forward Error Correction) types", h2)
table([["Code", "Idea", "Decoder", "Real-world use"],
       ["Convolutional (short constraint length, e.g. K = 3..9)", "Each output bit = XOR of current and previous K-1 input bits via "
        "generator polynomials (e.g. K=7, 171/133 octal, rate 1/2).", "Viterbi algorithm (maximum-likelihood trellis search).",
        "NASA/CCSDS, GSM, Wi-Fi, DVB-S, many military modems"],
       ["Reed-Solomon (RS) block codes", "Symbols over GF(2^8); RS(n,k) corrects (n-k)/2 byte errors, e.g. RS(255,223).",
        "Berlekamp-Massey + Chien search + Forney.", "CD/DVD, QR codes, CCSDS, DVB"],
       ["Concatenated", "Outer RS + interleaver + inner convolutional (classic CCSDS/DVB-S chain).",
        "Viterbi -&gt; de-interleave -&gt; RS.", "Deep space, satellite TV"],
       ["LDPC", "Large sparse parity-check matrix H; near-Shannon-limit performance.",
        "Belief propagation / min-sum iterative decoding.", "DVB-S2, 5G NR, Wi-Fi 802.11n/ac, CCSDS"]],
      [34 * mm, 58 * mm, 38 * mm, 40 * mm])
P("<b>Blind FEC recognition</b> is its own research topic: estimate code rate and constraint length by rank analysis of "
  "bit-stream matrices, recover generator polynomials via Gaussian elimination / Walsh-Hadamard, or - more practically - "
  "<b>try a library of known standard codes</b> and keep the one whose decoded output has the lowest syndrome weight / "
  "highest structure.")

P("4.8 Bit stream correlation, header and payload", h2)
P("Once bits are clean, frames usually start with a fixed <b>sync word / preamble</b> (e.g. CCSDS ASM 0x1ACFFC1D, "
  "Barker codes, alternating 1010 preambles). Autocorrelation of the bit stream reveals the <b>frame length</b> (peaks "
  "repeat every frame). Aligning frames and checking which bit positions are <b>constant or slowly-changing</b> "
  "(counters, IDs) vs <b>random-looking</b> separates <b>header</b> from <b>payload</b>. Cross-correlation against a "
  "library of known sync words can also identify the standard.")

P("4.9 Visualisations named in the statement", h2)
B(["<b>Spectrum / PSD</b>: power vs frequency (FFT, Welch). Shows bandwidth, centre, SNR.",
   "<b>Waterfall / spectrogram</b>: frequency vs time, colour = power. Shows bursts, hopping, FSK tones.",
   "<b>Constellation plot</b>: I vs Q scatter of symbols after sync. Instantly reveals BPSK / QPSK / 16-QAM etc.",
   "Useful extras: eye diagram, instantaneous frequency/phase plot, cyclic spectrum, bit-map view of frames."])

# ---------------- 5. Word by word ----------------
story.append(PageBreak())
P("5. Word-by-word analysis of the statement", h1)
P("Every phrase that carries a requirement, a hint or a trap:")
table([["Phrase in statement", "What it really means", "Implication for our solution"],
       ["\"Automated model\"", "The core ask is <b>automation</b> - replace manual analyst steps.",
        "One-click \"Analyse\" pipeline with sensible defaults; manual override for experts."],
       ["\".IQ and .wav files\"", "Two input formats, both recordings (offline), not live streaming.",
        "Strong file loader; live SDR input is only a bonus."],
       ["\"signal parameter extraction\"", "Estimate numbers: Fs, centre freq, bandwidth, baud rate, SNR, modulation order...",
        "Show a parameter report panel with confidence values."],
       ["\"collected off the air\"", "Real, noisy, non-cooperative signals.",
        "Must be robust to noise, offset, fading - test with impairments."],
       ["\"few Khz to Ghz bands\"", "Huge range of bandwidths and carriers.",
        "Algorithms must be rate-agnostic (normalise to samples/symbol)."],
       ["\"analysis is being carried out manually\"", "Current state = human experts with generic tools.",
        "Our value proposition: speed + consistency + deeper parameters."],
       ["\"designated sensors\"", "Results feed configuration of operational receivers/decoders.",
        "Export results (JSON/report) that another system can consume."],
       ["\"insufficient for fine grain analysis\"", "Current tools stop at spectrum; they don't get FEC / interleaving.",
        "Our differentiator is going <b>below the physical layer</b> into coding layers."],
       ["\"terrestrial signals ... HF, VHF, UHF\"", "Not satellite-only (despite Space Technology theme). HF implies fading/multipath.",
        "Include equaliser; test HF-like channels (Watterson model)."],
       ["\"retain the characteristics of wave form\"", "Raw recordings, not decoded data.", "We start from samples, not bits."],
       ["\"data points selected during recording\"", "Recording settings (Fs, centre, gain) chosen by operator vary.",
        "Cannot assume fixed Fs or centre; auto-estimate and let user input metadata."],
       ["\"different sensors and different locations\"", "Heterogeneous data: different dtypes, gains, IQ imbalance, DC offset.",
        "Pre-processing: DC removal, IQ imbalance correction, normalisation."],
       ["\"accuracy and confidence\"", "They care about how sure the tool is.",
        "Report confidence scores / probabilities, not just a label."],
       ["\"processed in different ways\"", "Real audio (.wav) vs complex baseband (.IQ).",
        "Separate ingestion paths, common downstream pipeline."],
       ["\"GNU Radio, python, C++\"", "Suggested tech stack (not mandatory).",
        "Python + NumPy/SciPy for speed of development; GNU Radio blocks or C++ for heavy parts (Viterbi, LDPC)."],
       ["\"more information rich inputs\"", "Enrich raw data with derived features / metadata.",
        "Produce feature vectors + annotated SigMF-like output."],
       ["\"spectral relationship from training data\"", "Hint at <b>machine learning</b> trained on spectral features from both formats.",
        "ML modulation classifier (and possibly FEC/interleaver classifier) trained on synthetic + RadioML data."],
       ["\"deeper analysis\"", "Beyond classification: coding layers, framing.", "Full chain down to header/payload."],
       ["\"should be able to demodulate\"", "Explicit hard requirement - not just classify.",
        "Working demodulators for FSK, PSK, QAM producing bits."],
       ["\"GUI based model\"", "Must be a usable graphical tool.", "Desktop GUI (PyQt/PySide + pyqtgraph) or local web UI."],
       ["\"Additional features if feasible\"", "Room to impress.", "SNR, bandwidth, burst detection, multi-signal, report export."],
       ["\"short-constrained convolution codes\"", "Convolutional codes with <b>short constraint length</b> (K about 3-9).",
        "Viterbi is feasible (2^(K-1) states); build a library of common polynomials."],
       ["\"Concatenated codes\"", "Outer + inner codes chained (RS + convolutional).", "Pipeline must allow chaining decoders with an interleaver between."],
       ["\"LDPC\"", "Modern iterative codes; needs parity-check matrix.",
        "Support standard matrices (DVB-S2, CCSDS, 5G/Wi-Fi) - fully blind LDPC recovery is research-level."],
       ["\"Bit stream correlation\"", "Find repeating patterns in decoded bits.", "Autocorrelation, sync-word search, frame alignment view."],
       ["\"improve feature visibility\"", "Visual clarity for analysts.", "Clean interactive plots, zoom, markers, overlays."],
       ["\"identification of header and payload\"", "The final output: frame structure.", "Colour-coded frame map: constant fields vs varying fields."]],
      [40 * mm, 60 * mm, 70 * mm])

# ---------------- 6. Pipeline ----------------
P("6. The full processing chain (what our software actually does)", h1)
steps = [("1. Ingest", ".wav / .IQ loader, dtype + endianness detection, metadata, DC & IQ imbalance fix"),
         ("2. Visualise", "PSD, waterfall, time plot - interactive"),
         ("3. Detect", "Find signal(s), centre frequency, bandwidth, SNR, bursts"),
         ("4. Isolate", "Frequency shift to baseband, filter, decimate"),
         ("5. Estimate", "Symbol rate, carrier offset, roll-off"),
         ("6. Classify", "Modulation type & order (cumulants + ML) with confidence"),
         ("7. Demodulate", "Timing recovery, carrier recovery, equaliser, constellation, symbols -&gt; bits"),
         ("8. De-interleave", "Detect interleaver type & size (rank analysis), undo it"),
         ("9. Decode FEC", "Identify code (rate, K, polynomials / RS params / LDPC matrix), Viterbi / RS / BP decode"),
         ("10. Correlate", "Autocorrelation, sync word search, frame length, header vs payload map"),
         ("11. Report", "Export parameters + bits + plots (JSON / PDF / SigMF)")]
table([["Stage", "What happens"]] + [[a, b] for a, b in steps], [35 * mm, 135 * mm])
callout("<b>Note the order:</b> on the transmit side it is <i>bits -&gt; FEC encode -&gt; interleave -&gt; modulate</i>. "
        "So the receiver must undo in reverse: <i>demodulate -&gt; de-interleave -&gt; FEC decode</i>. Interleaver and code "
        "detection are coupled - the rank-based methods find them together.")

# ---------------- 7. Existing ----------------
story.append(PageBreak())
P("7. Existing solutions and their gaps", h1)
P("7.1 How it is done today", h2)
P("As the statement itself says, analysts do it <b>manually</b>: look at spectrum/waterfall, measure bandwidth and baud by "
  "eye, try demodulators, and rely on experience and signal databases. Deep coding-layer analysis (FEC, interleaving) is "
  "done rarely, slowly, or with expensive specialised tools.")
P("7.2 Open-source tools", h2)
table([["Tool", "What it does well", "Gap vs. our problem"],
       ["GNU Radio (+ gr-inspector)", "DSP framework: blocks for demod, sync, FEC (gr-fec: conv, LDPC, polar). gr-inspector does basic signal detection/OFDM estimation.",
        "A toolkit, not an automated analyser. You must already know the signal to build a flowgraph."],
       ["Inspectrum", "Great offline spectrogram viewer; manual symbol-rate cursors; extracts symbols.", "Fully manual; no classification, FEC or interleaving."],
       ["Universal Radio Hacker (URH)", "Demodulates simple ASK/FSK/PSK, protocol reverse engineering, bit-level diff/labels.",
        "Aimed at simple IoT protocols; no QAM, no blind FEC/interleaver identification."],
       ["SigDigger / Suscan", "Real-time and file-based signal inspector; baud estimation, PSK/FSK/ASK inspectors, constellation.",
        "No automatic modulation classification pipeline, no coding layer."],
       ["SDR#, GQRX, SDR++, HDSDR", "Receivers with waterfall, recording to wav/IQ.", "Listening/recording, not analysis."],
       ["Baudline, Audacity", "Spectral analysis of audio/wav.", "Visual only."],
       ["fldigi, multimon-ng, dsd", "Decoders for specific known modes.", "Work only if you already know the exact standard."],
       ["RadioML datasets + research code", "Deep-learning AMC benchmarks (O'Shea et al.).",
        "Classification only; synthetic; no end-to-end demod/decoding or GUI."]],
      [38 * mm, 70 * mm, 62 * mm])
P("7.3 Commercial / government-grade tools", h2)
table([["Tool (vendor)", "Notes"],
       ["go2MONITOR / go2DECODE (PROCITEC)", "Automatic classification and decoding of hundreds of HF/VHF/UHF modes - the closest real-world equivalent. Expensive, closed."],
       ["W-CODE / W-SPECTRA (WAVECOM)", "Signal analysis & decoding of many HF/V/UHF and satellite modes; blind analysis tools."],
       ["CA100 / signal analysis suites (Rohde & Schwarz)", "Professional COMINT/signal analysis with modulation recognition, bitstream analysis."],
       ["Code3 / Code300 (Hoka Electronic)", "Decoder for large number of data modes, HF-focused."],
       ["MATLAB (Signal Analyzer, Comms / DL Toolboxes)", "Excellent for prototyping AMC and FEC; licence-bound, not a turnkey analyst tool."],
       ["Keysight 89600 VSA", "Lab-grade vector signal analysis, great constellation/EVM - needs known signal parameters."]],
      [60 * mm, 110 * mm])
P("7.4 Gaps our solution targets", h2)
B(["<b>End-to-end automation</b>: existing free tools cover one step each; nothing goes from raw file to header/payload automatically.",
   "<b>Blind coding-layer analysis</b>: interleaver and FEC identification is almost absent in open tools.",
   "<b>Heterogeneous input handling</b>: no tool auto-detects raw IQ dtype/format robustly.",
   "<b>Explainability + confidence</b>: ML classifiers give labels without showing evidence; analysts need both.",
   "<b>Sovereign, offline, low-cost</b>: commercial suites are expensive, foreign, and closed - an indigenous open tool is attractive to NTRO (Atmanirbhar angle)."])

# ---------------- 8. Expected solution ----------------
P("8. The expected solution - deliverables checklist", h1)
table([["#", "Requirement", "Concrete deliverable", "Must / Nice"],
       ["0", "GUI accepting .IQ or .wav", "Desktop app: file open, format/metadata dialog, analysis tabs", "Must"],
       ["i", "Identify parameters: sampling frequency, modulation, FEC, interleaving (+ extras)",
        "Parameter panel: Fs, centre, bandwidth, SNR, symbol rate, modulation + confidence, interleaver type/size, FEC type/params", "Must"],
       ["ii", "Demodulate FSK, QAM, PSK", "Working demods: 2/4-FSK, BPSK/QPSK/8PSK, 16/64-QAM -&gt; bit stream", "Must"],
       ["iii", "De-interleave: Block, Convolutional, Diagonal, Pseudo-random", "Detection + de-interleaver for each; PN via known seeds/library", "Must (PN partial)"],
       ["iv", "FEC: conv + Viterbi, RS, concatenated, LDPC", "Decoders for each + blind identification of common standard codes", "Must"],
       ["v", "Bit stream correlation", "Autocorrelation plot, sync word finder, frame alignment, header/payload map", "Must"],
       ["E1", "Spectral features: sampling frequency, constellation, waterfall", "Interactive PSD, spectrogram, constellation, eye diagram", "Must"],
       ["E2", "Improve feature visibility", "Clean, responsive visual design; zoom/markers", "Must"],
       ["+", "Additional features", "Multi-signal detection, burst detection, report export, batch mode, standard recognition", "Nice"]],
      [8 * mm, 50 * mm, 90 * mm, 22 * mm])

# ---------------- 9. Difficulties ----------------
story.append(PageBreak())
P("9. Hidden difficulties, traps and ambiguities", h1)
B(["<b>No real data from NTRO.</b> We must build a <b>signal generator</b> (synthetic test bench) that creates files with "
   "known modulation + FEC + interleaver + frame structure, then prove our tool recovers them. This generator is also our demo "
   "and our ML training source.",
   "<b>Raw .IQ has no header.</b> Wrong dtype guess = garbage. Needs auto-detection + user override.",
   "<b>Real vs complex .wav.</b> Audio-demodulated signals (e.g. AFSK after an FM receiver) are real; stereo wavs are often IQ.",
   "<b>Phase ambiguity</b> after PSK/QAM demod (rotations, bit inversions) breaks FEC detection unless every rotation is tried.",
   "<b>Differential encoding, scramblers and Gray mapping</b> sit between demod and FEC in real systems - not mentioned in "
   "the statement, but they will appear. Scrambler (LFSR) detection is a good \"additional feature\".",
   "<b>Blind LDPC and pseudo-random interleaver identification</b> are open research problems. Honest approach: detect from a "
   "library of standards (DVB-S2, CCSDS, 802.11, 5G) and say so.",
   "<b>Coupling:</b> you cannot decode FEC before de-interleaving, and you cannot easily detect the interleaver without "
   "exploiting FEC redundancy. Rank-based joint search is the standard approach.",
   "<b>HF channel</b>: fading and multipath make constellations smeared; need equalisation and adequate SNR.",
   "<b>Computation</b>: brute-force searches (interleaver sizes x code params x rotations) explode - need smart pruning and vectorised / C++ code.",
   "<b>\"Model\" wording</b>: judges may expect some ML; but ML alone cannot do FEC decoding. Pitch: ML where it helps "
   "(classification), deterministic DSP where correctness matters."])

# ---------------- 10. Questions ----------------
P("10. Questions to clarify / assumptions to state", h1)
P("Ask these to the SPOC/mentor if possible; otherwise write them as explicit assumptions in the submission:")
B(["Will sample data be provided? If not, can we assume synthetic + public datasets (RadioML 2016/2018, SigMF recordings)?",
   "For .IQ files, is metadata (Fs, centre frequency, dtype) available, or must it be fully blind?",
   "One signal per file, or multiple simultaneous signals in the captured band?",
   "Continuous signals or bursty/TDMA?",
   "Are the target signals based on known standards (STANAG, MIL-STD, CCSDS, DVB) or proprietary?",
   "Is 'sampling frequency' meant as file sample rate, symbol rate, or both?",
   "Is OFDM / multicarrier in scope (not listed, but common in UHF)?",
   "Preferred platform: Windows/Linux desktop, offline? Any restrictions on open-source licences?",
   "Expected performance: minimum SNR, max file size, time-to-result?"])

# ---------------- 11. Scope ----------------
P("11. Suggested scope: MVP, strong, stretch", h1)
table([["Tier", "Contents"],
       ["MVP (must work in demo)", "Loader for wav + raw IQ (int8/int16/float32); PSD, waterfall, constellation; SNR/bandwidth/centre/symbol-rate "
        "estimation; AMC for BPSK/QPSK/8PSK/16QAM/64QAM/2FSK/4FSK; demodulators; block + convolutional interleavers; "
        "conv code K=7 r=1/2 Viterbi + RS(255,223); concatenated chain; bit autocorrelation + sync word finder; synthetic signal generator."],
       ["Strong", "Blind block-interleaver size + conv-code rate/K detection via GF(2) rank; diagonal interleaver; LDPC decoding for standard "
        "matrices; ML classifier with confidence + cumulant explanation; header/payload colour map; JSON/PDF report export."],
       ["Stretch", "Pseudo-random interleaver via LFSR seed search; scrambler detection; multi-signal channelisation; HF equaliser; "
        "standard recognition (e.g. 'looks like STANAG 4285'); GNU Radio OOT block packaging; live SDR input."]],
      [35 * mm, 135 * mm])
P("<b>Candidate tech stack:</b> Python 3 + NumPy/SciPy for DSP, PyTorch for AMC model, PySide6/PyQt + pyqtgraph for a "
  "fast GUI, commpy/galois/pyldpc or GNU Radio gr-fec for coding (or our own implementations), Numba/C++ for hot loops "
  "(Viterbi, LDPC, rank search), SigMF for metadata.")

# ---------------- 12. Glossary ----------------
P("12. Glossary", h1)
table([["Term", "Meaning"],
       ["AMC", "Automatic Modulation Classification"],
       ["ASM / sync word", "Attached Sync Marker - fixed bit pattern at frame start"],
       ["Baud / symbol rate", "Symbols transmitted per second"],
       ["BER", "Bit Error Rate"],
       ["Constellation", "I/Q scatter plot of received symbols"],
       ["Constraint length (K)", "Memory of a convolutional encoder + 1; 'short' K means few trellis states"],
       ["Costas loop", "Carrier phase recovery loop for PSK"],
       ["Cumulants (C40, C42...)", "Higher-order statistics that differ per modulation - classic AMC features"],
       ["FEC", "Forward Error Correction - redundancy added to fix errors without retransmission"],
       ["GF(2)", "Binary field (0/1 with XOR); rank over GF(2) is used for blind code/interleaver detection"],
       ["I/Q", "In-phase / Quadrature - the two components of a complex baseband signal"],
       ["Interleaver", "Permutation of bits to spread burst errors"],
       ["LDPC", "Low-Density Parity-Check code"],
       ["PSD", "Power Spectral Density"],
       ["RS", "Reed-Solomon code"],
       ["SIGINT / COMINT", "Signals intelligence / Communications intelligence"],
       ["SigMF", "Signal Metadata Format - open standard for describing IQ recordings"],
       ["SNR", "Signal-to-Noise Ratio"],
       ["Viterbi", "Maximum-likelihood decoder for convolutional codes"],
       ["Waterfall", "Spectrogram: frequency vs time with colour-coded power"]],
      [42 * mm, 128 * mm])

# ---------------- 13. Sources ----------------
P("13. Sources", h1)
B(["Problem statement text as provided (SIH 2026, PS ID 26147).",
   "SIH 2026 problem statement listings identifying sponsor NTRO and theme Space Technology: "
   "scribd.com/document/1078552603/SIH-2026-Problem-Statements ; sih-explorer.amanuniyal47.workers.dev/explore ; "
   "kaggle.com/datasets/riteshmaurya86/sih-2026-problem-statements-dataset",
   "Background on NTRO, DSP, coding and tools: general domain knowledge (public information). Verify sponsor details "
   "on the official sih.gov.in portal before submission."])

def footer(c, d):
    c.saveState()
    c.setFont("Arial", 8)
    c.setFillColor(colors.grey)
    c.drawString(20 * mm, 10 * mm, "Introduction to SIH 26147 - NTRO - Signal analysis of .IQ / .wav")
    c.drawRightString(190 * mm, 10 * mm, f"Page {d.page}")
    c.restoreState()

doc = SimpleDocTemplate(r"D:\spacetech\introduction to 147.pdf", pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
                        title="Introduction to SIH 26147", author="Team")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("ok")
