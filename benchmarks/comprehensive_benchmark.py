#!/usr/bin/env python3
"""
Comprehensive Benchmark Suite for Threshold Signature Schemes
==============================================================

This script runs a complete benchmark analysis covering:
- All signature schemes (SRTS, FROST, TBLS, MuSig2)
- DKG comparison (Pedersen vs Feldman)
- Multiple curves (secp256k1, BLS12-381, ristretto255)
- Network conditions (0%, 1%, 2%, 5% packet loss)
- Scale parameters (n=3 to n=100)
- Five distinct phases with specific measurement goals

Usage:
    python -m benchmarks.comprehensive_benchmark
    python -m benchmarks.comprehensive_benchmark --phase 1 --output results/
    python -m benchmarks.comprehensive_benchmark --dry-run
    python -m benchmarks.comprehensive_benchmark --resume
"""

import argparse
import json
import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.config import (
    BenchmarkConfig, SchemeType, CurveType, DKGType,
    validate_combination, valid_curves_for, valid_dkg_for,
    is_preferred, COMPATIBILITY
)
from benchmarks.metrics import flatten_result, create_empty_result, get_memory_usage_mb
from benchmarks.network_simulator import NetworkSimulator, RETRY_TIMEOUT_MS
from benchmarks.reporter import BenchmarkReporter


# =============================================================================
# PHASE DEFINITIONS
# =============================================================================

# Swarm sizes: n = 3, 5, 10, 20, 50, 100
# t = ceil(2n/3) for threshold schemes, t = n for MuSig2
SCALE_PARAMS = [(3, 2), (5, 3), (10, 6), (20, 11), (50, 26), (100, 51)]

# Packet loss rates
LOSS_RATES = [0.0, 0.01, 0.02, 0.05]  # 0%, 1%, 2%, 5%

# Iterations per combination
ITERATIONS = 30
WARMUP_ITERATIONS = 5

# Random seed for reproducibility
RANDOM_SEED = 42


