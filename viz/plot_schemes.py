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
    
    def _annotate_tbls_invalid(self, ax: plt.Axes, invalid_curves: set = None) -> None:
        """
        Overlay 'N/A' text on tBLS + secp256k1 and tBLS + ristretto255 regions.
        This is called after plotting to mark invalid curve combinations.
        
        Args:
            ax: Matplotlib axes object
            invalid_curves: Set of curve names that are invalid for tBLS
        """
        if invalid_curves:
            ax.text(0.98, 0.02, 
                    f"N/A for tBLS + {', '.join(sorted(invalid_curves))}",
                    transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=10, style='italic', color='#C73E1D',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='#C73E1D', alpha=0.8))
        
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
    
    # =========================================================================
    # GROUP A - Signing Performance Plots (DKG-agnostic)
    # =========================================================================
    
    def plot_compatibility_matrix(self, figsize: Tuple[int, int] = (14, 6),
                                  save: bool = True) -> str:
        """
        Plot compatibility matrices: scheme × curve and scheme × DKG type.
        
        Shows valid (green), suboptimal (yellow), and invalid (red) combinations.
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Color mapping
        color_map = {'valid': '#4CAF50', 'suboptimal': '#FFC107', 'invalid': '#F44336'}
        
        # Matrix 1: Scheme × Curve
        schemes = ['srts', 'frost', 'musig2', 'tbls']
        curves = ['secp256k1', 'bls12-381', 'ristretto255']
        
        matrix_curve = np.zeros((len(schemes), len(curves)))
        labels_curve = []
        
        for i, scheme in enumerate(schemes):
            row_labels = []
            for j, curve in enumerate(curves):
                status = COMPATIBILITY['curve'].get((scheme, curve), 'invalid')
                matrix_curve[i, j] = {'valid': 2, 'suboptimal': 1, 'invalid': 0}[status]
                row_labels.append(status.capitalize())
            labels_curve.append(row_labels)
        
        im1 = axes[0].imshow(matrix_curve, cmap='RdYlGn', vmin=0, vmax=2, aspect='auto')
        axes[0].set_xticks(range(len(curves)))
        axes[0].set_yticks(range(len(schemes)))
        axes[0].set_xticklabels([c.upper().replace('-', '-') for c in curves], fontsize=10)
        axes[0].set_yticklabels([s.upper() for s in schemes], fontsize=10)
        axes[0].set_xlabel('Curve', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Scheme', fontsize=12, fontweight='bold')
        axes[0].set_title('Scheme × Curve Compatibility', fontsize=14, fontweight='bold')
        
        # Add text labels
        for i in range(len(schemes)):
            for j in range(len(curves)):
                text = axes[0].text(j, i, labels_curve[i][j], ha='center', va='center',
                                   fontsize=9, color='black' if matrix_curve[i,j] == 1 else 'white')
        
        # Matrix 2: Scheme × DKG Type
        dkg_types = ['feldman_vss', 'pedersen_dkg', 'not_applicable']
        
        matrix_dkg = np.zeros((len(schemes), len(dkg_types)))
        labels_dkg = []
        
        for i, scheme in enumerate(schemes):
            row_labels = []
            for j, dkg in enumerate(dkg_types):
                status = COMPATIBILITY['dkg'].get((scheme, dkg), 'invalid')
                matrix_dkg[i, j] = {'valid': 2, 'suboptimal': 1, 'invalid': 0}[status]
                dkg_short = dkg.replace('_', '\n').replace('not\napplicable', 'N/A')
                row_labels.append(status.capitalize())
            labels_dkg.append(row_labels)
        
        im2 = axes[1].imshow(matrix_dkg, cmap='RdYlGn', vmin=0, vmax=2, aspect='auto')
        axes[1].set_xticks(range(len(dkg_types)))
        axes[1].set_yticks(range(len(schemes)))
        axes[1].set_xticklabels(['Feldman\nVSS', 'Pedersen\nDKG', 'N/A'], fontsize=10)
        axes[1].set_yticklabels([s.upper() for s in schemes], fontsize=10)
        axes[1].set_xlabel('DKG Type', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Scheme', fontsize=12, fontweight='bold')
        axes[1].set_title('Scheme × DKG Type Compatibility', fontsize=14, fontweight='bold')
        
        # Add text labels
        for i in range(len(schemes)):
            for j in range(len(dkg_types)):
                text = axes[1].text(j, i, labels_dkg[i][j], ha='center', va='center',
                                   fontsize=9, color='black' if matrix_dkg[i,j] == 1 else 'white')
        
        # Add colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = fig.colorbar(im2, cax=cbar_ax)
        cbar.set_ticks([0, 1, 2])
        cbar.set_ticklabels(['Invalid', 'Suboptimal', 'Valid'])
        
        plt.tight_layout(rect=[0, 0, 0.9, 1])
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"compatibility_matrix_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"compatibility_matrix_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_ops_per_second(self, df: pd.DataFrame,
                           figsize: Tuple[int, int] = (14, 9),
                           save: bool = True) -> str:
        """
        Plot operations per second vs n per scheme+curve.
        
        Higher is better. Skip invalid combinations per COMPATIBILITY.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        grouped = df.groupby(['scheme', 'curve'])
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for (scheme, curve), group in grouped:
            if 'ops_per_second' not in group.columns:
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
                marker = 'x'
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['ops_per_second'],
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Operations per Second', fontsize=14, fontweight='bold')
        ax.set_title('Signing Throughput vs Swarm Size\n(Higher is better)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        if has_musig2:
            self._annotate_musig2(ax)
        
        if tbls_invalid_curves:
            ax.text(0.98, 0.02,
                   f"N/A for tBLS + {', '.join(sorted(tbls_invalid_curves))}",
                   transform=ax.transAxes, ha='right', va='bottom',
                   fontsize=10, style='italic', color='#C73E1D',
                   bbox=dict(boxstyle='round', facecolor='white', edgecolor='#C73E1D', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"ops_per_second_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"ops_per_second_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_overhead_percentage(self, df: pd.DataFrame,
                                figsize: Tuple[int, int] = (14, 9),
                                save: bool = True) -> str:
        """
        Plot overhead percentage vs n per scheme+curve.
        
        Shows how much of total time is network overhead.
        Lower is better. Skip invalid combinations.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        grouped = df.groupby(['scheme', 'curve'])
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for (scheme, curve), group in grouped:
            if 'overhead_percentage' not in group.columns:
                continue
            
            if self._skip_if_invalid(scheme, curve):
                if scheme.lower() == 'tbls':
                    tbls_invalid_curves.add(curve)
                continue
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            if scheme.lower() == 'musig2':
                has_musig2 = True
                marker = 'x'
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['overhead_percentage'],
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Network Overhead (%)', fontsize=14, fontweight='bold')
        ax.set_title('Network Overhead as Percentage of Total Time\n(Lower is better)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        if has_musig2:
            self._annotate_musig2(ax)
        
        if tbls_invalid_curves:
            ax.text(0.98, 0.02,
                   f"N/A for tBLS + {', '.join(sorted(tbls_invalid_curves))}",
                   transform=ax.transAxes, ha='right', va='bottom',
                   fontsize=10, style='italic', color='#C73E1D',
                   bbox=dict(boxstyle='round', facecolor='white', edgecolor='#C73E1D', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"overhead_percentage_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"overhead_percentage_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_efficiency_score(self, df: pd.DataFrame,
                             figsize: Tuple[int, int] = (14, 9),
                             save: bool = True) -> str:
        """
        Bar chart of efficiency score per scheme+curve.
        
        Lower is better. Skip invalid combinations.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if 'efficiency_score' not in df.columns:
            print("⚠ efficiency_score column not found")
            return None
        
        # Aggregate by scheme+curve
        agg_df = df.groupby(['scheme', 'curve'])['efficiency_score'].mean().reset_index()
        
        labels = []
        scores = []
        colors = []
        
        for _, row in agg_df.iterrows():
            scheme = row['scheme']
            curve = row['curve']
            
            if self._skip_if_invalid(scheme, curve):
                continue
            
            label = f"{scheme.upper()}\n({curve})"
            labels.append(label)
            scores.append(row['efficiency_score'])
            colors.append(self.SCHEME_COLORS.get(scheme, '#333333'))
        
        x_pos = range(len(labels))
        
        bars = ax.bar(x_pos, scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax.set_xlabel('Scheme (Curve)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Efficiency Score (lower is better)', fontsize=14, fontweight='bold')
        ax.set_title('Overall Efficiency Score by Scheme and Curve\n(Normalized sum of keygen + sign + verify times)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on top of bars
        for i, (x, score) in enumerate(zip(x_pos, scores)):
            ax.text(x, score + 0.05, f'{score:.2f}', ha='center', va='bottom',
                   fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"efficiency_score_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"efficiency_score_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_threshold_sensitivity(self, df: pd.DataFrame,
                                  n_fixed: int = 20,
                                  figsize: Tuple[int, int] = (14, 9),
                                  save: bool = True) -> str:
        """
        Fix n, vary t from ceil(n/2) to n-1, plot sign_ms vs t/n ratio.
        
        Skip tBLS (t-independent) and MuSig2 (t always equals n).
        Only makes sense for SRTS and FROST.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter to fixed n
        df_n = df[df['n'] == n_fixed].copy()
        
        if len(df_n) == 0:
            print(f"⚠ No data for n={n_fixed}")
            return None
        
        # Filter to SRTS and FROST only
        df_filtered = df_n[df_n['scheme'].isin(['srts', 'frost'])]
        
        if len(df_filtered) == 0:
            print("⚠ No SRTS or FROST data available for threshold sensitivity")
            return None
        
        # Calculate t/n ratio
        df_filtered['t_ratio'] = df_filtered['t'] / df_filtered['n']
        
        # Group by scheme
        for scheme in ['srts', 'frost']:
            scheme_data = df_filtered[df_filtered['scheme'] == scheme]
            
            if len(scheme_data) == 0:
                continue
            
            # Aggregate by t_ratio
            agg = scheme_data.groupby('t_ratio')['sign_ms'].mean().reset_index()
            
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            ax.plot(agg['t_ratio'], agg['sign_ms'],
                   marker='o', linewidth=2.5, markersize=10,
                   label=f"{scheme.upper()} (n={n_fixed})",
                   color=color, alpha=0.8)
        
        ax.set_xlabel('Threshold Ratio (t/n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Signing Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title(f'Threshold Sensitivity Analysis (n={n_fixed})\n(How signing time varies with threshold ratio)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"threshold_sensitivity_n{n_fixed}_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"threshold_sensitivity_n{n_fixed}_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_slowdown_vs_n(self, df: pd.DataFrame,
                          figsize: Tuple[int, int] = (14, 9),
                          save: bool = True) -> str:
        """
        Plot slowdown_percentage vs n at each fixed loss rate.
        
        Shows which schemes degrade faster as swarm grows under stress.
        Do not split by DKG type.
        """
        if 'slowdown_percentage' not in df.columns:
            print("⚠ slowdown_percentage column not found")
            return None
        
        # Get unique loss rates (> 0)
        loss_rates = sorted(df[df['loss_rate'] > 0]['loss_rate'].unique())
        
        if len(loss_rates) == 0:
            print("⚠ No stress test data (loss_rate > 0) available")
            return None
        
        n_cols = 2
        n_rows = (len(loss_rates) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 8 * n_rows // 2))
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        
        for idx, loss_rate in enumerate(loss_rates):
            ax = axes[idx]
            df_loss = df[abs(df['loss_rate'] - loss_rate) < 0.001]
            
            grouped = df_loss.groupby(['scheme', 'curve'])
            
            has_musig2 = False
            tbls_invalid_curves = set()
            
            for (scheme, curve), group in grouped:
                if 'slowdown_percentage' not in group.columns:
                    continue
                
                if self._skip_if_invalid(scheme, curve):
                    if scheme.lower() == 'tbls':
                        tbls_invalid_curves.add(curve)
                    continue
                
                label = f"{scheme.upper()} ({curve})"
                color = self.SCHEME_COLORS.get(scheme, '#333333')
                marker = self.CURVE_MARKERS.get(curve, 'o')
                
                if scheme.lower() == 'musig2':
                    has_musig2 = True
                    marker = 'x'
                
                group = group.sort_values('n')
                
                ax.plot(group['n'], group['slowdown_percentage'],
                       marker=marker, linewidth=2, markersize=8,
                       label=label, color=color, alpha=0.8)
            
            ax.set_xlabel('Number of Participants (n)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Slowdown (%)', fontsize=12, fontweight='bold')
            ax.set_title(f'Packet Loss: {loss_rate*100:.1f}%', fontsize=13, fontweight='bold')
            ax.legend(fontsize=9, loc='upper left', framealpha=0.8)
            ax.grid(True, alpha=0.3)
            
            n_values = sorted(df['n'].unique())
            ax.set_xticks(n_values)
            
            if has_musig2:
                self._annotate_musig2(ax)
        
        # Hide unused subplots
        for idx in range(len(loss_rates), len(axes)):
            axes[idx].set_visible(False)
        
        fig.suptitle('Performance Degradation vs Swarm Size Under Network Stress\n(Lower slowdown = better resilience)',
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"slowdown_vs_n_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"slowdown_vs_n_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_signing_latency_shaded(self, df: pd.DataFrame,
                                   figsize: Tuple[int, int] = (14, 9),
                                   save: bool = True) -> str:
        """
        One line per scheme at 0% loss with shaded band to 5% loss.
        
        Shows degradation envelope. Do not split by DKG type.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get baseline (0% loss) and max stress (5% loss)
        df_baseline = df[abs(df['loss_rate'] - 0.0) < 0.001]
        df_stress = df[abs(df['loss_rate'] - 0.05) < 0.001]  # 5% = 0.05
        
        if len(df_baseline) == 0 or len(df_stress) == 0:
            print("⚠ Need both baseline (0%) and stress (5%) data")
            return None
        
        # Group by scheme
        for scheme in ['srts', 'frost', 'musig2', 'tbls']:
            baseline_scheme = df_baseline[df_baseline['scheme'] == scheme]
            stress_scheme = df_stress[df_stress['scheme'] == scheme]
            
            if len(baseline_scheme) == 0:
                continue
            
            # Aggregate by curve and n
            for curve in baseline_scheme['curve'].unique():
                base_curve = baseline_scheme[baseline_scheme['curve'] == curve]
                stress_curve = stress_scheme[stress_scheme['curve'] == curve]
                
                if self._skip_if_invalid(scheme, curve):
                    continue
                
                # Aggregate by n
                base_agg = base_curve.groupby('n')['sign_ms'].mean()
                stress_agg = stress_curve.groupby('n')['sign_ms'].mean() if len(stress_curve) > 0 else None
                
                color = self.SCHEME_COLORS.get(scheme, '#333333')
                label = f"{scheme.upper()} ({curve})"
                
                # Plot baseline
                ax.plot(base_agg.index, base_agg.values,
                       marker='o', linewidth=2.5, markersize=8,
                       label=label, color=color, alpha=0.9)
                
                # Plot shaded region to stress
                if stress_agg is not None and len(stress_agg) > 0:
                    # Align indices
                    common_n = base_agg.index.intersection(stress_agg.index)
                    if len(common_n) > 0:
                        ax.fill_between(common_n,
                                       base_agg.loc[common_n].values,
                                       stress_agg.loc[common_n].values,
                                       alpha=0.2, color=color)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Signing Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title('Signing Latency: Baseline to 5% Packet Loss Envelope\n(Shaded area shows degradation range)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        # Check for MuSig2
        if 'musig2' in df_baseline['scheme'].values:
            self._annotate_musig2(ax)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"signing_latency_shaded_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"signing_latency_shaded_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_signing_latency_grid(self, df: pd.DataFrame,
                                 figsize: Tuple[int, int] = (18, 14),
                                 save: bool = True) -> str:
        """
        Subplot grid: rows = loss rate (0,1,2,5%), cols = curve.
        
        All schemes per cell. Grey-out invalid scheme+curve combinations.
        Do not split by DKG type.
        """
        loss_rates = [0.0, 0.01, 0.02, 0.05]  # 0%, 1%, 2%, 5%
        curves = ['secp256k1', 'bls12-381', 'ristretto255']
        
        fig, axes = plt.subplots(len(loss_rates), len(curves), figsize=figsize)
        
        for row_idx, loss_rate in enumerate(loss_rates):
            for col_idx, curve in enumerate(curves):
                ax = axes[row_idx, col_idx]
                
                # Filter data
                df_subset = df[(abs(df['loss_rate'] - loss_rate) < 0.001) & 
                              (df['curve'] == curve)]
                
                if len(df_subset) == 0:
                    ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                           transform=ax.transAxes, fontsize=14, color='gray')
                    ax.set_xticks([])
                    ax.set_yticks([])
                else:
                    # Check if this curve is invalid for any scheme
                    for scheme in ['srts', 'frost', 'musig2', 'tbls']:
                        scheme_data = df_subset[df_subset['scheme'] == scheme]
                        
                        if len(scheme_data) == 0:
                            continue
                        
                        if self._skip_if_invalid(scheme, curve):
                            # Grey out invalid combination
                            ax.axhspan(0, 1e10, alpha=0.3, color='gray')
                            ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                                   transform=ax.transAxes, fontsize=20,
                                   color='gray', fontweight='bold')
                            break
                        
                        color = self.SCHEME_COLORS.get(scheme, '#333333')
                        marker = self.CURVE_MARKERS.get(curve, 'o')
                        
                        if scheme.lower() == 'musig2':
                            marker = 'x'
                        
                        group = scheme_data.sort_values('n')
                        
                        ax.plot(group['n'], group['sign_ms'],
                               marker=marker, linewidth=2, markersize=8,
                               label=scheme.upper(), color=color, alpha=0.8)
                    
                    ax.set_xticks(sorted(df['n'].unique()))
                    ax.grid(True, alpha=0.3)
                
                # Labels
                if row_idx == len(loss_rates) - 1:
                    ax.set_xlabel('n', fontsize=11, fontweight='bold')
                if col_idx == 0:
                    ax.set_ylabel('Sign (ms)', fontsize=11, fontweight='bold')
                
                loss_pct = int(loss_rate * 100)
                ax.set_title(f'{curve}\n{loss_pct}% loss', fontsize=12, fontweight='bold')
        
        # Add legend at top
        handles, labels = axes[0, 0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc='upper center', ncol=4,
                      bbox_to_anchor=(0.5, 1.02), fontsize=12)
        
        fig.suptitle('Signing Latency Across Loss Rates and Curves',
                    fontsize=16, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"signing_latency_grid_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"signing_latency_grid_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    # =========================================================================
    # GROUP B - DKG Setup Phase Plots
    # =========================================================================
    
    def _get_dkg_type_from_phase(self, phase: str) -> str:
        """Extract DKG type from phase name."""
        phase_lower = phase.lower()
        if 'pedersen' in phase_lower:
            return 'pedersen_dkg'
        elif 'feldman' in phase_lower:
            return 'feldman_vss'
        return 'not_applicable'
    
    def plot_dkg_keygen_vs_n(self, df: pd.DataFrame,
                            figsize: Tuple[int, int] = (18, 12),
                            save: bool = True) -> str:
        """
        Keygen time vs n, lines split by (scheme + curve + dkg_type).
        
        One subplot per curve so curve effect is visible.
        Only valid combinations per COMPATIBILITY.
        """
        curves = ['secp256k1', 'bls12-381', 'ristretto255']
        
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        for col_idx, curve in enumerate(curves):
            ax = axes[col_idx]
            
            df_curve = df[df['curve'] == curve]
            
            if len(df_curve) == 0:
                ax.text(0.5, 0.5, f'No data for {curve}', ha='center', va='center',
                       transform=ax.transAxes, fontsize=12, color='gray')
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            
            # Add DKG type column
            df_curve = df_curve.copy()
            df_curve['dkg_type'] = df_curve['_phase'].apply(self._get_dkg_type_from_phase)
            
            # Group by scheme and dkg_type
            grouped = df_curve.groupby(['scheme', 'dkg_type'])
            
            for (scheme, dkg_type), group in grouped:
                if 'keygen_ms' not in group.columns:
                    continue
                
                # Skip invalid combinations
                if self._skip_if_invalid(scheme, curve, dkg_type):
                    continue
                
                label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()})"
                color = self.SCHEME_COLORS.get(scheme, '#333333')
                
                # Different linestyles for DKG types
                linestyle = '--' if dkg_type == 'pedersen_dkg' else '-'
                
                group = group.sort_values('n')
                agg = group.groupby('n')['keygen_ms'].mean()
                
                ax.plot(agg.index, agg.values,
                       marker='o', linewidth=2.5, markersize=8,
                       label=label, color=color, alpha=0.8, linestyle=linestyle)
            
            ax.set_xlabel('Number of Participants (n)', fontsize=12, fontweight='bold')
            ax.set_ylabel('KeyGen Time (ms)', fontsize=12, fontweight='bold')
            ax.set_title(f'{curve.upper()}', fontsize=13, fontweight='bold')
            ax.legend(fontsize=9, loc='upper left', framealpha=0.8)
            ax.grid(True, alpha=0.3)
            
            n_values = sorted(df['n'].unique())
            ax.set_xticks(n_values)
        
        fig.suptitle('DKG Key Generation Time vs Swarm Size\n(Solid = Feldman VSS, Dashed = Pedersen DKG)',
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"dkg_keygen_vs_n_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"dkg_keygen_vs_n_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_dkg_keygen_vs_loss(self, df: pd.DataFrame,
                               figsize: Tuple[int, int] = (14, 9),
                               save: bool = True) -> str:
        """
        Keygen time vs loss_rate, split by (scheme + dkg_type).
        
        Pedersen has more rounds so it degrades faster under packet loss.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Add DKG type column
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Filter to DKG phases only
        df_dkg = df_copy[df_copy['dkg_type'].isin(['feldman_vss', 'pedersen_dkg'])]
        
        if len(df_dkg) == 0:
            print("⚠ No DKG data available")
            return None
        
        # Group by scheme and dkg_type
        grouped = df_dkg.groupby(['scheme', 'dkg_type'])
        
        for (scheme, dkg_type), group in grouped:
            if 'keygen_ms' not in group.columns:
                continue
            
            # Skip invalid combinations (use a representative curve)
            # We aggregate across curves here
            curves_in_group = group['curve'].unique()
            skip_all = True
            for curve in curves_in_group:
                if not self._skip_if_invalid(scheme, curve, dkg_type):
                    skip_all = False
                    break
            
            if skip_all:
                continue
            
            label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            linestyle = '--' if dkg_type == 'pedersen_dkg' else '-'
            
            # Aggregate by loss_rate
            agg = group.groupby('loss_rate')['keygen_ms'].mean().reset_index()
            
            ax.plot(agg['loss_rate'] * 100, agg['keygen_ms'],
                   marker='o', linewidth=2.5, markersize=8,
                   label=label, color=color, alpha=0.8, linestyle=linestyle)
        
        ax.set_xlabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
        ax.set_ylabel('KeyGen Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title('DKG Key Generation Time vs Packet Loss\n(Pedersen DKG degrades faster due to more rounds)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"dkg_keygen_vs_loss_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"dkg_keygen_vs_loss_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_dkg_overhead_vs_n(self, df: pd.DataFrame,
                              figsize: Tuple[int, int] = (14, 9),
                              save: bool = True) -> str:
        """
        Network overhead during keygen vs n, split by (scheme + dkg_type).
        
        Shows O(n²) message complexity difference between Feldman and Pedersen.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Add DKG type column
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Filter to DKG phases only
        df_dkg = df_copy[df_copy['dkg_type'].isin(['feldman_vss', 'pedersen_dkg'])]
        
        if len(df_dkg) == 0:
            print("⚠ No DKG data available")
            return None
        
        # Group by scheme and dkg_type
        grouped = df_dkg.groupby(['scheme', 'dkg_type'])
        
        for (scheme, dkg_type), group in grouped:
            if 'network_overhead_ms' not in group.columns:
                continue
            
            # Skip invalid combinations
            curves_in_group = group['curve'].unique()
            skip_all = True
            for curve in curves_in_group:
                if not self._skip_if_invalid(scheme, curve, dkg_type):
                    skip_all = False
                    break
            
            if skip_all:
                continue
            
            label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            linestyle = '--' if dkg_type == 'pedersen_dkg' else '-'
            
            # Aggregate by n
            agg = group.groupby('n')['network_overhead_ms'].mean().reset_index()
            
            ax.plot(agg['n'], agg['network_overhead_ms'],
                   marker='o', linewidth=2.5, markersize=8,
                   label=label, color=color, alpha=0.8, linestyle=linestyle)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Network Overhead During DKG (ms)', fontsize=14, fontweight='bold')
        ax.set_title('DKG Network Communication Overhead vs Swarm Size\n(Shows O(n²) message complexity)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"dkg_overhead_vs_n_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"dkg_overhead_vs_n_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_dkg_pedersen_overhead_cost(self, df: pd.DataFrame,
                                       figsize: Tuple[int, int] = (14, 9),
                                       save: bool = True) -> str:
        """
        Explicit overhead percentage: (pedersen - feldman) / feldman * 100 vs n.
        
        Per valid scheme+curve combination. This is the key number for the paper.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Add DKG type column
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Separate Feldman and Pedersen
        df_feldman = df_copy[df_copy['dkg_type'] == 'feldman_vss']
        df_pedersen = df_copy[df_copy['dkg_type'] == 'pedersen_dkg']
        
        if len(df_feldman) == 0 or len(df_pedersen) == 0:
            print("⚠ Need both Feldman and Pedersen data")
            return None
        
        # Aggregate by scheme, curve, n
        feldman_agg = df_feldman.groupby(['scheme', 'curve', 'n'])['keygen_ms'].mean().reset_index()
        pedersen_agg = df_pedersen.groupby(['scheme', 'curve', 'n'])['keygen_ms'].mean().reset_index()
        
        # Merge on scheme, curve, n
        merged = pd.merge(feldman_agg, pedersen_agg,
                         on=['scheme', 'curve', 'n'],
                         suffixes=('_feldman', '_pedersen'))
        
        if len(merged) == 0:
            print("⚠ No matching scheme+curve+n combinations found")
            return None
        
        # Calculate overhead percentage
        merged['overhead_pct'] = ((merged['keygen_ms_pedersen'] - merged['keygen_ms_feldman']) /
                                  merged['keygen_ms_feldman'] * 100)
        
        # Plot per scheme+curve
        grouped = merged.groupby(['scheme', 'curve'])
        
        for (scheme, curve), group in grouped:
            if self._skip_if_invalid(scheme, curve):
                continue
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['overhead_pct'],
                   marker='o', linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Pedersen Overhead (%)', fontsize=14, fontweight='bold')
        ax.set_title('Pedersen DKG Security Premium\n(Extra keygen time compared to Feldman VSS)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"dkg_pedersen_overhead_cost_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"dkg_pedersen_overhead_cost_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_dkg_keygen_amortization(self, df: pd.DataFrame,
                                    figsize: Tuple[int, int] = (14, 9),
                                    save: bool = True) -> str:
        """
        Keygen_ms / sign_ms ratio vs n, split by dkg_type.
        
        Shows how many signatures needed before DKG cost amortizes.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Add DKG type column
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Filter to DKG phases
        df_dkg = df_copy[df_copy['dkg_type'].isin(['feldman_vss', 'pedersen_dkg'])]
        
        if len(df_dkg) == 0:
            print("⚠ No DKG data available")
            return None
        
        # Calculate amortization ratio
        df_dkg = df_dkg[df_dkg['sign_ms'] > 0]  # Avoid division by zero
        df_dkg['amortization_ratio'] = df_dkg['keygen_ms'] / df_dkg['sign_ms']
        
        # Group by scheme, curve, dkg_type
        grouped = df_dkg.groupby(['scheme', 'curve', 'dkg_type'])
        
        for (scheme, curve, dkg_type), group in grouped:
            if 'amortization_ratio' not in group.columns:
                continue
            
            # Skip invalid combinations
            if self._skip_if_invalid(scheme, curve, dkg_type):
                continue
            
            label = f"{scheme.upper()} ({curve}, {dkg_type.replace('_', ' ').title()})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            linestyle = '--' if dkg_type == 'pedersen_dkg' else '-'
            
            # Aggregate by n
            agg = group.groupby('n')['amortization_ratio'].mean().reset_index()
            
            ax.plot(agg['n'], agg['amortization_ratio'],
                   marker='o', linewidth=2.5, markersize=8,
                   label=label, color=color, alpha=0.8, linestyle=linestyle)
        
        ax.axhline(y=1, color='gray', linestyle=':', linewidth=2, alpha=0.5,
                  label='Break-even (1 signature)')
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('KeyGen/Sign Ratio', fontsize=14, fontweight='bold')
        ax.set_title('DKG Cost Amortization Analysis\n(Ratio = keygen_time / sign_time; lower = faster break-even)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=10, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        n_values = sorted(df['n'].unique())
        ax.set_xticks(n_values)
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"dkg_keygen_amortization_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"dkg_keygen_amortization_{timestamp}.pdf"
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
