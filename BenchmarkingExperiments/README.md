# BenchmarkingExperiments

This directory contains all experimental outputs from the DualGauge evaluation study: generated code samples, agentic execution logs, LLM evaluator verdicts, and aggregated metrics across all evaluated model configurations.

## Data Access

Pre-computed results for all evaluated configurations (10 LLMs × 3 languages, 3 agentic coding systems, and 45+ Python-only factor sweeps) are available on Zenodo (click [here](https://doi.org/10.5281/zenodo.20480617)

## Directory Structure

Once downloaded, the data follows this layout:

```
BenchmarkingExperiments/
├── generated_samples/        # Raw model outputs (Phase 1)
│   └── {language}/{model}/{benchmark_id}/
├── execution_results/        # Agentic executor logs and traces (Phase 2)
│   └── {language}/{model}/{benchmark_id}/
└── evaluation_results/       # LLM evaluator verdicts and summaries (Phase 3)
    └── {language}/{model}/{benchmark_id}/
```

## Replication

To reproduce the results from scratch, follow the Quick Start in the [root README](../README.md). Per-task execution logs are included in the release to support cost estimation before replication.
