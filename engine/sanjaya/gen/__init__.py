"""SANJAYA-Gen v0 (PRD §8.2): deterministic, seeded, with taps at every layer.
Scope: the G1 vertical slice (QPSK + CC K=7 + block 48x32 + additive scrambler + CRC frames)."""
import numpy as np
from ..recipe import Recipe, Modulation, ConvCode, Interleaver, Scrambler, Crc, Field, Framing
from ..chain import encode_frames, shape, sps_of
from ..bits import crc_bits, to_bits
from ..dsp import rotate


def gen0_recipe(symbol_rate: float = 9600.0, sps: float = 8, rolloff: float = 0.35) -> Recipe:
    fields = [Field(name="counter", bits=16, kind="counter"), Field(name="length", bits=8, kind="length"),
              Field(name="payload", bits=704, kind="payload"), Field(name="crc", bits=16, kind="crc"),
              Field(name="fill", bits=18, kind="fill")]                 # 762 info + 6 tail -> 1536 coded = 48 x 32
    return Recipe(
        sample_rate_hz=symbol_rate * sps,
        modulation=Modulation(scheme="qpsk", symbol_rate_hz=symbol_rate, rolloff=rolloff),
        fec=ConvCode(K=7, generators_octal=["171", "133"]),
        interleaver=Interleaver(rows=48, cols=32),
        scrambler=Scrambler(poly_exponents=[8, 7, 5, 3, 0], seed=0xFF),
        framing=Framing(asm_hex="1ACFFC1D", fields=fields,
                        crc=Crc(width=16, poly=0x1021, init=0xFFFF)))


def build_info(recipe: Recipe, counters: np.ndarray, payload: np.ndarray) -> np.ndarray:
    """Assemble frame information bits field by field; CRC over every field before it."""
    rows = []
    for c, pl in zip(counters, payload):
        bits, crc_done = [], False
        for f in recipe.framing.fields:
            if f.kind == "counter":
                bits.append(to_bits(int(c), f.bits))
            elif f.kind == "length":
                bits.append(to_bits(pl.size // 8, f.bits))
            elif f.kind == "payload":
                bits.append(pl)
            elif f.kind == "crc":
                cr = recipe.framing.crc
                bits.append(to_bits(crc_bits(np.concatenate(bits), cr.width, cr.poly, cr.init, cr.refin, cr.refout, cr.xorout), f.bits))
                crc_done = True
            else:
                bits.append(to_bits(f.value or 0, f.bits))
        assert crc_done
        rows.append(np.concatenate(bits))
    return np.array(rows, np.uint8)


def generate(seed: int = 147, esn0_db: float = 12.0, n_frames: int = 40, guard_s: float = 0.05,
             recipe: Recipe | None = None, cfo_hz: float | None = None, gain: float = 0.3, clock_ppm: float = 0.0):
    """Returns (x complex64, recipe, truth dict, taps dict). clock_ppm: receiver sample clock error
    (+ = receiver clock fast, so each symbol spans sps*(1 + ppm*1e-6) samples of the recording)."""
    recipe = recipe or gen0_recipe()
    rng = np.random.default_rng(seed)
    fs, sps = recipe.sample_rate_hz, sps_of(recipe)
    pay_bits = next(f.bits for f in recipe.framing.fields if f.kind == "payload")
    counters = (int(rng.integers(0, 1 << 16)) + np.arange(n_frames)) % (1 << 16)
    payload = rng.integers(0, 2, (n_frames, pay_bits), dtype=np.uint8)
    info = build_info(recipe, counters, payload)
    taps = encode_frames(recipe, info)
    stream = taps["symbols"].ravel()

    guard = int(round(guard_s * fs))
    sps_rx = sps * (1 + clock_ppm * 1e-6)
    n = 2 * guard + int(np.ceil(stream.size * sps_rx))
    cfo = float(rng.uniform(-400, 400)) if cfo_hz is None else cfo_hz
    phase, delay = float(rng.uniform(0, 2 * np.pi)), float(rng.uniform(0, sps))
    clean = shape(stream, sps_rx, recipe.modulation.rolloff, n, guard + delay)
    imp = gain * rotate(clean, cfo / fs, phase)
    p_sig = float(np.mean(np.abs(imp[guard: n - guard]) ** 2))
    sigma2 = p_sig * sps / 10 ** (esn0_db / 10)                        # Es/N0 = P * sps / sigma^2
    noise = np.sqrt(sigma2 / 2) * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    x = (imp + noise).astype(np.complex64)

    truth = {"generator": "sanjaya-gen v0", "seed": seed, "esn0_db": esn0_db, "n_frames": n_frames,
             "cfo_hz": cfo, "phase_rad": phase, "delay_samples": delay, "gain": gain, "noise_var": sigma2,
             "guard_samples": guard, "first_symbol_sample": guard + delay, "counter_start": int(counters[0]),
             "clock_ppm": clock_ppm, "samples_per_symbol_actual": sps_rx}
    taps.update(info=info, clean=clean, impaired=imp)
    return x, recipe, truth, taps
