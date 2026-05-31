import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import traceback
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.constants import NUM_OF_WORKERS, BENCHMARKS_DIR, EXPERIMENTS_DIR
from utils import save_text, log_message, extract_code_blocks, determine_file_extension, read_item_json, get_model, determine_language_from_text, ProgressLogger, load_generation_profile

### -----------------------------
### Argument Parsing
### -----------------------------

def get_args():
    parser = argparse.ArgumentParser(description="Generate and save model completions for benchmark prompts.")
    parser.add_argument('--model', type=str, required=True, help='Output/model label used for experiment folders (e.g., gpt-4, qwen3-32b)')
    parser.add_argument('--model_spec', type=str, default=None, help='Optional provider/model spec used for inference (e.g., openai:gpt-5-high, vllm:Qwen/Qwen3-32B). Defaults to --model.')
    parser.add_argument('--input_dir', type=str, default=BENCHMARKS_DIR, help='Directory containing numbered item folders')
    parser.add_argument('--output_dir', type=str, default=os.path.join(EXPERIMENTS_DIR, 'generated_samples'), help='Base output directory')
    parser.add_argument('--k', type=int, default=1, help='Number of samples to generate per prompt')
    parser.add_argument('--no_parallel', action='store_true', help='Disable parallelism')
    parser.add_argument('--skip_existing', action='store_true', help='Skip prompts that already have generated outputs')
    parser.add_argument('--language', type=str, default=None, help='Fallback language when benchmark has no implementation_details (e.g. python, javascript, c, cpp)')
    parser.add_argument('--benchmark_ids', type=int, nargs='+', default=None, help='Only process these benchmark IDs (e.g. --benchmark_ids 1 10 57)')
    parser.add_argument('--temperature', type=float, default=0.0, help='Sampling temperature (default: 0.0)')
    parser.add_argument('--include_requirements', action='store_true', help='Include the shared Requirements section in the generation prompt')
    return parser.parse_args()


def extension_to_language_bucket(ext: str | None) -> str:
    """Map file extensions to stable directory names."""
    if ext == '.py':
        return 'python'
    if ext == '.js':
        return 'javascript'
    if ext == '.c':
        return 'c'
    if ext in {'.cpp', '.cc', '.hpp', '.h'}:
        return 'cpp'
    return 'unknown'


def infer_language_bucket(args, item) -> str:
    """Choose the top-level output folder for a sample run."""
    if args.language:
        ext = determine_language_from_text(args.language)
        return extension_to_language_bucket(ext)

    original_impl = item.get('implementation_details', item.get('implementation_detail', ''))
    ext = determine_language_from_text(original_impl)
    return extension_to_language_bucket(ext)

### -----------------------------
### Core Logic
### -----------------------------

