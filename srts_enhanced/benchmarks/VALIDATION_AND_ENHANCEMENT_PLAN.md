# Comprehensive Benchmark Validation & Enhancement Plan

## Overview
This document provides a complete validation checklist and enhancement roadmap for the SRTS Enhanced benchmark suite. It covers theoretical analysis, empirical measurements, and comparison against expected results.

---

## Phase 0: Theoretical Analysis ✅ COMPLETED

### Objectives
- Generate property comparison matrix for all schemes
- Calculate theoretical communication costs
- Compare DKG protocols (Pedersen vs Feldman)

### Validation Checklist

#### 1. Scheme Property Matrix
- [x] **Online Signing Rounds**: Verify counts match protocol specs
  - SRTS: 1 round ✓
  - FROST: 2 rounds ✓
  - MuSig2: 2 rounds ✓
  - TBLS: 1 round ✓

- [x] **Security Properties**:
  - Dealer-free DKG support
  - Adaptive corruption resistance
  - Nonce reuse safety

- [x] **Output Characteristics**:
  - Standard Schnorr signature format
  - Signature sizes (bytes)
  - Pairing requirements

**Action**: Run `python -m srts_enhanced.benchmarks.scheme_analysis` to regenerate matrix.

#### 2. Communication Cost Calculator
- [x] Verify formula correctness:
  ```
  DKG Round 1: n × (n × 32) bytes  [Broadcast commitments]
  DKG Round 2: n × ((n-1) × 96) bytes [P2P shares + proofs]
  Presign: n × (n × 64) bytes [Nonce commitments]
  Sign: n × (n × 36) bytes [Signature shares]
  ```

- [ ] **Validate against real measurements** (Phase 1-3 results)

**Expected Scaling**:
| n | Total Bytes (Theory) | Expected Overhead |
|---|---------------------|-------------------|
| 5 | ~15 KB | Minimal |
| 10 | ~22 KB | Low |
| 20 | ~85 KB | Moderate |
| 50 | ~500 KB | High |

---

## Phase 1: Baseline Performance & DKG Comparison

### Objectives
- Measure actual performance with no network simulation
- Compare Pedersen vs Feldman DKG overhead
- Establish baseline metrics for all schemes

### Test Configuration
```python
schemes = [SRTS, FROST, TBLS, MuSig2]
curves = [secp256k1, BLS12-381]
dkg_methods = [Pedersen, Feldman]
scales = [(3,2), (5,3), (10,6), (20,11)]
iterations = 20
```

### Validation Metrics

#### 1. DKG Comparison (Pedersen vs Feldman)
**Hypothesis**: Feldman is 1.3-1.5x faster due to simpler ZK proofs.

| Metric | Pedersen | Feldman | Expected Ratio |
|--------|----------|---------|----------------|
| KeyGen Time (n=10) | ~15ms | ~10ms | 1.5:1 |
| Communication Overhead | Higher | Lower | 1.3:1 |
| Security Level | Information-theoretic | Computational | - |

**Validation Steps**:
- [ ] Run Phase 1 benchmarks
- [ ] Extract `timing_keygen_mean_ms` for both DKG types
- [ ] Calculate ratio: `pedersen_time / feldman_time`
- [ ] Verify ratio is in range [1.2, 1.8]

#### 2. Scheme Performance Ranking
**Expected Order (Fastest to Slowest)**:
1. **MuSig2** (sign only): ~0.05ms (no presign phase in online)
2. **SRTS** (online): ~4-5ms (uses presignatures)
3. **FROST** (full): ~15-20ms (two-round protocol)
4. **TBLS**: ~40-50ms (pairing operations)

**Validation**:
- [ ] Verify MuSig2 has fastest online sign
- [ ] Verify SRTS outperforms FROST in online phase
- [ ] Confirm TBLS verification is fastest (<1ms for batch)

---

## Phase 2: Curve Comparison

### Objectives
Evaluate performance across different elliptic curves.

