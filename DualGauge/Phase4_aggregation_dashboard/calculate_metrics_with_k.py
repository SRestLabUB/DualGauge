#!/usr/bin/env python3
"""
Script to calculate pass@k, secure@k_pass, and secure_pass@k metrics from metrics.json files
in each benchmark directory, aggregating by taking the mean across all problems.

Usage: python3 calculate_metrics_with_k.py <folder> [--k K_VALUE]

File structure:
- BenchmarkingExperiments/benchmarking_results/{benchmark_id}/metrics.json
  Each metrics.json contains metrics for each LLM (n, c, s, sp)

Formulas (using actual pass@k calculation with binomial coefficients):
- pass@k = mean([pass_at_k(n, c, k) for each problem])
  where pass_at_k(n, c, k) = 1 - C(n-c, k) / C(n, k)
  
- secure@k_pass = mean([secure_at_k_pass(n, s, k) for each problem])
  where secure_at_k_pass(n, s, k) = 1 - C(n-s, k) / C(n, k)
  
- secure_pass@k = mean([secure_pass_at_k(c, sp, k) for each problem])
  where secure_pass_at_k(c, sp, k) = 1 - C(c-sp, k) / C(c, k)

Where:
- n = total samples for a problem
- c = functionally correct samples for a problem
- s = securely correct samples for a problem
- sp = both secure and functionally correct samples for a problem
- C(n, k) = binomial coefficient "n choose k"

Usage: python scripts/calculate_metrics_with_k.py BenchmarkingExperiments/benchmarking_results/claude-haiku-4-5   
"""

import argparse
import json
import numpy as np
from pathlib import Path
from math import comb
from collections import defaultdict


# def calculate_at_k(total: int, count: int, k: int) -> float:
#     """
#     Generic function to calculate @k metric using binomial coefficients.
    
#     Formula: 1 - C(total - count, k) / C(total, k)
#     This calculates the probability that at least one of k samples
#     drawn from total samples has the desired property (count).
    
#     Args:
#         total: Total number of samples to choose from
#         count: Number of samples with the desired property
#         k: Number of samples to consider
        
#     Returns:
#         @k value as a percentage (0-100)
#     """
    # if total >= k and k > 0:
    #     if count >= total:
    #         # All samples have the desired property
    #         return 100.0
    #     elif total - count >= k:
    #         # Standard case: enough samples without the property to choose k from
    #         return (1 - comb(total - count, k) / comb(total, k)) * 100
    #     else:
    #         # Not enough samples without the property: at least one with property guaranteed
    #         return 100.0
    # return 0.0


def calculate_at_k(n: int, c: int, k: int) -> float:
#     """
#     Unbiased estimator of pass@k from Chen et al. (2021).
#     n: total samples generated
#     c: # correct (pass tests)
#     k: # draws/attempts
#     """
    if n >= k and k > 0:
        if n - c < k:
            return 100.0
        return (1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))) * 100
    return 0.0


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
    return calculate_at_k(n, c, k)


def secure_at_k(n: int, s: int, k: int) -> float:
    """
    Calculate secure@k for a single problem.
    
    Args:
        n: Total number of samples
        s: Number of secure samples
        k: Number of samples to consider
        
    Returns:
        secure@k value as a percentage (0-100)
    """
    return calculate_at_k(n, s, k)


def secure_at_k_pass(c: int, sp: int, k: int) -> float:
    """
    Calculate secure@k_pass for a single problem.
    
    Args:
        c: Number of functionally correct samples
        sp: Number of both secure and functionally correct samples
        k: Number of samples to consider
        
    Returns:
        secure@k_pass value as a percentage (0-100)
    """
    return calculate_at_k(c, sp, k)


def secure_pass_at_k(n: int, sp: int, k: int) -> float:
    """
    Calculate secure_pass@k for a single problem.
    
    Args:
        n: Number of total samples
        sp: Number of both secure and functionally correct samples
        k: Number of samples to consider
        
    Returns:
        secure_pass@k value as a percentage (0-100)
    """
    return calculate_at_k(n, sp, k)


