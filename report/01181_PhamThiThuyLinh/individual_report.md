# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| Họ và tên | Phạm Thị Thuỳ Linh |
| MSSV | 01181 |
| Khóa/Lớp | K3 - Data Pipeline & Observability |
| Tên nhóm | ChickenGuy |
| Vai trò chính | Vai trò 1: Điều phối pipeline |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| Configuration & Environment | `src/core/config.py`, `src/core/utils.py` | Environment vars, `.env` | Class `Settings`, `Paths` | Hoàn thành |
| Baseline Orchestration | `src/pipelines/phase1.py` | Raw data & Clean DF | End-to-end Baseline Pipeline | Hoàn thành |
| Corruption & Repair Flow | `src/pipelines/corruption_flow.py` | Corrupted & Repaired DFs | End-to-end Corruption Flow | Hoàn thành |
| Pipeline Execution Scripts | `script/run_phase1.py`, `script/run_corruption_flow.py` | Entrypoint calls | Pipeline execution | Hoàn thành |

### Các công việc cụ thể đã hoàn thành trong mốc:
1. Chốt tiêu chuẩn phụ tráchship, branch, tiêu chí hoàn thành và đường dẫn artifacts chuẩn trong `Paths`.
2. Kiểm tra tương thích Python 3.11–3.13, dependencies trong `pyproject.toml`, provider config và `.env` cục bộ.
3. Lập sơ đồ handoff và điều phối luồng dữ liệu end-to-end: `raw -> clean -> index -> evaluate -> report`.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Environment Setup | `src/core/config.py` | `load_settings()`, `require_llm_credentials()` | `python -c "from core.config import load_settings; load_settings()"` |
| Baseline Pipeline | `src/pipelines/phase1.py` | Run Pha 1 thành công | `python script/run_phase1.py` |
| Corruption Pipeline | `src/pipelines/corruption_flow.py` | Run Pha 2 thành công | `python script/run_corruption_flow.py` |

## 4. Cách xác minh và lệnh chạy

```bash
.venv/bin/python script/run_phase1.py
.venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Pha 1 sinh đầy đủ baseline artifacts; Pha 2 sinh đầy đủ corrupted, repaired artifacts và comparison report.
- **Kết quả thực tế:** Cả 2 scripts chạy mượt mà 100%, tạo đầy đủ 100% artifacts trong `data/`.

## 5. Phân tích kết quả thực nghiệm

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | --: | --: | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Baseline và Repaired đạt mức tối đa 1.0000 |
| `mean_token_f1` | 1.0000 | 0.7892 | 1.0000 | Token F1 suy giảm do dữ liệu nhiễu trong Corrupted flow |
| `judge_accuracy` | 1.0000 | 0.7833 | 1.0000 | Phục hồi hoàn toàn sau bước Repair |
| `mean_judge_score` | 5.00 | 4.13 | 5.00 | Mean score khôi phục về 5.00 tuyệt đối |

## 6. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi (Vai trò 1).
- [x] Tôi có thể giải thích luồng end-to-end orchestration của pipeline.
- [x] Báo cáo không chứa secret hay API key.

**Họ và tên:** Phạm Thị Thuỳ Linh  
**Ngày xác nhận:** 2026-08-06
