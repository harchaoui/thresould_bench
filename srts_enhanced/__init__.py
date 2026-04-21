"""
SRTS Enhanced - Single-Round Threshold Schnorr Signatures
Enhanced implementation based on Shoup 2025 s4 with multi-curve support
"""

__version__ = "0.1.0"
__author__ = "SRTS Enhanced Team"

from .curves import CurveAdapter, get_curve
from .dkg import PedersenDKG, FeldmanVSS
from .schemes import SRTS, FROST, TBLS

__all__ = [
    "CurveAdapter",
    "get_curve",
    "PedersenDKG",
    "FeldmanVSS",
    "SRTS",
    "FROST",
    "TBLS",
]
