from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


import re
from datetime import datetime, UTC
import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a structured pandas DataFrame ready for embedding & indexing."""
    rows: list[dict] = []

    for record in records:
        title = normalize_whitespace(record.title or "")
        summary = normalize_whitespace(record.summary or "")
        if not title:
            continue

        authors = [normalize_whitespace(a) for a in record.authors if normalize_whitespace(a)]
        if not authors:
            authors = ["Unknown Author"]
        authors_joined = ", ".join(authors)

        categories = [normalize_whitespace(c) for c in record.categories if normalize_whitespace(c)]
        if not categories:
            categories = ["General"]
        categories_joined = ", ".join(categories)
        primary_category = normalize_whitespace(record.primary_category or categories[0])

        published_str = normalize_whitespace(record.published or "2024-01-01")
        try:
            pub_dt = datetime.strptime(published_str[:10], "%Y-%m-%d")
        except ValueError:
            pub_dt = datetime(2024, 1, 1)
            published_str = "2024-01-01"

        if run_date.tzinfo is not None:
            run_date_naive = run_date.replace(tzinfo=None)
        else:
            run_date_naive = run_date

        age_days = max(0, (run_date_naive.date() - pub_dt.date()).days)

        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published_str}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id),
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_str,
                "updated": normalize_whitespace(record.updated or published_str),
                "abs_url": normalize_whitespace(record.abs_url or ""),
                "pdf_url": normalize_whitespace(record.pdf_url or ""),
                "comment": normalize_whitespace(record.comment or ""),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Deduplicate by paper_id (keep first) and title
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")

    # Sort by publication date descending
    df = df.sort_values(by=["published"], ascending=False).reset_index(drop=True)
    return df

