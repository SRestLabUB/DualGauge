#!/usr/bin/env python3
"""
Script to calculate metrics from evaluation results and output to CSV.

Takes an evaluation_results folder with structure:
evaluation_results/
├── model_1/
│   ├── benchmark_0/
│   │   ├── sample_1/summary.json
│   │   ├── sample_2/summary.json
│   │   └── ...
│   ├── benchmark_1/
│   └── ...
├── model_2/
└── ...

Outputs a CSV with one row per model containing all metrics.

Usage: python3 generate_metrics_csv.py evaluation_results [--k K_VALUE] [--output OUTPUT.csv]
"""

import argparse
import json
import csv
import numpy as np
from pathlib import Path
from collections import defaultdict


def calculate_at_k(n: int, c: int, k: int) -> float:
    """
    Unbiased estimator of pass@k from Chen et al. (2021).
    n: total samples generated
    c: # correct (pass tests)
    k: # draws/attempts
    """
    if n >= k and k > 0:
        if n - c < k:
            return 100.0
        return (1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))) * 100
    return 0.0


def pass_at_k(n: int, c: int, k: int) -> float:
    """Calculate pass@k for a single problem."""
    return calculate_at_k(n, c, k)


def secure_at_k(n: int, s: int, k: int) -> float:
    """Calculate secure@k for a single problem."""
    return calculate_at_k(n, s, k)


def secure_at_k_pass(c: int, sp: int, k: int) -> float:
    """Calculate secure@k_pass for a single problem."""
    return calculate_at_k(c, sp, k)


def secure_pass_at_k(n: int, sp: int, k: int) -> float:
    """Calculate secure_pass@k for a single problem."""
    return calculate_at_k(n, sp, k)


def process_summary_file(summary_file: Path):
    """
    Process a single summary.json file and extract sample metrics.
    
    Returns:
        Tuple of (is_functionally_correct, is_secure, is_both, 
                  func_passed, func_total, sec_passed, sec_total)
    """
    try:
        with open(summary_file, 'r') as f:
            data = json.load(f)
        
        categories = data.get("categories", {})
        
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
        
        is_both = is_functionally_correct and is_secure
        
        return (is_functionally_correct, is_secure, is_both, 
                func_passed, func_total, sec_passed, sec_total)
        
    except Exception as e:
        print(f"Warning: Error reading {summary_file}: {e}")
        return False, False, False, 0, 0, 0, 0


def process_model_directory(model_dir: Path):
    """
    Process all benchmarks for a single model.
    
    Args:
        model_dir: Path to model directory containing benchmark subdirectories
        
    Returns:
        Dictionary with lists and test case counts: {
            "n_list": [n per problem],
            "c_list": [c per problem],
            "s_list": [s per problem],
            "sp_list": [sp per problem],
            "func_test_passed": total functional test cases passed,
            "func_test_total": total functional test cases,
            "sec_test_passed": total security test cases passed,
            "sec_test_total": total security test cases
        }
    """
    # Find all benchmark directories
    benchmark_dirs = [d for d in model_dir.iterdir() 
                     if d.is_dir() and not d.name.startswith('.')]
    
    n_list = []
    c_list = []
    s_list = []
    sp_list = []
    
    # For raw test case metrics
    func_test_passed_total = 0
    func_test_total_total = 0
    sec_test_passed_total = 0
    sec_test_total_total = 0
    
    for benchmark_dir in sorted(benchmark_dirs):
        # Find all summary.json files in this benchmark
        summary_files = list(benchmark_dir.rglob("summary.json"))
        
        if not summary_files:
            continue
        
        # Count metrics for this benchmark (problem)
        n = len(summary_files)
        c = 0
        s = 0
        sp = 0
        
        for summary_file in summary_files:
            (is_correct, is_secure, is_both, 
             func_passed, func_total, sec_passed, sec_total) = process_summary_file(summary_file)
            
            if is_correct:
                c += 1
            if is_secure:
                s += 1
            if is_both:
                sp += 1
            
            # Accumulate raw test case counts
            func_test_passed_total += func_passed
            func_test_total_total += func_total
            sec_test_passed_total += sec_passed
            sec_test_total_total += sec_total
        
        n_list.append(n)
        c_list.append(c)
        s_list.append(s)
        sp_list.append(sp)
    
    return {
        "n_list": n_list,
        "c_list": c_list,
        "s_list": s_list,
        "sp_list": sp_list,
        "func_test_passed": func_test_passed_total,
        "func_test_total": func_test_total_total,
        "sec_test_passed": sec_test_passed_total,
        "sec_test_total": sec_test_total_total
    }