def dataset_pass_at_k(c_list: list, n_list: list, k: int) -> float:
    """
    Calculate dataset-level pass@k by taking mean of pass@k across all problems.
    
    Args:
        c_list: list of c (functionally correct samples) for each problem
        n_list: list of n (total samples) for each problem (same length as c_list)
        k: Number of samples to consider
        
    Returns:
        Mean pass@k across all problems
    """
    vals = [pass_at_k(n, c, k) for c, n in zip(c_list, n_list)]
    return float(np.mean(vals)) if vals else 0.0


def dataset_secure_at_k(s_list: list, n_list: list, k: int) -> float:
    """
    Calculate dataset-level secure@k by taking mean across all problems.
    
    Args:
        s_list: list of s (secure samples) for each problem
        n_list: list of n (total samples) for each problem
        k: Number of samples to consider
        
    Returns:
        Mean secure@k across all problems
    """
    vals = [secure_at_k(n, s, k) for s, n in zip(s_list, n_list)]
    return float(np.mean(vals)) if vals else 0.0


def dataset_secure_at_k_pass(sp_list: list, c_list: list, k: int) -> float:
    """
    Calculate dataset-level secure@k_pass by taking mean across all problems.
    
    Args:
        s_list: list of s (secure samples) for each problem
        n_list: list of n (total samples) for each problem
        k: Number of samples to consider
        
    Returns:
        Mean secure@k_pass across all problems
    """
    vals = [secure_at_k_pass(c, sp, k) for c, sp in zip(c_list, sp_list)]
    return float(np.mean(vals)) if vals else 0.0


def dataset_secure_pass_at_k(sp_list: list, n_list: list, k: int) -> float:
    """
    Calculate dataset-level secure_pass@k by taking mean across all problems.
    
    Args:
        sp_list: list of sp (both secure and functionally correct) for each problem
        n_list: list of n (total samples) for each problem
        k: Number of samples to consider
        
    Returns:
        Mean secure_pass@k across all problems
    """
    vals = [secure_pass_at_k(n, sp, k) for sp, n in zip(sp_list, n_list)]
    return float(np.mean(vals)) if vals else 0.0


def load_metrics_from_directories(evaluation_results_dir: Path):
    """
    Load all metrics.json files from evaluation_results directory structure.
    
    Expected structure: evaluation_results/{benchmark_id}/metrics.json
    
    Args:
        evaluation_results_dir: Path to evaluation_results directory
        
    Returns:
        Dictionary mapping model_name to lists of metrics per problem:
        {
            "model_name": {
                "n_list": [n1, n2, ...],
                "c_list": [c1, c2, ...],
                "s_list": [s1, s2, ...],
                "sp_list": [sp1, sp2, ...]
            }
        }
    """
    model_data = defaultdict(lambda: {
        "n_list": [],
        "c_list": [],
        "s_list": [],
        "sp_list": []
    })
    
    # Find all metrics.json files
    metrics_files = list(evaluation_results_dir.glob("*/metrics.json"))
    
    if not metrics_files:
        print(f"Warning: No metrics.json files found in {evaluation_results_dir}")
        print(f"Expected structure: {evaluation_results_dir}/*/metrics.json")
        return {}
    
    print(f"Found {len(metrics_files)} metrics.json files")
    
    for metrics_file in sorted(metrics_files):
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
            
            # Handle different possible formats of metrics.json
            # Format 1: {"llm_name": {"n": ..., "c": ..., "s": ..., "sp": ...}, ...}
            # Format 2: {"models": [{"llm_name": ..., "n": ..., ...}, ...]}
            # Format 3: {"llm_name": {"pass_at_k": ..., "secure_pass_at_k": ..., ...}}
            
            if isinstance(data, dict):
                # Check if it's format with models array
                if "models" in data:
                    models = data["models"]
                else:
                    # Assume keys are model names
                    models = []
                    for model_name, model_data_item in data.items():
                        if isinstance(model_data_item, dict):
                            model_entry = {"llm_name": model_name, **model_data_item}
                            models.append(model_entry)
                
                # Process each model in this problem
                for model_entry in models:
                    # Get model name
                    model_name = model_entry.get("llm_name") or model_entry.get("model")
                    if not model_name:
                        continue
                    
                    # Extract n, c, s, sp
                    n = model_entry.get("n", 0)
                    c = model_entry.get("c", 0)
                    s = model_entry.get("s", 0)
                    sp = model_entry.get("sp", 0)
                    
                    # Add to model's data
                    model_data[model_name]["n_list"].append(n)
                    model_data[model_name]["c_list"].append(c)
                    model_data[model_name]["s_list"].append(s)
                    model_data[model_name]["sp_list"].append(sp)
                    
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error reading {metrics_file}: {e}")
            continue
    
    return dict(model_data)


