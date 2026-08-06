from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame([r.__dict__ for r in records])
    
    # 1. Normalize
    df['title'] = df['title'].str.strip()
    df['summary'] = df['summary'].str.strip()
    
    # 2. Parse published date & 3. Calculate age
    df['published'] = pd.to_datetime(df['published'], errors='coerce')
    # Use timezone-naive run_date for subtraction
    if run_date.tzinfo is not None:
        run_date = run_date.replace(tzinfo=None)
    df['age_days'] = (run_date - df['published']).dt.days
    df['published'] = df['published'].dt.strftime('%Y-%m-%d')
    
    # 4. Helper columns
    df['authors_joined'] = df['authors'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
    df['categories_joined'] = df['categories'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
    df['summary_chars'] = df['summary'].str.len()
    
    # Build text_for_embedding
    def create_embedding_text(row):
        return (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Published: {row['published']}\n"
            f"Summary: {row['summary']}"
        )
    df['text_for_embedding'] = df.apply(create_embedding_text, axis=1)
    
    # 5. Drop duplicates and invalid rows
    df = df.drop_duplicates(subset=['paper_id'])
    df = df.dropna(subset=['title', 'summary'])
    df = df[(df['title'] != "") & (df['summary'] != "")]
    
    # 6. Sort
    df = df.sort_values(by=['published'], ascending=False).reset_index(drop=True)
    
    return df
