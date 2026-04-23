#!/bin/bash

# Check and install dependencies
pip3 install -r requirements.txt
pip install -r requirements.txt

# Run the benchmark
python3 -m srts_enhanced.benchmarks.comprehensive_benchmark
