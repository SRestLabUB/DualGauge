#!/usr/bin/env python3
"""
Script to generate metrics.json files for each benchmark directory.

This script:
1. Reads all summary.json files from evaluation_results/{benchmark_id}/*/summary.json
2. For each benchmark, groups samples by LLM
3. Calculates per-benchmark metrics for each LLM:
   - n: total number of samples
   - c: number of functionally correct samples
   - s: number of secure samples
   - sp: number of samples that are both functionally correct and secure
   - pass_at_k: pass@k for k=1,2,3,4,5
   - secure_pass_at_k: secure_pass@k for k=1,2,3,4,5
   - secure_at_k_pass: secure@k_pass for k=1,2,3,4,5
4. Stores metrics.json in each benchmark directory

Usage: python3 scripts/generate_metrics_per_benchmark.py -f BenchmarkingExperiments/benchmarking_results/claude-haiku-4-5
"""

import argparse
import json
from pathlib import Path
from math import comb
from collections import defaultdict


def pass_at_k(n: int, c: int, k: int) -> float:
    """
    Calculate pass@k for a single problem.
    
    Args:
        n: Total number of samples
        c: Number of functionally correct samples
        k: Number of samples to consider
        
    Returns:
        pass@k value as a percentage (0-100)
    """
    if n >= k and k > 0:
        if c >= n:
            return 100.0
        elif n - c >= k:
            return (1 - comb(n - c, k) / comb(n, k)) * 100
        else:
            return 100.0
    return 0.0


def secure_pass_at_k(n: int, sp: int, k: int) -> float:
    """
    Calculate secure@k_pass for a single problem.
    
    Args:
        n: Total number of samples
        s: Number of secure samples
        k: Number of samples to consider
        
    Returns:
        secure@k_pass value as a percentage (0-100)
    """
    if n >= k and k > 0:
        if sp >= n:
            return 100.0
        elif n - sp >= k:
            return (1 - comb(n - sp, k) / comb(n, k)) * 100
        else:
            return 100.0
    return 0.0


def secure_at_k_pass(c: int, sp: int, k: int) -> float:
    """
    Calculate secure_pass@k for a single problem.
    
    Args:
        c: Number of functionally correct samples
        sp: Number of both secure and functionally correct samples
        k: Number of samples to consider
        
    Returns:
        secure_pass@k value as a percentage (0-100)
    """
    if c >= k and k > 0:
        if sp >= c:
            return 100.0
        elif c - sp >= k:
            return (1 - comb(c - sp, k) / comb(c, k)) * 100
        else:
            return 100.0
    return 0.0


def calculate_metrics_for_llm(samples: list, k_values=[1, 2, 3, 4, 5]):
    """
    Calculate metrics for a single LLM based on its samples.
    
    Args:
        samples: List of sample data dictionaries from summary.json files
        k_values: List of k values to calculate pass@k metrics for
        
    Returns:
        Dictionary with n, c, s, sp, and pass@k metrics
    """
    n = len(samples)  # Total number of samples
    c = 0  # Functionally correct samples
    s = 0  # Secure samples
    sp = 0  # Both secure and functionally correct samples
    
    for sample in samples:
        categories = sample.get("categories", {})
        
        # Check functional correctness
        func_correctness = categories.get("Functional Correctness", {})
        func_passed = func_correctness.get("passed_test_cases", 0)
        func_total = func_correctness.get("total_test_cases", 0)
        is_functionally_correct = func_passed == func_total if func_total > 0 else False
        
        # Check security
        security = categories.get("Security", {})
        sec_passed = security.get("passed_test_cases", 0)
        sec_total = security.get("total_test_cases", 0)
        is_secure = sec_passed == sec_total if sec_total > 0 else False
        
        # Update counters
        if is_functionally_correct:
            c += 1
        if is_secure:
            s += 1
        if is_functionally_correct and is_secure:
            sp += 1
    
    # Calculate pass@k metrics for different k values
    metrics = {
        "n": n,
        "c": c,
        "s": s,
        "sp": sp,
        "pass_at_k": {},
        "secure_pass_at_k": {},
        "secure_at_k_pass": {}
    }
    
    for k in k_values:
        metrics["pass_at_k"][f"k{k}"] = round(pass_at_k(n, c, k), 2)
        metrics["secure_at_k_pass"][f"k{k}"] = round(secure_at_k_pass(n, sp, k), 2)
        metrics["secure_pass_at_k"][f"k{k}"] = round(secure_pass_at_k(c, sp, k), 2)
    
    return metrics


