# Phase 3: LLM Evaluator

Reads Phase 2 execution results and issues Pass/Fail verdicts for each test case using an LLM-as-a-Judge.

## Overview

Phase 2 tells us *what happened* when the code ran. Phase 3 tells us *whether that was correct*. Rather than exact string matching, the evaluator reasons semantically — understanding that `"403 Forbidden"` and `"Access Denied"` are functionally equivalent, or that a function that correctly rejects null input satisfies a security test even if the error message differs.

### Key Features

- **Semantic Evaluation**: LLM judge reasons about intent rather than string equality.
- **Knowledge Gap Resolution**: If the candidate code uses an obscure library the evaluator doesn't recognize, a stronger Resolver model fetches context before judging.
- **Dual-Model Architecture**: A fast Evaluator model handles bulk judgments; a stronger Resolver handles edge cases.
- **Checkpointing**: Skips already-evaluated samples so runs can be resumed safely.

## Usage

Run from the repository root:

```bash
python3 DualGauge/Phase3_llm_evaluator/evaluate_samples.py \
  --log-dir BenchmarkingExperiments/execution_results/<language>/<model> [options]
```

### Examples

**Standard run:**
```bash
python3 DualGauge/Phase3_llm_evaluator/evaluate_samples.py \
  --log-dir BenchmarkingExperiments/execution_results/python/gpt-4.1
```

**Specify evaluator and resolver models:**
```bash
python3 DualGauge/Phase3_llm_evaluator/evaluate_samples.py \
  --log-dir BenchmarkingExperiments/execution_results/python/gpt-4.1 \
  --evaluator-model claude-haiku-4-5 \
  --resolver-model claude-sonnet-4-5
```

**Custom output directory:**
```bash
python3 DualGauge/Phase3_llm_evaluator/evaluate_samples.py \
  --log-dir BenchmarkingExperiments/execution_results/python/gpt-4.1 \
  --output-dir BenchmarkingExperiments/evaluation_results/python/gpt-4.1
```

## Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--log-dir` | `BenchmarkingExperiments/execution_results` | Input directory containing Phase 2 `result.json` files. |
| `--output-dir` | Derived from `--log-dir` | Output directory. `execution_results` is replaced with `evaluation_results` in the path if omitted. |
| `--evaluator-model` | `gpt-4o` | Model for standard Pass/Fail judgment. |
| `--resolver-model` | `gpt-4o` | Model for resolving unknown libraries/symbols before evaluation. |
| `--model` | `None` | Shorthand to set both `--evaluator-model` and `--resolver-model` to the same model. |
| `--max-workers` | `5` | Number of parallel evaluation threads. |
| `--benchmark_ids` | `None` | Only evaluate these benchmark IDs (e.g. `--benchmark_ids 1 10 57`). |

## How It Works

1. **Ingestion** — reads `result.json` files from Phase 2 execution results.
2. **Gap Detection** — scans the candidate code for imported libraries. If the evaluator model might not know a library (e.g. an obscure third-party package), the Resolver model is called first to provide context.
3. **Evaluation** — for each test case, constructs a prompt containing the task description, candidate code, observed output, and any gap context, then asks the LLM for a `PASS` or `FAIL` verdict with justification.
4. **Output** — writes per-sample `summary.json` (verdicts) and `debug.json` (full reasoning).

## Output Structure

```
BenchmarkingExperiments/evaluation_results/
└── <language>/
    └── <model>/
        └── <benchmark_id>/
            └── sample_<n>/
                ├── summary.json   # Pass/Fail verdict per fc_test and sec_test
                └── debug.json     # full evaluator prompt, reasoning, and gap resolution
```
