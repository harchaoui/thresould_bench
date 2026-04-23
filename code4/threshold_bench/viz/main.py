#!/usr/bin/env python3
"""
Main entry point for generating all benchmark visualizations.

Aggregates data loading and all plot categories into a single command.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import BenchmarkDataLoader, load_benchmark_data
from plot_schemes import SchemeComparator
from plot_network import NetworkAnalyzer


class VisualizationPipeline:
    """Orchestrate the complete visualization pipeline."""
    
    def __init__(self, results_dir: str = "benchmark_results",
                 output_dir: str = "output"):
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output)
        
        # Create output subdirectories
        (self.output_dir / 'figures').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'interactive').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'reports').mkdir(parents=True, exist_ok=True)
        
        self.data_loader = BenchmarkDataLoader(str(self.results_dir))
        self.scheme_comparator = SchemeComparator(str(self.output_dir / 'figures'))
        self.network_analyzer = NetworkAnalyzer(str(self.output_dir / 'figures'))
        
        self.df: Optional[pd.DataFrame] = None
        self.generated_plots: List[str] = []
        self.generated_reports: List[str] = []
    
    def run_full_pipeline(self, 
                         generate_scheme_plots: bool = True,
                         generate_network_plots: bool = True,
                         generate_report: bool = True) -> dict:
        """
        Execute the complete visualization pipeline.
        
        Args:
            generate_scheme_plots: Generate Category 1 (Scheme Comparison) plots
            generate_network_plots: Generate Category 3 (Network Resilience) plots
            generate_report: Generate markdown summary report
            
        Returns:
            Dictionary with lists of generated files
        """
        print("=" * 70)
        print("📊 THRESHOLD SIGNATURE BENCHMARK VISUALIZATION PIPELINE")
        print("=" * 70)
        print(f"\nInput directory: {self.results_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Load data
        print("\n" + "-" * 70)
        print("Step 1: Loading Benchmark Data")
        print("-" * 70)
        
        try:
            self.df = self.data_loader.load_all_phases()
            self.df = self.data_loader.add_derived_metrics(self.df)
            
            print(f"✓ Loaded {len(self.df)} records from {len(self.data_loader.loaded_files)} files")
            print(f"\nData Summary:")
            print(f"  Schemes: {', '.join(self.df['scheme'].unique())}")
            print(f"  Curves: {', '.join(self.df['curve'].unique())}")
            print(f"  Participant counts: {sorted(self.df['n'].unique())}")
            print(f"  Loss rates: {sorted(self.df['loss_rate'].unique())}")
            print(f"  Phases: {', '.join(self.df['_phase'].unique() if '_phase' in self.df.columns else ['N/A'])}")
            
        except FileNotFoundError as e:
            print(f"✗ Error loading data: {e}")
            return {'error': str(e)}
        
        # Step 2: Generate scheme comparison plots
        if generate_scheme_plots:
            print("\n" + "-" * 70)
            print("Step 2: Generating Scheme Comparison Plots")
            print("-" * 70)
            
            scheme_plots = self.scheme_comparator.generate_all_scheme_plots(self.df)
            self.generated_plots.extend(scheme_plots)
        
        # Step 3: Generate network resilience plots
        if generate_network_plots:
            print("\n" + "-" * 70)
            print("Step 3: Generating Network Resilience Plots")
            print("-" * 70)
            
            network_plots = self.network_analyzer.generate_all_network_plots(self.df)
            self.generated_plots.extend(network_plots)
        
        # Step 4: Generate summary report
        if generate_report:
            print("\n" + "-" * 70)
            print("Step 4: Generating Summary Report")
            print("-" * 70)
            
            report_path = self._generate_summary_report()
            if report_path:
                self.generated_reports.append(report_path)
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE")
        print("=" * 70)
        print(f"\nGenerated {len(self.generated_plots)} plots")
        print(f"Generated {len(self.generated_reports)} reports")
        print(f"\nOutput locations:")
        print(f"  Figures: {self.output_dir / 'figures'}")
        print(f"  Reports: {self.output_dir / 'reports'}")
        
        return {
            'plots': self.generated_plots,
            'reports': self.generated_reports,
            'data_records': len(self.df),
            'source_files': self.data_loader.loaded_files,
        }
    
    def _generate_summary_report(self) -> str:
        """Generate a comprehensive markdown summary report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / 'reports' / f"benchmark_summary_{timestamp}.md"
        
        df = self.df
        
        with open(report_path, 'w') as f:
            f.write("# 📊 Threshold Signature Benchmark Summary\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overview
            f.write("## Overview\n\n")
            f.write(f"- **Total configurations tested:** {len(df)}\n")
            f.write(f"- **Schemes evaluated:** {', '.join(df['scheme'].unique())}\n")
            f.write(f"- **Curves tested:** {', '.join(df['curve'].unique())}\n")
            f.write(f"- **Participant range:** {df['n'].min()} to {df['n'].max()}\n")
            f.write(f"- **Packet loss range:** {df['loss_rate'].min()*100:.1f}% to {df['loss_rate'].max()*100:.1f}%\n\n")
            
            # Performance Summary Table
            f.write("## Performance Summary (Baseline, 0% Loss)\n\n")
            
            baseline = df[df['loss_rate'] == 0.0]
            
            f.write("| Scheme | Curve | Avg KeyGen (ms) | Avg Sign (ms) | Avg Verify (ms) |\n")
            f.write("|--------|-------|-----------------|---------------|----------------|\n")
            
            for (scheme, curve), group in baseline.groupby(['scheme', 'curve']):
                keygen = group['keygen_ms'].mean()
                sign = group['sign_ms'].mean()
                verify = group['verify_ms'].mean()
                f.write(f"| {scheme.upper()} | {curve} | {keygen:.2f} | {sign:.2f} | {verify:.2f} |\n")
            
            f.write("\n")
            
            # Network Resilience Analysis
            f.write("## Network Resilience Analysis\n\n")
            
            if 'slowdown_percentage' in df.columns:
                stress_df = df[df['loss_rate'] > 0.0]
                
                f.write("### Performance Degradation Under Stress\n\n")
                f.write("| Scheme | Max Loss Tested | Avg Slowdown | Recommendation |\n")
                f.write("|--------|-----------------|--------------|----------------|\n")
                
                for scheme in df['scheme'].unique():
                    scheme_stress = stress_df[stress_df['scheme'] == scheme]
                    if len(scheme_stress) > 0:
                        max_loss = scheme_stress['loss_rate'].max()
                        avg_slowdown = scheme_stress['slowdown_percentage'].mean()
                        
                        if avg_slowdown < 20:
                            rec = "✅ Excellent"
                        elif avg_slowdown < 50:
                            rec = "⚠️ Good"
                        elif avg_slowdown < 100:
                            rec = "⚠️ Fair"
                        else:
                            rec = "❌ Poor"
                        
                        f.write(f"| {scheme.upper()} | {max_loss*100:.1f}% | {avg_slowdown:.1f}% | {rec} |\n")
                
                f.write("\n")
            
            # Recommendations
            f.write("## Recommendations by Use Case\n\n")
            
            # Find best schemes for different metrics
            baseline_avg = baseline.groupby('scheme').agg({
                'sign_ms': 'mean',
                'verify_ms': 'mean',
                'keygen_ms': 'mean',
            })
            
            f.write("### ⚡ Lowest Signing Latency\n")
            best_sign = baseline_avg['sign_ms'].idxmin()
            f.write(f"**{best_sign.upper()}** - Average: {baseline_avg.loc[best_sign, 'sign_ms']:.2f} ms\n\n")
            
            f.write("### ✅ Fastest Verification\n")
            best_verify = baseline_avg['verify_ms'].idxmin()
            f.write(f"**{best_verify.upper()}** - Average: {baseline_avg.loc[best_verify, 'verify_ms']:.2f} ms\n\n")
            
            f.write("### 🔑 Fastest Key Generation\n")
            best_keygen = baseline_avg['keygen_ms'].idxmin()
            f.write(f"**{best_keygen.upper()}** - Average: {baseline_avg.loc[best_keygen, 'keygen_ms']:.2f} ms\n\n")
            
            if 'slowdown_percentage' in df.columns:
                f.write("### 🛡️ Most Network Resilient\n")
                stress_avg = stress_df.groupby('scheme')['slowdown_percentage'].mean()
                best_resilient = stress_avg.idxmin()
                f.write(f"**{best_resilient.upper()}** - Average slowdown: {stress_avg.loc[best_resilient]:.1f}%\n\n")
            
            # Generated Plots
            f.write("## Generated Visualizations\n\n")
            f.write("See the `figures/` directory for:\n\n")
            f.write("- **Signing latency comparisons** - How signing time scales with participants\n")
            f.write("- **Verification time charts** - Critical for high-throughput scenarios\n")
            f.write("- **Key generation costs** - One-time DKG setup overhead\n")
            f.write("- **Time breakdown charts** - Where does the time go?\n")
            f.write("- **Degradation curves** - Performance under packet loss\n")
            f.write("- **Network overhead heatmaps** - Scale × loss interaction\n")
            f.write("- **Retry distributions** - Protocol chattiness analysis\n")
            f.write("- **CDF plots** - Tail latency and reliability\n")
            
            f.write("\n---\n")
            f.write(f"*Report generated by Threshold Bench Visualization Pipeline*\n")
        
        print(f"✓ Saved: {report_path}")
        return str(report_path)


def main():
    """Command-line interface for the visualization pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate comprehensive visualizations for threshold signature benchmarks'
    )
    parser.add_argument(
        '--results-dir', '-r',
        default='benchmark_results',
        help='Directory containing benchmark JSON files (default: benchmark_results)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Directory for output files (default: output)'
    )
    parser.add_argument(
        '--no-scheme-plots',
        action='store_true',
        help='Skip scheme comparison plots'
    )
    parser.add_argument(
        '--no-network-plots',
        action='store_true',
        help='Skip network resilience plots'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip summary report generation'
    )
    
    args = parser.parse_args()
    
    pipeline = VisualizationPipeline(
        results_dir=args.results_dir,
        output_dir=args.output_dir
    )
    
    results = pipeline.run_full_pipeline(
        generate_scheme_plots=not args.no_scheme_plots,
        generate_network_plots=not args.no_network_plots,
        generate_report=not args.no_report
    )
    
    if 'error' in results:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
