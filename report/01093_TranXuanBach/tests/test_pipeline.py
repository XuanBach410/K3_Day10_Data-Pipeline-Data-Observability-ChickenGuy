import os
from datetime import datetime, UTC
import pandas as pd
import pytest

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import PaperRecord, parse_crossref_payload
from observability.quality import build_freshness_report, run_data_quality_checks


def test_parse_crossref_payload():
    payload = {
        "status": "ok",
        "message": {
            "items": [
                {
                    "DOI": "10.1234/test.001",
                    "title": ["<jats:p>Test Paper Title</jats:p>"],
                    "abstract": "<jats:p>This is a test abstract summary for the paper.</jats:p>",
                    "author": [{"given": "Jane", "family": "Doe"}],
                    "subject": ["Computer Science"],
                    "published-online": {"date-parts": [[2024, 1, 15]]},
                    "URL": "https://doi.org/10.1234/test.001",
                }
            ]
        },
    }
    records = parse_crossref_payload(payload)
    assert len(records) == 1
    rec = records[0]
    assert rec.paper_id == "10.1234/test.001"
    assert rec.title == "Test Paper Title"
    assert rec.summary == "This is a test abstract summary for the paper."
    assert rec.authors == ["Jane Doe"]
    assert rec.published == "2024-01-15"


def test_build_clean_dataframe():
    records = [
        PaperRecord(
            paper_id="10.1234/test.001",
            title="Test Paper Title",
            summary="This is a test abstract summary for the paper.",
            authors=["Jane Doe"],
            categories=["Computer Science"],
            primary_category="Computer Science",
            published="2024-01-15",
            updated="2024-01-15",
            abs_url="https://doi.org/10.1234/test.001",
            pdf_url="https://doi.org/10.1234/test.001",
            comment="",
        )
    ]
    now = datetime(2024, 6, 1, tzinfo=UTC)
    df = build_clean_dataframe(records, now)
    assert not df.empty
    assert len(df) == 1
    assert "text_for_embedding" in df.columns
    assert "age_days" in df.columns
    assert df.iloc[0]["summary_chars"] > 0


def test_data_quality_checks_and_freshness(tmp_path):
    settings = load_settings()
    now = datetime(2024, 6, 1, tzinfo=UTC)
    records = [
        PaperRecord(
            paper_id="10.1234/test.001",
            title="Test Paper Title",
            summary="This is a test abstract summary for the paper with sufficient text length to pass quality checks.",
            authors=["Jane Doe"],
            categories=["Computer Science"],
            primary_category="Computer Science",
            published="2024-05-01",
            updated="2024-05-01",
            abs_url="https://doi.org/10.1234/test.001",
            pdf_url="https://doi.org/10.1234/test.001",
            comment="",
        )
    ]
    df = build_clean_dataframe(records, now)

    quality = run_data_quality_checks(df, settings, "test_quality")
    assert quality["success"] is True

    freshness_path = tmp_path / "freshness.json"
    freshness = build_freshness_report(df, settings, freshness_path)
    assert freshness["is_fresh"] is True


def test_corrupt_clean_dataframe(tmp_path):
    now = datetime(2024, 6, 1, tzinfo=UTC)
    records = [
        PaperRecord(
            paper_id=f"10.1234/test.{i:03d}",
            title=f"Test Paper Title Number {i}",
            summary=f"This is test abstract summary number {i} with long descriptive text for test coverage.",
            authors=[f"Author {i}"],
            categories=["Computer Science"],
            primary_category="Computer Science",
            published="2024-05-01",
            updated="2024-05-01",
            abs_url=f"https://doi.org/10.1234/test.{i:03d}",
            pdf_url="",
            comment="",
        )
        for i in range(1, 10)
    ]
    df = build_clean_dataframe(records, now)
    log_path = tmp_path / "corruption_log.json"
    corrupted_df = corrupt_clean_dataframe(df, log_path)

    assert log_path.exists()
    assert len(corrupted_df) != len(df) or (corrupted_df["summary"] == "").any()
