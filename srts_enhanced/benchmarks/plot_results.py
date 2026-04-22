#!/usr/bin/env python3
"""
Generate publication-quality plots from benchmark CSV data.

This script parses the latest CSV in benchmark_results/ and generates:
1. Signing Latency vs. Number of Participants (for all schemes)
2. Verification Time Comparison
3. Signature Size Comparison
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path


def find_latest_csv(benchmark_dir: str = "benchmark_results") -> str:
    """Find the most recent benchmark CSV file with the most data (rows)."""
    csv_files = glob.glob(os.path.join(benchmark_dir, "benchmark_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No benchmark CSV files found in {benchmark_dir}")
    
    # Find the CSV with the most rows (excluding header)
    best_file = None
    max_rows = 0
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r') as f:
                row_count = sum(1 for _ in f) - 1  # Subtract header
                if row_count > max_rows:
                    max_rows = row_count
                    best_file = csv_file
        except Exception:
            continue
    
    if best_file is None:
        # Fallback to most recent by modification time
        best_file = max(csv_files, key=os.path.getmtime)
    
    return best_file


def load_benchmark_data(csv_path: str) -> pd.DataFrame:
    """Load and clean benchmark data from CSV."""
    df = pd.read_csv(csv_path)
    
    # Remove rows with all NaN values (if any)
    df = df.dropna(how='all')
    
    # Calculate total signing time for schemes that have it
    # For SRTS: online_sign = partial_sign + aggregate
    # For FROST: sign = partial_sign + aggregate
    # For MuSig2: sign = aggregate (no partial sign phase)
    
    if 'timing_partial_sign_mean_ms' in df.columns:
        df['timing_online_sign_mean_ms'] = (
            df['timing_partial_sign_mean_ms'].fillna(0) + 
            df['timing_aggregate_mean_ms'].fillna(0)
        )
    
    return df


def plot_signing_latency(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Signing Latency vs. Number of Participants."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Color palette for schemes
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    markers = {'srts': 'o', 'frost': 's', 'musig2': '^', 'tbls': 'D'}
    
    # Group by scheme and curve
    grouped = df.groupby(['scheme', 'curve'])
    
    for (scheme, curve), group in grouped:
        if 'timing_online_sign_mean_ms' not in group.columns:
            continue
            
        label = f"{scheme.upper()} ({curve})"
        color = scheme_colors.get(scheme, '#333333')
        marker = markers.get(scheme, 'o')
        
        ax.plot(group['n'], group['timing_online_sign_mean_ms'], 
                marker=marker, linewidth=2.5, markersize=10,
                label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Signing Latency (ms)', fontsize=14, fontweight='bold')
    ax.set_title('Threshold Signature Schemes: Signing Latency vs. Swarm Size\n(Simulated WAN: 50ms latency, 1% packet loss)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    # Set x-axis to show integer values
    n_values = sorted(df['n'].unique())
    ax.set_xticks(n_values)
    
    plt.tight_layout()
    
    # Save figure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"signing_latency_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # Also save as PDF for publications
    pdf_path = os.path.join(output_dir, f"signing_latency_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def plot_verification_time(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Verification Time Comparison across schemes."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    markers = {'srts': 'o', 'frost': 's', 'musig2': '^', 'tbls': 'D'}
    
    grouped = df.groupby(['scheme', 'curve'])
    
    for (scheme, curve), group in grouped:
        if 'timing_verify_mean_ms' not in group.columns:
            continue
            
        label = f"{scheme.upper()} ({curve})"
        color = scheme_colors.get(scheme, '#333333')
        marker = markers.get(scheme, 'o')
        
        ax.plot(group['n'], group['timing_verify_mean_ms'], 
                marker=marker, linewidth=2.5, markersize=10,
                label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Verification Time (ms)', fontsize=14, fontweight='bold')
    ax.set_title('Signature Verification Performance\n(Lower is better - TBLS excels at verification)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    n_values = sorted(df['n'].unique())
    ax.set_xticks(n_values)
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"verification_time_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    pdf_path = os.path.join(output_dir, f"verification_time_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def plot_signature_size(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Signature Size Comparison (bar chart)."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get average signature size per scheme-curve combination
    if 'signature_final_sig_avg_size_bytes' in df.columns:
        avg_sizes = df.groupby(['scheme', 'curve'])['signature_final_sig_avg_size_bytes'].mean().reset_index()
        avg_sizes['label'] = avg_sizes['scheme'].str.upper() + ' (' + avg_sizes['curve'] + ')'
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4749']
        
        bars = ax.bar(range(len(avg_sizes)), avg_sizes['signature_final_sig_avg_size_bytes'],
                     color=colors[:len(avg_sizes)], alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax.set_xticks(range(len(avg_sizes)))
        ax.set_xticklabels(avg_sizes['label'], rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Signature Size (bytes)', fontsize=14, fontweight='bold')
        ax.set_title('Signature Size Comparison Across Schemes\n(Smaller signatures reduce bandwidth for UAV swarms)', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # Add value labels on top of bars
        for i, (idx, row) in enumerate(avg_sizes.iterrows()):
            height = row['signature_final_sig_avg_size_bytes']
            ax.text(i, height + 2, f'{height:.1f} B', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"signature_size_{timestamp}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        
        pdf_path = os.path.join(output_dir, f"signature_size_{timestamp}.pdf")
        plt.savefig(pdf_path, bbox_inches='tight')
        print(f"✓ Saved: {pdf_path}")
        
        plt.close()
        return output_path
    
    print("⚠ Signature size data not available")
    return None


def plot_overhead_stack(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Overhead Stack Bar Chart - Crypto Time vs Network Overhead."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    # Group by scheme and get stress metrics
    if 'stress_metrics_avg_crypto_time_ms' not in df.columns or 'stress_metrics_avg_network_overhead_ms' not in df.columns:
        print("⚠ Stress metrics not available for overhead stack plot")
        return None
    
    grouped = df.groupby(['scheme', 'curve'])
    
    schemes_plot = []
    crypto_times = []
    network_times = []
    
    for (scheme, curve), group in grouped:
        avg_crypto = group['stress_metrics_avg_crypto_time_ms'].mean()
        avg_network = group['stress_metrics_avg_network_overhead_ms'].mean()
        
        if avg_crypto > 0 or avg_network > 0:
            label = f"{scheme.upper()} ({curve})"
            schemes_plot.append(label)
            crypto_times.append(avg_crypto)
            network_times.append(avg_network)
    
    if not schemes_plot:
        print("⚠ No data available for overhead stack plot")
        return None
    
    x_pos = range(len(schemes_plot))
    
    # Create stacked bar chart
    bars_crypto = ax.bar(x_pos, crypto_times, label='Crypto Time', 
                         color='#2E86AB', alpha=0.9, edgecolor='black', linewidth=1.5)
    bars_network = ax.bar(x_pos, network_times, bottom=crypto_times, 
                          label='Network Overhead (Retries)', 
                          color='#FF6B6B', alpha=0.9, edgecolor='black', linewidth=1.5)
    
    ax.set_xlabel('Scheme (Curve)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Time (ms)', fontsize=14, fontweight='bold')
    ax.set_title('Performance Under Stress: Crypto Time vs Network Overhead\\n(Shows which schemes suffer most from network jitter)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(schemes_plot, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=12, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (crypto, network) in enumerate(zip(crypto_times, network_times)):
        total = crypto + network
        ax.text(i, crypto / 2, f'{crypto:.1f}', ha='center', va='center', 
                fontsize=9, fontweight='bold', color='white')
        if network > 0:
            ax.text(i, crypto + network / 2, f'{network:.1f}', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"overhead_stack_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    pdf_path = os.path.join(output_dir, f"overhead_stack_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def plot_degradation_curve(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Degradation Curve - Performance vs Packet Loss Rate."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    markers = {'srts': 'o', 'frost': 's', 'musig2': '^', 'tbls': 'D'}
    
    # Check if we have packet_loss_rate column (from comprehensive benchmark with multiple loss rates)
    if 'packet_loss_rate' not in df.columns:
        # Try to infer from network_mode
        if 'network_mode' in df.columns:
            # Map network modes to approximate loss rates
            loss_mapping = {
                'none': 0.0,
                'lan': 0.0,
                'wan': 0.0,
                'lossy': 0.01,
                'mobile': 0.005
            }
            df['packet_loss_rate'] = df['network_mode'].map(loss_mapping).fillna(0.0)
        else:
            print("⚠ No packet loss rate data available for degradation curve")
            return None
    
    grouped = df.groupby(['scheme', 'curve'])
    
    for (scheme, curve), group in grouped:
        if 'stress_metrics_avg_network_overhead_ms' not in group.columns:
            continue
        
        label = f"{scheme.upper()} ({curve})"
        color = scheme_colors.get(scheme, '#333333')
        marker = markers.get(scheme, 'o')
        
        # Group by packet loss rate and calculate mean overhead
        loss_groups = group.groupby('packet_loss_rate')['stress_metrics_avg_network_overhead_ms'].mean()
        
        ax.plot(loss_groups.index * 100, loss_groups.values,  # Convert to percentage
                marker=marker, linewidth=2.5, markersize=10,
                label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Network Overhead (ms)', fontsize=14, fontweight='bold')
    ax.set_title('Degradation Curve: Network Overhead vs Packet Loss\\n(Shows breaking point where schemes become unusable)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"degradation_curve_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    pdf_path = os.path.join(output_dir, f"degradation_curve_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def plot_retry_distribution(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Retry Distribution Box Plot."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    if 'stress_metrics_avg_retries_per_iter' not in df.columns:
        print("⚠ Retry metrics not available")
        return None
    
    # Prepare data for box plot
    plot_data = []
    labels = []
    
    for scheme in df['scheme'].unique():
        scheme_data = df[df['scheme'] == scheme]['stress_metrics_avg_retries_per_iter']
        if len(scheme_data) > 0:
            plot_data.append(scheme_data.values)
            labels.append(scheme.upper())
    
    if not plot_data:
        print("⚠ No retry data available")
        return None
    
    # Create box plot
    bp = ax.boxplot(plot_data, labels=labels, patch_artist=True,
                    boxprops=dict(facecolor='#A8DADC', edgecolor='black', linewidth=1.5),
                    medianprops=dict(color='red', linewidth=2),
                    whiskerprops=dict(color='black', linewidth=1.5),
                    capprops=dict(color='black', linewidth=1.5))
    
    ax.set_xlabel('Scheme', fontsize=14, fontweight='bold')
    ax.set_ylabel('Retries per Iteration', fontsize=14, fontweight='bold')
    ax.set_title('Retry Distribution by Scheme\\n(Identifies chatty vs robust protocols)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"retry_distribution_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    pdf_path = os.path.join(output_dir, f"retry_distribution_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def plot_keygen_time(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Plot Key Generation Time vs. Number of Participants."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scheme_colors = {
        'srts': '#2E86AB',
        'frost': '#A23B72', 
        'musig2': '#F18F01',
        'tbls': '#C73E1D'
    }
    
    markers = {'srts': 'o', 'frost': 's', 'musig2': '^', 'tbls': 'D'}
    
    grouped = df.groupby(['scheme', 'curve'])
    
    for (scheme, curve), group in grouped:
        if 'timing_keygen_mean_ms' not in group.columns:
            continue
            
        label = f"{scheme.upper()} ({curve})"
        color = scheme_colors.get(scheme, '#333333')
        marker = markers.get(scheme, 'o')
        
        ax.plot(group['n'], group['timing_keygen_mean_ms'], 
                marker=marker, linewidth=2.5, markersize=10,
                label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Key Generation Time (ms)', fontsize=14, fontweight='bold')
    ax.set_title('DKG Protocol Performance: Key Generation Time\n(One-time setup cost per swarm configuration)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    n_values = sorted(df['n'].unique())
    ax.set_xticks(n_values)
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"keygen_time_{timestamp}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    pdf_path = os.path.join(output_dir, f"keygen_time_{timestamp}.pdf")
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved: {pdf_path}")
    
    plt.close()
    return output_path


def generate_summary_table(df: pd.DataFrame, output_dir: str = "benchmark_results"):
    """Generate a markdown summary table of performance metrics."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"performance_summary_{timestamp}.md")
    
    with open(output_path, 'w') as f:
        f.write("# 📊 Benchmark Performance Summary\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"Data source: `{os.path.basename(df.attrs.get('source_file', 'N/A'))}`\n\n")
        
        # Online Signing Performance
        f.write("## ⚡ Online Signing Latency (ms)\n\n")
        f.write("| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Best Use Case |\n")
        f.write("|--------|-------|-----|-----|------|------|---------------|\n")
        
        if 'timing_online_sign_mean_ms' in df.columns:
            for (scheme, curve), group in df.groupby(['scheme', 'curve']):
                row = group.set_index('n')['timing_online_sign_mean_ms']
                vals = [f"{row.get(n, 0):.1f}" for n in [3, 5, 10, 20]]
                
                use_cases = {
                    ('srts', 'ed25519'): "Real-time Control",
                    ('srts', 'secp256k1'): "Bitcoin Compat",
                    ('frost', 'ed25519'): "Small Groups",
                    ('musig2', 'secp256k1'): "2-of-2 Consensus",
                    ('tbls', 'bls12-381'): "Telemetry Aggregation"
                }
                use_case = use_cases.get((scheme, curve), "General Purpose")
                
                f.write(f"| {scheme.upper()} | {curve} | {' | '.join(vals)} | {use_case} |\n")
        
        f.write("\n## ✅ Verification Time (ms)\n\n")
        f.write("| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Avg |\n")
        f.write("|--------|-------|-----|-----|------|------|-----|\n")
        
        if 'timing_verify_mean_ms' in df.columns:
            for (scheme, curve), group in df.groupby(['scheme', 'curve']):
                row = group.set_index('n')['timing_verify_mean_ms']
                vals = [f"{row.get(n, 0):.2f}" for n in [3, 5, 10, 20]]
                avg = group['timing_verify_mean_ms'].mean()
                f.write(f"| {scheme.upper()} | {curve} | {' | '.join(vals)} | {avg:.2f} |\n")
        
        f.write("\n## 📦 Signature Sizes\n\n")
        f.write("| Scheme | Curve | Avg Size (bytes) |\n")
        f.write("|--------|-------|------------------|\n")
        
        if 'signature_final_sig_avg_size_bytes' in df.columns:
            for (scheme, curve), group in df.groupby(['scheme', 'curve']):
                avg_size = group['signature_final_sig_avg_size_bytes'].mean()
                f.write(f"| {scheme.upper()} | {curve} | {avg_size:.1f} |\n")
    
    print(f"✓ Saved: {output_path}")
    return output_path


def main():
    """Main entry point for generating plots."""
    return main_wrapper()

def main_wrapper(output_dir: str = None):
    """Wrapper function for programmatic access."""
    print("=" * 60)
    print("📈 SRTS Enhanced - Benchmark Visualization Tool")
    print("=" * 60)
    
    # Find latest CSV
    if output_dir:
        csv_path = find_latest_csv(output_dir)
    else:
        csv_path = find_latest_csv()
    print(f"\n📂 Loading data from: {csv_path}")
    
    # Load data
    df = load_benchmark_data(csv_path)
    df.attrs['source_file'] = csv_path
    
    print(f"✓ Loaded {len(df)} benchmark records")
    print(f"  Schemes: {df['scheme'].unique().tolist()}")
    print(f"  Curves: {df['curve'].unique().tolist()}")
    print(f"  Participant counts: {sorted(df['n'].unique().tolist())}")
    
    # Output directory
    output_path = Path(output_dir) if output_dir else Path(os.path.dirname(csv_path))
    
    print("\n🎨 Generating plots...")
    
    # Generate all plots
    plots_generated = []
    
    # Original plots
    try:
        plots_generated.append(plot_signing_latency(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate signing latency plot: {e}")
    
    try:
        plots_generated.append(plot_verification_time(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate verification time plot: {e}")
    
    try:
        plots_generated.append(plot_signature_size(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate signature size plot: {e}")
    
    try:
        plots_generated.append(plot_keygen_time(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate keygen time plot: {e}")
    
    # New stress analysis plots
    try:
        plots_generated.append(plot_overhead_stack(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate overhead stack plot: {e}")
    
    try:
        plots_generated.append(plot_degradation_curve(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate degradation curve plot: {e}")
    
    try:
        plots_generated.append(plot_retry_distribution(df, str(output_path)))
    except Exception as e:
        print(f"⚠ Could not generate retry distribution plot: {e}")
    
    try:
        generate_summary_table(df, str(output_path))
    except Exception as e:
        print(f"⚠ Could not generate summary table: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {len(plots_generated)} plots successfully")
    print("=" * 60)
    
    return plots_generated


if __name__ == "__main__":
    main()
