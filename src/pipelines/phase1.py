from __future__ import annotations


from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> None:
    """Run baseline Phase 1 data pipeline end-to-end."""
    print("=== Phase 1: Starting Baseline Data Pipeline ===", flush=True)
    settings = load_settings()
    run_date = now_utc()

    # 1. Ingest raw records from Crossref API or snapshot
    print(f"1. Fetching raw records from {settings.source_api}...", flush=True)
    raw_records = fetch_source_records(settings)
    print(f"   Fetched {len(raw_records)} raw records.", flush=True)

    # 2. Clean records into DataFrame
    print("2. Cleaning raw records into DataFrame...", flush=True)
    df_clean = build_clean_dataframe(raw_records, run_date)
    print(f"   Cleaned DataFrame contains {len(df_clean)} rows.", flush=True)

    # Save clean dataset artifacts
    write_csv(df_clean, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df_clean.to_dict(orient="records"))
    print(f"   Saved clean CSV to {settings.paths.clean_csv}", flush=True)
    print(f"   Saved clean JSON to {settings.paths.clean_json}", flush=True)

    # 3. Build Chroma vector index & embedding manifest
    print(f"3. Building ChromaDB embedding index with model '{settings.embedding_model}'...", flush=True)
    index = LocalEmbeddingIndex.build(df_clean, settings, settings.paths.embeddings_json)
    print(f"   Built index '{index.collection_name}' with {len(index.documents)} documents.", flush=True)

    # 4. Generate evaluation test set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        print("4. Generating new evaluation test set...", flush=True)
        build_test_set(df_clean, settings.paths.eval_testset)
    else:
        print(f"4. Using existing evaluation test set at {settings.paths.eval_testset}", flush=True)

    # 5. Run evaluation pipeline
    print("5. Evaluating retrieval and answer quality...", flush=True)
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"   Retrieval Hit Rate: {eval_bundle.summary['retrieval_hit_rate']:.4f}", flush=True)
    print(f"   Mean Token F1:      {eval_bundle.summary['mean_token_f1']:.4f}", flush=True)
    print(f"   Judge Accuracy:     {eval_bundle.summary['judge_accuracy']:.4f}", flush=True)
    print(f"   Mean Judge Score:   {eval_bundle.summary['mean_judge_score']:.2f}", flush=True)

    # 6. Data Observability: Quality checks & Freshness report
    print("6. Running Data Quality & Freshness observability checks...", flush=True)
    quality_res = run_data_quality_checks(df_clean, settings, report_name="baseline_quality")
    freshness_res = build_freshness_report(df_clean, settings, settings.paths.freshness_report)
    print(f"   Quality Status: {'PASSED' if quality_res['success'] else 'FAILED'}", flush=True)
    print(f"   Freshness Status: {'FRESH' if freshness_res['is_fresh'] else 'STALE'}", flush=True)

    # 7. Generate Markdown report
    print("7. Generating Phase 1 Baseline report...", flush=True)
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "total_records": len(raw_records),
        "clean_rows": len(df_clean),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_res,
        freshness=freshness_res,
    )
    print(f"   Baseline report written to {settings.paths.baseline_report}", flush=True)

    # 8. Agent Demo Answers on sample questions
    if not df_clean.empty:
        sample_title = df_clean.iloc[0]["title"]
        demo_questions = [
            f"What is the main summary of the paper '{sample_title}'?",
            f"Who authored the paper '{sample_title}'?",
        ]
        demo_results = []
        for q in demo_questions:
            res = answer_question(q, settings, index)
            demo_results.append(
                {
                    "question": q,
                    "answer": res.answer,
                    "retrieved_doc_ids": res.retrieved_doc_ids,
                    "retrieved_titles": res.retrieved_titles,
                }
            )
        write_json(settings.paths.demo_answers, demo_results)

    print("=== Phase 1 Baseline Completed Successfully! ===", flush=True)

