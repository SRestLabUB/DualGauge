#!/usr/bin/env python3
"""
Simple script to run the fresh consolidated pipeline.
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
# Add current directory and parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from evaluation_pipeline import FreshSecurityPipeline, load_config_from_env, print_config


def infer_output_dir_from_log_dir(log_dir: str) -> str:
    """Map execution-results paths to parallel evaluation-results paths."""
    log_path = Path(log_dir)
    parts = list(log_path.parts)

    for i, part in enumerate(parts):
        if part == "execution_results":
            parts[i] = "evaluation_results"
            return str(Path(*parts))

    return str(log_path.parent / "evaluation_results" / log_path.name)


def parse_arguments():
    """Parse command-line arguments."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.constants import EXPERIMENTS_DIR, DEFAULT_AGENT_MODEL

    default_log_dir = os.path.join(EXPERIMENTS_DIR, 'execution_results')

    parser = argparse.ArgumentParser(
        description='Run the LLM Security Benchmark Evaluation Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --log-dir BenchmarkingExperiments/execution_results/python/gpt-5-nano-v10
  %(prog)s --log-dir BenchmarkingExperiments/execution_results --model gpt-4o
  %(prog)s --evaluator-model gpt-4o --resolver-model claude-sonnet-4-6
        """
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        default=default_log_dir,
        help='Path to the directory containing execution results (result.json files)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Path to the output directory for results (default: derived from --log-dir)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Use a single model for both evaluation and resolution (e.g., gpt-4o, claude-sonnet-4-6)'
    )

    parser.add_argument(
        '--evaluator-model',
        type=str,
        default=None,
        help='LLM model for evaluation (default: gpt-4o)'
    )

    parser.add_argument(
        '--resolver-model',
        type=str,
        default=None,
        help='LLM model for gap resolution (default: same as evaluator-model)'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: 5)'
    )

    parser.add_argument(
        '--benchmark_ids',
        type=int,
        nargs='+',
        default=None,
        help='Only evaluate these benchmark IDs (e.g. --benchmark_ids 1 10 57)'
    )

    return parser.parse_args()


def main():
    """Run the evaluation pipeline."""
    args = parse_arguments()
    config = load_config_from_env()

    config.log_dir = args.log_dir
    config.output_dir = args.output_dir or infer_output_dir_from_log_dir(config.log_dir)

    # --model sets both evaluator and resolver to the same model
    if args.model:
        config.evaluator_model = args.model
        config.resolver_model = args.model

    if args.evaluator_model:
        config.evaluator_model = args.evaluator_model

    if args.resolver_model:
        config.resolver_model = args.resolver_model
    elif not args.model:
        # Default resolver to same as evaluator when not specified
        config.resolver_model = config.evaluator_model

    if args.max_workers:
        config.max_workers = args.max_workers
    
    print_config(config)

    try:
        pipeline = FreshSecurityPipeline(config)
        results = pipeline.run_pipeline(benchmark_ids=set(args.benchmark_ids) if args.benchmark_ids else None)
        
        if results['status'] == 'success':
            print("\nPipeline completed successfully")
            return 0
        else:
            print(f"\nPipeline failed: {results.get('message', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
