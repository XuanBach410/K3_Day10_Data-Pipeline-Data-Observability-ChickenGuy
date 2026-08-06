# 📋 Báo cáo Nhiệm vụ — Đinh Hoài Nam (MSSV: 01889)

> **Vai trò 2 — Data Ingestion & Recovery**
> **Project:** Day 10 — Data Pipeline & Data Observability | Group ChickenGuy

---

## 👤 Thông tin thành viên

| Trường    | Thông tin                              |
|-----------|----------------------------------------|
| Họ và tên | Đinh Hoài Nam                          |
| MSSV      | 01889                                  |
| Vai trò   | Vai trò 2 — Data Ingestion & Recovery  |
| Branch    | `feature/role2-data-ingestion-recovery` |

---

## ✅ Nhiệm vụ được giao

1. Tạo branch `feature/role2-data-ingestion-recovery` từ `main`.
2. Commit báo cáo cá nhân `report/01889_DinhHoaiNam/` và các file `src/ingestion/`.
3. Push lên GitHub và tạo Pull Request vào `main`.

---

## 📁 Các file đã commit

### Báo cáo cá nhân
```
01889_DinhHoaiNam/
├── individual_report.md
└── src/
    └── ingestion/
        ├── cleaning.py
        ├── corruption.py
        └── crossref.py
```

### Source code chính (repo root)
```
src/ingestion/
├── __init__.py
├── cleaning.py
├── corruption.py
└── crossref.py
```

---

## 🔧 Bộ lệnh Git đã thực hiện

```bash
git checkout main
git pull origin main
git checkout -b feature/role2-data-ingestion-recovery
git add report/01889_DinhHoaiNam/
git add src/ingestion/
git commit -m "feat(role2): complete Crossref ingestion, cleaning, corruption & repair flow"
git push -u origin feature/role2-data-ingestion-recovery
```

---

## 📊 Kết quả thực hiện

| Bước | Lệnh                          | Trạng thái |
|------|-------------------------------|-----------|
| 1    | `git checkout main`           | ✅ Thành công |
| 2    | `git pull origin main`        | ✅ Already up to date |
| 3    | `git checkout -b feature/...` | ✅ Branch mới tạo thành công |
| 4    | `git add` các file            | ✅ 4 files staged |
| 5    | `git commit`                  | ✅ Commit `7909066` — 4 files, 573 insertions |
| 6    | `git push -u origin`          | ✅ Push thành công |

---

## 🔗 Pull Request

- **Branch:** `feature/role2-data-ingestion-recovery` → `main`
- **GitHub URL:** https://github.com/XuanBach410/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy/pull/new/feature/role2-data-ingestion-recovery
- **Commit message:** `feat(role2): complete Crossref ingestion, cleaning, corruption & repair flow`

---

## 🏗️ Data Pipeline Architecture — Chi tiết kỹ thuật

### Tổng quan luồng xử lý (Phase 1 Baseline)

```
Crossref API
     │
     ▼
[1] fetch_source_records()       ← crossref.py
     │   - HTTP GET với retry/backoff (max 3 lần)
     │   - Rate limit 429/503 → exponential backoff
     │   - Fallback: cached JSON snapshot → mock data
     │
     ▼
[2] parse_crossref_payload()     ← crossref.py
     │   - Parse JSON response → list[PaperRecord]
     │   - Strip HTML/JATS XML tags khỏi abstract
     │   - Extract DOI, title, authors, subjects, dates, URLs
     │
     ▼
[3] build_clean_dataframe()      ← cleaning.py
     │   - Normalize whitespace toàn bộ trường
     │   - Fallback: author="Unknown Author", category="General"
     │   - Tính age_days = run_date - published_date
     │   - Tạo text_for_embedding cho ChromaDB
     │   - Dedup by paper_id (keep first), dedup by title
     │   - Sort theo published DESC
     │
     ▼
[4] LocalEmbeddingIndex.build()  ← retrieval/index.py
     │   - Nhúng text_for_embedding vào ChromaDB
     │   - Embedding model: all-MiniLM-L6-v2
     │
     ▼
[5] evaluate_pipeline()          ← evaluation/metrics.py
     │   - Retrieval Hit Rate, Mean Token F1
     │   - Judge Accuracy, Mean Judge Score
     │
     ▼
[6] run_data_quality_checks()    ← observability/quality.py
     │   - 6 checks: row_count, null_ids, dup_ids, null_titles,
     │               short_summaries, freshness
     │
     ▼
[7] generate_phase1_report()     ← observability/reporting.py
         - Markdown report tổng hợp kết quả
```

