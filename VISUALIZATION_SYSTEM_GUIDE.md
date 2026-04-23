# 📊 Threshold Signature Benchmark Visualization System

## Overview

This visualization package provides comprehensive plotting tools to analyze threshold signature benchmark data across multiple dimensions:

- **Per Scheme**: SRTS, FROST, TBLS, MuSig2 comparison
- **Per Curve**: secp256k1, bls12-381, ristretto255 analysis
- **Per Setup Method**: Feldman vs Pedersen DKG comparison
- **Per Network Conditions**: 0%, 0.5%, 1%, 2%, 5% packet loss
- **Per Scale**: n=3 to n=100 participants
- **Per Phase**: All 6 benchmark phases integrated

## Directory Structure

```
/workspace/
├── viz/                          # Visualization package (READY TO USE)
│   ├── __init__.py
│   ├── data_loader.py            # Unified data loading from JSON files
│   ├── plot_schemes.py           # Category 1: Scheme comparison plots
│   ├── plot_network.py           # Category 3: Network resilience plots
│   ├── main.py                   # One-command pipeline orchestration
│   └── README.md                 # Package documentation
│
├── benchmark_results/            # YOUR DATA DIRECTORY (CREATE THIS)
│   ├── phase1_baseline_feldman_*.json
│   ├── phase1_baseline_pedersen_*.json
│   ├── phase2_curves_schnorr_*.json
│   ├── phase2_curves_tbls_*.json
│   ├── phase3_network_loss0_*.json
│   ├── phase3_network_loss5_*.json
│   ├── phase3_network_loss10_*.json
│   ├── phase3_network_loss20_*.json
│   ├── phase3_network_loss50_*.json
│   ├── phase4_dkg_analysis_feldman_*.json
│   ├── phase4_dkg_analysis_pedersen_*.json
│   ├── phase5_stress_loss_*.json
│   └── phase5_stress_scale_*.json
│
└── output/                       # GENERATED OUTPUT
    ├── figures/                  # PNG plots (300 DPI)
    │   ├── scheme_signing_latency_vs_n.png
    │   ├── scheme_verification_comparison.png
    │   ├── scheme_keygen_comparison.png
    │   ├── scheme_time_breakdown.png
    │   ├── network_degradation_curves.png
    │   ├── network_overhead_heatmap.png
    │   ├── network_retry_boxplot.png
    │   └── network_cdf_plot.png
    └── reports/
        └── benchmark_summary_YYYYMMDD_HHMMSS.md
```

## Quick Start

### Step 1: Prepare Your Data

Copy your JSON benchmark files into `/workspace/benchmark_results/`:

```bash
mkdir -p /workspace/benchmark_results
cp /path/to/your/phase*.json /workspace/benchmark_results/
```

**Required JSON Format:**

Each JSON file should contain a list of records with these fields:
```json
[
  {
    "scheme": "srts",
    "curve": "secp256k1",
    "n": 10,
    "t": 6,
    "loss_rate": 0.00,
    "keygen_ms": 6.41,
    "sign_ms": 7.55,
    "verify_ms": 2.13,
    "network_overhead_ms": 0.00
  }
]
```

### Step 2: Install Dependencies

```bash
cd /workspace
pip install seaborn matplotlib pandas numpy scipy
```

### Step 3: Run the Visualization Pipeline

**Option A: Command Line Interface**

```bash
cd /workspace
python -m viz.main -r benchmark_results -o output
```

**Option B: Python API**

```python
from viz import VisualizationPipeline

# Initialize pipeline
pipeline = VisualizationPipeline(
    results_dir="benchmark_results",
    output_dir="output"
)

# Run full pipeline
results = pipeline.run_full_pipeline()

print(f"Generated {len(results['plots'])} plots")
print(f"Generated {len(results['reports'])} reports")
```

**Command Line Options:**

```bash
# Full pipeline (default)
python -m viz.main -r benchmark_results -o output

# Skip scheme comparison plots
python -m viz.main -r benchmark_results -o output --no-scheme-plots

# Skip network resilience plots
python -m viz.main -r benchmark_results -o output --no-network-plots

# Skip summary report
python -m viz.main -r benchmark_results -o output --no-report

# Custom directories
python -m viz.main -r /path/to/results -o /path/to/output
```

## Generated Visualizations

### Category 1: Scheme Comparison (plot_schemes.py)

