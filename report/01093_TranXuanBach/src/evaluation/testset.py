from __future__ import annotations

from typing import Any

import pandas as pd


from typing import Any
import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build evaluation test set from clean DataFrame."""
    if df.empty:
        raise ValueError("Cannot build test set from empty DataFrame.")

    test_set: list[dict[str, Any]] = []
    counter = 1

    # Select representative papers (up to 15 papers to keep evaluation fast & precise)
    sample_df = df.head(15)

    for _, row in sample_df.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]
        summary = row["summary"]
        authors_joined = row["authors_joined"]
        published = row["published"]
        categories_joined = row["categories_joined"]

        # Question type 1: summary / abstract
        gt_summary = first_sentence(summary) if summary else title
        test_set.append(
            {
                "id": f"eval_{counter:03d}",
                "question_type": "summary",
                "question": f"What is the main summary of the paper '{title}'?",
                "ground_truth": gt_summary,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        counter += 1

        # Question type 2: authors
        test_set.append(
            {
                "id": f"eval_{counter:03d}",
                "question_type": "authors",
                "question": f"Who authored the paper '{title}'?",
                "ground_truth": authors_joined,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        counter += 1

        # Question type 3: publication date
        test_set.append(
            {
                "id": f"eval_{counter:03d}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        counter += 1

        # Question type 4: categories
        test_set.append(
            {
                "id": f"eval_{counter:03d}",
                "question_type": "categories",
                "question": f"What categories does the paper '{title}' belong to?",
                "ground_truth": categories_joined,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        counter += 1

    write_json(output_path, test_set)
    return test_set