---

## 📦 Module Chi tiết

### `crossref.py` — Thu thập dữ liệu từ Crossref API

**Dataclass `PaperRecord`** — schema chuẩn hoá:

| Field             | Kiểu           | Mô tả                          |
|-------------------|----------------|-------------------------------|
| `paper_id`        | `str`          | DOI hoặc `crossref_{idx}`     |
| `title`           | `str`          | Tiêu đề bài báo               |
| `summary`         | `str`          | Abstract (đã strip HTML/JATS) |
| `authors`         | `list[str]`    | Danh sách tên tác giả         |
| `categories`      | `list[str]`    | Chủ đề / subject areas        |
| `primary_category`| `str`          | Chủ đề chính                  |
| `published`       | `str`          | `YYYY-MM-DD`                  |
| `updated`         | `str`          | `YYYY-MM-DD`                  |
| `abs_url`         | `str`          | URL bài báo                   |
| `pdf_url`         | `str`          | URL PDF (nếu có)              |
| `comment`         | `str`          | Tên journal/publisher         |

**Hàm chính:**

```python
fetch_source_records(settings) -> list[PaperRecord]
```
- Endpoint: `GET https://api.crossref.org/works`
- Params: `query`, `filter`, `rows` (từ Settings)
- Header: `User-Agent: Day10DataObservabilityLab/1.0`
- **Retry strategy:**
  - Max 3 lần
  - HTTP 429/503 → exponential backoff (1s → 2s → 4s)
  - Exception → backoff rồi retry
- **Fallback chain:** API → cached JSON → mock data (2 bản ghi mẫu)
- Cache: lưu raw API response + parsed records thành `.json`

**Parser:**

```python
parse_crossref_payload(payload) -> list[PaperRecord]
```
- Strip HTML tags: `re.sub(r"<[^>]+>", " ", text)`
- Extract date từ `date-parts: [[year, month, day]]`
- Fallback date: `"2024-01-01"` nếu format sai
- Bỏ qua record không có title (skip)

---

### `cleaning.py` — Làm sạch & chuẩn hoá dữ liệu

**Hàm chính:**

```python
build_clean_dataframe(records, run_date) -> pd.DataFrame
```

**Các bước xử lý:**

| Bước | Xử lý                                                       |
|------|-------------------------------------------------------------|
| 1    | `normalize_whitespace()` cho title, summary, authors, categories |
| 2    | Skip record nếu title rỗng sau normalize                    |
| 3    | Fallback authors = `["Unknown Author"]` nếu rỗng           |
| 4    | Fallback categories = `["General"]` nếu rỗng               |
| 5    | Parse published date → tính `age_days` (so với run_date)   |
| 6    | Tạo `text_for_embedding` gộp title + authors + date + categories + summary |
| 7    | `drop_duplicates(subset=["paper_id"], keep="first")`        |
| 8    | `drop_duplicates(subset=["title"], keep="first")`           |
| 9    | Sort by `published` DESC                                    |

**Output DataFrame columns:**

```
paper_id | title | summary | authors | categories | primary_category
published | updated | abs_url | pdf_url | comment
authors_joined | categories_joined | summary_chars | age_days | text_for_embedding
```

---

### `corruption.py` — Mô phỏng lỗi dữ liệu (Data Quality Testing)

**Hàm chính:**

```python
corrupt_clean_dataframe(df, output_log_path) -> pd.DataFrame
```

Inject **6 loại lỗi có kiểm soát** vào DataFrame:

| # | Scenario               | Mô tả                                          | Điều kiện    |
|---|------------------------|------------------------------------------------|--------------|
| 1 | `drop_latest_records`  | Xoá 2 bản ghi mới nhất (test missing paper)    | `len >= 4`   |
| 2 | `blank_summary`        | Set abstract = `""` cho 2 rows                 | `len >= 2`   |
| 3 | `inject_noise`         | Thêm prefix `[NOISE_CORRUPTED_GARBAGE]` vào 2 rows | `len >= 4` |
| 4 | `truncate_title`       | Cắt title còn 10 ký tự cho 2 rows             | `len >= 5`   |
| 5 | `make_stale_date`      | Set published = `"2015-01-01"`, age_days=3650  | `len >= 6`   |
| 6 | `add_duplicate_rows`   | Nhân bản row đầu tiên (test duplicate paper_id) | `not empty` |
| 7 | Recompute              | Cập nhật `text_for_embedding` với nội dung đã corrupt | always |

