"""
Benchmark Results Reporter
==========================
Generates reports in JSON and Markdown formats.
Reads only flat keys from results - no nested dict access.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class BenchmarkReporter:
    """Generate benchmark reports in multiple formats."""
    
    def __init__(self, results: List[Dict[str, Any]], output_dir: str = "benchmark_results"):
        self.results = results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_all(self):
        """Generate all report formats."""
        print(f"\nGenerating reports in {self.output_dir}/...")
        
        json_path = self.generate_json()
        print(f"  ✓ JSON: {json_path}")
        
        md_path = self.generate_markdown()
        print(f"  ✓ Markdown: {md_path}")
        
        summary_path = self.generate_summary()
        print(f"  ✓ Summary: {summary_path}")
        
        return {
            "json": str(json_path),
            "markdown": str(md_path),
            "summary": str(summary_path)
        }
    
    def generate_json(self) -> str:
        """Generate JSON report with flat structure."""
        filepath = self.output_dir / f"benchmark_{self.timestamp}.json"
        
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_configurations": len(self.results)
            },
            "results": self.results
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(filepath)
    
    def generate_markdown(self) -> str:
        """
        Generate Markdown report with tables.
        Shows: scheme, curve, dkg, n, loss_rate, keygen_ms, sign_ms, 
               verify_ms, network_overhead_ms, compatibility
        Flags suboptimal rows with ⚠ and invalid rows with ✗
        """
        filepath = self.output_dir / f"benchmark_{self.timestamp}.md"
        
        lines = [
            "# Threshold Signature Schemes - Benchmark Results",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Total Configurations Tested:** {len(self.results)}",
            "",
            "---",
            ""
        ]
        
        # Group by scheme
        schemes = {}
        for result in self.results:
            scheme = result.get("scheme", "unknown")
            if scheme not in schemes:
                schemes[scheme] = []
            schemes[scheme].append(result)
        
        for scheme_name, scheme_results in sorted(schemes.items()):
            lines.append(f"## {scheme_name.upper()}")
            lines.append("")
            
            # Create table header
            lines.append(
                "| Curve | DKG | n | t | Loss% | KeyGen (ms) | Sign (ms) | Verify (ms) | Net Overhead (ms) | Status |"
            )
            lines.append(
                "|-------|-----|---|---|-------|-------------|-----------|-------------|-------------------|--------|"
            )
            
            # Sort by curve, dkg, and n
            sorted_results = sorted(
                scheme_results, 
                key=lambda x: (x.get("curve", ""), x.get("dkg", ""), x.get("n", 0))
            )
            
            for result in sorted_results:
                curve = result.get("curve", "")
                dkg = result.get("dkg", "")
                n = result.get("n", 0)
                t = result.get("t", 0)
                loss_rate = result.get("loss_rate", 0.0)
                
                # Read flat keys only
                keygen = result.get("keygen_ms")
                sign = result.get("sign_ms")
                verify = result.get("verify_ms")
                net_overhead = result.get("network_overhead_ms")
                compatibility = result.get("compatibility", "unknown")
                
                # Format values
                keygen_str = f"{keygen:.2f}" if keygen is not None else "N/A"
                sign_str = f"{sign:.2f}" if sign is not None else "N/A"
                verify_str = f"{verify:.2f}" if verify is not None else "N/A"
                net_str = f"{net_overhead:.2f}" if net_overhead is not None else "N/A"
                
                # Add status flags
                status = ""
                if compatibility == "suboptimal":
                    status = "⚠ suboptimal"
                elif compatibility == "invalid":
                    status = "✗ invalid"
                else:
                    status = "✓ valid"
                
                lines.append(
                    f"| {curve} | {dkg} | {n} | {t} | {loss_rate*100:.1f}% | "
                    f"{keygen_str} | {sign_str} | {verify_str} | {net_str} | {status} |"
                )
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Add summary statistics
        lines.append("## Summary Statistics")
        lines.append("")
        self._add_summary_table(lines)
        
        # Write file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        return str(filepath)
    
    def _add_summary_table(self, lines: List[str]):
        """Add summary statistics table."""
        if not self.results:
            lines.append("No results available.")
            return
        
        # Calculate averages by scheme
        scheme_stats = {}
        for result in self.results:
            scheme = result.get("scheme", "unknown")
            if scheme not in scheme_stats:
                scheme_stats[scheme] = {
                    "keygen": [], "sign": [], "verify": [], "net_overhead": []
                }
            
            keygen = result.get("keygen_ms")
            sign = result.get("sign_ms")
            verify = result.get("verify_ms")
            net_overhead = result.get("network_overhead_ms")
            
            if keygen is not None:
                scheme_stats[scheme]["keygen"].append(keygen)
            if sign is not None:
                scheme_stats[scheme]["sign"].append(sign)
            if verify is not None:
                scheme_stats[scheme]["verify"].append(verify)
            if net_overhead is not None:
                scheme_stats[scheme]["net_overhead"].append(net_overhead)
        
        lines.append("### Average Performance by Scheme")
        lines.append("")
        lines.append("| Scheme | Avg KeyGen (ms) | Avg Sign (ms) | Avg Verify (ms) | Avg Net Overhead (ms) |")
        lines.append("|--------|-----------------|---------------|-----------------|----------------------|")
        
        for scheme_name in sorted(scheme_stats.keys()):
            stats = scheme_stats[scheme_name]
            avg_keygen = sum(stats["keygen"]) / len(stats["keygen"]) if stats["keygen"] else 0
            avg_sign = sum(stats["sign"]) / len(stats["sign"]) if stats["sign"] else 0
            avg_verify = sum(stats["verify"]) / len(stats["verify"]) if stats["verify"] else 0
            avg_net = sum(stats["net_overhead"]) / len(stats["net_overhead"]) if stats["net_overhead"] else 0
            
            lines.append(
                f"| {scheme_name} | {avg_keygen:.2f} | {avg_sign:.2f} | "
                f"{avg_verify:.2f} | {avg_net:.2f} |"
            )
        
        lines.append("")
        
        # Count by compatibility
        valid_count = sum(1 for r in self.results if r.get("compatibility") == "valid")
        suboptimal_count = sum(1 for r in self.results if r.get("compatibility") == "suboptimal")
        invalid_count = sum(1 for r in self.results if r.get("compatibility") == "invalid")
        
        lines.append("### Compatibility Summary")
        lines.append("")
        lines.append(f"- ✓ Valid: {valid_count}")
        lines.append(f"- ⚠ Suboptimal: {suboptimal_count}")
        lines.append(f"- ✗ Invalid: {invalid_count}")
        lines.append("")
    
    def generate_summary(self) -> str:
        """Generate a concise text summary report."""
        filepath = self.output_dir / f"summary_{self.timestamp}.txt"
        
        lines = [
            "=" * 80,
            "THRESHOLD SIGNATURE SCHEMES - BENCHMARK SUMMARY",
            "=" * 80,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total configurations: {len(self.results)}",
            "",
        ]
        
        if not self.results:
            lines.append("No benchmark results available.")
        else:
            # Find fastest scheme for each operation (only considering non-null values)
            valid_keygen = [(r, r.get("keygen_ms")) for r in self.results if r.get("keygen_ms") is not None]
            valid_sign = [(r, r.get("sign_ms")) for r in self.results if r.get("sign_ms") is not None]
            valid_verify = [(r, r.get("verify_ms")) for r in self.results if r.get("verify_ms") is not None]
            
            if valid_keygen:
                best_keygen = min(valid_keygen, key=lambda x: x[1])
                lines.append("PERFORMANCE LEADERS:")
                lines.append("-" * 40)
                lines.append(
                    f"Fastest KeyGen:  {best_keygen[0].get('scheme')} "
                    f"({best_keygen[0].get('curve')}, n={best_keygen[0].get('n')})"
                )
                lines.append(f"                 {best_keygen[1]:.2f} ms")
                lines.append("")
            
            if valid_sign:
                best_sign = min(valid_sign, key=lambda x: x[1])
                lines.append(
                    f"Fastest Sign:    {best_sign[0].get('scheme')} "
                    f"({best_sign[0].get('curve')}, n={best_sign[0].get('n')})"
                )
                lines.append(f"                 {best_sign[1]:.2f} ms")
                lines.append("")
            
            if valid_verify:
                best_verify = min(valid_verify, key=lambda x: x[1])
                lines.append(
                    f"Fastest Verify:  {best_verify[0].get('scheme')} "
                    f"({best_verify[0].get('curve')})"
                )
                lines.append(f"                 {best_verify[1]:.2f} ms")
                lines.append("")
            
            # Average performance by scheme
            lines.append("AVERAGE PERFORMANCE BY SCHEME:")
            lines.append("-" * 40)
            
            schemes = {}
            for result in self.results:
                scheme = result.get("scheme", "unknown")
                if scheme not in schemes:
                    schemes[scheme] = {"keygen": [], "sign": [], "verify": []}
                
                keygen = result.get("keygen_ms")
                sign = result.get("sign_ms")
                verify = result.get("verify_ms")
                
                if keygen is not None:
                    schemes[scheme]["keygen"].append(keygen)
                if sign is not None:
                    schemes[scheme]["sign"].append(sign)
                if verify is not None:
                    schemes[scheme]["verify"].append(verify)
            
            for scheme_name in sorted(schemes.keys()):
                data = schemes[scheme_name]
                avg_keygen = sum(data["keygen"]) / len(data["keygen"]) if data["keygen"] else 0
                avg_sign = sum(data["sign"]) / len(data["sign"]) if data["sign"] else 0
                avg_verify = sum(data["verify"]) / len(data["verify"]) if data["verify"] else 0
                
                lines.append(
                    f"{scheme_name:10s}: KeyGen={avg_keygen:7.2f}ms, "
                    f"Sign={avg_sign:7.2f}ms, Verify={avg_verify:7.2f}ms"
                )
        
        lines.append("")
        lines.append("=" * 80)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        return str(filepath)
    
    def print_coverage_report(
        self, 
        planned_combinations: List[Dict[str, Any]],
        skip_log: List[Dict[str, Any]]
    ):
        """
        Print coverage report showing which combinations were planned,
        which ran successfully, which were skipped, and which are missing.
        
        Args:
            planned_combinations: List of all planned combination dicts
            skip_log: List of skipped combinations with reasons
        """
        print("\n" + "=" * 80)
        print("COVERAGE REPORT")
        print("=" * 80)
        
        # Create set of completed combinations
        completed_keys = set()
        for result in self.results:
            key = (
                result.get("phase"),
                result.get("scheme"),
                result.get("curve"),
                result.get("dkg"),
                result.get("n"),
                result.get("loss_rate")
            )
            completed_keys.add(key)
        
        # Create set of skipped combinations
        skipped_keys = set()
        for skip in skip_log:
            key = (
                skip.get("phase"),
                skip.get("scheme"),
                skip.get("curve"),
                skip.get("dkg"),
                skip.get("n"),
                skip.get("loss_rate")
            )
            skipped_keys.add(key)
        
        # Create set of planned combinations
        planned_keys = set()
        for combo in planned_combinations:
            key = (
                combo.get("phase"),
                combo.get("scheme"),
                combo.get("curve"),
                combo.get("dkg"),
                combo.get("n"),
                combo.get("loss_rate")
            )
            planned_keys.add(key)
        
        # Calculate missing
        missing_keys = planned_keys - completed_keys - skipped_keys
        
        # Count by status
        valid_ran = sum(1 for r in self.results if r.get("compatibility") == "valid")
        suboptimal_ran = sum(1 for r in self.results if r.get("compatibility") == "suboptimal")
        invalid_skipped = len(skip_log)
        missing = len(missing_keys)
        
        print(f"\nTotal planned combinations: {len(planned_keys)}")
        print(f"  ✓ Valid ran:         {valid_ran}")
        print(f"  ⚠ Suboptimal ran:    {suboptimal_ran}")
        print(f"  ✗ Invalid skipped:   {invalid_skipped}")
        print(f"  ? Missing:           {missing}")
        
        if missing > 0:
            print("\nMissing combinations:")
            for key in sorted(missing_keys)[:20]:  # Show first 20
                print(f"  - Phase: {key[0]}, Scheme: {key[1]}, Curve: {key[2]}, "
                      f"DKG: {key[3]}, n: {key[4]}, Loss: {key[5]}")
            if len(missing_keys) > 20:
                print(f"  ... and {len(missing_keys) - 20} more")
        
        print("\n" + "=" * 80)