def calculate_model_metrics(model_data: dict, k: int):
    """
    Calculate aggregated metrics for a model across all problems.
    
    Args:
        model_data: Dictionary with n_list, c_list, s_list, sp_list, and test case counts
        k: Number of samples to consider for pass@k calculation
        
    Returns:
        Dictionary with all metrics
    """
    n_list = model_data["n_list"]
    c_list = model_data["c_list"]
    s_list = model_data["s_list"]
    sp_list = model_data["sp_list"]
    
    if not n_list:
        return None
    
    # Calculate pass@k for each problem, then take mean
    pass_at_k_vals = [pass_at_k(n, c, k) for n, c in zip(n_list, c_list)]
    secure_at_k_vals = [secure_at_k(n, s, k) for n, s in zip(n_list, s_list)]
    secure_at_k_pass_vals = [secure_at_k_pass(c, sp, k) for c, sp in zip(c_list, sp_list)]
    secure_pass_at_k_vals = [secure_pass_at_k(n, sp, k) for n, sp in zip(n_list, sp_list)]
    
    pass_at_k_mean = float(np.mean(pass_at_k_vals)) if pass_at_k_vals else 0.0
    secure_at_k_mean = float(np.mean(secure_at_k_vals)) if secure_at_k_vals else 0.0
    secure_at_k_pass_mean = float(np.mean(secure_at_k_pass_vals)) if secure_at_k_pass_vals else 0.0
    secure_pass_at_k_mean = float(np.mean(secure_pass_at_k_vals)) if secure_pass_at_k_vals else 0.0
    
    # Calculate raw test case percentages
    func_test_passed = model_data["func_test_passed"]
    func_test_total = model_data["func_test_total"]
    sec_test_passed = model_data["sec_test_passed"]
    sec_test_total = model_data["sec_test_total"]
    
    func_test_pct = (func_test_passed / func_test_total * 100) if func_test_total > 0 else 0.0
    sec_test_pct = (sec_test_passed / sec_test_total * 100) if sec_test_total > 0 else 0.0
    
    return {
        'model_name': None,  # Will be filled in later
        'pass@k': round(pass_at_k_mean, 2),
        'secure@k': round(secure_at_k_mean, 2),
        'secure@k_pass': round(secure_at_k_pass_mean, 2),
        'secure_pass@k': round(secure_pass_at_k_mean, 2),
        'total_n': sum(n_list),
        'total_c': sum(c_list),
        'total_s': sum(s_list),
        'total_sp': sum(sp_list),
        'num_problems': len(n_list),
        'func_test_passed': func_test_passed,
        'func_test_total': func_test_total,
        'func_test_pct': round(func_test_pct, 2),
        'sec_test_passed': sec_test_passed,
        'sec_test_total': sec_test_total,
        'sec_test_pct': round(sec_test_pct, 2)
    }


