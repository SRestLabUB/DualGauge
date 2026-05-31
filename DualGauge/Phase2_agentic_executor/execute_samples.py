#!/usr/bin/env python3

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import read_json, write_json, ensure_dir, get_model, ProgressLogger
from config.constants import (
    BENCHMARKS_DIR,
    EXPERIMENTS_DIR,
    DEFAULT_AGENT_MODEL,
    DEFAULT_WORKERS,
    DEFAULT_MAX_RETRIES,
)
from agent import execute_sample


LANGUAGE_DIRS = {"python", "javascript", "c", "cpp"}


def normalize_language_dir(language: str | None) -> str | None:
    """Normalize language aliases to canonical directory names."""
    if language == "js":
        return "javascript"
    return language


def parse_arguments():
    parser = argparse.ArgumentParser(description='Execute code samples and capture traces')
    
    parser.add_argument('--input', required=True, help='Path to generated samples directory')
    parser.add_argument('--output', default=None, help='Output directory (default: execution_results/<language>/<model>/)')
    parser.add_argument('--benchmark_id', type=int, default=None, help='Process a single benchmark ID')
    parser.add_argument('--benchmark_ids', type=int, nargs='+', default=None, help='Process specific benchmark IDs (e.g. --benchmark_ids 1 10 57)')
    parser.add_argument('--agent_model', default=DEFAULT_AGENT_MODEL, help=f'LLM model for agent (format: provider:model-name, e.g. openai:gpt-4o, vllm:Llama-3.1-8B)')
    parser.add_argument('--temperature', type=float, default=0.0, help='Sampling temperature (default: 0.0)')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help=f'Number of parallel workers')
    parser.add_argument('--sequential', action='store_true', help='Run sequentially with detailed stdout logging')
    parser.add_argument('--max_retries', type=int, default=DEFAULT_MAX_RETRIES, help=f'Max environment fix retries')
    parser.add_argument('--no_docker', action='store_true', help='Disable Docker (run locally)')
    parser.add_argument('--keep_workdir', action='store_true', help='Keep workspace directory after execution')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--skip_existing', action='store_true', help='Skip those that are done already')
    parser.add_argument('--timeout', type=int, default=60, help='Execution timeout in seconds')

    
    return parser.parse_args()


def resolve_input_path(input_path):
    """Normalize sample directory layouts to the current language/model layout."""
    if os.path.isdir(input_path):
        return input_path

    normalized = os.path.normpath(input_path)
    parts = normalized.split(os.sep)
    candidates = []

    # Legacy flat shape:
    #   BenchmarkingExperiments/generated_samples/<model>
    # Current shape:
    #   BenchmarkingExperiments/generated_samples/<language>/<model>
    if len(parts) >= 3:
        maybe_language = normalize_language_dir(parts[-3])
        maybe_model = parts[-1]
        if maybe_language in LANGUAGE_DIRS:
            candidates.append(os.path.join(*parts[:-2], maybe_model))
    elif len(parts) >= 1:
        maybe_model = parts[-1]
        for language_dir in sorted(LANGUAGE_DIRS):
            candidates.append(os.path.join(normalized, language_dir, maybe_model))
            candidates.append(os.path.join(*parts[:-1], language_dir, maybe_model))

    for candidate in candidates:
        if os.path.isdir(candidate):
            print(f"Input path not found: {input_path}")
            print(f"Using existing sample directory instead: {candidate}")
            return candidate

    raise FileNotFoundError(
        f"Generated samples directory not found: {input_path}\n"
        f"Expected current layout: BenchmarkingExperiments/generated_samples/<language>/<model>\n"
        f"Example for this repo: BenchmarkingExperiments/generated_samples/python/gpt-5-nano\n"
        f"If you deleted it, rerun Phase 1 to regenerate samples before running the executor."
    )


def extract_input_metadata(input_path):
    """Extract language/model names from the resolved generated-samples path."""
    normalized = os.path.normpath(input_path)
    parts = normalized.split(os.sep)
    model_name = parts[-1]
    language_dir = normalize_language_dir(parts[-2]) if len(parts) >= 2 else None
    if language_dir not in LANGUAGE_DIRS:
        language_dir = None
    return language_dir, model_name


