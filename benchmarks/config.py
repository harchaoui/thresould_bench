"""
Benchmark Configuration for Threshold Signature Schemes
========================================================
Defines all benchmark parameters, schemes, curves, DKG types, and compatibility rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class SchemeType(Enum):
    """Supported signature schemes."""
    SRTS = "srts"
    FROST = "frost"
    TBLS = "tbls"
    MUSIG2 = "musig2"


class CurveType(Enum):
    """Supported elliptic curves."""
    SECP256K1 = "secp256k1"
    BLS12_381 = "bls12-381"
    RISTRETTO255 = "ristretto255"


class DKGType(Enum):
    """Supported DKG protocols."""
    PEDERSEN = "pedersen"
    FELDMAN = "feldman"
    NOT_APPLICABLE = "not_applicable"  # For MuSig2 which has no DKG


# =============================================================================
# SECTION 1 — COMPATIBILITY RULES
# =============================================================================
# Every phase must consult this before scheduling any combination.
# =============================================================================

COMPATIBILITY: Dict[str, Dict[str, Dict[str, Tuple[str, str]]]] = {
    # scheme -> curve -> dkg -> (status, reason)
    # status: "valid" | "suboptimal" | "invalid"
    
    "srts": {
        "secp256k1": {
            "feldman": ("valid", "Standard configuration"),
            "pedersen": ("valid", "Preferred DKG for SRTS"),
            "not_applicable": ("invalid", "SRTS requires DKG"),
        },
        "ristretto255": {
            "feldman": ("valid", "Standard configuration"),
            "pedersen": ("valid", "Preferred DKG for SRTS"),
            "not_applicable": ("invalid", "SRTS requires DKG"),
        },
        "bls12-381": {
            "feldman": ("suboptimal", "Schnorr scheme on pairing curve - works but not optimal"),
            "pedersen": ("suboptimal", "Schnorr scheme on pairing curve - works but not optimal"),
            "not_applicable": ("invalid", "SRTS requires DKG"),
        },
    },
    
    "frost": {
        "secp256k1": {
            "feldman": ("valid", "Standard configuration"),
            "pedersen": ("valid", "Preferred DKG for FROST"),
            "not_applicable": ("invalid", "FROST requires DKG"),
        },
        "ristretto255": {
            "feldman": ("valid", "Standard configuration"),
            "pedersen": ("valid", "Preferred DKG for FROST"),
            "not_applicable": ("invalid", "FROST requires DKG"),
        },
        "bls12-381": {
            "feldman": ("suboptimal", "Schnorr scheme on pairing curve - works but not optimal"),
            "pedersen": ("suboptimal", "Schnorr scheme on pairing curve - works but not optimal"),
            "not_applicable": ("invalid", "FROST requires DKG"),
        },
    },
    
    "musig2": {
        "secp256k1": {
            "feldman": ("invalid", "MuSig2 does not use DKG"),
            "pedersen": ("invalid", "MuSig2 does not use DKG"),
            "not_applicable": ("valid", "MuSig2 is n-of-n multisig, no DKG needed"),
        },
        "ristretto255": {
            "feldman": ("invalid", "MuSig2 does not use DKG"),
            "pedersen": ("invalid", "MuSig2 does not use DKG"),
            "not_applicable": ("valid", "MuSig2 is n-of-n multisig, no DKG needed"),
        },
        "bls12-381": {
            "feldman": ("invalid", "MuSig2 does not use DKG"),
            "pedersen": ("invalid", "MuSig2 does not use DKG"),
            "not_applicable": ("suboptimal", "MuSig2 on pairing curve - works but not optimal"),
        },
    },
    
    "tbls": {
        "secp256k1": {
            "feldman": ("invalid", "tBLS requires BLS12-381 curve"),
            "pedersen": ("invalid", "tBLS requires BLS12-381 curve"),
            "not_applicable": ("invalid", "tBLS requires DKG"),
        },
        "ristretto255": {
            "feldman": ("invalid", "tBLS requires BLS12-381 curve"),
            "pedersen": ("invalid", "tBLS requires BLS12-381 curve"),
            "not_applicable": ("invalid", "tBLS requires DKG"),
        },
        "bls12-381": {
            "feldman": ("valid", "Standard tBLS configuration"),
            "pedersen": ("suboptimal", "tBLS typically uses Feldman, Pedersen works but adds complexity"),
            "not_applicable": ("invalid", "tBLS requires DKG"),
        },
    },
}


def validate_combination(scheme: str, curve: str, dkg: str) -> Tuple[str, str]:
    """
    Validate a scheme/curve/dkg combination.
    
    Returns:
        Tuple of (status, reason) where status is "valid", "suboptimal", or "invalid"
    """
    try:
        status, reason = COMPATIBILITY[scheme][curve][dkg]
        return status, reason
    except KeyError:
        return "invalid", f"Unknown combination: {scheme}/{curve}/{dkg}"


def valid_curves_for(scheme: str) -> List[str]:
    """Return list of valid and suboptimal curves for a scheme."""
    if scheme not in COMPATIBILITY:
        return []
    curves = []
    for curve, dkg_dict in COMPATIBILITY[scheme].items():
        for dkg, (status, _) in dkg_dict.items():
            if status in ("valid", "suboptimal"):
                if curve not in curves:
                    curves.append(curve)
                break
    return curves


def valid_dkg_for(scheme: str, curve: str) -> List[str]:
    """Return list of valid and suboptimal DKG types for a scheme/curve combo."""
    if scheme not in COMPATIBILITY:
        return []
    if curve not in COMPATIBILITY[scheme]:
        return []
    dkg_types = []
    for dkg, (status, _) in COMPATIBILITY[scheme][curve].items():
        if status in ("valid", "suboptimal"):
            dkg_types.append(dkg)
    return dkg_types


def is_preferred(scheme: str, curve: str, dkg: str) -> bool:
    """Check if a combination is preferred (e.g., Pedersen for SRTS/FROST)."""
    if scheme in ("srts", "frost") and dkg == "pedersen":
        return True
    if scheme == "tbls" and curve == "bls12-381" and dkg == "feldman":
        return True
    if scheme == "musig2" and dkg == "not_applicable":
        return True
    return False


# =============================================================================
# Benchmark Configuration Dataclass
# =============================================================================

@dataclass
class BenchmarkConfig:
    """Main benchmark configuration."""
    
    # Schemes to benchmark
    schemes: List[SchemeType] = field(default_factory=lambda: [
        SchemeType.SRTS,
        SchemeType.FROST,
        SchemeType.TBLS,
        SchemeType.MUSIG2
    ])
    
    # Curves to test
    curves: List[CurveType] = field(default_factory=lambda: [
        CurveType.SECP256K1,
        CurveType.BLS12_381,
        CurveType.RISTRETTO255
    ])
    
    # DKG methods (for threshold schemes)
    dkg_methods: List[DKGType] = field(default_factory=lambda: [
        DKGType.PEDERSEN,
        DKGType.FELDMAN,
        DKGType.NOT_APPLICABLE
    ])
    
    # Scale parameters: list of (n, t) tuples
    # For MuSig2, t is ignored (always n-of-n)
    scale_params: List[Tuple[int, int]] = field(default_factory=lambda: [
        (3, 2),      # Small threshold
        (5, 3),      # Medium threshold
        (10, 6),     # Larger threshold
        (20, 11),    # High threshold
        (50, 26),    # Large scale
        (100, 51),   # Very large scale
    ])
    
    # Packet loss rate (0.0 to 1.0)
    # Default is 0.0 (no loss)
    packet_loss_rate: float = 0.0
    
    # Number of iterations for statistical significance
    iterations: int = 30
    
    # Warmup iterations (not included in results)
    warmup_iterations: int = 5
    
    # Enable memory profiling
    enable_memory_profiling: bool = True
    
    # Output directory
    output_dir: str = "benchmark_results"
    
    # Verbose output
    verbose: bool = True
    
    # Include suboptimal combinations
    include_suboptimal: bool = False
    
    # Random seed for reproducibility
    random_seed: int = 42


# Default configuration instance
DEFAULT_CONFIG = BenchmarkConfig()

# Quick benchmark config (for testing)
QUICK_CONFIG = BenchmarkConfig(
    schemes=[SchemeType.SRTS, SchemeType.FROST],
    curves=[CurveType.SECP256K1],
    scale_params=[(3, 2), (5, 3)],
    iterations=5,
    warmup_iterations=1,
    enable_memory_profiling=False
)
