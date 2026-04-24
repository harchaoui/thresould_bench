# Comprehensive Benchmark Summary - Performance Under Stress

**Generated:** 2026-04-23T16:18:02.873875

**Phases Completed:** phase0_theoretical, phase1_baseline, phase2_curves, phase3_network, phase4_dkg, phase5_stress

## Overall Statistics

- Total configurations tested: 103
- Start time: 2026-04-23T15:32:43.591000

## Stress Analysis Report

### Performance Degradation Analysis

**Under varying packet loss conditions** (comparing identical n/t configurations):

- **FROST**: Experienced 161.3% slowdown at 5.0% packet loss. Network overhead: 50.0ms.
- **SRTS**: Experienced 133.5% slowdown at 5.0% packet loss. Network overhead: 41.7ms.
- **TBLS**: Experienced 3.2% slowdown at 5.0% packet loss. Network overhead: 56.7ms.

### Recommendations

- **Most resilient to packet loss**: TBLS (3.2% slowdown)
- **Most sensitive to packet loss**: FROST (161.3% slowdown)

**Use Case Recommendations**:

- **For mobile/unstable networks**: Prefer schemes with lower slowdown percentages.
- **For LAN/datacenter environments**: All schemes perform well; choose based on baseline latency.
- **For high-throughput applications**: SRTS/FROST offer best balance of speed and resilience.
- **For signature size efficiency**: TBLS provides constant-size signatures regardless of n.
- **For low-latency requirements**: MuSig2 shows best baseline performance in ideal conditions.

## Phase Results

### phase1_baseline_feldman

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 2.77 | 2.47 | 2.14 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 3.73 | 3.85 | 2.15 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 6.61 | 7.71 | 2.22 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 11.11 | 14.03 | 2.14 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 2.87 | 2.90 | 2.23 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 3.68 | 4.19 | 2.14 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.42 | 8.41 | 2.13 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 11.03 | 15.72 | 2.14 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 22.01 | 223.76 | 975.16 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 28.92 | 332.33 | 967.45 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 50.62 | 660.01 | 962.29 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 87.90 | 1226.77 | 974.84 | 0.00 |
| musig2 | secp256k1 | 3 | 3 | 0.00% | 5.77 | 0.02 | 2.03 | 0.00 |
| musig2 | secp256k1 | 5 | 5 | 0.00% | 9.21 | 0.02 | 1.99 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 19.13 | 0.05 | 2.05 | 0.00 |

### phase1_baseline_pedersen

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 2.77 | 2.44 | 2.10 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 3.58 | 3.63 | 2.08 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 6.46 | 7.37 | 2.09 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 10.77 | 13.49 | 2.08 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 2.70 | 2.72 | 2.08 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 3.58 | 4.10 | 2.08 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.29 | 8.26 | 2.10 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 10.84 | 15.10 | 2.10 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 21.69 | 219.59 | 956.13 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 28.99 | 333.93 | 974.08 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 51.27 | 666.88 | 967.51 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 86.56 | 1221.13 | 969.85 | 0.00 |
| musig2 | secp256k1 | 3 | 3 | 0.00% | 5.84 | 0.02 | 2.03 | 0.00 |
| musig2 | secp256k1 | 5 | 5 | 0.00% | 9.18 | 0.02 | 1.99 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 18.73 | 0.04 | 2.00 | 0.00 |

### phase2_curves_schnorr

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.00% | 6.73 | 7.88 | 2.20 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.63 | 8.62 | 2.20 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 18.98 | 0.05 | 2.00 | 0.00 |
| musig2 | ristretto255 | 10 | 10 | 0.00% | 12.60 | 0.04 | 2.51 | 0.00 |

### phase2_curves_tbls

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| tbls | bls12-381 | 10 | 6 | 0.00% | 51.56 | 665.20 | 969.87 | 0.00 |

### phase3_network_loss0

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.00% | 6.46 | 7.42 | 2.19 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 10.99 | 13.66 | 2.12 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.38 | 8.30 | 2.13 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 11.01 | 15.26 | 2.13 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 52.81 | 673.93 | 967.91 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 87.27 | 1242.16 | 977.01 | 0.00 |

### phase3_network_loss10

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 1.00% | 6.61 | 13.40 | 2.20 | 6.67 |
| srts | secp256k1 | 20 | 11 | 1.00% | 11.34 | 32.94 | 2.24 | 20.00 |
| frost | secp256k1 | 10 | 6 | 1.00% | 6.68 | 8.69 | 2.19 | 0.00 |
| frost | secp256k1 | 20 | 11 | 1.00% | 11.36 | 25.25 | 2.22 | 10.00 |
| tbls | bls12-381 | 10 | 6 | 1.00% | 51.69 | 670.14 | 967.53 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 1.00% | 87.53 | 1239.69 | 974.14 | 6.67 |

