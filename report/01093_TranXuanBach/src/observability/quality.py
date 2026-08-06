from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


from typing import Any
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality checks on clean/corrupted DataFrame and save JSON artifact."""
    total_rows = len(df)
    if total_rows == 0:
        result = {
            "report_name": report_name,
            "total_rows": 0,
            "null_paper_ids": 0,
            "duplicate_paper_ids": 0,
            "null_titles": 0,
            "short_summaries": 0,
            "stale_rows": 0,
            "checks": {
                "row_count_passed": False,
                "null_paper_ids_passed": False,
                "duplicate_paper_ids_passed": False,
                "null_titles_passed": False,
                "summary_length_passed": False,
                "freshness_passed": False,
            },
            "success": False,
        }
        write_json(settings.paths.quality_dir / f"{report_name}.json", result)
        return result

    null_paper_ids = int(df["paper_id"].isna().sum() + (df["paper_id"] == "").sum())
    duplicate_paper_ids = int(df["paper_id"].duplicated().sum())
    null_titles = int(df["title"].isna().sum() + (df["title"] == "").sum())
    
    summary_lengths = df["summary"].apply(lambda s: len(str(s).strip()) if pd.notna(s) else 0)
    short_summaries = int((summary_lengths < 50).sum())

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    checks = {
        "row_count_passed": bool(total_rows >= 1),
        "null_paper_ids_passed": bool(null_paper_ids == 0),
        "duplicate_paper_ids_passed": bool(duplicate_paper_ids == 0),
        "null_titles_passed": bool(null_titles == 0),
        "summary_length_passed": bool(short_summaries == 0),
        "freshness_passed": bool(stale_rows == 0),
    }

    success = all(checks.values())

    result = {
        "report_name": report_name,
        "total_rows": total_rows,
        "null_paper_ids": null_paper_ids,
        "duplicate_paper_ids": duplicate_paper_ids,
        "null_titles": null_titles,
        "short_summaries": short_summaries,
        "stale_rows": stale_rows,
        "checks": checks,
        "success": success,
    }

    write_json(settings.paths.quality_dir / f"{report_name}.json", result)
    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Aggregate freshness report for DataFrame and save JSON artifact."""
    total_rows = len(df)
    if total_rows == 0:
        payload = {
            "latest_published": "N/A",
            "oldest_published": "N/A",
            "freshness_threshold_days": settings.freshness_threshold_days,
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    published_series = df["published"].dropna().astype(str)
    latest_published = str(published_series.max()) if not published_series.empty else "N/A"
    oldest_published = str(published_series.min()) if not published_series.empty else "N/A"

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": bool(stale_rows == 0 and total_rows > 0),
    }

    write_json(report_path, payload)
    return payload

