# Comprehensive Benchmark Visualization Plan

## Executive Summary

This document outlines a complete visualization strategy for threshold signature scheme benchmarking data. The goal is to provide **multi-dimensional analysis** across:
- **Schemes**: SRTS, FROST, TBLS, MuSig2
- **Curves**: secp256k1, bls12-381, ristretto255, ed25519
- **Setup Methods**: Feldman DKG, Pedersen DKG
- **Network Conditions**: 0%, 0.5%, 1%, 2%, 5% packet loss
- **Scale**: n=3 to n=100 participants
- **Phases**: Baseline, Curves, Network, DKG Analysis, Stress Tests

---

## Data Architecture

### Input Files Structure

```
benchmark_results/
├── phase1_baseline_feldman_*.json      # Feldman DKG baseline
├── phase1_baseline_pedersen_*.json     # Pedersen DKG baseline
├── phase2_curves_schnorr_*.json        # Curve comparison (Schnorr schemes)
├── phase2_curves_tbls_*.json           # Curve comparison (TBLS)
├── phase3_network_loss0_*.json         # 0% packet loss
├── phase3_network_loss5_*.json         # 0.5% packet loss
├── phase3_network_loss10_*.json        # 1% packet loss
├── phase3_network_loss20_*.json        # 2% packet loss
├── phase3_network_loss50_*.json        # 5% packet loss
├── phase4_dkg_analysis_feldman_*.json  # DKG scaling (Feldman)
├── phase4_dkg_analysis_pedersen_*.json # DKG scaling (Pedersen)
├── phase5_stress_loss_*.json           # Stress test (loss)
├── phase5_stress_scale_*.json          # Stress test (scale)
└── comprehensive_summary_*.md          # Aggregated summary
```

### Unified Data Schema

All JSON files follow this structure:
```json
{
  "phase": "phase1_baseline_feldman",
  "timestamp": "2026-04-23T11:32:23",
  "results": [
    {
      "scheme": "srts|frost|tbls|musig2",
      "curve": "secp256k1|bls12-381|ristretto255",
      "n": 10,
      "t": 6,
      "loss_rate": 0.00,
      "keygen_ms": 6.41,
      "sign_ms": 7.55,
      "verify_ms": 2.13,
      "network_overhead_ms": 0.00
    }
  ]
}
```

---

## Visualization Categories

### Category 1: Scheme Comparison (Primary Analysis)

#### Plot 1.1: Signing Latency vs Participants (All Schemes)
- **X-axis**: Number of participants (n)
- **Y-axis**: Signing time (ms)
- **Lines**: One per scheme-curve combination
- **Color**: By scheme
- **Marker**: By curve
- **Facets**: Separate plots for each DKG type (Feldman/Pedersen)
- **Insight**: Shows scalability and absolute performance

#### Plot 1.2: Verification Time Comparison
- **Type**: Line chart or bar chart
- **Focus**: TBLS batch verification advantage
- **Insight**: Critical for high-throughput scenarios

#### Plot 1.3: Key Generation Time (DKG Cost)
- **X-axis**: Number of participants (n)
- **Y-axis**: KeyGen time (ms)
- **Comparison**: Feldman vs Pedersen overhead
- **Insight**: One-time setup cost analysis

#### Plot 1.4: Total Operation Time Breakdown
- **Type**: Stacked area chart
- **Components**: KeyGen + Sign + Verify + Network Overhead
- **Insight**: Where does time go?

---

### Category 2: Curve Analysis

#### Plot 2.1: secp256k1 vs bls12-381 Performance
- **Side-by-side comparison** for same scheme
- **Metrics**: Sign, Verify, KeyGen
- **Normalization**: Show relative slowdown factor
- **Insight**: BLS pairing cost vs Schnorr efficiency

#### Plot 2.2: Signature Size by Curve
- **Type**: Bar chart
- **Y-axis**: Bytes
- **Include**: secp256k1 (64B), ed25519 (64B), BLS (48B constant)
- **Insight**: Bandwidth implications for UAV swarms

#### Plot 2.3: Security Level vs Performance Trade-off
- **X-axis**: Security bits (128, 192, 256)
- **Y-axis**: Operations/sec
- **Bubble size**: Signature size
- **Insight**: Optimal choice for security requirements