def default_output_base(input_path: str, explicit_output: str | None = None) -> str:
    """Mirror the generated-samples layout under execution_results by default."""
    if explicit_output:
        return explicit_output

    resolved_input = resolve_input_path(input_path)
    language_dir, model_name = extract_input_metadata(resolved_input)
    if language_dir:
        return os.path.join(EXPERIMENTS_DIR, "execution_results", language_dir, model_name)
    return os.path.join(EXPERIMENTS_DIR, "execution_results", model_name)



def summarize_phase2_results(test_results):
    """Summarize Phase 2 execution/evidence stats. No correctness/pass claims."""
    summary = {
        "total_tests": len(test_results),
        "executed": 0,
        "evidence_collected": 0,
        "full_evidence_collected": 0,
        "trace_collected": 0,
        "coverage_collected": 0,
        "executor_failures": 0,
        "environment_failures": 0,
        "benchmark_data_failures": 0,
        "candidate_observable_failures": 0,
        "timeouts": 0,
        "oom": 0,
        "status_counts": {},
        "failure_origin_counts": {},
        "input_source_counts": {},
        "output_channel_counts": {},
    }
    for test in test_results:
        phase2 = test.get("phase2", {})
        status = phase2.get("execution_status", "unknown")
        origin = phase2.get("failure_origin") or "none"
        input_source = phase2.get("input_source", "unknown")

        summary["status_counts"][status] = summary["status_counts"].get(status, 0) + 1
        summary["failure_origin_counts"][origin] = summary["failure_origin_counts"].get(origin, 0) + 1
        summary["input_source_counts"][input_source] = summary["input_source_counts"].get(input_source, 0) + 1

        for channel in phase2.get("output_channels", []):
            summary["output_channel_counts"][channel] = summary["output_channel_counts"].get(channel, 0) + 1

        if phase2.get("executed"):
            summary["executed"] += 1
        if phase2.get("evidence_collected"):
            summary["evidence_collected"] += 1
        if phase2.get("full_evidence_collected"):
            summary["full_evidence_collected"] += 1
        if phase2.get("trace_collected"):
            summary["trace_collected"] += 1
        if phase2.get("coverage_collected"):
            summary["coverage_collected"] += 1

        if origin == "executor":
            summary["executor_failures"] += 1
        elif origin == "environment":
            summary["environment_failures"] += 1
        elif origin == "benchmark_data":
            summary["benchmark_data_failures"] += 1
        elif origin == "candidate":
            summary["candidate_observable_failures"] += 1

        if status == "candidate_timeout" or test.get("observed", {}).get("timeout"):
            summary["timeouts"] += 1
        if status == "candidate_oom":
            summary["oom"] += 1

    return summary


def format_phase2_summary_line(summary):
    total = summary.get("total_tests", 0)
    return (
        f"executed={summary.get('executed', 0)}/{total} "
        f"evidence={summary.get('evidence_collected', 0)}/{total} "
        f"full_evidence={summary.get('full_evidence_collected', 0)}/{total} "
        f"trace={summary.get('trace_collected', 0)} "
        f"coverage={summary.get('coverage_collected', 0)} "
        f"executor_err={summary.get('executor_failures', 0)} "
        f"env_err={summary.get('environment_failures', 0)} "
        f"candidate_err={summary.get('candidate_observable_failures', 0)} "
        f"timeouts={summary.get('timeouts', 0)} "
        f"oom={summary.get('oom', 0)}"
    )


