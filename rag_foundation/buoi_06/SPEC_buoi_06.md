# SPECIFICATION - BUỔI 06

Tài liệu này định hướng và quy định các ràng buộc dành cho AI Agent khi triển khai project demo tại `RAG/rag_foundation/buoi_06/`.

## 1. Quyền Truy Cập Workspace (Workspace Restrictions)
**Chỉ được phép đọc:**
- `RAG/rag_foundation/buoi_05/output/chunks/`
- `RAG/rag_foundation/buoi_05/.venv/`
- `RAG/rag_foundation/buoi_06/`

**Không được phép đọc:**
- Source code của Buổi 5
- README các buổi trước
- Notebook
- Git history
- Các thư mục khác

> **Lưu ý:** Buổi 5 được xem là *black box*. Không thực hiện reverse engineering và không phân tích cách Buổi 5 hoạt động.

## 2. Môi trường Python (Python Environment)
- Sử dụng đúng interpreter trong: `RAG/rag_foundation/buoi_05/.venv/`
- **Không** tạo virtual environment mới.

## 3. Package & Thư viện (Dependencies)
Chỉ cài đặt và sử dụng các thư viện sau:
- `streamlit`
- `google-genai`
- `chromadb`
- `psycopg`
- `python-dotenv`

**Không** cài thêm bất kỳ framework nào khác.

## 4. Phong cách lập trình (Coding Style)
- Ưu tiên: ít file, ít class, ít function, code dễ đọc.
- **Không tạo:** Repository pattern, service layer, dependency injection, factory, plugin.

## 5. Phạm vi dự án (Scope)
Chỉ tập trung vào 4 phần chính:
- **Index**: Đưa dữ liệu vào vector store / database.
- **Retrieval**: Tìm kiếm / truy vấn đoạn thông tin phù hợp.
- **Answer**: Sinh câu trả lời dựa trên thông tin tìm kiếm được.
- **Streamlit**: Giao diện người dùng đơn giản.

**Không** phát triển các tính năng ngoài các yêu cầu trên.

## 6. Xử lý lỗi (Error Handling)
- Chỉ áp dụng `try/except` ở mức tối thiểu.
- **Không cần:** Retry, logging, monitoring.

## 7. Bảo mật (Security)
- Tuyệt đối **không** in ra API Key, password, secret hay bất kỳ thông tin nhạy cảm nào.

## 8. Giới hạn quy mô code (Code Size)
- Mục tiêu tổng dung lượng code Python khoảng **300–500 dòng**.
- Nếu vượt quá khoảng **700 dòng**, cần tiến hành đơn giản hóa thiết kế.
