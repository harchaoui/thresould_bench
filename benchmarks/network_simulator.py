"""
Network Simulator for Benchmark Testing
========================================
Simulates network conditions: latency, packet loss, and bandwidth limits.
"""

import time
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass


# =============================================================================
# Constants
# =============================================================================

# Retry timeout represents a realistic LAN ACK timeout (100ms)
# This is the time we wait before assuming a packet was lost and retrying
RETRY_TIMEOUT_MS = 100.0


@dataclass
class NetworkCondition:
    """Network condition parameters."""
    latency_ms: float = 0.0       # Fixed latency in milliseconds
    jitter_ms: float = 0.0        # Random jitter variation
    packet_loss_rate: float = 0.0 # Probability of packet loss (0.0 to 1.0)
    bandwidth_mbps: float = 0.0   # Bandwidth limit in Mbps (0 = unlimited)


class NetworkSimulator:
    """
    Simulates network conditions for distributed signing protocols.
    
    Usage:
        simulator = NetworkSimulator(packet_loss_rate=0.01, random_seed=42)
        
        # Simulate sending a message with retry
        result = simulator.send_with_retry(data_size_bytes)
        
        # Get overhead metrics
        overhead = simulator.get_overhead_ms()
    """
    
    def __init__(
        self,
        latency_ms: float = 0.0,
        jitter_ms: float = 0.0,
        packet_loss_rate: float = 0.0,
        bandwidth_mbps: float = 0.0,
        random_seed: int = 42
    ):
        """
        Initialize network simulator.
        
        Args:
            latency_ms: Base latency in milliseconds
            jitter_ms: Random jitter variation
            packet_loss_rate: Probability of packet loss (0.0 to 1.0)
            bandwidth_mbps: Bandwidth limit in Mbps (0 = unlimited)
            random_seed: Random seed for reproducibility
        """
        self.condition = NetworkCondition(
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            packet_loss_rate=packet_loss_rate,
            bandwidth_mbps=bandwidth_mbps
        )
        self.random_seed = random_seed
        random.seed(random_seed)
        
        # Statistics tracking
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_retried = 0
        self.total_bytes_sent = 0
        self.total_latency_ms = 0.0
        self.total_overhead_ms = 0.0
        
    def simulate_delay(self, data_size_bytes: int = 0) -> Dict[str, Any]:
        """
        Simulate network delay based on current conditions.
        
        Args:
            data_size_bytes: Size of data being sent (for bandwidth calculation)
            
        Returns:
            Dict with keys:
                - success (bool): Whether the packet was delivered
                - delay (float): Actual delay applied in milliseconds
                - lost (bool): Whether this was a lost packet
        """
        result = {"success": True, "delay": 0.0, "lost": False}
        
        # Check for packet loss
        if random.random() < self.condition.packet_loss_rate:
            self.packets_lost += 1
            self.packets_sent += 1
            result["success"] = False
            result["lost"] = True
            return result
        
        self.packets_sent += 1
        self.total_bytes_sent += data_size_bytes
        
        # Calculate total delay
        total_delay = self.condition.latency_ms
        
        # Add jitter
        if self.condition.jitter_ms > 0:
            jitter = random.uniform(-self.condition.jitter_ms, self.condition.jitter_ms)
            total_delay += jitter
        
        # Add bandwidth delay
        if self.condition.bandwidth_mbps > 0 and data_size_bytes > 0:
            # Convert Mbps to bytes/ms: Mbps * 10^6 / 8 / 1000 = bytes/ms
            bandwidth_bytes_per_ms = (self.condition.bandwidth_mbps * 1e6) / 8 / 1000
            bandwidth_delay = data_size_bytes / bandwidth_bytes_per_ms
            total_delay += bandwidth_delay
        
        # Apply delay
        if total_delay > 0:
            time.sleep(total_delay / 1000.0)  # Convert ms to seconds
            self.total_latency_ms += total_delay
        
        result["delay"] = total_delay
        return result
    
    def send_message(self, data_size_bytes: int = 0) -> Dict[str, Any]:
        """Simulate sending a message with network conditions."""
        return self.simulate_delay(data_size_bytes)
    
    def receive_message(self, data_size_bytes: int = 0) -> Dict[str, Any]:
        """Simulate receiving a message with network conditions."""
        return self.simulate_delay(data_size_bytes)
    
    def send_with_retry(
        self, 
        data_size_bytes: int = 0, 
        max_retries: int = 3,
        timeout_ms: float = RETRY_TIMEOUT_MS
    ) -> Dict[str, Any]:
        """
        Send a message with automatic retry on packet loss.
        
        Args:
            data_size_bytes: Size of data being sent
            max_retries: Maximum number of retry attempts
            timeout_ms: Timeout per attempt before retry (simulates waiting for ACK).
                       Default is RETRY_TIMEOUT_MS (100ms), representing a realistic
                       LAN ACK timeout.
            
        Returns:
            Dict with keys:
                - success (bool): Whether the packet was eventually delivered
                - delay (float): Total delay including retries and timeouts
                - retries (int): Number of retries needed
                - lost (bool): Whether any packets were lost during transmission
        """
        total_delay = 0.0
        retries = 0
        
        for attempt in range(max_retries + 1):
            result = self.simulate_delay(data_size_bytes)
            total_delay += result["delay"]
            
            if result["success"]:
                return {
                    "success": True,
                    "delay": total_delay,
                    "retries": retries,
                    "lost": retries > 0
                }
            
            # Packet lost, apply timeout before retry (simulates waiting for ACK timeout)
            if attempt < max_retries:
                retries += 1
                self.packets_retried += 1
                # Apply realistic timeout delay for each retry
                time.sleep(timeout_ms / 1000.0)
                total_delay += timeout_ms
        
        # All retries exhausted
        return {
            "success": False,
            "delay": total_delay,
            "retries": retries,
            "lost": True
        }
    
    def get_overhead_ms(self) -> float:
        """
        Get total retry-induced overhead in milliseconds.
        
        This returns the cumulative time spent waiting for retries due to
        packet loss. It's the sum of all timeout delays applied during
        send_with_retry calls.
        
        Returns:
            Total overhead in milliseconds
        """
        return self.total_overhead_ms
    
    def reset_overhead_tracking(self):
        """Reset overhead tracking for fresh measurement."""
        self.total_overhead_ms = 0.0
    
    def round_trip(self, data_size_bytes: int = 0):
        """Context manager for simulating round-trip communication."""
        return RoundTripContext(self, data_size_bytes)
    
    def get_stats(self) -> dict:
        """Get network simulation statistics."""
        return {
            "packets_sent": self.packets_sent,
            "packets_lost": self.packets_lost,
            "packets_retried": self.packets_retried,
            "packet_loss_rate_actual": (
                self.packets_lost / self.packets_sent 
                if self.packets_sent > 0 else 0.0
            ),
            "total_bytes_sent": self.total_bytes_sent,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "avg_latency_ms": (
                self.total_latency_ms / self.packets_sent 
                if self.packets_sent > 0 else 0.0
            ),
            "total_overhead_ms": round(self.total_overhead_ms, 2)
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_retried = 0
        self.total_bytes_sent = 0
        self.total_latency_ms = 0.0
        self.total_overhead_ms = 0.0


class RoundTripContext:
    """Context manager for round-trip network simulation."""
    
    def __init__(self, simulator: NetworkSimulator, data_size_bytes: int = 0):
        self.simulator = simulator
        self.data_size_bytes = data_size_bytes
        
    def __enter__(self):
        # Simulate send delay
        self.simulator.send_message(self.data_size_bytes)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Simulate receive delay
        if exc_type is None:  # Only if no exception occurred
            self.simulator.receive_message(self.data_size_bytes)


def create_simulator_from_preset(
    preset: str, 
    packet_loss_rate: float = 0.0,
    random_seed: int = 42
) -> NetworkSimulator:
    """
    Create a network simulator from a preset configuration.
    
    Presets:
        - 'none': No simulation (real hardware)
        - 'lan': Local area network (1ms latency)
        - 'wan': Wide area network (50ms latency, 5ms jitter)
        - 'lossy': Lossy network (ONLY packet loss, no base latency)
        - 'mobile': Mobile network (100ms latency, 20ms jitter, 0.5% loss)
    
    Args:
        preset: Name of the preset configuration
        packet_loss_rate: Override packet loss rate
        random_seed: Random seed for reproducibility
        
    Returns:
        Configured NetworkSimulator instance
    """
    # For 'lossy' mode, we want ONLY packet loss with NO base latency
    # Network overhead comes entirely from retry timeouts, not fixed delays
    if preset == 'lossy':
        simulator = NetworkSimulator(
            latency_ms=0.0, 
            packet_loss_rate=packet_loss_rate,
            random_seed=random_seed
        )
        return simulator
    
    presets = {
        'none': NetworkSimulator(random_seed=random_seed),
        'lan': NetworkSimulator(latency_ms=1.0, random_seed=random_seed),
        'wan': NetworkSimulator(latency_ms=50.0, jitter_ms=5.0, random_seed=random_seed),
        'mobile': NetworkSimulator(
            latency_ms=100.0, 
            jitter_ms=20.0, 
            packet_loss_rate=0.005,
            random_seed=random_seed
        )
    }
    
    if preset not in presets:
        raise ValueError(
            f"Unknown network preset: {preset}. "
            f"Available: ['none', 'lan', 'wan', 'lossy', 'mobile']"
        )
    
    simulator = presets[preset]
    # Allow override of packet loss rate for other presets too
    if packet_loss_rate >= 0:
        simulator.condition.packet_loss_rate = packet_loss_rate
    
    return simulator