def discover_samples(input_path, benchmark_id=None, benchmark_ids=None):
    samples = []
    supported_extensions = ['.py', '.c', '.cpp', '.cc', '.h', '.hpp', '.js']
    input_path = resolve_input_path(input_path)

    # Build allowed set from both --benchmark_id and --benchmark_ids
    allowed = None
    if benchmark_ids:
        allowed = set(benchmark_ids)
    if benchmark_id is not None:
        allowed = (allowed or set()) | {benchmark_id}

    for item in os.listdir(input_path):
        item_path = os.path.join(input_path, item)
        if not os.path.isdir(item_path) or not item.isdigit():
            continue

        bid = int(item)
        if allowed is not None and bid not in allowed:
            continue
        
        code_outputs_dir = os.path.join(item_path, "code_outputs")
        if not os.path.exists(code_outputs_dir):
            continue
        
        for filename in os.listdir(code_outputs_dir):
            ext = os.path.splitext(filename)[1]
            if ext not in supported_extensions:
                continue
            
            import re
            pattern = r'(\d+)_sample_(\d+)\.' + ext[1:] + r'$'
            match = re.match(pattern, filename)
            if match:
                file_bid = int(match.group(1))
                sample_num = int(match.group(2))
                if file_bid == bid: # and mapping.get(str(file_bid)) == 'api':
                    lang = "python" if ext == ".py" else ("cpp" if ext in [".cpp", ".cc"] else ("js" if ext == ".js" else "c"))
                    samples.append({
                        "sample_id": f"{bid}_sample_{sample_num}",
                        "benchmark_id": bid,
                        "sample_number": sample_num,
                        "file_path": os.path.join(code_outputs_dir, filename),
                        "language": lang
                    })
    
    samples.sort(key=lambda x: (x["benchmark_id"], x["sample_number"]))
    return samples


def discover_input_files(benchmark_id):
    benchmark_dir = os.path.join(BENCHMARKS_DIR, str(benchmark_id))
    if not os.path.exists(benchmark_dir):
        return None, {}
    
    input_files = {}
    for root, dirs, files in os.walk(benchmark_dir):
        for file in files:
            if file == "tests.json":
                continue
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, benchmark_dir)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    input_files[relative_path] = f.read()
            except Exception:
                pass
    
    return benchmark_dir, input_files


def load_test_cases(benchmark_id):
    test_file = os.path.join(BENCHMARKS_DIR, str(benchmark_id), "tests.json")
    if not os.path.exists(test_file):
        raise FileNotFoundError(f"Test file not found: {test_file}")
    return read_json(test_file)

