# AGENT SPECIFICATION — BUỔI 07

## 1. Workspace
- **Vùng được đọc**:
  - `rag_foundation/buoi_05/output/chunks/`
  - `rag_foundation/buoi_05/.venv/`
  - `rag_foundation/buoi_06/`
  - `rag_foundation/buoi_07/`
- **Vùng được ghi**:
  - `rag_foundation/buoi_07/`
- **Quy tắc tuyệt đối**: Không chỉnh sửa hoặc thao tác làm biến đổi code, dữ liệu, hoặc output của Buổi 05 và Buổi 06. Mọi đường dẫn trong code phải dùng `Path(__file__).resolve()`.

## 2. Python Environment
- Sử dụng trực tiếp môi trường ảo tại `rag_foundation/buoi_05/.venv/`.
- **Tuyệt đối không tạo virtual environment mới**.

## 3. Input
- Dữ liệu đầu vào là các file JSON đã được chia chunk hoàn chỉnh nằm trong `rag_foundation/buoi_05/output/chunks/`.
- Buổi 05 đã hoàn thành phần chuẩn hóa dữ liệu. Buổi 07 **không chạy lại OCR, không parse PDF, không chia chunk lại**.

## 4. Packages
- Chỉ sử dụng các thư viện trực tiếp được quy định:
  - `streamlit` (>=1.61, <2)
  - `google-genai` (>=2.16, <3)
  - `chromadb` (>=1.5, <2)
  - `python-dotenv` (>=1.2, <2)
- Dùng thư viện chuẩn của Python (`json`, `pathlib`, `hashlib`, `unittest`, `unittest.mock`, `re`, `argparse`, `math`, `os`, `tempfile`).
- Không dùng LangChain, LlamaIndex hoặc các RAG framework nâng cao khác.

## 5. Pipeline Architecture
Quy trình xử lý RAG bao gồm 9 bước tuyến tính:
1. **Validate**: Kiểm tra cấu trúc và tính hợp lệ của JSON input.
2. **Embedding**: Tạo vector biểu diễn bằng Google Gemini Embedding API.
3. **Chroma Persistent**: Lưu trữ vector và metadata vào ChromaDB theo cơ chế persistent.
4. **Retrieval**: Truy vấn semantic top-k theo cosine distance.
5. **Confidence Gate**: Lọc evidence dựa trên ngưỡng `RAG_MAX_DISTANCE`.
6. **Generation**: Gọi Gemini LLM để tổng hợp câu trả lời dựa trên context đạt yêu cầu.
7. **Citation**: Gắn nhãn và trích dẫn thông tin nguồn (Source, Page, Chunk ID) từ metadata gốc.
8. **Streamlit UI**: Hiển thị câu trả lời, nguồn trích dẫn và các cảnh báo (nếu có).
9. **Unittest Offline**: Kiểm thử tự động với Mock API.

## 6. Data Contract
Mỗi chunk JSON khi nạp vào hệ thống bắt buộc phải chứa đầy đủ 6 trường dữ liệu sau:
- `chunk_id` (str): Mã định danh duy nhất của chunk.
- `strategy` (str): Chiến lược chunking (`fixed-size`, `semantic`, hoặc `hierarchical`).
- `source` (str): Tên file tài liệu gốc.
- `page_start` (int): Trang bắt đầu.
- `page_end` (int): Trang kết thúc.
- `text` (str): Nội dung văn bản của chunk.

## 7. Index Contract
- **Collection Isolation**: Mỗi `strategy` lưu trữ trong 1 Chroma collection riêng biệt.
- **Model & Dimension Consistency**: Model embedding và số chiều (dimension, mặc định 768) của Index và Query phải hoàn toàn trùng khớp.
- **Embedding Thật**: Phải gọi Gemini API thật khi tạo index sản phẩm; không tạo hoặc chèn vector giả (random/zeros) khi API lỗi.
- **Validation**: Chặn triệt để các vector chứa giá trị NaN, Infinity, Boolean hoặc Vector toàn số 0 (zero vector).
- **Chroma Setup**: Dùng Chroma cosine distance metric với `embedding_function=None` (tự quản lý embedding vectors).
- **Idempotent**: Việc index lại cùng tập dữ liệu không làm nhân bản dữ liệu (hỗ trợ upsert / reset kiểm soát).
- **Status Read-only**: Cung cấp hàm đọc thống kê index mà không làm biến đổi dữ liệu.
- **Validation First**: Kiểm tra toàn bộ vector embedding thành công trước khi thực hiện reset hoặc upsert vào database.

## 8. Retrieval Contract
- Trả về danh sách evidence thật kèm thông số khoảng cách (`distance`).
- Lọc evidence nghiêm ngặt: Chỉ những evidence có `distance <= RAG_MAX_DISTANCE` mới được đưa vào ngữ cảnh Generation.
- Nếu không có evidence nào đạt ngưỡng (evidence yếu), chặn không gọi Generation và thông báo không đủ thông tin.

## 9. Citation Contract
- Trích dẫn nguồn bắt buộc lấy từ metadata thật của chunk trong database.
- Không tin tưởng hoặc sử dụng thông tin `source`, `page`, `chunk_id` do LLM tự sinh trong văn bản phản hồi.
- Kết quả trả về phải chứa cặp `citations` và `warnings`; hệ thống code tự động thay thế các label trích dẫn bằng citation chuẩn.

## 10. Security
- Không lưu hoặc in API key ra log/screen.
- Nạp secret qua biến môi trường (dùng `python-dotenv`).
- File `.env` chứa thông tin thực tế được gitignore.

## 11. Testing & Mocking
- Tất cả unit test trong `tests/` chạy hoàn toàn offline không cần Internet hay API key thật.
- Sử dụng `unittest.mock` để giả lập Google GenAI API response và ChromaDB in-memory client.
- Dùng `tempfile` để lưu database tạm trong khi chạy test.

## 12. Coding Style
- Mã nguồn tối giản, ưu tiên ít file, ít class và hàm ngắn gọn, rõ ràng.
- Tránh tạo các tầng kiến trúc trừu tượng phức tạp không cần thiết.
