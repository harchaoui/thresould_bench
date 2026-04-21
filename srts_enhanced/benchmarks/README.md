# SRTS Enhanced - Benchmark Suite

Comprehensive benchmarking framework for threshold signature schemes including SRTS, FROST, TBLS, and MuSig2.

## Features

- **Multi-Scheme Support**: Benchmark SRTS, FROST, TBLS, and MuSig2
- **Multi-Curve Support**: Test across secp256k1, BLS12-381, ristretto255
- **Scalability Testing**: Evaluate performance from n=3 to n=100+ participants
- **Network Simulation**: Simulate LAN, WAN, lossy, and mobile network conditions
- **Comprehensive Metrics**: Timing, memory, communication overhead, signature sizes
- **Multiple Output Formats**: JSON, CSV, Markdown tables, summary reports

## Quick Start

### Run Quick Benchmark
```bash
cd /workspace/thresould_bench
python -m srts_enhanced.benchmarks.benchmark_main --quick
```

### Run Full Benchmark Suite
```bash
python -m srts_enhanced.benchmarks.benchmark_main --all
```

## Usage Examples

### Test Specific Schemes
```bash
# Test only SRTS and FROST
python -m srts_enhanced.benchmarks.benchmark_main --schemes SRTS,FROST

# Test only MuSig2
python -m srts_enhanced.benchmarks.benchmark_main --schemes MUSIG2
```

### Test Specific Curves
```bash
# Test only secp256k1
python -m srts_enhanced.benchmarks.benchmark_main --curves secp256k1

# Test multiple curves
python -m srts_enhanced.benchmarks.benchmark_main --curves secp256k1,bls12-381
```

### Network Simulation
```bash
# Simulate LAN conditions (1ms latency)
python -m srts_enhanced.benchmarks.benchmark_main --network lan

# Simulate WAN conditions (50ms latency)
python -m srts_enhanced.benchmarks.benchmark_main --network wan

# Simulate lossy network (1% packet loss)
python -m srts_enhanced.benchmarks.benchmark_main --network lossy

# Simulate mobile network (100ms latency, jitter)
python -m srts_enhanced.benchmarks.benchmark_main --network mobile
```

### Scale Testing
```bash
# Test up to n=50 participants
python -m srts_enhanced.benchmarks.benchmark_main --max-n 50

# Test specific range
python -m srts_enhanced.benchmarks.benchmark_main --min-n 5 --max-n 20
```

### Custom Iterations
```bash
# Run 50 iterations per configuration for better statistics
python -m srts_enhanced.benchmarks.benchmark_main --iterations 50
```

## Command Line Options

```
usage: benchmark_main.py [-h] [--all | --quick] [--schemes SCHEMES]
                         [--curves CURVES] [--max-n MAX_N] [--min-n MIN_N]
                         [--iterations ITERATIONS]
                         [--network {none,lan,wan,lossy,mobile}]
                         [--output-dir OUTPUT_DIR] [--no-memory-profile]
                         [--verbose] [--quiet]

SRTS Enhanced Benchmark Suite

optional arguments:
  -h, --help            show this help message and exit
  --all                 Run full benchmark suite (comprehensive)
  --quick               Run quick benchmark (fewer iterations, smaller scale)
  --schemes SCHEMES     Comma-separated list of schemes to test
                        (SRTS,FROST,TBLS,MUSIG2)
  --curves CURVES       Comma-separated list of curves to test
                        (secp256k1,bls12-381,ristretto255)
  --max-n MAX_N         Maximum number of participants (default: 100)
  --min-n MIN_N         Minimum number of participants (default: 3)
  --iterations ITERATIONS
                        Number of iterations per configuration
  --network {none,lan,wan,lossy,mobile}
                        Network simulation mode (default: none)
  --output-dir OUTPUT_DIR
                        Output directory for results (default: benchmark_results)
  --no-memory-profile   Disable memory profiling
  --verbose             Enable verbose output (default: True)
  --quiet               Suppress output during benchmark
```

## Output Files

After running benchmarks, results are saved in the `benchmark_results/` directory:

### JSON Report (`benchmark_YYYYMMDD_HHMMSS.json`)
Complete raw data with all metrics, suitable for programmatic analysis.

### CSV Report (`benchmark_YYYYMMDD_HHMMSS.csv`)
Flattened data in spreadsheet format for Excel/Google Sheets analysis.

### Markdown Report (`benchmark_YYYYMMDD_HHMMSS.md`)
Formatted tables and charts for documentation and papers.

