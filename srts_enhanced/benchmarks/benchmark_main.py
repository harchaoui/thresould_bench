#!/usr/bin/env python3
"""
Main Benchmark Entry Point for SRTS Enhanced

Usage:
    # Run full benchmark suite
    python -m srts_enhanced.benchmarks.benchmark_main --all
    
    # Run quick benchmark (fewer iterations)
    python -m srts_enhanced.benchmarks.benchmark_main --quick
    
    # Run specific schemes
    python -m srts_enhanced.benchmarks.benchmark_main --schemes SRTS,FROST --curves secp256k1
    
    # Run with network simulation
    python -m srts_enhanced.benchmarks.benchmark_main --network wan
    
    # Custom configuration
    python -m srts_enhanced.benchmarks.benchmark_main --max-n 50 --iterations 20
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srts_enhanced.benchmarks.config import (
    BenchmarkConfig, SchemeType, CurveType, NetworkMode,
    QUICK_CONFIG, FULL_CONFIG
)
from srts_enhanced.benchmarks.runner import BenchmarkRunner
from srts_enhanced.benchmarks.reporter import BenchmarkReporter


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SRTS Enhanced Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                    # Run full benchmark suite
  %(prog)s --quick                  # Run quick test
  %(prog)s --schemes SRTS,FROST     # Test specific schemes
  %(prog)s --network wan            # Simulate WAN conditions
  %(prog)s --max-n 50               # Scale up to n=50
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Run full benchmark suite (comprehensive)"
    )
    mode_group.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (fewer iterations, smaller scale)"
    )
    
    # Scheme selection
    parser.add_argument(
        "--schemes",
        type=str,
        default=None,
        help="Comma-separated list of schemes to test (SRTS,FROST,TBLS,MUSIG2)"
    )
    
    # Curve selection
    parser.add_argument(
        "--curves",
        type=str,
        default=None,
        help="Comma-separated list of curves to test (secp256k1,bls12-381,ristretto255)"
    )
    
    # Scale parameters
    parser.add_argument(
        "--max-n",
        type=int,
        default=100,
        help="Maximum number of participants (default: 100)"
    )
    
    parser.add_argument(
        "--min-n",
        type=int,
        default=3,
        help="Minimum number of participants (default: 3)"
    )
    
    # Iterations
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of iterations per configuration (default: varies by mode)"
    )
    
    # Network simulation
    parser.add_argument(
        "--network",
        type=str,
        choices=["none", "lan", "wan", "lossy", "mobile"],
        default="none",
        help="Network simulation mode (default: none)"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Output directory for results (default: benchmark_results)"
    )
    
    parser.add_argument(
        "--no-memory-profile",
        action="store_true",
        help="Disable memory profiling"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Enable verbose output (default: True)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output during benchmark"
    )
    
    return parser.parse_args()


def build_config(args) -> BenchmarkConfig:
    """Build benchmark configuration from arguments."""
    
    # Start with base config
    if args.quick:
        config = QUICK_CONFIG
    elif args.all:
        config = FULL_CONFIG
    else:
        config = BenchmarkConfig()
    
    # Override schemes if specified
    if args.schemes:
        scheme_map = {
            "SRTS": SchemeType.SRTS,
            "FROST": SchemeType.FROST,
            "TBLS": SchemeType.TBLS,
            "MUSIG2": SchemeType.MUSIG2
        }
        config.schemes = [scheme_map[s.strip().upper()] for s in args.schemes.split(",")]
    
    # Override curves if specified
    if args.curves:
        curve_map = {
            "secp256k1": CurveType.SECP256K1,
            "bls12-381": CurveType.BLS12_381,
            "ristretto255": CurveType.RISTRETTO255,
            "secp256r1": CurveType.SECP256R1
        }
        config.curves = [curve_map[c.strip().lower()] for c in args.curves.split(",")]
    
    # Adjust scale parameters based on max-n
    config.scale_params = [
        (n, t) for n, t in config.scale_params
        if args.min_n <= n <= args.max_n
    ]
    
    # Ensure we have at least one scale parameter
    if not config.scale_params:
        config.scale_params = [(min(5, args.max_n), min(3, args.max_n // 2 + 1))]
    
    # Override iterations if specified
    if args.iterations:
        config.iterations = args.iterations
    
    # Set network mode
    network_map = {
        "none": NetworkMode.NONE,
        "lan": NetworkMode.LAN,
        "wan": NetworkMode.WAN,
        "lossy": NetworkMode.LOSSY,
        "mobile": NetworkMode.MOBILE
    }
    config.network_mode = network_map[args.network]
    
    # Memory profiling
    config.enable_memory_profiling = not args.no_memory_profile
    
    # Verbose output
    config.verbose = args.verbose and not args.quiet
    
    # Output directory
    config.output_dir = args.output_dir
    
    return config


def main():
    """Main entry point."""
    args = parse_args()
    
    # Build configuration
    config = build_config(args)
    
    print("\n" + "=" * 80)
    print("SRTS ENHANCED - BENCHMARK SUITE")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  Schemes: {[s.value for s in config.schemes]}")
    print(f"  Curves: {[c.value for c in config.curves]}")
    print(f"  Scale: n={config.scale_params[0][0]} to {config.scale_params[-1][0]}")
    print(f"  Iterations: {config.iterations}")
    print(f"  Network: {config.network_mode.value}")
    print(f"  Memory profiling: {'enabled' if config.enable_memory_profiling else 'disabled'}")
    print("=" * 80 + "\n")
    
    # Run benchmarks
    runner = BenchmarkRunner(config)
    results = runner.run_all()
    
    if not results:
        print("\n⚠ No benchmark results generated!")
        return 1
    
    # Generate reports
    reporter = BenchmarkReporter(results, output_dir=config.output_dir)
    report_files = reporter.generate_all()
    
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to:")
    for format_name, filepath in report_files.items():
        print(f"  {format_name.upper():10s}: {filepath}")
    
    # Print quick summary
    summary_file = report_files["summary"]
    with open(summary_file, 'r') as f:
        print("\n" + f.read())
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