def calculate_metrics_for_llm(data: dict, k: int):
    """
    Calculate aggregated dataset-level metrics for a single LLM across all problems.
    
    Args:
        data: Dictionary with n_list, c_list, s_list, sp_list for the LLM
        k: Number of samples to consider for pass@k calculation
        
    Returns:
        Dictionary with aggregated dataset metrics only
    """
    n_list = data["n_list"]
    c_list = data["c_list"]
    s_list = data["s_list"]
    sp_list = data["sp_list"]
    
    # Calculate mean metrics across all problems (dataset-level metrics)
    pass_at_k_mean = dataset_pass_at_k(c_list, n_list, k)
    secure_at_k_mean = dataset_secure_at_k(s_list, n_list, k)
    secure_at_k_pass_mean = dataset_secure_at_k_pass(sp_list, c_list, k)
    secure_pass_at_k_mean = dataset_secure_pass_at_k(sp_list, n_list, k)
    
    # Calculate total n, c, s, sp for reporting
    total_n = sum(n_list)
    total_c = sum(c_list)
    total_s = sum(s_list)
    total_sp = sum(sp_list)
    
    return {
        'pass@k': round(pass_at_k_mean, 2),
        'secure@k': round(secure_at_k_mean, 2),
        'secure@k_pass': round(secure_at_k_pass_mean, 2),
        'secure_pass@k': round(secure_pass_at_k_mean, 2),
        'total_n': total_n,
        'total_c': total_c,
        'total_s': total_s,
        'total_sp': total_sp,
        'num_problems': len(n_list)
    }


def generate_metrics_report_for_llm(llm_name: str, all_metrics: list, output_path: Path, k_value: int, num_iterations: int):
    """
    Generate metrics report in JSON format for a single LLM.
    Contains x metric sets (one for each iteration).
    
    Args:
        llm_name: Name of the LLM
        all_metrics: List of dictionaries, each with aggregated dataset metrics for one iteration
        output_path: Path to save the metrics report JSON file
        k_value: The k value used in calculations
        num_iterations: Number of iterations (x)
    """
    # Determine model type based on name
    model_type = "Open"  # Default type
    if "claude" in llm_name.lower() or "gpt" in llm_name.lower() or "gemini" in llm_name.lower():
        model_type = "Proprietary"
    
    # Create final report structure with all x metric sets
    report = {
        "k": k_value,
        "llm_name": llm_name,
        "type": model_type,
        "num_iterations": num_iterations,
        "metrics": all_metrics  # x entries, one per iteration
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"  ✅ Generated report: {output_path.name} ({num_iterations} metric sets)")


def load_evaluation_results_path(input_file: Path):
    """
    Load evaluation_results directory path from input file.
    
    Expected file format: single line with path to evaluation_results directory
    Or JSON format: {"evaluation_results_path": "path/to/evaluation_results"}
    
    Args:
        input_file: Path to input file containing evaluation_results path
        
    Returns:
        Path to evaluation_results directory, or None if not found
    """
    try:
        with open(input_file, 'r') as f:
            content = f.read().strip()
            
        # Try JSON format first
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "evaluation_results_path" in data:
                return Path(data["evaluation_results_path"])
        except json.JSONDecodeError:
            pass
        
        # Try simple text format (single line with path)
        if content:
            return Path(content)
            
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_file}")
        return None
    except Exception as e:
        print(f"Error reading input file {input_file}: {e}")
        return None
    
    return None


