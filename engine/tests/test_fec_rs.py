"""PS clause (iv): Reed-Solomon FEC through the full known-recipe chain (encode -> channel -> decode)."""
from sanjaya.recipe import Recipe, Modulation, RSCode, Interleaver, Scrambler, Crc, Field, Framing
from sanjaya.gen import generate
from sanjaya.pipeline import frontend, unwrap


def rs_recipe() -> Recipe:
    m, n, k = 6, 63, 51                                            # t = 6 symbol errors correctable
    fields = [Field(name="counter", bits=16, kind="counter"), Field(name="length", bits=8, kind="length"),
              Field(name="payload", bits=254, kind="payload"), Field(name="crc", bits=16, kind="crc"),
              Field(name="fill", bits=12, kind="fill")]             # 306 = k * m
    return Recipe(sample_rate_hz=9600.0 * 8, modulation=Modulation(scheme="qpsk", symbol_rate_hz=9600.0, rolloff=0.35),
                  fec=RSCode(n=n, k=k, m=m), interleaver=Interleaver(rows=18, cols=21),   # 378 = n * m
                  scrambler=Scrambler(poly_exponents=[8, 7, 5, 3, 0], seed=0xFF),
                  framing=Framing(asm_hex="1ACFFC1D", fields=fields, crc=Crc(width=16, poly=0x1021, init=0xFFFF)))


def test_rs_decodes_bit_exact_with_channel_noise():
    x, r, truth, taps = generate(recipe=rs_recipe(), esn0_db=9.0, n_frames=20)
    fe = frontend(x, r)
    uw = unwrap(fe, r)
    assert len(fe.starts) == truth["n_frames"] and uw.crc_ok.all()
    assert (uw.info == taps["info"]).all()
