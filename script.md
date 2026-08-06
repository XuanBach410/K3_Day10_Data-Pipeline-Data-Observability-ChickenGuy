# 🎤 Kịch Bản Thuyết Trình Project Day 10: Data Pipeline & Data Observability
**Nhóm:** ChickenGuy — VinUni K3  
**Báo cáo viên cá nhân:** Đinh Hoài Nam (MSSV: 2A202601889) — **Vai trò 2: Data Ingestion & Recovery**  
**Ứng dụng Demo:** Web Dashboard (`http://localhost:5050`) & Slide Presentation (`slide.html`)

---

## ⏱️ Tổng Quan Kế Hoạch Thuyết Trình (Thời lượng: ~7 phút)

| Phần | Thời lượng | Người trình bày | Nội dung chính |
| :--- | :--- | :--- | :--- |
| **Phần 1: Giới thiệu & Tổng quan Hệ thống** | 1 phút | Đại diện Nhóm / Hoài Nam | Đặt vấn đề RAG failure do rác dữ liệu & Kiến trúc 4 Roles |
| **Phần 2: Chi tiết Vai trò 2 (Hoài Nam)** | 2.5 phút | **Đinh Hoài Nam** | Crossref API, Data Cleaning, 6 Corruption Scenarios & Data Repair |
| **Phần 3: Demo Live Dashboard (`app.py`)** | 2 phút | **Đinh Hoài Nam** | Thao tác chạy Live Phase 1, Gây lỗi Phase 2, Quan sát Observability & Sửa lỗi |
| **Phần 4: Kết luận & Bài học kinh nghiệm** | 1 phút | Đại diện Nhóm / Hoài Nam | Tầm quan trọng của Data Observability trong RAG Production |
| **Phần 5: Q&A** | 0.5 phút | Cả nhóm | Trả lời câu hỏi phản biện của Giám khảo / TAs |

---

## 📜 Kịch Bản Chi Tiết (Spoken Script — Lời Nói Trực Tiếp)

### 🎬 PHẦN 1: MỞ ĐẦU & ĐẶT VẤN ĐỀ (1 PHÚT)

> **Lời thoại (Hoài Nam):**
> *"Kính chào Thầy/Cô và các bạn! Em là **Đinh Hoài Nam**, đại diện cho nhóm **ChickenGuy** trình bày bài lab Day 10 với đề tài: **Data Pipeline & Data Observability cho Hệ thống Retrieval-Augmented Generation (RAG)**.*
>
> *Trong thực tế triển khai RAG, đa số các đội ngũ AI chỉ tập trung vào mô hình LLM hoặc thuật toán Embedding. Tuy nhiên, rủi ro lớn nhất khiến RAG thất bại trong Production lại nằm ở **Chất lượng dữ liệu đầu vào (Data Quality)**. Khi dữ liệu thô bị hỏng, rác, hoặc lạc hậu (stale), Retrieval sẽ lấy sai ngữ cảnh, kéo theo LLM đưa ra câu trả lời sai lệch hoàn toàn.*
>
> *Để giải quyết triệt để vấn đề này, nhóm ChickenGuy đã xây dựng một **End-to-End Pipeline hoàn chỉnh** phân chia theo 4 vai trò chuyên môn hóa:*
> 1. **Role 1 (Phạm Thị Thúy Linh):** Quản lý Cấu hình (Core Config) & Điều phối Pipeline.
> 2. **Role 2 (Đinh Hoài Nam - Em phụ trách):** Thu thập dữ liệu Crossref API, Data Cleaning, Mô phỏng Lỗi dữ liệu & Tự động Sửa lỗi (Recovery).
> 3. **Role 3 (Trịnh Quốc Trọng):** Vector Embedding, Lưu trữ ChromaDB & RAG Agent.
> 4. **Role 4 (Trần Xuân Bách):** Data Observability Quality Checks, Đánh giá RAG Metrics & Báo cáo.*"

---

### ⚙️ PHẦN 2: BÁO CÁO KỸ THUẬT VAI TRÒ 2 — ĐINH HOÀI NAM (2.5 PHÚT)