### Summary Report (`summary_YYYYMMDD_HHMMSS.txt`)
Concise text summary highlighting performance leaders and averages.

## Example Output

### Markdown Table
```markdown
## SRTS

| Curve      | n   | t   | KeyGen (ms) | Sign (ms) | Verify (ms) | Sig Size (bytes) |
|------------|-----|-----|-------------|-----------|-------------|------------------|
| secp256k1  | 3   | 2   | 12.45       | 8.32      | 2.15        | 64               |
| secp256k1  | 5   | 3   | 18.67       | 11.54     | 2.18        | 64               |
| secp256k1  | 10  | 6   | 35.21       | 19.87     | 2.21        | 64               |
```

### Summary
```
PERFORMANCE LEADERS:
----------------------------------------
Fastest KeyGen:  MUSIG2 (secp256k1, n=3)
                 8.45 ms

Fastest Sign:    SRTS (secp256k1, n=3)
                 5.32 ms

Fastest Verify:  SRTS (secp256k1)
                 1.89 ms

Smallest Sig:    SRTS (secp256k1)
                 64 bytes

AVERAGE PERFORMANCE BY SCHEME:
----------------------------------------
FROST     : KeyGen=  45.23ms, Sign=  22.45ms, Verify=  3.12ms
MUSIG2    : KeyGen=  18.67ms, Sign=  12.34ms, Verify=  2.45ms
SRTS      : KeyGen=  38.91ms, Sign=   8.76ms, Verify=  1.98ms
TBLS      : KeyGen=  125.43ms, Sign=  45.67ms, Verify=  8.34ms
```

## Architecture

```
srts_enhanced/benchmarks/
├── __init__.py           # Package exports
├── config.py             # Configuration classes and presets
├── metrics.py            # Metrics collection and statistics
├── simulator.py          # Network condition simulation
├── runner.py             # Main benchmark execution engine
├── reporter.py           # Report generation (JSON/CSV/MD)
└── benchmark_main.py     # CLI entry point
```

## Metrics Collected

### Timing Metrics
- **KeyGen**: Time to generate keys and run DKG
- **Presign**: Time to generate presignatures (SRTS/FROST)
- **Partial Sign**: Time for each participant to sign
- **Aggregate**: Time to combine partial signatures
- **Verify**: Time to verify final signature
- **Statistics**: Mean, median, std dev, min, max, P95, P99, ops/sec

### Memory Metrics
- Peak memory usage during key generation
- Peak memory usage during signing

### Communication Metrics
- Bytes sent per operation
- Bytes received per operation
- Total communication overhead

### Signature Metrics
- Final signature size in bytes
- Verification time

## Network Simulation Presets

| Mode    | Latency | Jitter | Packet Loss | Use Case           |
|---------|---------|--------|-------------|--------------------|
| none    | 0ms     | 0ms    | 0%          | Real hardware      |
| lan     | 1ms     | 0ms    | 0%          | Local network      |
| wan     | 50ms    | 5ms    | 0%          | Internet (cross-region) |
| lossy   | 10ms    | 0ms    | 1%          | Unreliable network |
| mobile  | 100ms   | 20ms   | 0.5%        | Cellular network   |

## Programmatic Usage

```python
from srts_enhanced.benchmarks import (
    BenchmarkRunner,
    BenchmarkConfig,
    SchemeType,
    CurveType,
    NetworkMode,
    BenchmarkReporter
)

# Create custom configuration
config = BenchmarkConfig(
    schemes=[SchemeType.SRTS, SchemeType.FROST],
    curves=[CurveType.SECP256K1],
    scale_params=[(3, 2), (5, 3), (10, 6)],
    iterations=20,
    network_mode=NetworkMode.LAN
)

# Run benchmarks
runner = BenchmarkRunner(config)
results = runner.run_all()

# Generate reports
reporter = BenchmarkReporter(results, output_dir="my_results")
reporter.generate_all()
```

## Performance Tips

1. **Use `--quick`** for initial testing and development
2. **Run `--all`** overnight for comprehensive results
3. **Increase `--iterations`** for more statistically significant results
4. **Use `--network wan`** to simulate real-world distributed signing
5. **Disable memory profiling** with `--no-memory-profile` for faster runs
6. **Focus on specific schemes** with `--schemes` to reduce runtime

## Requirements

- Python 3.8+
- pytest (for testing)
- fastecdsa
- py-ecc
- cryptography

## License

MIT License