### Test Matrix
| Scheme | secp256k1 | ed25519 | ristretto255 | BLS12-381 |
|--------|-----------|---------|--------------|-----------|
| SRTS | ✓ | ✓ | ✓ | ✗ |
| FROST | ✓ | ✓ | ✓ | ✗ |
| MuSig2 | ✓ | ✓ | ✓ | ✗ |
| TBLS | ✗ | ✗ | ✗ | ✓ |

### Expected Results

**Relative Performance (secp256k1 = 1.0)**:
- **ed25519**: 0.85-0.90x (12-15% faster)
- **ristretto255**: 0.88-0.92x (similar to ed25519)
- **BLS12-381**: 2.0-3.0x slower (pairing cost)

**Validation**:
- [ ] Run Phase 2 benchmarks
- [ ] Normalize times to secp256k1 baseline
- [ ] Verify ed25519 shows ~12% improvement
- [ ] Document any anomalies

---

## Phase 3: Network Impact Analysis

### Objectives
Quantify effects of realistic network conditions on UAV swarms.

### Network Profiles

| Mode | Latency | Packet Loss | Use Case |
|------|---------|-------------|----------|
| LAN | 1ms | 0% | Same room |
| WAN | 50ms | 0% | Ground station |
| LOSSY | 50ms | 1% | Urban environment |
| MOBILE | 100ms | 3% | High mobility |
| SATELLITE | 500ms | 5% | Remote ops |

### Critical Metrics

#### 1. Protocol Resilience
**Hypothesis**: SRTS handles packet loss better than MuSig2.

| Scheme | LAN Time | LOSSY Time | Degradation |
|--------|----------|------------|-------------|
| SRTS | 4ms | ~5ms | +25% |
| FROST | 15ms | ~25ms | +66% |
| MuSig2 | 0.05ms | FAIL | N/A |

**Why**: 
- SRTS presignatures tolerate delays
- MuSig2 requires all participants in real-time
- FROST can handle some drops with reconstruction

**Validation**:
- [ ] Run Phase 3 with each network mode
- [ ] Measure failure rates (especially MuSig2)
- [ ] Plot latency degradation curves

#### 2. Communication Overhead vs Network
**Expected**: Total bytes scale as O(n²), but wall-clock time scales differently based on parallelism.

**Formula**:
```
Total Time = max(per_node_compute) + network_latency * num_rounds + retransmit_overhead
```

**Validation**:
- [ ] Compare theoretical bytes (Phase 0) vs measured
- [ ] Identify bottlenecks (send/recv vs compute)

---

## Phase 4: DKG Deep Dive

### Objectives
Analyze DKG performance at scale and under stress.

### Test Parameters
```python
scales = [(10,6), (20,11), (50,26)]
dkg_types = [Pedersen, Feldman]
network_modes = [NONE, WAN, LOSSY]
```

### Key Questions

1. **Scalability**: At what n does DKG become impractical?
   - Expected: n > 50 shows significant delays (>1s)

2. **DKG Choice**: When to use Pedersen vs Feldman?
   - **Pedersen**: Adversarial environments, high security
   - **Feldman**: Performance-critical, trusted participants

3. **Network Sensitivity**: Which DKG phase is most affected?
   - Expected: Round 2 (P2P shares) most sensitive to loss

**Validation**:
- [ ] Run Phase 4 benchmarks
- [ ] Plot KeyGen time vs n (log scale)
- [ ] Identify inflection points

---

## Phase 5: Stress Testing

### Objectives
Push schemes to limits and identify breaking points.

### Test Scenarios

#### 1. Large Scale (n=100)
**Expected**:
- SRTS: Still functional (~50-100ms online)
- FROST: Slow but works (~200-300ms)
- MuSig2: May timeout
- TBLS: Very slow verification

#### 2. Extreme Packet Loss (10%)
**Expected**:
- SRTS: Degrades gracefully
- FROST: High failure rate
- MuSig2: Complete failure

