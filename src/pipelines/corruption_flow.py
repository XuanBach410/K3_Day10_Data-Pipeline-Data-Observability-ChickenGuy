from __future__ import annotations


import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run Corruption -> Evaluate -> Repair -> Compare flow end-to-end."""
    print("=== Phase 2: Starting Corruption, Repair & Comparison Flow ===")
    settings = load_settings()
    run_date = now_utc()

    # 1. Verify baseline artifacts exist
    if not settings.paths.baseline_metrics.exists() or not settings.paths.clean_json.exists():
        raise RuntimeError(
    # 1. Load Baseline clean dataset
    if not settings.paths.clean_csv.exists():
        print(f"1. Clean CSV not found at {settings.paths.clean_csv}. Running Phase 1 baseline first...", flush=True)
        raw_records = fetch_source_records(settings)
        df_baseline = build_clean_dataframe(raw_records, run_date)
        write_csv(df_baseline, settings.paths.clean_csv)
    else:
        print(f"1. Loaded Baseline dataset from {settings.paths.clean_csv}", flush=True)
        df_baseline = pd.read_csv(settings.paths.clean_csv)

    # 2. Corrupt Clean DataFrame & log actions
    print("2. Simulating data corruption scenarios...", flush=True)
    df_corrupted, corruption_log = corrupt_clean_dataframe(df_baseline)
    print(f"   Corrupted DataFrame contains {len(df_corrupted)} records.", flush=True)
    write_csv(df_corrupted, settings.paths.corrupted_csv)
    write_json(settings.paths.corrupted_json, df_corrupted.to_dict(orient="records"))
    write_json(settings.paths.corruption_log, corruption_log)
    print(f"   Saved corrupted CSV to {settings.paths.corrupted_csv}", flush=True)
    print(f"   Saved corruption log to {settings.paths.corruption_log}", flush=True)

    # 3. Build Corrupted Index
    print("3. Building ChromaDB index for Corrupted dataset...", flush=True)
    index_corrupted = LocalEmbeddingIndex.build(
        df_corrupted,
        settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    # 4. Evaluate Corrupted Pipeline
    print("4. Evaluating Corrupted pipeline performance on same test set...", flush=True)
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"   [Corrupted] Retrieval Hit Rate: {corrupted_eval.summary['retrieval_hit_rate']:.4f}", flush=True)
    print(f"   [Corrupted] Mean Token F1:      {corrupted_eval.summary['mean_token_f1']:.4f}", flush=True)
    print(f"   [Corrupted] Judge Accuracy:     {corrupted_eval.summary['judge_accuracy']:.4f}", flush=True)
    print(f"   [Corrupted] Mean Judge Score:   {corrupted_eval.summary['mean_judge_score']:.2f}", flush=True)

    # 5. Data Observability on Corrupted Dataset
    print("5. Running Observability Quality & Freshness checks on Corrupted dataset...", flush=True)
    quality_corrupted = run_data_quality_checks(df_corrupted, settings, report_name="corrupted_quality")
    freshness_corrupted = build_freshness_report(df_corrupted, settings, settings.paths.corrupted_freshness)
    write_json(settings.paths.corrupted_quality, quality_corrupted)

    # 6. Repair Dataset from raw source snapshot
    print("6. Repairing dataset from raw source snapshot...", flush=True)
    raw_snapshot = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_snapshot, run_date)
    print(f"   Repaired DataFrame contains {len(df_repaired)} records.", flush=True)
    write_csv(df_repaired, settings.paths.repaired_csv)
    write_json(settings.paths.repaired_json, df_repaired.to_dict(orient="records"))
    print(f"   Saved repaired CSV to {settings.paths.repaired_csv}", flush=True)

    # 7. Build Repaired Index
    print("7. Building ChromaDB index for Repaired dataset...", flush=True)
    index_repaired = LocalEmbeddingIndex.build(
        df_repaired,
        settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    # 8. Evaluate Repaired Pipeline
    print("8. Evaluating Repaired pipeline performance on same test set...", flush=True)
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"   [Repaired] Retrieval Hit Rate: {repaired_eval.summary['retrieval_hit_rate']:.4f}", flush=True)
    print(f"   [Repaired] Mean Token F1:      {repaired_eval.summary['mean_token_f1']:.4f}", flush=True)
    print(f"   [Repaired] Judge Accuracy:     {repaired_eval.summary['judge_accuracy']:.4f}", flush=True)
    print(f"   [Repaired] Mean Judge Score:   {repaired_eval.summary['mean_judge_score']:.2f}", flush=True)

    # 9. Data Observability on Repaired Dataset
    print("9. Running Observability Quality & Freshness checks on Repaired dataset...", flush=True)
    quality_repaired = run_data_quality_checks(df_repaired, settings, report_name="repaired_quality")
    freshness_repaired = build_freshness_report(df_repaired, settings, settings.paths.repaired_freshness)
    write_json(settings.paths.repaired_quality, quality_repaired)

    # 10. Generate Corruption Comparison Report
    print("10. Generating Corruption vs. Baseline vs. Repaired Comparison Report...", flush=True)
    baseline_eval = evaluate_pipeline(
        settings=settings,
        index=LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json),
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    quality_baseline = run_data_quality_checks(df_baseline, settings, report_name="baseline_quality")
    freshness_baseline = build_freshness_report(df_baseline, settings, settings.paths.freshness_report)

    generate_corruption_report(
        report_path=settings.paths.corruption_report,
        baseline_metrics=baseline_eval.summary,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        baseline_quality=quality_baseline,
        corrupted_quality=quality_corrupted,
        repaired_quality=quality_repaired,
        baseline_freshness=freshness_baseline,
        corrupted_freshness=freshness_corrupted,
        repaired_freshness=freshness_repaired,
        corruption_log=corruption_log,
    )
    print(f"   Comparison report written to {settings.paths.corruption_report}", flush=True)
    print("=== Phase 2 Corruption Flow Completed Successfully! ===", flush=True)