### phase3_network_loss20

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 2.00% | 8.08 | 29.16 | 2.73 | 23.33 |
| srts | secp256k1 | 20 | 11 | 2.00% | 12.45 | 47.88 | 2.46 | 40.00 |
| frost | secp256k1 | 10 | 6 | 2.00% | 6.90 | 14.66 | 2.45 | 6.67 |
| frost | secp256k1 | 20 | 11 | 2.00% | 13.48 | 54.74 | 2.58 | 43.33 |
| tbls | bls12-381 | 10 | 6 | 2.00% | 51.29 | 691.52 | 970.89 | 13.33 |
| tbls | bls12-381 | 20 | 11 | 2.00% | 86.87 | 1244.54 | 966.30 | 20.00 |

### phase3_network_loss5

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.50% | 6.65 | 10.64 | 2.20 | 3.33 |
| srts | secp256k1 | 20 | 11 | 0.50% | 11.35 | 16.92 | 2.20 | 3.33 |
| frost | secp256k1 | 10 | 6 | 0.50% | 6.70 | 14.59 | 2.23 | 6.67 |
| frost | secp256k1 | 20 | 11 | 0.50% | 11.29 | 18.92 | 2.26 | 3.33 |
| tbls | bls12-381 | 10 | 6 | 0.50% | 51.51 | 689.01 | 974.08 | 13.33 |
| tbls | bls12-381 | 20 | 11 | 0.50% | 88.87 | 1237.46 | 981.61 | 0.00 |

### phase3_network_loss50

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 5.00% | 7.19 | 32.45 | 2.50 | 30.00 |
| srts | secp256k1 | 20 | 11 | 5.00% | 12.13 | 58.55 | 2.46 | 53.33 |
| frost | secp256k1 | 10 | 6 | 5.00% | 6.99 | 36.69 | 2.42 | 36.67 |
| frost | secp256k1 | 20 | 11 | 5.00% | 12.56 | 63.21 | 2.52 | 63.33 |
| tbls | bls12-381 | 10 | 6 | 5.00% | 52.35 | 713.20 | 968.21 | 36.67 |
| tbls | bls12-381 | 20 | 11 | 5.00% | 87.25 | 1300.01 | 961.97 | 76.67 |

### phase4_dkg_analysis_feldman

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 2.76 | 2.48 | 2.13 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 3.76 | 3.81 | 2.17 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 6.61 | 7.64 | 2.21 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 11.07 | 13.77 | 2.14 | 0.00 |
| srts | secp256k1 | 50 | 26 | 0.00% | 26.80 | 32.94 | 2.30 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 2.94 | 2.89 | 2.17 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 3.66 | 4.18 | 2.14 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.48 | 8.39 | 2.14 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 11.07 | 15.45 | 2.15 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 25.65 | 37.17 | 2.17 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 22.00 | 222.13 | 962.84 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 28.99 | 334.59 | 973.06 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 50.79 | 673.20 | 972.75 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 86.58 | 1230.80 | 977.64 | 0.00 |
| tbls | bls12-381 | 50 | 26 | 0.00% | 200.16 | 2925.96 | 975.91 | 0.00 |

### phase4_dkg_analysis_pedersen

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 2.78 | 2.51 | 2.16 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 3.71 | 3.78 | 2.17 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 6.60 | 7.63 | 2.13 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 11.09 | 13.76 | 2.14 | 0.00 |
| srts | secp256k1 | 50 | 26 | 0.00% | 25.36 | 32.85 | 2.14 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 2.80 | 2.82 | 2.14 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 3.66 | 4.18 | 2.12 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 6.56 | 8.42 | 2.15 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 11.07 | 15.53 | 2.15 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 25.64 | 37.30 | 2.14 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 21.64 | 221.66 | 961.84 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 29.00 | 341.23 | 965.45 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 50.80 | 664.47 | 962.10 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 87.48 | 1237.67 | 967.10 | 0.00 |
| tbls | bls12-381 | 50 | 26 | 0.00% | 200.18 | 2880.72 | 963.83 | 0.00 |

### phase5_stress_loss

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 1.00% | 6.52 | 10.92 | 2.17 | 3.33 |
| frost | secp256k1 | 10 | 6 | 1.00% | 6.68 | 14.82 | 2.23 | 6.67 |

### phase5_stress_scale

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 50 | 26 | 0.00% | 25.69 | 33.20 | 2.12 | 0.00 |
| srts | secp256k1 | 100 | 51 | 0.00% | 51.36 | 66.17 | 2.15 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 25.60 | 36.78 | 2.12 | 0.00 |
| frost | secp256k1 | 100 | 51 | 0.00% | 51.39 | 74.14 | 2.14 | 0.00 |