#### 3. Batch Operations (1000 signatures)
**Expected**:
- SRTS: Linear scaling with batching benefit
- TBLS: Best aggregation (constant size)

**Validation**:
- [ ] Run stress tests
- [ ] Record failure modes
- [ ] Document practical limits

---

## Enhancement Opportunities

### 1. Optimization Targets

#### A. Batch Verification
**Current**: Individual verification
**Proposed**: Batch verify for SRTS/FROST
**Expected Gain**: 3-5x faster for bulk ops

**Implementation**:
```python
def batch_verify(signatures, messages, pub_keys):
    # Aggregate pairing checks for TBLS
    # Multi-exponentiation for Schnorr
    pass
```

#### B. Parallel DKG Share Generation
**Current**: Sequential
**Proposed**: Thread pool for share creation
**Expected Gain**: 2-3x faster for large n

#### C. Compression for Communication
**Current**: Uncompressed points (32 bytes)
**Proposed**: Compressed representation
**Expected Gain**: 50% bandwidth reduction

### 2. New Features

#### A. MANET Mobility Model
Simulate UAV movement patterns:
- Random waypoint
- Group mobility
- Formation flying

**Impact**: Dynamic topology affects P2P phases

#### B. Energy Consumption Profiling
Measure CPU cycles and estimate battery drain:
```python
energy_mJ = (cpu_cycles * voltage^2 * capacitance) / frequency
```

#### C. Real Hardware Testing
Deploy on Raspberry Pi / Jetson Nano:
- Validate simulated latency
- Measure thermal throttling effects

---

## Execution Roadmap

### Session 1: Validation (Complete)
- [x] Phase 0: Theoretical analysis
- [ ] Phase 1: Baseline + DKG comparison
- [ ] Generate validation report

### Session 2: Network & Curves
- [ ] Phase 2: Curve comparison
- [ ] Phase 3: Network impact
- [ ] Create performance plots

### Session 3: Optimization
- [ ] Implement batch verification
- [ ] Add parallel DKG
- [ ] Re-benchmark optimized versions

### Session 4: Advanced Features
- [ ] MANET simulator
- [ ] Energy profiling
- [ ] Hardware deployment guide

---

## How to Use This Plan

### For Validation:
1. Run specific phase: `python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase N`
2. Check off completed items in checklist
3. Compare results against "Expected" values
4. Document deviations

### For Enhancement:
1. Select optimization from "Enhancement Opportunities"
2. Implement in separate branch
3. Run before/after benchmarks
4. Update performance tables

### For Reporting:
1. Generate CSV results from `benchmark_results/`
2. Use `plot_results.py` for visualizations
3. Compile markdown summary
4. Compare against theoretical predictions (Phase 0)

---

## Quick Reference Commands

```bash
# Run theoretical analysis (instant)
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 0

# Run baseline benchmarks (5-10 min)
python -m srts_enhanced.benchmarks.comprehensive_benchmark --phase 1

# Run all phases (30-60 min)
python -m srts_enhanced.benchmarks.comprehensive_benchmark

# Quick test mode (1-2 min)
python -m srts_enhanced.benchmarks.comprehensive_benchmark --quick

# Generate plots from existing results
python -m srts_enhanced.benchmarks.plot_results

# View scheme properties
python -c "from srts_enhanced.benchmarks.scheme_analysis import SchemePropertyAnalyzer; \
          a = SchemePropertyAnalyzer(); print(a.generate_property_matrix())"
```

---

## Success Criteria

✅ **Validation Complete** when:
- All 5 phases executed successfully
- Measured results within 20% of theoretical predictions
- DKG comparison shows expected 1.3-1.5x ratio
- Network degradation patterns documented

✅ **Enhancement Complete** when:
- Batch verification implemented and tested
- Performance improved by ≥30% for target operations
- Documentation updated with new metrics
- Code merged to main branch

---

**Next Step**: Execute Phase 1 benchmarks and compare DKG performance against theoretical predictions.