def generate_metrics_csv(evaluation_results_dir: Path, k: int, output_file: Path):
    """
    Generate CSV with metrics for all models.
    
    Args:
        evaluation_results_dir: Path to evaluation_results directory
        k: k value for pass@k calculations
        output_file: Path to output CSV file
    """
    # Find all model directories
    model_dirs = [d for d in evaluation_results_dir.iterdir() 
                 if d.is_dir() and not d.name.startswith('.')]
    
    if not model_dirs:
        print(f"Error: No model directories found in {evaluation_results_dir}")
        return
    
    print(f"Found {len(model_dirs)} model(s)")
    print(f"Calculating metrics with k={k}...\n")
    
    all_metrics = []
    
    for model_dir in sorted(model_dirs):
        model_name = model_dir.name
        print(f"Processing {model_name}...")
        
        # Process all benchmarks for this model
        model_data = process_model_directory(model_dir)
        
        if not model_data["n_list"]:
            print(f"  ⚠️  No data found, skipping")
            continue
        
        # Calculate metrics
        metrics = calculate_model_metrics(model_data, k)
        
        if metrics:
            metrics['model_name'] = model_name
            all_metrics.append(metrics)
            
            print(f"  ✅ pass@{k}={metrics['pass@k']:.2f}, "
                  f"secure@{k}={metrics['secure@k']:.2f}, "
                  f"secure@{k}_pass={metrics['secure@k_pass']:.2f}, "
                  f"secure_pass@{k}={metrics['secure_pass@k']:.2f}")
            print(f"     Sample-level: n={metrics['total_n']}, c={metrics['total_c']}, "
                  f"s={metrics['total_s']}, sp={metrics['total_sp']}, "
                  f"problems={metrics['num_problems']}")
            print(f"     Test-level: Functional={metrics['func_test_passed']}/{metrics['func_test_total']} "
                  f"({metrics['func_test_pct']:.2f}%), "
                  f"Security={metrics['sec_test_passed']}/{metrics['sec_test_total']} "
                  f"({metrics['sec_test_pct']:.2f}%)\n")
    
    if not all_metrics:
        print("Error: No metrics calculated for any model")
        return
    
    # Write to CSV
    fieldnames = [
        'model_name',
        f'pass@{k}',
        f'secure@{k}',
        f'secure@{k}_pass',
        f'secure_pass@{k}',
        'total_n',
        'total_c',
        'total_s',
        'total_sp',
        'num_problems',
        'func_test_passed',
        'func_test_total',
        'func_test_pct',
        'sec_test_passed',
        'sec_test_total',
        'sec_test_pct'
    ]
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in all_metrics:
            # Rename keys to include k value
            row = {
                'model_name': metrics['model_name'],
                f'pass@{k}': metrics['pass@k'],
                f'secure@{k}': metrics['secure@k'],
                f'secure@{k}_pass': metrics['secure@k_pass'],
                f'secure_pass@{k}': metrics['secure_pass@k'],
                'total_n': metrics['total_n'],
                'total_c': metrics['total_c'],
                'total_s': metrics['total_s'],
                'total_sp': metrics['total_sp'],
                'num_problems': metrics['num_problems'],
                'func_test_passed': metrics['func_test_passed'],
                'func_test_total': metrics['func_test_total'],
                'func_test_pct': metrics['func_test_pct'],
                'sec_test_passed': metrics['sec_test_passed'],
                'sec_test_total': metrics['sec_test_total'],
                'sec_test_pct': metrics['sec_test_pct']
            }
            writer.writerow(row)
    
    print(f"{'='*80}")
    print(f"✅ Successfully generated metrics for {len(all_metrics)} model(s)!")
    print(f"📊 CSV saved to: {output_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Calculate metrics from evaluation results and output to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  
  # Specify output file
  python3 generate_metrics_csv.py --input_folder ../../../BenchmarkingExperiments/benchmarking_results --k 5 --output results.csv
        """
    )
    
    parser.add_argument(
        "--input_folder",
        type=str,
        default="../../../BenchmarkingExperiments/benchmarking_results",
        help="Path to the evaluation_results directory containing model folders"
    )
    
    parser.add_argument(
        "-k", "--k-value",
        type=int,
        default=1,
        help="Number of samples to consider for pass@k calculation (default: 1)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: metrics_k{k}.csv in current directory)"
    )
    
    args = parser.parse_args()
    
    evaluation_results_dir = Path(args.input_folder).resolve()
    k_value = args.k_value
    
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path(f"metrics_k{k_value}.csv")
    
    if not evaluation_results_dir.exists():
        print(f"Error: Directory not found: {evaluation_results_dir}")
        return
    
    if not evaluation_results_dir.is_dir():
        print(f"Error: Not a directory: {evaluation_results_dir}")
        return
    
    generate_metrics_csv(evaluation_results_dir, k_value, output_file)


if __name__ == "__main__":
    main()