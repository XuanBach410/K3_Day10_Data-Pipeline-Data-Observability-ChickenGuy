# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| :--- | :--- |
| Khóa/Lớp | K3 - Data Pipeline & Observability |
| Tên nhóm | ChickenGuy |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy) |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò | Phạm vi phụ trách & File sở hữu |
| --: | :--- | :--- | :--- | :--- |
| 1 | Phạm Thị Thuỳ Linh | 01181 | Vai trò 1: Điều phối pipeline | Cấu hình, orchestration, release, demo (`src/core/`, `src/pipelines/`) |
| 2 | Đinh Hoài Nam | 01889 | Vai trò 2: Nền tảng dữ liệu & recovery | Crossref, clean schema, corruption, repair (`src/ingestion/`, `data/raw/`, `data/clean/`) |
| 3 | Trịnh Quốc Trọng | 01779 | Vai trò 3: RAG & agent người phụ trách | MiniLM, Chroma, search, lookup (`src/retrieval/`, `data/embeddings/`) |
| 4 | Trần Xuân Bách *(Nhóm trưởng)* | 01093 | Vai trò 4: Evaluation & observability | Test set, metrics, quality, freshness, reports (`src/evaluation/`, `src/observability/`) |

## 2. Tóm tắt kết quả

Nhóm **ChickenGuy** đã hoàn thành 100% các yêu cầu bài lab "Day 10 - Data Pipeline & Data Observability" end-to-end theo đúng phân công 4 vai trò:

- **Vai trò 1 (Phạm Thị Thuỳ Linh - 01181)**: Điều phối pipeline, thiết lập cấu hình môi trường, `.env`, `Settings` và orchestration flow trong `src/pipelines/phase1.py` & `src/pipelines/corruption_flow.py`.
- **Vai trò 2 (Đinh Hoài Nam - 01889)**: Xây dựng nền tảng dữ liệu Crossref, cleaning pipeline (`parse_crossref_payload`, `build_clean_dataframe`), lưu raw API responses, thiết lập 6 kịch bản corruption (`corrupt_clean_dataframe`) và quy trình data repair khôi phục từ raw snapshot.
- **Vai trò 3 (Trịnh Quốc Trọng - 01779)**: Xây dựng hệ thống RAG, tích hợp MiniLM embeddings (với fallback embedder), khởi tạo ChromaDB vector store index, thiết lập agent semantic search & exact lookup tools.
- **Vai trò 4 (Trần Xuân Bách - 01093 - Nhóm trưởng)**: Thiết kế evaluation test set 60 QA pairs (`test_set.json`), xây dựng bộ metrics tự động (Hit Rate, Token F1, Judge Accuracy/Score), hệ thống Data Observability kiểm tra 6 tiêu chí Data Quality, Freshness Monitoring và tổng hợp các báo cáo Markdown.