def generate_sample(model, item, sample_idx, args, log_path, progress: ProgressLogger):
    """Generate a single completion for one item and save outputs."""
    item_id = str(item['benchmark_id'])
    lang = args.language or item.get('implementation_details', '')[:30].strip()
    t_start = time.time()
    progress.log("START", benchmark=item_id, sample=sample_idx, lang=lang)

    try:
        language_bucket = infer_language_bucket(args, item)

        base_out_dir = os.path.join(args.output_dir, language_bucket, args.model, item_id)
        raw_dir = os.path.join(base_out_dir, 'raw_outputs')
        code_dir = os.path.join(base_out_dir, 'code_outputs')
        raw_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}.txt")
        code_base_path = os.path.join(code_dir, f"{item_id}_sample_{sample_idx}")

        if args.skip_existing and os.path.exists(raw_path):
            progress.log("SKIP", benchmark=item_id, sample=sample_idx, reason="already_exists")
            return

        original_impl = item.get('implementation_details', item.get('implementation_detail', ''))

        # --language always overrides implementation_details for both prompt and extension.
        # Without --language, use the benchmark's own implementation_details.
        if args.language:
            impl_details = f"Write the code in {args.language.capitalize()}."
            ext = determine_language_from_text(args.language)
        else:
            impl_details = original_impl
            ext = determine_language_from_text(original_impl)

        impl_section = f"Implementation Details:\n{impl_details}\n\n" if impl_details else ""

        # Always require a runnable entry point so the executor can run the code directly.
        lang_lower = (args.language or "").lower()
        is_c_cpp = lang_lower in ("c", "cpp", "c++")
        if is_c_cpp:
            lang_requirement = (
                "\n- IMPORTANT: Always include a complete `main()` function. "
                "If the task is a server (HTTP, socket, etc.), implement the server with its natural entry point in `main()`. "
                "If the task is a function or library, implement the function AND add a `main()` that "
                "reads input from stdin in whatever format is natural for the function's parameters, "
                "calls the function, and prints the result to stdout. "
                "The binary must compile and run standalone without any external driver."
            )
        else:
            lang_requirement = ""

        prompt_text = (
            f"You are an expert software developer.\n\n"
            f"Task:\n{item['prompt']}\n\n"
            f"{impl_section}"
        )
        if args.include_requirements:
            prompt_text += (
                f"Requirements:\n"
                f"- Output ONLY the code block.\n"
                f"- Do not include any explanations.\n"
                f"- Follow the task and implementation details faithfully.\n"
                f"- Do not invent or force an artificial input/output interface unless the task explicitly requires it.\n"
                f"- Produce complete code that is natural for the requested task (for example, a function, script, or server route, depending on the prompt)."
                f"{lang_requirement}"
            )

        t_llm = time.time()
        reasoning_trace = None
        api_error = None
        event_trace = None
        stderr_trace = None
        if hasattr(model, "generate_with_metadata"):
            result = model.generate_with_metadata(prompt_text)
            completion = result.get("content", "")
            raw_completion = result.get("raw_content", completion)
            reasoning_trace = result.get("reasoning")
            event_trace = result.get("events")
            stderr_trace = result.get("stderr")
            api_error = result.get("error")
        else:
            completion = model.generate(prompt_text)
            raw_completion = completion
        llm_elapsed = round(time.time() - t_llm, 2)

        # Make API failures visible in the progress log instead of being
        # buried as an empty completion.
        if completion == "ERROR" or api_error:
            err_msg = (api_error or "all retries exhausted")[:200]
            log_message(log_path, f"{item_id}_sample_{sample_idx}: API_ERROR {err_msg}")
            # Save whatever diagnostic output the model captured so failures
            # can be inspected without re-running.
            if event_trace or stderr_trace:
                os.makedirs(raw_dir, exist_ok=True)
                if event_trace:
                    save_text(event_trace, os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_events.jsonl"))
                if stderr_trace:
                    save_text(stderr_trace, os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_stderr.txt"))
            progress.log("END", benchmark=item_id, sample=sample_idx,
                         status="api_error", error=err_msg[:120],
                         total_elapsed=f"{round(time.time() - t_start, 2)}s")
            return

        # Extract code
        code_blocks = extract_code_blocks(completion)

        progress.log("LLM", benchmark=item_id, sample=sample_idx,
                     elapsed=f"{llm_elapsed}s", code_blocks=len(code_blocks))

        if code_blocks:
            combined_code = "\n\n".join(code_blocks)

            if not ext:
                ext = determine_file_extension(combined_code)

            if not ext:
                ext = ".txt"
                log_message(log_path, f"{item_id}_sample_{sample_idx}: Could not determine code language. Saved as .txt")

            language_bucket = extension_to_language_bucket(ext)
            base_out_dir = os.path.join(args.output_dir, language_bucket, args.model, item_id)
            raw_dir = os.path.join(base_out_dir, 'raw_outputs')
            code_dir = os.path.join(base_out_dir, 'code_outputs')
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(code_dir, exist_ok=True)
            raw_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}.txt")
            code_base_path = os.path.join(code_dir, f"{item_id}_sample_{sample_idx}")
            save_text(raw_completion, raw_path)
            if reasoning_trace:
                reasoning_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_reasoning.txt")
                save_text(reasoning_trace, reasoning_path)
            if event_trace:
                events_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_events.jsonl")
                save_text(event_trace, events_path)
            if stderr_trace:
                stderr_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_stderr.txt")
                save_text(stderr_trace, stderr_path)
            save_text(combined_code, code_base_path + ext)

            if len(code_blocks) > 1:
                log_message(log_path, f"{item_id}_sample_{sample_idx}: Multiple code blocks found, combined into one file.")

            status = "success"
        else:
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(code_dir, exist_ok=True)
            save_text(raw_completion, raw_path)
            if reasoning_trace:
                reasoning_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_reasoning.txt")
                save_text(reasoning_trace, reasoning_path)
            if event_trace:
                events_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_events.jsonl")
                save_text(event_trace, events_path)
            if stderr_trace:
                stderr_path = os.path.join(raw_dir, f"{item_id}_sample_{sample_idx}_stderr.txt")
                save_text(stderr_trace, stderr_path)
            save_text("", code_base_path + ".txt")
            ext = ".txt"
            status = "no_code_block"

        total_elapsed = round(time.time() - t_start, 2)
        progress.log("END", benchmark=item_id, sample=sample_idx,
                     status=status, ext=ext, llm_elapsed=f"{llm_elapsed}s",
                     total_elapsed=f"{total_elapsed}s")

    except Exception as e:
        error_trace = traceback.format_exc()
        log_message(log_path, f"ERROR processing {item_id}_sample_{sample_idx}: {e}\n{error_trace}")
        total_elapsed = round(time.time() - t_start, 2)
        progress.log("END", benchmark=item_id, sample=sample_idx,
                     status="error", error=str(e)[:120], total_elapsed=f"{total_elapsed}s")


### -----------------------------
### Entry Point
### -----------------------------

def main():
    args = get_args()

    # Configure logging so retry/error messages from the wrappers reach
    # stderr in real time (instead of being silently swallowed).
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    generation_profile = load_generation_profile(args.model)

    # Resolve the API/serve model name. Order of precedence:
    #   1. --model_spec (explicit CLI override)
    #   2. <provider>:<model_id> built from models.yaml
    #   3. --model (legacy bare name)
    if args.model_spec:
        resolved_spec = args.model_spec
    elif generation_profile.get("provider") and generation_profile.get("model_id"):
        resolved_spec = f"{generation_profile['provider']}:{generation_profile['model_id']}"
    else:
        resolved_spec = args.model

    model = get_model(
        resolved_spec,
        temperature=args.temperature,
        max_tokens=generation_profile.get("max_tokens"),
        extra_body=generation_profile.get("extra_body"),
        system_prompt_prefix=generation_profile.get("system_prompt_prefix"),
        thinking=generation_profile.get("thinking"),
        reasoning_effort=generation_profile.get("reasoning_effort"),
        output_config=generation_profile.get("output_config"),
    )

    run_language_bucket = extension_to_language_bucket(determine_language_from_text(args.language)) if args.language else "auto"
    out_base = os.path.join(args.output_dir, run_language_bucket, args.model)
    os.makedirs(out_base, exist_ok=True)

    log_path = os.path.join(out_base, "generation_log.txt")
    progress = ProgressLogger(os.path.join(out_base, "generation_progress.log"))

    # Collect all item.json files
    allowed_ids = set(args.benchmark_ids) if args.benchmark_ids else None
    items = []
    for sample in os.listdir(args.input_dir):
        if not sample.isdigit():
            continue
        if allowed_ids and int(sample) not in allowed_ids:
            continue
        item_path = os.path.join(args.input_dir, sample, "tests.json")
        if os.path.exists(item_path):
            items.append(read_item_json(item_path))

    print(f"Found {len(items)} item.json files.")

    tasks = [(item, i) for item in items for i in range(args.k)]
    total_tasks = len(tasks)

    t_run_start = time.time()
    results = {"success": 0, "no_code_block": 0, "skip": 0, "error": 0}
    llm_times = []

    def _wrapped(item, i):
        generate_sample(model, item, i, args, log_path, progress)

    if args.no_parallel:
        for item, i in tqdm(tasks, desc="Generating Samples", total=total_tasks):
            _wrapped(item, i)
    else:
        with ThreadPoolExecutor(max_workers=NUM_OF_WORKERS) as executor:
            futures = [executor.submit(_wrapped, item, i) for item, i in tasks]
            for _ in tqdm(as_completed(futures), total=len(futures), desc="Generating Samples"):
                pass

    total_elapsed = round(time.time() - t_run_start, 1)

    # Read progress log to build summary stats
    success = no_code = errors = skips = 0
    slowest = []
    try:
        with open(progress.log_path, 'r') as f:
            for line in f:
                if "END" in line:
                    if "status=success" in line:
                        success += 1
                    elif "status=no_code_block" in line:
                        no_code += 1
                    elif "status=error" in line:
                        errors += 1
                if "SKIP" in line:
                    skips += 1
                if "total_elapsed" in line and "END" in line:
                    try:
                        elapsed_str = [p for p in line.split() if p.startswith("total_elapsed=")][0]
                        elapsed_val = float(elapsed_str.split("=")[1].rstrip("s"))
                        bm = [p for p in line.split() if p.startswith("benchmark=")][0].split("=")[1]
                        smp = [p for p in line.split() if p.startswith("sample=")][0].split("=")[1]
                        slowest.append((elapsed_val, f"{bm}_sample_{smp}"))
                    except Exception:
                        pass
    except Exception:
        pass

    slowest.sort(reverse=True)
    summary = [
        f"Total tasks: {total_tasks}  Success: {success}  No code block: {no_code}  Error: {errors}  Skipped: {skips}",
        f"Total elapsed: {total_elapsed}s",
    ]
    if slowest:
        top = "  ".join(f"{s} ({e}s)" for e, s in slowest[:5])
        summary.append(f"Slowest: {top}")

    progress.summary(summary)
    print(f"All samples generated. Log: {log_path}")
    print(f"Progress log: {progress.log_path}")


if __name__ == "__main__":
    main()
