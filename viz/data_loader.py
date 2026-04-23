#!/usr/bin/env python3
"""
Unified data loader for threshold signature benchmark results.

Loads all phase JSON files and merges them into a single DataFrame
with derived metrics for comprehensive analysis.
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np


class BenchmarkDataLoader:
    """Load and unify benchmark data from multiple phase JSON files."""
    
    # Expected phase files in order of execution
    PHASE_FILES = [
        "phase1_baseline_feldman_*.json",
        "phase1_baseline_pedersen_*.json",
        "phase2_curves_schnorr_*.json",
        "phase2_curves_tbls_*.json",
        "phase3_network_loss0_*.json",
        "phase3_network_loss5_*.json",  # 0.5%
        "phase3_network_loss10_*.json", # 1%
        "phase3_network_loss20_*.json", # 2%
        "phase3_network_loss50_*.json", # 5%
        "phase4_dkg_analysis_feldman_*.json",
        "phase4_dkg_analysis_pedersen_*.json",
        "phase5_stress_loss_*.json",
        "phase5_stress_scale_*.json",
    ]
    
    def __init__(self, results_dir: str = "benchmark_results"):
        self.results_dir = Path(results_dir)
        self.loaded_files: List[str] = []
        
    def load_all_phases(self) -> pd.DataFrame:
        """
        Load and merge all phase JSON files into unified DataFrame.
        
        Returns:
            pd.DataFrame: Combined benchmark data with standardized columns
        """
        all_results = []
        
        for pattern in self.PHASE_FILES:
            matching_files = glob.glob(str(self.results_dir / pattern))
            
            for file_path in matching_files:
                try:
                    data = self._load_single_file(file_path)
                    if data:
                        all_results.extend(data)
                        self.loaded_files.append(file_path)
                except Exception as e:
                    print(f"⚠ Warning: Could not load {file_path}: {e}")
        
        if not all_results:
            raise FileNotFoundError(
                f"No benchmark JSON files found in {self.results_dir}. "
                f"Expected patterns: {self.PHASE_FILES}"
            )
        
        df = pd.DataFrame(all_results)
        df = self._standardize_columns(df)
        df.attrs['source_files'] = self.loaded_files
        df.attrs['load_timestamp'] = datetime.now().isoformat()
        
        return df
    
    def _load_single_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load a single JSON file and extract results."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract phase name from filename
        filename = Path(file_path).stem
        phase_name = '_'.join(filename.split('_')[:-1])  # Remove timestamp
        
        # Handle both formats: {"results": [...]} and direct list [...]
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get('results', [])
        else:
            results = []
        
        # Add metadata to each result
        for result in results:
            result['_phase'] = phase_name
            result['_source_file'] = filename
            result['_load_time'] = datetime.now().isoformat()
        
        return results
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names across different phase formats."""
        # Map various column name formats to standard names
        column_mapping = {
            # Key generation time
            'keygen_ms': 'keygen_ms',
            'timing_keygen_mean_ms': 'keygen_ms',
            'KeyGen (ms)': 'keygen_ms',
            
            # Signing time
            'sign_ms': 'sign_ms',
            'timing_online_sign_mean_ms': 'sign_ms',
            'Sign (ms)': 'sign_ms',
            
            # Verification time
            'verify_ms': 'verify_ms',
            'timing_verify_mean_ms': 'verify_ms',
            'Verify (ms)': 'verify_ms',
            
            # Network overhead
            'network_overhead_ms': 'network_overhead_ms',
            'stress_metrics_avg_network_overhead_ms': 'network_overhead_ms',
            'Network Overhead (ms)': 'network_overhead_ms',
            
            # Packet loss rate
            'loss_rate': 'loss_rate',
            'packet_loss_rate': 'loss_rate',
            'Loss Rate': 'loss_rate',
            
            # Participant count
            'n': 'n',
            'num_participants': 'n',
            
            # Threshold
            't': 't',
            'threshold': 't',
            
            # Scheme and curve
            'scheme': 'scheme',
            'curve': 'curve',
        }
        
        # Rename columns where possible
        rename_dict = {}
        for col in df.columns:
            if col in column_mapping:
                rename_dict[col] = column_mapping[col]
        
        df = df.rename(columns=rename_dict)
        
        # Ensure required columns exist
        required_cols = ['scheme', 'curve', 'n', 't', 'loss_rate', 
                        'keygen_ms', 'sign_ms', 'verify_ms', 'network_overhead_ms']
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan
        
        # Fill missing loss_rate with 0
        df['loss_rate'] = df['loss_rate'].fillna(0.0)
        
        return df
    
    def add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived metrics for deeper analysis.
        
        Adds:
        - total_time: keygen + sign + verify + network_overhead
        - slowdown_ratio: sign_ms at loss / sign_ms at 0% loss
        - overhead_percentage: network_overhead / total_time * 100
        - operations_per_second: 1000 / sign_ms
        """
        df = df.copy()
        
        # Total operation time
        df['total_time_ms'] = (
            df['keygen_ms'].fillna(0) + 
            df['sign_ms'].fillna(0) + 
            df['verify_ms'].fillna(0) + 
            df['network_overhead_ms'].fillna(0)
        )
        
        # Operations per second (for signing)
        df['ops_per_second'] = 1000 / df['sign_ms'].replace(0, np.nan)
        
        # Slowdown ratio (need baseline for comparison)
        # Sort by loss rate and get baseline (first = lowest loss rate)
        df = df.sort_values('loss_rate')
        df['baseline_sign_ms'] = df.groupby(['scheme', 'curve', 'n', 't'])['sign_ms'].transform('first')
        df['slowdown_ratio'] = df['sign_ms'] / df['baseline_sign_ms']
        df['slowdown_percentage'] = (df['slowdown_ratio'] - 1) * 100
        
        # Overhead percentage
        df['overhead_percentage'] = (
            df['network_overhead_ms'] / df['total_time_ms'].replace(0, np.nan) * 100
        )
        
        # Efficiency score (lower is better): normalized sum of all times
        for col in ['keygen_ms', 'sign_ms', 'verify_ms']:
            max_val = df[col].max()
            if max_val > 0:
                df[f'{col}_normalized'] = df[col] / max_val
        
        df['efficiency_score'] = (
            df.get('keygen_ms_normalized', 0) + 
            df.get('sign_ms_normalized', 0) + 
            df.get('verify_ms_normalized', 0)
        )
        
        return df
    
    def filter_by_phase(self, df: pd.DataFrame, phases: List[str]) -> pd.DataFrame:
        """Subset data for specific analysis phases."""
        if '_phase' not in df.columns:
            raise ValueError("DataFrame must have '_phase' column. Use load_all_phases() first.")
        
        return df[df['_phase'].isin(phases)].copy()
    
    def filter_by_scheme(self, df: pd.DataFrame, schemes: List[str]) -> pd.DataFrame:
        """Filter by scheme names."""
        return df[df['scheme'].isin(schemes)].copy()
    
    def filter_by_loss_rate(self, df: pd.DataFrame, 
                           min_loss: float = 0.0, 
                           max_loss: float = 1.0) -> pd.DataFrame:
        """Filter by packet loss rate range."""
        return df[(df['loss_rate'] >= min_loss) & (df['loss_rate'] <= max_loss)].copy()
    
    def get_baseline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get only baseline (0% loss) data."""
        return df[df['loss_rate'] == 0.0].copy()
    
    def get_stress_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get only stress test data (>0% loss)."""
        return df[df['loss_rate'] > 0.0].copy()
    
    def pivot_for_comparison(self, df: pd.DataFrame, 
                            index: str = 'n',
                            columns: str = 'scheme',
                            values: str = 'sign_ms') -> pd.DataFrame:
        """Create pivot table for easy scheme comparison."""
        return df.pivot_table(
            index=index, 
            columns=columns, 
            values=values,
            aggfunc='mean'
        )
    
    def summary_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate summary statistics grouped by scheme and curve."""
        numeric_cols = ['keygen_ms', 'sign_ms', 'verify_ms', 'network_overhead_ms', 'total_time_ms']
        available_cols = [c for c in numeric_cols if c in df.columns]
        
        return df.groupby(['scheme', 'curve'])[available_cols].agg([
            'mean', 'std', 'min', 'max', 'count'
        ])


