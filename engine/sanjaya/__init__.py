"""SANJAYA engine. Interface conventions (PRD §6.2) are binding:

- complex baseband: complex64, full scale = 1.0
- bits: uint8 0/1, MSB-first for field values
- LLR = ln P(b=0)/P(b=1), float32 (positive favours 0); bit 0 maps to the +1 symbol level
- conv generators in octal (MSB = current input); CRCs in hex normal form; LFSRs as polynomial exponents + seed
- SNR = Es/N0 in the occupied bandwidth; u = standard uncertainty (k = 1)
"""
__version__ = "0.1.0"