> **Lời thoại (Hoài Nam):**
> *"Bây giờ em xin đi sâu vào nhiệm vụ chuyên môn của **Vai trò 2: Data Ingestion, Corruption & Recovery Engine** mà em trực tiếp thiết kế.*
>
> #### 1️⃣ Ingestion từ Crossref REST API (`src/ingestion/crossref.py`)
> *Dữ liệu của hệ thống được thu thập trực tiếp từ **Crossref REST API** - nguồn metadata bài báo khoa học chuẩn quốc tế.*
> - *Em xây dựng hàm `fetch_source_records()` tích hợp cơ chế **Exponential Backoff Retry** (tối đa 3 lần) xử lý các trường hợp server bị Rate Limit (HTTP 429) hoặc tạm thời quá tải (HTTP 503).*
> - *Nếu mạng ngắt kết nối hoàn toàn, hệ thống chuyển sang **Fallback Mechanism** dùng JSON Snapshot hoặc Mock Dataset để đảm bảo pipeline không bao giờ bị sập.*
> - *Hàm `parse_crossref_payload()` thực hiện lọc bỏ hoàn toàn các thẻ HTML/JATS XML rác trong abstract, chuẩn hóa định dạng ngày `YYYY-MM-DD` và trích xuất danh sách tác giả, DOI.*
>
> #### 2️⃣ Data Cleaning & Normalization (`src/ingestion/cleaning.py`)
> *Sau khi lấy dữ liệu thô, hàm `build_clean_dataframe()` tiến hành:*
> - *Chuẩn hóa khoảng trắng dư thừa (`normalize_whitespace`).*
> - *Gán giá trị mặc định uy tín nếu thiếu thông tin (vd: author = 'Unknown Author', category = 'General').*
> - *Tính toán chỉ số **Freshness (`age_days`)** dựa trên khoảng cách giữa ngày đăng bài và ngày chạy pipeline.*
> - *Tạo trường tổng hợp `text_for_embedding` phục vụ tối ưu hóa cho bước Vectorize của Role 3.*
> - *Loại bỏ các bản ghi trùng lặp theo `paper_id` và `title`.*
>
> #### 3️⃣ Engine Mô Phỏng Lỗi Dữ Liệu — Data Corruption (`src/ingestion/corruption.py`)
> *Để kiểm thử năng lực của hệ thống Observability (Role 4), em đã xây dựng **6 kịch bản gây lỗi chủ động (Controlled Corruption Scenarios)**:*
> 1. **`drop_latest_records`**: Xóa 2 bài báo mới nhất → Kiểm thử lỗi mất mát dữ liệu nguồn (Missing Data).
> 2. **`blank_summary`**: Xóa trắng tóm tắt của 2 bài báo → Kiểm thử lỗi rỗng dữ liệu (Empty Abstract).
> 3. **`inject_noise`**: Chèn chuỗi ký tự rác `[NOISE_CORRUPTED_GARBAGE]` → Mô phỏng nhiễu từ vựng.
> 4. **`truncate_title`**: Cắt tiêu đề còn 10 ký tự → Mô phỏng lỗi xén dữ liệu.
> 5. **`make_stale_date`**: Đưa ngày xuất bản về năm 2015 (`age_days = 3650`) → Kích hoạt cảnh báo Dữ liệu Lạc hậu (Stale Data).
> 6. **`add_duplicate_rows`**: Nhân bản bản ghi → Kích hoạt cảnh báo Trùng lặp Khóa chính (Duplicate Paper ID).*
>
> #### 4️⃣ Luồng Tự Động Khôi Phục — Data Repair (`src/pipelines/corruption_flow.py`)
> *Khi Observability phát hiện chỉ số Quality bị FAILED, luồng Recovery của em sẽ tự động kích hoạt: **Re-ingest lại từ snapshot nguồn uy tín**, tái cấu trúc DataFrame sạch và Rebuild lại ChromaDB Index. Nhờ đó khôi phục lại 100% hiệu năng tìm kiếm RAG.*"

---

### 🖥️ PHẦN 3: DEMO TRỰC TIẾP TRÊN WEB DASHBOARD (`http://localhost:5050`) (2 PHÚT)

*(Mở trình duyệt sang `http://localhost:5050`)*

