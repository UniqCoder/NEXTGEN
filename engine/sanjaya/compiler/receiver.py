#!/usr/bin/env python3
"""SANJAYA compiled receiver: decodes one emitter's recipe from a recording, with NumPy only.

The recipe below was recovered blind and certified by SANJAYA; this file is the Recipe Compiler's output for a
designated sensor, and needs neither SANJAYA nor SciPy. It measures the recording itself (carrier offset,
symbol clock, phase), so a different sensor with its own sample rate, clock error, tuning or an inverted
spectrum still decodes.

usage:  python receiver.py RECORDING [--fs HZ --dtype cf32_le|ci16_le]
        RECORDING: SigMF (.sigmf-data with its .sigmf-meta), WAV (2 channels = I/Q, 1 channel = receiver audio)
        or headerless IQ with --fs and --dtype. Output: one JSON line per frame on stdout, a summary on stderr."""
import json
import sys
import wave
from pathlib import Path

import numpy as np

RECIPE = None  # @@RECIPE@@  (the compiler replaces this line with the certified recipe)

SPAN = 6              # pulse half-span in symbols
VV_BLOCK = 256        # symbols per Viterbi-Viterbi phase block
ASM_ACCEPT = 0.5      # normalised sync-marker correlation needed to accept a frame
SQ2 = np.float32(np.sqrt(0.5))


