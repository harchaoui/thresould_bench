"""
Benchmark Results Reporter
Generates reports in JSON and Markdown formats.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any


class BenchmarkReporter:
    """Generate benchmark reports in multiple formats."""
    
    def __init__(self, results: List[Dict[str, Any]], output_dir: str = "benchmark_results"):
        self.results = results
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
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
            "json": json_path,
            "markdown": md_path,
            "summary": summary_path
        }
    
    def generate_json(self) -> str:
        """Generate JSON report."""
        filepath = os.path.join(self.output_dir, f"benchmark_{self.timestamp}.json")
        
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_configurations": len(self.results)
            },
            "results": self.results
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath
    
    def generate_markdown(self) -> str:
        """Generate Markdown report with tables."""
        filepath = os.path.join(self.output_dir, f"benchmark_{self.timestamp}.md")
        
        lines = [
            "# SRTS Enhanced - Benchmark Results",
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
            scheme = result["scheme"]
            if scheme not in schemes:
                schemes[scheme] = []
            schemes[scheme].append(result)
        
        for scheme_name, scheme_results in sorted(schemes.items()):
            lines.append(f"## {scheme_name.upper()}")
            lines.append("")
            
            # Create table header
            lines.append("| Curve | n | t | KeyGen (ms) | Sign (ms) | Verify (ms) | Sig Size (bytes) |")
            lines.append("|-------|---|---|-------------|-----------|-------------|------------------|")
            
            # Sort by curve and n
            sorted_results = sorted(scheme_results, key=lambda x: (x["curve"], x["n"]))
            
            for result in sorted_results:
                curve = result["curve"]
                n = result["n"]
                t = result["t"]
                
                # Extract timing metrics
                keygen = result.get("timing", {}).get("keygen_mean_ms", 0)
                sign = result.get("timing", {}).get("partial_sign_mean_ms", 0)
                verify = result.get("timing", {}).get("verify_mean_ms", 0)
                sig_size = result.get("signatures", {}).get("final_sig_avg_size_bytes", 0)
                
                lines.append(
                    f"| {curve} | {n} | {t} | {keygen:.2f} | {sign:.2f} | {verify:.2f} | {sig_size:.0f} |"
                )
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Add comparison section
        lines.append("## Performance Comparison")
        lines.append("")
        lines.append("### Key Generation Time by Scale")
        lines.append("")
        lines.append("```")
        
        # Simple ASCII chart for keygen times
        if self.results:
            max_keygen = max(r.get("timing", {}).get("keygen_mean_ms", 0) for r in self.results)
            for result in sorted(self.results, key=lambda x: x["n"])[:10]:  # Show first 10
                keygen = result.get("timing", {}).get("keygen_mean_ms", 0)
                bar_len = int((keygen / max_keygen) * 40) if max_keygen > 0 else 0
                bar = "█" * bar_len
                lines.append(f"{result['scheme']:6s} n={result['n']:3d} {bar} {keygen:.2f}ms")
        
        lines.append("```")
        lines.append("")
        
        # Write file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        return filepath
    
    def generate_summary(self) -> str:
        """Generate a concise summary report."""
        filepath = os.path.join(self.output_dir, f"summary_{self.timestamp}.txt")
        
        lines = [
            "=" * 80,
            "SRTS ENHANCED - BENCHMARK SUMMARY",
            "=" * 80,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total configurations: {len(self.results)}",
            "",
        ]
        
        if not self.results:
            lines.append("No benchmark results available.")
        else:
            # Find fastest scheme for each operation
            best_keygen = min(self.results, key=lambda x: x.get("timing", {}).get("keygen_mean_ms", float('inf')))
            best_sign = min(self.results, key=lambda x: x.get("timing", {}).get("partial_sign_mean_ms", float('inf')))
            best_verify = min(self.results, key=lambda x: x.get("timing", {}).get("verify_mean_ms", float('inf')))
            smallest_sig = min(self.results, key=lambda x: x.get("signatures", {}).get("final_sig_avg_size_bytes", float('inf')))
            
            lines.append("PERFORMANCE LEADERS:")
            lines.append("-" * 40)
            lines.append(f"Fastest KeyGen:  {best_keygen['scheme']} ({best_keygen['curve']}, n={best_keygen['n']})")
            lines.append(f"                 {best_keygen.get('timing', {}).get('keygen_mean_ms', 0):.2f} ms")
            lines.append("")
            lines.append(f"Fastest Sign:    {best_sign['scheme']} ({best_sign['curve']}, n={best_sign['n']})")
            lines.append(f"                 {best_sign.get('timing', {}).get('partial_sign_mean_ms', 0):.2f} ms")
            lines.append("")
            lines.append(f"Fastest Verify:  {best_verify['scheme']} ({best_verify['curve']})")
            lines.append(f"                 {best_verify.get('timing', {}).get('verify_mean_ms', 0):.2f} ms")
            lines.append("")
            lines.append(f"Smallest Sig:    {smallest_sig['scheme']} ({smallest_sig['curve']})")
            lines.append(f"                 {smallest_sig.get('signatures', {}).get('final_sig_avg_size_bytes', 0):.0f} bytes")
            lines.append("")
            
            # Average performance by scheme
            lines.append("AVERAGE PERFORMANCE BY SCHEME:")
            lines.append("-" * 40)
            
            schemes = {}
            for result in self.results:
                scheme = result["scheme"]
                if scheme not in schemes:
                    schemes[scheme] = {"keygen": [], "sign": [], "verify": []}
                schemes[scheme]["keygen"].append(result.get("timing", {}).get("keygen_mean_ms", 0))
                schemes[scheme]["sign"].append(result.get("timing", {}).get("partial_sign_mean_ms", 0))
                schemes[scheme]["verify"].append(result.get("timing", {}).get("verify_mean_ms", 0))
            
            for scheme_name in sorted(schemes.keys()):
                data = schemes[scheme_name]
                avg_keygen = sum(data["keygen"]) / len(data["keygen"]) if data["keygen"] else 0
                avg_sign = sum(data["sign"]) / len(data["sign"]) if data["sign"] else 0
                avg_verify = sum(data["verify"]) / len(data["verify"]) if data["verify"] else 0
                
                lines.append(f"{scheme_name:10s}: KeyGen={avg_keygen:7.2f}ms, Sign={avg_sign:7.2f}ms, Verify={avg_verify:7.2f}ms")
        
        lines.append("")
        lines.append("=" * 80)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        return filepath
