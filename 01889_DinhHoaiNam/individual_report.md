# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| Họ và tên | Đinh Hoài Nam |
| MSSV | 01889 |
| Khóa/Lớp | K3 - Data Pipeline & Observability |
| Tên nhóm | ChickenGuy |
| Vai trò chính | Vai trò 2: Nền tảng dữ liệu & recovery |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| Crossref Ingestion | `src/ingestion/crossref.py` | Crossref REST API | `crossref_response.json`, `crossref_records.json` | Hoàn thành |
| Data Cleaning | `src/ingestion/cleaning.py` | List `PaperRecord` | `papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Corruption Simulation | `src/ingestion/corruption.py` | Clean DataFrame | `papers_clean_corrupted.csv`, `corruption_log.json` | Hoàn thành |
| Data Repair | `src/ingestion/crossref.py`, `cleaning.py` | Raw snapshot JSON | `papers_clean_repaired.csv`, `papers_clean_repaired.json` | Hoàn thành |

### Các công việc cụ thể đã hoàn thành trong mốc:
1. Đọc Crossref payload và định nghĩa `PaperRecord`; xác định DOI làm `paper_id` ổn định.
2. Hoàn thiện `parse_crossref_payload`, bóc tách thẻ JATS XML (`<jats:p>`), làm sạch HTML, hỗ trợ retry 3 lần với exponential backoff cho lỗi 429/503.
3. Đọc target clean schema, chốt quy tắc xử lý null, date parsing ISO, khử trùng lặp và tính toán `age_days` & `text_for_embedding`.
4. Thiết lập 6 kịch bản data corruption (drop records, blank summary, inject noise, truncate title, stale date, duplicate rows) và ghi log chi tiết `corruption_log.json`.
5. Xây dựng cơ chế Data Repair tái tạo 100% dữ liệu từ raw source snapshot.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Ingestion & Retry | `fetch_source_records` | 24 bản ghi học thuật Crossref | `data/raw/crossref_records.json` |
| Text Cleaning & JATS Parsing | `build_clean_dataframe` | DataFrame 24 hàng chuẩn hóa | `data/clean/papers_clean.csv` |
| Corruption Simulation | `corrupt_clean_dataframe` | 6 kịch bản lỗi + log | `data/results/corruption_log.json` |
| Data Repair | `load_raw_records` + cleaning | Khôi phục 24 bản ghi sạch | `data/clean/papers_clean_repaired.csv` |

## 4. Cách xác minh và lệnh chạy

```bash
.venv/bin/python -c "from ingestion.crossref import fetch_source_records; from core.config import load_settings; print(len(fetch_source_records(load_settings())))"
.venv/bin/pytest tests/test_pipeline.py
```

- **Kết quả mong đợi:** Fetch & parse 24 bản ghi hợp lệ; Unit test `test_parse_crossref_payload`, `test_build_clean_dataframe` và `test_corrupt_clean_dataframe` passing.
- **Kết quả thực tế:** Tất cả unit tests đều PASSED. Dữ liệu raw và clean được khởi tạo đầy đủ.

## 5. Phân tích kết quả thực nghiệm

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | --: | --: | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Việc xóa 2 paper ở step corruption làm mất top-k context |
| `mean_token_f1` | 1.0000 | 0.7892 | 1.0000 | Rỗng summary & noise làm suy giảm từ vựng trùng khớp |
| Data Quality Status | PASSED | FAILED | PASSED | Phát hiện thành công 3/6 lỗi dữ liệu phát sinh |

## 6. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi (Vai trò 2).
- [x] Tôi có thể giải thích chi tiết luồng ingestion, cleaning, corruption và repair.
- [x] Báo cáo không chứa secret hay API key.

**Họ và tên:** Đinh Hoài Nam  
**Ngày xác nhận:** 2026-08-06
