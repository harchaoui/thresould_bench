# Comprehensive Benchmark Suite - User Guide

## Overview

The comprehensive benchmark suite provides a complete validation framework for threshold signature schemes in UAV swarm scenarios. It tests across 5 critical dimensions:

1. **Baseline Performance** - All schemes, varying scale, DKG comparison
2. **Curve Comparison** - ed25519, secp256k1, ristretto255, BLS12-381
3. **Network Impact** - LAN, WAN, lossy, mobile conditions
4. **DKG Deep Dive** - Pedersen vs Feldman protocols
5. **Stress Testing** - Large scale (n=100), extreme conditions

## Quick Start

### Run Quick Test (2 minutes)
```bash
python -m srts_enhanced.benchmarks.comprehensive_benchmark --quick
```

This runs a minimal test with:
- Schemes: SRTS, FROST
- Curve: secp256k1
- Scale: n=3,5
- Iterations: 5

### Run Full Suite (30-60 minutes)
```bash
python -m srts_enhanced.benchmarks.comprehensive_benchmark
```

### Run Specific Phase
```bash
# Phase 1: Baseline Performance
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 1

# Phase 2: Curve Comparison
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 2

# Phase 3: Network Impact
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 3

# Phase 4: DKG Analysis
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 4

# Phase 5: Stress Testing
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 5
```

### Custom Output Directory
```bash
python -m srts_enhanced.benchmarks.comprehensive_benchmark --output my_results/
```

## What Gets Measured

### Performance Metrics
- **KeyGen Time**: Total and per-party key generation
- **Presign Time**: Offline presignature generation (SRTS/FROST)
- **Partial Sign**: Individual signature computation
- **Aggregate**: Signature combination time
- **Verify**: Signature verification time
- **Total Online**: End-to-end signing latency

### Statistical Measures
- Mean, median, standard deviation
- P95, P99 percentiles
- Success rate under packet loss
- Memory usage peak

### Communication Metrics
- Messages sent per phase
- Bytes transmitted
- Round trips required
- Network overhead

## Output Files

Each benchmark run generates:

### CSV Files
`phaseX_YYYYMMDD_HHMMSS.csv` - Raw timing data with all metrics

Example columns:
```csv
phase,scheme,curve,n,t,timing_keygen_mean_ms,timing_sign_mean_ms,timing_verify_mean_ms,signature_avg_size_bytes
phase1_baseline,srts,secp256k1,10,6,15.3,4.2,8.5,96
```

### JSON Files
`phaseX_YYYYMMDD_HHMMSS.json` - Complete results with metadata

### Plots (PNG + PDF)
- `signing_latency_*.png/pdf` - Latency vs participants
- `verification_time_*.png/pdf` - Verify time comparison
- `signature_size_*.png/pdf` - Size bar chart
- `keygen_time_*.png/pdf` - KeyGen scaling

### Summary Reports
- `performance_summary_*.md` - Markdown tables
- `comprehensive_summary_*.md` - Phase-by-phase analysis

## Interpreting Results

### Expected Performance Patterns

#### SRTS (Single-Round Threshold Schnorr)
- **KeyGen**: O(n²) - scales quadratically
- **Online Sign**: O(1) - constant time (presign offloaded)
- **Verify**: O(n) - linear in participants
- **Best for**: Real-time control loops

Expected metrics (secp256k1, n=20):
- Online sign: 4-8ms
- Verify: 8-12ms
- Sig size: 96 bytes

#### FROST (Flexible Round-Optimized Schnorr)
- **KeyGen**: O(n²) - quadratic
- **Sign**: O(n) - linear (no presign optimization)
- **Verify**: O(n) - linear
- **Best for**: General purpose, small groups

Expected metrics (secp256k1, n=20):
- Sign: 60-100ms
- Verify: 10-15ms
- Sig size: 258 bytes

#### TBLS (Threshold BLS)
- **KeyGen**: O(n²) - quadratic
- **Sign**: O(n) - linear
- **Verify**: O(1) - constant (fastest!)
- **Best for**: Telemetry aggregation, batch verify

Expected metrics (BLS12-381, n=20):
- Sign: 40-60ms
- Verify: 0.8-1.5ms
- Sig size: 96 bytes (G1 only)

#### MuSig2 (Multi-Signature)
- **KeyGen**: O(n) - linear
- **Sign**: O(n) - linear
- **Verify**: O(1) - constant
- **Best for**: 2-of-2 consensus, small teams

Expected metrics (secp256k1, n=10):
- Sign: 5-15ms
- Verify: 8-12ms
- Sig size: 65 bytes

### DKG Comparison

#### Feldman DKG
- **Pros**: Faster (20-50%), simpler protocol
- **Cons**: Requires trusted setup assumptions
- **Use when**: Trusted environment, rapid deployment

