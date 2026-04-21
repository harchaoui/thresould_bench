# 📊 Benchmark Performance Summary

*Generated: 2026-04-21 21:36:12*

Data source: `benchmark_20260421_194915.csv`

## ⚡ Online Signing Latency (ms)

| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Best Use Case |
|--------|-------|-----|-----|------|------|---------------|
| FROST | secp256k1 | 31.0 | 45.8 | 0.0 | 0.0 | General Purpose |
| SRTS | secp256k1 | 28.2 | 40.7 | 0.0 | 0.0 | Bitcoin Compat |

## ✅ Verification Time (ms)

| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Avg |
|--------|-------|-----|-----|------|------|-----|
| FROST | secp256k1 | 11.95 | 9.85 | 0.00 | 0.00 | 10.90 |
| SRTS | secp256k1 | 11.42 | 7.77 | 0.00 | 0.00 | 9.60 |

## 📦 Signature Sizes

| Scheme | Curve | Avg Size (bytes) |
|--------|-------|------------------|
| FROST | secp256k1 | 257.8 |
| SRTS | secp256k1 | 280.2 |