> **Lời thoại (Hoài Nam):**
> *"Sau đây em xin thao tác trực tiếp trên **Live Web Dashboard** của nhóm tại cổng `localhost:5050`.*
>
> *(Thao tác 1: Nhấn nút **▶ Run Phase 1 Baseline**)*
> - *"Em nhấn **Run Phase 1 Baseline**. Các bạn có thể thấy ở ô Terminal bên phải, log thực thi được stream realtime từ Python subprocess qua cơ chế **Server-Sent Events (SSE)**.*
> - *Ở góc trái, sơ đồ **Complete Flow Architecture** gồm 7 bước của Phase 1 đang lần lượt sáng đèn xanh khi từng bước hoàn thành.*
> - *Kết quả Phase 1: **24 bản ghi sạch**, Retrieval Hit Rate đạt **1.0000 (100%)**, Token F1 đạt **1.0000**, và Data Quality Status đạt **PASSED** (6/6 checks).*
>
> *(Thao tác 2: Nhấn nút **⚡ Run Phase 2 Corruption & Repair**)*
> - *Tiếp theo, em nhấn **Run Phase 2 Corruption & Repair**. Pipeline Phase 2 gồm 10 bước khép kín sẽ được chạy.*
> - *Tại Bước 2 & 5: Engine Corruption của em bơm 6 loại lỗi vào. Ngay lập tức, hệ thống Observability phát hiện bất thường và chuyển trạng thái Quality sang **FAILED** (thất bại ở 3 checks: Duplicate IDs, Short Summaries, Stale Rows).*
> - *Mức độ ảnh hưởng đến RAG: **Retrieval Hit Rate lập tức sụt giảm từ 100% xuống 80%**, Token F1 giảm từ **1.0000 xuống 0.7784**, và Judge Accuracy giảm xuống **76.67%**.*
> - *Tại Bước 6-9: Luồng Data Repair của em tự động khôi phục dữ liệu từ nguồn thô. Kết quả: Quality Status trở lại **PASSED**, Freshness trở lại **FRESH**, và Hit Rate khôi phục hoàn toàn về **100%**.*
>
> *(Chuyển sang Tab **📊 Metrics & Evaluation** và **💥 Corruption Scenarios**)*
> - *Trong tab Metrics, bảng so sánh ma trận 3 giai đoạn hiển thị rất rõ tác động âm của Corruption và hiệu quả phục hồi tuyệt đối sau Repair.*"

---

### 🎯 PHẦN 4: KẾT LUẬN & BÀI HỌC KINH NGHIỆM (1 PHÚT)

> **Lời thoại (Hoài Nam):**
> *"Qua bài lab Day 10, nhóm ChickenGuy rút ra 3 kết luận cốt lõi:*
> 1. **Data Observability là bắt buộc:** Không thể xây dựng RAG tin cậy nếu không có cơ chế giám sát dữ liệu tự động 24/7 (Quality Checks + Freshness Monitoring).
> 2. **Kiến trúc Pipeline Tự khôi phục (Self-healing Pipeline):** Khi phát hiện dữ liệu lỗi, cơ chế Re-ingestion từ nguồn uy tín giúp hệ thống tự phục hồi mà không cần can thiệp thủ công bằng tay.
> 3. **Hiệu quả của việc phối hợp 4 Roles:** Việc tách biệt Data Ingestion, Vector Indexing và Observability giúp codebase vô cùng modular, dễ mở rộng và dễ bảo trì.*
>
> *Em xin chân thành cảm ơn Thầy/Cô và các bạn đã lắng nghe. Nhóm sẵn sàng nhận câu hỏi phản biện ạ!"*

---

## ❓ PHẦN 5: CÁC CÂU HỎI PHẢN BIỆN THƯỜNG GẶP DÀNH CHO NHÓM (Q&A)

### ❓ Câu 1: *"Tại sao trong `crossref.py` bạn lại cần cả Fallback Snapshot và Mock Data?"*
> **Trả lời (Hoài Nam):**  
> *"Dạ, Crossref REST API là dịch vụ công cộng trực tuyến, đôi khi bị quá tải dẫn đến phản hồi HTTP 429 hoặc 503. Em thiết kế 3 tầng bảo vệ (3-tier resilience):*
> 1. *Tầng 1: Retry 3 lần với Exponential Backoff (1s -> 2s -> 4s).*
> 2. *Tầng 2: Nếu API quá tải sau 3 lần, đọc từ file local JSON snapshot đã cache trước đó (`data/raw/raw_records.json`).*
> 3. *Tầng 3: Nếu chạy lần đầu ở môi trường không có mạng và chưa có cache, trả về Mock Data chuẩn định dạng để pipeline không bị cản trở. Nhờ vậy hệ thống luôn chạy thông suốt 100%."*

---

### ❓ Câu 2: *"Cơ chế phát hiện và sửa lỗi (Data Repair) của bạn hoạt động như thế nào?"*
> **Trả lời (Hoài Nam):**  
> *"Dạ, khi module Observability của bạn Xuân Bách (Role 4) báo về `quality.success == False` hoặc `freshness.is_fresh == False`, luồng Repair sẽ:*
> 1. *Bỏ qua hoàn toàn dữ liệu bị hỏng trong bộ nhớ RAM/CSV tạm.*
> 2. *Truy xuất lại bản ghi thô nguyên bản từ `raw_records.json` (tệp authoritative source).*
> 3. *Chạy lại hàm `build_clean_dataframe()` để loại bỏ rác, tính lại `age_days` chuẩn, và gán lại schema đúng.*
> 4. *Rebuild lại ChromaDB Index để phục hồi lại hiệu năng RAG ban đầu."*