#### 1.1 Signing Latency vs Participants
- **File**: `scheme_signing_latency_vs_n.png`
- **Type**: Line chart with error bands
- **X-axis**: Number of participants (n)
- **Y-axis**: Signing time (ms)
- **Lines**: One per scheme (SRTS, FROST, TBLS, MuSig2)
- **Facets**: Separate curves (secp256k1, bls12-381)
- **Insight**: How signing scales with group size

#### 1.2 Verification Time Comparison
- **File**: `scheme_verification_comparison.png`
- **Type**: Grouped bar chart
- **X-axis**: Scheme
- **Y-axis**: Verification time (ms)
- **Groups**: Different participant counts
- **Insight**: Critical for high-throughput verification scenarios

#### 1.3 Key Generation Cost (DKG Overhead)
- **File**: `scheme_keygen_comparison.png`
- **Type**: Line chart
- **X-axis**: Number of participants (n)
- **Y-axis**: KeyGen time (ms)
- **Lines**: One per scheme
- **Note**: MuSig2 has no DKG (t=n always)
- **Insight**: One-time setup cost comparison

#### 1.4 Total Time Breakdown
- **File**: `scheme_time_breakdown.png`
- **Type**: Stacked bar chart
- **X-axis**: Scheme × participant count
- **Y-axis**: Total time (ms)
- **Stacks**: KeyGen, Sign, Verify components
- **Insight**: Where does the time go?

#### 1.5 Radar Chart (Holistic View)
- **File**: `scheme_radar_chart.png`
- **Type**: Radar/spider chart
- **Axes**: KeyGen, Sign, Verify, Network overhead, Scalability
- **One radar per scheme**
- **Insight**: Multi-dimensional comparison at a glance

### Category 3: Network Resilience (plot_network.py)

#### 3.1 Performance Degradation Curves
- **File**: `network_degradation_curves.png`
- **Type**: Line chart
- **X-axis**: Packet loss rate (%)
- **Y-axis**: Slowdown percentage (%)
- **Lines**: One per scheme
- **Baseline**: 0% loss performance
- **Insight**: Which schemes handle network instability best?

#### 3.2 Network Overhead Heatmap
- **File**: `network_overhead_heatmap.png`
- **Type**: Heatmap
- **X-axis**: Packet loss rate (%)
- **Y-axis**: Number of participants (n)
- **Color**: Network overhead (ms)
- **Facets**: One heatmap per scheme
- **Insight**: Scale × loss interaction effects

#### 3.3 Retry Distribution Box Plot
- **File**: `network_retry_boxplot.png`
- **Type**: Box plot
- **X-axis**: Scheme
- **Y-axis**: Estimated retries (derived from overhead)
- **Groups**: Different loss rates
- **Insight**: Protocol chattiness under stress

#### 3.4 Time-to-Completion CDF
- **File**: `network_cdf_plot.png`
- **Type**: Cumulative distribution function
- **X-axis**: Total time (ms)
- **Y-axis**: CDF (0 to 1)
- **Lines**: One per scheme at specific loss rate
- **Insight**: Tail latency and reliability guarantees

## Output Reports

### Summary Report (`output/reports/benchmark_summary_*.md`)

Auto-generated markdown report including:

1. **Overview Statistics**
   - Total configurations tested
   - Schemes, curves, participant range
   - Packet loss range

2. **Performance Summary Table**
   - Average KeyGen, Sign, Verify times per scheme

3. **Network Resilience Analysis**
   - Performance degradation under stress
   - Recommendations by scheme

4. **Use Case Recommendations**
   - ⚡ Lowest signing latency
   - ✅ Fastest verification
   - 🔑 Fastest key generation
   - 🛡️ Most network resilient

5. **Generated Visualizations List**
   - Description of each plot type

## Data Loader API

For custom analysis, use the data loader directly:

```python
from viz import BenchmarkDataLoader

loader = BenchmarkDataLoader("benchmark_results")

# Load all phases into unified DataFrame
df = loader.load_all_phases()

# Add derived metrics (slowdown %, total time, etc.)
df = loader.add_derived_metrics(df)

# Now df contains all benchmark data with columns:
# - scheme, curve, n, t, loss_rate
# - keygen_ms, sign_ms, verify_ms, network_overhead_ms
# - total_time_ms, slowdown_percentage, _phase
```

