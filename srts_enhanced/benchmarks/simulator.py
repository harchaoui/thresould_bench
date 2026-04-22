"""
Network Simulator for Benchmark Testing
Simulates network conditions: latency, packet loss, and bandwidth limits.
"""

import time
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass


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
        simulator = NetworkSimulator(latency_ms=50.0, packet_loss_rate=0.01)
        
        # Simulate sending a message - returns status dict instead of raising
        result = simulator.send_message(data_size_bytes)
        if not result['success']:
            # Handle packet loss gracefully
        
        # Simulate receiving a message
        simulator.receive_message(data_size_bytes)
        
        # Simulate round-trip
        with simulator.round_trip():
            # perform network operation
            pass
    """
    
    def __init__(
        self,
        latency_ms: float = 0.0,
        jitter_ms: float = 0.0,
        packet_loss_rate: float = 0.0,
        bandwidth_mbps: float = 0.0
    ):
        self.condition = NetworkCondition(
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            packet_loss_rate=packet_loss_rate,
            bandwidth_mbps=bandwidth_mbps
        )
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_retried = 0
        self.total_bytes_sent = 0
        self.total_latency_ms = 0.0
        
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
    
    def send_with_retry(self, data_size_bytes: int = 0, max_retries: int = 3) -> Dict[str, Any]:
        """
        Send a message with automatic retry on packet loss.
        
        Args:
            data_size_bytes: Size of data being sent
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict with keys:
                - success (bool): Whether the packet was eventually delivered
                - delay (float): Total delay including retries
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
            
            # Packet lost, apply exponential backoff before retry
            if attempt < max_retries:
                retries += 1
                self.packets_retried += 1
                backoff = 0.01 * (2 ** attempt)  # Exponential backoff: 10ms, 20ms, 40ms...
                time.sleep(backoff)
        
        # All retries exhausted
        return {
            "success": False,
            "delay": total_delay,
            "retries": retries,
            "lost": True
        }
    
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
            )
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_retried = 0
        self.total_bytes_sent = 0
        self.total_latency_ms = 0.0


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


def create_simulator_from_preset(preset: str) -> NetworkSimulator:
    """
    Create a network simulator from a preset configuration.
    
    Presets:
        - 'none': No simulation (real hardware)
        - 'lan': Local area network (1ms latency)
        - 'wan': Wide area network (50ms latency, 5ms jitter)
        - 'lossy': Lossy network (10ms latency, 1% packet loss)
        - 'mobile': Mobile network (100ms latency, 20ms jitter, 0.5% loss)
    """
    presets = {
        'none': NetworkSimulator(),
        'lan': NetworkSimulator(latency_ms=1.0),
        'wan': NetworkSimulator(latency_ms=50.0, jitter_ms=5.0),
        'lossy': NetworkSimulator(latency_ms=10.0, packet_loss_rate=0.01),
        'mobile': NetworkSimulator(latency_ms=100.0, jitter_ms=20.0, packet_loss_rate=0.005)
    }
    
    if preset not in presets:
        raise ValueError(f"Unknown network preset: {preset}. Available: {list(presets.keys())}")
    
    return presets[preset]
