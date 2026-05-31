# Phase 1: Sample Generation

Queries a target code generator for each benchmark in `DualGauge-Bench/` and saves the generated code. Backends can be direct LLM APIs or CLI-driven coding agents such as Codex.

## Usage

Run from the repository root:

```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model <model_name> --language <language> [options]
```

### Examples

**Standard run (1 sample per benchmark):**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model gpt-4.1 --language python
```

**Generate 5 samples per benchmark:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model claude-haiku-4-5 --language python --k 5
```

**Use a model spec to route to the right provider:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model qwen3-14b --model_spec vllm:Qwen/Qwen3-14B --language python
```

**Use Codex as an agentic generator:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model codex-default --model_spec codex --language python
```

**Use Codex with an explicit model override:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model codex-gpt54 --model_spec codex:gpt-5.4 --language python
```

**Use Claude Code as an agentic generator:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model claudecode-default --model_spec claudecode --language python
```

**Use Claude Code with an explicit model override:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model claudecode-sonnet --model_spec claudecode:sonnet --language python
```

**Use OpenHands as an agentic generator:**
```bash
python3.11 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model openhands-default --model_spec openhands --language python
```

**Use OpenHands with an explicit model override:**
```bash
python3.11 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model openhands-opus47 --model_spec openhands:claude-opus-4-7 --language python
```

**Use SWE-agent as an agentic generator:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model sweagent-gpt4o --model_spec sweagent:gpt-4o --language python
```

**Use SWE-agent with Claude:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model sweagent-sonnet --model_spec sweagent:claude-sonnet-4-20250514 --language python
```

**Run specific benchmarks only:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model gpt-4.1 --language python --benchmark_ids 1 5 42
```

**Resume an interrupted run:**
```bash
python3 DualGauge/Phase1_sample_generation/generate_samples.py \
  --model gpt-4.1 --language python --skip_existing
```

## Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--model` | **Required** | Output label used for experiment folders (e.g. `gpt-4.1`, `qwen3-14b`). Should match an entry in `experiments/models.yaml` for auto-config. |
| `--model_spec` | `None` | Explicit provider/model spec for inference (e.g. `openai:gpt-4.1`, `vllm:Qwen/Qwen3-14B`, `codex`, `codex:gpt-5.4`, `claudecode`, `claudecode:sonnet`, `openhands`, `openhands:claude-opus-4-7`). Overrides `--model` for the backend call. |
| `--language` | `None` | Language to generate code in: `python`, `cpp`, `javascript`, `c`. Overrides any `implementation_details` in the benchmark. |
| `--k` | `1` | Number of samples to generate per benchmark. |
| `--input_dir` | `DualGauge-Bench/` | Directory containing numbered benchmark folders (each with `tests.json`). |
| `--output_dir` | `BenchmarkingExperiments/generated_samples` | Base output directory. |
| `--benchmark_ids` | `None` | Only process these benchmark IDs (e.g. `--benchmark_ids 1 10 57`). |
| `--temperature` | `0.0` | Sampling temperature. |
| `--include_requirements` | `False` | Include the shared `Requirements:` block in the prompt. By default it is omitted. |
| `--skip_existing` | `False` | Skip benchmarks that already have output files. |
| `--no_parallel` | `False` | Disable parallelism (useful for debugging). |

## Output Structure

```
BenchmarkingExperiments/generated_samples/
└── <language>/
    └── <model>/
        ├── generation_log.txt
        ├── generation_progress.log
        └── <benchmark_id>/
            ├── raw_outputs/
            │   └── <id>_sample_<n>.txt        # full LLM response
            └── code_outputs/
                └── <id>_sample_<n>.<ext>      # extracted code block
```

The file extension is inferred from `implementation_details` or from the code content itself.

## Notes for Codex

- Requires the local `codex` CLI to be installed and authenticated.
- Phase 1 runs Codex in `read-only` sandbox mode with approvals disabled so generation stays non-destructive.
- `--model_spec codex` uses your local Codex default model from `~/.codex/config.toml`. Use `--model_spec codex:<model>` only when you want to override it explicitly.
- The final Codex response is normalized into a single code artifact for downstream phases.

## Notes for Claude Code

- Requires the local `claude` CLI to be installed and authenticated.
- Phase 1 runs Claude Code in non-interactive `-p` mode with `bypassPermissions` so the agent can use its tools without prompts.
- `--model_spec claudecode` uses Claude Code's local default model. Use `--model_spec claudecode:<model>` only when you want to override it explicitly.
- The full Claude event stream is saved per sample as `_events.jsonl`.

## Notes for OpenHands

- Requires the local `openhands` CLI to be installed and configured.
- Phase 1 runs OpenHands in `--headless --json` mode, which auto-approves actions by design.
- Each sample runs in an isolated temporary workspace so OpenHands can create/edit files without touching the repository.
- `--model_spec openhands` uses the model from your OpenHands settings. Use `--model_spec openhands:<model>` to override it for a run.
- The full OpenHands event stream is saved per sample as `_events.jsonl`.
