from __future__ import annotations

import pandas as pd


from typing import Any
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate multiple data quality defects on DataFrame and log actions."""
    corrupted_df = df.copy()
    corruption_log: list[dict[str, Any]] = []

    if corrupted_df.empty:
        write_json(output_log_path, corruption_log)
        return corrupted_df

    total_orig = len(corrupted_df)

    # 1. Drop top 2 latest records (if length allows)
    if total_orig >= 4:
        dropped_ids = corrupted_df.iloc[:2]["paper_id"].tolist()
        corrupted_df = corrupted_df.iloc[2:].reset_index(drop=True)
        corruption_log.append(
            {
                "scenario": "drop_latest_records",
                "count": len(dropped_ids),
                "affected_paper_ids": dropped_ids,
                "description": "Dropped latest 2 papers to test missing paper retrieval failure.",
            }
        )

    # 2. Blank summary for 2 rows
    if len(corrupted_df) >= 2:
        target_indices = [0, 1]
        blanked_ids = []
        for idx in target_indices:
            paper_id = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "summary"] = ""
            corrupted_df.at[idx, "summary_chars"] = 0
            blanked_ids.append(paper_id)
        corruption_log.append(
            {
                "scenario": "blank_summary",
                "count": len(blanked_ids),
                "affected_paper_ids": blanked_ids,
                "description": "Set abstract summary to empty string.",
            }
        )

    # 3. Inject text noise into summary for 2 rows
    if len(corrupted_df) >= 4:
        noise_indices = [2, 3]
        noised_ids = []
        for idx in noise_indices:
            paper_id = corrupted_df.at[idx, "paper_id"]
            orig_sum = str(corrupted_df.at[idx, "summary"])
            corrupted_df.at[idx, "summary"] = f"[NOISE_CORRUPTED_GARBAGE] {orig_sum}"
            noised_ids.append(paper_id)
        corruption_log.append(
            {
                "scenario": "inject_noise",
                "count": len(noised_ids),
                "affected_paper_ids": noised_ids,
                "description": "Injected noise prefix into abstract summary.",
            }
        )

    # 4. Truncate title for 2 rows
    if len(corrupted_df) >= 5:
        trunc_indices = [3, 4]
        trunc_ids = []
        for idx in trunc_indices:
            paper_id = corrupted_df.at[idx, "paper_id"]
            orig_title = str(corrupted_df.at[idx, "title"])
            corrupted_df.at[idx, "title"] = orig_title[:10]
            trunc_ids.append(paper_id)
        corruption_log.append(
            {
                "scenario": "truncate_title",
                "count": len(trunc_ids),
                "affected_paper_ids": trunc_ids,
                "description": "Truncated paper title to 10 characters.",
            }
        )

    # 5. Stale publication date for 2 rows
    if len(corrupted_df) >= 6:
        stale_indices = [4, 5]
        stale_ids = []
        for idx in stale_indices:
            paper_id = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "published"] = "2015-01-01"
            corrupted_df.at[idx, "age_days"] = 3650
            stale_ids.append(paper_id)
        corruption_log.append(
            {
                "scenario": "make_stale_date",
                "count": len(stale_ids),
                "affected_paper_ids": stale_ids,
                "description": "Set published date back to 2015-01-01 (stale).",
            }
        )

    # 6. Add duplicate rows
    if not corrupted_df.empty:
        dup_row = corrupted_df.iloc[[0]].copy()
        dup_id = dup_row.iloc[0]["paper_id"]
        corrupted_df = pd.concat([corrupted_df, dup_row], ignore_index=True)
        corruption_log.append(
            {
                "scenario": "add_duplicate_rows",
                "count": 1,
                "affected_paper_ids": [dup_id],
                "description": "Duplicated first row to introduce duplicate paper_id defect.",
            }
        )

    # 7. Recompute text_for_embedding for all rows so vector store gets corrupted content
    for idx in range(len(corrupted_df)):
        title = corrupted_df.at[idx, "title"]
        authors_joined = corrupted_df.at[idx, "authors_joined"]
        published = corrupted_df.at[idx, "published"]
        categories_joined = corrupted_df.at[idx, "categories_joined"]
        summary = corrupted_df.at[idx, "summary"]
        corrupted_df.at[idx, "summary_chars"] = len(str(summary))
        corrupted_df.at[idx, "text_for_embedding"] = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

    write_json(output_log_path, corruption_log)
    return corrupted_df