class ComprehensiveBenchmark:
    """
    Comprehensive benchmark execution engine.
    
    Implements the full validation plan across all dimensions with:
    - Proper interleaving at each (n, loss) point
    - Immediate saving of results after each combination
    - Skip logging for invalid combinations
    - Resume capability from existing output files
    """
    
    def __init__(self, output_dir: str = "benchmark_results", 
                 include_suboptimal: bool = False,
                 resume: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.include_suboptimal = include_suboptimal
        self.resume = resume
        
        self.all_results: List[Dict[str, Any]] = []
        self.skip_log: List[Dict[str, Any]] = []
        self.planned_combinations: List[Dict[str, Any]] = []
        
        self.metadata = {
            "start_time": datetime.now().isoformat(),
            "version": "2.0",
            "phases_completed": [],
            "include_suboptimal": include_suboptimal,
            "resume": resume
        }
        
        # Track completed combinations for resume
        self.completed_keys: Set[Tuple] = set()
        if resume:
            self._scan_existing_results()
    
    def _scan_existing_results(self):
        """Scan existing JSON files in output_dir to find completed combinations."""
        print(f"\nScanning for existing results in {self.output_dir}...")
        
        for json_file in self.output_dir.glob("*.json"):
            if json_file.name.startswith("skipped_"):
                continue
                
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    
                # Handle both single result and list of results
                results = data if isinstance(data, list) else [data]
                
                for result in results:
                    key = (
                        result.get("phase"),
                        result.get("scheme"),
                        result.get("curve"),
                        result.get("dkg"),
                        result.get("n"),
                        result.get("loss_rate")
                    )
                    if all(k is not None for k in key):
                        self.completed_keys.add(key)
                        self.all_results.append(result)
                        
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Warning: Could not parse {json_file}: {e}")
        
        print(f"  Found {len(self.completed_keys)} completed combinations")
    
    def _is_completed(self, phase: str, scheme: str, curve: str, 
                      dkg: str, n: int, loss_rate: float) -> bool:
        """Check if a combination has already been completed."""
        key = (phase, scheme, curve, dkg, n, loss_rate)
        return key in self.completed_keys
    
    def _mark_completed(self, phase: str, scheme: str, curve: str, 
                        dkg: str, n: int, loss_rate: float):
        """Mark a combination as completed."""
        key = (phase, scheme, curve, dkg, n, loss_rate)
        self.completed_keys.add(key)
    
    def _save_result(self, result: Dict[str, Any]):
        """Save a single result immediately to JSON file."""
        scheme = result["scheme"]
        curve = result["curve"]
        dkg = result["dkg"]
        n = result["n"]
        loss_rate = result["loss_rate"]
        phase = result["phase"]
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{phase}_{scheme}_{curve}_{dkg}_n{n}_loss{int(loss_rate*100)}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    
    def _log_skip(self, phase: str, scheme: str, curve: str, dkg: str,
                  n: int, loss_rate: float, reason: str):
        """Log a skipped combination."""
        skip_entry = {
            "phase": phase,
            "scheme": scheme,
            "curve": curve,
            "dkg": dkg,
            "n": n,
            "loss_rate": loss_rate,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.skip_log.append(skip_entry)
    
    def _save_skip_log(self):
        """Save skip log to JSON file."""
        filepath = self.output_dir / f"skipped_combinations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.skip_log, f, indent=2, default=str)
        
        print(f"  Saved skip log: {filepath}")
    
    def _get_curves_for_scheme(self, scheme: str) -> List[str]:
        """Get valid curves for a scheme, optionally including suboptimal."""
        curves = valid_curves_for(scheme)
        if not self.include_suboptimal:
            # Filter out suboptimal curves
            filtered = []
            for curve in curves:
                for dkg in [DKGType.PEDERSEN.value, DKGType.FELDMAN.value, DKGType.NOT_APPLICABLE.value]:
                    status, _ = validate_combination(scheme, curve, dkg)
                    if status == "valid":
                        filtered.append(curve)
                        break
            return filtered
        return curves
    
    def _run_single_combination(
        self, phase: str, scheme: str, curve: str, dkg: str,
        n: int, t: int, loss_rate: float, run_keygen: bool = True,
        run_signing: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Run a single benchmark combination.
        
        Args:
            phase: Phase name
            scheme: Scheme name
            curve: Curve name
            dkg: DKG type
            n: Number of participants
            t: Threshold
            loss_rate: Packet loss rate
            run_keygen: Whether to run keygen
            run_signing: Whether to run signing
            
        Returns:
            Result dict or None if failed
        """
        # Validate combination
        status, reason = validate_combination(scheme, curve, dkg)
        
        if status == "invalid":
            self._log_skip(phase, scheme, curve, dkg, n, loss_rate, reason)
            return None
        
        # Check if already completed (for resume)
        if self._is_completed(phase, scheme, curve, dkg, n, loss_rate):
            print(f"    Skipping (already completed): {scheme}/{curve}/{dkg}/n={n}/loss={loss_rate}")
            return None
        
        # Set random seed for reproducibility
        random.seed(RANDOM_SEED)
        
        print(f"    Running: {scheme}/{curve}/{dkg}/n={n}/t={t}/loss={loss_rate*100:.0f}%")
        
        # Create network simulator
        network_sim = NetworkSimulator(
            packet_loss_rate=loss_rate,
            random_seed=RANDOM_SEED
        )
        
        # Import and initialize scheme
        try:
            if scheme == "srts":
                from srts_enhanced.schemes import SRTS as SchemeClass
            elif scheme == "frost":
                from srts_enhanced.schemes import FROST as SchemeClass
            elif scheme == "tbls":
                from srts_enhanced.schemes import TBLS as SchemeClass
            elif scheme == "musig2":
                from srts_enhanced.schemes import MuSig2 as SchemeClass
            else:
                raise ValueError(f"Unknown scheme: {scheme}")
            
            scheme_instance = SchemeClass(curve_name=curve)
            
        except Exception as e:
            print(f"    Error initializing scheme: {e}")
            return None
        
        # Collect metrics
        keygen_times = []
        sign_times = []
        verify_times = []
        network_overheads = []
        retries_list = []
        messages_list = []
        sig_sizes = []
        memory_usages = []
        successful_iters = 0
        
        # Warmup iterations
        for _ in range(WARMUP_ITERATIONS):
            self._run_iteration(
                scheme_instance, n, t, network_sim,
                run_keygen, run_signing,
                collect_metrics=False
            )
        
        # Actual iterations
        for i in range(ITERATIONS):
            result = self._run_iteration(
                scheme_instance, n, t, network_sim,
                run_keygen, run_signing,
                collect_metrics=True
            )
            
            if result:
                if run_keygen and "keygen_ms" in result:
                    keygen_times.append(result["keygen_ms"])
                if run_signing and "sign_ms" in result:
                    sign_times.append(result["sign_ms"])
                if run_signing and "verify_ms" in result:
                    verify_times.append(result["verify_ms"])
                if "network_overhead_ms" in result:
                    network_overheads.append(result["network_overhead_ms"])
                if "retries" in result:
                    retries_list.append(result["retries"])
                if "messages" in result:
                    messages_list.append(result["messages"])
                if "sig_size" in result:
                    sig_sizes.append(result["sig_size"])
                if "memory_mb" in result:
                    memory_usages.append(result["memory_mb"])
                
                if result.get("success", False):
                    successful_iters += 1
        
        # Calculate statistics
        import statistics
        
        def calc_stats(values):
            if not values:
                return None, None, None, None
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0.0
            median_val = statistics.median(values)
            sorted_vals = sorted(values)
            p95_idx = int(len(sorted_vals) * 0.95)
            p95_val = sorted_vals[min(p95_idx, len(sorted_vals) - 1)]
            return mean_val, std_val, median_val, p95_val
        
        keygen_mean, keygen_std, keygen_median, keygen_p95 = calc_stats(keygen_times)
        sign_mean, sign_std, sign_median, sign_p95 = calc_stats(sign_times)
        verify_mean, verify_std, verify_median, verify_p95 = calc_stats(verify_times)
        net_mean, _, _, _ = calc_stats(network_overheads)
        retries_mean, _, _, _ = calc_stats(retries_list)
        messages_mean, _, _, _ = calc_stats(messages_list)
        sig_size_mean, _, _, _ = calc_stats(sig_sizes)
        memory_mean, _, _, _ = calc_stats(memory_usages)
        
        # Build result using flatten_result helper
        preferred = is_preferred(scheme, curve, dkg)
        musig2_nofn = (scheme == "musig2")
        tbls_noninteractive = (scheme == "tbls")
        
        # Create runner_output structure for flatten_result
        runner_output = {
            "timing": {},
            "stress_metrics": {},
            "signatures": {},
            "memory": {}
        }
        
        if run_keygen:
            if keygen_mean is not None:
                runner_output["timing"]["keygen_mean_ms"] = keygen_mean
                runner_output["timing"]["keygen_std_ms"] = keygen_std
                runner_output["timing"]["keygen_median_ms"] = keygen_median
                runner_output["timing"]["keygen_p95_ms"] = keygen_p95
        
        if run_signing:
            if sign_mean is not None:
                runner_output["timing"]["partial_sign_mean_ms"] = sign_mean
                runner_output["timing"]["partial_sign_std_ms"] = sign_std
                runner_output["timing"]["partial_sign_median_ms"] = sign_median
                runner_output["timing"]["partial_sign_p95_ms"] = sign_p95
            
            if verify_mean is not None:
                runner_output["timing"]["verify_mean_ms"] = verify_mean
                runner_output["timing"]["verify_std_ms"] = verify_std
                runner_output["timing"]["verify_median_ms"] = verify_median
                runner_output["timing"]["verify_p95_ms"] = verify_p95
            
            if net_mean is not None:
                runner_output["stress_metrics"]["avg_network_overhead_ms"] = net_mean
            if retries_mean is not None:
                runner_output["stress_metrics"]["avg_retries_per_iter"] = retries_mean
            if messages_mean is not None:
                runner_output["stress_metrics"]["avg_messages_per_iter"] = messages_mean
            
            runner_output["stress_metrics"]["completion_rate"] = successful_iters / ITERATIONS
            runner_output["stress_metrics"]["successful_iterations"] = successful_iters
            runner_output["stress_metrics"]["total_iterations"] = ITERATIONS
            
            if sig_size_mean is not None:
                runner_output["signatures"]["final_sig_avg_size_bytes"] = sig_size_mean
            
            if memory_mean is not None:
                runner_output["memory"]["keygen_mean_mb"] = memory_mean
        
        result = flatten_result(
            runner_output=runner_output,
            phase=phase,
            scheme=scheme,
            curve=curve,
            dkg=dkg,
            n=n,
            t=t,
            loss_rate=loss_rate,
            compatibility=status,
            preferred=preferred,
            musig2_nofn=musig2_nofn,
            tbls_noninteractive=tbls_noninteractive
        )
        
        # Save immediately
        self._save_result(result)
        self.all_results.append(result)
        self._mark_completed(phase, scheme, curve, dkg, n, loss_rate)
        
        return result
    
    def _run_iteration(
        self, scheme, n: int, t: int, network_sim: NetworkSimulator,
        run_keygen: bool, run_signing: bool,
        collect_metrics: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Run a single iteration of the benchmark.
        
        Returns dict with timing metrics if collect_metrics=True.
        """
        import time
        
        message = b"Benchmark test message for performance evaluation"
        participants = list(range(1, n + 1))
        
        result = {"success": True}
        
        try:
            # Key Generation
            if run_keygen:
                keygen_start = time.perf_counter()
                
                # MuSig2 uses keygen_multi (n-of-n)
                if hasattr(scheme, 'scheme_name') and scheme.scheme_name == "MuSig2":
                    keys = scheme.keygen_multi(n)
                else:
                    keys = scheme.keygen(n, t)
                
                keygen_end = time.perf_counter()
                
                if collect_metrics:
                    result["keygen_ms"] = (keygen_end - keygen_start) * 1000
                    
                    # Memory usage
                    try:
                        result["memory_mb"] = get_memory_usage_mb()
                    except:
                        pass
            
            # Signing (if applicable)
            if run_signing:
                is_musig2 = hasattr(scheme, 'scheme_name') and scheme.scheme_name == "MuSig2"
                
                # Presign phase for SRTS/FROST
                presign_data = None
                if hasattr(scheme, 'presign') and not is_musig2:
                    presign_start = time.perf_counter()
                    presign_data = scheme.presign(message, participants)
                    presign_data["public_key"] = keys.get("public_key")
                    presign_end = time.perf_counter()
                    
                    if collect_metrics:
                        result["presign_ms"] = (presign_end - presign_start) * 1000
                    
                    # Network simulation
                    net_result = network_sim.send_with_retry(1024, max_retries=3)
                    if collect_metrics:
                        result["network_overhead_ms"] = net_result["delay"]
                        result["retries"] = net_result["retries"]
                        result["messages"] = 1 + net_result["retries"]
                
                # Partial signing
                partial_sigs = []
                sign_participants = participants if is_musig2 else participants[:t]
                
                partial_sign_start = time.perf_counter()
                
                if is_musig2:
                    # MuSig2-specific signing
                    agg_key = keys.get("aggregated_key_obj") or keys.get("aggregated_key") or keys.get("public_key")
                    
                    # Generate nonces
                    nonces = []
                    for pid in sign_participants:
                        nonce = scheme.generate_nonces(pid)
                        nonces.append(nonce)
                    
                    # Presign for each participant
                    presign_data_list = []
                    for i in range(len(sign_participants)):
                        pd = scheme.presign(
                            message=message,
                            nonces=nonces,
                            agg_key=agg_key,
                            participant_index=i
                        )
                        presign_data_list.append(pd)
                    
                    # Sign
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
                        
                        # Network simulation
                        if collect_metrics:
                            net_result = network_sim.send_with_retry(256, max_retries=3)
                            result["network_overhead_ms"] = result.get("network_overhead_ms", 0) + net_result["delay"]
                            result["retries"] = result.get("retries", 0) + net_result["retries"]
                            result["messages"] = result.get("messages", 0) + 1 + net_result["retries"]
                else:
                    # Threshold schemes
                    for i, pid in enumerate(sign_participants):
                        share = keys["shares"][i][1]
                        
                        if hasattr(scheme, 'partial_sign'):
                            psig = scheme.partial_sign(message, share, pid)
                        else:
                            psig = scheme.sign(message, share, pid, presign_data)
                        
                        partial_sigs.append(psig)
                        
                        # Network simulation
                        if collect_metrics:
                            net_result = network_sim.send_with_retry(256, max_retries=3)
                            result["network_overhead_ms"] = result.get("network_overhead_ms", 0) + net_result["delay"]
                            result["retries"] = result.get("retries", 0) + net_result["retries"]
                            result["messages"] = result.get("messages", 0) + 1 + net_result["retries"]
                
                partial_sign_end = time.perf_counter()
                
                if collect_metrics:
                    result["sign_ms"] = (partial_sign_end - partial_sign_start) * 1000
                
                # Aggregate
                aggregate_start = time.perf_counter()
                
                if is_musig2:
                    sig_result = scheme.aggregate(partial_sigs, presign_data_list[0])
                    if isinstance(sig_result, dict):
                        sig = sig_result.get('aggregated_serialized', sig_result.get('serialized'))
                    else:
                        sig = sig_result
                elif hasattr(scheme, 'aggregate'):
                    if presign_data:
                        sig = scheme.aggregate(partial_sigs, presign_data)
                    else:
                        sig = scheme.aggregate(partial_sigs, message, keys["public_key"])
                else:
                    sig = partial_sigs[0]
                
                aggregate_end = time.perf_counter()
                
                # Verify
                verify_start = time.perf_counter()
                
                if hasattr(scheme, 'verify'):
                    if is_musig2:
                        pk_to_verify = keys.get("aggregated_key_obj") or keys.get("aggregated_key")
                    else:
                        pk_to_verify = keys.get("aggregated_key") or keys.get("public_key")
                    
                    valid = scheme.verify(message, sig, pk_to_verify)
                    if not valid:
                        result["success"] = False
                
                verify_end = time.perf_counter()
                
                if collect_metrics:
                    result["verify_ms"] = (verify_end - verify_start) * 1000
                    
                    # Signature size
                    if isinstance(sig, dict) and 'signature' in sig:
                        sig_bytes = sig.get('signature', b'')
                    elif isinstance(sig, bytes):
                        sig_bytes = sig
                    else:
                        sig_bytes = str(sig).encode()
                    
                    result["sig_size"] = len(sig_bytes)
            
            return result if collect_metrics else None
            
        except Exception as e:
            if collect_metrics:
                result["success"] = False
                result["error"] = str(e)
            return result if collect_metrics else None
    
    def generate_planned_combinations(self) -> List[Dict[str, Any]]:
        """Generate all planned combinations for all phases."""
        planned = []
        
        # Phase 1: DKG setup cost (keygen only, loss=0% only)
        phase1_schemes = ["srts", "frost", "tbls", "musig2"]
        phase1_dkg_map = {
            "srts": ["feldman", "pedersen"],
            "frost": ["feldman", "pedersen"],
            "tbls": ["feldman", "pedersen"],
            "musig2": ["not_applicable"]
        }
        
        for scheme in phase1_schemes:
            for curve in self._get_curves_for_scheme(scheme):
                for dkg in phase1_dkg_map.get(scheme, []):
                    status, _ = validate_combination(scheme, curve, dkg)
                    if status == "invalid":
                        continue
                    
                    for n, t in SCALE_PARAMS:
                        if scheme == "musig2":
                            t = n
                        
                        planned.append({
                            "phase": "phase1_dkg",
                            "scheme": scheme,
                            "curve": curve,
                            "dkg": dkg,
                            "n": n,
                            "t": t,
                            "loss_rate": 0.0
                        })
        
        # Phase 2: Signing + verification, no network stress (loss=0%)
        phase2_schemes = ["srts", "frost", "tbls", "musig2"]
        
        for scheme in phase2_schemes:
            for curve in self._get_curves_for_scheme(scheme):
                # Use pedersen for threshold schemes, not_applicable for musig2
                dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                
                # Special case: tbls with pedersen is suboptimal
                if scheme == "tbls" and dkg == "pedersen" and not self.include_suboptimal:
                    continue
                
                status, _ = validate_combination(scheme, curve, dkg)
                if status == "invalid":
                    continue
                
                for n, t in SCALE_PARAMS:
                    if scheme == "musig2":
                        t = n
                    
                    planned.append({
                        "phase": "phase2_signing",
                        "scheme": scheme,
                        "curve": curve,
                        "dkg": dkg,
                        "n": n,
                        "t": t,
                        "loss_rate": 0.0
                    })
        
        # Phase 3: Network stress (signing only, multiple loss rates)
        phase3_schemes = ["srts", "frost", "tbls", "musig2"]
        phase3_loss_rates = [0.01, 0.02, 0.05]  # 1%, 2%, 5%
        
        for scheme in phase3_schemes:
            for curve in self._get_curves_for_scheme(scheme):
                # Exclude suboptimal curves from network stress unless flag is set
                if not self.include_suboptimal:
                    # Check if this is a suboptimal combination
                    dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                    status, _ = validate_combination(scheme, curve, dkg)
                    if status == "suboptimal":
                        continue
                
                dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                
                status, _ = validate_combination(scheme, curve, dkg)
                if status == "invalid":
                    continue
                
                for loss_rate in phase3_loss_rates:
                    for n, t in SCALE_PARAMS:
                        if scheme == "musig2":
                            t = n
                        
                        planned.append({
                            "phase": "phase3_network",
                            "scheme": scheme,
                            "curve": curve,
                            "dkg": dkg,
                            "n": n,
                            "t": t,
                            "loss_rate": loss_rate
                        })
        
        # Phase 4: DKG deep dive (keygen cost vs loss rate)
        phase4_schemes = ["srts", "frost", "tbls"]
        phase4_dkg_map = {
            "srts": ["feldman", "pedersen"],
            "frost": ["feldman", "pedersen"],
            "tbls": ["feldman", "pedersen"]
        }
        phase4_loss_rates = [0.01, 0.02, 0.05]
        
        for scheme in phase4_schemes:
            for curve in self._get_curves_for_scheme(scheme):
                for dkg in phase4_dkg_map.get(scheme, []):
                    status, _ = validate_combination(scheme, curve, dkg)
                    if status == "invalid":
                        continue
                    
                    # Skip suboptimal unless flag is set
                    if status == "suboptimal" and not self.include_suboptimal:
                        continue
                    
                    for loss_rate in phase4_loss_rates:
                        for n, t in SCALE_PARAMS:
                            planned.append({
                                "phase": "phase4_dkg_deepdive",
                                "scheme": scheme,
                                "curve": curve,
                                "dkg": dkg,
                                "n": n,
                                "t": t,
                                "loss_rate": loss_rate
                            })
        
        # Phase 5: Stress scale (large n, no loss)
        phase5_schemes = ["srts", "frost", "tbls", "musig2"]
        phase5_n_values = [(50, 26), (100, 51)]
        
        for scheme in phase5_schemes:
            for curve in self._get_curves_for_scheme(scheme):
                dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                
                status, _ = validate_combination(scheme, curve, dkg)
                if status == "invalid":
                    continue
                
                for n, t in phase5_n_values:
                    if scheme == "musig2":
                        t = n
                    
                    planned.append({
                        "phase": "phase5_stress_scale",
                        "scheme": scheme,
                        "curve": curve,
                        "dkg": dkg,
                        "n": n,
                        "t": t,
                        "loss_rate": 0.0
                    })
        
        self.planned_combinations = planned
        return planned
    
    def print_coverage_report(self):
        """Print coverage report at start of run."""
        reporter = BenchmarkReporter(self.all_results, str(self.output_dir))
        reporter.print_coverage_report(self.planned_combinations, self.skip_log)
    
    def run_phase(self, phase_num: int) -> List[Dict[str, Any]]:
        """Run a specific phase."""
        phase_methods = {
            1: self.run_phase1_dkg,
            2: self.run_phase2_signing,
            3: self.run_phase3_network,
            4: self.run_phase4_dkg_deepdive,
            5: self.run_phase5_stress_scale
        }
        
        if phase_num not in phase_methods:
            raise ValueError(f"Invalid phase number: {phase_num}")
        
        print(f"\n{'='*80}")
        print(f"PHASE {phase_num}")
        print(f"{'='*80}")
        
        results = phase_methods[phase_num]()
        self.metadata["phases_completed"].append(f"phase{phase_num}")
        
        return results
    
    def run_all_phases(self):
        """Run all phases in sequence."""
        for phase_num in range(1, 6):
            self.run_phase(phase_num)
    
    def run_phase1_dkg(self) -> List[Dict[str, Any]]:
        """
        PHASE 1 — DKG setup cost (keygen only, loss=0% only)
        
        DKG type is the variable here. Signing is not run in this phase.
        """
        print("\n--- Phase 1: DKG Setup Cost ---")
        results = []
        
        schemes = ["srts", "frost", "tbls", "musig2"]
        dkg_map = {
            "srts": ["feldman", "pedersen"],
            "frost": ["feldman", "pedersen"],
            "tbls": ["feldman", "pedersen"],
            "musig2": ["not_applicable"]
        }
        
        # Interleaved execution: for each (n, loss), run all schemes
        for n, t_base in SCALE_PARAMS:
            loss_rate = 0.0
            
            for scheme in schemes:
                for dkg in dkg_map.get(scheme, []):
                    for curve in self._get_curves_for_scheme(scheme):
                        # Adjust t for MuSig2
                        t = n if scheme == "musig2" else t_base
                        
                        result = self._run_single_combination(
                            phase="phase1_dkg",
                            scheme=scheme,
                            curve=curve,
                            dkg=dkg,
                            n=n,
                            t=t,
                            loss_rate=loss_rate,
                            run_keygen=True,
                            run_signing=False
                        )
                        
                        if result:
                            results.append(result)
        
        return results
    
    def run_phase2_signing(self) -> List[Dict[str, Any]]:
        """
        PHASE 2 — Signing + verification, no network stress
        
        DKG type does NOT split here. Use pedersen for all threshold schemes.
        This phase isolates pure cryptographic signing cost.
        """
        print("\n--- Phase 2: Signing Performance (No Network Stress) ---")
        results = []
        
        schemes = ["srts", "frost", "tbls", "musig2"]
        
        # Interleaved execution
        for n, t_base in SCALE_PARAMS:
            loss_rate = 0.0
            
            for scheme in schemes:
                dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                t = n if scheme == "musig2" else t_base
                
                for curve in self._get_curves_for_scheme(scheme):
                    result = self._run_single_combination(
                        phase="phase2_signing",
                        scheme=scheme,
                        curve=curve,
                        dkg=dkg,
                        n=n,
                        t=t,
                        loss_rate=loss_rate,
                        run_keygen=True,
                        run_signing=True
                    )
                    
                    if result:
                        results.append(result)
        
        return results
    
    def run_phase3_network(self) -> List[Dict[str, Any]]:
        """
        PHASE 3 — Network stress (signing only, DKG not split)
        
        Use pedersen for all threshold schemes.
        MuSig2 MUST be included here.
        """
        print("\n--- Phase 3: Network Stress Testing ---")
        results = []
        
        schemes = ["srts", "frost", "tbls", "musig2"]
        loss_rates = [0.01, 0.02, 0.05]  # 1%, 2%, 5%
        
        # Interleaved execution
        for loss_rate in loss_rates:
            for n, t_base in SCALE_PARAMS:
                for scheme in schemes:
                    dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                    t = n if scheme == "musig2" else t_base
                    
                    for curve in self._get_curves_for_scheme(scheme):
                        # Exclude suboptimal from network stress unless flag set
                        if not self.include_suboptimal:
                            status, _ = validate_combination(scheme, curve, dkg)
                            if status == "suboptimal":
                                continue
                        
                        result = self._run_single_combination(
                            phase="phase3_network",
                            scheme=scheme,
                            curve=curve,
                            dkg=dkg,
                            n=n,
                            t=t,
                            loss_rate=loss_rate,
                            run_keygen=False,
                            run_signing=True
                        )
                        
                        if result:
                            results.append(result)
        
        return results
    
    def run_phase4_dkg_deepdive(self) -> List[Dict[str, Any]]:
        """
        PHASE 4 — DKG deep dive (keygen cost vs loss rate)
        
        This is the only phase where DKG type × loss rate cross is measured.
        Only keygen_ms and network_overhead_ms are recorded here.
        Signing is NOT run in this phase.
        """
        print("\n--- Phase 4: DKG Deep Dive (Keygen vs Loss Rate) ---")
        results = []
        
        schemes = ["srts", "frost", "tbls"]
        dkg_map = {
            "srts": ["feldman", "pedersen"],
            "frost": ["feldman", "pedersen"],
            "tbls": ["feldman", "pedersen"]
        }
        loss_rates = [0.01, 0.02, 0.05]
        
        # Interleaved execution
        for loss_rate in loss_rates:
            for n, t_base in SCALE_PARAMS:
                for scheme in schemes:
                    t = t_base
                    
                    for dkg in dkg_map.get(scheme, []):
                        for curve in self._get_curves_for_scheme(scheme):
                            # Skip suboptimal unless flag set
                            if not self.include_suboptimal:
                                status, _ = validate_combination(scheme, curve, dkg)
                                if status == "suboptimal":
                                    continue
                            
                            result = self._run_single_combination(
                                phase="phase4_dkg_deepdive",
                                scheme=scheme,
                                curve=curve,
                                dkg=dkg,
                                n=n,
                                t=t,
                                loss_rate=loss_rate,
                                run_keygen=True,
                                run_signing=False
                            )
                            
                            if result:
                                results.append(result)
        
        return results
    
    def run_phase5_stress_scale(self) -> List[Dict[str, Any]]:
        """
        PHASE 5 — Stress scale (large n, no loss)
        
        All four schemes, all valid curves, n=50 and n=100 only.
        """
        print("\n--- Phase 5: Stress Scale (Large n) ---")
        results = []
        
        schemes = ["srts", "frost", "tbls", "musig2"]
        scale_params = [(50, 26), (100, 51)]
        
        # Interleaved execution
        for n, t_base in scale_params:
            loss_rate = 0.0
            
            for scheme in schemes:
                dkg = "not_applicable" if scheme == "musig2" else "pedersen"
                t = n if scheme == "musig2" else t_base
                
                for curve in self._get_curves_for_scheme(scheme):
                    result = self._run_single_combination(
                        phase="phase5_stress_scale",
                        scheme=scheme,
                        curve=curve,
                        dkg=dkg,
                        n=n,
                        t=t,
                        loss_rate=loss_rate,
                        run_keygen=True,
                        run_signing=True
                    )
                    
                    if result:
                        results.append(result)
        
        return results
    
    def print_combination_table(self):
        """Print table showing complete planned combination space."""
        print("\n" + "=" * 100)
        print("PLANNED COMBINATION SPACE")
        print("=" * 100)
        print(f"{'Phase':<20} {'Scheme':<10} {'Curve':<15} {'DKG':<15} {'n values':<20} {'Loss rates':<15} {'Count':<8} {'Status':<10}")
        print("-" * 100)
        
        # Group by phase, scheme, curve, dkg
        from collections import defaultdict
        grouped = defaultdict(lambda: {"n_values": set(), "loss_rates": set(), "count": 0})
        
        for combo in self.planned_combinations:
            key = (combo["phase"], combo["scheme"], combo["curve"], combo["dkg"])
            grouped[key]["n_values"].add(combo["n"])
            grouped[key]["loss_rates"].add(combo["loss_rate"])
            grouped[key]["count"] += 1
        
        for (phase, scheme, curve, dkg), data in sorted(grouped.items()):
            n_vals = sorted(data["n_values"])
            loss_vals = sorted([f"{lr*100:.0f}%" for lr in data["loss_rates"]])
            
            status, _ = validate_combination(scheme, curve, dkg)
            status_str = "✓ valid" if status == "valid" else ("⚠ suboptimal" if status == "suboptimal" else "✗ invalid")
            
            print(f"{phase:<20} {scheme:<10} {curve:<15} {dkg:<15} {str(n_vals):<20} {str(loss_vals):<15} {data['count']:<8} {status_str:<10}")
        
        print("-" * 100)
        print(f"Total planned combinations: {len(self.planned_combinations)}")
        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Benchmark Suite for TSS")
    parser.add_argument("--output", "-o", type=str, default="benchmark_results",
                        help="Output directory for results")
    parser.add_argument("--phase", "-p", type=int, choices=[0, 1, 2, 3, 4, 5],
                        help="Run specific phase (0=all, 1-5=specific)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned combinations without executing")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing results in output directory")
    parser.add_argument("--include-suboptimal", action="store_true",
                        help="Include suboptimal combinations in benchmark")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode: fewer iterations for testing")
    
    args = parser.parse_args()
    
    # Create benchmark runner
    benchmark = ComprehensiveBenchmark(
        output_dir=args.output,
        include_suboptimal=args.include_suboptimal,
        resume=args.resume
    )
    
    # Generate planned combinations
    benchmark.generate_planned_combinations()
    
    # Dry run mode
    if args.dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No benchmarks will be executed")
        print("=" * 80)
        benchmark.print_combination_table()
        
        print("\n\nCombination counts by phase:")
        from collections import Counter
        phase_counts = Counter(c["phase"] for c in benchmark.planned_combinations)
        for phase, count in sorted(phase_counts.items()):
            print(f"  {phase}: {count} combinations")
        
        print(f"\nTotal: {len(benchmark.planned_combinations)} combinations")
        return
    
    # Print coverage report at start
    benchmark.print_coverage_report()
    
    # Run benchmarks
    start_time = time.time()
    
    if args.phase == 0 or args.phase is None:
        benchmark.run_all_phases()
    else:
        benchmark.run_phase(args.phase)
    
    elapsed = time.time() - start_time
    
    # Save skip log
    benchmark._save_skip_log()
    
    # Final coverage report
    benchmark.print_coverage_report()
    
    print(f"\nBenchmark completed in {elapsed:.2f} seconds")
    print(f"Results saved to: {benchmark.output_dir}")
    
    # Generate summary reports
    if benchmark.all_results:
        reporter = BenchmarkReporter(benchmark.all_results, str(benchmark.output_dir))
        reporter.generate_all()


if __name__ == "__main__":
    main()
