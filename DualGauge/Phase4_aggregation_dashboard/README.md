# Phase 4: Aggregation & Metrics

Reads Phase 3 evaluation results and computes `pass@k`, `secure@k`, and `secure-pass@k` metrics per model, outputting a summary CSV for the paper.

## Metric Definitions

| Metric | Meaning |
| :--- | :--- |
| `pass@k` | Probability that at least one of k samples passes all functional correctness tests |
| `secure@k` | Probability that at least one of k samples passes all security tests |
| `secure-pass@k` | Probability that at least one of k samples passes **both** |

All three use the unbiased estimator from Chen et al. (2021).

## Usage

Run from the repository root:

```bash
python3 DualGauge/Phase4_aggregation_dashboard/calculate_all_metrics.py \
  --input_folder BenchmarkingExperiments/evaluation_results/python [options]
```

Point `--input_folder` at a single language directory so its immediate children are model directories.

### Examples

**Python results, k=1:**
```bash
python3 DualGauge/Phase4_aggregation_dashboard/calculate_all_metrics.py \
  --input_folder BenchmarkingExperiments/evaluation_results/python
```

**Custom k and output file:**
```bash
python3 DualGauge/Phase4_aggregation_dashboard/calculate_all_metrics.py \
  --input_folder BenchmarkingExperiments/evaluation_results/python \
  --k-value 5 --output results_k5.csv
```

## Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--input_folder` | `BenchmarkingExperiments/benchmarking_results` | Directory whose immediate children are model directories, each containing `<benchmark_id>/sample_<n>/summary.json` files. |
| `--k-value` / `-k` | `1` | Number of samples to use for pass@k calculation. |
| `--output` | `metrics_k<k>.csv` | Output CSV path. |

## Output

A single CSV with one row per model containing:
- `pass@k`, `secure@k`, `secure-pass@k` (overall and per-language)
- Per-benchmark breakdown available in the per-benchmark metrics script

## Dashboard

An interactive Next.js dashboard for visualizing results.

```bash
cd DualGauge/Phase4_aggregation_dashboard/dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the benchmark report.
