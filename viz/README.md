# Threshold Benchmark Visualization Module

Comprehensive visualization system for threshold signature scheme benchmarks.

## Quick Start

```bash
# Run the full visualization pipeline
cd code4/threshold_bench
python -m viz -r benchmark_results -o output
```

## Features

### Data Loading (`data_loader.py`)
- Unified loading of all phase JSON files
- Automatic column standardization
- Derived metrics calculation (slowdown ratios, overhead percentages)
- Filtering utilities (by phase, scheme, loss rate)

### Scheme Comparison (`plot_schemes.py`)
- **Signing Latency vs Participants** - Scalability analysis
- **Verification Time Comparison** - Throughput potential
- **Key Generation Time** - DKG setup costs
- **Time Breakdown Charts** - Component analysis
- **Radar Charts** - Holistic comparison

### Network Resilience (`plot_network.py`)
- **Degradation Curves** - Performance vs packet loss
- **Overhead Heatmaps** - Scale × network quality interaction
- **Retry Distributions** - Protocol chattiness
- **CDF Plots** - Tail latency analysis

### Main Pipeline (`main.py`)
- One-command generation of all visualizations
- Markdown summary report with recommendations
- Organized output structure

## Usage Examples

### Python API

```python
from viz import VisualizationPipeline, load_benchmark_data

# Load data
df = load_benchmark_data("benchmark_results")

# Run full pipeline
pipeline = VisualizationPipeline(
    results_dir="benchmark_results",
    output_dir="output"
)
results = pipeline.run_full_pipeline()

print(f"Generated {len(results['plots'])} plots")
```

### Command Line

```bash
# Basic usage
python -m viz -r benchmark_results -o output

# Skip certain plot types
python -m viz --no-network-plots

# Custom directories
python -m viz -r /path/to/results -o /path/to/output
```

## Output Structure

```
output/
├── figures/
│   ├── signing_latency_20260423_120000.png
│   ├── signing_latency_20260423_120000.pdf
│   ├── verification_time_*.png
│   ├── keygen_time_*.png
│   ├── degradation_curve_*.png
│   ├── overhead_heatmap_*.png
│   └── ...
├── interactive/
│   └── (future: Plotly HTML files)
└── reports/
    └── benchmark_summary_20260423_120000.md
```

## Requirements

```
matplotlib >= 3.7.0
seaborn >= 0.12.0
pandas >= 2.0.0
numpy >= 1.24.0
scipy >= 1.10.0
```

## Installation

```bash
pip install matplotlib seaborn pandas numpy scipy
```

## Architecture

```
viz/
├── __init__.py          # Package exports
├── data_loader.py       # Data loading and preprocessing
├── plot_schemes.py      # Category 1: Scheme comparisons
├── plot_curves.py       # Category 2: Curve analysis (TODO)
├── plot_network.py      # Category 3: Network resilience
├── plot_dkg.py          # Category 4: DKG comparison (TODO)
├── plot_scale.py        # Category 5: Scale analysis (TODO)
├── dashboard.py         # Category 6: Interactive dashboards (TODO)
├── stats.py             # Category 7: Statistical analysis (TODO)
├── report_gen.py        # Report generation utilities (TODO)
└── main.py              # Main entry point
```

## Supported Benchmark Phases

The loader automatically detects and merges these phase files:
- `phase1_baseline_feldman_*.json` - Feldman DKG baseline
- `phase1_baseline_pedersen_*.json` - Pedersen DKG baseline
- `phase2_curves_schnorr_*.json` - Curve comparison (Schnorr)
- `phase2_curves_tbls_*.json` - Curve comparison (TBLS)
- `phase3_network_loss0_*.json` - 0% packet loss
- `phase3_network_loss5_*.json` - 0.5% packet loss
- `phase3_network_loss10_*.json` - 1% packet loss
- `phase3_network_loss20_*.json` - 2% packet loss
- `phase3_network_loss50_*.json` - 5% packet loss
- `phase4_dkg_analysis_feldman_*.json` - DKG scaling (Feldman)
- `phase4_dkg_analysis_pedersen_*.json` - DKG scaling (Pedersen)
- `phase5_stress_loss_*.json` - Stress test (loss)
- `phase5_stress_scale_*.json` - Stress test (scale)

## Data Schema

Expected JSON format:
```json
{
  "phase": "phase1_baseline_feldman",
  "timestamp": "2026-04-23T11:32:23",
  "results": [
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
}
```

## Contributing

To add new plot types:
1. Create a new module (e.g., `plot_curves.py`)
2. Implement a class with plotting methods
3. Add to `__init__.py` exports
4. Integrate into `main.py` pipeline

## License

MIT License
