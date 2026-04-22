# SRTS Enhanced - How to Run

Complete step-by-step guide from testing to visualization.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Step 1: Run Tests](#3-step-1-run-tests)
4. [Step 2: Run Benchmarks](#4-step-2-run-benchmarks)
5. [Step 3: Parse and Analyze Data](#5-step-3-parse-and-analyze-data)
6. [Step 4: Generate Visualizations](#6-step-4-generate-visualizations)
7. [Step 5: Interpret Results](#7-step-5-interpret-results)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

### System Requirements
- python3 3.8+
- pip (python3 package manager)
- matplotlib, numpy, pandas (for visualization)

### Installation

```bash
cd /workspace/srts_enhanced

# Install required dependencies
pip install cryptography coincurve>=18.0.0 matplotlib numpy pandas

# Verify installation
python3 -c "import srts_enhanced; print('Package loaded successfully')"
```

### Required Dependencies
- **cryptography**: High-level cryptographic operations
- **coincurve>=18.0.0**: Low-level curve operations (required for raw byte access)
- **matplotlib**: Plotting and visualization
- **numpy**: Numerical operations
- **pandas**: Data manipulation and CSV export

---

## 2. Project Structure

See the project tree in the first section of this document. Key directories:
- `tests/` - Unit and integration tests
- `benchmarks/` - Performance benchmarking suite
- `schemes/` - Signature implementations (MuSig2, FROST, TBLS)

---

## 3. Step 1: Run Tests

Before running benchmarks, verify that all cryptographic implementations are correct.

### 3.1 Run All Tests

```bash
cd /workspace/srts_enhanced

# Run comprehensive test suite
python3 -m pytest tests/test_all.py -v

# OR run directly
python3 tests/test_all.py
```

### 3.2 Run Specific Scheme Tests

```bash
# Test MuSig2 specifically
python3 tests/test_musig2.py

# Test all schemes via test_all.py
python3 tests/test_all.py
```

### Expected Output

Tests should verify:
- ✅ Key generation works correctly
- ✅ Signing produces valid signatures
- ✅ Verification accepts valid signatures
- ✅ Aggregation combines signatures correctly
- ✅ Threshold schemes require minimum participants

### If Tests Fail

1. Check that `coincurve>=18.0.0` is installed
2. Verify python3 version is 3.8+
3. Check error messages for missing dependencies

---

## 4. Step 2: Run Benchmarks

Once tests pass, run the comprehensive benchmark suite to collect performance data under stress.

### 4.1 Quick Start (Default Configuration)

```bash
cd /workspace/srts_enhanced/benchmarks

# Run full comprehensive benchmark with default settings
python3 comprehensive_benchmark.py
```

This will:
- Test all schemes (MuSig2, FROST, TBLS)
- Run across multiple packet loss rates (0%, 0.5%, 1%, 2%, 5%)
- Test various participant counts (n=5, 10, 15)
- Generate JSON and CSV output files
- Create a summary report

### 4.2 Custom Configuration

Edit `comprehensive_benchmark.py` or create a custom runner:

```python
# custom_benchmark.py
from comprehensive_benchmark import ComprehensiveBenchmark
from config import BenchmarkConfig

config = BenchmarkConfig(
    n_values=[5, 10],           # Number of participants
    t_values=[3, 6],            # Threshold values
    iterations_per_config=20,   # Iterations per configuration
    packet_loss_rates=[0.0, 0.01, 0.05],  # Loss rates to test
    network_modes=['perfect', 'lossy']
)

benchmark = ComprehensiveBenchmark(config)
benchmark.run_all_phases()
```

### 4.3 Run Specific Phases

The benchmark runs in phases:
- **Phase 1**: Single-signer baseline
- **Phase 2**: Multi-signer without network simulation
- **Phase 3**: Network stress testing (packet loss)
- **Phase 4**: Scalability analysis (varying n, t)
- **Phase 5**: Summary report generation

```bash
# Run only Phase 3 (stress testing)
python3 comprehensive_benchmark.py --phase 3

# Run Phases 1-3 only
python3 comprehensive_benchmark.py --phases 1-3
```

### 4.4 Output Files

After completion, you'll find:
- `benchmark_results_TIMESTAMP.json` - Detailed metrics
- `benchmark_results_TIMESTAMP.csv` - Flattened data for analysis
- `summary_report_TIMESTAMP.md` - Human-readable summary

### 4.5 Expected Runtime

- **Quick test** (n=5, 10 iterations): ~2-5 minutes
- **Full suite** (all configurations): ~15-30 minutes
- **Extended stress test** (high iterations): ~1 hour

---

## 5. Step 3: Parse and Analyze Data

### 5.1 Load JSON Results

```python
import json
import pandas as pd

# Load JSON results
with open('benchmark_results_20240101_120000.json', 'r') as f:
    results = json.load(f)

# Convert to DataFrame for analysis
df = pd.DataFrame(results)

# View available columns
print(df.columns.tolist())
```

### 5.2 Key Metrics to Analyze

#### Timing Metrics
- `total_time_ms`: Total time per iteration
- `avg_crypto_time_ms`: Pure cryptographic operation time
- `avg_network_overhead_ms`: Time spent on retries/delays

#### Stress Metrics
- `avg_retries_per_iter`: Average retry count per iteration
- `bandwidth_inflation_factor`: Message bloat due to retries
- `completion_rate`: Success rate within retry limits

#### Schema Fields
```json
{
  "scheme": "MUSIG2",
  "network_mode": "lossy",
  "packet_loss_rate": 0.01,
  "n": 10,
  "t": 6,
  "metrics": {
    "avg_total_time_ms": 150.5,
    "avg_crypto_time_ms": 40.2,
    "avg_network_overhead_ms": 110.3,
    "avg_retries_per_iter": 1.4,
    "bandwidth_inflation_factor": 1.4,
    "completion_rate": 0.98
  }
}
```

### 5.3 Example Analysis Queries

```python
import pandas as pd

df = pd.read_csv('benchmark_results_20240101_120000.csv')

# Compare schemes at 1% packet loss
loss_1pct = df[df['packet_loss_rate'] == 0.01]
scheme_comparison = loss_1pct.groupby('scheme')['metrics_avg_total_time_ms'].mean()
print(scheme_comparison)

# Find degradation from 0% to 5% loss
for scheme in df['scheme'].unique():
    scheme_data = df[df['scheme'] == scheme]
    baseline = scheme_data[scheme_data['packet_loss_rate'] == 0.0]['metrics_avg_total_time_ms'].mean()
    stressed = scheme_data[scheme_data['packet_loss_rate'] == 0.05]['metrics_avg_total_time_ms'].mean()
    degradation = ((stressed - baseline) / baseline) * 100
    print(f"{scheme}: {degradation:.1f}% slowdown at 5% packet loss")
```

---

## 6. Step 4: Generate Visualizations

### 6.1 Automatic Plot Generation

The plotting script automatically finds and processes result files:

```bash
cd /workspace/srts_enhanced/benchmarks

# Generate all plots from latest results
python3 plot_results.py

# Generate plots from specific file
python3 plot_results.py --input benchmark_results_20240101_120000.json

# Generate plots from CSV
python3 plot_results.py --input benchmark_results_20240101_120000.csv
```

### 6.2 Available Plot Types

#### A. Overhead Stack Bar Chart
Shows crypto time vs network overhead per scheme:
- **X-axis**: Schemes (MuSig2, FROST, TBLS)
- **Y-axis**: Total time (stacked)
- **Stack**: Crypto time (bottom) + Network overhead (top)
- **Insight**: Which schemes suffer most from network issues

#### B. Degradation Curve
Performance vs packet loss rate:
- **X-axis**: Packet loss rate (0%, 0.5%, 1%, 2%, 5%)
- **Y-axis**: Total time or throughput
- **Lines**: One per scheme
- **Insight**: Breaking point where schemes become unusable

#### C. Retry Distribution Box Plot
Retry variance per scheme:
- **X-axis**: Network mode
- **Y-axis**: Number of retries
- **Insight**: Communication choppiness variance

#### D. Completion Rate Heatmap
Success rates across conditions:
- **X-axis**: Packet loss rate
- **Y-axis**: Scheme
- **Color**: Completion rate percentage
- **Insight**: Reliability under stress

### 6.3 Generated Files

Plots are saved as:
- `scheme_comparison_OVERHEAD_STACK.png`
- `degradation_curves_LOSS_RATE.png`
- `retry_distribution_BOX.png`
- `completion_rate_HEATMAP.png`

### 6.4 Customize Plots

Edit `plot_results.py` to customize:
- Color schemes
- Figure sizes
- Metric selections
- Output formats

---

## 7. Step 5: Interpret Results

### 7.1 Reading the Summary Report

The generated `summary_report_TIMESTAMP.md` contains:

1. **Executive Summary**: High-level findings
2. **Stress Analysis**: Comparative performance under load
3. **Scheme Rankings**: Best/worst performers
4. **Recommendations**: Use-case-specific advice

### 7.2 Key Questions to Answer

#### Performance Under Stress
- Which scheme degrades least at 5% packet loss?
- What is the "breaking point" for each scheme?
- How much overhead do retries add?

#### Scalability
- How does performance change as n (participants) increases?
- Does threshold (t) affect performance significantly?
- Which scheme scales best?

#### Reliability
- Which scheme maintains highest completion rate?
- Are there schemes that timeout frequently?
- What's the bandwidth cost of resilience?

### 7.3 Example Conclusions

From the enhanced summary report, you might see:

```
UNDER 1% PACKET LOSS:
  ✅ MUSIG2 experienced 40% slowdown due to high round-trip sensitivity
  ✅ TBLS remained stable with only 10% overhead despite larger keys
  ⚠️ FROST showed moderate degradation (25% slowdown)

RECOMMENDATIONS:
  📱 Mobile networks (high loss): Prefer TBLS
  🏢 LAN environments (low loss): Prefer MUSIG2
  ⚖️ Balanced scenarios: Consider FROST
```

### 7.4 Actionable Insights

Use the data to decide:
- **Production deployment**: Choose scheme based on expected network conditions
- **Parameter tuning**: Optimize n and t for your use case
- **Infrastructure needs**: Plan for bandwidth overhead
- **Timeout configuration**: Set appropriate retry limits

---

## 8. Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'coincurve'`
**Solution**: 
```bash
pip install coincurve>=18.0.0
```

#### Issue: `AttributeError: 'Ed25519PublicKey' object has no attribute 'public_bytes_raw'`
**Solution**: Ensure `coincurve>=18.0.0` is installed and being used instead of standard cryptography library for raw operations.

#### Issue: Benchmark stops after few iterations
**Solution**: This was fixed in the enhanced version. If it persists, check that `simulator.py` returns status flags instead of raising exceptions.

#### Issue: No plots generated
**Solution**: 
1. Verify result files exist
2. Check that matplotlib is installed: `pip install matplotlib`
3. Ensure input file path is correct

#### Issue: CSV missing stress metrics columns
**Solution**: The enhanced `comprehensive_benchmark.py` flattens nested structures. Ensure you're using the updated version.

### Getting Help

1. Check `benchmarks/README.md` for detailed documentation
2. Review `COMPREHENSIVE_BENCHMARK_GUIDE.md` for methodology
3. Examine test files for usage examples
4. Check error logs in terminal output

---

## Quick Reference Commands

```bash
# 1. Install dependencies
pip install cryptography coincurve>=18.0.0 matplotlib numpy pandas

# 2. Run tests
python3 tests/test_all.py

# 3. Run benchmarks
cd benchmarks && python3 comprehensive_benchmark.py

# 4. Generate plots
python3 plot_results.py

# 5. Analyze specific metric
python3 -c "
import pandas as pd
df = pd.read_csv('benchmark_results_latest.csv')
print(df.groupby('scheme')['metrics_avg_total_time_ms'].mean())
"
```

---

## Next Steps

After completing this workflow:
1. **Compare results** across different network conditions
2. **Tune parameters** (n, t, retry limits) for your use case
3. **Document findings** for your team/stakeholders
4. **Integrate benchmarks** into CI/CD for regression testing
5. **Extend analysis** with custom metrics if needed

Happy benchmarking! 🚀
