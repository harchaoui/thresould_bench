# Comprehensive Benchmark Summary - Performance Under Stress

**Generated:** 2026-04-24T00:32:03.779113

**Phases Completed:** phase0_theoretical, phase1_baseline, phase2_curves, phase3_network, phase4_dkg, phase5_stress

## Overall Statistics

- Total configurations tested: 103
- Start time: 2026-04-23T23:18:05.027850

## Stress Analysis Report

### Performance Degradation Analysis

**Under varying packet loss conditions** (comparing identical n/t configurations):

- **FROST**: Experienced 105.7% slowdown at 5.0% packet loss. Network overhead: 53.3ms.
- **SRTS**: Experienced 115.3% slowdown at 5.0% packet loss. Network overhead: 56.7ms.
- **TBLS**: Experienced 3.0% slowdown at 5.0% packet loss. Network overhead: 50.0ms.

### Recommendations

- **Most resilient to packet loss**: TBLS (3.0% slowdown)
- **Most sensitive to packet loss**: SRTS (115.3% slowdown)

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
| srts | secp256k1 | 3 | 2 | 0.00% | 4.42 | 3.98 | 3.42 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 5.95 | 6.00 | 3.43 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 10.35 | 12.10 | 3.45 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 18.00 | 22.06 | 3.44 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 4.41 | 4.46 | 3.41 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 5.97 | 6.82 | 3.50 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 10.38 | 13.72 | 3.54 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 17.69 | 24.72 | 3.50 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 35.47 | 361.66 | 1553.95 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 46.83 | 535.83 | 1557.80 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 84.20 | 1090.03 | 1558.39 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 141.04 | 1988.37 | 1560.50 | 0.00 |
| musig2 | secp256k1 | 3 | 3 | 0.00% | 9.02 | 0.03 | 3.20 | 0.00 |
| musig2 | secp256k1 | 5 | 5 | 0.00% | 14.96 | 0.04 | 3.26 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 29.99 | 0.07 | 3.24 | 0.00 |

### phase1_baseline_pedersen

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 4.50 | 4.30 | 3.57 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 6.38 | 9.34 | 3.67 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 10.30 | 12.05 | 3.42 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 17.88 | 22.08 | 3.46 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 4.41 | 4.47 | 3.42 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 5.89 | 6.70 | 3.43 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 10.48 | 13.57 | 3.49 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 17.82 | 25.18 | 3.44 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 35.47 | 360.12 | 1568.28 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 47.35 | 542.82 | 1581.71 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 82.97 | 1079.03 | 1562.74 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 139.13 | 1976.10 | 1559.03 | 0.00 |
| musig2 | secp256k1 | 3 | 3 | 0.00% | 9.28 | 0.03 | 3.26 | 0.00 |
| musig2 | secp256k1 | 5 | 5 | 0.00% | 15.00 | 0.04 | 3.27 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 30.10 | 0.08 | 3.26 | 0.00 |

### phase2_curves_schnorr

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.00% | 10.66 | 12.97 | 3.71 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 10.55 | 13.72 | 3.44 | 0.00 |
| musig2 | secp256k1 | 10 | 10 | 0.00% | 29.82 | 0.07 | 3.23 | 0.00 |
| musig2 | ristretto255 | 10 | 10 | 0.00% | 19.87 | 0.07 | 4.01 | 0.00 |

### phase2_curves_tbls

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| tbls | bls12-381 | 10 | 6 | 0.00% | 81.02 | 1076.27 | 1561.13 | 0.00 |

### phase3_network_loss0

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.00% | 10.44 | 12.30 | 3.50 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 17.81 | 22.16 | 3.43 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 10.52 | 13.85 | 3.47 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 17.80 | 24.97 | 3.42 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 82.24 | 1076.97 | 1548.31 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 139.36 | 1972.71 | 1553.91 | 0.00 |

### phase3_network_loss10

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 1.00% | 10.74 | 19.01 | 3.51 | 6.67 |
| srts | secp256k1 | 20 | 11 | 1.00% | 18.34 | 29.02 | 3.53 | 6.67 |
| frost | secp256k1 | 10 | 6 | 1.00% | 12.56 | 21.83 | 4.04 | 10.00 |
| frost | secp256k1 | 20 | 11 | 1.00% | 17.92 | 33.94 | 3.48 | 10.00 |
| tbls | bls12-381 | 10 | 6 | 1.00% | 86.45 | 1140.49 | 1633.96 | 10.00 |
| tbls | bls12-381 | 20 | 11 | 1.00% | 140.73 | 2059.96 | 1603.63 | 3.33 |

### phase3_network_loss20

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 2.00% | 10.65 | 16.15 | 3.51 | 16.67 |
| srts | secp256k1 | 20 | 11 | 2.00% | 17.86 | 46.61 | 3.47 | 26.67 |
| frost | secp256k1 | 10 | 6 | 2.00% | 10.49 | 19.66 | 3.47 | 6.67 |
| frost | secp256k1 | 20 | 11 | 2.00% | 17.76 | 34.25 | 3.43 | 10.00 |
| tbls | bls12-381 | 10 | 6 | 2.00% | 81.14 | 1101.00 | 1544.51 | 26.67 |
| tbls | bls12-381 | 20 | 11 | 2.00% | 145.39 | 2076.38 | 1612.54 | 23.33 |

