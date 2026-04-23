#!/usr/bin/env python3
"""
Scheme comparison visualizations - Category 1 from visualization plan.

Generates plots comparing different threshold signature schemes across
multiple dimensions: latency, verification, key generation, and total time.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)


# =============================================================================
# COMPATIBILITY RULES
# =============================================================================
# Scheme × Curve validity: valid, suboptimal, or invalid
# Scheme × DKG Type validity: valid, suboptimal, or invalid

COMPATIBILITY = {
    # Scheme × Curve compatibility
    'curve': {
        ('srts', 'secp256k1'): 'valid',
        ('srts', 'bls12-381'): 'suboptimal',
        ('srts', 'ristretto255'): 'valid',
        ('frost', 'secp256k1'): 'valid',
        ('frost', 'bls12-381'): 'suboptimal',
        ('frost', 'ristretto255'): 'valid',  # preferred
        ('musig2', 'secp256k1'): 'valid',
        ('musig2', 'bls12-381'): 'suboptimal',
        ('musig2', 'ristretto255'): 'valid',
        ('tbls', 'secp256k1'): 'invalid',   # tBLS requires pairing-friendly
        ('tbls', 'bls12-381'): 'valid',
        ('tbls', 'ristretto255'): 'invalid', # tBLS requires pairing-friendly
    },
    # Scheme × DKG Type compatibility
    'dkg': {
        ('srts', 'feldman_vss'): 'valid',
        ('srts', 'pedersen_dkg'): 'valid',   # preferred, stronger security
        ('srts', 'not_applicable'): 'invalid',
        ('frost', 'feldman_vss'): 'valid',
        ('frost', 'pedersen_dkg'): 'valid',  # preferred, stronger security
        ('frost', 'not_applicable'): 'invalid',
        ('musig2', 'feldman_vss'): 'invalid',  # uses own key aggregation
        ('musig2', 'pedersen_dkg'): 'invalid', # same reason
        ('musig2', 'not_applicable'): 'valid', # MuSig2 only
        ('tbls', 'feldman_vss'): 'valid',
        ('tbls', 'pedersen_dkg'): 'suboptimal', # overhead with no security gain
        ('tbls', 'not_applicable'): 'invalid',
    },
}


class SchemeComparator:
    """Generate comparative visualizations across threshold signature schemes."""
    
    # Color palette for schemes (colorblind-friendly)
    SCHEME_COLORS = {
        'srts': '#2E86AB',      # Blue
        'frost': '#A23B72',     # Purple
        'musig2': '#F18F01',    # Orange
        'tbls': '#C73E1D',      # Red
    }
    
    # Markers for curves
    CURVE_MARKERS = {
        'secp256k1': 'o',
        'bls12-381': 's',
        'ristretto255': '^',
        'ed25519': 'D',
    }
    
    def __init__(self, output_dir: str = "output/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _skip_if_invalid(self, scheme: str, curve: str, dkg: str = None) -> bool:
        """
        Check if a scheme+curve+dkg combination is invalid per COMPATIBILITY.
        
        Returns True if the combination should be skipped (invalid).
        """
        scheme_lower = scheme.lower()
        curve_lower = curve.lower()
        
        # Check curve compatibility
        if (scheme_lower, curve_lower) in COMPATIBILITY['curve']:
            if COMPATIBILITY['curve'][(scheme_lower, curve_lower)] == 'invalid':
                return True
        
        # Check DKG compatibility if provided
        if dkg is not None:
            dkg_lower = dkg.lower()
            if (scheme_lower, dkg_lower) in COMPATIBILITY['dkg']:
                if COMPATIBILITY['dkg'][(scheme_lower, dkg_lower)] == 'invalid':
                    return True
        
        return False
    
    def _annotate_musig2(self, ax: plt.Axes) -> None:
        """
        Add × marker style and footnote for MuSig2 being n-of-n only.
        """
        ax.text(0.5, -0.18, 
                "× MuSig2 is n-of-n only, not a true threshold scheme",
                transform=ax.transAxes, ha='center', fontsize=10, 
                style='italic', color='#555555')
    
    def _annotate_tbls_invalid(self, ax: plt.Axes) -> None:
        """
        Overlay 'N/A' text on tBLS + secp256k1 and tBLS + ristretto255 regions.
        This is called after plotting to mark invalid curve combinations.
        """
        # Get current x-axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # We'll add N/A annotations where tBLS would appear with invalid curves
        # This is handled in individual plot methods by checking compatibility
        pass  # Actual annotation done in plot methods where we know positions
        
    def plot_signing_latency(self, df: pd.DataFrame, 
                            title_suffix: str = "",
                            figsize: Tuple[int, int] = (14, 9),
                            save: bool = True) -> str:
        """
        Plot 1.1: Signing Latency vs Number of Participants (All Schemes)
        
        Args:
            df: DataFrame with benchmark data
            title_suffix: Additional text for title
            figsize: Figure size (width, height)
            save: Whether to save to file
            
        Returns:
            Path to saved figure (if save=True)
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Group by scheme and curve
        grouped = df.groupby(['scheme', 'curve'])
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for (scheme, curve), group in grouped:
            if 'sign_ms' not in group.columns:
                continue
            
            # Skip invalid scheme+curve combinations
            if self._skip_if_invalid(scheme, curve):
                if scheme.lower() == 'tbls':
                    tbls_invalid_curves.add(curve)
                continue
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            if scheme.lower() == 'musig2':
                has_musig2 = True
                marker = 'x'  # Special marker for MuSig2
            
            # Sort by n for proper line plotting
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['sign_ms'], 
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Signing Time (ms)', fontsize=14, fontweight='bold')
        
        title = 'Threshold Signature Schemes: Signing Latency vs Swarm Size'
        if title_suffix:
            title += f'\n{title_suffix}'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Set x-axis to show integer values
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        # Add MuSig2 footnote if present
        if has_musig2:
            self._annotate_musig2(ax)
        
        # Annotate tBLS invalid curves
        if tbls_invalid_curves:
            ax.text(0.98, 0.02, 
                    f"N/A for tBLS + {', '.join(sorted(tbls_invalid_curves))}",
                    transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=10, style='italic', color='#C73E1D',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='#C73E1D', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"signing_latency_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            # Also save PDF
            pdf_path = self.output_dir / f"signing_latency_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_verification_time(self, df: pd.DataFrame,
                              title_suffix: str = "",
                              figsize: Tuple[int, int] = (14, 9),
                              save: bool = True) -> str:
        """
        Plot 1.2: Verification Time Comparison
        
        Highlights TBLS batch verification advantage.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        grouped = df.groupby(['scheme', 'curve'])
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for (scheme, curve), group in grouped:
            if 'verify_ms' not in group.columns:
                continue
            
            # Skip invalid scheme+curve combinations
            if self._skip_if_invalid(scheme, curve):
                if scheme.lower() == 'tbls':
                    tbls_invalid_curves.add(curve)
                continue
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            if scheme.lower() == 'musig2':
                has_musig2 = True
                marker = 'x'  # Special marker for MuSig2
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['verify_ms'], 
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Verification Time (ms)', fontsize=14, fontweight='bold')
        
        title = 'Signature Verification Performance\n(Lower is better - TBLS excels at verification)'
        if title_suffix:
            title += f'\n{title_suffix}'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        # Add MuSig2 footnote if present
        if has_musig2:
            self._annotate_musig2(ax)
        
        # Annotate tBLS invalid curves
        if tbls_invalid_curves:
            ax.text(0.98, 0.02, 
                    f"N/A for tBLS + {', '.join(sorted(tbls_invalid_curves))}",
                    transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=10, style='italic', color='#C73E1D',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='#C73E1D', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"verification_time_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"verification_time_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_keygen_time(self, df: pd.DataFrame,
                        dkg_type: Optional[str] = None,
                        figsize: Tuple[int, int] = (14, 9),
                        save: bool = True) -> str:
        """
        Plot 1.3: Key Generation Time (DKG Cost)
        
        Args:
            dkg_type: Filter by 'feldman' or 'pedersen', or None for all
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        plot_df = df.copy()
        if dkg_type and '_phase' in df.columns:
            phase_keyword = 'feldman' if dkg_type == 'feldman' else 'pedersen'
            plot_df = df[df['_phase'].str.contains(phase_keyword, case=False, na=False)]
        
        grouped = plot_df.groupby(['scheme', 'curve'])
        
        for (scheme, curve), group in grouped:
            if 'keygen_ms' not in group.columns:
                continue
                
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['keygen_ms'], 
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Key Generation Time (ms)', fontsize=14, fontweight='bold')
        
        subtitle = ""
        if dkg_type:
            subtitle = f"DKG Type: {dkg_type.upper()}"
        ax.set_title('DKG Protocol Performance: Key Generation Time\n(One-time setup cost per swarm configuration)', 
                    fontsize=16, fontweight='bold', pad=20)
        if subtitle:
            ax.text(0.5, -0.15, subtitle, transform=ax.transAxes, 
                   ha='center', fontsize=12, style='italic')
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(plot_df['n'].unique())
        ax.set_xticks(n_values)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{dkg_type}" if dkg_type else ""
            output_path = self.output_dir / f"keygen_time{suffix}_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"keygen_time{suffix}_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_total_time_breakdown(self, df: pd.DataFrame,
                                 n_value: Optional[int] = None,
                                 figsize: Tuple[int, int] = (14, 9),
                                 save: bool = True) -> str:
        """
        Plot 1.4: Total Operation Time Breakdown (Stacked Bar Chart)
        
        Shows where time goes: KeyGen + Sign + Verify + Network Overhead
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter to specific n if provided
        plot_df = df.copy()
        if n_value:
            plot_df = df[df['n'] == n_value]
        
        # Calculate components
        if 'total_time_ms' not in plot_df.columns:
            plot_df['total_time_ms'] = (
                plot_df['keygen_ms'].fillna(0) + 
                plot_df['sign_ms'].fillna(0) + 
                plot_df['verify_ms'].fillna(0) + 
                plot_df['network_overhead_ms'].fillna(0)
            )
        
        # Group by scheme-curve
        plot_df['scheme_curve'] = plot_df['scheme'].str.upper() + ' (' + plot_df['curve'] + ')'
        grouped = plot_df.groupby('scheme_curve')
        
        labels = []
        keygen_times = []
        sign_times = []
        verify_times = []
        network_times = []
        
        for name, group in grouped:
            labels.append(name)
            keygen_times.append(group['keygen_ms'].mean())
            sign_times.append(group['sign_ms'].mean())
            verify_times.append(group['verify_ms'].mean())
            network_times.append(group['network_overhead_ms'].mean())
        
        x_pos = range(len(labels))
        
        # Stacked bar chart
        bars1 = ax.bar(x_pos, keygen_times, label='KeyGen', 
                      color='#2E86AB', alpha=0.9, edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x_pos, sign_times, bottom=keygen_times, label='Sign', 
                      color='#A23B72', alpha=0.9, edgecolor='black', linewidth=1.5)
        bars3 = ax.bar(x_pos, verify_times, 
                      bottom=np.array(keygen_times) + np.array(sign_times), 
                      label='Verify', color='#F18F01', alpha=0.9, edgecolor='black', linewidth=1.5)
        bars4 = ax.bar(x_pos, network_times, 
                      bottom=np.array(keygen_times) + np.array(sign_times) + np.array(verify_times), 
                      label='Network Overhead', color='#C73E1D', alpha=0.9, edgecolor='black', linewidth=1.5)
        
        ax.set_xlabel('Scheme (Curve)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title('Total Operation Time Breakdown\n(Shows contribution of each phase)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax.legend(fontsize=12, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add total time labels on top
        totals = np.array(keygen_times) + np.array(sign_times) + np.array(verify_times) + np.array(network_times)
        for i, (x, total) in enumerate(zip(x_pos, totals)):
            ax.text(x, total + 5, f'{total:.1f}ms', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_n{n_value}" if n_value else ""
            output_path = self.output_dir / f"time_breakdown{suffix}_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"time_breakdown{suffix}_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_radar_chart(self, df: pd.DataFrame,
                        normalize: bool = True,
                        figsize: Tuple[int, int] = (10, 10),
                        save: bool = True) -> str:
        """
        Dashboard 6.2: Radar Chart (Spider Plot)
        
        Holistic comparison across multiple dimensions:
        - Signing Speed
        - Verification Speed
        - KeyGen Speed
        - Signature Size (if available)
        - Network Resilience
        """
        # Calculate metrics per scheme
        metrics_df = df.groupby('scheme').agg({
            'sign_ms': 'mean',
            'verify_ms': 'mean',
            'keygen_ms': 'mean',
            'slowdown_percentage': 'mean' if 'slowdown_percentage' in df.columns else lambda x: 0,
        }).reset_index()
        
        if len(metrics_df) == 0:
            print("⚠ No data available for radar chart")
            return None
        
        # Define axes
        categories = ['Sign Speed', 'Verify Speed', 'KeyGen Speed', 'Resilience']
        N = len(categories)
        
        # Normalize metrics (higher is better for all)
        # For times, invert so lower time = higher score
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
        
        for idx, row in metrics_df.iterrows():
            scheme = row['scheme']
            
            # Calculate scores (0-100 scale, higher is better)
            if normalize:
                sign_score = 100 * (1 - row['sign_ms'] / metrics_df['sign_ms'].max())
                verify_score = 100 * (1 - row['verify_ms'] / metrics_df['verify_ms'].max())
                keygen_score = 100 * (1 - row['keygen_ms'] / metrics_df['keygen_ms'].max())
            else:
                sign_score = 100 / row['sign_ms'] if row['sign_ms'] > 0 else 0
                verify_score = 100 / row['verify_ms'] if row['verify_ms'] > 0 else 0
                keygen_score = 100 / row['keygen_ms'] if row['keygen_ms'] > 0 else 0
            
            # Resilience: lower slowdown = higher score
            if 'slowdown_percentage' in row:
                resilience_score = 100 / (1 + abs(row['slowdown_percentage']) / 100)
            else:
                resilience_score = 50  # Default if no stress data
            
            values = [sign_score, verify_score, keygen_score, resilience_score]
            values += values[:1]  # Close the loop
            
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            ax.plot(angles, values, 'o-', linewidth=2, markersize=8, 
                   label=scheme.upper(), color=color, alpha=0.8)
            ax.fill(angles, values, alpha=0.15, color=color)
        
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), categories, fontsize=12)
        ax.set_title('Holistic Scheme Comparison\n(Higher score = better performance)', 
                    fontsize=14, fontweight='bold', pad=20)
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
        ax.grid(True)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"radar_chart_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"radar_chart_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def generate_all_scheme_plots(self, df: pd.DataFrame) -> List[str]:
        """Generate all Category 1 (Scheme Comparison) plots including GROUP A and GROUP B."""
        plots = []
        
        print("\n" + "=" * 60)
        print("Generating Scheme Comparison Plots")
        print("=" * 60)
        
        # Original plots
        try:
            plots.append(self.plot_signing_latency(df))
        except Exception as e:
            print(f"⚠ Could not generate signing latency plot: {e}")
        
        try:
            plots.append(self.plot_verification_time(df))
        except Exception as e:
            print(f"⚠ Could not generate verification time plot: {e}")
        
        try:
            plots.append(self.plot_keygen_time(df))
        except Exception as e:
            print(f"⚠ Could not generate keygen time plot: {e}")
        
        try:
            plots.append(self.plot_total_time_breakdown(df))
        except Exception as e:
            print(f"⚠ Could not generate time breakdown plot: {e}")
        
        try:
            plots.append(self.plot_radar_chart(df))
        except Exception as e:
            print(f"⚠ Could not generate radar chart: {e}")
        
        # GROUP A - Signing performance plots (DKG-agnostic)
        print("\n--- GROUP A: Signing Performance Plots ---")
        
        try:
            plots.append(self.plot_compatibility_matrix())
        except Exception as e:
            print(f"⚠ Could not generate compatibility matrix: {e}")
        
        try:
            plots.append(self.plot_ops_per_second(df))
        except Exception as e:
            print(f"⚠ Could not generate ops_per_second plot: {e}")
        
        try:
            plots.append(self.plot_overhead_percentage(df))
        except Exception as e:
            print(f"⚠ Could not generate overhead_percentage plot: {e}")
        
        try:
            plots.append(self.plot_efficiency_score(df))
        except Exception as e:
            print(f"⚠ Could not generate efficiency_score plot: {e}")
        
        try:
            plots.append(self.plot_threshold_sensitivity(df))
        except Exception as e:
            print(f"⚠ Could not generate threshold_sensitivity plot: {e}")
        
        try:
            plots.append(self.plot_slowdown_vs_n(df))
        except Exception as e:
            print(f"⚠ Could not generate slowdown_vs_n plot: {e}")
        
        try:
            plots.append(self.plot_signing_latency_shaded(df))
        except Exception as e:
            print(f"⚠ Could not generate signing_latency_shaded plot: {e}")
        
        try:
            plots.append(self.plot_signing_latency_grid(df))
        except Exception as e:
            print(f"⚠ Could not generate signing_latency_grid plot: {e}")
        
        # GROUP B - DKG setup phase plots
        print("\n--- GROUP B: DKG Setup Phase Plots ---")
        
        try:
            plots.append(self.plot_dkg_keygen_vs_n(df))
        except Exception as e:
            print(f"⚠ Could not generate dkg_keygen_vs_n plot: {e}")
        
        try:
            plots.append(self.plot_dkg_keygen_vs_loss(df))
        except Exception as e:
            print(f"⚠ Could not generate dkg_keygen_vs_loss plot: {e}")
        
        try:
            plots.append(self.plot_dkg_overhead_vs_n(df))
        except Exception as e:
            print(f"⚠ Could not generate dkg_overhead_vs_n plot: {e}")
        
        try:
            plots.append(self.plot_dkg_pedersen_overhead_cost(df))
        except Exception as e:
            print(f"⚠ Could not generate dkg_pedersen_overhead_cost plot: {e}")
        
        try:
            plots.append(self.plot_dkg_keygen_amortization(df))
        except Exception as e:
            print(f"⚠ Could not generate dkg_keygen_amortization plot: {e}")
        
        print(f"\n✓ Generated {len(plots)} scheme comparison plots")
        return plots


if __name__ == "__main__":
    import sys
    from data_loader import load_benchmark_data
    
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/figures"
    
    print("Loading benchmark data...")
    df = load_benchmark_data(results_dir)
    
    comparator = SchemeComparator(output_dir)
    comparator.generate_all_scheme_plots(df)
