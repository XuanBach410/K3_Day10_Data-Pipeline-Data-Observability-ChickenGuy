from __future__ import annotations
import json
from datetime import datetime, UTC

from core.config import load_settings, require_llm_credentials
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import build_index_from_dataframe
from retrieval.llm import get_llm
from retrieval.qa import AnswerGenerator

def main() -> None:
    print("--- BẮT ĐẦU PHA 1: XÂY DỰNG BASELINE PIPELINE ---")
    
    # 1. Load settings
    settings = load_settings()
    # require_llm_credentials(settings)
    
    # 2. Load or fetch raw records
    print("\n1. Fetching data from Crossref API...")
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        print(f"Data exists. Loading from {settings.paths.raw_records_json}...")
        records = load_raw_records(settings.paths.raw_records_json)
        
    print(f"Loaded {len(records)} raw records.")
    
    # 3. Clean data
    print("\n2. Cleaning data...")
    df_clean = build_clean_dataframe(records, datetime.now(UTC))
    print(f"Cleaned data shape: {df_clean.shape}")
    
    # 4. Save clean CSV/JSON
    print("\n3. Saving clean data...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(settings.paths.clean_csv, index=False)
    df_clean.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)
    
    # 5. Build Chroma index
    print("\n4. Building Vector Index (ChromaDB)...")
    manifest = build_index_from_dataframe(
        df=df_clean,
        settings=settings,
        collection_name=settings.baseline_collection_name,
        output_manifest_path=settings.paths.embeddings_json
    )
    print(f"Index built with {manifest.total_chunks} chunks.")
    
    # Test set & Evaluation are skipped in this minimal implementation to focus on RAG functionality
    print("\n[NOTE] Skipped Testset Generation & Quality Reporting for this demo.")
    
    # 10. Demo agent
    print("\n5. Testing the Agent...")
    try:
        require_llm_credentials(settings)
        llm = get_llm(settings)
        agent = AnswerGenerator(settings, llm, settings.baseline_collection_name)
        
        test_question = "What is agentic retrieval augmented generation?"
        print(f"\nQ: {test_question}")
        response = agent.generate(test_question)
        print(f"\nA:\n{response.answer}")
        
        # Save demo answers
        settings.paths.demo_answers.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.paths.demo_answers, "w", encoding="utf-8") as f:
            json.dump([response.model_dump()], f, indent=2, ensure_ascii=False)
            
        print(f"\nDemo answer saved to {settings.paths.demo_answers}")
    except Exception as e:
        print(f"\n[ERROR] Could not test agent: {e}")
        print("Please check your .env file and ensure LLM credentials (e.g. GOOGLE_API_KEY) are set.")

    print("\n--- PHA 1 HOÀN TẤT ---")

if __name__ == "__main__":
    main()