## Plot APIs

### Scheme Comparator

```python
from viz import SchemeComparator

comparator = SchemeComparator(output_dir="output/figures")

# Generate all scheme comparison plots
plots = comparator.generate_all_scheme_plots(df)

# Or generate individual plots
comparator.plot_signing_latency_vs_n(df)
comparator.plot_verification_comparison(df)
comparator.plot_keygen_comparison(df)
comparator.plot_time_breakdown(df)
comparator.plot_radar_chart(df)
```

### Network Analyzer

```python
from viz import NetworkAnalyzer

analyzer = NetworkAnalyzer(output_dir="output/figures")

# Generate all network resilience plots
plots = analyzer.generate_all_network_plots(df)

# Or generate individual plots
analyzer.plot_degradation_curves(df)
analyzer.plot_overhead_heatmap(df)
analyzer.plot_retry_boxplot(df)
analyzer.plot_cdf(df)
```

## Expected JSON File Patterns

The data loader looks for these file patterns:

| Pattern | Phase | Description |
|---------|-------|-------------|
| `phase1_baseline_feldman_*.json` | Phase 1 | Baseline with Feldman DKG |
| `phase1_baseline_pedersen_*.json` | Phase 1 | Baseline with Pedersen DKG |
| `phase2_curves_schnorr_*.json` | Phase 2 | Curve comparison (Schnorr schemes) |
| `phase2_curves_tbls_*.json` | Phase 2 | Curve comparison (TBLS only) |
| `phase3_network_loss0_*.json` | Phase 3 | Network test: 0% loss |
| `phase3_network_loss5_*.json` | Phase 3 | Network test: 0.5% loss |
| `phase3_network_loss10_*.json` | Phase 3 | Network test: 1% loss |
| `phase3_network_loss20_*.json` | Phase 3 | Network test: 2% loss |
| `phase3_network_loss50_*.json` | Phase 3 | Network test: 5% loss |
| `phase4_dkg_analysis_feldman_*.json` | Phase 4 | DKG analysis: Feldman |
| `phase4_dkg_analysis_pedersen_*.json` | Phase 4 | DKG analysis: Pedersen |
| `phase5_stress_loss_*.json` | Phase 5 | Stress test: varying loss |
| `phase5_stress_scale_*.json` | Phase 5 | Stress test: large scale (n=50,100) |

## Troubleshooting

### "No benchmark JSON files found"

**Solution**: Ensure your JSON files are in the correct directory and match the expected naming patterns.

```bash
# Check if files exist
ls -la benchmark_results/phase*.json

# Verify file naming matches patterns
# Example: phase1_baseline_feldman_20260423_113223.json
```

### "ModuleNotFoundError: No module named 'seaborn'"

**Solution**: Install required dependencies:

```bash
pip install seaborn matplotlib pandas numpy scipy
```

### "KeyError: 'slowdown_percentage'"

**Solution**: Make sure to call `add_derived_metrics()` after loading data:

```python
df = loader.load_all_phases()
df = loader.add_derived_metrics(df)  # This adds slowdown_percentage
```

## Extending the System

### Adding New Plot Categories

The system is designed for extension. To add Category 2 (Curve Analysis), Category 4 (DKG Comparison), etc.:

1. Create new file: `viz/plot_curves.py`
2. Implement plot class following existing pattern
3. Add to `__init__.py` exports
4. Integrate into `main.py` pipeline

### Adding Custom Metrics

Extend `BenchmarkDataLoader.add_derived_metrics()`:

```python
def add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Existing metrics
    df['total_time_ms'] = df['keygen_ms'] + df['sign_ms'] + df['verify_ms']
    
    # Add your custom metric
    df['efficiency_score'] = df['sign_ms'] / df['n']  # Example
    
    return df
```

## Next Steps

1. **Copy your JSON files** to `/workspace/benchmark_results/`
2. **Run the pipeline**: `python -m viz.main -r benchmark_results -o output`
3. **Review generated plots** in `output/figures/`
4. **Read summary report** in `output/reports/`
5. **Customize analysis** using the Python API for deeper insights

## Support

For issues or feature requests, refer to:
- `COMPREHENSIVE_VISUALIZATION_PLAN.md` - Full design document
- `viz/README.md` - Package-level documentation
- Source code comments in each module

---

*Generated by Threshold Bench Visualization Team*