---

### ❓ Câu 3: *"Tại sao chỉ cần xóa 2 bài báo mới nhất mà Hit Rate của RAG lại giảm từ 100% xuống 80%?"*
> **Trả lời (Hoài Nam):**  
> *"Dạ, trong bộ câu hỏi testset (60 samples), có các câu hỏi truy vấn trực tiếp thông tin từ 2 bài báo mới nhất đó. Khi 2 bài báo này bị `drop_latest_records`, ChromaDB Vector Index không còn chứa văn bản ngữ cảnh tương ứng. Do đó khi RAG thực hiện Top-K Retrieval, nó trả về các bài báo không liên quan, làm các truy vấn đó bị Miss -> kéo Hit Rate tổng giảm 20%."*

---

## 🎯 PHẦN 6: BỘ CÂU HỎI "XOÁY ĐÁP XOAY" DÀNH CHO BẠN ĐI ĐẶT CHO CÁC NHÓM KHÁC

Các câu hỏi được thiết kế theo chuẩn chuyên gia Data Engineering & Observability, dùng để hỏi phản biện nhóm khác:

### 🥊 Nhóm 1: Về Ingestion & API Resilience (Hỏi người làm Role 2 / Ingestion)
1. ❓ *"Khi API nguồn bị quá tải trả về HTTP 429 hoặc timeout, pipeline của nhóm bạn xử lý như thế nào? Có cơ chế Exponential Backoff hay Fallback Dataset không, hay sẽ crash ngay lập tức?"*
2. ❓ *"Dữ liệu thô từ API thường chứa rất nhiều thẻ rác XML/HTML như `<jats:p>` hay `<i>`. Nhóm bạn dùng Regex hay thư viện gì để clean rác này, và làm thế nào để đảm bảo sau khi clean không làm mất nội dung chính của tóm tắt?"*

### 🥊 Nhóm 2: Về Data Observability & Quality Checks (Hỏi người làm Role 4 / Observability)
3. ❓ *"Trong hệ thống Observability của nhóm bạn, làm thế nào để bạn phát hiện ra một bản ghi bị **Duplicated Key (Paper ID)** hay **Title bị cắt ngắn (Truncated)**? Bộ chỉ số Check của nhóm bạn có tự động trả về `success = False` hay phải nhìn bằng mắt thường?"*
4. ❓ *"Tiêu chí xác định một bài báo bị **Stale (Lạc hậu)** trong hệ thống của bạn là gì? Chỉ số `freshness_threshold_days` được cấu hình bao nhiêu ngày, và nếu dữ liệu bị stale thì hệ thống của bạn đưa ra cảnh báo hay chặn luồng pipeline?"*

### 🥊 Nhóm 3: Về Vector Index & Embedding Corruption (Hỏi người làm Role 3 / Retrieval)
5. ❓ *"Khi dữ liệu bị chèn chuỗi ký tự rác (Noise Corruption), tại sao Vector Index của bạn vẫn cho phép lưu dữ liệu đó vào ChromaDB? Và việc rác nằm trong Vector Index ảnh hưởng như thế nào đến điểm Cosine Similarity / Distance khi query?"*
6. ❓ *"Nhóm bạn sử dụng Embedding Model nào (`all-MiniLM-L6-v2` hay OpenAI)? Nếu dữ liệu đầu vào bị rỗng summary (`summary = ""`), Embedding Model của bạn xử lý ra sao hay tạo ra Vector 0?"*

### 🥊 Nhóm 4: Về Self-Healing & Data Recovery (Hỏi người làm Role 2 & Role 1 / Recovery)
7. ❓ *"Khi Observability phát hiện dữ liệu bị hỏng (Corrupted), luồng Repair của nhóm bạn sẽ khôi phục dữ liệu từ đâu? Bạn xóa các bản ghi lỗi hay Re-ingest lại từ nguồn authoritative gốc?"*
8. ❓ *"Sau khi Repair dữ liệu xong, nhóm bạn có đánh giá lại chỉ số RAG (Hit Rate, Token F1) không? Kết quả Hit Rate sau khi Repair có khôi phục lại được 100% như ban đầu không và tại sao?"*

---

*Tài liệu này được soạn thảo đầy đủ cho buổi thuyết trình Day 10 Codelab của nhóm ChickenGuy tại VinUni.*
