"""Winning plan v3 for SIH 26147: formal review of v2 (findings register) + review-ready plan.
All citations and hardware/signal facts re-verified 26 Sep 2026 (arXiv, Crossref, maker docs).
Run from inside _build/:  python make_plan_v3.py"""
import math
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
TEAL, GREEN, GOLD, RED = colors.HexColor("#2a6f77"), colors.HexColor("#dcefe9"), colors.HexColor("#fbeee9"), colors.HexColor("#f6d5d1")
GREY = colors.HexColor("#c9c2b2")
body = ParagraphStyle("b", fontName="Arial", fontSize=9.2, leading=12.8, spaceAfter=4)
small = ParagraphStyle("s", fontName="Arial", fontSize=7.7, leading=9.9)
tiny = ParagraphStyle("t", fontName="Arial", fontSize=7.0, leading=8.9)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=15.5, leading=19.5, textColor=NAVY, spaceBefore=2, spaceAfter=6)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=11, leading=14.2, textColor=ACCENT, spaceBefore=6, spaceAfter=3)
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
          ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra: st.append(("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, LIGHT]))
    t.setStyle(TableStyle(st + (extra or []))); story.append(t); story.append(Spacer(1, 6))
def callout(text, bg=LIGHT, border=ACCENT):
    t = Table([[Paragraph(text, body)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t); story.append(Spacer(1, 6))
def sup(x): return f"<super>{x}</super>"
def sub(x): return f"<sub>{x}</sub>"
E = lambda n: f"10{sup(n)}"        # 10^n

rid = [
 # correctness
 ("R01", "M", "C4", "'Separates transmitter from sensor clock error when two sensors hear one emitter' is underdetermined: 2 equations, 3 unknowns.", "Network clock solution with one GPS/atomic reference fixing the gauge. §5 C4"),
 ("R02", "M", "C1", "'Explained energy 99.1 %' undefined. At 14.2 dB SNR the signal is only 96.3 % of in-band energy, so the figure is only valid if normalised by signal energy.", "Defined η = 1 − (P" + sub("r") + " − P" + sub("n") + ")/(P" + sub("x") + " − P" + sub("n") + ") with P" + sub("n") + " from the Sensor Twin. §5 C1, §9"),
 ("R03", "M", "C1 KPI", "'False-certificate rate = 0' cannot be demonstrated; zero observed failures only bounds the rate.", "Rule of three: 0 false PASS in ≥ 30,000 near-miss trials → P(PASS | wrong) ≤ " + E("−4") + " (95 %). §5 C1"),
 ("R04", "M", "C3 KPI", "'Stitched curve reaches 95 % with less than half the single-file data' is ill-posed: pooling cannot beat equal total data.", "KPI = alignment loss ≤ 10 % versus one capture of equal total length. §5 C3"),
 ("R05", "M", "Tier 3", "'Amateur satellites with AO-40-style FEC (UHF 435-438 MHz)' with BPSK is wrong: FUNcube-family BPSK is VHF (145.935 MHz for AO-73); the UHF AO-40-style examples listed by gr-satellites use FSK.", "Row corrected with verified frequencies. §7"),
 ("R06", "M", "Tier 3", "multimon-ng listed as a NAVTEX decoder; its mode list has no NAVTEX.", "Truth source is fldigi. §7"),
 ("R07", "M", "Refs", "arXiv 2402.17450 ('Conformal Shield') is an adversarial-attack detector for AMC that uses conformal prediction, not a paper on conformal prediction sets.", "Described correctly; Angelopoulos &amp; Bates (arXiv 2107.07511) added as the conformal reference. §13"),
 ("R08", "M", "Tier 3", "'Only public, unencrypted broadcasts' contradicts STANAG 4285, whose payloads are typically encrypted.", "Policy restated: modem and framing layers only; payloads never decrypted or displayed. §7"),
 ("R09", "m", "Tier 3", "STANAG 4285 given as '8PSK 2400 Bd, convolutional interleaver'. Verified: BPSK/QPSK/8PSK by data rate; rate-1/2 K=7 code; short or long interleaving (type not asserted).", "Corrected. §7"),
 ("R10", "m", "Tier 3", "Meteor LRPT called 'the entire PS chain'; it has no LDPC. Also 72 kBd (80 kBd on some passes); N2-3 antenna only partly deployed.", "Precise wording; LDPC covered by QO-100 DVB-S2 (stretch) and HIL. §7"),
 ("R11", "m", "C2", "Worked example '14 more codewords, 2.3 s' was not derived; 'codeword' undefined.", "Derived planning model with formula and exact numbers. §5 C2"),
 ("R12", "m", "C2", "Data-need claim attributed to arXiv 2601.15903 without verifying that it states it.", "Rank criterion attributed to Sicot, Houcke, Barbier (Signal Processing, 2009). §5 C2"),
 ("R13", "m", "C5", "'gr-digital / gr-fec blocks' - the GNU Radio core has no Reed-Solomon or generic de-interleaver.", "Out-of-tree blocks named; bit-exact release gate. §5 C5"),
 ("R14", "m", "C5 KPI", "'Decodes 100 % of frames proven offline' mixes offline and live conditions.", "Two KPIs: bit-exact on the source recording; live FER within 1 dB. §5 C5"),
 ("R15", "m", "§6 HIL", "'HF fading on real hardware' overclaims: Pluto tunes 325 MHz-3.8 GHz; fading is emulated at baseband on a UHF carrier.", "Wording corrected. §7"),
 ("R16", "m", "§0", "'Five of them are new in v2' - six are new (C2-C7); C1 and C8 evolve v1 ideas.", "Corrected. §5"),
 ("R17", "m", "Refs", "Non-binary LDPC paper is in the 2026 issue of Digital Communications and Networks; RS paper venue is IEEE Communications Letters; IET title abbreviated.", "Full, verified citations with DOIs. §13"),
 ("R18", "m", "§2, §5", "'0 of 43' reads as a fact about competitors' code; it is a statement about README claims.", "Method and snapshot date stated wherever counts appear. §3, §6"),
 ("R19", "m", "§2", "'3 show a verified real capture' - we did not verify them.", "'3 describe a real capture'. §3"),
 ("R20", "m", "C7", "WAV-Lifting implied FM audio can be inverted to IQ; FM demodulation discards RF phase.", "Honest limit: linear chains lifted; FM message analysed instead. §5 C7"),
 ("R21", "m", "C6", "Counter chronology ignored counter wrap-around.", "Formula with modulus 2" + sup("b") + " and elapsed-time disambiguation. §5 C6"),
 ("R22", "m", "C3", "Stitching alignment assumed; exact only with a sync marker.", "Honest limit and joint phase search stated; per-capture proof ejects mis-associations. §5 C3"),
 # rigour and programme
 ("R23", "M", "§3 KPIs", "KPIs lack SNR definition, observation length and sample size; identification targets at BER " + E("−2") + " with no data length are not credible for large interleavers.", "Metric definitions and conditioned acceptance criteria. §4, §9"),
 ("R24", "m", "§3 KPI", "Fs target '0.1 %' is weak and inconsistent with the 1 ppm Sensor Twin KPI.", "≤ 10 ppm for standard-anchored captures ≥ 10 s. §4"),
 ("R25", "C", "§8", "No effort model: 8 crown + 7 depth innovations + full PS in 10 weeks; 7 innovations in 2 weeks. Schedule not credible.", "Work breakdown, capacity, 17 % reserve, P1/P2/P3 classes, minimum winning configuration. §10"),
 ("R26", "M", "§8", "No gates with entry/exit criteria; no rule for activating stretch work.", "Gates G0-G5; P2 only from measured reserve at G3. §10"),
 ("R27", "M", "all", "No technology readiness levels; NTRO and ISRO reviewers think in TRLs.", "TRL today and at finale per element (NASA NPR 7123.1 definitions). §10"),
 ("R28", "M", "§10", "Risks unscored; no owners or triggers.", "5 x 5 risk register. §11"),
 ("R29", "M", "§9", "Live RF demo assumes a transmitter is allowed at the venue.", "Every demo beat has a fallback (sealed files, throttled replay). §12"),
 ("R30", "m", "§8", "No assumptions register (dates, offline mode, single-carrier scope, finale data).", "Assumptions register. §2"),
 ("R31", "m", "§8", "Per-person load not checked.", "Load per role ≤ 6.25 pw. §10"),
 # V&V and assurance
 ("R32", "M", "§3", "No requirement IDs or verification methods.", "R-01...R-15 with Test / Analysis / Inspection / Demonstration. §4"),
 ("R33", "M", "§6", "No independence: the team would grade its own work.", "Independent verification with sealed test sets. §9"),
 ("R34", "M", "§7", "Hostile input not considered: NTRO ingests files from untrusted sources.", "Coverage-guided fuzzing of all parsers; least-privilege engine. §8"),
 ("R35", "M", "§7", "No supply-chain control (SBOM, pinned hashes) for an air-gapped deployment.", "Offline wheelhouse with pinned hashes; SBOM per release. §8"),
 ("R36", "M", "§7", "'No network at runtime' asserted, not verified.", "Network-isolation test with packet capture in acceptance. §8"),
 ("R37", "m", "§7", "Licences unaddressed (several oracles are copyleft).", "Oracles used only in the test harness; licence register. §8"),
 ("R38", "m", "§6", "Spectrum law and receive-side legality not addressed.", "Legal and ethics box. §7"),
 ("R39", "m", "§6", "No data-management plan.", "SigMF metadata, checksums, manifests for every capture. §7"),
 # missed opportunities
 ("R40", "M", "C3", "Stitching demonstrated only on lab receivers, not on 'different sensors and different locations'.", "Simultaneous GPS-timestamped recordings from ≥ 3 public KiwiSDRs in different countries. §7"),
 ("R41", "M", "C4", "No independent physical truth for the frequency/timing estimators.", "Satellite Doppler curve versus SGP4 prediction from public TLEs. §7"),
 ("R42", "M", "C6", "Physical-trait passports validated only on the bench.", "ADS-B: every aircraft self-identifies (24-bit ICAO address) - thousands of real transmitters with truth. §7"),
 ("R43", "M", "Tier 3", "No real LDPC signal in the plan.", "QO-100 wideband beacon (DVB-S2, LDPC + BCH) as stretch. §7"),
 ("R44", "m", "§0", "Informal wording in a formal plan.", "Formal register. all"),
]
sev = {k: sum(1 for r in rid if r[1] == k) for k in ("C", "M", "m")}

# ============================================================ COVER
story.append(Spacer(1, 22 * mm))
P('<font color="#c8553d">SIH 2026 &middot; PS 26147 &middot; NTRO &middot; WINNING PLAN v3 &middot; REVIEW-READY EDITION</font>',
  ParagraphStyle("k", parent=body, fontSize=11.5, fontName="Arial-Bold"))
P("Project SANJAYA", title)
P("A blind signal-forensics system that <b>proves</b> its answers, says <b>how much more data</b> an open question needs, "
  "pools short captures from <b>different sensors</b>, and hands NTRO's designated sensors a <b>ready-to-run receiver</b>.",
  ParagraphStyle("st", parent=body, fontSize=13.5, leading=18.5, textColor=TEAL))
story.append(Spacer(1, 6 * mm))
callout("<b>What v3 is.</b> v2 was put through a formal design review of the kind used before a preliminary design review: every sentence read "
        "against the problem statement (PS), every citation re-checked at its source, every hardware and signal fact checked against "
        f"maker or operator documentation, every number recomputed. The review raised <b>{len(rid)} findings</b> ({sev['C']} critical, {sev['M']} major, {sev['m']} minor; "
        "Section 1). All are dispositioned in this edition. v2 scored <b>6.4 / 10</b> on the review scorecard: a strong concept, not yet review-ready.",
        bg=colors.white, border=TEAL)
table([["Verification performed for this edition (26 Sep 2026)", "Result"],
       ["17 research citations: title, venue, date checked on arXiv and Crossref", "All exist; 1 misdescribed (arXiv 2402.17450) and 3 with imprecise date, venue or title - corrected"],
       ["12 foundations (8 new: Gardner, Cluzeau, Valembois, Sicot, Marazin, Merchant, Wilson, Hanley)", "All confirmed with DOIs on Crossref"],
       ["Signal facts: Meteor-M LRPT, STANAG 4285, HFDL, NAVTEX, FUNcube, QO-100, ADS-B, AIS", "2 errors and 3 imprecisions in v2 (FUNcube band, NAVTEX decoder; STANAG, Meteor, encryption wording) - corrected"],
       ["Hardware facts: ADALM-Pluto, RTL-SDR Blog V4, KiwiSDR", "Confirmed (ranges, oscillator accuracy, channel count, GPS timestamps)"],
       ["Every worked number in the plan", "Recomputed; formulas shown next to each number"]],
      [120 * mm, 60 * mm])
P("<i>Conventions: SNR is E" + sub("s") + "/N" + sub("0") + " in the occupied bandwidth unless stated. KPIs are pre-registered <b>targets</b>, "
  "not results. 'pw' = person-week of 40 hours. Competitor statements are what their public READMEs claim (snapshot 26 Sep 2026); code was not run.</i>", tiny)
story.append(PageBreak())

# ============================================================ 0. SCORECARD
P("0. Review of v2 - scorecard and verdict", h1)
P("Scored against ten criteria a space-agency review board would apply. Weights reflect what decides an NTRO evaluation: "
  "correctness, coverage and innovation first; then evidence, feasibility and assurance.")
score = [
    ("Technical correctness", 15, 6, "Six factual or mathematical errors (FUNcube band, NAVTEX decoder, 'Conformal Shield' misdescribed, two-sensor clock separation underdetermined, undefined 'explained energy', STANAG wording).", "Every fact re-verified; formulas and definitions added; errors corrected."),
    ("Coverage of the PS", 15, 9, "All clauses mapped; acceptance criteria loosely defined.", "Requirement IDs, verification method and precise acceptance criteria (Section 4)."),
    ("Innovation and uniqueness", 15, 9, "Eight crown innovations at 0 of 43 READMEs; strong narrative.", "Kept; each now has honest limits, validation on real data and a TRL."),
    ("Quantitative rigour", 10, 4, "KPIs lacked observation length, SNR definition, sample sizes; 'false-certificate rate = 0' is unprovable; one ill-posed KPI.", "Metric definitions, Wilson intervals, rule-of-three bound, derived worked examples."),
    ("Feasibility and schedule", 10, 4, "15 innovations plus full PS in 10 weeks with no effort model; P4 packed 7 innovations into 2 weeks.", "Work-breakdown with person-weeks, capacity, 17% reserve, priority classes, gates."),
    ("Verification and validation", 10, 5, "No requirement traceability, no independence, no pre-registration.", "V&amp;V plan with independent verification and sealed test sets (Section 9)."),
    ("Real-data realism", 10, 7, "Strong tiers; two wrong specifics; missed multi-site, Doppler and identity-labelled sources.", "Multi-site KiwiSDR, SGP4 Doppler truth, ADS-B identities, QO-100 LDPC, SatNOGS archive."),
    ("Risk management", 5, 5, "Risks listed without likelihood, consequence, owner or trigger; no venue fallback.", "5 x 5 register with owners and triggers; fallback for every demo beat."),
    ("Security and compliance", 5, 3, "Nothing on hostile input, supply chain, zero-network proof, licences, spectrum law.", "Assurance section: fuzzing, SBOM, pinned offline deps, network-isolation test, legal."),
    ("Clarity and presentation", 5, 8, "Clear; some informal wording ('goated').", "Formal register throughout."),
]
rows = [["Criterion", "Weight", "v2", "Why", "v3 action"]]
for c, w, s, why, act in score: rows.append([c, f"{w}%", f"{s}/10", why, act])
tot = sum(w * s for _, w, s, _, _ in score) / 100
rows.append(["<b>Weighted total</b>", "100%", f"<b>{tot:.1f}/10</b>", "Strong concept; would not pass a design review with these findings open.", f"All {len(rid)} findings dispositioned (Section 1)."])
table(rows, [30 * mm, 13 * mm, 11 * mm, 68 * mm, 58 * mm],
      extra=[("BACKGROUND", (2, i), (2, i), GREEN if score[i - 1][2] >= 8 else GOLD if score[i - 1][2] >= 6 else RED) for i in range(1, len(score) + 1)]
            + [("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), colors.HexColor("#e6e1d6"))])
P("What changed from v2 to v3", h2)
table([["Area", "v2", "v3"],
       ["Evidence standard", "Facts from memory", "Every citation and hardware/signal fact verified at source; DOIs and arXiv IDs listed"],
       ["KPIs", "Single numbers", "Defined metrics, conditions (SNR, data length), sample sizes, confidence intervals"],
       ["Proof-of-Decode", "Energy + whiteness", "Four calibrated tests incl. cyclostationarity at the symbol rate; near-miss rejection; certificate lists what it could and could not rule out"],
       ["Insufficient data", "Claimed", "Quantified: hard-decision rank methods need ~24 h of signal for a 1,500-bit interleaver (derivation in C2); SANJAYA's answer measured against that"],
       ["Real data", "4 tiers", "Adds multi-site KiwiSDR (GPS-timestamped), SGP4 Doppler truth, ADS-B identities, QO-100 DVB-S2 (real LDPC), SatNOGS archive"],
       ["Programme", "Phases", "Work breakdown (31.2 pw P1 vs 37.5 pw capacity), priority classes, gates G0-G5, TRL now and at finale"],
       ["Assurance", "Absent", "Hostile-input fuzzing, SBOM, pinned offline dependencies, network-isolation proof, signing keys, licences, spectrum law"]],
      [28 * mm, 42 * mm, 110 * mm])
story.append(PageBreak())

# ============================================================ 1. FINDINGS REGISTER
P("1. Findings register (review item discrepancies)", h1)
P("Severity: <b>C</b> critical (would sink the evaluation), <b>M</b> major (an expert judge would catch it), <b>m</b> minor. "
  "Every finding is closed in the section named in the last column.")
table([["ID", "Sev", "Where (v2)", "Finding", "Disposition in v3"]] + [list(r) for r in rid],
      [10 * mm, 8 * mm, 16 * mm, 88 * mm, 58 * mm], style=tiny,
      extra=[("BACKGROUND", (1, i), (1, i), RED if r[1] == "C" else GOLD if r[1] == "M" else colors.white) for i, r in enumerate(rid, 1)])
P(f"<b>Totals:</b> {len(rid)} findings - {sev['C']} critical, {sev['M']} major, {sev['m']} minor. All dispositioned.", small)
story.append(PageBreak())

# ============================================================ 2. MISSION, SCOPE, ASSUMPTIONS
P("2. Mission, scope and assumptions", h1)
callout("<b>Mission.</b> Turn any recording from any NTRO sensor into a <b>proven</b> transmitter recipe - sampling frequency, modulation, "
        "interleaving, FEC, scrambling, frame structure, header and payload - automatically, offline, with a statement of what the data can "
        "and cannot support, and deliver that recipe back to designated sensors as something they can run.", bg=colors.white, border=NAVY)
table([["In scope", "Out of scope (by design)"],
       ["Recorded .IQ and .wav files, HF / VHF / UHF, few kHz to MHz bandwidths; single-carrier PSK / QAM / FSK / MSK families; "
        "block, convolutional, diagonal, pseudo-random interleaving; convolutional, RS, concatenated, LDPC codes; scramblers; framing; header / payload.",
        "Decryption of payloads; live SDR control as a requirement (supported as a bonus); OFDM unless the SPOC asks for it; cloud services; "
        "LLM chat interfaces."]],
      [95 * mm, 85 * mm])
P("Minimum winning configuration (what must exist at the finale, whatever happens)", h2)
B(["100 % of the PS (R-01 to R-15) on the bench and on real signals with independent truth.",
   "C1 Proof-of-Decode, C2 Data-Sufficiency, C3 Evidence Stitching with C4-lite, C5 Recipe Compiler - the answer to the PS's two central complaints (insufficient data, different sensors) and its output requirement (designated sensors).",
   "A real signal decoded end to end with independent confirmation (Meteor-M LRPT versus SatDump), and multi-site real stitching (KiwiSDR)."])
P("Assumptions register (to confirm with the SPOC / mentor)", h2)
table([["ID", "Assumption", "If wrong"],
       ["A-01", "Analysis of recorded files is the requirement; live reception is a bonus.", "C5 already produces live receivers; add a live-input path (1 pw from reserve)."],
       ["A-02", "Recordings may lack metadata; sampling frequency may be unknown.", "None - both cases designed for."],
       ["A-03", "Signals of interest are single-carrier; OFDM not required.", "Add OFDM parameter estimation as P2 (1.5 pw)."],
       ["A-04", "Payload decryption is out of scope.", "Out of scope regardless; report structure only."],
       ["A-05", "Finale evaluation may use NTRO-provided files of unknown content.", "Designed for; C2 reports when a file cannot support a decision."],
       ["A-06", "Target hardware is a laptop class machine, no GPU required.", "GPU path optional; nothing depends on it."],
       ["A-07", "About ten build weeks between idea selection and finale; SIH 2026 dates to be confirmed on sih.gov.in.", "Re-plan with the same WBS; P2/P3 absorb the change."],
       ["A-08", "Six members at about 25 h per week each (37.5 pw).", "Descoping order in §10."]],
      [12 * mm, 100 * mm, 68 * mm])
story.append(PageBreak())

# ============================================================ 3. FIELD
P("3. The field: 43 public competitors", h1)
P("<i>Method: the 43 ranked repositories in repos.pdf; each README searched for every capability, matching sentences read by hand; "
  "snapshot 26 Sep 2026. Counts are README claims, not verified behaviour.</i>", small)
table([["Capability", "READMEs claiming it", "Best in field", "Limitation"],
       ["Loader, PSD, waterfall, constellation", "~40", "sanket (C++ mmap), harikesh (WebGL)", "Table stakes."],
       ["PSK/QAM/FSK demodulation", "~28", "NaidhruvK (lock-check, equaliser)", "AWGN-tuned in most."],
       ["Fixed-catalogue FEC (K=7 Viterbi, RS(255,223))", "~25", "Gururaghavendra123 (CRC-gated search)", "Blind only inside the catalogue."],
       ["ML modulation classifier", "~22", "RadioFry", "Trained on synthetic RadioML."],
       ["UNKNOWN / provenance / abstain labels", "~20", "karurravishanker", "Labels uncertainty; never reduces it."],
       ["GF(2) rank interleaver ID (hard bits)", "~6", "ShantanuSomwanshi (size, PN seed)", "Needs error-free rows: data-hungry (§5 C2)."],
       ["Multi-signal detection", "~6", "aayushkasurde", "Detects; never cancels."],
       ["Real over-the-air capture", "3 describe one", "ICHNOVA (KiwiSDR time stations)", "No real signal with a full PHY + coding chain and independent truth."],
       ["CRC library sweep", "2", "yoganandasp15, aayushkasurde", "Known CRCs only."],
       ["Protocol profiles", "1", "yoganandasp15", "No sample-rate or clock back-solving."],
       ["Voice / CW / noise-only labels", "~6", "yoganandasp15 (NO SIGNAL verdict, CW class, voice formants)", "Labels only; none uses them to decide whether to run the decode chain."]],
      [55 * mm, 25 * mm, 50 * mm, 50 * mm])
P("Where every competitor stops", h2)
table([["#", "Wall", "Evidence (README claims)"],
       ["1", "One file at a time", "None mentions combining captures."],
       ["2", "One sensor at a time", "Three restate the PS sentence; none models sensors."],
       ["3", "No answer to 'is this enough data?'", "None estimates data needed."],
       ["4", "Output ends in a report", "None generates a receiver."],
       ["5", "Truth from their own generator", "33 describe synthetic or generated test data."],
       ["6", "Catalogue-bound coding layer", "LDPC is 'pick from list' or 'not identifiable'."],
       ["7", "Scramblers not identified", "Fixed descramblers at most."],
       ["8", ".wav = stereo IQ or Hilbert of mono", "Receiver audio chains not modelled."],
       ["9", "Bit-level verification at best", "CRC / re-encode BER only."],
       ["10", "Models never improve in use", "Retrain scripts on synthetic data."]],
      [8 * mm, 62 * mm, 110 * mm])
story.append(PageBreak())

# ============================================================ 4. REQUIREMENTS
P("4. Pillar A - the expected solution as verifiable requirements", h1)
callout("<b>PS, expected solution (verbatim):</b> <i>\"The expected system should improve feature visibility of signals with the help of GUI, enable automated "
        "signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall (time-frequency domain), demodulate "
        "signals, carry out de-interleaving and error correction. The output can then be used to carry out correlation of bit stream for identification "
        "of header and payload.\"</i>", bg=colors.white, border=NAVY)
P("Verification method: <b>T</b> test, <b>A</b> analysis, <b>I</b> inspection, <b>D</b> demonstration (NASA Systems Engineering Handbook, SP-2016-6105 Rev 2). "
  "Reference laptop: 8-core x86-64, 16 GB RAM, integrated GPU, SSD.")
reqs = [
 ("R-01", ".IQ or .wav input", "WAV parse (mono real / stereo IQ, 8-32 bit, float); raw IQ dtype {u8,i8,i16,i32,f16,f32,f64} x endianness x I/Q order sniff with confidence; SigMF sidecar; manual override; C7 for receiver audio.",
  "T", "Correct format on 100 % of 200 bench files ≥ 64 kB at SNR ≥ 0 dB; every ambiguous case surfaced, never silent."),
 ("R-02", "(i) Sampling frequency", "Header / SigMF; else back-solved from a recognised standard's symbol clock and the anti-alias edge; sensor clock error reported.",
  "T, A", "≤ 10 ppm on standard-anchored captures ≥ 10 s at SNR ≥ 10 dB; otherwise 'Fs unknown' stated with normalised units."),
 ("R-03", "(i) Other parameters", "Centre offset, occupied bandwidth, SNR, symbol rate, roll-off, FSK tones and index, burst timing.",
  "T", "Symbol rate ≤ " + E("−4") + " relative (≥ 1,000 symbols, SNR ≥ 10 dB); SNR ±1 dB (SNR ≥ 0 dB); bandwidth ±5 %."),
 ("R-04", "(i) Modulation", "Three experts fused; calibrated probabilities; split-conformal 95 % prediction set; open-set 'novel'.",
  "T", "Top-1 ≥ 98 % at SNR ≥ 10 dB with ≥ 1,000 symbols over 11 classes (BPSK, QPSK, OQPSK, 8PSK, 16QAM, 64QAM, 2/4/8-FSK, MSK, GMSK); set coverage 0.95 ± 0.01 (n ≥ 2,000)."),
 ("R-05", "(i) FEC", "Blind conv (rate, K, generators), RS (n, k), LDPC (catalogue by syndrome), concatenation by peeling.",
  "T", "P" + sub("id") + " vs BER and data-length curves published; ≥ 95 % at BER ≤ " + E("−3") + " with ≤ " + E("5") + " coded bits for convolutional codes (K ≤ 9) and ≤ " + E("6") + " for RS (n ≤ 255); characterised to BER " + E("−2") + "."),
 ("R-06", "(i) Interleaving", "Block, convolutional, diagonal, pseudo-random; soft rank profile joint with code ID; PN seed library.",
  "T", "When C2 declares the data sufficient: P" + sub("id") + " ≥ 95 % (periods ≤ 4,096 bits, BER ≤ " + E("−3") + "); data required vs period and BER reported as curves; characterised to BER " + E("−2") + "."),
 ("R-07", "(ii) Demodulate FSK, QAM, PSK", "RRC matched filter, Oerder-Meyr + Gardner timing, M-th power + Costas carrier, CMA → DD-LMS equaliser, FSK bank; soft LLRs.",
  "T", "BER within 0.5 dB of theory at BER " + E("−4") + " (AWGN) per scheme; HF (Watterson) curves reported."),
 ("R-08", "(iii) De-interleave x 4 types", "Invertible operators parameterised by R-06; manual override.", "T", "Bit-exact round trip on " + E("4") + " random vectors per type."),
 ("R-09", "(iv) FEC decode x 4 families", "C++ soft Viterbi (K 3-9, punctured), RS Berlekamp-Massey, concatenated, LDPC normalised min-sum.",
  "T", "Within 0.2 dB at FER " + E("−3") + " of reference implementations: liquid-dsp or GNU Radio gr-fec (convolutional, RS), AFF3CT (LDPC)."),
 ("R-10", "(v) Bit-stream correlation, header and payload", "Autocorrelation frame length; soft sync discovery; aligned raster; counters, length fields; CRC solved by GF(2) algebra.",
  "T", "Frame length and sync on 100 % of framed files with ≥ 20 frames at BER ≤ " + E("−3") + "; field class accuracy ≥ 95 % per column."),
 ("R-11", "GUI and feature visibility", "Built React + three.js front-end (desktop via Tauri); 5-step flow; waterfall, PSD, constellation on first view.",
  "D, I", "All three spectral features visible on first load; any clause ≤ 2 clicks; 100 MB file interactive < 2 s."),
 ("R-12", "Automated", "Autopilot from raw file to header / payload; Expert overrides any stage.", "D, T", "One click; full chain < 10 s for " + E("6") + " samples."),
 ("R-13", "GNU Radio, Python, C++", "Python orchestration; C++ kernels; GNU Radio for C5 output and as oracle.", "I", "Each used for a stated reason."),
 ("R-14", "Output for designated sensors", "Certificate, SigMF, bits, CSV, recipe file, compiled receiver (C5).", "T, D", "Compiled receiver bit-exact on source recording (§5 C5)."),
 ("R-15", "Signal type triage (first step of (i))", "Before decoding, classify the file's content as digital data, analog voice, carrier / Morse or noise from spectral features (occupied band, symbol-rate line, frame-to-frame level and spectral change, single-line energy); only digital data enters the decode chain; mixed captures split by the Scene step.",
  "T", "Correct class on ≥ 95 % of 400 labelled files (synthetic + real: KiwiSDR voice and data, SatNOGS audio); verdict < 1 s per file; files too short for a verdict say so."),
]
table([["ID", "PS clause", "Design", "Verify", "Acceptance criterion"]] + [list(r) for r in reqs],
      [11 * mm, 25 * mm, 70 * mm, 11 * mm, 63 * mm], style=tiny)
story.append(PageBreak())

# ============================================================ 5. USPs
P("5. Pillar B - the USPs", h1)
P("<b>Crown innovations</b> answer sentences in the PS and are claimed by none of the 43 competitor READMEs. Six are new in this plan "
  "(C2-C7); C1 and C8 evolve v1 ideas. Each card states honest limits, real-data validation, priority class (P1 = minimum winning "
  "configuration, P2 = from reserve, P3 = bench prototype and roadmap) and technology readiness (TRL, NASA NPR 7123.1).")

def card(name, prio, trl, pw, rows_):
    head = [Paragraph(f'<font color="white"><b>{name}</b></font>', small), Paragraph(f'<font color="white">{prio} &middot; TRL {trl} &middot; {pw} pw</font>', small)]
    data = [head] + [[Paragraph(f"<b>{k}</b>", small), Paragraph(v, small)] for k, v in rows_]
    t = Table(data, colWidths=[27 * mm, 153 * mm])
    style = [("BACKGROUND", (0, 0), (-1, 0), TEAL), ("GRID", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("BACKGROUND", (0, 1), (0, -1), LIGHT), ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#eef2f7")),
             ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]
    for i, (k, _) in enumerate(rows_, 1):
        if k == "Honest limits": style.append(("BACKGROUND", (1, i), (1, i), GOLD))
    t.setStyle(TableStyle(style))
    story.append(KeepTogether([t, Spacer(1, 6)]))

card("C1 · Proof-of-Decode and the Decode Certificate", "P1", "2 → 5", "1.5", [
 ("PS", "<i>\"This limitation reduces the accuracy and confidence of interpretation and data analysis that require detailed information.\"</i>"),
 ("Design", "Re-encode the decoded bits through the recovered chain (code → interleaver → scrambler → mapper → pulse shape), apply the estimated channel "
  "(gain, CFO, phase trajectory, timing, equaliser taps), subtract, and test the residual r. A PASS needs all four tests, with thresholds calibrated on Tiers 1-2: "
  "<b>(T1)</b> explained signal energy η = 1 − (P" + sub("r") + " − P" + sub("n") + ")/(P" + sub("x") + " − P" + sub("n") + ") ≥ η" + sub("min") + ", with noise power P" + sub("n") + " from the Sensor Twin (C4); "
  "<b>(T2)</b> residual-to-noise ratio P" + sub("r") + "/P" + sub("n") + " within ±0.2 dB; <b>(T3)</b> no cyclostationary feature at the symbol rate left in r (cyclic coherence at α = 1/T below threshold); "
  "<b>(T4)</b> pre-whitened residual white (Ljung-Box) and Gaussian (kurtosis). CRC pass rate and syndrome weight are recorded as independent bit-level corroboration."),
 ("Certificate", "SHA-256 of the input, SANJAYA version and configuration hash, full recipe, every test statistic and threshold, and the <b>near-miss alternatives</b> "
  "tested (e.g. 8PSK for QPSK, wrong roll-off, wrong interleaver period) with whether each was rejected. Ed25519 signature with an offline per-site key. Deterministic: same version + file + configuration → identical recipe."),
 ("Honest limits", "A PASS means the recipe explains the recording to the noise floor. Recipes that produce identical waveforms (for example a scrambler folded into random "
  "payload) cannot be separated by the proof; structure (frames, CRC) separates them, and the certificate reports such equivalences. At low SNR near-miss rejection weakens; "
  "the certificate lists which alternatives it could not rule out."),
 ("New because", "No competitor README claims waveform-level verification; the best claim bit-level checks (Gururaghavendra123, Venkata-Manoj, anshumanarchit)."),
 ("Built on", "Analysis-by-synthesis / successive cancellation; Gardner (IEEE SP Magazine, 1991) cyclostationarity; Ljung and Box (Biometrika, 1978); Hanley and Lippman-Hand (JAMA, 1983) rule of three."),
 ("Real validation", "PASS certificates on Meteor-M LRPT and HFDL recordings must agree with SatDump and dumphfdl decodes."),
 ("KPI", "P(PASS | wrong recipe) ≤ " + E("−4") + " (95 % upper bound: 0 false PASS in ≥ 30,000 near-miss trials); P(PASS | right recipe) ≥ 95 % at SNR ≥ 6 dB with ≥ " + E("4") + " symbols."),
])
card("C2 · Data-Sufficiency Engine and collection tasking", "P1", "2 → 4", "1.0", [
 ("PS", "<i>\"This data is often insufficient for fine grain analysis for parameter extraction such as modulation type, sampling rate, FEC, interleaving, etc.\"</i>"),
 ("Design", "Each open decision is a hypothesis set with log-evidence from calibrated likelihoods (demodulation, rank / syndrome statistics, C1 re-synthesis). Decide when the best "
  "posterior ≥ 1 − α (α = " + E("−3") + "). Otherwise measure the evidence growth rate D (nats per second, the slope of the log Bayes factor between the top two hypotheses) and predict "
  "ΔT ≈ [ln((1 − α)/α) − ln B] / D (Wald's sequential-test approximation). The result becomes a <b>tasking note</b>: centre frequency, occupied bandwidth, minimum complex sample rate "
  "(≥ 1.25 x occupied bandwidth), duration (ΔT x 1.3), minimum SNR, and the best sensor from the Twin."),
 ("Why it matters", "For methods that need error-free rows (the hard-decision rank criterion; Sicot, Houcke, Barbier, Signal Processing 2009), rows needed ≈ 2N / (1 − p)" + sup("N") + " for period N bits at bit error rate p. "
  "At p = 3 x " + E("−3") + " and 4.8 kbit/s: <b>N = 96 → 256 rows, 24.6 kbit, 5.1 s</b>; <b>N = 1,500 → 2.7 x " + E("5") + " rows, 4.1 x " + E("8") + " bits, about 23.6 hours</b>. "
  "This is why 'insufficient data' is real, why soft-decision and code-aided identification (D1) and stitching (C3) matter, and why an analyst needs to be told the number."),
 ("Honest limits", "Predictions assume the emitter keeps one mode; a mode change shows up as a collapsing evidence rate and is flagged, not extrapolated."),
 ("New because", "No competitor README estimates the data a decision needs; they print a result or UNKNOWN."),
 ("Built on", "Wald (Annals of Mathematical Statistics, 1945); Bayesian model comparison; Sicot et al. (2009) rank criterion."),
 ("KPI", "Median |ΔT" + sub("pred") + " − ΔT" + sub("actual") + "| / ΔT" + sub("actual") + " ≤ 30 % (90th percentile ≤ 60 %) on Tiers 1-2; reported on Tier 3."),
])
card("C3 · Evidence Stitching across captures, sensors and locations", "P1", "2 → 5", "1.5", [
 ("PS", "<i>\"Since the data point are recorded from different sensors and different locations, the parameters may vary. Therefore, the data available for analysis is often insufficient...\"</i>"),
 ("Design", "(1) <b>Associate</b> captures to one emitter only when recipes agree and passport distance is below threshold. (2) <b>Normalise</b> each capture with its sensor's Twin "
  "(resample to a common symbol grid, remove CFO, match gain). (3) <b>Align</b> exactly on a sync word or frame marker; otherwise search the phase per capture over the candidate period. "
  "(4) <b>Pool</b>: a code's dual space is identical in every capture, so aligned soft codeword rows are stacked into one matrix and log-likelihoods add. "
  "(5) <b>Safety</b>: C1 then runs per capture - a wrongly associated capture fails its own proof and is ejected."),
 ("Honest limits", "Without a sync marker the phase search grows with the period. Captures in different emitter modes are never pooled."),
 ("New because", "No competitor README combines captures; all are single-file."),
 ("Real validation", "One HF transmission recorded at the same time by ≥ 3 public KiwiSDRs in different countries, with GPS-timestamped IQ - literally 'different sensors and different locations'."),
 ("KPI", "Alignment loss ≤ 10 %: K captures of total length T reach within 10 % (relative) of the identification probability of one capture of length T. Association false-merge ≤ 1 %."),
])
card("C4 · Sensor Twin and network clock solution", "P1-lite / P2-full", "2 → 5 (lite)", "0.5 + 0.5", [
 ("PS", "<i>\"The analysis of signals is primarily dependent on the basic characteristics of data points selected during recording of these signals.\"</i>"),
 ("Design", "Per sensor: sample-clock error ε" + sub("s") + ", local-oscillator error, anti-alias response, noise-floor shape, IQ gain and phase imbalance, DC, clipping level, phase noise. "
  "Learned passively from signals of opportunity: standard-frequency broadcasts (atomic-referenced carriers), recognised standards (exact symbol clocks), empty bands, strong carriers. "
  "<b>Network clock solution</b>: each observation of emitter e at sensor s gives δ" + sub("es") + " = ε" + sub("e") + " + ε" + sub("s") + " (after removing Doppler: SGP4 from public TLEs for satellites; negligible at ppm level for HF sky-wave). "
  "One reference - a GPS-disciplined receiver such as a KiwiSDR, or an atomic-referenced broadcast - fixes the gauge; weighted least squares gives every sensor and emitter clock with its uncertainty."),
 ("Honest limits", "With no reference, sensor and emitter clocks cannot be separated (the network has one free offset); SANJAYA then reports relative clocks only."),
 ("Uses", "C3 normalisation; C6 emitter clocks; metadata-lie detection (declared sample rate versus anti-alias edge and symbol clocks); Twin-conditioned training data (P2)."),
 ("New because", "Competitor READMEs correct DC and IQ imbalance per file; none keeps a persistent sensor model."),
 ("KPI", "Sensor clock error within 1 ppm (1σ) of a GPS-disciplined reference; declared-vs-measured sample-rate discrepancies ≥ 0.5 % detected in ≥ 99 % of recordings containing a recognised standard."),
])
card("C5 · Recipe Compiler: from a recording to a deployable receiver", "P1", "2 → 5", "1.5", [
 ("PS", "<i>\"...the resultant data is then utilised for processing signals in the designated sensors.\"</i>"),
 ("Design", "Input: a <b>certified</b> recipe only (C1 PASS). Output (a): a GNU Radio 3.10 flowgraph using gr-digital (symbol sync, Costas loop, constellation decoder, additive scrambler, "
  "access-code correlator) and gr-fec (convolutional decoding), plus SANJAYA out-of-tree blocks where the core has none (Reed-Solomon, generic de-interleaver, CRC-n, schema-driven frame parser). "
  "(b): a versioned recipe file (JSON, SigMF-compatible namespace) for NTRO's own receivers. (c): a recipe-matched detector - coherent gain ≈ 10 log" + sub("10") + " L dB for L known symbols "
  "(≈ 15 dB for a 32-symbol sync word) plus incoherent integration across frames."),
 ("Release gate", "The compiled receiver, run on the source recording, must reproduce SANJAYA's decoded bits exactly before it can be exported."),
 ("Honest limits", "Chains with no GNU Radio or SANJAYA block (rare) export the recipe file only."),
 ("New because", "No competitor README generates a receiver; outputs end in reports or JSON."),
 ("KPI", "100 % bit-exact on source recordings; live frame-error-rate curve on the hardware-in-the-loop rig within 1 dB of the offline decoder's."),
])
card("C6 · Emitter Passport and Counter Chronology", "P2", "2 → 4 (5 for physical traits on ADS-B)", "1.0", [
 ("PS", "<i>\"This creates a need for advanced data processing to extract the observation data.\"</i>"),
 ("Design", "Passport = recipe (exact fields) + physical traits (emitter symbol-clock error after sensor and Doppler correction, carrier offset, IQ image, phase-noise profile, "
  "turn-on transient) + protocol state (counters, sequence numbers). Recipe must match exactly; traits by Mahalanobis distance; open-set threshold → 'new emitter'. "
  "<b>Counter chronology</b>: for a b-bit counter and frame period T" + sub("f") + ", frames between captures n = ((c" + sub("2") + " − c" + sub("1") + ") mod 2" + sup("b") + ") + k·2" + sup("b") + ", "
  "k = round[(Δt/T" + sub("f") + " − ((c" + sub("2") + " − c" + sub("1") + ") mod 2" + sup("b") + ")) / 2" + sup("b") + "]; duty cycle = n·T" + sub("f") + "/Δt; equal counters at two sensors give a common epoch."),
 ("Honest limits", "Physical traits drift with temperature and ageing; passports carry uncertainty and are re-anchored by recipe and counters."),
 ("Real validation", "ADS-B at 1090 MHz: every aircraft broadcasts its 24-bit ICAO address - thousands of physical transmitters with self-declared identity, receivable across India with an RTL-SDR. "
  "(ADS-B is pulse-position modulation: used only to validate physical traits.)"),
 ("KPI", "Closed-set re-identification ≥ 90 % top-1 among ≥ 50 emitters; open-set AUROC ≥ 0.95; chronology exact on the rig's counters."),
])
card("C7 · WAV-Lifting: undoing the receiver's audio chain", "P3", "2 → 4", "1.0", [
 ("PS", "<i>\"The data saved as .IQ and .wav have different parameters ... The spectral relationship from training data containing both .IQ and .wav formats can be utilised...\"</i>"),
 ("Design", "Classify the .wav: stereo IQ, real IF, or receiver audio. For linear receivers (SSB / AM / CW audio) estimate sideband orientation, audio offset, passband edges and AGC trajectory, then "
  "rebuild complex baseband (analytic signal + shift), keeping sideband and spectral inversion as hypotheses."),
 ("Honest limits", "FM demodulation discards RF phase: for FM audio SANJAYA analyses the demodulated message (e.g. AFSK / FSK data) and marks IQ-only features unavailable."),
 ("Real data", "KiwiSDR: two of its four channels on one frequency, one GPS-timestamped IQ and one USB audio, recorded simultaneously. SatNOGS archive: demodulated audio plus decoded frames (open API, CC BY-SA); lossy audio treated as a known impairment."),
 ("KPI", "Recipe agreement IQ vs lifted WAV ≥ 95 % on paired KiwiSDR recordings (linear chains)."),
])
card("C8 · Proof-gated Learning Flywheel (on-premises)", "P3", "2 → 4", "1.0", [
 ("PS", "<i>\"The spectral relationship from training data ... can be utilised for identifying signal parameters and carry out deeper analysis.\"</i>"),
 ("Design", "Only C1 PASS results with margin become labels. Scheduled fine-tuning of the small models; split-conformal recalibration on a fresh calibration split; prototype and passport library growth."),
 ("Safeguards", "Frozen golden set never trained on; automatic rollback if golden accuracy drops by more than 1 point; per-class quotas against drift toward easy signals; active-learning queue for "
  "NOVEL and FAIL cases; model files inherit the data's classification; no network."),
 ("Honest limits", "Self-training only reinforces what the system can already prove; genuinely new signal types still need an analyst (few-shot teach)."),
 ("Built on", "Wireless foundation models and few-shot adaptation: IQFM (arXiv 2506.06718), EMind (2508.18785), Radio-FM (2608.05793), RFPrompt (2605.03279); Angelopoulos and Bates (arXiv 2107.07511)."),
 ("KPI", "Golden-set accuracy non-decreasing over ≥ 3 rounds; admitted-label error bounded by the C1 false-PASS bound."),
])
P("Depth USPs - the strongest coding layer in the field", h2)
table([["USP", "What", "Class", "Basis"],
       ["D1 Soft joint coding engine", "Interleaver + code jointly from soft LLRs; rank-profile plot; peeling of concatenated codes; open-set LDPC for n ≤ 1,024 (P3).", "P1 (open-set P3)",
        "Valembois 2001; Marazin, Gautier, Burel 2011; Sicot et al. 2009; arXiv 1501.03715; arXiv 2601.15903; DCN 2026 (LDPC)"],
       ["D2 Blind scrambler recovery", "Additive and self-synchronising LFSRs; Berlekamp-Massey on idle runs; standard library.", "P1", "Cluzeau (IEEE Trans. Computers, 2007); Massey 1969; IET Comms 2026"],
       ["D3 Bit-Lens with CRC solving", "Aligned raster, entropy map, counters, length fields; any CRC polynomial solved in GF(2); schema export.", "P1", "Sensors 2024 (frame sync); Emp. SE 2026 (format inference)"],
       ["D4 Scene + successive cancellation", "OS-CFAR scene; proven emitters subtracted; buried emitters revealed and decoded.", "P2", "SIC theory; CSRD2025; ZoomSpec"],
       ["D5 Signal Genome + back-solving", "~30 named standards; true sample rate and sensor clock from a matched standard.", "P2", "Public standards"],
       ["D6 HF robustness", "Watterson channel (ITU-R F.1487) emulated in software and on the rig; fractionally-spaced equaliser; real HF via KiwiSDR.", "P2", "Watterson, Juroshek, Bensema 1970"],
       ["D7 Trust layer", "Calibrated probabilities, split-conformal sets (P1); open-set and few-shot teach (P2).", "P1 / P2", "Angelopoulos &amp; Bates 2021; arXiv 2605.26600"]],
      [34 * mm, 78 * mm, 20 * mm, 48 * mm])
P("Deliberately not doing: LLM chat interfaces (3 of 43 READMEs have one; a liability for an air-gapped user), cloud and login, black-box-only deep learning.", small)
story.append(PageBreak())

# ============================================================ 6. INNOVATION GAP
P("6. The High-Innovation Gap - where SANJAYA wins", h1)
P("<i>Bars: number of the 43 competitor READMEs claiming each capability (keyword search + manual reading, snapshot 26 Sep 2026).</i>", small)
bars = [("Loader + PSD + waterfall + constellation", 40), ("PSK/QAM/FSK demodulation", 28), ("Fixed-catalogue Viterbi + RS", 25),
        ("ML modulation classifier", 22), ("UNKNOWN / provenance labels", 20), ("GF(2) rank interleaver ID (hard)", 6), ("Multi-signal detection", 6),
        ("Real over-the-air capture", 3), ("CRC library sweep", 2), ("Protocol profiles", 1)]
ours = ["C1 Proof-of-Decode", "C2 Data-Sufficiency Engine", "C3 Evidence Stitching", "C4 Sensor Twin + clock network", "C5 Recipe Compiler",
        "C6 Emitter Passport + Chronology", "C7 WAV-Lifting", "C8 Proof-gated Flywheel", "D2 Blind scrambler ID", "D4 Successive cancellation"]
rowh, top = 4.2 * mm, 6 * mm
dh = top + (len(bars) + len(ours) + 2) * rowh + 7 * mm
d = Drawing(W, dh)
x0, bw = 70 * mm, 100 * mm
y = dh - top
d.add(String(0, y + 2, "Crowded: many competitors claim it", fontName="Arial-Bold", fontSize=8, fillColor=NAVY))
y -= rowh
for name, n in bars:
    d.add(String(x0 - 3, y + 1.2, name, fontName="Arial", fontSize=7.1, fillColor=colors.HexColor("#333333"), textAnchor="end"))
    d.add(Rect(x0, y, bw * n / 43, rowh - 1.4, fillColor=colors.HexColor("#b9b2a3"), strokeColor=None))
    d.add(String(x0 + bw * n / 43 + 2, y + 1.2, f"{n}/43", fontName="Arial", fontSize=7, fillColor=colors.HexColor("#555555")))
    y -= rowh
y -= rowh * 0.4
d.add(Line(0, y + rowh * 0.7, W, y + rowh * 0.7, strokeColor=ACCENT, strokeWidth=0.8, strokeDashArray=[3, 2]))
d.add(String(0, y - 1, "Empty: claimed by none of the 43", fontName="Arial-Bold", fontSize=8, fillColor=ACCENT))
y -= rowh
for name in ours:
    d.add(String(x0 - 3, y + 1.2, name, fontName="Arial-Bold", fontSize=7.1, fillColor=TEAL, textAnchor="end"))
    d.add(Rect(x0, y, 1.2, rowh - 1.4, fillColor=ACCENT, strokeColor=None))
    d.add(String(x0 + 4, y + 1.2, "0/43", fontName="Arial-Bold", fontSize=7, fillColor=ACCENT))
    y -= rowh
d.add(Line(x0, 3 * mm, x0 + bw, 3 * mm, strokeColor=GREY))
for k in (0, 10, 20, 30, 40):
    d.add(String(x0 + bw * k / 43, 0, str(k), fontName="Arial", fontSize=6.5, fillColor=colors.grey, textAnchor="middle"))
story.append(d)
story.append(Spacer(1, 3))
P("Head-to-head with the three strongest competitors (repos.pdf ranking; README claims)", h2)
Y, N, Pp = "Yes", "No", "Partial"
table([["Capability", "ShantanuSomwanshi (9.0)", "NaidhruvK (8.8)", "Gururaghavendra123 (8.6)", "SANJAYA (planned)"],
       ["PS (i)-(v) full chain", Y, Y, Y, Y],
       ["GUI", Y, "Not evident", Y, Y + " (built)"],
       ["Blind interleaver size", Y + " (hard rank)", Y + " (hard rank)", "Catalogue", Y + " (soft, joint)"],
       ["Waveform-level proof", N, N, N + " (CRC gate)", Y],
       ["Data needed for a decision", N, N, N, Y],
       ["Pools captures / sensors", N, N, N, Y],
       ["Receiver for sensors", N, N, N, Y],
       ["Real signal, full chain, independent truth", N, N, N, Y],
       ["Blind scrambler ID", N, "Fixed descrambler", N, Y],
       ["CRC solved (not looked up)", N, N, "Known CRC check", Y]],
      [48 * mm, 32 * mm, 30 * mm, 36 * mm, 34 * mm],
      extra=[("BACKGROUND", (4, 1), (4, 10), GREEN)])
callout("<b>Why this gap is durable.</b> The crown innovations depend on each other: the Flywheel needs Proof; Stitching needs the Twin and the "
        "Data-Sufficiency maths; the Passport needs Bit-Lens counters and the clock network; the Compiler needs certified recipes. "
        "Copying one idea from a deck does not reproduce the system.", bg=colors.white, border=TEAL)
story.append(PageBreak())

# ============================================================ 7. REAL DATA
P("7. Beating insufficient data with real recordings", h1)
P("<b>Inside the algorithm</b>: soft decisions, joint identification and sequential stopping need less data (C2, D1); stitching and the Twin let data be pooled (C3, C4). "
  "<b>Outside</b>: a real-data engine where every recording has truth we did not create.")
d = Drawing(W, 52 * mm)
tiers = [("Tier 1 - SANJAYA-Gen (synthetic)", "Exact truth; every PS combination incl. LDPC, diagonal and PN interleavers; optionally shaped by measured Sensor Twins."),
         ("Tier 2 - Cabled hardware-in-the-loop", "Our waveforms through real DACs, ADCs and oscillators (Pluto → coax → attenuators → RTL-SDR V4 and Pluto RX); exact truth."),
         ("Tier 3 - Real signals + independent truth", "Over-the-air; truth from open-source decoders, self-identifying broadcasts, orbital predictions and GPS timestamps."),
         ("Tier 4 - NTRO archives, on-premises", "After selection: Proof-gated Flywheel (C8); no data leaves the site.")]
for i, (a, b) in enumerate(tiers):
    yy = 2 * mm + i * 12.5 * mm
    xx = i * 8 * mm
    d.add(Rect(xx, yy, W - 12 * mm - xx, 10.5 * mm, fillColor=[LIGHT, GREEN, colors.HexColor("#d6e6ea"), GOLD][i], strokeColor=TEAL, strokeWidth=0.6))
    d.add(String(xx + 3 * mm, yy + 6.3 * mm, a, fontName="Arial-Bold", fontSize=8, fillColor=NAVY))
    d.add(String(xx + 3 * mm, yy + 2.2 * mm, b, fontName="Arial", fontSize=6.5, fillColor=colors.HexColor("#333333")))
d.add(Line(W - 4 * mm, 4 * mm, W - 4 * mm, 44 * mm, strokeColor=ACCENT, strokeWidth=1.2))
d.add(Polygon([W - 4 * mm, 49 * mm, W - 6.5 * mm, 44 * mm, W - 1.5 * mm, 44 * mm], fillColor=ACCENT, strokeColor=None))
d.add(String(W - 4 * mm, 0.5 * mm, "more real", fontName="Arial", fontSize=6.5, fillColor=ACCENT, textAnchor="middle"))
story.append(d)
story.append(Spacer(1, 3))
P("Tier 3 catalogue (facts verified against operator, maker and project documentation)", h2)
table([["Signal", "Verified parameters", "Exercises", "Independent truth", "How"],
       ["<b>Meteor-M N2-4</b> (N2-3 weaker: antenna partly deployed)", "137.9 MHz (137.1 backup); QPSK 72 kBd (80 kBd on some passes); rate-1/2 convolutional code, interleaving, Reed-Solomon over CCSDS frames",
        "Demod, Viterbi, RS, concatenation, interleaving, framing (not LDPC)", "SatDump decode", "RTL-SDR V4 + V-dipole, passes over India"],
       ["<b>HFDL</b>", "1800 Bd; BPSK 300 / QPSK 600 / 8PSK 1200-1800 bit/s; FEC and interleaving per ARINC 635", "Demod x 3 PSK orders, FEC, interleaving, CRC frames", "dumphfdl (reads recorded CF32/CS16 IQ)", "KiwiSDR IQ"],
       ["<b>STANAG 4285</b>", "1800 Hz tone, 2400 Bd; BPSK/QPSK/8PSK by rate (75-3600 bit/s); rate-1/2 K=7 code; short or long interleaving; 80-symbol preamble, 4 x 32 data + 3 x 16 probes",
        "HF fading, equaliser, FEC, interleaving", "Preamble and probe sequences from the public standard + C1 proof (payloads usually encrypted: modem layers only)", "KiwiSDR IQ"],
       ["<b>NAVTEX / SITOR-B</b>", "518 kHz; 100 Bd FSK, 170 Hz shift; time-diversity error correction", "FSK, framing", "fldigi", "KiwiSDR"],
       ["<b>AO-40-FEC satellites</b>", "FUNcube family: BPSK 1200 Bd on VHF (AO-73: 145.935 MHz); some UHF satellites use AO-40-style FEC on FSK near 437 MHz", "Concatenated RS + convolutional, interleaving, scrambling",
        "gr-satellites", "RTL-SDR; check live status on SatNOGS"],
       ["<b>QO-100 WB beacon</b> (stretch: real LDPC)", "10,491.5 MHz; DVB-S2, QPSK 1.5 MS/s, FEC 4/5 (LDPC + BCH); India within footprint", "LDPC, BCH, scrambling, framing",
        "Published beacon parameters; transport-stream CRC and continuity checks", "60-90 cm dish + PLL LNB → 741.5 MHz IF → Pluto"],
       ["<b>ADS-B</b> (C6 only)", "1090 MHz; pulse-position modulation; 24-bit ICAO address in every message", "Physical-trait passports", "Aircraft's own ICAO address (dump1090)", "RTL-SDR anywhere near air routes"],
       ["<b>AIS</b> (optional)", "161.975 / 162.025 MHz; GMSK 9600 bit/s; HDLC, NRZI, bit stuffing, CRC-16", "GMSK, framing; MMSI identities", "AIS-catcher", "Coastal sites only"]],
      [30 * mm, 52 * mm, 34 * mm, 34 * mm, 30 * mm], style=tiny)
P("Three sources of truth that need no decoder", h2)
table([["Source", "What it proves", "Used by"],
       ["<b>Multi-site KiwiSDR</b>: up to 4 channels per receiver; IQ saved with GPS timestamps (kiwirecorder 'kiwi-wav'); receivers across many countries",
        "Same transmission from different sensors and locations, time-aligned to GPS - the PS's own scenario", "C3, C4"],
       ["<b>SGP4 Doppler</b>: public TLEs predict each satellite pass's Doppler curve", "Independent physical truth for our carrier and symbol-rate estimators; residual = transmitter + sensor clock", "C4, R-02, R-03"],
       ["<b>Atomic-referenced broadcasts</b> (standard-frequency and time stations on HF)", "Absolute reference for sensor clock error", "C4"],
       ["<b>SatNOGS archive</b>: demodulated audio, waterfalls and decoded frames (open API, CC BY-SA)", "Receiver-audio recordings with decoded truth, at scale", "C7, C8"]],
      [70 * mm, 80 * mm, 30 * mm])
P("Tier 2 rig (verified specifications)", h2)
table([["Item", "Specification", "Role", "Approx. cost"],
       ["ADALM-Pluto", "325 MHz-3.8 GHz; one TX, one RX; reference ±25 ppm", "Transmitter; also a 'poor-clock' receiver", "₹20-28k"],
       ["2 x RTL-SDR Blog V4", "500 kHz-1.766 GHz; 1 ppm TCXO; HF via built-in upconverter", "'Good-clock' sensors; Meteor, ADS-B", "₹8-10k"],
       ["Attenuators (≥ 50 dB total), splitter, coax, shielding", "Conducted path only", "Two sensors fed simultaneously", "₹3-5k"],
       ["V-dipole (137 MHz); optional dish + PLL LNB", "Tier 3 reception", "Meteor; QO-100 (stretch)", "₹1-2k (+ ₹5-8k)"]],
      [40 * mm, 60 * mm, 50 * mm, 30 * mm])
callout("<b>Legal and ethics.</b> <b>Transmit</b>: conducted only - coax into ≥ 50 dB of attenuation, no antenna, shielded. Where a test signal fits it, "
        "the licence-exempt 433.05-434.79 MHz band (WPC G.S.R. 347(E), 2022: ≤ 10 mW e.r.p., ≤ 10 kHz channel bandwidth, ≤ 10 % duty cycle) is used as a "
        "second safeguard; wider test signals stay strictly conducted. <b>Receive</b>: public broadcasts only; confirm equipment and reception rules "
        "(Indian Wireless Telegraphy Act, 1933; WPC) with the institute. <b>Content</b>: payloads never decrypted or displayed; identities (ICAO, MMSI) used "
        "only as truth labels, never published. <b>KiwiSDR</b>: respect each operator's time limits and credit them.", bg=colors.white, border=NAVY)
P("<b>Data management.</b> Every capture stored as SigMF (data + metadata: UTC time, receiver, location, antenna, gain, sample rate, centre frequency, truth source), "
  "with SHA-256 checksums in a versioned manifest; synthetic sets regenerated from recorded seeds.", small)
story.append(PageBreak())

# ============================================================ 8. SYSTEM AND ASSURANCE
P("8. System, interfaces and assurance", h1)
d = Drawing(W, 60 * mm)
def box(text, x, yb, w, dark=False):
    d.add(Rect(x * mm, yb * mm, w * mm, 12 * mm, rx=3, ry=3, fillColor=NAVY if dark else colors.white, strokeColor=TEAL))
    d.add(String((x + w / 2) * mm, (yb + 4.6) * mm, text, fontName="Arial-Bold", fontSize=7, fillColor=colors.white if dark else NAVY, textAnchor="middle"))
def arrow(x1, y1, x2, y2):
    d.add(Line(x1 * mm, y1 * mm, x2 * mm, y2 * mm, strokeColor=ACCENT, strokeWidth=1.1))
    a = math.atan2(y2 - y1, x2 - x1); L = 2.4
    d.add(Polygon([x2 * mm, y2 * mm, (x2 - L * math.cos(a - 0.45)) * mm, (y2 - L * math.sin(a - 0.45)) * mm,
                   (x2 - L * math.cos(a + 0.45)) * mm, (y2 - L * math.sin(a + 0.45)) * mm], fillColor=ACCENT, strokeColor=None))
box("Sensors A, B, ...", 0, 44, 36); box("Recordings (.IQ / .wav)", 46, 44, 40); box("SANJAYA engine", 96, 44, 36, dark=True); box("Certified recipe", 142, 44, 38)
box("Collection tasking note", 0, 6, 40); box("Designated sensors: live receiver", 62, 6, 52); box("Recipe Compiler", 142, 6, 38)
arrow(36, 50, 46, 50); arrow(86, 50, 96, 50); arrow(132, 50, 142, 50)
arrow(161, 44, 161, 18); arrow(142, 12, 114, 12)
arrow(104, 44, 30, 18); arrow(14, 18, 14, 44)
for k, ln in enumerate(["Inside the engine: Proof (C1),", "Stitching (C3), Sensor Twin (C4),", "Passport (C6), Flywheel (C8)"]):
    d.add(String(112 * mm, (38 - 4.2 * k) * mm, ln, fontName="Arial-Italic", fontSize=7, fillColor=TEAL))
d.add(String(64 * mm, 26 * mm, "C2: what to record next", fontName="Arial-Italic", fontSize=6.8, fillColor=ACCENT))
d.add(String(W / 2, 0.5 * mm, "Only certified recipes compile (C5 gate); C2 closes the loop back to collection.", fontName="Arial-Italic", fontSize=7, fillColor=ACCENT, textAnchor="middle"))
story.append(d)
table([["Layer", "Technology", "Interface"],
       ["Engine", "Python 3.11 + NumPy/SciPy; C++17 (pybind11): Viterbi, LDPC min-sum, bit-packed GF(2) elimination; <i>galois</i> for GF(2" + sup("m") + ")", "Versioned local API (localhost only)"],
       ["GUI", "React + three.js front-end (built); Tauri desktop shell", "Consumes the local API; no remote origins"],
       ["Recipe", "JSON schema, semantic-versioned; SigMF-compatible namespace", "Shared by certificate, compiler and sensors"],
       ["Oracles", "AFF3CT, liquid-dsp, GNU Radio blocks; Tier-3 decoders (SatDump, gr-satellites, dumphfdl, fldigi, dump1090, AIS-catcher)", "Test harness only - not shipped"],
       ["ML", "PyTorch small encoders (&lt; 5 M parameters, CPU); split conformal", "Model files versioned with data manifests"]],
      [22 * mm, 100 * mm, 58 * mm])
P("Assurance for an intelligence user", h2)
table([["Concern", "Control", "Verified by"],
       ["Hostile input (files from untrusted sources)", "Coverage-guided fuzzing of WAV, raw-IQ and SigMF parsers; strict size and type limits; engine runs least-privilege, isolated from the UI", "≥ 24 CPU-hours fuzzing, zero crashes or hangs (T)"],
       ["Network leakage", "No network code paths at runtime; local API bound to 127.0.0.1", "Full demo in a network-isolated sandbox with packet capture: zero outbound packets (T)"],
       ["Supply chain", "Offline wheelhouse; every dependency pinned by hash; SBOM (CycloneDX) per release; signed installer", "Build from wheelhouse on a clean offline machine (D)"],
       ["Integrity of certificates", "Ed25519 key generated offline per site; private key never exported; configuration and version hashed into every certificate", "Reproduce a certificate on a second machine (T)"],
       ["Licences", "Licence register; copyleft tools used only as oracles in the harness; SANJAYA's own GNU Radio blocks released with source", "Inspection of release bundle (I)"]],
      [38 * mm, 90 * mm, 52 * mm])
story.append(PageBreak())

# ============================================================ 9. V&V
P("9. Verification and validation plan", h1)
table([["Level", "What", "Pass rule"],
       ["Unit", "Every estimator, decoder and parser, checked against oracles (AFF3CT, liquid-dsp, GNU Radio) and analytic cases", "Oracle agreement within stated tolerance"],
       ["Integration", "Full chain on Tier 1 with known truth", "Recipe exact; decoded bits exact"],
       ["System", "Tiers 1-3, including near-miss wrong hypotheses for C1", "Section 4 acceptance criteria"],
       ["Independent", "A member who did not build the module runs sealed test sets (Tier 1 seeds and Tier 2-3 captures never shown to developers)", "Numbers reported as measured, with intervals"],
       ["Operational", "Demo script on the frozen build, five rehearsals, one with an injected failure", "Under 7 minutes; fallbacks exercised"]],
      [22 * mm, 108 * mm, 50 * mm])
P("Metric definitions (pre-registered: frozen in this document before any measurement)", h2)
table([["Metric", "Definition"],
       ["SNR", "E" + sub("s") + "/N" + sub("0") + " in the occupied bandwidth, measured by the M2M4 estimator and cross-checked against the PSD."],
       ["P" + sub("id"), "Fraction of trials in which the full parameter is right (e.g. interleaver type and period). Reported with a 95 % Wilson interval; n ≥ 500 per condition (half-width ≤ 1.9 % at 0.95)."],
       ["BER", "Always labelled pre-FEC (after demodulation) or post-FEC."],
       ["False PASS", "P(PASS | recipe wrong), over deliberately wrong near-miss recipes; when zero are observed, bounded by the rule of three (3/n)."],
       ["η, ρ", "Explained signal energy and residual-to-noise ratio as defined in C1."],
       ["Alignment loss", "1 − P" + sub("id") + "(K stitched captures, total T) / P" + sub("id") + "(one capture, length T)."],
       ["ΔT error", "|ΔT" + sub("pred") + " − ΔT" + sub("actual") + "| / ΔT" + sub("actual") + ", where ΔT" + sub("actual") + " is the extra duration after which the decision actually became decisive."]],
      [26 * mm, 154 * mm])
P("Every run records code version, configuration hash, dataset manifest hash and seeds, so any number in the pitch can be reproduced on demand. "
  "A fast regression suite runs on every merge; the full bench runs nightly.", small)
story.append(PageBreak())

# ============================================================ 10. PROGRAMME
P("10. Programme: effort, capacity, gates, readiness", h1)
P("Capacity: 6 members x 25 h/week x 10 weeks = 1,500 h = <b>37.5 pw</b>. P1 is planned at 31.2 pw, leaving <b>6.3 pw (17 %) reserve</b>. "
  "P2 draws on reserve only after gate G3; P3 is bench prototypes and roadmap.")
wbs = [
 ("WP01", "Ingest and forensics (R-01)", "P1", 1.0, "DSP"), ("WP02", "Measurements, Fs back-solve (R-02, R-03)", "P1", 1.5, "DSP"),
 ("WP03", "Receivers PSK/QAM/FSK/GMSK + equaliser (R-07)", "P1", 3.0, "DSP"), ("WP04", "AMC experts, calibration, conformal (R-04, D7)", "P1", 1.5, "ML"),
 ("WP05", "FEC decoders in C++ (R-09)", "P1", 2.5, "Coding"), ("WP06", "Blind coding layer, hard → soft (R-05, R-06, D1)", "P1", 3.5, "Coding"),
 ("WP07", "Scrambler recovery (D2)", "P1", 1.0, "Protocol"), ("WP08", "Bit-Lens + CRC solving (R-10, D3)", "P1", 1.5, "Protocol"),
 ("WP09", "C1 Proof-of-Decode + certificate", "P1", 1.5, "ML"), ("WP10", "C2 Data-Sufficiency + tasking", "P1", 1.0, "ML"),
 ("WP11", "C4-lite Twin + C3 Stitching", "P1", 2.0, "Data"), ("WP12", "C5 Recipe Compiler + OOT blocks", "P1", 1.5, "Product"),
 ("WP13", "SANJAYA-Gen, bench, CI", "P1", 2.0, "Protocol"), ("WP14", "Real-data engine: rig, Meteor, multi-site KiwiSDR, HFDL, truth pipelines", "P1", 2.0, "Data"),
 ("WP15", "UI-engine integration (R-11, R-12)", "P1", 1.5, "Product"), ("WP16", "Assurance: fuzzing, isolation test, SBOM, installer", "P1", 1.5, "Product"),
 ("WP17", "Independent verification runs + KPI report", "P1", 1.0, "Protocol*"), ("WP18", "Pitch, demo, rehearsals", "P1", 1.0, "Data (lead)"), ("WP19", "Signal type triage: digital / voice / CW / noise gate (R-15)", "P1", 0.7, "ML"),
]
p1 = sum(w[3] for w in wbs)
p2 = [("C4-full, C6 Passport + chronology, D4 cancellation, D5 Genome, D6 real-HF tuning, D7 open-set", 4.0)]
p3 = [("C7 WAV-Lifting, C8 Flywheel, open-set LDPC, QO-100 real LDPC", 4.5)]
rows = [["WP", "Content", "Class", "pw", "Owner"]] + [[a, b, c, f"{dd:.1f}", e] for a, b, c, dd, e in wbs]
rows.append(["", "<b>P1 total</b>", "", f"<b>{p1:.1f}</b>", "reserve 6.3 pw"])
rows.append(["P2", p2[0][0], "P2", f"{p2[0][1]:.1f}", "from reserve after G3"])
rows.append(["P3", p3[0][0], "P3", f"{p3[0][1]:.1f}", "bench / roadmap"])
table(rows, [12 * mm, 104 * mm, 12 * mm, 12 * mm, 40 * mm],
      extra=[("BACKGROUND", (0, len(wbs) + 1), (-1, len(wbs) + 1), colors.HexColor("#e6e1d6"))])
P("<i>* The protocol lead coordinates independent verification but never verifies WP07, WP08 or WP13, which they build. "
  "Load per role (P1): DSP 5.5, Coding 6.0, Protocol 5.5, ML 4.7, Product 4.5, Data lead 5.0 pw - all within 6.25 pw each; Coding is the tightest.</i>", tiny)
assert abs(p1 - 31.2) < 1e-9
P("Gates", h2)
table([["Gate", "When", "Exit criterion"],
       ["G0", "Idea submission", "Deck from this plan; UI clip; C1 clip on a synthetic file"],
       ["G1", "End W2", "Spine decodes Tier 1 and Tier 2 files in the UI; bench and CI running"],
       ["G2", "End W4", "Blind coding core + C1 on Tiers 1-2; first Meteor decode matches SatDump"],
       ["G3", "End W6", "R-01 to R-15 pass on the bench; <b>decide P2 activation from measured reserve</b>"],
       ["G4", "End W8", "C2, C3 (multi-site real), C5 (bit-exact) complete; demo script frozen"],
       ["G5", "End W9", "Independent KPI report; feature freeze; W10 rehearsal only"]],
      [14 * mm, 26 * mm, 140 * mm])
P("Technology readiness (NASA NPR 7123.1: TRL 2 concept formulated; 4 validated in the lab; 5 validated in a relevant environment)", h2)
table([["Element", "Today", "Finale target", "Evidence at target"],
       ["C1 Proof", "2", "5", "Certificates on real Meteor and HFDL recordings agree with independent decoders"],
       ["C2 Data-Sufficiency", "2", "4", "Prediction error on Tiers 1-2"],
       ["C3 Stitching + C4-lite", "2", "5", "Multi-site KiwiSDR stitching; sensor clock versus GPS reference"],
       ["C5 Compiler", "2", "5", "Bit-exact on a real recording; live on the rig"],
       ["C6 Passport", "2", "4 (5 traits)", "Rig counters; ADS-B identities"],
       ["C7, C8", "2", "4", "Bench prototypes"],
       ["Front-end", "4", "5", "Built today with demo data; wired to the engine on real recordings"]],
      [38 * mm, 18 * mm, 26 * mm, 98 * mm])
story.append(PageBreak())

# ============================================================ 11. RISKS
P("11. Risk register", h1)
P("Likelihood (L) and consequence (C) from 1 to 5; score = L x C. Red ≥ 15, amber 8-14.")
risks = [
 ("K01", "Real signals need more data than captures hold (large interleavers)", 4, 4, "Sync-aided stitching (C3); soft methods (D1); C2 reports honestly", "P" + sub("id") + " on Tier 3 < 80 % at G3", "Coding"),
 ("K02", "Schedule overrun", 4, 4, "WBS with 17 % reserve; gates; P2/P3 descoping order", "Any WP > 25 % over at a gate", "Lead"),
 ("K03", "Demo failure at the venue", 3, 4, "Frozen build; 5 rehearsals; backup laptop; fallback per beat (§12)", "Any rehearsal failure", "Product"),
 ("K04", "False certificates", 2, 5, "Four-test proof; calibrated thresholds; near-miss testing; independent runs", "Any false PASS in bench", "ML"),
 ("K05", "RF equipment not allowed at the venue", 3, 3, "Cabled, low power; file-replay fallback", "Venue rules", "Lead"),
 ("K06", "Meteor reception poor or satellite status changes", 3, 3, "Prefer N2-4; several passes per day; HFDL and STANAG via KiwiSDR", "No clean pass by W2", "Data"),
 ("K07", "Coding lead overloaded (6.0 of 6.25 pw)", 3, 3, "Pair with ML lead on WP06; move open-set LDPC to P3", "WP06 late at G2", "Lead"),
 ("K08", "Legal or institute approval for the rig", 2, 4, "Conducted only; licence-exempt band where applicable; early approval", "No approval by W1", "Data"),
 ("K09", "Hostile or malformed files crash the engine", 2, 4, "Fuzzing; limits; isolation", "Any crash in fuzzing", "Product"),
 ("K10", "Team availability (examinations)", 3, 3, "Reserve; cross-trained pairs", "&gt; 1 member away &gt; 1 week", "Lead"),
 ("K11", "Stitching associates the wrong captures", 2, 3, "Recipe + passport association; per-capture proof ejects", "False-merge &gt; 1 %", "Data"),
 ("K12", "Dependency or licence problem", 2, 3, "Pinned wheelhouse; licence register", "Build fails offline", "Product"),
]
rows = [["ID", "Risk", "L", "C", "Score", "Mitigation", "Trigger", "Owner"]]
for r in risks: rows.append([r[0], r[1], str(r[2]), str(r[3]), str(r[2] * r[3]), r[4], r[5], r[6]])
table(rows, [10 * mm, 46 * mm, 7 * mm, 7 * mm, 11 * mm, 55 * mm, 30 * mm, 14 * mm], style=tiny,
      extra=[("BACKGROUND", (4, i), (4, i), RED if r[2] * r[3] >= 15 else GOLD if r[2] * r[3] >= 8 else GREEN) for i, r in enumerate(risks, 1)])

# ============================================================ 12. DEMO
P("12. Demonstration with a fallback for every beat", h1)
table([["Time", "Beat", "What judges see", "Fallback"],
       ["0:00", "The problem", "A real Meteor-M recording: a noisy waterfall.", "Recorded screen video"],
       ["0:30", "Autopilot on real data", "Every layer recovered; matches SatDump.", "Cached results, same UI"],
       ["1:40", "Proof", "Ridge sinks into the noise; certificate prints; a near-miss (8PSK) is rejected on screen.", "Offline; no hardware needed"],
       ["2:30", "Insufficient data", "0.4 s capture → tasking note; multi-site KiwiSDR captures stitched → proven.", "Offline; deterministic"],
       ["3:30", "Mystery signal", "A judge chooses modulation, interleaver, code, scrambler; the rig transmits over cable; SANJAYA recovers all.", "Judge picks one of 20 sealed pre-generated files"],
       ["4:40", "Recipe Compiler", "One click: a GNU Radio receiver decodes the live cable stream.", "Throttled file-source replay"],
       ["5:40", "Passport + hidden signal", "Only if P2 delivered; otherwise skipped (demo ends by 6:00).", "Skip"],
       ["6:30", "Numbers", "Independent KPI table with confidence intervals; close on the mission sentence.", "Printed handout"]],
      [11 * mm, 30 * mm, 90 * mm, 49 * mm])
P("Questions to answer cold", h2)
table([["Question", "Answer"],
       ["How do you know it is right with no ground truth?", "Four-test waveform proof with near-miss rejection; agreement with independent decoders on real signals; bounded false-PASS rate."],
       ["How much signal do you need?", "It depends on the question; SANJAYA computes it (C2). Example: hard-rank methods need about 23.6 h for a 1,500-bit interleaver at BER 3 x " + E("−3") + "; we show our measured curve against that."],
       ["Our sensors differ.", "The Sensor Twin learns each one from signals it already hears; the clock network separates sensor and emitter clocks given one reference."],
       ["What is the maturity?", "TRL 2 today for the innovations (front-end TRL 4); targets per element in §10."],
       ["Can it run on our isolated network?", "Yes: offline installer, pinned dependencies, SBOM, zero-network test in acceptance."],
       ["Blind LDPC?", "Catalogue identification by syndrome; short-code recovery (n ≤ 1,024) as research mode; long-code blind recovery is not claimed."],
       ["Encrypted payloads?", "Recipe and frame structure recovered; payload flagged high-entropy; decryption out of scope."]],
      [52 * mm, 128 * mm])
story.append(PageBreak())

# ============================================================ 13. REFERENCES
P("13. References (verified 26 Sep 2026)", h1)
P("Research on blind identification, sensing and learning", h2)
refs = [
 ("Singh et al., 'Blind Identification of Channel Codes: A Subspace-Coding Approach', arXiv 2601.15903, 2026", "https://arxiv.org/abs/2601.15903"),
 ("'Open-set blind recognition of non-binary LDPC codes', Digital Communications and Networks, 2026", "https://doi.org/10.1016/j.dcan.2025.10.004"),
 ("Ding et al., 'Joint Blind Identification of Cyclic Codes and Synchronization Scramblers From Synchronous Scrambling Sequences of Cyclic Codes Based on Soft Decision Information', IET Communications, 2026", "https://doi.org/10.1049/cmu2.70192"),
 ("Tixier, 'Blind identification of an unknown interleaved convolutional code', arXiv 1501.03715, 2015", "https://arxiv.org/abs/1501.03715"),
 ("'Blind Recognition of Reed-Solomon Codes Based on Galois Field Fourier Transform and Reliability Verification', IEEE Communications Letters, 2023", "https://doi.org/10.1109/LCOMM.2023.3285607"),
 ("Wei et al., 'Blind Recognition of Frame Synchronization Based on Deep Learning', Sensors, 2024", "https://doi.org/10.3390/s24206767"),
 ("Hu et al., 'Scalable hierarchical protocol format inference via feature-heuristic message delimiter', Empirical Software Engineering, 2026", "https://doi.org/10.1007/s10664-026-10814-6"),
 ("Mashaal et al., 'IQFM: A Wireless Foundational Model for I/Q Streams in AI-Native 6G', arXiv 2506.06718, 2025", "https://arxiv.org/abs/2506.06718"),
 ("Luo et al., 'EMind: A Foundation Model for Multi-task Electromagnetic Signals Understanding', arXiv 2508.18785, 2025", "https://arxiv.org/abs/2508.18785"),
 ("Zhou et al., 'Radio-FM: A Foundation Model for Radio Signal Representation Learning and Its Applications', arXiv 2608.05793, 2026", "https://arxiv.org/abs/2608.05793"),
 ("Uddin et al., 'RFPrompt: Prompt-Based Expert Adaptation of the Large Wireless Model for Modulation Classification', arXiv 2605.03279, 2026", "https://arxiv.org/abs/2605.03279"),
 ("Zhao et al., 'Geometry-Aware Contrastive Learning for Few-Shot Automatic Modulation Recognition', arXiv 2605.26600, 2026", "https://arxiv.org/abs/2605.26600"),
 ("Faysal et al., 'DenoMAE: A Multimodal Autoencoder for Denoising Modulation Signals', arXiv 2501.11538, 2025", "https://arxiv.org/abs/2501.11538"),
 ("Wen et al., 'Conformal Shield: A Novel Adversarial Attack Detection Framework for Automatic Modulation Classification', arXiv 2402.17450, 2024 (conformal prediction used for attack detection)", "https://arxiv.org/abs/2402.17450"),
 ("Chang et al., 'CSRD2025: A Large-Scale Synthetic Radio Dataset for Spectrum Sensing in Wireless Communications', arXiv 2508.19552, 2025", "https://arxiv.org/abs/2508.19552"),
 ("Yang et al., 'ZoomSpec: A Physics-Guided Coarse-to-Fine Framework for Wideband Spectrum Sensing', arXiv 2604.13568, 2026", "https://arxiv.org/abs/2604.13568"),
 ("Angelopoulos and Bates, 'A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification', arXiv 2107.07511, 2021", "https://arxiv.org/abs/2107.07511"),
]
table([["#", "Reference", "Link"]] + [[str(i), t, f'<link href="{u}"><font color="#2a6f77"><u>{u}</u></font></link>'] for i, (t, u) in enumerate(refs, 1)],
      [7 * mm, 113 * mm, 60 * mm], style=tiny)
P("Foundations (DOIs verified on Crossref)", h2)
found = [
 ("Wald, 'Sequential Tests of Statistical Hypotheses', Annals of Mathematical Statistics, 1945", "10.1214/aoms/1177731118", "C2"),
 ("Ljung and Box, 'On a measure of lack of fit in time series models', Biometrika, 1978", "10.1093/biomet/65.2.297", "C1"),
 ("Gardner, 'Exploitation of spectral redundancy in cyclostationary signals', IEEE Signal Processing Magazine, 1991", "10.1109/79.81007", "C1"),
 ("Massey, 'Shift-register synthesis and BCH decoding', IEEE Trans. Information Theory, 1969", "10.1109/TIT.1969.1054260", "D2"),
 ("Cluzeau, 'Reconstruction of a Linear Scrambler', IEEE Trans. Computers, 2007", "10.1109/TC.2007.1055", "D2"),
 ("Valembois, 'Detection and recognition of a binary linear code', Discrete Applied Mathematics, 2001", "10.1016/S0166-218X(00)00353-X", "D1"),
 ("Sicot, Houcke, Barbier, 'Blind detection of interleaver parameters', Signal Processing, 2009", "10.1016/j.sigpro.2008.09.012", "C2, D1"),
 ("Marazin, Gautier, Burel, 'Blind recovery of k/n rate convolutional encoders in a noisy environment', EURASIP JWCN, 2011", "10.1186/1687-1499-2011-168", "D1"),
 ("Watterson, Juroshek, Bensema, 'Experimental Confirmation of an HF Channel Model', IEEE Trans. Communication Technology, 1970", "10.1109/TCOM.1970.1090438", "D6"),
 ("Merchant, Revay, Stantchev, Nousain, 'Deep Learning for RF Device Fingerprinting in Cognitive Communication Networks', IEEE JSTSP, 2018", "10.1109/JSTSP.2018.2796446", "C6"),
 ("Wilson, 'Probable Inference, the Law of Succession, and Statistical Inference', JASA, 1927", "10.1080/01621459.1927.10502953", "§9"),
 ("Hanley and Lippman-Hand, 'If Nothing Goes Wrong, Is Everything All Right?', JAMA, 1983", "10.1001/jama.1983.03330370053031", "C1, §9"),
]
table([["Foundation", "DOI", "Used in"]] + [[t, f'<link href="https://doi.org/{d_}"><font color="#2a6f77"><u>{d_}</u></font></link>', u] for t, d_, u in found],
      [118 * mm, 48 * mm, 14 * mm], style=tiny)
P("Standards, programme references and tools", h2)
table([["Item", "Use"],
       ["NASA NPR 7123.1 (Appendix E, TRL definitions); NASA Systems Engineering Handbook SP-2016-6105 Rev 2 (verification methods)", "§4, §10"],
       ["ITU-R F.1487 (HF channel simulation); ARINC 635 (HFDL); STANAG 4285; ITU-R M.1371 (AIS); ITU-R M.540 (NAVTEX); ETSI EN 302 307 (DVB-S2); CCSDS 131.0-B (TM coding)", "§7"],
       ["WPC G.S.R. 347(E), 2022 (433.05-434.79 MHz exemption); Indian Wireless Telegraphy Act, 1933", "§7"],
       ["SigMF; GNU Radio 3.10 (gr-digital, gr-fec); SatDump; gr-satellites; dumphfdl; fldigi; dump1090; AIS-catcher; KiwiSDR and kiwirecorder; SatNOGS network API", "§5, §7, §8"],
       ["Signal facts cross-checked against: Signal Identification Wiki (LRPT, STANAG 4285, HFDL); AMSAT and AMSAT-UK (FUNcube-1); AMSAT-DL and BATC (QO-100); Analog Devices wiki (ADALM-Pluto); RTL-SDR Blog V4 datasheet; kiwisdr.com", "§7"]],
      [150 * mm, 30 * mm])
P("<b>Open items that paper cannot close</b>: measured KPIs (after the build); SIH 2026 dates and PS clarifications (SPOC); equipment procurement; institute approval for the rig; "
  "live status of FUNcube-family satellites at the time of recording.", small)

def footer(c, doc):
    c.saveState(); c.setFont("Arial", 7.5); c.setFillColor(colors.grey)
    c.drawString(15 * mm, 9 * mm, "Project SANJAYA - winning plan v3 (review-ready) - SIH 26147 (NTRO) - internal team document")
    c.drawRightString(195 * mm, 9 * mm, f"Page {doc.page}"); c.restoreState()

doc = SimpleDocTemplate(r"D:\spacetech\winning plan 147 v3.pdf", pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                        topMargin=14 * mm, bottomMargin=16 * mm, title="Project SANJAYA - Winning Plan v3")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("ok", "findings:", len(rid), sev, "P1 pw:", p1, "v2 score:", round(tot, 2))
