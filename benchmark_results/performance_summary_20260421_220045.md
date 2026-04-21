# 📊 Benchmark Performance Summary

*Generated: 2026-04-21 22:00:45*

Data source: `benchmark_20260421_194907.csv`

## ⚡ Online Signing Latency (ms)

| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Best Use Case |
|--------|-------|-----|-----|------|------|---------------|
| FROST | secp256k1 | 30.3 | 43.4 | 76.7 | 143.5 | General Purpose |
| SRTS | secp256k1 | 28.4 | 42.4 | 73.0 | 126.1 | Bitcoin Compat |

## ✅ Verification Time (ms)

| Scheme | Curve | n=3 | n=5 | n=10 | n=20 | Avg |
|--------|-------|-----|-----|------|------|-----|
| FROST | secp256k1 | 12.23 | 10.99 | 8.40 | 9.85 | 10.37 |
| SRTS | secp256k1 | 13.35 | 5.73 | 8.68 | 10.25 | 9.50 |

## 📦 Signature Sizes

| Scheme | Curve | Avg Size (bytes) |
|--------|-------|------------------|
| FROST | secp256k1 | 258.2 |
| SRTS | secp256k1 | 280.3 |
