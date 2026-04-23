# JSON Plot Support - Bugfix Summary

## Problem
The `plot_results.py` script only supported CSV files, but the benchmark suite now generates JSON output by default. This caused errors when trying to visualize benchmark results.

## Solution
Enhanced `plot_results.py` to support both JSON and CSV formats with automatic detection.

## Changes Made

### 1. Added JSON Import
```python
import json
```

### 2. New Function: `find_latest_data_file()`
- Searches for both JSON and CSV files
- Prefers JSON if available
- Selects file with most data rows
- Supports patterns: `*phase*.json`, `benchmark_*.json`, `*phase*.csv`, `benchmark_*.csv`

### 3. New Function: `load_benchmark_data_from_json()`
- Loads nested JSON structure
- Flattens timing, memory, stress_metrics, and signatures into columns
- Applies common cleaning operations
- Calculates `timing_online_sign_mean_ms` from partial_sign + aggregate

### 4. Refactored: `load_benchmark_data_from_csv()`
- Now calls shared `_clean_dataframe()` helper

### 5. New Helper: `_clean_dataframe()`
- Common cleaning logic for both JSON and CSV
- Removes all-NaN rows
- Calculates derived metrics

### 6. Updated: `main_wrapper()`
- Detects file type from extension
- Routes to appropriate loader function
- Uses `data_path` instead of `csv_path` throughout

## Usage

### Automatic Detection (Recommended)
```bash
cd /workspace/srts_enhanced/benchmarks
python3 plot_results.py
```

### Specify Output Directory
```python
from plot_results import main_wrapper
main_wrapper('../benchmark_results')
```

## Testing
Created test JSON file and verified:
- ✓ File detection works
- ✓ JSON loading and flattening works  
- ✓ All plots generate successfully
- ✓ Both PNG and PDF outputs created
- ✓ Summary markdown generated

## Backward Compatibility
- CSV support fully maintained
- Existing workflows unchanged
- Auto-detection prefers JSON but falls back to CSV

## Files Modified
- `/workspace/srts_enhanced/benchmarks/plot_results.py` (lines 1-708)

## Generated Plots
1. `signing_latency_*.png/pdf` - Signing time vs participants
2. `verification_time_*.png/pdf` - Verification comparison
3. `keygen_time_*.png/pdf` - Key generation scaling
4. `degradation_curve_*.png/pdf` - Network overhead analysis
5. `performance_summary_*.md` - Markdown summary table
