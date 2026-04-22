"""
Metrics Collection and Statistical Analysis for Benchmarks
Collects timing, memory, and communication metrics with statistical analysis.
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json


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
class CommunicationMetrics:
    """Communication overhead metrics."""
    operation_name: str
    bytes_sent: List[int] = field(default_factory=list)
    bytes_received: List[int] = field(default_factory=list)
    
    def add(self, sent: int, received: int = 0):
        """Add communication measurements."""
        self.bytes_sent.append(sent)
        self.bytes_received.append(received)
    
    @property
    def total_bytes_mean(self) -> float:
        total = [s + r for s, r in zip(self.bytes_sent, self.bytes_received)]
        return statistics.mean(total) if total else 0.0
    
    @property
    def sent_mean(self) -> float:
        return statistics.mean(self.bytes_sent) if self.bytes_sent else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation_name,
            "mean_bytes_sent": round(self.sent_mean, 2),
            "mean_bytes_received": round(statistics.mean(self.bytes_received) if self.bytes_received else 0, 2),
            "mean_total_bytes": round(self.total_bytes_mean, 2)
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
        self.communication_metrics: Dict[str, CommunicationMetrics] = {}
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
    
    def get_communication(self, operation_name: str) -> CommunicationMetrics:
        """Get or create communication metrics for an operation."""
        if operation_name not in self.communication_metrics:
            self.communication_metrics[operation_name] = CommunicationMetrics(operation_name)
        return self.communication_metrics[operation_name]
    
    def get_signature(self, operation_name: str) -> SignatureMetrics:
        """Get or create signature metrics for an operation."""
        if operation_name not in self.signature_metrics:
            self.signature_metrics[operation_name] = SignatureMetrics(operation_name)
        return self.signature_metrics[operation_name]
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata for the benchmark run."""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all metrics to dictionary."""
        return {
            "metadata": self.metadata,
            "timing": {k: v.to_dict() for k, v in self.timing_metrics.items()},
            "memory": {k: v.to_dict() for k, v in self.memory_metrics.items()},
            "communication": {k: v.to_dict() for k, v in self.communication_metrics.items()},
            "signatures": {k: v.to_dict() for k, v in self.signature_metrics.items()}
        }
    
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
