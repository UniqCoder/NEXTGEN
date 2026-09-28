# -*- coding: utf-8 -*-
"""SIH 2026 PS 26147 (NTRO) - SANJAYA - complete PPT-source content document.

Every technical claim traces to the repository's own evidence: PRD.md v2.4, HANDOFF.md (28 Sep 2026,
night), CURRENT_STATE.md (this session), the engine test suite (engine/scripts/check.py), and
`introduction to 147.pdf` / `147details.pdf` for the verbatim problem statement and the existing-tools
survey. External context (news, policy documents, market context) is cited by URL where used.

Run from inside _build/:  python make_content.py  ->  ../content.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY = colors.HexColor("#14213d")
ACCENT = colors.HexColor("#c8553d")
TEAL = colors.HexColor("#2a6f77")
LIGHT = colors.HexColor("#f4f1ea")
GREEN_BG = colors.HexColor("#dcefe9")
GOLD_BG = colors.HexColor("#fbeee9")
GREY = colors.HexColor("#c9c2b2")
INK = colors.HexColor("#1a1a2e")

body = ParagraphStyle("b", fontName="Arial", fontSize=9.0, leading=12.6, textColor=INK)
small = ParagraphStyle("s", fontName="Arial", fontSize=7.8, leading=10.4, textColor=INK)
tiny = ParagraphStyle("t", fontName="Arial", fontSize=7.0, leading=9.0, textColor=INK)
kicker = ParagraphStyle("k", parent=body, fontName="Arial-Bold", fontSize=9.5, textColor=ACCENT)
h_slide = ParagraphStyle("hs", parent=body, fontName="Arial-Bold", fontSize=16, leading=20, textColor=NAVY)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=10.5, leading=13.5, textColor=ACCENT)
sub = ParagraphStyle("sub", parent=body, fontSize=10.2, leading=14, textColor=TEAL)
bullet = ParagraphStyle("bl", parent=body, leftIndent=11, bulletIndent=2, spaceAfter=2)
title_big = ParagraphStyle("ti", fontName="Arial-Bold", fontSize=32, leading=38, textColor=NAVY)
W = 180 * mm

story = []


def P(t, s=body):
    story.append(Paragraph(t, s))


def B(items, s=bullet):
    for t in items:
        story.append(Paragraph(t, s, bulletText="\u2022"))
    story.append(Spacer(1, 3))


def band(label, width=34 * mm, bg=NAVY):
    t = Table([[Paragraph(f'<font color="white"><b>{label}</b></font>',
                          ParagraphStyle("band", parent=small, fontSize=8.2))]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    return t


def section(num_label, part, heading, one_line=None):
    story.append(Spacer(1, 4))
    hdr = Table([[band(num_label), band(part, width=44 * mm, bg=ACCENT)],
                 [Paragraph(heading, h_slide), ""],
                 [Paragraph(one_line, sub) if one_line else "", ""]],
                colWidths=[34 * mm, W - 34 * mm])
    hdr.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("SPAN", (0, 2), (1, 2)),
                             ("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    story.append(hdr)
    story.append(HRFlowable(width="100%", thickness=1.1, color=NAVY, spaceAfter=5))


def table(rows, widths, head=True, zebra=True, style=small, extra=None):
    data = [[Paragraph(str(c), style) for c in r] for r in rows]
    if head:
        data[0] = [Paragraph(f'<font color="white"><b>{c}</b></font>', style) for c in rows[0]]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
          ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        st.append(("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, LIGHT]))
    t.setStyle(TableStyle(st + (extra or [])))
    story.append(t)
    story.append(Spacer(1, 6))


def callout(text, bg=LIGHT, border=ACCENT):
    t = Table([[Paragraph(text, body)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)
    story.append(Spacer(1, 6))


def statrow(stats):
    boxes = []
    cw = W / len(stats)
    for bigv, lab in stats:
        inner = Table(
            [[Paragraph(f'<font color="#c8553d"><b>{bigv}</b></font>',
                        ParagraphStyle("sv", parent=body, fontSize=14, leading=17, fontName="Arial-Bold"))],
             [Paragraph(lab, tiny)]], colWidths=[cw - 8])
        inner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD_BG),
                                   ("BOX", (0, 0), (-1, -1), 0.6, ACCENT),
                                   ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
        boxes.append(inner)
    t = Table([boxes], colWidths=[cw] * len(stats))
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    story.append(Spacer(1, 6))


# ============================================================ COVER
story.append(Spacer(1, 16 * mm))
P('<font color="#c8553d">SIH 2026 \u00b7 PS 26147 \u00b7 SPONSOR NTRO \u00b7 THEME SPACE TECHNOLOGY \u00b7 CATEGORY SOFTWARE</font>',
  ParagraphStyle("k", parent=body, fontSize=10.5, fontName="Arial-Bold"))
P("Project SANJAYA", title_big)
P("The signal X-ray: automated .IQ / .wav analysis that proves its own answers", sub)
story.append(Spacer(1, 4 * mm))
callout("<b>What this document is.</b> Complete, presentation-ready source content for the SIH pitch deck: "
        "the problem, our solution, why we stand out against the tools analysts actually use today, every USP and "
        "feature with its build status, the one clause of the PS still being hardened, measured impact and "
        "benefits, and the references behind every technical claim. Every number below is either measured in this "
        "repository (engine/scripts/check.py, PRD.md \u00a716) or cited to an external source.", bg=LIGHT, border=NAVY)
story.append(PageBreak())

# ============================================================ 1. THE PROBLEM
section("1", "THE PROBLEM", "An intercepted signal, and no one to tell you what it is",
        "PS 26147, verbatim, plus the real-world scale of the problem it names")
P("<b>The problem statement, in NTRO's own words:</b>", h2)
B([
    "\u201cThe raw data for analysis of signal collected off the air typically range from few KHz to GHz bands. "
    "The analysis is being carried out manually to identify the signal parameters&nbsp;\u2026 This data is often "
    "insufficient for fine grain analysis for parameter extraction such as modulation type, sampling rate, FEC, "
    "interleaving, etc.&nbsp;\u2026 Since the data points are recorded from different sensors and different "
    "locations, the parameters may vary. Therefore, the data available for analysis is often insufficient to "
    "clearly identify fine details&nbsp;\u2026 This limitation reduces the accuracy and confidence of interpretation.\u201d",
])
P("<b>What that means on the ground:</b> when a SIGINT listening post intercepts an unknown transmission, the "
  "transmitter is not cooperating \u2014 no metadata, no manual, no header. A traditional receiver needs an "
  "operator to set the carrier, filter and baud rate by hand before anything useful comes out; get any one of "
  "them wrong and the output is noise. Today this is done by an expert staring at a spectrogram, guessing, and "
  "iterating \u2014 slow, inconsistent, and it does not scale to the volume of captures a modern monitoring "
  "programme produces.", body)
P("<b>Why this is a live, growing problem, not a hypothetical one:</b>", h2)
B([
    "India's Department of Telecommunications is rolling out nationwide AI-driven spectrum monitoring and "
    "analytics in phases through 2026-2035, explicitly to keep pace with denser, more contested RF use "
    "(<a href=\"https://nicf.gov.in/wp-content/uploads/2026/01/Policy-and-Regulatory-Frameworks-for-Emerging-Technologies-in-Spectrum-Management-1.pdf\">"
    "NICF, Policy and Regulatory Frameworks for Emerging Technologies in Spectrum Management, 2026</a>).",
    "India's Space Based Surveillance programme has been expedited, with its first satellites due in 2026 and "
    "full deployment by 2029 \u2014 more sensors, in more places, means more heterogeneous captures needing the "
    "exact kind of blind, sensor-agnostic analysis this PS asks for "
    "(<a href=\"https://en.wikipedia.org/wiki/Space_Based_Surveillance_project_(India)\">Space Based Surveillance "
    "project (India), Wikipedia</a>).",
    "Commercial-grade blind signal analysis exists (go2MONITOR, W-CODE, Rohde &amp; Schwarz COMINT suites, "
    "India's own Shoghi Communications HF/VHF/UHF monitoring systems) but is closed, foreign-dependent in most "
    "cases, and expensive \u2014 exactly the gap an indigenous, offline tool is meant to close "
    "(<a href=\"https://www.shoghicom.com/all-products/hf-vhfuhf-monitoring-system\">Shoghi Communications, HF/VHF/UHF "
    "Monitoring System</a>).",
])
statrow([("3 kHz \u2013 3 GHz", "HF/VHF/UHF span the PS asks to cover, one pipeline"),
         ("4", "unknowns before any bit is readable: Fs, modulation, FEC, interleaving"),
         ("2026\u20132035", "India's own phased spectrum-monitoring modernisation window")])
story.append(PageBreak())

# ============================================================ 2. OUR SOLUTION
section("2", "OUR SOLUTION", "Analysis by synthesis: decode, then prove the decode is right",
        "The one thing every other blind-analysis tool skips \u2014 checking its own answer")
P("SANJAYA is an offline, air-gap-ready desktop tool. Drop in a .wav, raw .IQ, or SigMF recording; it identifies "
  "the sampling frequency, modulation, FEC, interleaving and frame structure with no metadata and no prior "
  "knowledge, demodulates and decodes the signal, and \u2014 uniquely \u2014 <b>proves</b> that its answer actually "
  "explains the recording before it ever reports it as a result.", body)
P("<b>The method, in five steps:</b>", h2)
B([
    "<b>1&nbsp;\u00b7&nbsp;Observe &amp; measure.</b> Waterfall, PSD and constellation render immediately; sampling "
    "frequency, symbol rate, carrier offset, roll-off and SNR are each measured with an explicit confidence.",
    "<b>2&nbsp;\u00b7&nbsp;Hypothesise &amp; decode.</b> A best-first search over modulation, interleaver, code and "
    "scrambler recovers the transmitter's recipe blind \u2014 no library of pre-known standards required.",
    "<b>3&nbsp;\u00b7&nbsp;Re-synthesise &amp; subtract.</b> The decoded bits are re-encoded, re-modulated and "
    "subtracted from the original recording. If the recipe is right, what's left is pure noise.",
    "<b>4&nbsp;\u00b7&nbsp;Prove it, layer by layer.</b> PHY is checked against the measured noise floor; coding is "
    "checked by parity-membership; structure is checked by sync/CRC/counter recurrence. A wrong recipe fails at "
    "least one layer \u2014 that is the whole point.",
    "<b>5&nbsp;\u00b7&nbsp;Sign it, and let anyone re-check it.</b> A PASS is signed into a portable, Ed25519 Decode "
    "Certificate. <code>sanjaya verify</code> re-derives every statistic from the file alone and reproduces the "
    "verdict independently \u2014 measured at \u2248&nbsp;1.7&nbsp;s.",
])
callout("<b>The core idea, in one line:</b> \u201cFinding is hard, checking is cheap.\u201d Fast, fallible search "
        "proposes candidate recipes; deterministic physics and algebra verify them. A search mistake costs time \u2014 "
        "never correctness. This is what separates a labelled guess from a proven answer.", bg=GREEN_BG, border=TEAL)
story.append(PageBreak())

# ============================================================ 3. USPs
section("3", "THE FIVE USPs", "What no analysis tool in this field does at all",
        "Verified, working, tested code \u2014 not roadmap slides")
usps = [
    ("Layered proof + signed, re-checkable Decode Certificate",
     "Re-synthesises the waveform from the decoded bits, subtracts it, and tests the residual at three "
     "independent layers (PHY, coding, structure). A PASS is Ed25519-signed; anyone can re-derive every "
     "statistic from the recording alone and reproduce the verdict on a different machine \u2014 measured "
     "\u2248&nbsp;1.7&nbsp;s. A tampered certificate or a tampered recording is caught and named."),
    ("Data-Sufficiency Engine",
     "When a recording is too short or weak to decide, SANJAYA predicts exactly how much more data would "
     "settle the question (P50/P90 extra duration), backed by a power analysis proving the test would have "
     "caught even a weak code at that length \u2014 so \u201cno code exists\u201d is never confused with "
     "\u201cnot enough evidence yet.\u201d Verified against controlled truncations: predicted 23.7 frames "
     "needed, measured need was 23.6."),
    ("Evidence Stitching + Sensor Twin",
     "Pools several short captures of the same emitter from different sensors \u2014 each with its own clock "
     "error, tuning offset, gain and noise floor, even a flipped spectral orientation \u2014 aligns them on a "
     "shared sync marker, and decodes from the pooled stream when no single capture has enough data alone. A "
     "capture of a different emitter (a decoy) is detected and dropped automatically."),
    ("Recipe Compiler",
     "Once certified, compiles a from-scratch, dependency-free receiver plus a GNU Radio flowgraph, ready to "
     "hand to a designated sensor \u2014 directly answering the PS's own phrase, \u201cthe resultant data is "
     "then utilised for processing signals in the designated sensors.\u201d A release gate requires the "
     "compiled receiver to reproduce every decoded bit exactly against the source recording, or nothing ships."),
    ("Honest, calibrated abstention",
     "Every undecided result shows exactly what was measured and why it stopped \u2014 never a fabricated "
     "duration or a guessed decode. This is enforced by design: a real UI bug that could have briefly shown a "
     "fabricated decode number in place of an honest \u201cundecided\u201d was found and fixed with a "
     "regression test, precisely because the system is built not to tolerate that failure mode."),
]
for i, (t, d) in enumerate(usps, 1):
    P(f"<b>USP&nbsp;{i}&nbsp;\u2014&nbsp;{t}</b>", h2)
    P(d, body)
    story.append(Spacer(1, 3))
story.append(PageBreak())

# ============================================================ 4. WOW FEATURE
section("4", "THE WOW FEATURE", "The certificate that anyone can check \u2014 without trusting SANJAYA at all",
        "This is the single feature to lead the demo with")
P("Every competing approach in this space \u2014 open-source or commercial \u2014 gives an analyst a <b>label</b>: "
  "\u201cthis is QPSK, rate-1/2 convolutional.\u201d None of them give the analyst a way to <b>check</b> that label "
  "without re-running the same tool and trusting it again. SANJAYA's Decode Certificate changes that:", body)
B([
    "The certificate is a self-contained, signed document: the file's SHA-256, the full recovered recipe, a "
    "verdict for every proof layer, every statistic and its threshold, and the near-miss hypotheses that were "
    "tried and rejected.",
    "<code>sanjaya verify recording.iq certificate.json</code> re-derives every one of those statistics directly "
    "from the recording \u2014 no search, no engine trust, no internet \u2014 and either reproduces the exact "
    "verdict, or names precisely which statistic changed and by how much.",
    "Tamper with the certificate, or swap in a different recording, and <code>verify</code> catches it and says "
    "exactly what does not match \u2014 demonstrated live, not claimed.",
    "This turns \u201ctrust our software\u201d into \u201ccheck the math yourself\u201d \u2014 the single property "
    "an intelligence analyst, and a judging panel of DSP engineers, will trust the most.",
])
callout("<b>Demo beat:</b> decode a recording live \u2192 export the certificate \u2192 hand it to a second laptop "
        "with no engine installed \u2192 <code>sanjaya verify</code> reproduces the verdict in under two seconds. "
        "Then tamper one byte of the certificate and show it get caught.", bg=GOLD_BG, border=ACCENT)
story.append(PageBreak())

# ============================================================ 5. FEATURES
section("5", "EVERY FEATURE", "The full feature set, mapped to the problem statement's own clauses",
        "Working code, verified this session against the source")
table([
    ["Feature", "What it delivers"],
    ["Ingest &amp; forensics", "WAV (mono/stereo), raw IQ (dtype/endianness/I-Q-order auto-sniffed), SigMF, with confidence scoring"],
    ["Triage gate", "Digital / voice / CW / noise classification before any decode is attempted"],
    ["Spectral visualisation", "Real-time waterfall, PSD and constellation, computed from the actual recording"],
    ["Measurement", "Sampling frequency, symbol rate, CFO, SNR, roll-off \u2014 each with an uncertainty"],
    ["Modulation ID + demod", "Blind: QPSK, BPSK, FSK (2/4-tone verified; 8-tone identifies correctly on real captures, blind-decode verification pending). Known-recipe: BPSK, QPSK, 8PSK, 16QAM, 64QAM, 2/4/8-tone FSK"],
    ["De-interleaving", "Block (blind + known-recipe), Diagonal and Pseudo-random (known-recipe)"],
    ["FEC decode", "Convolutional/Viterbi, Reed\u2013Solomon, Concatenated, LDPC \u2014 all four, known-recipe; conv blind"],
    ["Scrambler recovery", "Additive LFSR, library + exhaustive low-degree search, including the post-FEC coset case"],
    ["Bit-stream correlation", "Blind sync/frame/CRC/counter recovery; GF(2) CRC polynomial solving"],
    ["Standards recognition", "Matches measured parameters against a small cited table (STANAG 4285, MIL-188-110A, HFDL, "
     "PSK31/63, NAVTEX/SITOR-B, HF DSC, RTTY, 2G ALE) \u2014 verified correct on 6 real off-air recordings"],
    ["Layered proof + certificate", "Ed25519-signed Decode Certificate; independent re-check via sanjaya verify"],
    ["Data-Sufficiency Engine", "Predictive P50/P90 extra-duration estimate + collection tasking note"],
    ["Evidence Stitching + Sensor Twin", "Multi-sensor pooling, clock/tuning/SNR estimation relative to other sensors"],
    ["Recipe Compiler", "Bit-exact-gated standalone receiver + GNU Radio flowgraph export"],
    ["Export", "Certificate JSON, PDF, recipe JSON, frame/field CSV"],
    ["Quality system", "116 automated tests, an enforced module-layering rule, a deterministic seeded generator "
     "with per-layer ground truth for every test"],
], [48 * mm, W - 48 * mm])
story.append(PageBreak())

# ============================================================ 6. PS COVERAGE
section("6", "PS COVERAGE", "Every clause of the expected solution, and where each one stands",
        "Four of five core clauses are strong; the fifth \u2014 blind breadth \u2014 is being actively hardened")
P("The PS's own \u201cexpected solution\u201d lists five processing clauses plus two GUI clauses. Reading it "
  "strictly \u2014 \u201cautomated\u201d means the tool works this out itself, not that it works once a human "
  "supplies the answer \u2014 here is where each stands today:", body)
table([
    ["Clause", "Blind (automatic)", "Known-recipe"],
    ["(i) Identify Fs / modulation / FEC / interleaving", "QPSK, BPSK, FSK (2/4-tone) + rate-\u00bd conv + block interleaver", "n/a \u2014 this clause is blind ID"],
    ["(ii) Demodulate FSK / QAM / PSK", "\u2014", "BPSK\u201364QAM + FSK (2/4/8-tone), all live"],
    ["(iii) De-interleave Block/Conv/Diagonal/PRand", "Block", "Block, Diagonal, Pseudo-random live"],
    ["(iv) FEC: Viterbi/RS/Concatenated/LDPC", "rate-\u00bd convolutional", "All four decode; three of four (conv/RS/concat/LDPC) certify"],
    ["(v) Bit-stream correlation \u2192 header/payload", "Live on the blind-decodable family", "n/a"],
    ["(E1) PSD / constellation / waterfall", "Live", ""],
    ["(E2) Visual clarity", "Live", ""],
], [56 * mm, 62 * mm, W - 118 * mm])
P("<b>The clause being actively hardened: blind breadth beyond QPSK/BPSK.</b> This is the honest centre of the "
  "remaining engineering, and it is being worked on the same rigorous footing as everything else in this system "
  "\u2014 nothing here is a shortcut, and nothing is presented before it is tested.", h2)
B([
    "<b>Blind FSK is now live for 2- and 4-tone signals.</b> The non-coherent tone-bank demodulator, frame/sync "
    "discovery and the same dual-code search used for QPSK/BPSK now run directly on FSK-demodulated bits \u2014 "
    "verified end to end: the recipe search recovers the exact code, interleaver geometry and scrambler with "
    "<b>no recipe supplied</b>, and every recovered frame's CRC checks out. 8-tone signals (e.g. 2G ALE) already "
    "classify correctly \u2014 this engine identifies them by family, rate and standard on real off-air captures "
    "\u2014 and 8-tone blind decode is the immediate next step on the same path, not a new derivation.",
    "<b>Why FSK generalises safely where 8PSK/16QAM/64QAM do not (yet):</b> those constellations carry a "
    "rotation/I-Q-swap ambiguity that is not guaranteed data-independent past two symmetric points, so extending "
    "blind search to them without the same rigor BPSK/QPSK received risks a wrong decode \u2014 the one outcome "
    "this system is built to prevent. FSK's non-coherent tone-energy detection has no such ambiguity at all, "
    "which is exactly why it was reachable this cycle and the others are being taken one at a time, each with "
    "its own dedicated derivation, the same discipline that got BPSK and now FSK across the line.",
    "<b>Certification for FSK is the very next step</b> \u2014 decode is proven correct by CRC today; wiring it "
    "through the same statistical proof layer that convolutional/RS/LDPC already have is the next, well-defined "
    "unit of work, not an open question.",
])
story.append(PageBreak())

# ============================================================ 7. WHY WE STAND OUT
section("7", "WHY WE STAND OUT", "Measured against the tools an analyst actually reaches for today",
        "Not a repo popularity contest \u2014 a capability comparison against real, deployed tooling")
P("The right benchmark for this PS is not other hackathon prototypes \u2014 it's the open-source and commercial "
  "tools an NTRO analyst would otherwise use. Judged against that field:", body)
table([
    ["Tool", "What it is", "Where SANJAYA is ahead"],
    ["GNU Radio + gr-inspector", "DSP toolkit; you build the flowgraph", "You must already know the signal. SANJAYA works it out, then proves it."],
    ["Inspectrum, SigDigger/Suscan", "Manual spectrogram/baud-rate viewers", "No classification, no FEC, no interleaving, no proof \u2014 fully manual"],
    ["Universal Radio Hacker", "Simple ASK/FSK/PSK IoT protocol RE", "No QAM, no blind FEC/interleaver ID, no signed proof"],
    ["fldigi, multimon-ng, dsd", "Decoders for specific known modes", "Only work if you already know the exact standard; SANJAYA is blind"],
    ["go2MONITOR / go2DECODE, W-CODE, Rohde &amp; Schwarz CA100", "Commercial, closed, expensive COMINT suites; the closest real capability match", "No re-checkable signed certificate anywhere in this class; SANJAYA is sovereign, offline and open"],
    ["RadioML + research AMC code", "Deep-learning modulation classification benchmarks", "Classification only \u2014 no demod, no decode, no proof, no GUI"],
], [46 * mm, 58 * mm, W - 104 * mm])
callout("<b>The structural gap SANJAYA closes, and no tool above does at all:</b> a mathematically layered proof "
        "of the decoded answer, a signed certificate any third party can re-check offline, predictive "
        "data-sufficiency, multi-sensor evidence stitching, and a bit-exact-gated receiver hand-off to a sensor. "
        "These five are interlocking \u2014 the compiler consumes certified recipes, stitching needs the Sensor "
        "Twin and the sufficiency maths, the proof arbitrates both \u2014 which is why no single feature copied "
        "in isolation reproduces the system.", bg=GREEN_BG, border=TEAL)
story.append(PageBreak())

# ============================================================ 8. IMPACT & BENEFITS
section("8", "IMPACT &amp; BENEFITS", "What changes for the analyst, in numbers",
        "Time, trust and sovereignty \u2014 quantified where the project has measured it")
statrow([("2\u201313 s", "measured blind decode time, vs. an expert's manual iterate-and-guess workflow"),
         ("~1.7 s", "measured independent certificate re-verification, on a second machine, offline"),
         ("\u2264 10\u207b\u2074", "target false-certificate bound per certificate, once the near-miss campaign runs")])
B([
    "<b>Analyst time:</b> the PS itself names the bottleneck \u2014 manual parameter guessing that does not scale "
    "across sensors and locations. A blind decode measured in single-digit seconds, with the confidence to trust "
    "the answer without re-verifying by hand, converts an expert-hours task into an operator-minutes task.",
    "<b>Confidence, quantified, not asserted:</b> a genuine CRC-16 pass by chance is 2\u207b\u00b9\u2076 per frame; "
    "twenty consecutive passes by chance is 2\u207b\u00b3\u00b2\u2070. The layered proof turns \u201cI think this is "
    "right\u201d into a number, on every certificate, every time.",
    "<b>Sovereignty and cost:</b> the closest real-world capability match (go2MONITOR, W-CODE, Rohde &amp; Schwarz "
    "COMINT suites) is closed, foreign, and licensed at a cost that puts it out of reach for routine, "
    "wide-deployment use. SANJAYA runs fully offline, air-gapped by design (zero outbound network calls), on "
    "commodity hardware \u2014 directly serving the indigenous, low-cost angle NTRO's own spectrum-monitoring "
    "modernisation is oriented around.",
    "<b>Data-starved sensors, handled honestly:</b> when a real capture is too short \u2014 exactly the failure "
    "mode the PS itself names (\u201cinsufficient for fine grain analysis\u201d) \u2014 the Data-Sufficiency Engine "
    "gives a concrete, testable answer (how much more, from where) instead of either a wrong guess or a shrug.",
])
story.append(PageBreak())

# ============================================================ 9. REFERENCES
section("9", "REFERENCES &amp; RESEARCH LINKS", "Every technical and contextual claim, sourced",
        "Standards, algorithms, and the external context cited above")
P("<b>Signal-processing and coding-theory foundations implemented in the engine:</b>", h2)
B([
    "Viterbi, A. (1967). \u201cError bounds for convolutional codes and an asymptotically optimum decoding "
    "algorithm.\u201d IEEE Transactions on Information Theory \u2014 the maximum-likelihood decoder behind the "
    "engine's convolutional/Viterbi FEC.",
    "Berlekamp, E. &amp; Massey, J. (1969). The Berlekamp\u2013Massey algorithm \u2014 used for both Reed\u2013Solomon "
    "error-locator recovery and blind scrambler polynomial identification.",
    "CCSDS 131.0-B (TM Synchronization and Channel Coding) \u2014 source of the reference PHY attached sync marker "
    "(0x1ACFFC1D) and the CCSDS additive randomiser used as the engine's library scrambler.",
    "Gallager, R. (1962). \u201cLow-Density Parity-Check Codes.\u201d IRE Transactions on Information Theory \u2014 "
    "the LDPC decoder's log-domain min-sum belief propagation.",
    "SigMF (Signal Metadata Format), sigmf.org \u2014 the open metadata standard the ingestion layer parses and the "
    "Recipe Compiler's package annotates output with.",
    "O'Shea, T. &amp; West, N. \u2014 RadioML datasets/benchmarks, referenced as the field's standard for automatic "
    "modulation classification comparisons.",
])
P("<b>External context cited in this document:</b>", h2)
B([
    "NICF, <i>Policy and Regulatory Frameworks for Emerging Technologies in Spectrum Management</i> (2026) \u2014 "
    "<a href=\"https://nicf.gov.in/wp-content/uploads/2026/01/Policy-and-Regulatory-Frameworks-for-Emerging-Technologies-in-Spectrum-Management-1.pdf\">"
    "nicf.gov.in</a>",
    "\u201cSpace Based Surveillance project (India)\u201d \u2014 "
    "<a href=\"https://en.wikipedia.org/wiki/Space_Based_Surveillance_project_(India)\">en.wikipedia.org</a>",
    "Shoghi Communications, <i>HF/VHF/UHF Monitoring System</i> \u2014 "
    "<a href=\"https://www.shoghicom.com/all-products/hf-vhfuhf-monitoring-system\">shoghicom.com</a>",
    "SIH 2026 Problem Statement 26147, as issued by NTRO \u2014 verbatim text reproduced in Section 1 of this "
    "document, from the team's own <code>introduction to 147.pdf</code>.",
])
callout("<b>A note on rigour, for the judging panel.</b> Every capability marked \u201clive\u201d or "
        "\u201cverified\u201d in this document was re-checked against the actual source code and test suite on the "
        "date of writing \u2014 not carried forward from an earlier claim. Where a capability decodes but is not yet "
        "certified, or is blind for one family but not yet another, that is stated plainly rather than glossed "
        "over. This discipline \u2014 proving claims, not just stating them \u2014 is the project's thesis applied "
        "to its own documentation.", bg=LIGHT, border=NAVY)

doc = SimpleDocTemplate("../content.pdf", pagesize=A4,
                        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                        title="Project SANJAYA - SIH 2026 PS 26147", author="Team SANJAYA")
doc.build(story)
print("wrote content.pdf")
