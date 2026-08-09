# YÊU CẦU KỸ THUẬT (SPEC) — RAG FOUNDATION BUỔI 05

## 1. Tổng quan & Mục tiêu

Tài liệu này quy định chi tiết yêu cầu thiết kế và triển khai cho **Buổi 05: Xử lý OCR tài liệu PDF tiếng Việt & So sánh các chiến lược Chunking**. 

Hệ thống được thiết kế dưới dạng một module độc lập, minh họa trực quan quá trình chuyển đổi từ file tài liệu PDF tiếng Việt sang văn bản chuẩn Unicode NFC và tiến hành phân đoạn (chunking) theo 3 chiến lược khác nhau.

---

## 2. Dữ liệu Đầu vào (Input)

- **Vị trí**: Tất cả các file PDF tiếng Việt công khai nằm trong thư mục `RAG/rag_foundation/buoi_05/datademo/`.
- **Đặc điểm dữ liệu**: 
  - Các văn bản quy phạm pháp luật, thông tư, quyết định tiếng Việt (ví dụ: Thông tư NHNN).
  - Có thể chứa cả trang dạng **Text Layer** (trích xuất trực tiếp) hoặc trang dạng **Scan / Ảnh / Font lỗi** (cần fallback sang OCR).
- **Ràng buộc an toàn**: Không sử dụng tài liệu nội bộ, thông tin cá nhân hay dữ liệu nhạy cảm.

---

## 3. Quy trình Xử lý & Dữ liệu Đầu ra (Output)

### 3.1. Luồng Xử lý OCR & Trích xuất Văn bản
1. **Thử nghiệm PyMuPDF (`fitz`)**: Đọc từng trang PDF để lấy Text Layer sẵn có.
2. **Kiểm tra chất lượng Text**: Khi một trang bị lỗi (lỗi font, lỗi encoding, xuất hiện ký tự lạ, hoặc rỗng), tiến hành render trang đó thành hình ảnh và kích hoạt fallback OCR toàn bộ file bằng **LlamaParse** (`llama-cloud`).
3. **Chuẩn hóa Unicode**: Tất cả văn bản trích xuất (từ PyMuPDF hoặc LlamaParse) phải được chuẩn hóa sang định dạng **Unicode NFC** (`unicodedata.normalize('NFC', text)`).
4. **Lưu trữ dữ liệu Raw**: Lưu toàn bộ văn bản sau trích xuất/OCR dưới dạng các file JSON/Markdown trung gian trong thư mục `RAG/rag_foundation/buoi_05/output/`.

### 3.2. Cấu trúc Metadata Tiêu chuẩn
Mỗi văn bản trích xuất và từng chunk tạo ra phải mang đầy đủ các trường metadata:
- `chunk_id`: Mã định danh duy nhất của chunk (dạng string/UUID).
- `source`: Tên file PDF nguồn (ví dụ: `TT_02_2023_NHNN.pdf`).
- `page_start`: Trang bắt đầu (1-indexed).
- `page_end`: Trang kết thúc (1-indexed).
- `ocr_used`: `True` nếu trang/file đã phải qua bước OCR (LlamaParse), `False` nếu dùng PyMuPDF text layer.
- `language`: Ngôn ngữ văn bản (mặc định: `vi`).
- `strategy`: Chiến lược chunking được áp dụng (`fixed-size`, `semantic`, `hierarchical`).
- `structure_metadata`: Metadata cấu trúc pháp lý (Chương, Mục, Điều, Khoản) nếu có (đặc biệt đối với `hierarchical`).

---

## 4. Ba Chiến lược Chunking cần So sánh

Hệ thống phải triển khai và cung cấp công cụ so sánh trực quan cho 3 chiến lược chunking sau:

1. **Fixed-size Chunking (Kích thước cố định)**:
   - Cắt văn bản theo số lượng ký tự hoặc token cố định (ví dụ: `chunk_size=500`, `chunk_overlap=50`).
   - Đảm bảo có vùng đè (overlap) giữa các chunk liên tiếp để không mất ngữ cảnh ranh giới.

2. **Semantic Chunking (Theo ranh giới ngữ nghĩa/đoạn văn)**:
   - Ưu tiên cắt theo các ranh giới tự nhiên của đoạn văn như ngắt đoạn (`\n\n`), ngắt dòng, hoặc hết câu (`.`, `?`, `!`).
   - Hạn chế tối đa việc cắt ngang câu hoặc cắt giữa từ.

3. **Hierarchical Chunking (Phân cấp theo cấu trúc văn bản)**:
   - Nhận diện và chia chunk dựa trên cấu trúc phân cấp pháp lý tiếng Việt: **Chương → Mục → Điều → Khoản → Điểm**.
   - Mỗi đơn vị cấu trúc chính (ví dụ: 1 Điều hoặc 1 Khoản) tạo thành mốc bắt đầu của 1 chunk.
   - *Cảnh báo an toàn*: Nếu văn bản không có cấu trúc phân cấp rõ ràng, hệ thống phải phát tín hiệu cảnh báo (`warning`) thay vì tự bịa ra tiêu đề/heading giả.

---

## 5. Quy định Bảo mật & Quản lý API Key

- **File cấu hình**: Sử dụng biến môi trường `LLAMA_CLOUD_API_KEY` lưu trong file `RAG/rag_foundation/buoi_05/src/.env`.
- **Nghiêm cấm đọc/in Secret**: Code xử lý và Giao diện UI **tuyệt đối không được in, ghi log hay hiển thị** giá trị thô của API Key ra console, file log hay màn hình ứng dụng Streamlit.

---

## 6. Phạm vi & Giới hạn của Buổi 05 (Constraints)

- ❌ **KHÔNG** tạo Vector Embedding (không dùng OpenAI Embeddings, HuggingFace, sentence-transformers, ...).
- ❌ **KHÔNG** lưu trữ dữ liệu vào Vector Database (không dùng ChromaDB, FAISS, Qdrant, Milvus, ...).
- ❌ **KHÔNG** gọi LLM để sinh câu trả lời hay tóm tắt trong phạm vi Buổi 05.
- ✅ Code phải thiết kế ở mức **demo đơn giản, dễ đọc, dễ hiểu**, tập trung vào việc giúp người mới học RAG nhìn thấy trực quan từng bước: **PDF → Text/OCR → Chunking**.

---

## 7. Cấu trúc Thư mục Bài làm

```text
RAG/rag_foundation/buoi_05/
├── SPEC_buoi_05.md            # Tài liệu yêu cầu kỹ thuật (File này)
├── app.py                     # Streamlit UI trực quan hóa quy trình
├── datademo/                  # Chứa các file PDF tiếng Việt công khai
│   ├── TT_02_2023_NHNN.pdf
│   ├── TT_06_2023_NHNN.pdf
│   └── TT_39_2016_NHNN.pdf
├── output/                    # Lưu trữ kết quả raw OCR & các file chunk JSON
├── src/
│   ├── .env                   # Lưu LLAMA_CLOUD_API_KEY
│   ├── check_ocr_env.py       # Script kiểm tra môi trường
│   ├── ocr_processor.py       # Module đọc PDF & OCR Fallback
│   └── chunking_strategies.py # Module 3 chiến lược chunking
├── storage/                   # Thư mục lưu cache tạm thời (nếu có)
└── tests/                     # Các kịch bản test kiểm thử
```
