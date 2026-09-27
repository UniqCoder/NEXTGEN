"""The Recipe and the Certificate: the single schema source (PRD §6.1, §6.7).
Schema v0.1 covers the G1 vertical slice; new families are added as new Literal members."""
from typing import Literal
from pydantic import BaseModel, Field as F


class Modulation(BaseModel):
    scheme: Literal["qpsk"]
    mapping: Literal["gray"] = "gray"
    symbol_rate_hz: float = F(gt=0)
    pulse: Literal["rrc"] = "rrc"
    rolloff: float = F(ge=0.0, le=1.0)


class ConvCode(BaseModel):
    family: Literal["conv"] = "conv"
    K: int = F(ge=3, le=9)
    generators_octal: list[str]
    terminated: bool = True


class Interleaver(BaseModel):
    kind: Literal["block"] = "block"
    rows: int = F(gt=0)      # written row by row
    cols: int = F(gt=0)      # read column by column


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


class Framing(BaseModel):
    asm_hex: str                       # attached sync marker, sent uncoded at the PHY
    asm_position: Literal["phy"] = "phy"
    fields: list[Field]                # information bits of one frame, in order
    crc: Crc                           # covers every field before the crc field

    @property
    def info_bits(self) -> int:
        return sum(f.bits for f in self.fields)


class Recipe(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    sample_rate_hz: float = F(gt=0)
    modulation: Modulation
    fec: ConvCode
    interleaver: Interleaver
    scrambler: Scrambler
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
    recipe_source: Literal["search", "supplied"]
    verdict: Literal["pass", "fail"]
    layers: list[LayerVerdict]
    near_misses: list[NearMiss]
    attempts_k: int
    false_pass_bound: float | None     # None until the G5 near-miss campaign sets the per-attempt bound
    equivalences: list[str]
    analyst_overrides: list[str]
