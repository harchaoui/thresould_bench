# SRTS Enhanced - Project Tree

```
srts_enhanced/
│
├── README.md                              # Main project documentation
├── HOWTO.md                               # Step-by-step guide (tests → benchmarks → visualization)
├── PROJECT_TREE.md                        # This file - detailed project structure
├── __init__.py                            # Package initialization
│
├── curves/                                # Cryptographic curve implementations
│   ├── __init__.py                        # Ed25519, ristretto255 curve operations
│   │                                      # - Key generation
│   │                                      # - Serialization (raw bytes, DER)
│   │                                      # - Curve-specific operations
│   └── __pycache__/                       # Python bytecode cache
│
├── dkg/                                   # Distributed Key Generation protocols
│   ├── __init__.py                        # DKG protocol implementations
│   │                                      # - Secret sharing
│   │                                      # - Share distribution
│   │                                      # - Key reconstruction
│   └── __pycache__/
│
├── schemes/                               # Signature scheme implementations
│   ├── __init__.py                        # Scheme registry and factory
│   │                                      # - Registers MUSIG2, FROST, TBLS
│   │                                      # - Factory pattern for scheme creation
│   ├── musig2_scheme.py                   # MuSig2 multi-signature scheme
│   │                                      # - Key aggregation
│   │                                      # - Nonce generation
│   │                                      # - Partial signatures
│   │                                      # - Signature aggregation
│   ├── frost_scheme.py                    # FROST threshold signature scheme
│   │                                      # - Threshold key generation
│   │                                      # - Signing shares
│   │                                      # - Lagrange interpolation
│   └── tbls_scheme.py                     # TBLS threshold BLS scheme
│   │                                      # - BLS signature operations
│   │                                      # - Threshold reconstruction
│   │                                      # - Pairing-based verification
│   └── __pycache__/
│
├── utils/                                 # Utility functions
│   ├── polynomial.py                      # Polynomial operations for secret sharing
│   │                                      # - Polynomial evaluation
│   │                                      # - Lagrange basis polynomials
│   │                                      # - Interpolation
│   └── __pycache__/
│
├── tests/                                 # Unit and integration tests
│   ├── __init__.py
│   ├── test_all.py                        # Comprehensive test suite for all schemes
│   │                                      # - Tests key generation
│   │                                      # - Tests signing/verification
│   │                                      # - Tests aggregation
│   │                                      # - Tests threshold operations
│   ├── test_musig2.py                     # MuSig2-specific tests
│   │                                      # - Multi-party signing
│   │                                      # - Aggregation correctness
│   └── __pycache__/
│
└── benchmarks/                            # Performance benchmarking suite
    ├── README.md                          # Benchmark-specific documentation
    ├── COMPREHENSIVE_BENCHMARK_GUIDE.md   # Detailed benchmark methodology
    ├── VALIDATION_AND_ENHANCEMENT_PLAN.md # Implementation plan and retrospective
    ├── __init__.py
    │
    ├── config.py                          # Benchmark configuration classes
    │                                      # - BenchmarkConfig dataclass
    │                                      # - Network mode settings
    │                                      # - Packet loss rate configuration
    │                                      # - Participant count (n, t) settings
    │
    ├── simulator.py                       # Network simulation (packet loss, latency)
    │                                      # - NetworkSimulator class
    │                                      # - Packet loss simulation
    │                                      # - Latency injection
    │                                      # - Status flags (success, delay)
    │                                      # - Retry counters
    │
    ├── metrics.py                         # Performance metrics collection
    │                                      # - Timing metrics
    │                                      # - Memory tracking
    │                                      # - Signature size measurement
    │                                      # - Stress metrics (retries, overhead)
    │
    ├── runner.py                          # Benchmark execution engine
    │                                      # - BenchmarkRunner class
    │                                      # - Retry logic with exponential backoff
    │                                      # - Soft failure handling
    │                                      # - Result aggregation
    │                                      # - Schema management (JSON/CSV)
    │
    ├── benchmark.py                       # Legacy benchmark implementation
    │                                      # - Basic benchmarking (deprecated)
    │
    ├── benchmark_main.py                  # Simple benchmark entry point
    │                                      # - Quick benchmark runner
    │
    ├── comprehensive_benchmark.py         # Full stress-testing benchmark suite ⭐
    │                                      # - Multi-phase execution
    │                                      # - Phase 1: Single-signer baseline
    │                                      # - Phase 2: Multi-signer (no network sim)
    │                                      # - Phase 3: Network stress testing
    │                                      # - Phase 4: Scalability analysis
    │                                      # - Phase 5: Summary report generation
    │                                      # - Multiple packet loss rates (0-5%)
    │                                      # - CSV/JSON export
    │                                      # - Intelligent stress analysis
    │
    ├── scheme_analysis.py                 # Per-scheme performance analysis
    │                                      # - Statistical analysis
    │                                      # - Comparative metrics
    │
    ├── reporter.py                        # Report generation utilities
    │                                      # - Markdown report generation
    │                                      # - Summary statistics
    │
    └── plot_results.py                    # Data visualization and plotting ⭐
                                       # - Overhead Stack Bar Chart
                                       # - Degradation Curves
                                       # - Retry Distribution Box Plot
                                       # - Completion Rate Heatmap
                                       # - Automatic file discovery
                                       # - Customizable styling
    └── __pycache__/
```

## File Responsibilities by Category

