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


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        # Extract fields safely
        doi = item.get("DOI", "")
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        
        abstract = item.get("abstract", "")
        # Remove common html tags from abstract if present
        abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "").strip()
        
        authors_list = item.get("author", [])
        authors = []
        for author in authors_list:
            given = author.get("given", "")
            family = author.get("family", "")
            authors.append(f"{given} {family}".strip())
            
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        # Publish date
        published = ""
        pub_date = item.get("published-print", item.get("published-online", {}))
        date_parts = pub_date.get("date-parts", [[]])[0]
        if len(date_parts) >= 3:
            published = f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
        elif len(date_parts) >= 2:
            published = f"{date_parts[0]:04d}-{date_parts[1]:02d}-01"
        elif len(date_parts) == 1:
            published = f"{date_parts[0]:04d}-01-01"
            
        updated = published # Crossref doesn't always have updated, use published
        
        abs_url = item.get("URL", "")
        pdf_url = item.get("link", [{"URL": ""}])[0].get("URL", "")
        
        if doi and title and abstract: # Minimum requirements
            record = PaperRecord(
                paper_id=doi,
                title=title,
                summary=abstract,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=""
            )
            records.append(record)
            
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records."""
    import requests
    import time
    import json
    
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "mailto": "vibe_coding_demo@example.com" # Good practice for Crossref API
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                payload = response.json()
                
                # Create directory if it doesn't exist
                settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
                
                # Save raw response
                with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                    
                records = parse_crossref_payload(payload)
                
                # Save parsed records as JSON
                records_dicts = [r.__dict__ for r in records]
                with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
                    json.dump(records_dicts, f, indent=2, ensure_ascii=False)
                    
                return records
            
            elif response.status_code in [429, 502, 503, 504]:
                print(f"API Rate limit or server error: {response.status_code}. Retrying...")
                time.sleep(2 ** attempt)
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch from Crossref API after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)
            
    return []


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    import json
    if not path.exists():
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        records_dicts = json.load(f)
        
    return [PaperRecord(**r) for r in records_dicts]
