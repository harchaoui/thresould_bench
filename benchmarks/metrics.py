"""
Metrics Collection and Statistical Analysis for Benchmarks
===========================================================
Collects timing, memory, and communication metrics with statistical analysis.
Produces flat schema output as specified in Section 3.
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json
from datetime import datetime


@dataclass
class TimingMetrics:
    """Timing metrics for a single operation."""
    operation_name: str
    durations_ms: List[float] = field(default_factory=list)
    
    def add(self, duration_ms: float):
        """Add a timing measurement."""
        self.durations_ms.append(duration_ms)
    
    @property
    def count(self) -> int:
        return len(self.durations_ms)
    
    @property
    def mean(self) -> float:
        return statistics.mean(self.durations_ms) if self.durations_ms else 0.0
    
    @property
    def median(self) -> float:
        return statistics.median(self.durations_ms) if self.durations_ms else 0.0
    
    @property
    def std_dev(self) -> float:
        return statistics.stdev(self.durations_ms) if len(self.durations_ms) > 1 else 0.0
    
    @property
    def min_val(self) -> float:
        return min(self.durations_ms) if self.durations_ms else 0.0
    
    @property
    def max_val(self) -> float:
        return max(self.durations_ms) if self.durations_ms else 0.0
    
    @property
    def p95(self) -> float:
        if not self.durations_ms:
            return 0.0
        sorted_data = sorted(self.durations_ms)
        idx = int(len(sorted_data) * 0.95)
        return sorted_data[min(idx, len(sorted_data) - 1)]
    
    @property
    def p99(self) -> float:
        if not self.durations_ms:
            return 0.0
        sorted_data = sorted(self.durations_ms)
        idx = int(len(sorted_data) * 0.99)
        return sorted_data[min(idx, len(sorted_data) - 1)]
    
    @property
    def ops_per_second(self) -> float:
        """Operations per second based on mean duration."""
        if self.mean == 0:
            return 0.0
        return 1000.0 / self.mean
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation_name,
            "count": self.count,
            "mean_ms": round(self.mean, 4),
            "median_ms": round(self.median, 4),
            "std_dev_ms": round(self.std_dev, 4),
            "min_ms": round(self.min_val, 4),
            "max_ms": round(self.max_val, 4),
            "p95_ms": round(self.p95, 4),
            "p99_ms": round(self.p99, 4),
            "ops_per_sec": round(self.ops_per_second, 2)
        }


@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    operation_name: str
    peak_memory_mb: List[float] = field(default_factory=list)
    
    def add(self, memory_mb: float):
        """Add a memory measurement."""
        self.peak_memory_mb.append(memory_mb)
    
    @property
    def mean(self) -> float:
        return statistics.mean(self.peak_memory_mb) if self.peak_memory_mb else 0.0
    
    @property
    def max_val(self) -> float:
        return max(self.peak_memory_mb) if self.peak_memory_mb else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation_name,
            "mean_mb": round(self.mean, 2),
            "max_mb": round(self.max_val, 2)
        }


@dataclass
class SignatureMetrics:
    """Signature-specific metrics."""
    operation_name: str
    signature_size_bytes: List[int] = field(default_factory=list)
    verification_time_ms: List[float] = field(default_factory=list)
    
    def add_signature(self, size_bytes: int):
        """Add signature size measurement."""
        self.signature_size_bytes.append(size_bytes)
    
    def add_verification(self, time_ms: float):
        """Add verification time measurement."""
        self.verification_time_ms.append(time_ms)
    
    @property
    def avg_signature_size(self) -> float:
        return statistics.mean(self.signature_size_bytes) if self.signature_size_bytes else 0.0
    
    @property
    def avg_verification_time(self) -> float:
        return statistics.mean(self.verification_time_ms) if self.verification_time_ms else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation_name,
            "avg_signature_size_bytes": round(self.avg_signature_size, 2),
            "avg_verification_time_ms": round(self.avg_verification_time, 4)
        }


class BenchmarkMetrics:
    """Main metrics collector for benchmark runs."""
    
    def __init__(self):
        self.timing_metrics: Dict[str, TimingMetrics] = {}
        self.memory_metrics: Dict[str, MemoryMetrics] = {}
        self.signature_metrics: Dict[str, SignatureMetrics] = {}
        self.metadata: Dict[str, Any] = {}
        
    def get_timing(self, operation_name: str) -> TimingMetrics:
        """Get or create timing metrics for an operation."""
        if operation_name not in self.timing_metrics:
            self.timing_metrics[operation_name] = TimingMetrics(operation_name)
        return self.timing_metrics[operation_name]
    
    def get_memory(self, operation_name: str) -> MemoryMetrics:
        """Get or create memory metrics for an operation."""
        if operation_name not in self.memory_metrics:
            self.memory_metrics[operation_name] = MemoryMetrics(operation_name)
        return self.memory_metrics[operation_name]
    
    def get_signature(self, operation_name: str) -> SignatureMetrics:
        """Get or create signature metrics for an operation."""
        if operation_name not in self.signature_metrics:
            self.signature_metrics[operation_name] = SignatureMetrics(operation_name)
        return self.signature_metrics[operation_name]
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata for the benchmark run."""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all metrics to dictionary (flat structure)."""
        result = dict(self.metadata)
        
        # Add timing metrics
        for op_name, timing in self.timing_metrics.items():
            result[f"{op_name}_mean_ms"] = timing.mean
            result[f"{op_name}_median_ms"] = timing.median
            result[f"{op_name}_std_ms"] = timing.std_dev
            result[f"{op_name}_p95_ms"] = timing.p95
        
        # Add memory metrics
        for op_name, mem in self.memory_metrics.items():
            result[f"{op_name}_mean_mb"] = mem.mean
        
        # Add signature metrics
        for op_name, sig in self.signature_metrics.items():
            result[f"{op_name}_avg_size_bytes"] = sig.avg_signature_size
            result[f"{op_name}_avg_verify_ms"] = sig.avg_verification_time
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save_json(self, filepath: str):
        """Save metrics to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, metrics: BenchmarkMetrics, operation_name: str):
        self.metrics = metrics
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        self.metrics.get_timing(self.operation_name).add(duration_ms)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB (platform-independent)."""
    try:
        import resource
        # Get memory usage in KB, convert to MB
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes, on Linux it's in KB
        import sys
        if sys.platform == 'darwin':
            return usage_kb / (1024 * 1024)
        else:
            return usage_kb / 1024
    except ImportError:
        return 0.0


# =============================================================================
# SECTION 3 — FLAT SCHEMA OUTPUT
# =============================================================================
# Every result must be saved as a flat dict — no nesting.
# This is the schema data_loader.py will consume directly.
# =============================================================================

def flatten_result(runner_output: Dict[str, Any], phase: str, 
                   scheme: str, curve: str, dkg: str, n: int, t: int,
                   loss_rate: float, compatibility: str, preferred: bool,
                   musig2_nofn: bool = False, tbls_noninteractive: bool = False) -> Dict[str, Any]:
    """
    Convert runner's native output format to the flat schema.
    
    Args:
        runner_output: Raw output from BenchmarkRunner
        phase: Phase name (e.g., "phase1_dkg")
        scheme: Scheme name
        curve: Curve name
        dkg: DKG type
        n: Number of participants
        t: Threshold
        loss_rate: Packet loss rate
        compatibility: "valid", "suboptimal", or "invalid"
        preferred: True if this is a preferred combination
        musig2_nofn: True only for MuSig2 (t always equals n)
        tbls_noninteractive: True only for tBLS (non-interactive signing)
    
    Returns:
        Flat dictionary matching the schema in Section 3
    """
    # Extract timing metrics from nested structure
    timing = runner_output.get("timing", {})
    stress_metrics = runner_output.get("stress_metrics", {})
    signatures = runner_output.get("signatures", {})
    memory = runner_output.get("memory", {})
    
    # Build flat result
    result = {
        # Core identifiers
        "scheme": scheme,
        "curve": curve,
        "dkg": dkg,
        "n": n,
        "t": t,
        "loss_rate": loss_rate,
        "phase": phase,
        
        # Compatibility flags
        "compatibility": compatibility,
        "preferred": preferred,
        "musig2_nofn": musig2_nofn,
        "tbls_noninteractive": tbls_noninteractive,
        
        # Key generation metrics
        "keygen_ms": timing.get("keygen_mean_ms"),
        "keygen_std_ms": timing.get("keygen_std_ms"),
        "keygen_median_ms": timing.get("keygen_median_ms"),
        "keygen_p95_ms": timing.get("keygen_p95_ms"),
        
        # Signing metrics (null for keygen-only phases)
        "sign_ms": timing.get("partial_sign_mean_ms"),
        "sign_std_ms": timing.get("partial_sign_std_ms"),
        "sign_median_ms": timing.get("partial_sign_median_ms"),
        "sign_p95_ms": timing.get("partial_sign_p95_ms"),
        
        # Verification metrics
        "verify_ms": timing.get("verify_mean_ms"),
        "verify_std_ms": timing.get("verify_std_ms"),
        "verify_median_ms": timing.get("verify_median_ms"),
        "verify_p95_ms": timing.get("verify_p95_ms"),
        
        # Network metrics
        "network_overhead_ms": stress_metrics.get("avg_network_overhead_ms"),
        "retries_per_iter": stress_metrics.get("avg_retries_per_iter"),
        "messages_per_iter": stress_metrics.get("avg_messages_per_iter"),
        "completion_rate": stress_metrics.get("completion_rate"),
        "successful_iterations": stress_metrics.get("successful_iterations"),
        "total_iterations": stress_metrics.get("total_iterations"),
        
        # Signature and memory metrics
        "signature_size_bytes": signatures.get("final_sig_avg_size_bytes"),
        "memory_mb": memory.get("keygen_mean_mb"),
        
        # Timestamp
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def create_empty_result(phase: str, scheme: str, curve: str, dkg: str, 
                        n: int, t: int, loss_rate: float, 
                        compatibility: str, preferred: bool,
                        musig2_nofn: bool = False, 
                        tbls_noninteractive: bool = False) -> Dict[str, Any]:
    """
    Create an empty result record with all fields set to null/defaults.
    Used for phases that don't measure certain metrics (e.g., keygen-only phases).
    """
    return {
        # Core identifiers
        "scheme": scheme,
        "curve": curve,
        "dkg": dkg,
        "n": n,
        "t": t,
        "loss_rate": loss_rate,
        "phase": phase,
        
        # Compatibility flags
        "compatibility": compatibility,
        "preferred": preferred,
        "musig2_nofn": musig2_nofn,
        "tbls_noninteractive": tbls_noninteractive,
        
        # All metrics set to null for phases that don't measure them
        "keygen_ms": None,
        "keygen_std_ms": None,
        "keygen_median_ms": None,
        "keygen_p95_ms": None,
        
        "sign_ms": None,
        "sign_std_ms": None,
        "sign_median_ms": None,
        "sign_p95_ms": None,
        
        "verify_ms": None,
        "verify_std_ms": None,
        "verify_median_ms": None,
        "verify_p95_ms": None,
        
        "network_overhead_ms": None,
        "retries_per_iter": None,
        "messages_per_iter": None,
        "completion_rate": None,
        "successful_iterations": None,
        "total_iterations": None,
        
        "signature_size_bytes": None,
        "memory_mb": None,
        
        "timestamp": datetime.now().isoformat()
    }
