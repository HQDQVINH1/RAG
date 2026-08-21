# Dependency Report — Buổi 17

## 1. Dữ liệu nguồn (Source Data Inspection)

### 1.1. Tệp `chunks_secure.csv` vs `chunks_normalized.csv`
- **Tệp dữ liệu chính (`chunks_secure.csv`)**:
  - Số dòng: **792 dòng**
  - Số cột: **14 cột**
  - Danh sách cột: `['chunk_id', 'document_id', 'text', 'source_file', 'title', 'so_ky_hieu', 'document_type', 'chapter', 'section', 'article', 'clause', 'effective_date', 'status', 'allowed_roles']`
- **Tệp dữ liệu đối chiếu (`chunks_normalized.csv`)**:
  - Số dòng: **792 dòng**
  - Số cột: **13 cột**
  - Danh sách cột: `['chunk_id', 'document_id', 'text', 'source_file', 'title', 'so_ky_hieu', 'document_type', 'chapter', 'section', 'article', 'clause', 'effective_date', 'status']`

### 1.2. Ánh xạ và kiểm tra các trường dữ liệu
- `chunk_id`: Có mặt trong cả 2 tệp CSV (Khớp 100%).
- `document_id`: Có mặt trong cả 2 tệp CSV (Khớp 100%).
- `citation`: Được sinh động trong retriever từ các trường (`so_ky_hieu`, `title`, `article`, `clause`, `chunk_id`).
- `title`: Có mặt trong cả 2 tệp CSV (`title`).
- `loai_van_ban`: Được lưu dưới dạng `document_type` trong cả 2 tệp CSV.
- `co_quan_ban_hanh`: Không có cột riêng biệt trong CSV (thông tin cơ quan phát hành nằm trong tiêu đề/nội dung hoặc metadata văn bản).
- `ngay_ban_hanh`: Được lưu dưới dạng `effective_date` trong cả 2 tệp CSV.
- `allowed_roles`: Có mặt duy nhất trong `chunks_secure.csv` dưới dạng chuỗi JSON danh sách vai trò (ví dụ: `["ROLE_ALL"]`, `["ROLE_COMPLIANCE"]`, `["ROLE_RISK"]`, `["ROLE_TELLER"]`).

### 1.3. Kết quả so sánh 2 tệp CSV
- 13 cột chung của `chunks_secure.csv` và `chunks_normalized.csv` hoàn toàn giống nhau 100% trên toàn bộ 792 dòng.
- **Xác nhận**: `chunks_secure.csv` = `chunks_normalized.csv` + `allowed_roles`. Không có sự sai lệch dữ liệu nào khác.

---

## 2. Phân tích SecureRetriever từ Buổi 16

- **Tệp / Module**: `src/secure_retriever.py`
- **Class / Hàm chính**: Class `SecureRetriever`, phương thức điều phối `retrieve(query, user_roles, method=..., top_k=..., candidate_k=...)`.
- **Input Role**: `user_roles: List[str]` (ví dụ: `["ROLE_ALL"]`, `["ROLE_COMPLIANCE"]`, `["ROLE_TELLER"]`).
- **Output**: `List[Dict[str, Any]]` với từng item chứa:
  - `chunk_id` (được bảo toàn)
  - `document_id` (được bảo toàn)
  - `text` (nội dung chunk)
  - `allowed_roles` (danh sách vai trò được phép truy cập)
  - `score` / `retrieval_score`
  - `retrieval_method`
  - `rank` / `final_rank`
  - `citation` (chuỗi trích dẫn được bảo toàn & tạo sẵn)
- **Cơ chế lọc phân quyền (RBAC Filter)**:
  - **Lọc TRƯỚC khi Retrieval / Context Generation (Pre-filtering)**:
    - Trong BM25 & Dense Search: Lọc trực tiếp từng candidate theo `allowed_roles_set` kết hợp với `user_roles` (`_is_accessible`) trước khi lấy top-k.
    - Trong Hybrid & Hybrid Rerank: Thực hiện RRF và Cross-Encoder Reranking trực tiếp trên các ứng viên đã vượt qua lọc quyền.
    - Trong Graph Search (Neo4j): Áp dụng điều kiện Cypher `WHERE any(role IN d.allowed_roles WHERE role IN $user_roles)` trước khi trả về node kết quả.
- **Bảo toàn thông tin**: `document_id`, `chunk_id` và `citation` đều được bảo toàn 100% trong kết quả truy xuất.

---

## 3. Kế hoạch tái sử dụng (Reuse Plan)

- Sử dụng trực tiếp `SecureRetriever` trong `src/secure_retriever.py` mà không cần sửa đổi code Buổi 16.
- Gọi `SecureRetriever.retrieve(query, user_roles, method="hybrid_rerank")` làm bộ lọc an toàn đầu vào cho tất cả các use case của Buổi 17 (Tra cứu quy định nội bộ RBAC & AI Compliance Gap Analysis).
- Đảm bảo rằng tài liệu không có quyền sẽ bị loại bỏ hoàn toàn trước khi xây dựng Context cho LLM.

---

SOURCE DATA: PASS
RBAC DATA AVAILABLE: YES
SECURE RETRIEVER REUSABLE: YES
REUSE PLAN: Tái sử dụng trực tiếp class SecureRetriever từ `src/secure_retriever.py`, gọi phương thức `retrieve(query, user_roles)` để lọc bảo toàn quyền truy cập trước khi đưa ngữ cảnh vào LLM và Audit Logger.
