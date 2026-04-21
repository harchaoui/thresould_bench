"""
Benchmark suite for threshold signature schemes.
Tests FROST, SRTS, and TBLS on real hardware with simulation capabilities.
"""

import time
import statistics
from typing import List, Dict, Callable
from dataclasses import dataclass
import json


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    scheme: str
    curve: str
    n: int  # Total participants
    t: int  # Threshold
    operation: str  # keygen, presign, sign, aggregate, verify
    times_ms: List[float]
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    
    def to_dict(self) -> dict:
        return {
            "scheme": self.scheme,
            "curve": self.curve,
            "n": self.n,
            "t": self.t,
            "operation": self.operation,
            "mean_ms": self.mean_ms,
            "std_ms": self.std_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "iterations": len(self.times_ms),
        }


def benchmark_operation(op_func: Callable, iterations: int = 10, 
                        warmup: int = 2) -> List[float]:
    """
    Benchmark an operation multiple times.
    
    Args:
        op_func: Function to benchmark
        iterations: Number of timed iterations
        warmup: Number of warmup iterations (not timed)
    
    Returns:
        List of execution times in milliseconds
    """
    times = []
    
    # Warmup
    for _ in range(warmup):
        op_func()
    
    # Timed runs
    for _ in range(iterations):
        start = time.perf_counter()
        op_func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    
    return times


def compute_stats(times: List[float]) -> tuple:
    """Compute statistics from timing data."""
    if len(times) == 0:
        return 0, 0, 0, 0
    
    mean_val = statistics.mean(times)
    std_val = statistics.stdev(times) if len(times) > 1 else 0
    min_val = min(times)
    max_val = max(times)
    
    return mean_val, std_val, min_val, max_val