def execute_sample_sequential(sample_info, args, model_name, benchmark_metadata, progress: ProgressLogger, setup_cache: dict = None, setup_cache_path: str = None):
    """Execute sample in sequential mode with stdout logging."""

    sample_id = sample_info["sample_id"]
    benchmark_id = sample_info["benchmark_id"]
    sample_number = sample_info["sample_number"]
    language = sample_info.get("language", "unknown")

    print(f"\n{'='*80}")
    print(f"Processing: {sample_id} ({language})")
    print(f"{'='*80}")

    n_tests = len(benchmark_metadata.get("fc_tests", [])) + len(benchmark_metadata.get("sec_tests", []))
    progress.log("START", sample=sample_id, lang=language, benchmark=benchmark_id, tests=n_tests)

    try:
        with open(sample_info["file_path"], 'r') as f:
            candidate_code = f.read()

        output_base = default_output_base(args.input, args.output)
        sample_dir = os.path.join(output_base, str(benchmark_id), f"sample_{sample_number}")
        ensure_dir(sample_dir)
        log_dir = sample_dir

        llm = get_model(args.agent_model, temperature=args.temperature)
        execution_started = datetime.now().isoformat()
        start_ts = time.time()

        cache_key = f"{benchmark_id}_{language}_sample_{sample_number}"
        cached_setup = (setup_cache or {}).get(cache_key)

        test_results, stats = execute_sample(
            sample_code=candidate_code,
            sample_filepath=sample_info["file_path"],
            fc_test_cases=benchmark_metadata["fc_tests"],
            sec_test_cases=benchmark_metadata["sec_tests"],
            input_files=benchmark_metadata["input_files"],
            llm=llm,
            use_docker=not args.no_docker,
            timeout=args.timeout,
            max_retries=args.max_retries,
            log_dir=log_dir,
            progress_callback=None,
            workdir_base=None,
            keep_workdir=args.keep_workdir,
            benchmark_metadata=benchmark_metadata,
            cached_setup=cached_setup,
        )
        end_ts = time.time()
        execution_finished = datetime.now().isoformat()

        # Persist setup to cache if it was freshly inferred
        if setup_cache is not None and cache_key not in setup_cache and stats.get("last_setup"):
            setup_cache[cache_key] = stats["last_setup"]
            if setup_cache_path:
                try:
                    write_json(setup_cache_path, setup_cache)
                except Exception:
                    pass

        phase2_summary = summarize_phase2_results(test_results)
        timed_out = phase2_summary["timeouts"]
        oom = phase2_summary["oom"]
        total_elapsed = round(end_ts - start_ts, 2)

        final_result = {
            "metadata": {
                "sample_id": sample_id,
                "llm_name": model_name,
                "program_number": sample_number,
                "candidate_code": candidate_code,
                "language": language,
                "prompt": benchmark_metadata.get("prompt", ""),
                "execution_timestamp": datetime.now().isoformat(),
                "execution_start_time": execution_started,
                "execution_end_time": execution_finished,
                "execution_elapsed_seconds": round(end_ts - start_ts, 6)
            },
            "test_results": test_results,
            "summary": phase2_summary
        }

        result_file = os.path.join(sample_dir, "result.json")
        write_json(result_file, final_result)

        cache_note = " (cached setup)" if cached_setup else ""
        progress.log("END", sample=sample_id, lang=language,
                     status="success", executed=phase2_summary["executed"],
                     evidence_collected=phase2_summary["evidence_collected"],
                     executor_failures=phase2_summary["executor_failures"],
                     environment_failures=phase2_summary["environment_failures"],
                     candidate_observable_failures=phase2_summary["candidate_observable_failures"],
                     timed_out=timed_out, oom=oom, total_tests=len(test_results),
                     llm_calls=stats["llm_calls"], setup_elapsed=f"{stats['setup_elapsed']}s",
                     total_elapsed=f"{total_elapsed}s")

        llm_breakdown = stats.get("llm_calls_by_type", {})
        llm_breakdown_str = "  ".join(f"{k}={v}" for k, v in sorted(llm_breakdown.items()))
        print(f"  ✓ Results: {format_phase2_summary_line(phase2_summary)}  llm_calls={stats['llm_calls']}({llm_breakdown_str})  elapsed={total_elapsed}s{cache_note}")
        print(f"  Files:")
        print(f"    - {result_file}")
        print(f"    - {os.path.join(sample_dir, 'execution.log')}")
        if args.keep_workdir:
            print(f"    - {os.path.join(sample_dir, 'workspace/')}")

        return {
            "sample_id": sample_id,
            "status": "success",
            "phase2_summary": phase2_summary,
            "executed": phase2_summary["executed"],
            "evidence_collected": phase2_summary["evidence_collected"],
            "llm_calls_by_type": stats.get("llm_calls_by_type", {}),
            "total": len(test_results),
            "timed_out": timed_out,
            "llm_calls": stats["llm_calls"],
            "total_elapsed": total_elapsed,
        }

    except Exception as e:
        total_elapsed = round(time.time() - (start_ts if 'start_ts' in dir() else time.time()), 2)
        print(f"\n  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        progress.log("END", sample=sample_id, lang=language,
                     status="error", error=str(e)[:120], total_elapsed=f"{total_elapsed}s")
        return {
            "sample_id": sample_id,
            "status": "error",
            "error": str(e)
        }


