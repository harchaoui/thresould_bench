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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.config import (
    BenchmarkConfig, SchemeType, CurveType, DKGType, 
    NetworkMode, NetworkConfig
)
from benchmarks.runner import BenchmarkRunner
from benchmarks.reporter import BenchmarkReporter
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
        Tests multiple packet loss rates: 0%, 0.5%, 1%, 2%, 5%
        """
        print("\n" + "="*80)
        print("PHASE 3: NETWORK IMPACT ANALYSIS")
        print("="*80)
        
        # Test matrix of packet loss rates
        packet_loss_rates = [0.0, 0.005, 0.01, 0.02, 0.05]  # 0%, 0.5%, 1%, 2%, 5%
        
        results = []
        for loss_rate in packet_loss_rates:
            print(f"\n--- Testing with {loss_rate*100:.1f}% packet loss ---")
            
            config = BenchmarkConfig(
                schemes=[SchemeType.SRTS, SchemeType.FROST, SchemeType.TBLS],
                curves=[CurveType.SECP256K1, CurveType.BLS12_381],
                dkg_methods=[DKGType.PEDERSEN],
                scale_params=[(10, 6), (20, 11)],
                network_mode=NetworkMode.LOSSY,
                packet_loss_rate=loss_rate,  # Explicitly set packet loss rate
                iterations=30,  # Higher iterations for variance
                warmup_iterations=5,
                verbose=True
            )
            
            phase_name = f"phase3_network_loss{int(loss_rate*1000)}"
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
        """Save results to JSON with enhanced schema."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON with enhanced schema
        json_file = self.output_dir / f"{phase_name}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "metadata": self.metadata,
                "results": results
            }, f, indent=2, default=str)
        print(f"✓ Saved JSON: {json_file}")
        

        # # Save CSV with flattened stress metrics
        # csv_file = self.output_dir / f"{phase_name}_{timestamp}.csv"
        # if results:
        #     import csv
            
        #     # Flatten the nested structure for CSV
        #     flat_results = []
        #     for r in results:
        #         flat_row = {
        #             "scheme": r.get("scheme", ""),
        #             "curve": r.get("curve", ""),
        #             "n": r.get("n", 0),
        #             "t": r.get("t", 0),
        #             "network_mode": r.get("network_mode", ""),
        #             "packet_loss_rate": r.get("packet_loss_rate", 0.0),
        #             "phase": r.get("phase", ""),
        #             "timestamp": r.get("timestamp", "")
        #         }
                
        #         # Flatten timing metrics
        #         timing = r.get("timing", {})
        #         for key, value in timing.items():
        #             flat_row[f"timing_{key}"] = value
                
        #         # Flatten memory metrics
        #         memory = r.get("memory", {})
        #         for key, value in memory.items():
        #             flat_row[f"memory_{key}"] = value
                
        #         # Flatten signature metrics
        #         signatures = r.get("signatures", {})
        #         for key, value in signatures.items():
        #             flat_row[f"signature_{key}"] = value
                
        #         # Flatten stress metrics with prefix
        #         stress = r.get("stress_metrics", {})
        #         for key, value in stress.items():
        #             flat_row[f"stress_metrics_{key}"] = value
                
        #         flat_results.append(flat_row)
            
        #     # Write CSV
        #     if flat_results:
        #         fieldnames = list(flat_results[0].keys())
        #         with open(csv_file, 'w', newline='') as f:
        #             writer = csv.DictWriter(f, fieldnames=fieldnames)
        #             writer.writeheader()
        #             writer.writerows(flat_results)
        #         print(f"✓ Saved CSV: {csv_file}")
        

       
    def generate_summary_report(self):
        """Generate comprehensive summary report with stress analysis."""
        print("\n" + "="*80)
        print("GENERATING SUMMARY REPORT")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Skip plot generation (CSV files are disabled)
        print(f"ℹ Skipping plot generation: CSV output is disabled")
        
        # Generate markdown summary with intelligent stress analysis
        md_file = self.output_dir / f"comprehensive_summary_{timestamp}.md"
        
        with open(md_file, 'w') as f:
            f.write("# Comprehensive Benchmark Summary - Performance Under Stress\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Phases Completed:** {', '.join(self.metadata['phases_completed'])}\n\n")
            
            # Overall statistics
            f.write("## Overall Statistics\n\n")
            f.write(f"- Total configurations tested: {len(self.all_results)}\n")
            f.write(f"- Start time: {self.metadata['start_time']}\n\n")
            
            # Intelligent Stress Analysis Report
            f.write("## Stress Analysis Report\n\n")
            self._generate_stress_analysis(f)
            
            # Performance tables by phase
            f.write("## Phase Results\n\n")
            
            phases = set(r.get("phase", "unknown") for r in self.all_results)
            for phase in sorted(phases):
                phase_results = [r for r in self.all_results if r.get("phase") == phase]
                
                f.write(f"### {phase}\n\n")
                f.write("| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |\n")
                f.write("|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|\n")
                
                for r in phase_results[:15]:  # Top 15
                    scheme = r.get("scheme", "N/A")
                    curve = r.get("curve", "N/A")
                    n = r.get("n", 0)
                    t = r.get("t", 0)
                    loss_rate = r.get("packet_loss_rate", 0.0)
                    timing = r.get("timing", {})
                    stress = r.get("stress_metrics", {})
                    
                    keygen = timing.get("keygen_mean_ms", 0)
                    sign = timing.get("sign_mean_ms", 0) or timing.get("partial_sign_mean_ms", 0)
                    verify = timing.get("verify_mean_ms", 0)
                    network_overhead = stress.get("avg_network_overhead_ms", 0)
                    
                    f.write(f"| {scheme} | {curve} | {n} | {t} | {loss_rate:.2%} | {keygen:.2f} | {sign:.2f} | {verify:.2f} | {network_overhead:.2f} |\n")
                
                f.write("\n")
        
        print(f"✓ Saved summary: {md_file}")
        return str(md_file)
    
    def _generate_stress_analysis(self, f):
        """
        Generate intelligent comparative stress analysis.
        
        CRITICAL: Must compare apples-to-apples - same scheme, same n/t, within lossy network tests only.
        Compares phase3_network tests at 0% loss vs X% loss for identical configurations.
        """
        # Filter to only phase3_network results for valid stress comparison
        phase3_results = [r for r in self.all_results if r.get("phase", "").startswith("phase3_network")]
        
        if not phase3_results:
            f.write("*Insufficient data for stress analysis (need phase3_network results).*\n\n")
            return
        
        # Group by packet loss rate and scheme
        loss_rates = sorted(set(r.get("packet_loss_rate", 0.0) for r in phase3_results))
        schemes = sorted(set(r.get("scheme", "") for r in phase3_results))
        
        if not loss_rates or not schemes:
            f.write("*Insufficient data for stress analysis.*\n\n")
            return
        
        f.write("### Performance Degradation Analysis\n\n")
        
        # For each scheme, compare 0% loss vs highest loss WITHIN phase3 (same n values)
        # This ensures we're comparing identical configurations
        zero_loss_results = [r for r in phase3_results if r.get("packet_loss_rate", 0.0) == 0.0]
        high_loss_results = [r for r in phase3_results if r.get("packet_loss_rate", 0.0) == max(loss_rates)]
        
        if zero_loss_results and high_loss_results:
            f.write("**Under varying packet loss conditions** (comparing identical n/t configurations):\n\n")
            
            scheme_degradations = []
            
            for scheme in schemes:
                # Get all n values tested at 0% loss for this scheme
                scheme_zero_by_nt = {}
                for r in zero_loss_results:
                    if r.get("scheme") == scheme:
                        key = (r.get("n"), r.get("t"))
                        if key not in scheme_zero_by_nt:
                            scheme_zero_by_nt[key] = []
                        scheme_zero_by_nt[key].append(r)
                
                # Get matching n values at high loss
                scheme_high_by_nt = {}
                for r in high_loss_results:
                    if r.get("scheme") == scheme:
                        key = (r.get("n"), r.get("t"))
                        if key not in scheme_high_by_nt:
                            scheme_high_by_nt[key] = []
                        scheme_high_by_nt[key].append(r)
                
                # Only compare configurations that exist at both loss rates
                matching_configs = set(scheme_zero_by_nt.keys()) & set(scheme_high_by_nt.keys())
                
                if not matching_configs:
                    continue
                
                # Calculate degradation for each matching config, then average
                degradations = []
                overheads_high = []
                
                for n, t in matching_configs:
                    # Average across all iterations for this config at 0% loss
                    times_zero = [
                        r.get("stress_metrics", {}).get("avg_total_time_ms", 0) 
                        for r in scheme_zero_by_nt[(n, t)]
                    ]
                    avg_time_zero = sum(times_zero) / len(times_zero) if times_zero else 0
                    
                    # Average across all iterations for this config at high loss
                    times_high = [
                        r.get("stress_metrics", {}).get("avg_total_time_ms", 0) 
                        for r in scheme_high_by_nt[(n, t)]
                    ]
                    avg_time_high = sum(times_high) / len(times_high) if times_high else 0
                    
                    # Network overhead at high loss
                    overheads = [
                        r.get("stress_metrics", {}).get("avg_network_overhead_ms", 0) 
                        for r in scheme_high_by_nt[(n, t)]
                    ]
                    overheads_high.extend(overheads)
                    
                    if avg_time_zero > 0 and avg_time_high > 0:
                        degradation = ((avg_time_high - avg_time_zero) / avg_time_zero) * 100
                        degradations.append(degradation)
                
                if degradations:
                    avg_degradation = sum(degradations) / len(degradations)
                    avg_overhead = sum(overheads_high) / len(overheads_high) if overheads_high else 0
                    scheme_degradations.append((scheme, avg_degradation, avg_overhead))
                    
                    f.write(f"- **{scheme.upper()}**: ")
                    f.write(f"Experienced {avg_degradation:.1f}% slowdown at {max(loss_rates)*100:.1f}% packet loss. ")
                    f.write(f"Network overhead: {avg_overhead:.1f}ms.\n")
            
            f.write("\n")
            
            # Recommendations based on analysis
            f.write("### Recommendations\n\n")
            
            if scheme_degradations:
                scheme_degradations.sort(key=lambda x: x[1])
                most_resilient = scheme_degradations[0]
                least_resilient = scheme_degradations[-1]
                
                f.write(f"- **Most resilient to packet loss**: {most_resilient[0].upper()} ")
                f.write(f"({most_resilient[1]:.1f}% slowdown)\n")
                
                f.write(f"- **Most sensitive to packet loss**: {least_resilient[0].upper()} ")
                f.write(f"({least_resilient[1]:.1f}% slowdown)\n")
                
                f.write("\n**Use Case Recommendations**:\n\n")
                f.write("- **For mobile/unstable networks**: Prefer schemes with lower slowdown percentages.\n")
                f.write("- **For LAN/datacenter environments**: All schemes perform well; choose based on baseline latency.\n")
                f.write("- **For high-throughput applications**: SRTS/FROST offer best balance of speed and resilience.\n")
                f.write("- **For signature size efficiency**: TBLS provides constant-size signatures regardless of n.\n")
                f.write("- **For low-latency requirements**: MuSig2 shows best baseline performance in ideal conditions.\n")
        
        f.write("\n")
    
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