#### Pedersen DKG
- **Pros**: Fully distributed, no trusted dealer
- **Cons**: Slower (ZK proofs), more rounds
- **Use when**: Untrusted environment, maximum security

Expected ratio: Pedersen takes ~1.5x longer than Feldman

### Network Impact

| Mode | Latency | Packet Loss | Overhead Added |
|------|---------|-------------|----------------|
| LAN | 1ms | 0% | +1-2ms |
| WAN | 50ms | 0% | +50ms per round |
| LOSSY | 10ms | 1% | +5-10% overhead |
| MOBILE | 100ms | 5% | +100ms + retries |

**Scheme resilience ranking:**
1. SRTS (single round, most tolerant)
2. TBLS (threshold aggregation)
3. FROST (multi-round, moderate)
4. MuSig2 (all-or-nothing, fragile)

## Validation Checklist

Before trusting benchmark results:

### Data Quality
- [ ] ≥20 iterations per configuration
- [ ] Standard deviation < 50% of mean
- [ ] No NaN or infinite values
- [ ] Timestamps sequential

### Correctness
- [ ] All signatures verify successfully
- [ ] TBLS verify < 2ms (pairing working)
- [ ] SRTS online < 10ms (presign optimized)
- [ ] Signature sizes match expected values

### Reproducibility
- [ ] Re-run produces similar results (±10%)
- [ ] Scheme rankings stable
- [ ] Scaling patterns consistent

## Troubleshooting

### Common Issues

#### "ImportError: attempted relative import"
**Fix:** Already fixed in runner.py - use absolute imports

#### "KeyError: -1" in TBLS
**Cause:** G2 serialization bug
**Fix:** Ensure py-ecc Fp2 coefficients handled correctly

#### "NotImplementedError" for ristretto255
**Cause:** Missing pynacl
**Fix:** `pip install pynacl`

#### High variance (>50% std dev)
**Cause:** System load, GC pauses
**Fix:** Increase iterations, isolate environment

#### Plot generation fails
**Cause:** Missing matplotlib
**Fix:** `pip install matplotlib numpy`

## Enhancement Opportunities

Based on benchmark findings, consider:

### If SRTS is too slow:
- Profile presignature generation
- Batch nonce generation
- Parallelize participant operations

### If FROST scaling is poor:
- Implement aggregation optimizations
- Cache repeated computations
- Consider hierarchical thresholds

### If network resilience is poor:
- Add retry logic with exponential backoff
- Implement timeout handling
- Consider erasure coding for partial sigs

### For specific use cases:

**Real-Time UAV Control:**
- Primary: SRTS + ed25519
- Avoid: FROST (too slow), TBLS (sign slow)

**Telemetry Aggregation:**
- Primary: TBLS + BLS12-381
- Leverage: Fast batch verification

**Intermittent Connectivity:**
- Primary: SRTS (single round)
- Avoid: MuSig2 (all-or-nothing)

## Next Steps After Benchmarking

1. **Review summary report**: `benchmark_results/comprehensive_summary_*.md`
2. **Analyze plots**: Open PNG files in viewer
3. **Compare to expectations**: Check against validation criteria
4. **Identify bottlenecks**: Look for O(n²) scaling issues
5. **Plan optimizations**: Focus on slowest phases
6. **Document findings**: Update BENCHMARK_PLAN.md with actual results

## Advanced Usage

### Custom Benchmark Configuration

Edit `srts_enhanced/benchmarks/comprehensive_benchmark.py`:

```python
config = BenchmarkConfig(
    schemes=[SchemeType.SRTS],  # Only SRTS
    curves=[CurveType.ED25519],  # Only ed25519
    dkg_methods=[DKGType.PEDERSEN],
    scale_params=[(10, 6), (20, 11), (50, 26)],
    network_mode=NetworkMode.WAN,
    iterations=50,  # Higher precision
    enable_memory_profiling=True
)
```

### Programmatic Access

```python
from srts_enhanced.benchmarks.comprehensive_benchmark import ComprehensiveBenchmark

benchmark = ComprehensiveBenchmark(output_dir="results/")
results = benchmark.run_phase_1_baseline()

# Analyze results
for r in results:
    print(f"{r['scheme']} n={r['n']}: {r['timing']['sign_mean_ms']:.2f}ms")
```

### Extending Benchmarks

Add new test scenarios by creating methods in `ComprehensiveBenchmark`:

```python
def run_phase_6_custom(self):
    config = BenchmarkConfig(
        schemes=[...],
        curves=[...],
        # custom params
    )
    return self._run_config(config, "phase6_custom")
```

## Support

For issues or questions:
1. Check VALIDATION_AND_ENHANCEMENT_PLAN.md
2. Review BENCHMARK_PLAN.md for methodology
3. Examine error logs in benchmark_results/
4. Run quick test to isolate issues

---

**Last Updated:** 2026-04-21
**Version:** 2.0
**Tested With:** Python 3.8+, fastecdsa, py-ecc, pynacl
