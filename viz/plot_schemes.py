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
    
    def plot_compatibility_matrix(self, figsize: Tuple[int, int] = (14, 6),
                                   save: bool = True) -> str:
        """
        GROUP A: Compatibility matrix heatmaps.
        
        Two side-by-side heatmaps:
        - Left: Scheme × Curve compatibility
        - Right: Scheme × DKG compatibility
        
        Colors: green=valid, yellow=suboptimal, red=invalid
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Color mapping
        color_map = {'valid': '#4CAF50', 'suboptimal': '#FFC107', 'invalid': '#F44336'}
        
        # === Left: Scheme × Curve ===
        schemes = ['srts', 'frost', 'musig2', 'tbls']
        curves = ['secp256k1', 'bls12-381', 'ristretto255']
        
        curve_matrix = np.zeros((len(schemes), len(curves)), dtype=int)
        curve_labels = np.empty((len(schemes), len(curves)), dtype=object)
        
        for i, scheme in enumerate(schemes):
            for j, curve in enumerate(curves):
                status = COMPATIBILITY['curve'].get((scheme, curve), 'invalid')
                curve_matrix[i, j] = {'valid': 2, 'suboptimal': 1, 'invalid': 0}[status]
                curve_labels[i, j] = status
        
        im1 = axes[0].imshow(curve_matrix, cmap='RdYlGn', vmin=0, vmax=2, aspect='auto')
        axes[0].set_xticks(range(len(curves)))
        axes[0].set_yticks(range(len(schemes)))
        axes[0].set_xticklabels(curves, fontsize=11)
        axes[0].set_yticklabels([s.upper() for s in schemes], fontsize=11)
        axes[0].set_xlabel('Curve', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Scheme', fontsize=12, fontweight='bold')
        axes[0].set_title('Scheme × Curve Compatibility', fontsize=14, fontweight='bold')
        
        # Add text labels
        for i in range(len(schemes)):
            for j in range(len(curves)):
                text_color = 'white' if curve_matrix[i, j] == 0 else 'black'
                axes[0].text(j, i, curve_labels[i, j].upper(), ha='center', va='center',
                            fontsize=10, fontweight='bold', color=text_color)
        
        # === Right: Scheme × DKG ===
        dkg_types = ['feldman_vss', 'pedersen_dkg', 'not_applicable']
        
        dkg_matrix = np.zeros((len(schemes), len(dkg_types)), dtype=int)
        dkg_labels = np.empty((len(schemes), len(dkg_types)), dtype=object)
        
        for i, scheme in enumerate(schemes):
            for j, dkg in enumerate(dkg_types):
                status = COMPATIBILITY['dkg'].get((scheme, dkg), 'invalid')
                dkg_matrix[i, j] = {'valid': 2, 'suboptimal': 1, 'invalid': 0}[status]
                dkg_labels[i, j] = status
        
        im2 = axes[1].imshow(dkg_matrix, cmap='RdYlGn', vmin=0, vmax=2, aspect='auto')
        axes[1].set_xticks(range(len(dkg_types)))
        axes[1].set_yticks(range(len(schemes)))
        axes[1].set_xticklabels(['Feldman VSS', 'Pedersen DKG', 'N/A'], fontsize=11, rotation=45, ha='right')
        axes[1].set_yticklabels([s.upper() for s in schemes], fontsize=11)
        axes[1].set_xlabel('DKG Type', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Scheme', fontsize=12, fontweight='bold')
        axes[1].set_title('Scheme × DKG Compatibility', fontsize=14, fontweight='bold')
        
        # Add text labels
        for i in range(len(schemes)):
            for j in range(len(dkg_types)):
                text_color = 'white' if dkg_matrix[i, j] == 0 else 'black'
                axes[1].text(j, i, dkg_labels[i, j].upper(), ha='center', va='center',
                            fontsize=10, fontweight='bold', color=text_color)
        
        # Add colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = fig.colorbar(im2, cax=cbar_ax)
        cbar.set_ticks([0, 1, 2])
        cbar.set_ticklabels(['Invalid', 'Suboptimal', 'Valid'])
        cbar.set_label('Compatibility Status', fontsize=12)
        
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
        GROUP A: Operations per second vs n per scheme+curve.
        
        Shows throughput capacity. Higher is better.
        Skips invalid scheme+curve combinations.
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
        ax.set_title('Throughput Capacity by Scheme and Curve\\n(Higher is better)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
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
        GROUP A: Overhead percentage vs n per scheme+curve.
        
        Shows what fraction of total time is network overhead.
        Lower is better.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if 'overhead_percentage' not in df.columns:
            print("⚠ overhead_percentage column not available")
            return None
        
        grouped = df.groupby(['scheme', 'curve'])
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for (scheme, curve), group in grouped:
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
            
            ax.plot(group['n'], group['overhead_percentage'],
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Network Overhead (%)', fontsize=14, fontweight='bold')
        ax.set_title('Network Overhead as Percentage of Total Time\\n(Lower is better)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
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
        GROUP A: Bar chart of efficiency_score per scheme+curve.
        
        Lower efficiency score is better (less slowdown under stress).
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if 'efficiency_score' not in df.columns:
            print("⚠ efficiency_score column not available")
            return None
        
        # Aggregate by scheme+curve
        agg_df = df.groupby(['scheme', 'curve'])['efficiency_score'].mean().reset_index()
        
        # Filter out invalid combinations
        valid_rows = []
        tbls_invalid_curves = set()
        
        for _, row in agg_df.iterrows():
            scheme = row['scheme']
            curve = row['curve']
            
            if self._skip_if_invalid(scheme, curve):
                if scheme.lower() == 'tbls':
                    tbls_invalid_curves.add(curve)
                continue
            
            valid_rows.append(row)
        
        if not valid_rows:
            print("⚠ No valid data for efficiency score plot")
            return None
        
        valid_df = pd.DataFrame(valid_rows)
        
        # Create bar positions
        x_pos = range(len(valid_df))
        colors = [self.SCHEME_COLORS.get(row['scheme'], '#333333') for _, row in valid_df.iterrows()]
        labels = [f"{row['scheme'].upper()} ({row['curve']})" for _, row in valid_df.iterrows()]
        
        bars = ax.bar(x_pos, valid_df['efficiency_score'], color=colors, alpha=0.8, edgecolor='black')
        
        ax.set_xlabel('Scheme (Curve)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Efficiency Score', fontsize=14, fontweight='bold')
        ax.set_title('Scheme Efficiency Comparison\\n(Lower score = less degradation under stress)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (idx, row) in enumerate(valid_df.iterrows()):
            ax.text(i, row['efficiency_score'] + 0.5, f"{row['efficiency_score']:.2f}",
                   ha='center', va='bottom', fontsize=10)
        
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
        GROUP A: Signing time vs t/n ratio at fixed n.
        
        Only for SRTS and FROST (threshold-sensitive schemes).
        Skips tBLS (t-independent) and MuSig2 (t always equals n).
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter to fixed n
        plot_df = df[df['n'] == n_fixed].copy()
        
        if len(plot_df) == 0:
            print(f"⚠ No data for n={n_fixed}")
            return None
        
        # Calculate t/n ratio
        plot_df['t_ratio'] = plot_df['t'] / plot_df['n']
        
        # Filter to only SRTS and FROST
        plot_df = plot_df[plot_df['scheme'].isin(['srts', 'frost'])]
        
        if len(plot_df) == 0:
            print("⚠ No threshold-sensitive schemes (SRTS/FROST) found")
            return None
        
        grouped = plot_df.groupby(['scheme', 'curve'])
        
        for (scheme, curve), group in grouped:
            if self._skip_if_invalid(scheme, curve):
                continue
            
            if 'sign_ms' not in group.columns:
                continue
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            group = group.sort_values('t_ratio')
            
            ax.plot(group['t_ratio'], group['sign_ms'],
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Threshold Ratio (t/n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Signing Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title(f'Threshold Sensitivity Analysis (n={n_fixed})\\n(How signing cost varies with threshold)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        ax.text(0.02, 0.98, "Note: tBLS is t-independent (flat)\nMuSig2 is n-of-n only (t/n=1)",
               transform=ax.transAxes, ha='left', va='top',
               fontsize=10, style='italic', color='#555555',
               bbox=dict(boxstyle='round', facecolor='white', edgecolor='#555555', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"threshold_sensitivity_{timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
            
            pdf_path = self.output_dir / f"threshold_sensitivity_{timestamp}.pdf"
            plt.savefig(pdf_path, bbox_inches='tight')
            print(f"✓ Saved: {pdf_path}")
            
            plt.close()
            return str(output_path)
        
        return None
    
    def plot_slowdown_vs_n(self, df: pd.DataFrame,
                            figsize: Tuple[int, int] = (14, 9),
                            save: bool = True) -> str:
        """
        GROUP A: Slowdown percentage vs n at each fixed loss rate.
        
        Shows which schemes degrade faster as swarm grows under stress.
        Does not split by DKG type.
        """
        if 'slowdown_percentage' not in df.columns:
            print("⚠ slowdown_percentage column not available")
            return None
        
        # Get unique loss rates
        loss_rates = sorted(df['loss_rate'].unique())
        
        if len(loss_rates) == 0:
            print("⚠ No loss rate data available")
            return None
        
        # Create subplot for each loss rate
        n_cols = 2
        n_rows = (len(loss_rates) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 6 * n_rows))
        axes = axes.flatten() if n_rows > 1 else [axes] if isinstance(axes, np.ndarray) else [axes]
        
        for idx, loss_rate in enumerate(loss_rates):
            if idx >= len(axes):
                break
            
            ax = axes[idx]
            loss_df = df[df['loss_rate'] == loss_rate].copy()
            
            grouped = loss_df.groupby(['scheme', 'curve'])
            
            has_musig2 = False
            tbls_invalid_curves = set()
            
            for (scheme, curve), group in grouped:
                if self._skip_if_invalid(scheme, curve):
                    if scheme.lower() == 'tbls':
                        tbls_invalid_curves.add(curve)
                    continue
                
                if 'slowdown_percentage' not in group.columns:
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
            ax.set_title(f'Loss Rate = {loss_rate*100:.0f}%', fontsize=13, fontweight='bold')
            ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
            ax.grid(True, alpha=0.3)
            
            n_values = sorted(loss_df['n'].unique())
            ax.set_xticks(n_values)
            
            # Add MuSig2 footnote if present
            if has_musig2:
                ax.text(0.5, -0.25, "× MuSig2 is n-of-n only",
                       transform=ax.transAxes, ha='center', fontsize=9,
                       style='italic', color='#555555')
        
        # Hide unused subplots
        for idx in range(len(loss_rates), len(axes)):
            axes[idx].set_visible(False)
        
        fig.suptitle('Slowdown vs Swarm Size Under Network Stress',
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
        GROUP A: One line per scheme at 0% loss with shaded band to 5% loss.
        
        Shows degradation envelope from best case (0%) to moderate stress (5%).
        Does not split by DKG type.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get data at 0% and 5% loss
        loss_0 = df[df['loss_rate'] == 0.0]
        loss_5 = df[df['loss_rate'] == 0.05]
        
        if len(loss_0) == 0 or len(loss_5) == 0:
            print("⚠ Need both 0% and 5% loss rate data")
            return None
        
        # Group by scheme+curve
        schemes_curves = set(loss_0.groupby(['scheme', 'curve']).groups.keys())
        
        has_musig2 = False
        tbls_invalid_curves = set()
        
        for scheme, curve in schemes_curves:
            if self._skip_if_invalid(scheme, curve):
                if scheme.lower() == 'tbls':
                    tbls_invalid_curves.add(curve)
                continue
            
            group_0 = loss_0[(loss_0['scheme'] == scheme) & (loss_0['curve'] == curve)]
            group_5 = loss_5[(loss_5['scheme'] == scheme) & (loss_5['curve'] == curve)]
            
            if 'sign_ms' not in group_0.columns or 'sign_ms' not in group_5.columns:
                continue
            
            # Merge on n to get matching points
            merged = pd.merge(
                group_0[['n', 'sign_ms']].rename(columns={'sign_ms': 'sign_0'}),
                group_5[['n', 'sign_ms']].rename(columns={'sign_ms': 'sign_5'}),
                on='n', how='inner'
            )
            
            if len(merged) == 0:
                continue
            
            merged = merged.sort_values('n')
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            if scheme.lower() == 'musig2':
                has_musig2 = True
                marker = 'x'
            
            # Plot main line (0% loss)
            ax.plot(merged['n'], merged['sign_0'],
                   marker=marker, linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.9)
            
            # Plot shaded area between 0% and 5%
            ax.fill_between(merged['n'], merged['sign_0'], merged['sign_5'],
                           alpha=0.2, color=color, label=None)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Signing Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title('Signing Latency Degradation Envelope\\n(Solid: 0% loss, Shaded: up to 5% loss)',
                    fontsize=16, fontweight='bold', pad=20)
        
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
                                   figsize: Tuple[int, int] = (18, 12),
                                   save: bool = True) -> str:
        """
        GROUP A: Subplot grid of signing latency.
        
        Rows = loss rate (0, 1, 2, 5%)
        Cols = curve (secp256k1, bls12-381, ristretto255)
        All schemes per cell, grey-out invalid combinations.
        Does not split by DKG type.
        """
        loss_rates = sorted(df['loss_rate'].unique())
        curves = ['secp256k1', 'bls12-381', 'ristretto255']
        
        # Filter to common loss rates for the grid
        target_losses = [0.0, 0.01, 0.02, 0.05]
        loss_rates = [lr for lr in loss_rates if lr in target_losses]
        
        if len(loss_rates) == 0:
            print("⚠ No matching loss rate data")
            return None
        
        n_rows = len(loss_rates)
        n_cols = len(curves)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
        
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        if n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for row_idx, loss_rate in enumerate(loss_rates):
            for col_idx, curve in enumerate(curves):
                ax = axes[row_idx][col_idx]
                
                loss_df = df[(df['loss_rate'] == loss_rate) & (df['curve'] == curve)]
                
                if len(loss_df) == 0:
                    ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes,
                           ha='center', va='center', fontsize=14, color='#999999')
                    ax.set_facecolor('#f5f5f5')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    continue
                
                grouped = loss_df.groupby(['scheme', 'curve'])
                
                has_data = False
                for (scheme, c), group in grouped:
                    if self._skip_if_invalid(scheme, curve):
                        # Grey out invalid combinations
                        continue
                    
                    if 'sign_ms' not in group.columns:
                        continue
                    
                    has_data = True
                    label = f"{scheme.upper()}"
                    color = self.SCHEME_COLORS.get(scheme, '#333333')
                    marker = self.CURVE_MARKERS.get(curve, 'o')
                    
                    if scheme.lower() == 'musig2':
                        marker = 'x'
                    
                    group = group.sort_values('n')
                    
                    ax.plot(group['n'], group['sign_ms'],
                           marker=marker, linewidth=2, markersize=8,
                           label=label, color=color, alpha=0.8)
                
                if not has_data:
                    ax.text(0.5, 0.5, 'Invalid\nCombination', transform=ax.transAxes,
                           ha='center', va='center', fontsize=12, color='#999999')
                    ax.set_facecolor('#f5f5f5')
                
                # Set titles and labels
                if row_idx == 0:
                    ax.set_title(curve, fontsize=12, fontweight='bold')
                if col_idx == 0:
                    ax.set_ylabel(f'{loss_rate*100:.0f}% Loss', fontsize=11, fontweight='bold')
                
                ax.grid(True, alpha=0.3)
                ax.set_xticks(sorted(loss_df['n'].unique()))
        
        # Add common labels
        fig.text(0.5, 0.02, 'Number of Participants (n)', ha='center', fontsize=14, fontweight='bold')
        fig.text(0.02, 0.5, 'Signing Time (ms)', va='center', rotation='vertical', fontsize=14, fontweight='bold')
        fig.suptitle('Signing Latency Across Loss Rates and Curves',
                    fontsize=16, fontweight='bold', y=0.995)
        
        # Add legend
        handles = [plt.Line2D([0], [0], marker='o', color='w',
                             markerfacecolor=self.SCHEME_COLORS.get(scheme, '#333'),
                             markersize=10, label=scheme.upper())
                  for scheme in ['srts', 'frost', 'musig2', 'tbls']]
        fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.98),
                  ncol=4, fontsize=11)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
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
    
    def _get_dkg_type_from_phase(self, phase: str) -> str:
        """
        Extract DKG type from _phase column value.
        """
        phase_lower = phase.lower()
        if 'pedersen' in phase_lower:
            return 'pedersen_dkg'
        elif 'feldman' in phase_lower:
            return 'feldman_vss'
        return 'not_applicable'
    
    def plot_dkg_keygen_vs_n(self, df: pd.DataFrame,
                              figsize: Tuple[int, int] = (14, 9),
                              save: bool = True) -> str:
        """
        GROUP B: KeyGen time vs n, split by (scheme + curve + dkg_type).
        
        One subplot per curve so curve effect is visible.
        Only valid combinations per COMPATIBILITY.
        """
        if '_phase' not in df.columns:
            print("⚠ _phase column not available for DKG analysis")
            return None
        
        curves = df['curve'].unique()
        n_curves = len(curves)
        
        if n_curves == 0:
            print("⚠ No curve data available")
            return None
        
        fig, axes = plt.subplots(1, n_curves, figsize=(6 * n_curves, 8), sharey=True)
        if n_curves == 1:
            axes = [axes]
        
        for col_idx, curve in enumerate(sorted(curves)):
            ax = axes[col_idx]
            curve_df = df[df['curve'] == curve].copy()
            curve_df['dkg_type'] = curve_df['_phase'].apply(self._get_dkg_type_from_phase)
            
            grouped = curve_df.groupby(['scheme', 'dkg_type'])
            
            for (scheme, dkg_type), group in grouped:
                if self._skip_if_invalid(scheme, curve, dkg_type):
                    continue
                
                if 'keygen_ms' not in group.columns:
                    continue
                
                label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()})"
                color = self.SCHEME_COLORS.get(scheme, '#333333')
                
                # Different linestyles for DKG types
                linestyle = '-' if dkg_type == 'feldman_vss' else '--'
                
                group = group.sort_values('n')
                
                ax.plot(group['n'], group['keygen_ms'],
                       marker='o', linewidth=2.5, markersize=8,
                       label=label, color=color, linestyle=linestyle, alpha=0.8)
            
            ax.set_xlabel('Number of Participants (n)', fontsize=12, fontweight='bold')
            ax.set_title(curve, fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xticks(sorted(curve_df['n'].unique()))
        
        axes[0].set_ylabel('Key Generation Time (ms)', fontsize=14, fontweight='bold')
        fig.suptitle('DKG Key Generation Time by Curve and DKG Type\\n(Solid: Feldman VSS, Dashed: Pedersen DKG)',
                    fontsize=16, fontweight='bold', y=1.02)
        
        # Add legend
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.98),
                  ncol=4, fontsize=11)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
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
        GROUP B: KeyGen time vs loss_rate, split by (scheme + dkg_type).
        
        Pedersen has more rounds so degrades faster under packet loss.
        Only valid combinations per COMPATIBILITY.
        """
        if '_phase' not in df.columns:
            print("⚠ _phase column not available for DKG analysis")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Group by scheme and dkg_type (aggregate across curves)
        grouped = df_copy.groupby(['scheme', 'dkg_type', 'loss_rate'])
        
        # Aggregate keygen_ms by mean
        agg_df = grouped['keygen_ms'].mean().reset_index()
        
        schemes_dkg = set(zip(agg_df['scheme'], agg_df['dkg_type']))
        
        for scheme, dkg_type in schemes_dkg:
            subset = agg_df[(agg_df['scheme'] == scheme) & (agg_df['dkg_type'] == dkg_type)]
            
            # Check validity for any curve (we aggregate across curves)
            # Use first available curve for validation
            curves_in_subset = df_copy[(df_copy['scheme'] == scheme) & 
                                        (df_copy['dkg_type'] == dkg_type)]['curve'].unique()
            
            if len(curves_in_subset) == 0:
                continue
            
            # Check if at least one curve is valid
            is_valid = any(not self._skip_if_invalid(scheme, c, dkg_type) for c in curves_in_subset)
            if not is_valid:
                continue
            
            label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            linestyle = '-' if dkg_type == 'feldman_vss' else '--'
            
            subset = subset.sort_values('loss_rate')
            
            ax.plot(subset['loss_rate'] * 100, subset['keygen_ms'],
                   marker='o', linewidth=2.5, markersize=8,
                   label=label, color=color, linestyle=linestyle, alpha=0.8)
        
        ax.set_xlabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Key Generation Time (ms)', fontsize=14, fontweight='bold')
        ax.set_title('DKG Performance Under Network Stress\\n(Solid: Feldman VSS, Dashed: Pedersen DKG)',
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
        GROUP B: Network overhead during keygen vs n, split by (scheme + dkg_type).
        
        Shows O(n²) message complexity difference between Feldman and Pedersen.
        Only valid combinations per COMPATIBILITY.
        """
        if '_phase' not in df.columns:
            print("⚠ _phase column not available for DKG analysis")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        grouped = df_copy.groupby(['scheme', 'dkg_type', 'curve'])
        
        for (scheme, dkg_type, curve), group in grouped:
            if self._skip_if_invalid(scheme, curve, dkg_type):
                continue
            
            if 'network_overhead_ms' not in group.columns:
                continue
            
            label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()}, {curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            linestyle = '-' if dkg_type == 'feldman_vss' else '--'
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['network_overhead_ms'],
                   marker=marker, linewidth=2, markersize=8,
                   label=label, color=color, linestyle=linestyle, alpha=0.7)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Network Overhead During KeyGen (ms)', fontsize=14, fontweight='bold')
        ax.set_title('DKG Network Communication Overhead\\n(Solid: Feldman VSS, Dashed: Pedersen DKG)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=9, loc='upper left', framealpha=0.9, ncol=2)
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
        GROUP B: Pedersen overhead cost percentage.
        
        (pedersen_keygen_ms - feldman_keygen_ms) / feldman_keygen_ms * 100 vs n
        Per valid scheme+curve combination.
        
        This is the key number for the paper: how much extra does stronger
        Pedersen security cost in practice?
        """
        if '_phase' not in df.columns:
            print("⚠ _phase column not available for DKG analysis")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Separate Feldman and Pedersen data
        feldman_df = df_copy[df_copy['dkg_type'] == 'feldman_vss']
        pedersen_df = df_copy[df_copy['dkg_type'] == 'pedersen_dkg']
        
        # Get unique scheme+curve combinations that have both
        feldman_groups = set(feldman_df.groupby(['scheme', 'curve']).groups.keys())
        pedersen_groups = set(pedersen_df.groupby(['scheme', 'curve']).groups.keys())
        common_groups = feldman_groups & pedersen_groups
        
        if len(common_groups) == 0:
            print("⚠ No scheme+curve combinations with both Feldman and Pedersen data")
            return None
        
        for scheme, curve in common_groups:
            if self._skip_if_invalid(scheme, curve, 'pedersen_dkg'):
                continue
            
            feldman_subset = feldman_df[(feldman_df['scheme'] == scheme) & 
                                        (feldman_df['curve'] == curve)]
            pedersen_subset = pedersen_df[(pedersen_df['scheme'] == scheme) & 
                                          (pedersen_df['curve'] == curve)]
            
            # Aggregate by n
            feldman_avg = feldman_subset.groupby('n')['keygen_ms'].mean()
            pedersen_avg = pedersen_subset.groupby('n')['keygen_ms'].mean()
            
            # Find common n values
            common_n = set(feldman_avg.index) & set(pedersen_avg.index)
            
            if len(common_n) == 0:
                continue
            
            common_n = sorted(common_n)
            
            # Calculate overhead percentage
            overhead_pct = []
            for n_val in common_n:
                f_val = feldman_avg[n_val]
                p_val = pedersen_avg[n_val]
                if f_val > 0:
                    overhead_pct.append((p_val - f_val) / f_val * 100)
                else:
                    overhead_pct.append(0)
            
            label = f"{scheme.upper()} ({curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            
            ax.plot(common_n, overhead_pct,
                   marker='o', linewidth=2.5, markersize=10,
                   label=label, color=color, alpha=0.8)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Pedersen Overhead (%)', fontsize=14, fontweight='bold')
        ax.set_title('Security Premium: Pedersen DKG vs Feldman VSS\\n(Positive = Pedersen costs more)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
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
        GROUP B: KeyGen/Sign ratio vs n, split by dkg_type.
        
        Shows how many signatures needed before DKG cost amortizes.
        Whether choosing Pedersen over Feldman shifts the break-even point.
        Only valid scheme+curve combinations.
        """
        if '_phase' not in df.columns:
            print("⚠ _phase column not available for DKG analysis")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        df_copy = df.copy()
        df_copy['dkg_type'] = df_copy['_phase'].apply(self._get_dkg_type_from_phase)
        
        # Filter to rows with both keygen_ms and sign_ms
        df_copy = df_copy.dropna(subset=['keygen_ms', 'sign_ms'])
        
        # Calculate ratio
        df_copy['keygen_sign_ratio'] = df_copy['keygen_ms'] / df_copy['sign_ms']
        
        grouped = df_copy.groupby(['scheme', 'dkg_type', 'curve'])
        
        for (scheme, dkg_type, curve), group in grouped:
            if self._skip_if_invalid(scheme, curve, dkg_type):
                continue
            
            label = f"{scheme.upper()} ({dkg_type.replace('_', ' ').title()}, {curve})"
            color = self.SCHEME_COLORS.get(scheme, '#333333')
            linestyle = '-' if dkg_type == 'feldman_vss' else '--'
            marker = self.CURVE_MARKERS.get(curve, 'o')
            
            group = group.sort_values('n')
            
            ax.plot(group['n'], group['keygen_sign_ratio'],
                   marker=marker, linewidth=2, markersize=8,
                   label=label, color=color, linestyle=linestyle, alpha=0.7)
        
        ax.set_xlabel('Number of Participants (n)', fontsize=14, fontweight='bold')
        ax.set_ylabel('KeyGen/Sign Time Ratio', fontsize=14, fontweight='bold')
        ax.set_title('DKG Cost Amortization Analysis\\n(Ratio = how many signs to pay back DKG cost)',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(fontsize=9, loc='upper left', framealpha=0.9, ncol=2)
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