- Ghi log tất cả thay đổi vào file JSON: `output_log_path`
- Mỗi log entry: `{scenario, count, affected_paper_ids, description}`

---

## 🔭 Data Observability — Chi tiết kỹ thuật

### Quality Checks (`observability/quality.py`)

**Hàm `run_data_quality_checks(df, settings, report_name)`** chạy **6 checks**:

| Check                      | Điều kiện PASS                    | Metric                     |
|----------------------------|-----------------------------------|---------------------------|
| `row_count_passed`         | `total_rows >= 1`                 | Tổng số bản ghi           |
| `null_paper_ids_passed`    | `null_paper_ids == 0`             | Null hoặc empty paper_id  |
| `duplicate_paper_ids_passed` | `duplicate_paper_ids == 0`      | Bản ghi trùng paper_id    |
| `null_titles_passed`       | `null_titles == 0`               | Null hoặc empty title     |
| `summary_length_passed`    | `short_summaries == 0`           | Summary < 50 ký tự        |
| `freshness_passed`         | `stale_rows == 0`                | `age_days > threshold`    |

- `success = all(checks.values())` — PASS khi toàn bộ 6 checks đều pass
- Kết quả lưu thành JSON tại `settings.paths.quality_dir/{report_name}.json`

**Hàm `build_freshness_report(df, settings, report_path)`:**

```json
{
  "latest_published": "2024-06-15",
  "oldest_published": "2024-01-01",
  "freshness_threshold_days": 365,
  "stale_rows": 2,
  "total_rows": 10,
  "is_fresh": false
}
```

### So sánh baseline vs corrupted

| Metric                  | Baseline (clean) | Corrupted (sau inject lỗi) |
|-------------------------|------------------|---------------------------|
| `null_paper_ids_passed` | ✅ PASS           | ✅ PASS (paper_id không bị đụng) |
| `duplicate_paper_ids_passed` | ✅ PASS      | ❌ FAIL (scenario 6 inject dup) |
| `null_titles_passed`    | ✅ PASS           | ❌ FAIL (scenario 4 truncate)   |
| `summary_length_passed` | ✅ PASS           | ❌ FAIL (scenario 2 blank)      |
| `freshness_passed`      | ✅ PASS           | ❌ FAIL (scenario 5 stale date) |
| **success**             | ✅ **PASSED**     | ❌ **FAILED**                   |

---

## 🔄 Pipeline Flow End-to-End (Phase 1)

```
phase1.py::main()
├── [1] fetch_source_records(settings)     → raw_records: list[PaperRecord]
├── [2] build_clean_dataframe(raw, date)  → df_clean: pd.DataFrame
│       ├── Lưu clean_dataset.csv
│       └── Lưu clean_dataset.json
├── [3] LocalEmbeddingIndex.build(df)     → ChromaDB vector index
├── [4] build_test_set(df)               → eval_testset.json
├── [5] evaluate_pipeline(...)           → metrics: hit_rate, f1, accuracy
├── [6] run_data_quality_checks(df)      → quality_report.json
│       └── build_freshness_report(df)   → freshness_report.json
└── [7] generate_phase1_report(...)      → baseline_report.md
```

**Artifacts sinh ra sau pipeline:**

| File                    | Nội dung                             |
|-------------------------|--------------------------------------|
| `raw_api_response.json` | Payload thô từ Crossref API          |
| `raw_records.json`      | Records đã parse thành PaperRecord   |
| `clean_dataset.csv`     | DataFrame sau bước cleaning          |
| `clean_dataset.json`    | Dạng JSON của clean DataFrame        |
| `embeddings.json`       | Manifest embedding ChromaDB          |
| `baseline_quality.json` | Kết quả 6 quality checks (baseline)  |
| `freshness_report.json` | Freshness report                     |
| `baseline_metrics.json` | Hit Rate, F1, Judge Score            |
| `baseline_report.md`    | Markdown report tổng hợp            |

---

## ⏱️ Thời gian thực hiện

- **Ngày thực hiện:** 2026-08-06
- **Thời gian push:** ~10:30 (GMT+7)
- **Merge vào main:** Sau khi PR được approve

---

*Document được tạo để ghi lại quá trình làm việc của Đinh Hoài Nam trong Day 10 Codelab tại VinUni.*
