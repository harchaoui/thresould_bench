#!/usr/bin/env python3
"""
Network resilience visualizations - Category 3 from visualization plan.

Generates plots analyzing scheme performance under varying network conditions:
- Performance degradation curves
- Network overhead heatmaps
- Retry distributions
- Time-to-completion CDFs
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)


class NetworkAnalyzer:
    """Generate network resilience visualizations."""
    
    SCHEME_COLORS = {
        'srts': '#2E86AB',
        'frost': '#A23B72',
        'musig2': '#F18F01',
        'tbls': '#C73E1D',
    }
    
    CURVE_MARKERS = {
        'secp256k1': 'o',
        'bls12-381': 's',
        'ristretto255': '^',
        'ed25519': 'D',
    }
    
    def __init__(self, output_dir: str = "output/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_degradation_curve(self, df: pd.DataFrame,
                              metric: str = 'sign_ms',
                              normalize: bool = True,
                              figsize: Tuple[int, int] = (14, 9),
                              save: bool = True) -> str:
        """
        Plot 3.1: Performance Degradation Curve
        
        Shows how performance degrades with increasing packet loss.
        
        Args:
            df: DataFrame with benchmark data including multiple loss rates
            metric: Metric to plot ('sign_ms', 'verify_ms', 'keygen_ms', etc.)
            normalize: If True, show slowdown ratio relative to 0% loss
            figsize: Figure size
            save: Whether to save to file
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if metric not in df.columns:
            raise ValueError(f"Metric '{metric}' not found in DataFrame")
        
        # Group by scheme, curve, and loss rate
        grouped = df.groupby(['scheme', 'curve', 'loss_rate'])
        
        # Calculate mean for each group
        agg_data = grouped[metric].mean().reset_index()
        
        if normalize:
            # Get baseline (0% loss) values for normalization
            baseline = agg_data[agg_data['loss_rate'] == 0.0].copy()
            baseline = baseline.rename(columns={metric: 'baseline'})
            baseline = baseline[['scheme', 'curve', 'baseline']]
            
            # Merge baseline back
            agg_data = agg_data.merge(baseline, on=['scheme', 'curve'], how='left')
            agg_data['slowdown_ratio'] = agg_data[metric] / agg_data['baseline']
            y_col = 'slowdown_ratio'
            ylabel = 'Slowdown Ratio (vs 0% loss)'
        else:
            y_col = metric
            ylabel = f'{metric} (ms)'
        
        # Plot for each scheme-curve combination
        for (scheme, curve), group in agg_data.groupby(['scheme', 'curve']):
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            group = group.sort_values('loss_rate')
            
            ax.plot(group['loss_rate'] * 100, group[y_col], 
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
        
        title = 'Performance Degradation Curve\n(Network Overhead vs Packet Loss)'
        if normalize:
            title += '\n(Shows breaking point where schemes become unusable)'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Add reference lines for degradation thresholds
        if normalize:
            ax.axhline(y=1.1, color='green', linestyle='--', alpha=0.5, label='10% degradation')
            ax.axhline(y=1.5, color='orange', linestyle='--', alpha=0.5, label='50% degradation')
            ax.axhline(y=2.0, color='red', linestyle='--', alpha=0.5, label='100% degradation')
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            norm_suffix = "_normalized" if normalize else ""
            output_path = self.output_dir / f"degradation_curve{norm_suffix}_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"degradation_curve{norm_suffix}_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_network_overhead_heatmap(self, df: pd.DataFrame,
                                     figsize: Tuple[int, int] = (14, 10),
                                     save: bool = True) -> str:
        """
        Plot 3.2: Network Overhead Heatmap
        
        X-axis: Packet loss rate
        Y-axis: Number of participants
        Color: Network overhead (ms)
        """
        if 'network_overhead_ms' not in df.columns:
            print("⚠ No network overhead data available")
            return None
        
        # Create pivot table for heatmap
        pivot_data = df.pivot_table(
            index='n',
            columns='loss_rate',
            values='network_overhead_ms',
            aggfunc='mean'
        )
        
        fig, axes = plt.subplots(1, len(df['scheme'].unique()), 
                                figsize=(figsize[0] * len(df['scheme'].unique()) // 2, figsize[1]),
                                sharey=True)
        
        if len(df['scheme'].unique()) == 1:
            axes = [axes]
        
        for idx, scheme in enumerate(sorted(df['scheme'].unique())):
            scheme_df = df[df['scheme'] == scheme]
            
            if len(scheme_df) == 0:
                continue
            
            pivot_data = scheme_df.pivot_table(
                index='n',
                columns='loss_rate',
                values='network_overhead_ms',
                aggfunc='mean'
            )
            
            ax = axes[idx] if idx < len(axes) else axes[-1]
            
            im = ax.imshow(pivot_data.values, aspect='auto', cmap='YlOrRd', 
                          interpolation='nearest')
            
            ax.set_xlabel('Packet Loss Rate')
            ax.set_ylabel('Participants (n)' if idx == 0 else '')
            ax.set_title(f'{scheme.upper()}', fontsize=14, fontweight='bold')
            
            # Set tick labels
            ax.set_xticks(range(len(pivot_data.columns)))
            ax.set_xticklabels([f'{r*100:.1f}%' for r in pivot_data.columns], rotation=45)
            ax.set_yticks(range(len(pivot_data.index)))
            ax.set_yticklabels(pivot_data.index.astype(int))
            
            # Add value annotations
            for i in range(len(pivot_data.index)):
                for j in range(len(pivot_data.columns)):
                    val = pivot_data.values[i, j]
                    if not np.isnan(val):
                        ax.text(j, i, f'{val:.1f}', ha='center', va='center', 
                               fontsize=8, color='black')
            
            plt.colorbar(im, ax=ax, label='Overhead (ms)')
        
        plt.suptitle('Network Overhead Heatmap\n(Interaction between scale and network quality)', 
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"overhead_heatmap_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"overhead_heatmap_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_retry_distribution(self, df: pd.DataFrame,
                               figsize: Tuple[int, int] = (12, 8),
                               save: bool = True) -> str:
        """
        Plot 3.3: Retry Distribution Box Plot
        
        Shows protocol chattiness under stress.
        """
        # Check if retry data exists
        retry_cols = [c for c in df.columns if 'retry' in c.lower()]
        
        if not retry_cols:
            # Synthesize retry data from network overhead if available
            if 'network_overhead_ms' not in df.columns:
                print("⚠ No retry or network overhead data available")
                return None
            
            # Estimate retries from overhead (assuming ~10ms per retry)
            df = df.copy()
            df['estimated_retries'] = df['network_overhead_ms'] / 10
            retry_col = 'estimated_retries'
        else:
            retry_col = retry_cols[0]
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Prepare data for box plot
        plot_data = []
        labels = []
        colors = []
        
        for scheme in sorted(df['scheme'].unique()):
            scheme_data = df[df['scheme'] == scheme][retry_col].dropna()
            if len(scheme_data) > 0:
                plot_data.append(scheme_data.values)
                labels.append(scheme.upper())
                colors.append(self.SCHEME_COLORS.get(scheme, '#333333'))
        
        if not plot_data:
            print("⚠ No retry data available")
            return None
        
        # Create box plot
        bp = ax.boxplot(plot_data, labels=labels, patch_artist=True,
                       boxprops=dict(facecolor='#A8DADC', edgecolor='black', linewidth=1.5),
                       medianprops=dict(color='red', linewidth=2),
                       whiskerprops=dict(color='black', linewidth=1.5),
                       capprops=dict(color='black', linewidth=1.5))
        
        # Color the boxes
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        ax.set_xlabel('Scheme', fontsize=14, fontweight='bold')
        ax.set_ylabel('Retries per Signing Round', fontsize=14, fontweight='bold')
        ax.set_title('Retry Distribution by Scheme\n(Identifies chatty vs robust protocols)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"retry_distribution_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"retry_distribution_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_time_cdf(self, df: pd.DataFrame,
                     loss_rate: Optional[float] = None,
                     metric: str = 'sign_ms',
                     figsize: Tuple[int, int] = (12, 8),
                     save: bool = True) -> str:
        """
        Plot 3.4: Time-to-Completion CDF
        
        Cumulative distribution function showing tail latency and reliability.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        plot_df = df.copy()
        if loss_rate is not None:
            plot_df = df[np.isclose(df['loss_rate'], loss_rate)]
        
        if len(plot_df) == 0:
            print(f"⚠ No data available for loss rate {loss_rate}")
            return None
        
        for scheme in sorted(df['scheme'].unique()):
            scheme_data = plot_df[plot_df['scheme'] == scheme][metric].dropna()
            
            if len(scheme_data) == 0:
                continue
            
            # Sort for CDF
            sorted_data = np.sort(scheme_data.values)
            cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            ax.plot(sorted_data, cdf, linewidth=2.5, label=scheme.upper(), 
                   color=color, alpha=0.8)
        
        ax.set_xlabel(f'{metric.replace("_", " ").title()} (ms)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Cumulative Probability P(X ≤ x)', fontsize=14, fontweight='bold')
        
        title = 'Time-to-Completion CDF'
        if loss_rate is not None:
            title += f'\n(Packet Loss = {loss_rate*100:.1f}%)'
        title += '\n(Shows tail latency and reliability)'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='lower right', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Add P50, P90, P99 reference lines
        ax.axvline(x=np.percentile(df[metric].dropna(), 50), color='gray', 
                  linestyle=':', alpha=0.5, label='P50')
        ax.axvline(x=np.percentile(df[metric].dropna(), 90), color='gray', 
                  linestyle='--', alpha=0.5, label='P90')
        ax.axvline(x=np.percentile(df[metric].dropna(), 99), color='gray', 
                  linestyle='-.', alpha=0.5, label='P99')
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            loss_suffix = f"_loss{int(loss_rate*100)}" if loss_rate is not None else ""
            output_path = self.output_dir / f"time_cdf{loss_suffix}_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"time_cdf{loss_suffix}_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def generate_all_network_plots(self, df: pd.DataFrame) -> List[str]:
        """Generate all Category 3 (Network Resilience) plots."""
        plots = []
        
        print("\n" + "=" * 60)
        print("Generating Network Resilience Plots")
        print("=" * 60)
        
        try:
            plots.append(self.plot_degradation_curve(df))
        except Exception as e:
            print(f"⚠ Could not generate degradation curve: {e}")
        
        try:
            plots.append(self.plot_network_overhead_heatmap(df))
        except Exception as e:
            print(f"⚠ Could not generate overhead heatmap: {e}")
        
        try:
            plots.append(self.plot_retry_distribution(df))
        except Exception as e:
            print(f"⚠ Could not generate retry distribution: {e}")
        
        try:
            # Generate CDF for different loss rates
            for loss_rate in sorted(df['loss_rate'].unique()):
                if loss_rate > 0:  # Only non-zero loss rates
                    plots.append(self.plot_time_cdf(df, loss_rate=loss_rate))
        except Exception as e:
            print(f"⚠ Could not generate CDF plots: {e}")
        
        print(f"\n✓ Generated {len(plots)} network resilience plots")
        return plots


if __name__ == "__main__":
    import sys
    from data_loader import load_benchmark_data
    
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/figures"
    
    print("Loading benchmark data...")
    df = load_benchmark_data(results_dir)
    
    analyzer = NetworkAnalyzer(output_dir)
    analyzer.generate_all_network_plots(df)