# ------------------------------------------------------------------------------------------------ input
def load(path, fs=None, dtype=None):
    p = Path(path)
    if p.suffix in (".sigmf-data", ".sigmf-meta"):
        base = p.with_suffix("")
        g = json.loads(base.with_suffix(".sigmf-meta").read_text())["global"]
        dtype, fs, p = g["core:datatype"], float(g["core:sample_rate"]), base.with_suffix(".sigmf-data")
    if p.suffix.lower() == ".wav":
        with wave.open(str(p)) as w:
            fs, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
            raw = np.frombuffer(w.readframes(w.getnframes()), {2: "<i2", 4: "<i4"}[width]).astype(np.float64)
        raw = raw.reshape(-1, ch) / 2 ** (8 * width - 1)
        if ch >= 2:
            return (raw[:, 0] + 1j * raw[:, 1]).astype(np.complex64), float(fs)
        X = np.fft.fft(raw[:, 0])                                     # receiver audio -> analytic signal
        h = np.zeros(X.size)
        h[0] = 1
        h[1:(X.size + 1) // 2] = 2
        if X.size % 2 == 0:
            h[X.size // 2] = 1
        return np.fft.ifft(X * h).astype(np.complex64), float(fs)
    if fs is None or dtype is None:
        sys.exit("headerless IQ needs --fs and --dtype")
    kind, scale = {"cf32_le": ("<f4", 1.0), "ci16_le": ("<i2", 1 / 32768)}[dtype]
    v = np.fromfile(p, kind).astype(np.float32) * scale
    return (v[0::2] + 1j * v[1::2]).astype(np.complex64), float(fs)


# ------------------------------------------------------------------------------------------------ PHY
def rrc(t, b):
    t = np.asarray(t, np.float64)
    out = np.empty_like(t)
    z = np.abs(t) < 1e-9
    s = (np.abs(np.abs(4 * b * t) - 1) < 1e-9) if b > 0 else np.zeros_like(z)
    r = ~(z | s)
    tr = t[r]
    out[r] = (np.sin(np.pi * tr * (1 - b)) + 4 * b * tr * np.cos(np.pi * tr * (1 + b))) / (np.pi * tr * (1 - (4 * b * tr) ** 2))
    out[z] = 1 - b + 4 * b / np.pi
    if b > 0:
        out[s] = b / np.sqrt(2) * ((1 + 2 / np.pi) * np.sin(np.pi / (4 * b)) + (1 - 2 / np.pi) * np.cos(np.pi / (4 * b)))
    return out


def norm(sps, b):
    n = np.arange(-int(np.ceil(SPAN * sps)), int(np.ceil(SPAN * sps)) + 1)
    return float(1 / np.sqrt((rrc(n / sps, b) ** 2).sum()))


def sample_at(x, inst, sps, b):
    """Matched-filter output at fractional sample instants."""
    L = 2 * int(np.ceil(SPAN * sps)) + 1
    out = np.empty(inst.size, np.complex64)
    k = norm(sps, b)
    for i in range(0, inst.size, 1 << 15):
        tt = inst[i: i + (1 << 15)]
        idx = np.ceil(tt - SPAN * sps).astype(np.int64)[:, None] + np.arange(L)[None]
        w = rrc((idx - tt[:, None]) / sps, b) * k
        ok = (idx >= 0) & (idx < x.size)
        out[i: i + (1 << 15)] = (x[np.where(ok, idx, 0)] * np.where(ok, w, 0.0)).sum(1)
    return out


def rotate(x, f_norm):
    return (x * np.exp(2j * np.pi * f_norm * np.arange(x.size))).astype(np.complex64)


def peak(P, k):
    n = P.size
    a, b, c = np.log(P[(k - 1) % n] + 1e-30), np.log(P[k] + 1e-30), np.log(P[(k + 1) % n] + 1e-30)
    den = a - 2 * b + c
    return k + (0.5 * (a - c) / den if den != 0 else 0.0)


def cfo_power(x, fs, M=4):
    v = x.astype(np.complex128) ** M
    nfft = 1 << int(np.ceil(np.log2(4 * v.size)))
    P = np.abs(np.fft.fft(v, nfft))
    f = peak(P, int(P.argmax())) / nfft
    return float((f - 1 if f >= 0.5 else f) * fs / M)


def timing_fit(x, sps_nom, b, block_symbols=512, iters=3):
    """Block-wise Oerder-Meyr phases fitted linearly: the actual samples per symbol and the first instant."""
    n_t = np.arange(-int(np.ceil(SPAN * sps_nom)), int(np.ceil(SPAN * sps_nom)) + 1)
    h = (rrc(n_t / sps_nom, b) * norm(sps_nom, b)).astype(np.float32)
    d = (h.size - 1) // 2
    y = np.convolve(x, h)[d: d + x.size]
    p = np.abs(y.astype(np.complex128)) ** 2
    n = np.arange(p.size)
    P = sps_nom
    for _ in range(iters):
        B = int(round(block_symbols * P))
        nb = p.size // B
        s = (p[: nb * B] * np.exp(-2j * np.pi * n[: nb * B] / P)).reshape(nb, B).sum(1)
        w = np.abs(s)
        good = w > 0.3 * w.max()
        if good.sum() >= 3:
            c = (np.arange(nb)[good] + 0.5) * B
            slope = np.polyfit(c, np.unwrap(np.angle(s[good])), 1, w=w[good])[0]
            P = 1.0 / (1.0 / P + slope / (2 * np.pi))
    B = int(round(block_symbols * P))
    nb = p.size // B
    s = (p[: nb * B] * np.exp(-2j * np.pi * n[: nb * B] / P)).reshape(nb, B).sum(1)
    good = np.abs(s) > 0.3 * np.abs(s).max()
    return float(P), float((-np.angle(s[good].sum()) / (2 * np.pi) * P) % P)


def symbols(x, fs, sps_nom, b, M=4):
    cfo = cfo_power(x, fs, M)
    xc = rotate(x, -cfo / fs)
    sps, t0 = timing_fit(xc, sps_nom, b)
    k = np.arange(int(np.floor((x.size - 1 - t0) / sps)) + 1)
    ys = sample_at(xc, t0 + sps * k, sps, b)
    nb = max(1, ys.size // VV_BLOCK)
    blk = ys[: nb * VV_BLOCK].reshape(nb, VV_BLOCK).astype(np.complex128)
    thM = np.unwrap(np.angle(-np.sum(blk ** M, 1)))
    theta = np.interp(np.arange(ys.size), (np.arange(nb) + 0.5) * VV_BLOCK, thM / M)
    return (ys * np.exp(-1j * theta)).astype(np.complex64), sps, cfo


def map_qpsk(bits):
    b = np.asarray(bits, np.float32)
    return ((1 - 2 * b[..., 0::2]) + 1j * (1 - 2 * b[..., 1::2])).astype(np.complex64) * SQ2


def frame_sync(ys, asm, period):
    best = None
    for conj in (False, True):
        z = np.conj(ys) if conj else ys
        c = np.correlate(z, asm, "valid")
        energy = np.sqrt(np.convolve(np.abs(z) ** 2, np.ones(asm.size), "valid")) * np.linalg.norm(asm)
        cn = np.abs(c) / np.maximum(energy, 1e-12)
        nfold = cn.size // period
        if nfold == 0:
            sys.exit("recording shorter than one frame of this emitter")
        fold = cn[: nfold * period].reshape(nfold, period).sum(0)
        off = int(fold.argmax())
        if best is None or fold[off] > best[0]:
            best = (fold[off], conj, off, c, cn)
    _, conj, off, c, cn = best
    cand = np.arange(off, cn.size, period)
    starts = cand[(cn[cand] > ASM_ACCEPT) & (cand + period <= ys.size)]
    return conj, starts, c[starts]


# ------------------------------------------------------------------------------------------------ coding
def lfsr(poly_exponents, seed, n):
    deg = max(poly_exponents)
    taps = [deg - e for e in poly_exponents if e != deg]
    s = [(seed >> (deg - 1 - i)) & 1 for i in range(deg)]
    out = np.empty(n, np.uint8)
    for k in range(n):
        out[k] = s[-1]
        fb = 0
        for t in taps:
            fb ^= s[t - 1]
        s = [fb] + s[:-1]
    return out


def deinterleave(y, rows, cols):
    return y.reshape(*y.shape[:-1], cols, rows).swapaxes(-1, -2).reshape(y.shape)


def gen_taps(octal, K):
    v = int(octal, 8)
    return np.array([(v >> (K - 1 - i)) & 1 for i in range(K)], np.uint8)


def viterbi(llr, K, gens, terminated=True):
    n = len(gens)
    Fr, T = llr.shape[0], llr.shape[1] // n
    Lr = llr[:, : T * n].reshape(Fr, T, n)
    S = 1 << (K - 1)
    G = np.array([gen_taps(g, K) for g in gens])
    ns = np.arange(S)
    b = ns >> (K - 2)
    pred = ((ns & ((1 << (K - 2)) - 1)) << 1)[:, None] | np.arange(2)[None, :]
    reg = np.empty((S, 2, K), np.uint8)
    reg[..., 0] = b[:, None]
    for i in range(K - 1):
        reg[..., i + 1] = (pred >> (K - 2 - i)) & 1
    sgn = (1.0 - 2.0 * ((reg[:, :, None, :] & G[None, None]).sum(-1) % 2)).astype(np.float32)
    pm = np.full((Fr, S), -1e30, np.float32)
    pm[:, 0] = 0.0
    dec = np.empty((T, Fr, S), np.uint8)
    for k in range(T):
        m = pm[:, pred] + np.einsum("sbj,fj->fsb", sgn, Lr[:, k])
        c = m.argmax(-1)
        dec[k] = c
        pm = np.take_along_axis(m, c[..., None], -1)[..., 0]
        pm -= pm.max(-1, keepdims=True)
    st = np.zeros(Fr, np.int64) if terminated else pm.argmax(-1)
    u = np.empty((Fr, T), np.uint8)
    rows = np.arange(Fr)
    for k in range(T - 1, -1, -1):
        c = dec[k, rows, st]
        u[:, k] = b[st]
        st = pred[st, c]
    return u


def crc(bits, width, poly, init, refin=False, refout=False, xorout=0):
    if refin:
        bits = bits.reshape(-1, 8)[:, ::-1].ravel()
    top, mask, reg = 1 << (width - 1), (1 << width) - 1, init
    for bit in bits.tolist():
        fb = ((reg & top) != 0) ^ bit
        reg = ((reg << 1) & mask) ^ (poly if fb else 0)
    if refout:
        reg = int(f"{reg:0{width}b}"[::-1], 2)
    return reg ^ xorout


def value(bits):
    v = 0
    for x in bits.tolist():
        v = (v << 1) | int(x)
    return v


# ------------------------------------------------------------------------------------------------ decode
def decode(x, fs, R=None):
    R = R or RECIPE
    mo, fec, il, fr = R["modulation"], R["fec"], R["interleaver"], R["framing"]
    ys, sps, cfo = symbols(x, fs, fs / mo["symbol_rate_hz"], mo["rolloff"])
    asm = map_qpsk(np.unpackbits(np.frombuffer(bytes.fromhex(fr["asm_hex"]), np.uint8)))
    period = asm.size + il["rows"] * il["cols"] // 2
    conj, starts, c = frame_sync(ys, asm, period)
    z = np.conj(ys) if conj else ys
    rot = np.round(np.angle(c) / (np.pi / 2)) * (np.pi / 2)
    frames = np.stack([z[s: s + period] for s in starts]) * np.exp(-1j * rot)[:, None]
    body = frames[:, asm.size:]
    dec = (np.sign(body.real) + 1j * np.sign(body.imag)) * SQ2              # decision-directed amplitude / noise
    amp = float(np.real(np.vdot(dec.ravel(), body.ravel())) / dec.size)
    sigma2 = float(np.mean(np.abs(body - amp * dec) ** 2))
    scale = np.float32(2 * np.sqrt(2) * amp / sigma2)
    llr = np.empty((body.shape[0], 2 * body.shape[1]), np.float32)
    llr[:, 0::2], llr[:, 1::2] = scale * body.real, scale * body.imag
    sc = R.get("scrambler")
    if sc:
        llr *= (1.0 - 2.0 * lfsr(sc["poly_exponents"], sc["seed"], llr.shape[1]))[None].astype(np.float32)
    llr = deinterleave(llr, il["rows"], il["cols"])
    u = viterbi(llr, fec["K"], fec["generators_octal"], fec["terminated"])
    info = u[:, : u.shape[1] - (fec["K"] - 1 if fec["terminated"] else 0)]
    out = []
    cr = fr.get("crc")
    for i, row in enumerate(info):
        pos, fields, ok = 0, {}, None
        for f in fr["fields"]:
            seg = row[pos: pos + f["bits"]]
            if f["kind"] == "crc" and cr:
                ok = value(seg) == crc(row[:pos], cr["width"], cr["poly"], cr["init"], cr["refin"], cr["refout"], cr["xorout"])
            fields[f["name"]] = np.packbits(seg).tobytes().hex() if f["kind"] == "payload" else value(seg)
            pos += f["bits"]
        out.append({"frame": i, "crc_ok": ok, "fields": fields, "info_hex": np.packbits(row).tobytes().hex(),
                    "info_bits": int(row.size)})
    return out, {"frames": len(out), "crc_ok": sum(1 for o in out if o["crc_ok"]), "cfo_hz": round(cfo, 2),
                 "symbol_rate_hz": round(fs / sps, 4), "inverted": bool(conj)}


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    opt = {argv[i]: argv[i + 1] for i in range(1, len(argv) - 1, 2)}
    x, fs = load(argv[0], float(opt["--fs"]) if "--fs" in opt else None, opt.get("--dtype"))
    frames, summary = decode(x, fs)
    for f in frames:
        print(json.dumps(f))
    print(json.dumps(summary), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
