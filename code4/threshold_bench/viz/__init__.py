# viz
"""
Threshold Signature Benchmark Visualization Package

This package provides comprehensive visualization tools for analyzing
threshold signature scheme benchmark results across multiple dimensions:
- Scheme comparison (SRTS, FROST, TBLS, MuSig2)
- Curve analysis (secp256k1, bls12-381, ristretto255)
- Network resilience (packet loss degradation)
- DKG setup methods (Feldman vs Pedersen)
- Scale analysis (n=3 to n=100)
"""

from .data_loader import BenchmarkDataLoader, load_benchmark_data
from .plot_schemes import SchemeComparator
from .plot_network import NetworkAnalyzer
from .main import VisualizationPipeline

__version__ = '1.0.0'
__author__ = 'Engineering Team'

__all__ = [
    'BenchmarkDataLoader',
    'load_benchmark_data',
    'SchemeComparator',
    'NetworkAnalyzer',
    'VisualizationPipeline',
]
