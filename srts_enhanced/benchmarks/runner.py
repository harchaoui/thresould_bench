"""
Main Benchmark Runner for SRTS Enhanced
Executes benchmarks across all schemes, curves, and configurations.
"""

import time
import os
from typing import Dict, Any, List
from datetime import datetime

from .config import (
    BenchmarkConfig, SchemeType, CurveType, DKGType, 
    NetworkMode, NetworkConfig, DEFAULT_CONFIG
)
from .metrics import BenchmarkMetrics, Timer, get_memory_usage_mb
from .simulator import NetworkSimulator, create_simulator_from_preset


class BenchmarkRunner:
    """
    Main benchmark execution engine.
    
    Runs comprehensive benchmarks across:
    - Multiple signature schemes (SRTS, FROST, TBLS, MuSig2)
    - Multiple curves (secp256k1, BLS12-381, ristretto255)
    - Various scale parameters (n, t)
    - Different DKG methods
    - Network conditions (LAN, WAN, lossy)
    """
    
    def __init__(self, config: BenchmarkConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.results: List[Dict[str, Any]] = []
        
    def run_all(self):
        """Run complete benchmark suite."""
        print("=" * 80)
        print("SRTS Enhanced - Comprehensive Benchmark Suite")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"Schemes: {[s.value for s in self.config.schemes]}")
        print(f"Curves: {[c.value for c in self.config.curves]}")
        print(f"Scale params: {self.config.scale_params}")
        print(f"Iterations: {self.config.iterations}")
        print(f"Network mode: {self.config.network_mode.value}")
        print("=" * 80)
        
        # Create network simulator
        network_sim = create_simulator_from_preset(self.config.network_mode.value)
        
        total_start = time.time()
        
        for scheme_type in self.config.schemes:
            for curve_type in self.config.curves:
                # Skip TBLS with non-BLS curves
                if scheme_type == SchemeType.TBLS and curve_type != CurveType.BLS12_381:
                    print(f"\n⊘ Skipping {scheme_type.value} with {curve_type.value} (incompatible)")
                    continue
                
                # Skip threshold schemes with ristretto255 (not yet fully supported)
                if scheme_type in [SchemeType.SRTS, SchemeType.FROST] and curve_type == CurveType.RISTRETTO255:
                    print(f"\n⊘ Skipping {scheme_type.value} with {curve_type.value} (limited support)")
                    continue
                
                print(f"\n{'='*60}")
                print(f"Benchmarking: {scheme_type.value.upper()} + {curve_type.value}")
                print(f"{'='*60}")
                
                for n, t in self.config.scale_params:
                    # For MuSig2, t must equal n (n-of-n multisig)
                    if scheme_type == SchemeType.MUSIG2:
                        t = n
                    
                    # Skip invalid threshold configurations
                    if t > n:
                        continue
                    
                    result = self._run_benchmark_config(
                        scheme_type=scheme_type,
                        curve_type=curve_type,
                        n=n,
                        t=t,
                        network_sim=network_sim
                    )
                    
                    if result:
                        self.results.append(result)
                        
                        # Print summary
                        print(f"\n✓ Completed: n={n}, t={t}")
                        if 'keygen_total_ms' in result['timing']:
                            print(f"  KeyGen: {result['timing']['keygen_total_ms']:.2f} ms")
                        if 'sign_total_ms' in result['timing']:
                            print(f"  Sign:   {result['timing']['sign_total_ms']:.2f} ms")
                        if 'verify_ms' in result['timing']:
                            print(f"  Verify: {result['timing']['verify_ms']:.2f} ms")
        
        total_duration = time.time() - total_start
        
        print("\n" + "=" * 80)
        print(f"Benchmark completed in {total_duration:.2f} seconds")
        print(f"Total configurations tested: {len(self.results)}")
        print("=" * 80)
        
        return self.results
    
    def _run_benchmark_config(
        self,
        scheme_type: SchemeType,
        curve_type: CurveType,
        n: int,
        t: int,
        network_sim: NetworkSimulator
    ) -> Dict[str, Any]:
        """Run benchmark for a specific configuration."""
        
        metrics = BenchmarkMetrics()
        metrics.set_metadata("scheme", scheme_type.value)
        metrics.set_metadata("curve", curve_type.value)
        metrics.set_metadata("n", n)
        metrics.set_metadata("t", t)
        metrics.set_metadata("timestamp", datetime.now().isoformat())
        metrics.set_metadata("iterations", self.config.iterations)
        
        try:
            # Import scheme dynamically
            if scheme_type == SchemeType.SRTS:
                from ..schemes import SRTS as SchemeClass
            elif scheme_type == SchemeType.FROST:
                from ..schemes import FROST as SchemeClass
            elif scheme_type == SchemeType.TBLS:
                from ..schemes import TBLS as SchemeClass
            elif scheme_type == SchemeType.MUSIG2:
                from ..schemes import MuSig2 as SchemeClass
            else:
                raise ValueError(f"Unknown scheme: {scheme_type}")
            
            # Initialize scheme
            curve_name = curve_type.value
            scheme = SchemeClass(curve_name=curve_name)
            
            # Warmup iterations
            if self.config.warmup_iterations > 0:
                print(f"  Warming up ({self.config.warmup_iterations} iterations)...")
                for _ in range(self.config.warmup_iterations):
                    self._run_single_iteration(scheme, n, t, metrics, network_sim, is_warmup=True)
            
            # Actual benchmark iterations
            print(f"  Running benchmarks ({self.config.iterations} iterations)...")
            for i in range(self.config.iterations):
                if self.config.verbose and i % 5 == 0:
                    print(f"    Iteration {i+1}/{self.config.iterations}")
                self._run_single_iteration(scheme, n, t, metrics, network_sim, is_warmup=False)
            
            # Compile results
            result = {
                "scheme": scheme_type.value,
                "curve": curve_type.value,
                "n": n,
                "t": t,
                "timing": {},
                "memory": {},
                "communication": {},
                "signatures": {}
            }
            
            # Add timing metrics
            for op_name, timing in metrics.timing_metrics.items():
                result["timing"][f"{op_name}_mean_ms"] = timing.mean
                result["timing"][f"{op_name}_median_ms"] = timing.median
                result["timing"][f"{op_name}_std_ms"] = timing.std_dev
                result["timing"][f"{op_name}_p95_ms"] = timing.p95
            
            # Add memory metrics if enabled
            if self.config.enable_memory_profiling:
                for op_name, mem in metrics.memory_metrics.items():
                    result["memory"][f"{op_name}_mean_mb"] = mem.mean
            
            # Add signature metrics
            for op_name, sig in metrics.signature_metrics.items():
                result["signatures"][f"{op_name}_avg_size_bytes"] = sig.avg_signature_size
                result["signatures"][f"{op_name}_avg_verify_ms"] = sig.avg_verification_time
            
            return result
            
        except Exception as e:
            print(f"  ✗ Error running benchmark: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _run_single_iteration(
        self,
        scheme,
        n: int,
        t: int,
        metrics: BenchmarkMetrics,
        network_sim: NetworkSimulator,
        is_warmup: bool = False
    ):
        """Run a single benchmark iteration."""
        
        message = b"Benchmark test message for performance evaluation"
        participants = list(range(1, n + 1))
        
        # Phase 1: Key Generation
        with Timer(metrics, "keygen"):
            # MuSig2 is n-of-n multi-sig (no threshold), uses keygen_multi
            if hasattr(scheme, 'scheme_name') and scheme.scheme_name == "MuSig2":
                keys = scheme.keygen_multi(n)
            else:
                keys = scheme.keygen(n, t)
        
        # Phase 2: Presignature Generation (for SRTS/FROST)
        presign_data = None
        is_musig2 = hasattr(scheme, 'scheme_name') and scheme.scheme_name == "MuSig2"
        
        if hasattr(scheme, 'presign') and not is_musig2:
            with Timer(metrics, "presign"):
                presign_data = scheme.presign(message, participants)
                presign_data["public_key"] = keys["public_key"]
                
                # Simulate network communication
                if not is_warmup:
                    network_sim.send_message(1024)  # Estimate presign data size
        
        # Phase 3: Partial Signing
        partial_sigs = []
        
        if is_musig2:
            # MuSig2: All n participants must sign
            sign_participants = participants
            # For MuSig2, use the aggregated_key_obj which has participant_keys attribute
            agg_key = keys.get("aggregated_key_obj") or keys.get("aggregated_key") or keys.get("public_key")
            
            # Generate nonces for all participants
            nonces = []
            with Timer(metrics, "nonce_gen"):
                for pid in sign_participants:
                    nonce = scheme.generate_nonces(pid)
                    nonces.append(nonce)
            
            # Presign phase - compute shared R and challenge
            presign_data_list = []
            with Timer(metrics, "presign"):
                for i in range(len(sign_participants)):
                    presign_data = scheme.presign(
                        message=message,
                        nonces=nonces,
                        agg_key=agg_key,
                        participant_index=i
                    )
                    presign_data_list.append(presign_data)
            
            # Sign phase
            with Timer(metrics, "partial_sign"):
                for i, pid in enumerate(sign_participants):
                    sk = keys["secret_keys"][i]
                    nonce = nonces[i]
                    psig = scheme.sign(
                        message=message,
                        key_pair=sk,
                        nonce=nonce,
                        presign_data=presign_data_list[i],
                        agg_key=agg_key
                    )
                    partial_sigs.append(psig)
                    
                    # Simulate network communication
                    if not is_warmup:
                        network_sim.send_message(256)
        else:
            # Threshold schemes: Use t participants
            sign_participants = participants[:t]
            
            with Timer(metrics, "partial_sign"):
                for i, pid in enumerate(sign_participants):
                    share = keys["shares"][i][1]
                    
                    if hasattr(scheme, 'partial_sign'):
                        psig = scheme.partial_sign(message, share, pid)
                    else:
                        # SRTS
                        if presign_data:
                            psig = scheme.sign(message, share, pid, presign_data)
                        else:
                            raise ValueError("Missing presign_data for SRTS signing")
                    
                    partial_sigs.append(psig)
                    
                    # Simulate network communication
                    if not is_warmup:
                        network_sim.send_message(256)
        
        # Phase 4: Signature Aggregation
        with Timer(metrics, "aggregate"):
            if is_musig2:
                sig = scheme.aggregate(partial_sigs, agg_nonces, agg_key, message)
            elif hasattr(scheme, 'aggregate'):
                if presign_data:
                    sig = scheme.aggregate(partial_sigs, presign_data)
                else:
                    sig = scheme.aggregate(partial_sigs, message, keys["public_key"])
            else:
                # Fallback
                sig = partial_sigs[0]
        
        # Phase 5: Verification
        with Timer(metrics, "verify"):
            if hasattr(scheme, 'verify'):
                pk_to_verify = keys.get("aggregated_key") or keys.get("public_key")
                valid = scheme.verify(message, sig, pk_to_verify)
                if not valid:
                    raise ValueError("Signature verification failed!")
        
        # Record signature size
        if isinstance(sig, dict) and 'signature' in sig:
            sig_bytes = sig.get('signature', b'')
        elif isinstance(sig, bytes):
            sig_bytes = sig
        else:
            sig_bytes = str(sig).encode()
        
        metrics.get_signature("final_sig").add_signature(len(sig_bytes))
        
        # Record memory usage if enabled
        if self.config.enable_memory_profiling and not is_warmup:
            mem_mb = get_memory_usage_mb()
            metrics.get_memory("keygen").add(mem_mb)
