#!/usr/bin/env python3
"""
Comprehensive Benchmark Suite for SRTS Enhanced
===============================================

This script runs a complete benchmark analysis covering:
- All signature schemes (SRTS, FROST, TBLS, MuSig2)
- DKG comparison (Pedersen vs Feldman)
- Multiple curves (secp256k1, BLS12-381, ristretto255, ed25519, ed448)
- Network conditions (LAN, WAN, LOSSY, MOBILE, SATELLITE)
- Scale parameters (n=3 to n=100)
- Batch operations and stress testing
- Theoretical property analysis and communication costs

Usage:
    python -m srts_enhanced.benchmarks.comprehensive_benchmark
    
Or with options:
    python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 1 --output results/
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.config import (
    BenchmarkConfig, SchemeType, CurveType, DKGType, 
    NetworkMode, NetworkConfig
)
from benchmarks.runner import BenchmarkRunner
from benchmarks.reporter import BenchmarkReporter
from benchmarks import plot_results
from benchmarks.scheme_analysis import SchemePropertyAnalyzer


class ComprehensiveBenchmark:
    """
    Comprehensive benchmark execution engine.
    
    Implements the full validation plan across all dimensions.
    """
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.all_results = []
        self.metadata = {
            "start_time": datetime.now().isoformat(),
            "version": "2.0",
            "phases_completed": []
        }
        
    def run_phase_0_theoretical_analysis(self):
        """
        Phase 0: Theoretical Analysis
        
        Generate property comparison matrix, DKG comparison, and communication costs.
        This is a static analysis phase that doesn't require actual crypto operations.
        """
        print("\n" + "="*80)
        print("PHASE 0: THEORETICAL ANALYSIS")
        print("="*80)
        
        analyzer = SchemePropertyAnalyzer()
        
        # Generate property matrix
        print("\nGenerating scheme property comparison matrix...")
        property_md = analyzer.generate_property_matrix()
        print(property_md)
        
        # Generate communication cost table
        print("\nGenerating communication cost analysis...")
        comm_md = analyzer.generate_communication_table(scales=[5, 10, 20, 50])
        print(comm_md)
        
        # Calculate specific costs for different n,t combinations
        print("\nDetailed Communication Costs:")
        print("-" * 80)
        test_cases = [(5, 3), (10, 6), (20, 11), (50, 26)]
        
        header = f"{'(n,t)':<12} {'DKG R1':<15} {'DKG R2':<15} {'Presign':<15} {'Sign':<15} {'Total':<15}"
        print(header)
        print("-" * len(header))
        
        for n, t in test_cases:
            costs = analyzer.calculate_communication_costs(n, t)
            row = (f"({n},{t})".ljust(12) + 
                   f"{costs['dkg_r1_bytes']:,}".ljust(15) +
                   f"{costs['dkg_r2_bytes']:,}".ljust(15) +
                   f"{costs['presign_r1_bytes']:,}".ljust(15) +
                   f"{costs['sign_broadcast_bytes']:,}".ljust(15) +
                   f"{costs['total_protocol_bytes']:,}".ljust(15))
            print(row)
        
        # Save comprehensive report
        report_file = analyzer.save_report(str(self.output_dir))
        print(f"\n✓ Saved detailed analysis to {report_file}")
        
        self.metadata["phases_completed"].append("phase0_theoretical")
        return [{"phase": "phase0_theoretical", "status": "completed"}]
    
    def run_phase_1_baseline(self):
        """
        Phase 1: Baseline Performance
        
        Test all schemes with secp256k1, varying n, no network simulation.
        Compare Pedersen vs Feldman DKG.
        """
        print("\n" + "="*80)
        print("PHASE 1: BASELINE PERFORMANCE")
        print("="*80)
        
        config = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.TBLS, SchemeType.MUSIG2],
            curves=[CurveType.SECP256K1, CurveType.BLS12_381],  # TBLS needs BLS
            dkg_methods=[DKGType.PEDERSEN, DKGType.FELDMAN],
            scale_params=[(3, 2), (5, 3), (10, 6), (20, 11)],
            network_mode=NetworkMode.NONE,
            iterations=20,
            warmup_iterations=5,
            enable_memory_profiling=True,
            verbose=True
        )
        
        results = self._run_config_with_dkg_comparison(config, "phase1_baseline")
        self.metadata["phases_completed"].append("phase1_baseline")
        return results
    
    def run_phase_2_curves(self):
        """
        Phase 2: Curve Comparison
        
        Evaluate all supported curves with fixed scale.
        """
        print("\n" + "="*80)
        print("PHASE 2: CURVE COMPARISON")
        print("="*80)
        
        # Schnorr schemes on various curves
        config_schnorr = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.MUSIG2],
            curves=[
                CurveType.SECP256K1,
                CurveType.RISTRETTO255,
                # Add ed25519 and ed448 if available
            ],
            dkg_methods=[DKGType.PEDERSEN],
            scale_params=[(10, 6)],  # Fixed medium scale
            network_mode=NetworkMode.NONE,
            iterations=20,
            warmup_iterations=5,
            verbose=True
        )
        
        # TBLS on BLS12-381 only
        config_tbls = BenchmarkConfig(
            schemes=[SchemeType.TBLS],
            curves=[CurveType.BLS12_381],
            dkg_methods=[DKGType.PEDERSEN],
            scale_params=[(10, 6)],
            network_mode=NetworkMode.NONE,
            iterations=20,
            warmup_iterations=5,
            verbose=True
        )
        
        results = []
        results.extend(self._run_config(config_schnorr, "phase2_curves_schnorr"))
        results.extend(self._run_config(config_tbls, "phase2_curves_tbls"))
        
        self.metadata["phases_completed"].append("phase2_curves")
        return results
    
    def run_phase_3_network(self):
        """
        Phase 3: Network Impact Analysis
        
        Quantify effects of different network conditions.
        """
        print("\n" + "="*80)
        print("PHASE 3: NETWORK IMPACT ANALYSIS")
        print("="*80)
        
        network_modes = [
            NetworkMode.LAN,
            NetworkMode.WAN,
            NetworkMode.LOSSY,
            NetworkMode.MOBILE
        ]
        
        results = []
        for net_mode in network_modes:
            config = BenchmarkConfig(
                schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.TBLS],
                curves=[CurveType.SECP256K1, CurveType.BLS12_381],
                dkg_methods=[DKGType.PEDERSEN],
                scale_params=[(10, 6), (20, 11)],
                network_mode=net_mode,
                iterations=30,  # Higher iterations for variance
                warmup_iterations=5,
                verbose=True
            )
            
            phase_name = f"phase3_network_{net_mode.value}"
            results.extend(self._run_config(config, phase_name))
        
        self.metadata["phases_completed"].append("phase3_network")
        return results
    
    def run_phase_4_dkg_deepdive(self):
        """
        Phase 4: DKG Deep Dive
        
        Comprehensive Pedersen vs Feldman comparison.
        """
        print("\n" + "="*80)
        print("PHASE 4: DKG DEEP DIVE")
        print("="*80)
        
        config = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.TBLS],
            curves=[CurveType.SECP256K1, CurveType.BLS12_381],
            dkg_methods=[DKGType.PEDERSEN, DKGType.FELDMAN],
            scale_params=[(3, 2), (5, 3), (10, 6), (20, 11), (50, 26)],
            network_mode=NetworkMode.NONE,
            iterations=20,
            warmup_iterations=5,
            verbose=True
        )
        
        results = self._run_config_with_dkg_comparison(config, "phase4_dkg_analysis")
        self.metadata["phases_completed"].append("phase4_dkg")
        return results
    
    def run_phase_5_stress(self):
        """
        Phase 5: Stress Testing
        
        Push systems to limits with large n, high loss, extreme latency.
        """
        print("\n" + "="*80)
        print("PHASE 5: STRESS TESTING")
        print("="*80)
        
        # Large scale test
        config_scale = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST],
            curves=[CurveType.SECP256K1],
            dkg_methods=[DKGType.PEDERSEN],
            scale_params=[(50, 26), (100, 51)],
            network_mode=NetworkMode.NONE,
            iterations=10,
            warmup_iterations=3,
            enable_memory_profiling=True,
            verbose=True
        )
        
        # High loss test
        config_loss = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST],
            curves=[CurveType.SECP256K1],
            dkg_methods=[DKGType.PEDERSEN],
            scale_params=[(10, 6)],
            network_mode=NetworkMode.LOSSY,  # Will be modified
            iterations=30,
            warmup_iterations=5,
            verbose=True
        )
        
        results = []
        results.extend(self._run_config(config_scale, "phase5_stress_scale"))
        results.extend(self._run_config(config_loss, "phase5_stress_loss"))
        
        self.metadata["phases_completed"].append("phase5_stress")
        return results
    
    def _run_config(self, config: BenchmarkConfig, phase_name: str) -> List[Dict]:
        """Run benchmark with given configuration."""
        runner = BenchmarkRunner(config)
        results = runner.run_all()
        
        # Add phase metadata
        for result in results:
            result["phase"] = phase_name
            result["timestamp"] = datetime.now().isoformat()
        
        self.all_results.extend(results)
        
        # Save intermediate results
        self._save_results(results, phase_name)
        
        return results
    
    def _run_config_with_dkg_comparison(self, config: BenchmarkConfig, phase_name: str) -> List[Dict]:
        """Run benchmark comparing Pedersen vs Feldman DKG."""
        all_phase_results = []
        
        for dkg_method in config.dkg_methods:
            print(f"\n--- Running with {dkg_method.value.upper()} DKG ---")
            
            # Create config for this DKG method
            dkg_config = BenchmarkConfig(
                schemes=config.schemes,
                curves=config.curves,
                dkg_methods=[dkg_method],
                scale_params=config.scale_params,
                network_mode=config.network_mode,
                iterations=config.iterations,
                warmup_iterations=config.warmup_iterations,
                enable_memory_profiling=config.enable_memory_profiling,
                verbose=config.verbose
            )
            
            results = self._run_config(dkg_config, f"{phase_name}_{dkg_method.value}")
            all_phase_results.extend(results)
        
        return all_phase_results
    
    def _save_results(self, results: List[Dict], phase_name: str):
        """Save results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = self.output_dir / f"{phase_name}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "metadata": self.metadata,
                "results": results
            }, f, indent=2)
        print(f"✓ Saved JSON: {json_file}")
        
       
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        print("\n" + "="*80)
        print("GENERATING SUMMARY REPORT")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate plots
        try:
            plot_files = plot_results.main_wrapper(str(self.output_dir))
            print(f"✓ Generated plots: {plot_files}")
        except Exception as e:
            print(f"⚠ Plot generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Generate markdown summary
        md_file = self.output_dir / f"comprehensive_summary_{timestamp}.md"
        
        with open(md_file, 'w') as f:
            f.write("# Comprehensive Benchmark Summary\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Phases Completed:** {', '.join(self.metadata['phases_completed'])}\n\n")
            
            # Overall statistics
            f.write("## Overall Statistics\n\n")
            f.write(f"- Total configurations tested: {len(self.all_results)}\n")
            f.write(f"- Start time: {self.metadata['start_time']}\n\n")
            
            # Performance tables by phase
            f.write("## Phase Results\n\n")
            
            phases = set(r.get("phase", "unknown") for r in self.all_results)
            for phase in sorted(phases):
                phase_results = [r for r in self.all_results if r.get("phase") == phase]
                
                f.write(f"### {phase}\n\n")
                f.write("| Scheme | Curve | n | t | KeyGen (ms) | Sign (ms) | Verify (ms) |\n")
                f.write("|--------|-------|---|---|-------------|-----------|-------------|\n")
                
                for r in phase_results[:10]:  # Top 10
                    scheme = r.get("scheme", "N/A")
                    curve = r.get("curve", "N/A")
                    n = r.get("n", 0)
                    t = r.get("t", 0)
                    timing = r.get("timing", {})
                    
                    keygen = timing.get("keygen_mean_ms", 0)
                    sign = timing.get("sign_mean_ms", 0) or timing.get("partial_sign_mean_ms", 0)
                    verify = timing.get("verify_mean_ms", 0)
                    
                    f.write(f"| {scheme} | {curve} | {n} | {t} | {keygen:.2f} | {sign:.2f} | {verify:.2f} |\n")
                
                f.write("\n")
        
        print(f"✓ Saved summary: {md_file}")
        return str(md_file)
    
    def run_all_phases(self):
        """Execute all benchmark phases."""
        print("\n" + "="*80)
        print("COMPREHENSIVE BENCHMARK SUITE")
        print("="*80)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"Output directory: {self.output_dir}")
        print("="*80)
        
        total_start = time.time()
        
        # Run each phase
        try:
            self.run_phase_1_baseline()
            self.run_phase_2_curves()
            self.run_phase_3_network()
            self.run_phase_4_dkg_deepdive()
            self.run_phase_5_stress()
        except KeyboardInterrupt:
            print("\n⚠ Benchmark interrupted by user")
        except Exception as e:
            print(f"\n✗ Benchmark failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        # Finalize
        total_duration = time.time() - total_start
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["total_duration_seconds"] = total_duration
        
        # Save final metadata
        meta_file = self.output_dir / f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(meta_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        # Generate summary
        self.generate_summary_report()
        
        print("\n" + "="*80)
        print(f"BENCHMARK COMPLETED in {total_duration:.2f} seconds")
        print(f"Total results: {len(self.all_results)}")
        print(f"Output: {self.output_dir}")
        print("="*80)
        
        return self.all_results


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Benchmark Suite for SRTS Enhanced"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4, 5, 0],
        default=0,
        help="Run specific phase (0 = all phases)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (fewer iterations, smaller scale)"
    )
    
    args = parser.parse_args()
    
    benchmark = ComprehensiveBenchmark(output_dir=args.output)
    
    if args.quick:
        print("Running quick benchmark mode...")
        # Override iterations for quick mode
        config = BenchmarkConfig(
            schemes=[SchemeType.SRTS, SchemeType.FROST],
            curves=[CurveType.SECP256K1],
            dkg_methods=[DKGType.PEDERSEN],
            scale_params=[(3, 2), (5, 3)],
            network_mode=NetworkMode.NONE,
            iterations=5,
            warmup_iterations=1,
            verbose=True
        )
        runner = BenchmarkRunner(config)
        results = runner.run_all()
        benchmark.all_results = results
        benchmark.generate_summary_report()
    else:
        if args.phase == 0 or args.phase == 0:
            benchmark.run_phase_0_theoretical_analysis()
        if args.phase == 0 or args.phase == 1:
            benchmark.run_phase_1_baseline()
        if args.phase == 0 or args.phase == 2:
            benchmark.run_phase_2_curves()
        if args.phase == 0 or args.phase == 3:
            benchmark.run_phase_3_network()
        if args.phase == 0 or args.phase == 4:
            benchmark.run_phase_4_dkg_deepdive()
        if args.phase == 0 or args.phase == 5:
            benchmark.run_phase_5_stress()
        
        if args.phase == 0:
            benchmark.generate_summary_report()


if __name__ == "__main__":
    main()
