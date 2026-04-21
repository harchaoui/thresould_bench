"""
Benchmark Configuration for SRTS Enhanced
Defines all benchmark parameters, schemes, curves, and test scenarios.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
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
    SECP256R1 = "secp256r1"


class DKGType(Enum):
    """Supported DKG protocols."""
    PEDERSEN = "pedersen"
    FELDMAN = "feldman"


class NetworkMode(Enum):
    """Network simulation modes."""
    NONE = "none"  # No simulation (real hardware)
    LAN = "lan"    # Local area network (1ms latency)
    WAN = "wan"    # Wide area network (50ms latency)
    LOSSY = "lossy"  # Lossy network (1% packet loss)
    MOBILE = "mobile"  # Mobile network (100ms latency)


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
        DKGType.FELDMAN
    ])
    
    # Scale parameters: list of (n, t) tuples
    # For MuSig2, t is ignored (always n-of-n)
    scale_params: List[tuple] = field(default_factory=lambda: [
        (3, 2),      # Small threshold
        (5, 3),      # Medium threshold
        (10, 6),     # Larger threshold
        (20, 11),    # High threshold
        (50, 26),    # Large scale
        (100, 51),   # Very large scale
    ])
    
    # Batch sizes for presignature generation
    batch_sizes: List[int] = field(default_factory=lambda: [1, 10, 100, 1000])
    
    # Network simulation mode
    network_mode: NetworkMode = NetworkMode.NONE
    
    # Number of iterations for statistical significance
    iterations: int = 10
    
    # Warmup iterations (not included in results)
    warmup_iterations: int = 3
    
    # Enable memory profiling
    enable_memory_profiling: bool = True
    
    # Enable CPU profiling
    enable_cpu_profiling: bool = False
    
    # Output formats
    output_formats: List[str] = field(default_factory=lambda: [
        "json", "csv", "markdown"
    ])
    
    # Output directory
    output_dir: str = "benchmark_results"
    
    # Verbose output
    verbose: bool = True
    
    # Save individual run data
    save_raw_data: bool = True


@dataclass
class NetworkConfig:
    """Network simulation parameters."""
    
    latency_ms: float = 0.0       # Artificial latency in milliseconds
    packet_loss_rate: float = 0.0 # Packet loss probability (0.0 to 1.0)
    bandwidth_mbps: float = 0.0   # Bandwidth limit in Mbps (0 = unlimited)
    
    @classmethod
    def from_mode(cls, mode: NetworkMode) -> 'NetworkConfig':
        """Create network config from predefined mode."""
        if mode == NetworkMode.LAN:
            return cls(latency_ms=1.0, packet_loss_rate=0.0)
        elif mode == NetworkMode.WAN:
            return cls(latency_ms=50.0, packet_loss_rate=0.0)
        elif mode == NetworkMode.LOSSY:
            return cls(latency_ms=10.0, packet_loss_rate=0.01)
        else:
            return cls()


# Default configuration instance
DEFAULT_CONFIG = BenchmarkConfig()

# Quick benchmark config (for testing)
QUICK_CONFIG = BenchmarkConfig(
    schemes=[SchemeType.SRTS, SchemeType.FROST],
    curves=[CurveType.SECP256K1],
    scale_params=[(3, 2), (5, 3)],
    batch_sizes=[1, 10],
    iterations=5,
    warmup_iterations=1,
    enable_memory_profiling=False
)

# Full benchmark config (comprehensive)
FULL_CONFIG = BenchmarkConfig(
    schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.TBLS, SchemeType.MUSIG2],
    curves=[CurveType.SECP256K1, CurveType.BLS12_381, CurveType.RISTRETTO255],
    scale_params=[(3, 2), (5, 3), (10, 6), (20, 11), (50, 26), (100, 51)],
    batch_sizes=[1, 10, 100, 1000],
    iterations=20,
    warmup_iterations=5,
    enable_memory_profiling=True,
    enable_cpu_profiling=False
)