class SchemeBenchmarker:
    """Benchmark runner for threshold signature schemes."""
    
    def __init__(self, curves: List[str] = None):
        self.curves = curves or ["secp256k1", "bls12-381"]
        self.results: List[BenchmarkResult] = []
    
    def benchmark_keygen(self, scheme_class, curve: str, 
                         n: int, t: int, iterations: int = 10) -> BenchmarkResult:
        """Benchmark key generation."""
        scheme = scheme_class(curve_name=curve)
        
        def op():
            scheme.keygen(n, t)
        
        times = benchmark_operation(op, iterations)
        mean, std, min_t, max_t = compute_stats(times)
        
        result = BenchmarkResult(
            scheme=scheme_class.__name__,
            curve=curve,
            n=n,
            t=t,
            operation="keygen",
            times_ms=times,
            mean_ms=mean,
            std_ms=std,
            min_ms=min_t,
            max_ms=max_t,
        )
        self.results.append(result)
        return result
    
    def benchmark_presign(self, scheme_class, curve: str,
                          n: int, t: int, iterations: int = 10) -> BenchmarkResult:
        """Benchmark presignature generation."""
        scheme = scheme_class(curve_name=curve)
        keys = scheme.keygen(n, t)
        participants = list(range(1, n + 1))
        
        def op():
            scheme.presign(b"test message", participants)
        
        times = benchmark_operation(op, iterations)
        mean, std, min_t, max_t = compute_stats(times)
        
        result = BenchmarkResult(
            scheme=scheme_class.__name__,
            curve=curve,
            n=n,
            t=t,
            operation="presign",
            times_ms=times,
            mean_ms=mean,
            std_ms=std,
            min_ms=min_t,
            max_ms=max_t,
        )
        self.results.append(result)
        return result
    
    def benchmark_sign(self, scheme_class, curve: str,
                       n: int, t: int, iterations: int = 10) -> BenchmarkResult:
        """Benchmark partial signature generation."""
        scheme = scheme_class(curve_name=curve)
        keys = scheme.keygen(n, t)
        participants = list(range(1, n + 1))
        message = b"test message"
        
        # For SRTS/FROST, need presign first
        if hasattr(scheme, 'presign'):
            presign_data = scheme.presign(message, participants)
        else:
            presign_data = keys
        
        share = keys["shares"][0][1]  # First participant's share
        participant_id = 1
        
        def op():
            if hasattr(scheme, 'generate_presignatures'):
                # SRTS style
                scheme.sign(message, share, participant_id, presign_data)
            else:
                # FROST style
                scheme.sign(message, share, participant_id, presign_data)
        
        times = benchmark_operation(op, iterations)
        mean, std, min_t, max_t = compute_stats(times)
        
        result = BenchmarkResult(
            scheme=scheme_class.__name__,
            curve=curve,
            n=n,
            t=t,
            operation="sign",
            times_ms=times,
            mean_ms=mean,
            std_ms=std,
            min_ms=min_t,
            max_ms=max_t,
        )
        self.results.append(result)
        return result
    
    def benchmark_aggregate(self, scheme_class, curve: str,
                            n: int, t: int, iterations: int = 10) -> BenchmarkResult:
        """Benchmark signature aggregation."""
        scheme = scheme_class(curve_name=curve)
        keys = scheme.keygen(n, t)
        participants = list(range(1, n + 1))
        message = b"test message"
        
        # Generate partial signatures
        if hasattr(scheme, 'presign'):
            presign_data = scheme.presign(message, participants)
        else:
            presign_data = keys
        
        partial_sigs = []
        for i in range(min(t, n)):
            pid = participants[i]
            share = keys["shares"][i][1]
            
            if scheme_class.__name__ == "TBLS":
                psig = scheme.partial_sign(message, share, pid)
            else:
                psig = scheme.sign(message, share, pid, presign_data)
            partial_sigs.append(psig)
        
        def op():
            if scheme_class.__name__ == "TBLS":
                scheme.aggregate(partial_sigs, message, keys["public_key"])
            else:
                scheme.aggregate(partial_sigs, presign_data)
        
        times = benchmark_operation(op, iterations)
        mean, std, min_t, max_t = compute_stats(times)
        
        result = BenchmarkResult(
            scheme=scheme_class.__name__,
            curve=curve,
            n=n,
            t=t,
            operation="aggregate",
            times_ms=times,
            mean_ms=mean,
            std_ms=std,
            min_ms=min_t,
            max_ms=max_t,
        )
        self.results.append(result)
        return result
    
    def benchmark_verify(self, scheme_class, curve: str,
                         n: int, t: int, iterations: int = 10) -> BenchmarkResult:
        """Benchmark signature verification."""
        scheme = scheme_class(curve_name=curve)
        keys = scheme.keygen(n, t)
        participants = list(range(1, n + 1))
        message = b"test message"
        
        # Create full signature
        if hasattr(scheme, 'presign'):
            presign_data = scheme.presign(message, participants)
        else:
            presign_data = keys
        
        partial_sigs = []
        for i in range(min(t, n)):
            pid = participants[i]
            share = keys["shares"][i][1]
            
            if scheme_class.__name__ == "TBLS":
                psig = scheme.partial_sign(message, share, pid)
            else:
                psig = scheme.sign(message, share, pid, presign_data)
            partial_sigs.append(psig)
        
        if scheme_class.__name__ == "TBLS":
            sig_result = scheme.aggregate(partial_sigs, message, keys["public_key"])
            signature = sig_result["signature"]
        else:
            sig_result = scheme.aggregate(partial_sigs, presign_data)
            signature = sig_result
        
        def op():
            if scheme_class.__name__ == "TBLS":
                scheme.verify(message, signature, keys["public_key"])
            else:
                scheme.verify(message, signature, keys["public_key"])
        
        times = benchmark_operation(op, iterations)
        mean, std, min_t, max_t = compute_stats(times)
        
        result = BenchmarkResult(
            scheme=scheme_class.__name__,
            curve=curve,
            n=n,
            t=t,
            operation="verify",
            times_ms=times,
            mean_ms=mean,
            std_ms=std,
            min_ms=min_t,
            max_ms=max_t,
        )
        self.results.append(result)
        return result
    
    def run_full_benchmark(self, n: int = 5, t: int = 3, 
                           iterations: int = 10) -> List[BenchmarkResult]:
        """Run complete benchmark suite for all schemes and curves."""
        from ..schemes import SRTS, FROST, TBLS
        
        schemes = [SRTS, FROST, TBLS]
        all_results = []
        
        for scheme_cls in schemes:
            for curve in self.curves:
                # Skip incompatible combinations
                if scheme_cls == TBLS and curve != "bls12-381":
                    continue
                
                print(f"Benchmarking {scheme_cls.__name__} on {curve} (n={n}, t={t})...")
                
                try:
                    result = self.benchmark_keygen(scheme_cls, curve, n, t, iterations)
                    print(f"  keygen: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")
                except Exception as e:
                    print(f"  keygen failed: {e}")
                
                if scheme_cls != TBLS:
                    try:
                        result = self.benchmark_presign(scheme_cls, curve, n, t, iterations)
                        print(f"  presign: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")
                    except Exception as e:
                        print(f"  presign failed: {e}")
                    
                    try:
                        result = self.benchmark_sign(scheme_cls, curve, n, t, iterations)
                        print(f"  sign: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")
                    except Exception as e:
                        print(f"  sign failed: {e}")
                    
                    try:
                        result = self.benchmark_aggregate(scheme_cls, curve, n, t, iterations)
                        print(f"  aggregate: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")
                    except Exception as e:
                        print(f"  aggregate failed: {e}")
                
                try:
                    result = self.benchmark_verify(scheme_cls, curve, n, t, iterations)
                    print(f"  verify: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")
                except Exception as e:
                    print(f"  verify failed: {e}")
                
                print()
        
        return self.results
    
    def export_results(self, filename: str = "benchmark_results.json"):
        """Export results to JSON file."""
        data = [r.to_dict() for r in self.results]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results exported to {filename}")
    
    def print_summary(self):
        """Print summary table of results."""
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        print(f"{'Scheme':<10} {'Curve':<12} {'n':<4} {'t':<4} {'Operation':<12} {'Mean(ms)':<10} {'Std(ms)':<10}")
        print("-"*80)
        
        for r in self.results:
            print(f"{r.scheme:<10} {r.curve:<12} {r.n:<4} {r.t:<4} {r.operation:<12} {r.mean_ms:<10.2f} {r.std_ms:<10.2f}")
        
        print("="*80)


def run_benchmark_suite(n: int = 5, t: int = 3, iterations: int = 10,
                        output_file: str = "benchmark_results.json"):
    """Convenience function to run full benchmark suite."""
    benchmarker = SchemeBenchmarker(curves=["secp256k1", "bls12-381"])
    results = benchmarker.run_full_benchmark(n, t, iterations)
    benchmarker.print_summary()
    benchmarker.export_results(output_file)
    return results