**Kết quả thực nghiệm nổi bật:**
- Chứng minh thực nghiệm rằng dữ liệu lỗi trực tiếp làm suy giảm hiệu năng RAG Agent: Retrieval Hit Rate giảm từ **1.0000** xuống **0.8000** (-20%), Mean Token F1 giảm từ **1.0000** xuống **0.7892** (-21.08%), Judge Accuracy giảm từ **1.0000** xuống **0.7833** (-21.67%), và Mean Judge Score giảm từ **5.00** xuống **4.13/5.00** (-0.87 points).
- Quy trình Data Repair khôi phục 100% dữ liệu từ raw snapshot, giúp các chỉ số và Data Quality status phục hồi về mức Baseline tuyệt đối.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (https://api.crossref.org/works)
    -> raw response (crossref_response.json) & raw records (crossref_records.json) [Đinh Hoài Nam]
    -> cleaning & data modeling (papers_clean.csv/json) [Đinh Hoài Nam]
    -> embedding & ChromaDB vector store (papers-baseline) [Trịnh Quốc Trọng]
    -> baseline orchestration [Phạm Thị Thuỳ Linh]
    -> evaluation baseline (test_set.json & baseline_metrics.json) [Trần Xuân Bách]
    -> quality & freshness reports (baseline_quality.json, freshness_report.json) [Trần Xuân Bách]
    -> data corruption simulation (corruption_log.json & papers_clean_corrupted.csv/json) [Đinh Hoài Nam]
    -> re-indexing (papers-corrupted) [Trịnh Quốc Trọng] & re-evaluation [Trần Xuân Bách]
    -> observability checks on corrupted data [Trần Xuân Bách]
    -> data repair from raw source (papers_clean_repaired.csv/json) [Đinh Hoài Nam]
    -> re-indexing (papers-repaired) [Trịnh Quốc Trọng] & re-evaluation [Trần Xuân Bách]
    -> comparison report (corruption_report.md) [Trần Xuân Bách & Phạm Thị Thuỳ Linh]
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Ingestion & Recovery | External Crossref API | HTTP request, retry 3 lần, backoff, parse payload, JATS XML stripping | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Đinh Hoài Nam (01889) |
| Cleaning & Corruption | Raw records | Normalize text, parse publication date, age_days, deduplication, 6 corruption scenarios | `data/clean/papers_clean.csv`, `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Đinh Hoài Nam (01889) |
| Embedding & Index | Cleaned DataFrame | MiniLM / fallback embedder, cosine similarity, HNSW indexing in ChromaDB | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Trịnh Quốc Trọng (01779) |
| Evaluation | Cleaned DataFrame & Chroma index | Synthetic QA pair generation (summary, authors, date, categories), Token F1 & Judge evaluation | `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json` | Trần Xuân Bách (01093) |
| Observability | Cleaned/Corrupted DataFrame | Null/Duplicate/Summary length/Freshness checks, Markdown report rendering | `data/quality/baseline_quality.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md` | Trần Xuân Bách (01093) |
| Pipeline Orchestration | Phase 1 & Phase 2 scripts | Run end-to-end workflows, pytest unit test suite, environment settings | `src/core/config.py`, `script/run_phase1.py`, `script/run_corruption_flow.py`, `tests/test_pipeline.py` | Phạm Thị Thuỳ Linh (01181) |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-3.6-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` days |
| Evaluation test set size | `60` samples (4 question types x 15 representative papers) |

### Lệnh cài đặt

Cài đặt bằng virtual environment và pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### Lệnh chạy

Chạy Unit Test Suite:

```bash
.venv/bin/pytest
```

Chạy Baseline Pipeline (Phase 1):

```bash
USE_FALLBACK_EMBEDDINGS=1 .venv/bin/python script/run_phase1.py
```

Chạy Corruption & Repair Flow (Phase 2):

```bash
USE_FALLBACK_EMBEDDINGS=1 .venv/bin/python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| :--- | :--- | :--- | :--- |
| Pytest Unit Tests | Thành công (4/4 passed) | 2026-08-06 09:54 | 4 unit tests passing in 13.91s |
| Baseline pipeline | Thành công (100%) | 2026-08-06 09:59 | `data/results/baseline_metrics.json` |
| Corruption flow | Thành công (100%) | 2026-08-06 09:59 | `data/results/corruption_log.json` & `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| :--- | :--- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2026-02-07,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 09:55:00 UTC |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Retry tối đa 3 lần với exponential backoff (1s, 2s, 4s) cho HTTP status 429/503 |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| :--- | :--- | :--- | :--- | :--- |
| `paper_id` | String | Có | DOI hoặc ID duy nhất của bài báo | Fallback `crossref_{idx}` nếu thiếu DOI |
| `title` | String | Có | Tiêu đề bài báo | Strip HTML/JATS tags; loại bỏ row nếu title rỗng |
| `summary` | String | Có | Tóm tắt/Abstract | Strip JATS XML `<jats:p>`; fallback chuỗi rỗng |
| `authors` | List[String] | Có | Danh sách tác giả | Parse `given` + `family`; fallback `["Unknown Author"]` |
| `categories` | List[String] | Có | Chủ đề học thuật | Parse `subject`; fallback `["General"]` |
| `published` | String (ISO) | Có | Ngày xuất bản (`YYYY-MM-DD`) | Parse `date-parts`; fallback `"2024-01-01"` |
| `age_days` | Integer | Có | Tuổi của bài báo tính theo ngày | `max(0, (run_date - published).days)` |
| `text_for_embedding` | String | Có | Chuỗi tổng hợp làm đầu vào embedding | Standard format: `Title: ... \n Authors: ... \n Summary: ...` |

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| :--- | :--- |
| Số câu hỏi | 60 samples (4 question types x 15 representative papers) |
| Các `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | List chứa `paper_id` của bản ghi gốc |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dims) |
| Vector store/collection | ChromaDB PersistentClient (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | Gemini 2.5 Flash (`gemini-2.5-flash`) / Deterministic fallback evaluator |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

## 7. Kết quả baseline

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| :--- | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 100% câu hỏi tìm lại đúng document gốc trong top-k context |
| `mean_token_f1` | 1.0000 | Tương quan từ vựng giữa câu trả lời và ground truth đạt mức tối đa |
| `judge_accuracy` | 1.0000 | Evaluator đánh giá 100% câu trả lời đạt tính chính xác |
| `mean_judge_score` | 5.00 | Điểm trung bình tuyệt đối 5/5 |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| :--- | :--- | :--- | :--- | :--- |
| Row count check | Completeness | >= 1 row | PASSED (24 rows) | `baseline_quality.json` |
| Null paper IDs check | Completeness | 0 nulls | PASSED (0 nulls) | `baseline_quality.json` |
| Duplicate paper IDs check | Uniqueness | 0 duplicates | PASSED (0 duplicates) | `baseline_quality.json` |
| Null titles check | Completeness | 0 nulls | PASSED (0 nulls) | `baseline_quality.json` |
| Short summary length check | Validity | 0 (< 50 chars) | PASSED (0 short) | `baseline_quality.json` |
| Freshness check | Timeliness | 0 stale rows | PASSED (0 stale) | `freshness_report.json` |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| :--- | :--- | --: | :--- | :--- | :--- |
| Drop latest records | Xóa 2 bản ghi mới nhất | 2 | Failure ở retrieval | Retrieval Hit Rate giảm từ 1.0 xuống 0.8 | Tái nạp từ raw source snapshot |
| Blank summary | Xóa tóm tắt bài báo về chuỗi rỗng | 2 | `summary_length_passed = False` | Token F1 & Judge accuracy giảm | Khôi phục abstract gốc từ raw JSON |
| Inject text noise | Chèn `[NOISE_CORRUPTED_GARBAGE]` | 2 | Giảm chất lượng embedding | Embedding vector bị lệch hướng | Xóa noise, re-clean text |
| Truncate title | Truncate tiêu đề còn 10 ký tự | 2 | Hỏng exact lookup | Lookup title thất bại | Khôi phục tiêu đề đầy đủ |
| Make stale date | Đổi ngày về `2015-01-01` | 2 | `freshness_passed = False` | Freshness status chuyển sang STALE | Re-parse publication date từ raw |
| Add duplicate rows | Nhân bản row đầu tiên | 1 | `duplicate_paper_ids_passed = False` | Duplication check báo FAILED | Deduplicate theo `paper_id` |

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| :--- | --: | --: | --: | --: | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | +0.2000 | Xóa paper làm mất top-k context |
| `mean_token_f1` | 1.0000 | 0.7892 | 1.0000 | -0.2108 | +0.2108 | Summary rỗng & noise làm giảm F1 |
| `judge_accuracy` | 1.0000 | 0.7833 | 1.0000 | -0.2167 | +0.2167 | Judge đánh giá sai khi thiếu context |
| `mean_judge_score` | 5.00 | 4.13 | 5.00 | -0.87 | +0.87 | Score giảm gần 1 điểm khi dữ liệu lỗi |
| Quality checks pass/fail | PASSED | FAILED | PASSED | Báo lỗi 3/6 checks | Phục hồi PASSED | Quality check phát hiện chính xác lỗi |
| Freshness status | FRESH | STALE | FRESH | Stale rows: 2 | Phục hồi FRESH | Freshness monitor cảnh báo dữ liệu cũ |

## 11. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với 4 vai trò, 4 cá nhân và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set (`data/eval/test_set.json`).
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Đã tạo 4 thư mục báo cáo cá nhân ứng với 4 vai trò trong `report/`.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