def execute_sample_parallel(sample_info, args, model_name, benchmark_metadata, progress_log_path: str, setup_cache: dict = None, setup_cache_path: str = None):
    """Execute sample in parallel mode."""

    sample_id = sample_info["sample_id"]
    benchmark_id = sample_info["benchmark_id"]
    sample_number = sample_info["sample_number"]
    language = sample_info.get("language", "unknown")

    # Each worker gets its own ProgressLogger pointing at the shared file (append-safe)
    progress = ProgressLogger(progress_log_path)

    n_tests = len(benchmark_metadata.get("fc_tests", [])) + len(benchmark_metadata.get("sec_tests", []))
    progress.log("START", sample=sample_id, lang=language, benchmark=benchmark_id, tests=n_tests)

    execution_log = {
        "sample_id": sample_id,
        "benchmark_id": benchmark_id,
        "language": language,
        "start_time": datetime.now().isoformat(),
    }
    start_ts = time.time()

    try:
        with open(sample_info["file_path"], 'r') as f:
            candidate_code = f.read()

        output_base = default_output_base(args.input, args.output)
        sample_dir = os.path.join(output_base, str(benchmark_id), f"sample_{sample_number}")
        ensure_dir(sample_dir)
        log_dir = sample_dir

        llm = get_model(args.agent_model, temperature=args.temperature)
        execution_started = datetime.now().isoformat()

        cache_key = f"{benchmark_id}_{language}_sample_{sample_number}"
        cached_setup = (setup_cache or {}).get(cache_key)

        test_results, stats = execute_sample(
            sample_code=candidate_code,
            sample_filepath=sample_info["file_path"],
            fc_test_cases=benchmark_metadata["fc_tests"],
            sec_test_cases=benchmark_metadata["sec_tests"],
            input_files=benchmark_metadata["input_files"],
            llm=llm,
            use_docker=not args.no_docker,
            timeout=args.timeout,
            max_retries=args.max_retries,
            log_dir=log_dir,
            keep_workdir=args.keep_workdir,
            benchmark_metadata=benchmark_metadata,
            cached_setup=cached_setup,
        )
        end_ts = time.time()
        execution_finished = datetime.now().isoformat()

        # Persist newly inferred setup to cache file (best-effort, parallel writes)
        if setup_cache_path and cache_key not in (setup_cache or {}) and stats.get("last_setup"):
            try:
                existing = {}
                if os.path.exists(setup_cache_path):
                    existing = read_json(setup_cache_path)
                existing[cache_key] = stats["last_setup"]
                write_json(setup_cache_path, existing)
            except Exception:
                pass

        phase2_summary = summarize_phase2_results(test_results)
        timed_out = phase2_summary["timeouts"]
        oom = phase2_summary["oom"]
        total_elapsed = round(end_ts - start_ts, 2)

        final_result = {
            "metadata": {
                "sample_id": sample_id,
                "llm_name": model_name,
                "program_number": sample_number,
                "candidate_code": candidate_code,
                "language": language,
                "prompt": benchmark_metadata.get("prompt", ""),
                "execution_timestamp": datetime.now().isoformat(),
                "execution_start_time": execution_started,
                "execution_end_time": execution_finished,
                "execution_elapsed_seconds": round(end_ts - start_ts, 6)
            },
            "test_results": test_results,
            "summary": phase2_summary
        }

        result_file = os.path.join(sample_dir, "result.json")
        write_json(result_file, final_result)

        progress.log("END", sample=sample_id, lang=language,
                     status="success", executed=phase2_summary["executed"],
                     evidence_collected=phase2_summary["evidence_collected"],
                     executor_failures=phase2_summary["executor_failures"],
                     environment_failures=phase2_summary["environment_failures"],
                     candidate_observable_failures=phase2_summary["candidate_observable_failures"],
                     timed_out=timed_out, oom=oom, total_tests=len(test_results),
                     llm_calls=stats["llm_calls"], setup_elapsed=f"{stats['setup_elapsed']}s",
                     total_elapsed=f"{total_elapsed}s")

        execution_log.update({
            "status": "success",
            "end_time": datetime.now().isoformat(),
            "phase2_summary": phase2_summary,
            "executed": phase2_summary["executed"],
            "evidence_collected": phase2_summary["evidence_collected"],
            "total": len(test_results),
            "timed_out": timed_out,
            "llm_calls": stats["llm_calls"],
            "llm_calls_by_type": stats.get("llm_calls_by_type", {}),
            "total_elapsed": total_elapsed,
        })
        return execution_log

    except Exception as e:
        import traceback
        total_elapsed = round(time.time() - start_ts, 2)
        progress.log("END", sample=sample_id, lang=language,
                     status="error", error=str(e)[:120], total_elapsed=f"{total_elapsed}s")
        execution_log.update({
            "status": "error",
            "end_time": datetime.now().isoformat(),
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return execution_log


def main():
    args = parse_arguments()
    
    mode = "SEQUENTIAL" if args.sequential else "PARALLEL"
    
    print("="*80)
    print(f"Executor Component - {mode} Mode")
    print("="*80)
    
    samples = discover_samples(args.input, args.benchmark_id, args.benchmark_ids)

    if not samples:
        print("ERROR: No samples found")
        sys.exit(1)
    model_name = os.path.basename(args.input.rstrip('/'))
    print(f"Model: {model_name}")
    if args.skip_existing:
        final_samples = []
        output_base = default_output_base(args.input, args.output)
        for sample in samples:
            bid = sample["benchmark_id"]
            sample_number = sample["sample_number"]
            sample_dir = os.path.join(output_base, str(bid), f"sample_{sample_number}", "result.json")
            if args.skip_existing and os.path.exists(sample_dir):
                print(f"Skipping existing sample: {sample['sample_id']}")
            else:
                final_samples.append(sample)
        samples = final_samples
    print(f"Samples: {len(samples)}")
    python_count = sum(1 for s in samples if s.get("language") == "python")
    c_count = sum(1 for s in samples if s.get("language") in ["c", "cpp"])
    print(f"  Python: {python_count}")
    print(f"  C/C++: {c_count}")
    js_count = sum(1 for s in samples if s.get("language") == "js")
    print(f"  JavaScript: {js_count}")
    benchmarks = {}
    for sample in samples:
        bid = sample["benchmark_id"]
        if bid not in benchmarks:
            benchmarks[bid] = []
        benchmarks[bid].append(sample)
    
    benchmark_metadata = {}
    for bid in benchmarks.keys():
        test_data = load_test_cases(bid)
        _, input_files = discover_input_files(bid)

        fc_tests = test_data.get("fc_tests", [])
        sec_tests = test_data.get("sec_tests", [])
        prompt = test_data.get("prompt", "")
        implementation_details = test_data.get("implementation_details", "")
        service_setup = test_data.get("service_setup", {})

        benchmark_metadata[bid] = {
            "fc_tests": fc_tests,
            "sec_tests": sec_tests,
            "input_files": input_files,
            "prompt": prompt,
            "implementation_details": implementation_details,
            "service_setup": service_setup,
            "benchmark_id": bid
        }

    output_base = default_output_base(args.input, args.output)
    ensure_dir(output_base)
    progress = ProgressLogger(os.path.join(output_base, "execution_progress.log"))

    # Load persisted setup cache: keyed on "{benchmark_id}_{language}"
    # Saves one LLM call per sample on re-runs.
    setup_cache_path = os.path.join(output_base, "setup_cache.json")
    setup_cache = {}
    if os.path.exists(setup_cache_path):
        try:
            setup_cache = read_json(setup_cache_path)
            print(f"Loaded setup cache: {len(setup_cache)} entries from {setup_cache_path}")
        except Exception:
            setup_cache = {}

    start_time = time.time()

    if args.sequential:
        results = []
        for sample in tqdm(samples, desc="Executing Samples"):
            bid = sample["benchmark_id"]
            result = execute_sample_sequential(sample, args, model_name, benchmark_metadata[bid], progress, setup_cache, setup_cache_path)
            results.append(result)

    else:
        log_file = os.path.join(output_base, "execution_log.json")

        print(f"\nParallel execution with {args.workers} workers")
        print(f"Detailed logs: {log_file}")
        print(f"Progress log:  {progress.log_path}\n")

        progress_log_path = progress.log_path
        all_logs = []
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {}
            for sample in samples:
                bid = sample["benchmark_id"]
                future = executor.submit(
                    execute_sample_parallel,
                    sample, args, model_name, benchmark_metadata[bid], progress_log_path,
                    setup_cache, setup_cache_path
                )
                futures[future] = sample

            for future in tqdm(as_completed(futures), total=len(futures), desc="Executing Samples"):
                try:
                    log_entry = future.result()
                    all_logs.append(log_entry)

                    sample_id = log_entry['sample_id']
                    lang = log_entry.get('language', '?')
                    elapsed_s = log_entry.get('total_elapsed', '?')
                    llm_c = log_entry.get('llm_calls', '?')
                    if log_entry['status'] == 'success':
                        print(f"✓ {sample_id} ({lang}): {format_phase2_summary_line(log_entry.get('phase2_summary', {}))}  llm_calls={llm_c}  elapsed={elapsed_s}s")
                    else:
                        print(f"✗ {sample_id} ({lang}): {log_entry.get('error', 'unknown error')}")

                except Exception as e:
                    sample = futures[future]
                    print(f"✗ {sample['sample_id']}: worker exception - {e}")

        write_json(log_file, {
            "execution_mode": "parallel",
            "timestamp": datetime.now().isoformat(),
            "total_samples": len(samples),
            "logs": all_logs
        })

        results = all_logs

    elapsed = time.time() - start_time
    successful = sum(1 for r in results if r.get("status") == "success")

    # Aggregate phase2 stats across all samples
    agg = {
        "total_tests": 0, "executed": 0, "evidence_collected": 0,
        "full_evidence_collected": 0, "trace_collected": 0, "coverage_collected": 0,
        "executor_failures": 0, "environment_failures": 0,
        "candidate_observable_failures": 0, "timeouts": 0, "oom": 0,
    }
    agg_llm_by_type = {}
    for r in results:
        ps = r.get("phase2_summary") or {}
        for k in agg:
            agg[k] += ps.get(k, 0)
        for k, v in (r.get("llm_calls_by_type") or {}).items():
            agg_llm_by_type[k] = agg_llm_by_type.get(k, 0) + v

    slowest = sorted(
        [(r.get("total_elapsed", 0), r.get("sample_id", "?")) for r in results if r.get("status") == "success"],
        reverse=True
    )[:5]
    most_llm = sorted(
        [(r.get("llm_calls", 0), r.get("sample_id", "?")) for r in results if r.get("status") == "success"],
        reverse=True
    )[:5]

    t = agg["total_tests"]
    summary_lines = [
        f"Total samples: {len(results)}  Success: {successful}  Error: {len(results)-successful}",
        f"Total elapsed: {elapsed:.1f}s  Avg per sample: {elapsed/max(len(results),1):.1f}s",
        f"Total tests: {t}",
        f"  executed:            {agg['executed']}/{t}",
        f"  evidence_collected:  {agg['evidence_collected']}/{t}",
        f"  full_evidence:       {agg['full_evidence_collected']}/{t}  (requires trace/coverage)",
        f"  trace_collected:     {agg['trace_collected']}/{t}",
        f"  coverage_collected:  {agg['coverage_collected']}/{t}",
        f"  executor_failures:   {agg['executor_failures']}",
        f"  environment_failures:{agg['environment_failures']}",
        f"  candidate_errors:    {agg['candidate_observable_failures']}",
        f"  timeouts:            {agg['timeouts']}",
        f"  oom:                 {agg['oom']}",
    ]
    if slowest:
        summary_lines.append("Slowest: " + "  ".join(f"{s} ({e}s)" for e, s in slowest))
    if most_llm:
        summary_lines.append("Most LLM calls: " + "  ".join(f"{s} ({c} calls)" for c, s in most_llm))
    progress.summary(summary_lines)

    print("\n" + "="*80)
    print(f"Execution Complete ({mode})")
    print(f"  Samples:   {successful}/{len(results)} succeeded")
    print(f"  Time:      {elapsed:.1f}s")
    print(f"\n  Test-level stats (across all samples):")
    print(f"    executed:           {agg['executed']}/{t}")
    print(f"    evidence:           {agg['evidence_collected']}/{t}")
    print(f"    full_evidence:      {agg['full_evidence_collected']}/{t}  ← trace/coverage required")
    print(f"    trace_collected:    {agg['trace_collected']}/{t}")
    print(f"    coverage_collected: {agg['coverage_collected']}/{t}")
    print(f"    executor_failures:  {agg['executor_failures']}")
    print(f"    env_failures:       {agg['environment_failures']}")
    print(f"    candidate_errors:   {agg['candidate_observable_failures']}")
    print(f"    timeouts:           {agg['timeouts']}")
    print(f"    oom:                {agg['oom']}")
    if agg_llm_by_type:
        total_llm = sum(agg_llm_by_type.values())
        print(f"\n  LLM calls by type (total={total_llm}):")
        for ctype, count in sorted(agg_llm_by_type.items(), key=lambda x: -x[1]):
            print(f"    {ctype:<35} {count}")
    print(f"  Progress log: {progress.log_path}")
    print("="*80)


if __name__ == "__main__":
    main()