### Core Cryptography (Production Code)
| File | Purpose | Key Functions |
|------|---------|---------------|
| `curves/__init__.py` | Elliptic curve operations | Key gen, serialization, raw byte access |
| `dkg/__init__.py` | Distributed key generation | Secret sharing, share distribution |
| `schemes/musig2_scheme.py` | MuSig2 implementation | Multi-sig aggregation |
| `schemes/frost_scheme.py` | FROST implementation | Threshold signatures |
| `schemes/tbls_scheme.py` | TBLS implementation | BLS threshold signatures |
| `utils/polynomial.py` | Mathematical utilities | Polynomial interpolation |

### Testing (Quality Assurance)
| File | Purpose | Coverage |
|------|---------|----------|
| `tests/test_all.py` | Comprehensive tests | All schemes, all operations |
| `tests/test_musig2.py` | MuSig2-specific tests | Multi-party workflows |

### Benchmarking (Performance Analysis)
| File | Purpose | Key Features |
|------|---------|--------------|
| `benchmarks/config.py` | Configuration | Network modes, loss rates, participant counts |
| `benchmarks/simulator.py` | Network simulation | Packet loss, latency, retry counting |
| `benchmarks/metrics.py` | Metrics collection | Timing, memory, bandwidth, stress metrics |
| `benchmarks/runner.py` | Execution engine | Retry logic, soft failures, result aggregation |
| `benchmarks/comprehensive_benchmark.py` | Full benchmark suite | Multi-phase, multi-loss-rate, reporting |
| `benchmarks/plot_results.py` | Visualization | 4 plot types, automatic generation |
| `benchmarks/reporter.py` | Report generation | Markdown summaries, stress analysis |

## Data Flow Architecture

```
┌─────────────┐
│   Tests     │ → Verify cryptographic correctness
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Config     │ → Set network conditions (loss rate, n, t)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Simulator  │ → Inject packet loss & latency
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Runner    │ → Execute benchmarks with retry logic
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Metrics    │ → Collect timing, retries, overhead
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Results   │ → JSON + CSV output
└──────┬──────┘
       │
       ├──────────→┌─────────────┐
       │           │   Plots     │ → PNG visualizations
       │           └─────────────┘
       │
       └──────────→┌─────────────┐
                   │   Report    │ → Markdown summary
                   └─────────────┘
```

## Output Files Generated

### During Testing
- Console output with pass/fail status
- No persistent files (unless pytest configured)

### During Benchmarking
- `benchmark_results_TIMESTAMP.json` - Complete metrics in JSON format
- `benchmark_results_TIMESTAMP.csv` - Flattened metrics for spreadsheet analysis
- `summary_report_TIMESTAMP.md` - Human-readable analysis and recommendations

### During Visualization
- `scheme_comparison_OVERHEAD_STACK.png` - Crypto time vs network overhead
- `degradation_curves_LOSS_RATE.png` - Performance vs packet loss
- `retry_distribution_BOX.png` - Retry variance analysis
- `completion_rate_HEATMAP.png` - Reliability heatmap

## Key Classes and Functions

### Configuration (`config.py`)
```python
@dataclass
class BenchmarkConfig:
    n_values: List[int]              # Participant counts
    t_values: List[int]              # Threshold values
    iterations_per_config: int       # Iterations per test
    packet_loss_rates: List[float]   # Loss rates to test [0.0, 0.005, 0.01, 0.02, 0.05]
    network_modes: List[str]         # ['perfect', 'lossy']
```

### Simulation (`simulator.py`)
```python
class NetworkSimulator:
    def send_message(...) -> Tuple[bool, float]  # (success, delay)
    def get_stats() -> Dict                      # packets_lost, packets_retried
```

### Execution (`runner.py`)
```python
class BenchmarkRunner:
    def run_iteration(...) -> Dict               # Single benchmark iteration
    def run_configuration(...) -> List[Dict]     # Full configuration test
```

### Comprehensive Benchmark (`comprehensive_benchmark.py`)
```python
class ComprehensiveBenchmark:
    def run_phase_1()  # Baseline
    def run_phase_2()  # Multi-signer
    def run_phase_3()  # Stress testing
    def run_phase_4()  # Scalability
    def run_phase_5()  # Reporting
    def run_all_phases()
```

### Visualization (`plot_results.py`)
```python
def plot_overhead_stack(data)           # Stacked bar chart
def plot_degradation_curves(data)       # Line plot
def plot_retry_distribution(data)       # Box plot
def plot_completion_rate(data)          # Heatmap
def generate_all_plots(input_file)      # Master function
```

## Dependencies

### Required
- `cryptography` - High-level crypto operations
- `coincurve>=18.0.0` - Low-level curve operations (critical for raw byte access)
- `matplotlib` - Plotting and visualization
- `numpy` - Numerical operations
- `pandas` - Data manipulation and CSV export

### Optional
- `pytest` - Test runner (for running tests with verbose output)

## Version Information

- **Python**: 3.8+
- **coincurve**: >=18.0.0 (required for public_bytes_raw functionality)
- **cryptography**: Latest stable version

## Quick Start Commands

```bash
# 1. Run tests
python tests/test_all.py

# 2. Run full benchmark suite
cd benchmarks && python comprehensive_benchmark.py

# 3. Generate visualizations
python plot_results.py

# 4. View results
ls -lh benchmark_results_*
```

For detailed usage instructions, see [HOWTO.md](HOWTO.md).
