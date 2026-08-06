from __future__ import annotations

from datetime import datetime
import json

import sys
from pathlib import Path

# ensure src is on sys.path when running from script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe


def main() -> None:
    settings = load_settings()

    # fetch or load raw records
    records = []
    try:
        if settings.refresh_source:
            records = fetch_source_records(settings)
        else:
            # try load existing snapshot
            records = load_raw_records(settings.paths.raw_records_json)
    except Exception:
        # fallback to fetching
        records = fetch_source_records(settings)

    print(f"Records obtained: {len(records)}")

    df = build_clean_dataframe(records, datetime.now())

    # ensure directories exist
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", force_ascii=False, indent=2)

    print("Saved cleaned CSV:", settings.paths.clean_csv)
    print("Saved cleaned JSON:", settings.paths.clean_json)


if __name__ == "__main__":
    main()
