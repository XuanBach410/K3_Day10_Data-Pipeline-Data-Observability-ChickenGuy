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
            "Baseline artifacts missing! Please run Phase 1 baseline pipeline first using: uv run python script/run_phase1.py"
        )

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_records_dict = read_json(settings.paths.clean_json)
    df_clean = pd.DataFrame(clean_records_dict)
    print(f"1. Loaded Baseline dataset with {len(df_clean)} records.")

    # 2. Simulate Corruption
    print("2. Simulating data corruption scenarios...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    print(f"   Corrupted DataFrame contains {len(df_corrupted)} records.")

    # Save Corrupted dataset artifacts
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))

    # 3. Build Corrupted Index
    print(f"3. Building ChromaDB index for Corrupted dataset...")
    corrupted_index = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)

    # 4. Evaluate Corrupted pipeline on same test set
    print("4. Evaluating Corrupted pipeline performance on same test set...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"   [Corrupted] Retrieval Hit Rate: {corrupted_bundle.summary['retrieval_hit_rate']:.4f}")
    print(f"   [Corrupted] Mean Token F1:      {corrupted_bundle.summary['mean_token_f1']:.4f}")
    print(f"   [Corrupted] Judge Accuracy:     {corrupted_bundle.summary['judge_accuracy']:.4f}")
    print(f"   [Corrupted] Mean Judge Score:   {corrupted_bundle.summary['mean_judge_score']:.2f}")

    # 5. Data Observability on Corrupted data
    print("5. Running Observability Quality & Freshness checks on Corrupted dataset...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted_quality")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "freshness_report_corrupted.json"
    )

    # 6. Repair Data Pipeline (Restoring clean dataset from authoritative raw records)
    print("6. Repairing dataset from raw source snapshot...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    print(f"   Repaired DataFrame contains {len(df_repaired)} records.")

    # Save Repaired dataset artifacts
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))

    # 7. Build Repaired Index
    print("7. Building ChromaDB index for Repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)

    # 8. Evaluate Repaired pipeline
    print("8. Evaluating Repaired pipeline performance on same test set...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"   [Repaired] Retrieval Hit Rate: {repaired_bundle.summary['retrieval_hit_rate']:.4f}")
    print(f"   [Repaired] Mean Token F1:      {repaired_bundle.summary['mean_token_f1']:.4f}")
    print(f"   [Repaired] Judge Accuracy:     {repaired_bundle.summary['judge_accuracy']:.4f}")
    print(f"   [Repaired] Mean Judge Score:   {repaired_bundle.summary['mean_judge_score']:.2f}")

    # 9. Data Observability on Repaired data
    print("9. Running Observability Quality & Freshness checks on Repaired dataset...")
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired_quality")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "freshness_report_repaired.json"
    )

    # 10. Generate Comparison Report
    print("10. Generating Corruption vs. Baseline vs. Repaired Comparison Report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"    Comparison report written to {settings.paths.comparison_report}")
    print("=== Phase 2 Corruption Flow Completed Successfully! ===")

