# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| Họ và tên | Trịnh Quốc Trọng |
| MSSV | 01779 |
| Khóa/Lớp | K3 - Data Pipeline & Observability |
| Tên nhóm | ChickenGuy |
| Vai trò chính | Vai trò 3: RAG & agent người phụ trách |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy](file:///Users/tranxuanbach/Documents/Documents/CODE/ALTHUCCHIEN%20/LABS/K3_Day10_Data-Pipeline-Data-Observability-ChickenGuy) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| Vector Indexing | `src/retrieval/index.py` | Cleaned DataFrame | `LocalEmbeddingIndex` (ChromaDB) | Hoàn thành |
| Embedding Provider | `src/retrieval/embeddings.py` | Text strings | 384-dim Dense Vectors / Fallback | Hoàn thành |
| LLM Provider Abstraction | `src/retrieval/llm.py` | Settings & Prompts | LangChain BaseChatModel | Hoàn thành |
| RAG Agent & Tools | `src/retrieval/agent.py`, `qa.py` | Question & Index | RAG Agent execution, Answers | Hoàn thành |

### Các công việc cụ thể đã hoàn thành trong mốc:
1. Đọc `LocalEmbeddingIndex`, `embeddings.py`, `agent.py` để làm rõ contract input/output cho RAG agent.
2. Chốt mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`, đặt tên collection ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) và lưu metadata tối thiểu (`paper_id`, `title`, `published`).
3. Bổ sung lớp `FallbackEmbedder` tự động (sử dụng Token Hashing Vectorizer định dạng 384 chiều) để đảm bảo pipeline chạy mượt mà 100% trong môi trường mạng restricted mà không bị timeout.
4. Chuẩn bị smoke queries cho 2 công cụ chính: `search_papers` (Semantic Search) và `lookup_paper_by_title` (Exact Lookup).

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Embedding Generation | `build_embedder` | MiniLM / Fallback Embedder (384d) | `papers_embeddings.json` |
| Vector Store Indexing | `LocalEmbeddingIndex.build` | Collection ChromaDB HNSW | `data/chroma/` persistence |
| Multi-provider LLM | `build_llm` | Support Gemini, OpenAI, Anthropic, Ollama | `src/retrieval/llm.py` |
| RAG Retrieval QA | `answer_question` | Top-k Context Retrieval + Response | Smoke test queries |

## 4. Cách xác minh và lệnh chạy

```bash
.venv/bin/python -c "from retrieval.embeddings import build_embedder; from core.config import load_settings; emb = build_embedder(load_settings()); print(len(emb.embed_query('test')))"
```

- **Kết quả mong đợi:** Vector đầu ra gồm 384 chiều floating point values; ChromaDB lưu trữ đúng 24 documents.
- **Kết quả thực tế:** Vector embedding khởi tạo chuẩn xác 384 dimensions; ChromaDB index hoạt động ổn định.

## 5. Phân tích kết quả thực nghiệm

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | --: | --: | --: | :--- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Retrieval Hit Rate suy giảm khi dữ liệu bị drop trong Corrupted state |
| `mean_token_f1` | 1.0000 | 0.7892 | 1.0000 | Token F1 khôi phục về mức tuyệt đối 1.0000 sau khi re-index Repaired dataset |
| `mean_judge_score` | 5.00 | 4.13 | 5.00 | Chất lượng câu trả lời của RAG Agent phục hồi hoàn toàn |

## 6. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi (Vai trò 3).
- [x] Tôi có thể giải thích cơ chế embedding, ChromaDB indexing và RAG Agent retrieval.
- [x] Báo cáo không chứa secret hay API key.

**Họ và tên:** Trịnh Quốc Trọng  
**Ngày xác nhận:** 2026-08-06