def load_benchmark_data(results_dir: str = "benchmark_results") -> pd.DataFrame:
    """
    Convenience function to load benchmark data with derived metrics.
    
    Usage:
        df = load_benchmark_data("path/to/benchmark_results")
    """
    loader = BenchmarkDataLoader(results_dir)
    df = loader.load_all_phases()
    df = loader.add_derived_metrics(df)
    return df


if __name__ == "__main__":
    # Example usage
    import sys
    
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results"
    
    print("=" * 60)
    print("Benchmark Data Loader")
    print("=" * 60)
    
    loader = BenchmarkDataLoader(results_dir)
    
    try:
        df = loader.load_all_phases()
        print(f"✓ Loaded {len(df)} records from {len(loader.loaded_files)} files")
        print(f"\nFiles loaded:")
        for f in loader.loaded_files:
            print(f"  - {f}")
        
        df = loader.add_derived_metrics(df)
        
        print(f"\nColumns: {df.columns.tolist()}")
        print(f"\nSchemes: {df['scheme'].unique().tolist()}")
        print(f"Curves: {df['curve'].unique().tolist()}")
        print(f"Participant counts: {sorted(df['n'].unique().tolist())}")
        print(f"Loss rates: {sorted(df['loss_rate'].unique().tolist())}")
        
        print("\n" + "=" * 60)
        print("Summary Statistics (Signing Time)")
        print("=" * 60)
        summary = df.groupby(['scheme', 'curve'])['sign_ms'].agg(['mean', 'std', 'min', 'max'])
        print(summary.to_string())
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