---

### Category 3: Network Resilience Analysis

#### Plot 3.1: Performance Degradation Curve
- **X-axis**: Packet loss rate (%)
- **Y-axis**: Slowdown factor (normalized to 0% loss)
- **Lines**: Per scheme
- **Critical points**: Mark 10%, 50%, 100% degradation thresholds
- **Insight**: Which schemes break first?

#### Plot 3.2: Network Overhead Heatmap
- **X-axis**: Packet loss rate
- **Y-axis**: Number of participants
- **Color**: Network overhead (ms)
- **Facets**: By scheme
- **Insight**: Interaction between scale and network quality

#### Plot 3.3: Retry Distribution Box Plot
- **X-axis**: Scheme
- **Y-axis**: Retries per signing round
- **Grouping**: By packet loss rate
- **Insight**: Protocol chattiness under stress

#### Plot 3.4: Time-to-Completion CDF
- **Type**: Cumulative distribution function
- **X-axis**: Total time (ms)
- **Y-axis**: P(success)
- **Lines**: Per scheme at fixed loss rate
- **Insight**: Tail latency and reliability

---

### Category 4: DKG Setup Method Comparison

#### Plot 4.1: Feldman vs Pedersen Overhead
- **Type**: Grouped bar chart
- **X-axis**: Scheme
- **Y-axis**: KeyGen time ratio (Pedersen/Feldman)
- **Grouping**: By participant count
- **Insight**: Security vs performance trade-off

#### Plot 4.2: DKG Message Complexity
- **X-axis**: Number of participants
- **Y-axis**: Network messages exchanged
- **Lines**: Feldman vs Pedersen
- **Theoretical overlay**: O(n²) reference line
- **Insight**: Scaling behavior validation

---

### Category 5: Scale Analysis (Stress Testing)

#### Plot 5.1: Large-Scale Performance (n=50, 100)
- **Focus**: Extrapolation accuracy
- **Compare**: Measured vs predicted (from n=3,5,10,20 trend)
- **Insight**: Does linear scaling hold?

#### Plot 5.2: Throughput vs Latency Trade-off
- **X-axis**: Concurrent operations/sec
- **Y-axis**: P99 latency (ms)
- **Points**: Different batch sizes
- **Insight**: Optimal operating point

#### Plot 5.3: Resource Utilization
- **Metrics**: CPU, Memory, Network bandwidth
- **Correlation**: With participant count
- **Insight**: Bottleneck identification

---

### Category 6: Multi-Dimensional Dashboards

#### Dashboard 6.1: Scheme Selector Matrix
```
┌─────────────┬──────────────┬─────────────┬──────────────┐
│ Use Case    │ Best Scheme  │ Reason      │ Runner-up    │
├─────────────┼──────────────┼─────────────┼──────────────┤
│ Low latency │ MuSig2       │ 0.01ms sign │ SRTS         │
│ Mobile net  │ TBLS         │ 4% slowdown │ SRTS         │
│ Large group │ SRTS         │ Linear scale│ FROST        │
│ Small sig   │ TBLS         │ 48B const   │ MuSig2       │
│ Batch verify│ TBLS         │ Aggregation │ -            │
└─────────────┴──────────────┴─────────────┴──────────────┘
```

#### Dashboard 6.2: Radar Chart (Spider Plot)
- **Axes**: 
  - Signing Speed
  - Verification Speed
  - KeyGen Speed
  - Signature Size
  - Network Resilience
  - Implementation Complexity
- **One polygon per scheme**
- **Insight**: Holistic comparison at a glance

#### Dashboard 6.3: Decision Tree Visualization
- **Root**: Network stability?
- **Branches**: Group size, Security level, Signature size req
- **Leaves**: Recommended scheme
- **Insight**: Actionable guidance

---

### Category 7: Statistical Analysis

#### Plot 7.1: Correlation Matrix Heatmap
- **Variables**: n, t, loss_rate, keygen, sign, verify, overhead
- **Color**: Pearson correlation coefficient
- **Insight**: Hidden relationships

#### Plot 7.2: ANOVA Analysis
- **Factor**: Scheme type
- **Response**: Signing time
- **Output**: F-statistic, p-value
- **Insight**: Are differences statistically significant?

