"""The Recipe and the Certificate: the single schema source (PRD §6.1, §6.7).
Schema v0.1 covers the G1 vertical slice; new families are added as new Literal members."""
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field as F


class Modulation(BaseModel):
    scheme: Literal["bpsk", "qpsk", "8psk", "16qam", "64qam", "fsk2", "fsk4", "fsk8"]
    mapping: Literal["gray"] = "gray"
    symbol_rate_hz: float = F(gt=0)
    pulse: Literal["rrc"] = "rrc"
    rolloff: float = F(ge=0.0, le=1.0)
    # FSK only (non-coherent tone bank, no pulse shaping): spacing between adjacent tones, Hz.
    # rolloff/pulse are unused for fsk* schemes (kept required for schema simplicity; pass 0.0/"rrc").
    fsk_tone_spacing_hz: float | None = F(default=None, gt=0)


class ConvCode(BaseModel):
    family: Literal["conv"] = "conv"
    K: int = F(ge=3, le=9)
    generators_octal: list[str]
    terminated: bool = True


class RSCode(BaseModel):
    """Reed-Solomon over GF(2^m), narrow-sense (roots alpha^1..alpha^(n-k)), corrects t = (n-k)//2 symbol
    errors. n <= 2^m - 1; n < 2^m - 1 is a shortened code (info_bits = k*m exactly)."""
    family: Literal["rs"] = "rs"
    n: int = F(gt=0)
    k: int = F(gt=0)
    m: int = F(ge=3, le=10)


class ConcatCode(BaseModel):
    """Serial concatenation: RS outer code protects the conv inner code's residual errors after Viterbi
    decode. info -> RS encode -> conv encode -> ... -> Viterbi decode -> RS decode -> info."""
    family: Literal["concat"] = "concat"
    outer: RSCode
    inner: ConvCode


class LDPCCode(BaseModel):
    """Regular LDPC over GF(2): H (m x n, k = n - m) as m row bitmasks (bit j = column j), decoded by
    log-domain min-sum belief propagation. Reference-grade, not a standard (no optimised H construction)."""
    family: Literal["ldpc"] = "ldpc"
    n: int = F(gt=0)
    m: int = F(gt=0)
    h_rows: list[int]
    max_iters: int = F(default=50, gt=0)


FEC = Annotated[Union[ConvCode, RSCode, ConcatCode, LDPCCode], F(discriminator="family")]


class Interleaver(BaseModel):
    kind: Literal["block", "diagonal", "random"] = "block"
    rows: int = F(gt=0)      # written row by row
    cols: int = F(gt=0)      # read column by column ('block'); matrix shape ('diagonal'); size = rows*cols ('random')
    seed: int | None = None  # required for 'random' (deterministic PRNG permutation)


class Scrambler(BaseModel):
    kind: Literal["additive"] = "additive"
    position: Literal["post_fec"] = "post_fec"
    poly_exponents: list[int]          # e.g. CCSDS x^8+x^7+x^5+x^3+1 -> [8, 7, 5, 3, 0]
    seed: int
    reset: Literal["per_frame"] = "per_frame"


class Crc(BaseModel):
    width: int
    poly: int                          # hex normal form
    init: int
    refin: bool = False
    refout: bool = False
    xorout: int = 0


class Field(BaseModel):
    name: str
    bits: int = F(gt=0)
    kind: Literal["counter", "length", "payload", "crc", "fill"]
    value: int | None = None           # constant value of a fill field (MSB-first); None = zeros


class Framing(BaseModel):
    asm_hex: str                       # attached sync marker, sent uncoded at the PHY
    asm_position: Literal["phy"] = "phy"
    fields: list[Field]                # information bits of one frame, in order
    crc: Crc | None = None             # covers every field before the crc field

    @property
    def info_bits(self) -> int:
        return sum(f.bits for f in self.fields)


class Recipe(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    sample_rate_hz: float = F(gt=0)
    modulation: Modulation
    fec: FEC
    interleaver: Interleaver
    scrambler: Scrambler | None = None
    framing: Framing


class LayerVerdict(BaseModel):
    layer: Literal["phy", "coding", "structure"]
    verdict: Literal["pass", "fail", "not_determinable"]
    reason: str | None = None
    stats: dict[str, float]
    thresholds: dict[str, float]
    calibration_id: str


class NearMiss(BaseModel):
    name: str
    layer: Literal["phy", "coding", "structure"]
    rejected: bool
    failed: list[str]                  # which layers failed under the near-miss


class CertificateBody(BaseModel):
    """Everything here is deterministic for (engine version, file, configuration) (NFR-06)."""
    engine_version: str
    config_hash: str
    input_sha256: str
    recipe: Recipe
    recipe_source: Literal["search", "supplied", "stitch"]
    verdict: Literal["pass", "fail"]
    layers: list[LayerVerdict]
    near_misses: list[NearMiss]
    attempts_k: int
    false_pass_bound: float | None     # None until the G5 near-miss campaign sets the per-attempt bound
    equivalences: list[str]
    analyst_overrides: list[str]
