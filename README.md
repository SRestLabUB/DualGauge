# DualGauge


**DualGauge** is the first fully automated framework for jointly evaluating the **functional correctness** and **security** of specification-only LLM code generation. Existing benchmarks measure one or the other — DualGauge measures both simultaneously, revealing that functional correctness substantially overestimates reliable code generation: the strongest model achieves 38.6% pass@1 on Python but only 14.8% secure-pass@1.

The framework pairs a curated benchmark suite (**DualGauge-Bench**) with a four-phase agentic evaluation pipeline. Benchmarks are language-agnostic — each specifies only the task in natural language, with no starter code — and every benchmark carries both a functional oracle and a security oracle with a CWE label.

![DualGauge Pipeline](DualGauge_pipeline.png)

## Benchmark: DualGauge-Bench

DualGauge-Bench contains **307 language-agnostic benchmarks** spanning **90 CWE categories** (OWASP Top 10, CERT standards, and beyond). Each benchmark has:

- `prompt` — natural-language task specification (no starter code)
- `fc_tests` — functional correctness tests with exact input/output pairs
- `sec_tests` — security behavioral tests, each labeled with a CWE ID
- `implementation_details` — optional language hints (e.g. "use Flask")

Benchmarks were sourced from CodeGuard+, SecurityEval, and Purple Llama CyberSecEval, then refined through a human–LLM co-creation process: an LLM draft was reviewed and corrected by human annotators for both correctness and security intent.

## Pipeline Architecture

DualGauge operates in four sequential phases:

| Phase | Component | Description |
| :--- | :--- | :--- |
| **Phase 1** | [Sample Generation](DualGauge/Phase1_sample_generation/README.md) | Queries target LLMs to generate code solutions for each benchmark prompt. |
| **Phase 2** | [Agentic Executor](DualGauge/Phase2_agentic_executor/README.md) | Runs code in isolated Docker containers with an autonomous self-correction loop for environment errors. |
| **Phase 3** | [LLM Evaluator](DualGauge/Phase3_llm_evaluator/README.md) | Semantically judges execution results (Pass/Fail) using an LLM-as-a-Judge with knowledge gap resolution. |
| **Phase 4** | [Aggregation & Metrics](DualGauge/Phase4_aggregation_dashboard/README.md) | Computes pass@k, secure@k, and secure-pass@k across all models and benchmarks. |

### Key Features

- **Specification-Only**: Benchmarks provide only a natural-language description — no function signatures, no starter code — matching real-world code generation use.
- **Dual Oracle**: Every benchmark has both functional tests (exact I/O) and security tests (CWE-labeled behavioral checks). A sample must pass both to count as secure-pass.
- **Agentic Self-Correction**: The executor autonomously fixes environment issues (missing packages, compile errors) and retries, ensuring the model's logic is evaluated rather than its setup.
- **Semantic Evaluation**: The LLM judge understands that `"403 Forbidden"` and `"Access Denied"` are functionally equivalent.
- **Knowledge Gap Resolution**: A resolver model fetches context for obscure libraries before passing judgment.
- **Sandboxed Execution**: All code runs in isolated Docker containers.
- **Language-Agnostic Benchmarks**: Each benchmark is evaluated in Python, C++, and JavaScript from the same specification.

## Repository Structure

```
DualGauge-Bench/          # Benchmark dataset (307 benchmarks)
DualGauge/                # Pipeline source code
├── Phase1_sample_generation/
├── Phase2_agentic_executor/
├── Phase3_llm_evaluator/
├── Phase4_aggregation_dashboard/
├── config/
├── models/
└── utils/
BenchmarkingExperiments/  # All experimental outputs (see README inside)
```

## Setup

```bash
pip install -r requirements.txt
```

Set API keys for the providers you intend to use:

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...       # optional
export DEEPSEEK_API_KEY=...     # optional
export XAI_API_KEY=...          # optional
```

Docker must be running for Phase 2 (sandboxed execution).

## Quick Start

**1. Generate Samples**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model gpt-4.1 --language python
```

**2. Execute (Agentic Loop)**
```bash
python3 DualGauge/Phase2_agentic_executor/execute_samples.py \
  --input BenchmarkingExperiments/generated_samples/python/gpt-4.1
```

**3. Evaluate (LLM Judge)**
```bash
python3 DualGauge/Phase3_llm_evaluator/evaluate_samples.py \
  --log-dir BenchmarkingExperiments/execution_results/python/gpt-4.1
```

**4. Compute Metrics**
```bash
python3 DualGauge/Phase4_aggregation_dashboard/calculate_all_metrics.py \
  --input_folder BenchmarkingExperiments/evaluation_results/python
```

## Experimental Data

Pre-computed results for all 45+ model configurations are available via Google Drive. See [BenchmarkingExperiments/README.md](BenchmarkingExperiments/README.md) for the download link and directory structure.
