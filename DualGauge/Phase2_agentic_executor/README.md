# Phase 2: Agentic Executor

Runs each generated code sample against its benchmark's test cases inside an isolated Docker container, using an autonomous self-correction loop to handle environment and setup failures.

## Overview

Phase 2 does not evaluate correctness — it collects execution *evidence*. For each test case, it produces the actual program output, stdout/stderr, coverage, and traces. Phase 3 then judges whether that evidence satisfies the expected behavior.

### Key Features

- **Agentic Self-Correction**: Automatically fixes missing dependencies, compilation errors, and runtime environment issues without modifying the candidate code itself.
- **Sandboxed Execution**: All code runs inside isolated Docker containers.
- **Dual-Mode Execution**: Handles both client-mode programs (stdin/stdout) and server-mode programs (HTTP servers, sockets).
- **Polyglot Support**: Python, C/C++, and JavaScript (Node.js).
- **Setup Caching**: Saves inferred environment setup per benchmark to speed up reruns.

## Usage

Run from the repository root:

```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/<language>/<model> [options]
```

### Examples

**Standard parallel run:**
```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/python/gpt-4.1
```

**Debug a single benchmark sequentially (no Docker):**
```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/python/gpt-4.1 \
  --benchmark_id 42 --sequential --no_docker
```

**Run specific benchmarks only:**
```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/python/gpt-4.1 \
  --benchmark_ids 1 5 42
```

**Resume an interrupted run:**
```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/python/gpt-4.1 \
  --skip_existing
```

## Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--input` | **Required** | Path to generated samples directory (e.g. `BenchmarkingExperiments/generated_samples/python/gpt-4.1`). |
| `--output` | Derived from `--input` | Output directory. Defaults to `BenchmarkingExperiments/execution_results/<language>/<model>`. |
| `--agent_model` | `gpt-5-nano` | LLM used for the agentic loop (setup inference, error classification, fix generation). Format: `provider:model-id`. |
| `--workers` | `100` | Number of parallel workers. |
| `--max_retries` | `3` | Maximum self-correction attempts per sample. |
| `--timeout` | `60` | Execution timeout in seconds per test case. |
| `--benchmark_id` | `None` | Process a single benchmark ID. |
| `--benchmark_ids` | `None` | Process specific benchmark IDs (e.g. `--benchmark_ids 1 10 57`). |
| `--sequential` | `False` | Run one sample at a time with detailed stdout logging (good for debugging). |
| `--no_docker` | `False` | Run locally instead of in Docker. **Only use for trusted code.** |
| `--skip_existing` | `False` | Skip samples that already have a `result.json`. |
| `--keep_workdir` | `False` | Preserve the sandbox workspace directory after execution. |

## The Agentic Loop

For each test case the agent:

1. **Infers setup** — inspects the candidate code to determine the execution mode (client vs. server) and required environment (imports, compile flags).
2. **Generates a harness** — writes a runner script that invokes the code and captures stdout, stderr, coverage, and traces.
3. **Executes** — runs the harness inside a Docker container against the test input.
4. **Classifies failures** — if execution fails, classifies the cause:
   - **Environment failure** (missing package, compile error): generates a fix script (e.g. `pip install`) and retries.
   - **Harness failure** (bad runner script): regenerates the harness and retries.
   - **Candidate failure** (the code itself crashed or produced wrong output): records as-is. The candidate code is never modified.
5. **Records evidence** — saves all observed outputs, traces, and failure metadata to `result.json`.

## Output Structure

```
BenchmarkingExperiments/execution_results/
└── <language>/
    └── <model>/
        ├── execution_progress.log
        ├── setup_cache.json         # cached environment setup per benchmark
        └── <benchmark_id>/
            └── sample_<n>/
                ├── result.json      # per-test execution evidence and summary
                └── execution.log    # agent activity log
```

### `result.json` structure

- `metadata` — model name, language, candidate code, prompt, timestamps
- `test_results` — per-test list with: execution status, observed output, failure origin (`executor` / `environment` / `benchmark_data` / `candidate`), output channels, trace
- `summary` — aggregate counts: executed, evidence collected, executor/environment/candidate failures, timeouts, OOM