### phase3_network_loss5

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 0.50% | 10.55 | 15.40 | 3.46 | 3.33 |
| srts | secp256k1 | 20 | 11 | 0.50% | 17.90 | 25.17 | 3.42 | 3.33 |
| frost | secp256k1 | 10 | 6 | 0.50% | 10.37 | 16.88 | 3.46 | 10.00 |
| frost | secp256k1 | 20 | 11 | 0.50% | 18.17 | 28.38 | 3.54 | 3.33 |
| tbls | bls12-381 | 10 | 6 | 0.50% | 83.01 | 1111.31 | 1589.55 | 10.00 |
| tbls | bls12-381 | 20 | 11 | 0.50% | 145.57 | 2057.53 | 1588.43 | 3.33 |

### phase3_network_loss50

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 5.00% | 10.96 | 52.22 | 3.70 | 50.00 |
| srts | secp256k1 | 20 | 11 | 5.00% | 20.86 | 76.70 | 3.92 | 63.33 |
| frost | secp256k1 | 10 | 6 | 5.00% | 10.67 | 44.18 | 3.57 | 40.00 |
| frost | secp256k1 | 20 | 11 | 5.00% | 18.07 | 83.51 | 3.53 | 66.67 |
| tbls | bls12-381 | 10 | 6 | 5.00% | 81.24 | 1118.82 | 1552.63 | 40.00 |
| tbls | bls12-381 | 20 | 11 | 5.00% | 140.30 | 2064.16 | 1560.10 | 60.00 |

### phase4_dkg_analysis_feldman

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 4.67 | 4.06 | 3.50 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 5.91 | 6.01 | 3.44 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 10.82 | 12.54 | 3.54 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 18.60 | 23.45 | 3.59 | 0.00 |
| srts | secp256k1 | 50 | 26 | 0.00% | 41.10 | 53.53 | 3.47 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 4.50 | 4.53 | 3.48 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 6.57 | 7.25 | 3.67 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 11.11 | 14.09 | 3.91 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 18.03 | 25.00 | 3.50 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 40.82 | 60.57 | 3.43 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 35.28 | 361.83 | 1568.68 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 52.09 | 591.18 | 1799.06 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 121.34 | 1365.49 | 1879.43 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 153.11 | 2054.68 | 1632.36 | 0.00 |
| tbls | bls12-381 | 50 | 26 | 0.00% | 319.97 | 4734.17 | 1574.83 | 0.00 |

### phase4_dkg_analysis_pedersen

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 3 | 2 | 0.00% | 4.62 | 4.22 | 3.53 | 0.00 |
| srts | secp256k1 | 5 | 3 | 0.00% | 6.17 | 6.26 | 3.57 | 0.00 |
| srts | secp256k1 | 10 | 6 | 0.00% | 12.58 | 12.47 | 3.48 | 0.00 |
| srts | secp256k1 | 20 | 11 | 0.00% | 18.14 | 22.87 | 3.49 | 0.00 |
| srts | secp256k1 | 50 | 26 | 0.00% | 41.44 | 54.40 | 3.46 | 0.00 |
| frost | secp256k1 | 3 | 2 | 0.00% | 4.40 | 4.44 | 3.41 | 0.00 |
| frost | secp256k1 | 5 | 3 | 0.00% | 5.87 | 6.66 | 3.41 | 0.00 |
| frost | secp256k1 | 10 | 6 | 0.00% | 10.64 | 14.15 | 3.63 | 0.00 |
| frost | secp256k1 | 20 | 11 | 0.00% | 18.54 | 25.80 | 3.65 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 41.84 | 60.97 | 3.74 | 0.00 |
| tbls | bls12-381 | 3 | 2 | 0.00% | 35.91 | 366.73 | 1583.79 | 0.00 |
| tbls | bls12-381 | 5 | 3 | 0.00% | 47.42 | 541.42 | 1562.34 | 0.00 |
| tbls | bls12-381 | 10 | 6 | 0.00% | 82.70 | 1086.04 | 1560.42 | 0.00 |
| tbls | bls12-381 | 20 | 11 | 0.00% | 142.67 | 2000.48 | 1561.12 | 0.00 |
| tbls | bls12-381 | 50 | 26 | 0.00% | 313.54 | 4743.31 | 1572.21 | 0.00 |

### phase5_stress_loss

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 10 | 6 | 1.00% | 10.51 | 18.26 | 3.52 | 6.67 |
| frost | secp256k1 | 10 | 6 | 1.00% | 10.38 | 25.57 | 3.46 | 13.33 |

### phase5_stress_scale

| Scheme | Curve | n | t | Loss Rate | KeyGen (ms) | Sign (ms) | Verify (ms) | Network Overhead (ms) |
|--------|-------|---|---|-----------|-------------|-----------|-------------|----------------------|
| srts | secp256k1 | 50 | 26 | 0.00% | 41.05 | 53.01 | 3.41 | 0.00 |
| srts | secp256k1 | 100 | 51 | 0.00% | 84.07 | 108.20 | 3.54 | 0.00 |
| frost | secp256k1 | 50 | 26 | 0.00% | 40.60 | 59.12 | 3.42 | 0.00 |
| frost | secp256k1 | 100 | 51 | 0.00% | 82.89 | 119.35 | 3.63 | 0.00 |