#### Plot 7.3: Regression Fit Quality
- **Model**: Time = α·n + β·loss + γ·(n×loss)
- **Plot**: Residuals vs fitted
- **R² value**: Displayed on plot
- **Insight**: Model validity

---

## Output Formats

### Static Images
- **PNG**: 300 DPI for presentations
- **PDF**: Vector format for publications
- **SVG**: Web-ready, editable

### Interactive Visualizations
- **HTML**: Plotly-based interactive charts
- **Dashboard**: Streamlit/Plotly Dash app
- **Jupyter Notebook**: Exploratory analysis

### Reports
- **Markdown**: Auto-generated summary with embedded plots
- **LaTeX**: Academic paper ready
- **PowerPoint**: Executive briefing deck

---

## Implementation Priority

### Phase 1: Core Plots (Week 1)
1. Signing latency comparison (all schemes)
2. Verification time comparison
3. Network degradation curves
4. Summary tables

### Phase 2: Advanced Analysis (Week 2)
1. DKG method comparison
2. Curve analysis
3. Statistical significance tests
4. Heatmaps

### Phase 3: Interactive Dashboard (Week 3)
1. Filterable web dashboard
2. Export functionality
3. Custom scenario builder

### Phase 4: Automation & CI (Week 4)
1. Auto-run on new data
2. Regression detection
3. Trend analysis over time

---

## Technical Stack

### Python Libraries
```python
# Core visualization
matplotlib >= 3.7.0
seaborn >= 0.12.0
plotly >= 5.14.0

# Data processing
pandas >= 2.0.0
numpy >= 1.24.0
scipy >= 1.10.0  # Statistics

# Dashboard
streamlit >= 1.22.0
dash >= 2.9.0

# Report generation
jinja2 >= 3.1.0
nbconvert >= 7.0.0
```

### File Organization
```
code4/threshold_bench/
├── viz/
│   ├── __init__.py
│   ├── data_loader.py      # Unified JSON/CSV loading
│   ├── plot_schemes.py     # Category 1
│   ├── plot_curves.py      # Category 2
│   ├── plot_network.py     # Category 3
│   ├── plot_dkg.py         # Category 4
│   ├── plot_scale.py       # Category 5
│   ├── dashboard.py        # Category 6
│   ├── stats.py            # Category 7
│   └── report_gen.py       # Markdown/LaTeX export
├── benchmark_results/      # Input data
└── output/
    ├── figures/           # PNG/PDF/SVG
    ├── interactive/       # HTML
    └── reports/           # MD/LaTeX
```

---

## Sample Code Structure

```python
# viz/data_loader.py
class BenchmarkDataLoader:
    def load_all_phases(self, results_dir: str) -> pd.DataFrame:
        """Load and merge all phase JSON files into unified DataFrame."""
        
    def add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate slowdown ratios, overhead percentages, etc."""
        
    def filter_by_phase(self, df: pd.DataFrame, phases: list) -> pd.DataFrame:
        """Subset data for specific analysis."""

# viz/plot_schemes.py
class SchemeComparator:
    def plot_signing_latency(self, df: pd.DataFrame, **kwargs):
        """Generate multi-scheme signing latency plot."""
        
    def plot_radar_chart(self, df: pd.DataFrame, normalize: bool = True):
        """Generate radar chart for holistic comparison."""

# Main entry point
def generate_all_visualizations(results_dir: str, output_dir: str):
    loader = BenchmarkDataLoader()
    df = loader.load_all_phases(results_dir)
    
    comparator = SchemeComparator()
    comparator.plot_signing_latency(df, output_dir=output_dir)
    # ... etc
```

---

## Success Metrics

1. **Completeness**: All 7 categories covered with ≥3 plots each
2. **Clarity**: Non-expert can identify best scheme in <30 seconds
3. **Actionability**: Clear recommendations for each use case
4. **Reproducibility**: Same input → same output (seeded random)
5. **Performance**: Generate all plots in <60 seconds
6. **Maintainability**: New plot types added in <1 hour

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize plots** based on immediate needs
3. **Implement Phase 1** core visualizations
4. **Validate** against existing benchmark data
5. **Iterate** based on feedback

---

*Generated by: Engineering Team*
*Date: 2026-04-23*
*Version: 1.0*
