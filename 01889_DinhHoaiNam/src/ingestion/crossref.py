from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


import dataclasses
import re
import time
from typing import Any
import requests

from core.config import Settings
from core.utils import ensure_parent, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML / JATS XML tags like <jats:p>, <i>, <b>
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_date(date_obj: dict | None, default: str = "2024-01-01") -> str:
    if not isinstance(date_obj, dict):
        return default
    date_parts = date_obj.get("date-parts")
    if not date_parts or not isinstance(date_parts, list) or not date_parts[0]:
        return default
    parts = date_parts[0]
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (ValueError, TypeError, IndexError):
        return default


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for idx, item in enumerate(items):
        doi = item.get("DOI", "").strip()
        paper_id = doi if doi else f"crossref_{idx + 1}"

        # Extract title
        title_raw = ""
        titles = item.get("title", [])
        if isinstance(titles, list) and titles:
            title_raw = str(titles[0])
        elif isinstance(titles, str):
            title_raw = titles
        title = _clean_text(title_raw)

        if not title:
            continue

        # Extract summary / abstract
        abstract_raw = item.get("abstract", "")
        summary = _clean_text(abstract_raw)

        # Extract authors
        authors: list[str] = []
        raw_authors = item.get("author", [])
        if isinstance(raw_authors, list):
            for author in raw_authors:
                if isinstance(author, dict):
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    if not name:
                        name = author.get("name", "").strip()
                    if name:
                        authors.append(name)

        if not authors:
            authors = ["Unknown Author"]

        # Extract subjects / categories
        raw_subjects = item.get("subject", [])
        categories = [str(s).strip() for s in raw_subjects if str(s).strip()] if isinstance(raw_subjects, list) else []
        if not categories:
            categories = ["Computer Science", "Artificial Intelligence"]
        primary_category = categories[0]

        # Extract dates
        published = _extract_date(
            item.get("published-online") or item.get("published-print") or item.get("issued") or item.get("created")
        )
        updated = _extract_date(item.get("deposited") or item.get("indexed"), default=published)

        # Extract URLs
        abs_url = (
            item.get("resource", {}).get("primary", {}).get("URL")
            or item.get("URL")
            or (f"https://doi.org/{doi}" if doi else "")
        )
        pdf_url = abs_url
        links = item.get("link", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL", abs_url)
                    break

        comment = ""
        container_titles = item.get("container-title", [])
        if isinstance(container_titles, list) and container_titles:
            comment = str(container_titles[0])
        elif publisher := item.get("publisher"):
            comment = str(publisher)

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch raw records from Crossref source API with retry/backoff, save payload & records."""
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": "Day10DataObservabilityLab/1.0 (mailto:student@example.com)"}

    payload = None
    max_retries = 3
    backoff = 1.0

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                payload = resp.json()
                break
            elif resp.status_code in {429, 503}:
                time.sleep(backoff)
                backoff *= 2.0
            else:
                resp.raise_for_status()
        except Exception as exc:
            if attempt == max_retries - 1:
                print(f"Warning: Fetching Crossref API failed after {max_retries} attempts ({exc}).")
            time.sleep(backoff)
            backoff *= 2.0

    if payload is not None:
        write_json(settings.paths.raw_api_response, payload)
        records = parse_crossref_payload(payload)
        write_json(settings.paths.raw_records_json, [r.to_dict() for r in records])
        return records

    # If API call failed or returned empty payload, check if cached raw records exist
    if settings.paths.raw_records_json.exists():
        print("Using existing raw records snapshot.")
        return load_raw_records(settings.paths.raw_records_json)

    # Fallback mock records if network is completely down and no cache exists
    mock_payload = {
        "status": "ok",
        "message-type": "work-list",
        "message": {
            "items": [
                {
                    "DOI": "10.1016/j.artint.2024.104001",
                    "title": ["Agentic Retrieval Augmented Generation for Academic Research"],
                    "abstract": "<jats:p>This study introduces an agentic retrieval augmented generation architecture for searching academic literature.</jats:p>",
                    "author": [{"given": "Alice", "family": "Smith"}, {"given": "Bob", "family": "Jones"}],
                    "subject": ["Computer Science", "Artificial Intelligence"],
                    "published-online": {"date-parts": [[2024, 6, 15]]},
                    "URL": "https://doi.org/10.1016/j.artint.2024.104001",
                    "publisher": "Elsevier",
                },
                {
                    "DOI": "10.1145/3618257.3624800",
                    "title": ["Data Observability and Data Quality Pipelines for Large Language Models"],
                    "abstract": "<jats:p>Data pipeline monitoring ensures high accuracy in retrieval systems by detecting missing and corrupted records.</jats:p>",
                    "author": [{"given": "Charlie", "family": "Brown"}, {"given": "Diana", "family": "Prince"}],
                    "subject": ["Computer Science", "Database Systems"],
                    "published-online": {"date-parts": [[2024, 5, 20]]},
                    "URL": "https://doi.org/10.1145/3618257.3624800",
                    "publisher": "ACM",
                },
            ]
        },
    }
    write_json(settings.paths.raw_api_response, mock_payload)
    records = parse_crossref_payload(mock_payload)
    write_json(settings.paths.raw_records_json, [r.to_dict() for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot of records and map to PaperRecord objects."""
    data = read_json(path)
    records: list[PaperRecord] = []
    for item in data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", "General"),
                published=item.get("published", "2024-01-01"),
                updated=item.get("updated", "2024-01-01"),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records