def process_benchmark_directory(benchmark_dir: Path):
    """
    Process a single benchmark directory and generate metrics.json.
    
    Args:
        benchmark_dir: Path to benchmark directory (e.g., evaluation_results/0/)
        
    Returns:
        Dictionary with metrics for each LLM, or None if no samples found
    """
    # Find all summary.json files in this benchmark directory
    summary_files = list(benchmark_dir.rglob("summary.json"))
    
    if not summary_files:
        return None
    
    # Group samples by LLM
    llm_samples = defaultdict(list)
    
    for summary_file in summary_files:
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            llm_name = data.get("llm_name")
            if not llm_name:
                print(f"Warning: No llm_name found in {summary_file}")
                continue
            
            llm_samples[llm_name].append(data)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Error reading {summary_file}: {e}")
            continue
    
    if not llm_samples:
        return None
    
    # Calculate metrics for each LLM
    metrics_data = {}
    
    for llm_name, samples in llm_samples.items():
        metrics = calculate_metrics_for_llm(samples)
        metrics_data[llm_name] = metrics
    
    return metrics_data


def generate_metrics_for_all_benchmarks(evaluation_results_dir: Path):
    """
    Generate metrics.json for all benchmark directories.
    
    Args:
        evaluation_results_dir: Path to evaluation_results directory
    """
    # Find all benchmark directories (direct subdirectories)
    benchmark_dirs = [d for d in evaluation_results_dir.iterdir() 
                     if d.is_dir() and not d.name.startswith('.')]
    
    if not benchmark_dirs:
        print(f"No benchmark directories found in {evaluation_results_dir}")
        return
    
    print(f"Found {len(benchmark_dirs)} benchmark directories")
    
    processed_count = 0
    skipped_count = 0
    
    for benchmark_dir in sorted(benchmark_dirs):
        benchmark_id = benchmark_dir.name
        metrics_file = benchmark_dir / "metrics.json"
        
        print(f"\nProcessing benchmark {benchmark_id}...")
        
        # Process benchmark directory
        metrics_data = process_benchmark_directory(benchmark_dir)
        
        if not metrics_data:
            print(f"  ⚠️  No samples found, skipping {benchmark_id}")
            skipped_count += 1
            continue
        
        # Write metrics.json
        try:
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            print(f"  ✅ Generated metrics.json for {benchmark_id}")
            print(f"     Found {len(metrics_data)} LLM(s): {', '.join(metrics_data.keys())}")
            
            # Print summary for each LLM
            for llm_name, metrics in metrics_data.items():
                print(f"     - {llm_name}: n={metrics['n']}, c={metrics['c']}, s={metrics['s']}, sp={metrics['sp']}")
            
            processed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error writing metrics.json for {benchmark_id}: {e}")
            skipped_count += 1
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  ✅ Processed: {processed_count} benchmarks")
    print(f"  ⚠️  Skipped: {skipped_count} benchmarks")
    print(f"{'='*80}")


def main():
    """Main function to generate metrics for all benchmarks."""
    parser = argparse.ArgumentParser(
        description="Generate metrics.json files for each benchmark directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default evaluation_results directory
  python3 generate_metrics_per_benchmark.py
  
  # Use custom directory
  python3 generate_metrics_per_benchmark.py --folder /path/to/evaluation_results
  python3 generate_metrics_per_benchmark.py -f ../../../BenchmarkingExperiments/benchmarking_results_2
        """
    )
    
    parser.add_argument(
        "-f", "--folder",
        type=str,
        help="Path to the evaluation results directory containing benchmark folders. "
             "Defaults to ../../../BenchmarkingExperiments/benchmarking_results relative to script location.",
        default=None
    )
    
    args = parser.parse_args()
    
    # Determine evaluation_results_dir
    if args.folder:
        evaluation_results_dir = Path(args.folder).resolve()
    else:
        # Use default path relative to script location
        script_dir = Path(__file__).parent
        evaluation_results_dir = script_dir.parent / "BenchmarkingExperiments" / "benchmarking_results"
    
    print(f"Generating metrics.json files for all benchmarks...")
    print(f"Evaluation results directory: {evaluation_results_dir}")
    
    if not evaluation_results_dir.exists():
        print(f"Error: evaluation_results directory not found at {evaluation_results_dir}")
        print(f"Please provide a valid directory path using --folder or -f option.")
        return
    
    generate_metrics_for_all_benchmarks(evaluation_results_dir)
    
    print(f"\n✅ Done! All metrics.json files have been generated.")


if __name__ == "__main__":
    main()

