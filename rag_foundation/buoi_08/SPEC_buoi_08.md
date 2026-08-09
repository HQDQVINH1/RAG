# AGENT SPECIFICATION — BUỔI 08: ADVANCED RAG & HYBRID RETRIEVAL

Tài liệu này quy định đầy đủ 12 tiêu chuẩn thiết kế (Contracts) và ràng buộc dành cho AI Agent khi phát triển dự án Advanced RAG tại `rag_foundation/buoi_08/`.

---

## 1. Workspace và Security Contract
- **Workspace Scope**: Tất cả file mã nguồn mới chỉ được phép ghi vào `rag_foundation/buoi_08/`.
- **Bảo mật tuyệt đối**: Không lưu, log, hay hardcode `GEMINI_API_KEY`, mật khẩu hoặc các thông tin nhạy cảm. Nạp bí mật thông qua `python-dotenv` từ `.env`.
- **Bảo vệ môi trường**: Không tạo `.venv` mới, chỉ sử dụng interpreter từ `rag_foundation/buoi_05/.venv/`.
- **Bảo vệ dữ liệu gốc**: Tuyệt đối không chỉnh sửa bất kỳ file nào thuộc Buổi 05, Buổi 06 và Buổi 07.

## 2. Quan Hệ Với Buổi 05 và Buổi 07
- **Đầu vào Data (Buổi 05)**: Đọc dữ liệu JSON chunks đã được cắt sẵn từ `rag_foundation/buoi_05/output/chunks/`. Không chạy lại OCR hay parse PDF.
- **Baseline Semantic RAG (Buổi 07)**: Sao chép file `rag_foundation/buoi_07/rag.py` vào `buoi_08/rag.py` để làm mốc đối chiếu (Baseline).
- **Tự quản lý storage**: Buổi 08 tự quản lý database ChromaDB tại `buoi_08/storage/chroma/`, không dùng chung storage của Buổi 07.

## 3. Data Contract
Mỗi chunk khi nạp vào hệ thống phải thỏa mãn 6 thuộc tính bắt buộc:
- `chunk_id` (str): Mã định danh duy nhất của đoạn văn bản.
- `strategy` (str): Chiến lược cắt nhỏ (`fixed-size`, `semantic`, hoặc `hierarchical`).
- `source` (str): Tên file tài liệu gốc.
- `page_start` (int): Số trang bắt đầu (>= 1).
- `page_end` (int): Số trang kết thúc (>= page_start).
- `text` (str): Nội dung văn bản thuần (chuỗi không rỗng).

## 4. BM25 Tokenizer & Retrieval Contract
- **Tokenizer**: Sử dụng hàm tách từ tiếng Việt chuẩn hóa (lower-case, loại bỏ ký tự đặc biệt, chuẩn hóa khoảng trắng).
- **BM25 Engine**: Sử dụng thuật toán BM25Okapi (`rank-bm25`) xây dựng chỉ mục trên tập dữ liệu chunks hợp lệ.
- **Lexical Candidates**: Trả về danh sách $N$ kết quả có điểm số BM25 lớn nhất kèm theo điểm số gốc (raw score) và xếp hạng (rank).

## 5. Semantic Candidate Contract
- **Vector Search Engine**: Sử dụng ChromaDB `PersistentClient` tại `buoi_08/storage/chroma/` với Cosine distance metric.
- **Model Embedding**: Tạo vector biểu diễn 768 chiều thông qua Google Gemini Embedding API (`gemini-embedding-2`).
- **Semantic Candidates**: Trả về danh sách $N$ ứng viên có Cosine distance nhỏ nhất kèm khoảng cách (distance) và xếp hạng.

## 6. RRF (Reciprocal Rank Fusion) Contract
- **Thuật toán Dung hợp**: Kết hợp danh sách ứng viên từ BM25 và Semantic search bằng công thức:
  $$RRF\_Score(d) = \sum_{m \in \{BM25, Semantic\}} \frac{1}{k + rank_m(d)}$$
  Trong đó hằng số $k = 60$.
- **Tối ưu ứng viên**: Thu thập danh sách $M$ ứng viên hàng đầu sau khi sắp xếp lại theo điểm số RRF giảm dần.

## 7. Cross-Encoder Reranker Contract
- **Xếp hạng nâng cao**: Sử dụng mô hình Cross-Encoder (như BAAI/bge-reranker-base hoặc Scoring LLM) để tính điểm số tương quan trực tiếp giữa cặp `(Query, Chunk Text)`.
- **Rerank Sorting**: Sắp xếp lại danh sách ứng viên từ RRF theo điểm số tương quan mới của Reranker.

## 8. Final Evidence và Citation Contract
- **Confidence Gate**: Loại bỏ các ứng viên có điểm số không đạt ngưỡng tương quan tối thiểu (`RAG_MAX_DISTANCE` hoặc Reranker threshold).
- **Evidence Citation**: Trích dẫn nguồn bắt buộc lấy trực tiếp từ metadata thật trong database (`source`, `page_start`, `page_end`, `chunk_id`). Không sử dụng nhãn trích dẫn tự phát sinh từ LLM.

## 9. Pipeline Trace Contract
Mọi lượt truy vấn Advanced RAG phải trả về object kết quả chứa đầy đủ vết xử lý (Execution Trace):
- `bm25_candidates`: Danh sách top candidates từ BM25 search.
- `semantic_candidates`: Danh sách top candidates từ Semantic vector search.
- `rrf_fused_candidates`: Danh sách candidates sau khi cộng điểm RRF.
- `reranked_candidates`: Danh sách candidates sau khi rerank.
- `final_evidence`: Danh sách bằng chứng đạt yêu cầu được đưa vào prompt.

## 10. Evaluation Metrics Contract
Module đánh giá (`evaluate.py`) đo lường hiệu năng RAG trên tập câu hỏi chuẩn (`eval/questions.json`) theo các chỉ số:
- **Hit Rate @ K**: Tỷ lệ tìm thấy ít nhất 1 chunk đúng trong Top-K.
- **MRR @ K (Mean Reciprocal Rank)**: Điểm xếp hạng nghịch đảo trung bình của chunk đúng đầu tiên.
- **Precision @ K & Recall @ K**: Độ chính xác và độ phủ của danh sách trích xuất.
- **NDCG @ K (Normalized Discounted Cumulative Gain)**: Đánh giá chất lượng thứ tự xếp hạng của danh sách trích xuất.

## 11. Offline Testing Contract
- **Mocking**: Tất cả unit test trong `tests/` phải hỗ trợ chạy hoàn toàn offline không phụ thuộc vào kết nối mạng hay API key thật.
- **In-Memory Testing**: Dùng Mock API và bộ dữ liệu mẫu trong `tests/fixtures/chunks_advanced_sample.json` để kiểm thử logic thuật toán BM25, RRF, Reranker và Citation mapping.

## 12. UI Comparison Contract
- **Giao diện so sánh Streamlit (`app.py`)**:
  - Hỗ trợ chế độ xem song song (Side-by-Side): **Baseline Semantic RAG (Buổi 07)** vs **Advanced Hybrid RAG (Buổi 08)**.
  - Hiển thị bảng so sánh chi tiết về thời gian xử lý, danh sách candidates thu được ở từng bước (BM25, Semantic, RRF, Reranker) và chất lượng câu trả lời cuối cùng.
