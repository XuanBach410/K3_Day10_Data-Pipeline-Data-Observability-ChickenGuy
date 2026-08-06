# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| Họ và tên | Trần Xuân Bách *(Nhóm trưởng)* |
| MSSV | 01093 |
| Khóa/Lớp | K3 - Data Pipeline & Observability |
| Tên nhóm | ChickenGuy |
| Vai trò chính | Vai trò 4: Evaluation & observability *(Nhóm trưởng)* |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| Synthetic Evaluation Test Set | `src/evaluation/testset.py` | Cleaned DataFrame | `data/eval/test_set.json` (60 samples) | Hoàn thành |
| Metrics Evaluation Pipeline | `src/evaluation/metrics.py` | RAG Answers & Reference | Token F1, Hit Rate, LLM Judge Score | Hoàn thành |
| Data Quality Monitoring | `src/observability/quality.py` | Cleaned/Corrupted DataFrame | `baseline_quality.json`, `corrupted_quality.json` | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py` | Published Dates | `freshness_report.json` | Hoàn thành |
| Observability Reporting | `src/observability/reporting.py` | Metrics & Quality JSONs | `phase1_report.md`, `corruption_report.md` | Hoàn thành |

### Các công việc cụ thể đã hoàn thành trong mốc:
1. Đọc `testset.py`, `metrics.py` để hiểu rõ định dạng câu trả lời và thuật toán tính các chỉ số (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`).
2. Thiết kế 60 QA evaluation pairs thuộc 4 loại câu hỏi (`summary`, `authors`, `date`, `categories`) trực tiếp từ dữ liệu bài báo thực.
3. Gắn `ground_truth_doc_ids` chính xác lấy từ `paper_id` gốc, tuyệt đối không tự bịa ID.
4. Xây dựng 6 tín hiệu Data Observability kiểm tra tự động: Row count, Null paper IDs, Duplicate paper IDs, Null titles, Short summary (< 50 chars), và Freshness staleness.
5. Tổng hợp báo cáo chứng minh thực nghiệm mối quan hệ nhân quả: Data Corruption trực tiếp gây ra suy giảm chất lượng RAG Agent và Data Repair giúp khôi phục 100% chất lượng.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Test Set Generation | `build_test_set` | 60 QA samples chuẩn hóa | `data/eval/test_set.json` |
| Automated Metrics | `evaluate_pipeline` | Metrics Baseline / Corrupted / Repaired | `baseline_metrics.json`, `corrupted_metrics.json` |
| Data Quality Checks | `run_data_quality_checks` | Check 6 tiêu chí Quality | `baseline_quality.json`, `corrupted_quality.json` |
| Freshness Monitoring | `build_freshness_report` | Freshness status (FRESH/STALE) | `freshness_report.json` |
| Markdown Reports | `generate_corruption_report` | Báo cáo so sánh 3 trạng thái | `data/reports/corruption_report.md` |

## 4. Cách xác minh và lệnh chạy

```bash
.venv/bin/pytest tests/test_pipeline.py
.venv/bin/python script/run_phase1.py
.venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** 60 QA samples sinh ra hợp lệ; Data Quality checks báo PASSED cho Baseline & Repaired, FAILED cho Corrupted; Reports được sinh ra tại `data/reports/`.
- **Kết quả thực tế:** Tất cả unit tests và pipeline evaluation đều PASSED 100%, artifacts sinh ra đầy đủ và khớp với Rubric.

## 5. Phân tích kết quả thực nghiệm

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | --: | --: | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Giảm 0.2000 (-20%) ở Corrupted state và phục hồi 100% ở Repaired state |
| `mean_token_f1` | 1.0000 | 0.7892 | 1.0000 | Giảm 0.2108 (-21.08%) do summary rỗng và text noise |
| `judge_accuracy` | 1.0000 | 0.7833 | 1.0000 | Giảm 0.2167 (-21.67%) và phục hồi hoàn toàn sau Repair |
| `mean_judge_score` | 5.00 | 4.13 | 5.00 | Giảm 0.87 points ở Corrupted state |
| Quality Checks Status | PASSED | FAILED | PASSED | Phát hiện chính xác 3/6 tiêu chí chất lượng bị FAILED |
| Freshness Status | FRESH | STALE | FRESH | Cảnh báo chính xác 2 bản ghi có ngày bị biến đổi về 2015-01-01 |

## 6. Cam kết của thành viên (Nhóm trưởng)

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi (Vai trò 4 - Nhóm trưởng).
- [x] Tôi có thể giải thích thuật toán evaluation, data quality checks và freshness monitoring.
- [x] Báo cáo không chứa secret hay API key.

**Họ và tên:** Trần Xuân Bách *(Nhóm trưởng)*  
**Ngày xác nhận:** 2026-08-06