def main():
    """Main function to calculate metrics and generate JSON report for each LLM."""
    parser = argparse.ArgumentParser(
        description="Calculate pass@k, secure@k_pass, and secure_pass@k metrics from metrics.json files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate with k=1 (default)
  python3 calculate_metrics_with_k.py ../../../BenchmarkingExperiments/benchmarking_results
  
  # Calculate with custom k value
  python3 calculate_metrics_with_k.py ../../../BenchmarkingExperiments/benchmarking_results --k 3
  python3 calculate_metrics_with_k.py ../../../BenchmarkingExperiments/benchmarking_results -k 5
  
  # Use absolute path
  python3 calculate_metrics_with_k.py /path/to/evaluation_results --k 2
        """
    )
    
    parser.add_argument(
        "folder",
        type=str,
        help="Path to the evaluation_results directory containing benchmark folders with metrics.json files"
    )
    
    parser.add_argument(
        "-k", "--k-value",
        type=int,
        default=1,
        help="Number of samples to consider for pass@k calculation (default: 1)"
    )
    
    args = parser.parse_args()
    
    evaluation_results_path = args.folder
    k_value = args.k_value
    
    # Always calculate metrics once (no iterations)
    num_iterations = 1
    
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "BenchmarkingExperiments" / "evaluation_report"
    
    # Resolve evaluation_results directory path
    evaluation_results_dir = Path(evaluation_results_path)
    
    # Resolve relative paths
    if not evaluation_results_dir.is_absolute():
        # If path starts with ../, resolve relative to current working directory
        if str(evaluation_results_dir).startswith('../'):
            evaluation_results_dir = (Path.cwd() / evaluation_results_dir).resolve()
        else:
            # Otherwise, resolve relative to script's parent directory (project root)
            evaluation_results_dir = (script_dir.parent / evaluation_results_dir).resolve()
    
    print(f"Calculating metrics from metrics.json files with k={k_value}...")
    print(f"Evaluation results directory: {evaluation_results_dir}")
    print(f"Output directory: {output_dir}")
    
    if not evaluation_results_dir.exists():
        print(f"Error: evaluation_results directory not found at {evaluation_results_dir}")
        return
    
    # Load metrics from all benchmark directories
    model_data = load_metrics_from_directories(evaluation_results_dir)
    
    if not model_data:
        print("No model data found. Please check that metrics.json files exist.")
        return
    
    print(f"\nFound {len(model_data)} LLM(s):")
    for model_name, data in sorted(model_data.items()):
        print(f"  - {model_name}: {len(data['n_list'])} problems")
    
    # Process each LLM separately
    print(f"\nGenerating reports for each LLM with k={k_value}...")
    print("=" * 100)
    
    for llm_name, data in sorted(model_data.items()):
        print(f"\nProcessing {llm_name}...")
        
        # Calculate metrics for this LLM
        llm_metrics = calculate_metrics_for_llm(data, k_value)
        llm_metrics['iteration'] = 1
        all_metrics = [llm_metrics]
        
        # Generate output filename: metrics_k{value}_{llm_name}.json
        # Sanitize LLM name for filename (replace spaces/special chars with underscores)
        safe_llm_name = llm_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_path = output_dir / f"metrics_k{k_value}_{safe_llm_name}.json"
        
        # Generate report for this LLM
        generate_metrics_report_for_llm(llm_name, all_metrics, output_path, k_value, num_iterations)
        
        # Print summary
        metrics = llm_metrics
        print(f"  Summary: pass@k={metrics['pass@k']:.2f}, secure@k={metrics['secure@k']:.2f}, secure@k_pass={metrics['secure@k_pass']:.2f}, secure_pass@k={metrics['secure_pass@k']:.2f}")
        print(f"  Total: n={metrics['total_n']}, c={metrics['total_c']}, s={metrics['total_s']}, sp={metrics['total_sp']}, problems={metrics['num_problems']}")
    
    print(f"\n{'='*100}")
    print(f"✅ Successfully generated {len(model_data)} report(s) with k={k_value}!")
    print(f"📊 Reports saved to: {output_dir}")


if __name__ == "__main__":
    main()
