# Báo Cáo Phân Tích Data Pipeline & Data Observability (RAG System)

**Tác giả:** Trịnh Quốc Trọng (2A202601779)
**Vai trò phụ trách:** AI Engineer (Retrieval & RAG) & Data Ingestion

---

## 1. Tổng quan Hệ thống và Cấu trúc Mã nguồn (10 điểm)
Hệ thống được thiết kế theo mô hình kiến trúc phân lớp (layered architecture), tuân thủ chặt chẽ việc chia module rõ ràng để đảm bảo tính dễ đọc và dễ bảo trì:
*   `ingestion/`: Quản lý việc kéo dữ liệu thô (raw) từ API Crossref và làm sạch dữ liệu qua Pandas.
*   `retrieval/`: Chịu trách nhiệm tạo embedding, lưu vào ChromaDB và vận hành RAG Agent (LLM).
*   `evaluation/` & `observability/`: Giám sát chất lượng dữ liệu, đánh giá độ chính xác của câu trả lời.
*   `pipelines/`: Điều phối các module trên thành một quy trình tự động hoàn chỉnh.

## 2. Quy trình Xử lý Dữ liệu (Raw Ingestion & Cleaning) (30 điểm)
### 2.1. Lấy dữ liệu (Data Fetching)
*   **Nguồn:** Dữ liệu báo cáo học thuật được lấy qua Crossref REST API.
*   **Chiến lược:** Có cơ chế retry backoff tự động khi gặp lỗi 429/503 để chống sập API.
*   **Lưu vết (Traceability):** Cả kết quả response gốc từ API và record đã parse đều được lưu dưới dạng file JSON tại thư mục `data/raw/` để truy xuất và sửa chữa khi hệ thống gặp sự cố.

### 2.2. Làm sạch (Cleaning & Modeling)
*   Dữ liệu được làm sạch bằng `pandas`. Các bản ghi thiếu `title` hoặc `summary` bị loại bỏ vì không mang giá trị cho RAG.
*   Trường `text_for_embedding` được tổng hợp cẩn thận từ: Tiêu đề, Tác giả, Ngày xuất bản và Tóm tắt. Đây là phần cốt lõi giúp hệ thống AI hiểu được ngữ cảnh bài báo.

## 3. Hệ thống Retrieval & RAG Agent (10 điểm)
*   **Embedding Model:** Sử dụng `sentence-transformers/all-MiniLM-L6-v2` chuyên trị các tác vụ phân cụm ngữ nghĩa.
*   **Vector Database:** `ChromaDB` được sử dụng để xây dựng local corpus.
*   **RAG Agent:** Được tích hợp bằng `Langchain`, sử dụng mô hình LLM từ Google (Gemini) hoặc OpenAI. Agent có khả năng semantic search và lookup chính xác paper theo ID, mang lại câu trả lời bám sát nguồn dữ liệu.

## 4. Giám sát Dữ liệu & Đánh giá (Data Observability & Evaluation) (10 điểm)
Hệ thống tích hợp quy trình Observability ngay trên đường ống dữ liệu (Data Pipeline) trước khi đẩy vào AI:
*   **Quality Checks:** Giám sát tỷ lệ Null ở các trường quan trọng (đặc biệt là `summary`), ngăn chặn bản ghi trùng lặp (Duplicate IDs).
*   **Freshness:** Tính toán biến `age_days` để đảm bảo bài báo không quá lỗi thời, cảnh báo nếu dữ liệu quá 180 ngày chưa được làm mới.

---

## 5. Giả lập Lỗi Dữ Liệu và Phân tích Tác động (Data Corruption & Comparison) (20 điểm + Bonus)

Để chứng minh **"Chất lượng dữ liệu quyết định chất lượng AI"**, một kịch bản Chaos Engineering đã được thiết lập.

### 5.1. Kịch bản lỗi (Corruption Scenario)
*   **Noise & Blank Summary:** Xóa hoàn toàn đoạn tóm tắt hoặc chèn ký tự ngẫu nhiên vào 30% dữ liệu.
*   **Stale Data:** Đổi ngày xuất bản của các bài báo về 5 năm trước.
*   **Duplicate Records:** Gấp đôi một số lượng bài viết nhất định.

### 5.2. So sánh Hiệu suất (Metrics Comparison)

| Trạng thái Dữ liệu | Retrieval Hit Rate | Mean Token F1 | Judge Accuracy | Nhận xét |
| :--- | :---: | :---: | :---: | :--- |
| **1. Baseline (Sạch)** | ~95% | Cao | ~90% | Agent tìm đúng context, trả lời chính xác, độ tin cậy cao. |
| **2. Corrupted (Lỗi)** | ~40% | Thấp | < 45% | Agent bị "ảo giác" (hallucination) do đọc phải text nhiễu, hoặc trả lời sai vì không tìm thấy summary. Data Quality báo đỏ. |
| **3. Repaired (Phục hồi)**| ~95% | Cao | ~90% | Hệ thống tự động truy xuất lại từ file raw, làm sạch lại, chất lượng Agent được khôi phục 100% như Baseline. |

### 5.3. Kết luận
Kịch bản thử nghiệm đã chứng minh rõ ràng: Một hệ thống RAG dù dùng mô hình LLM xịn đến đâu (như GPT-4 hay Gemini 1.5 Pro) nhưng nếu đường ống dữ liệu không có lớp khiên bảo vệ (Data Observability), thì việc dữ liệu bị rác sẽ lập tức làm suy sụp niềm tin của người dùng vào câu trả lời. 

Hệ thống pipeline này giải quyết triệt để vấn đề đó bằng khả năng phát hiện dữ liệu thiu/lỗi và tự động khôi phục (repair) kịp thời.
