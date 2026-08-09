# BÀI THỰC HÀNH — BUỔI 07: HOÀN THIỆN RAG PIPELINE VỚI AI AGENT

## 1. Mục tiêu

Dự án Buổi 07 hoàn thiện một hệ thống Retrieval-Augmented Generation (RAG) chuẩn sản xuất:
- **Kiểm soát dữ liệu nghiêm ngặt:** Loader & Validator kiểm tra schema, chặn duplicate `chunk_id` và loại bỏ text rỗng.
- **Vector Indexing bền vững:** Lưu trữ persistent vector store trong ChromaDB với Cosine distance metric, định danh collection theo `strategy`, `dimension` và `model_hash`.
- **Confidence Gate & Grounding:** Lọc bằng chứng qua ngưỡng `RAG_MAX_DISTANCE` (Cosine Distance) trước khi đưa vào Gemini LLM generation.
- **Citation Mapping minh bạch:** Tự động đối chiếu nhãn `[E1]`, `[E2]` sang metadata thật (`[Nguồn: ..., tr. N-M, chunk: ...]`) và phát hiện nhãn ảo `[E99]`.
- **Giao diện Streamlit & CLI:** Cung cấp đầy đủ công cụ quản trị Read-only status, Indexing và Query hỏi đáp.
- **Kiểm thử tự động:** Bộ test suite 33 test cases phủ 100% các tình huống biên.

---

## 2. Mối quan hệ với Buổi 05 và Buổi 06

- **Buổi 05 (Data Preparation):** Cung cấp các file chunks JSON đã qua chuẩn hóa và OCR tại `rag_foundation/buoi_05/output/chunks/` cùng môi trường ảo `rag_foundation/buoi_05/.venv/`.
- **Buổi 06 (RAG Demo):** Cung cấp mô hình RAG cơ bản thử nghiệm.
- **Buổi 07 (RAG Agent System):** Kế thừa dữ liệu Buổi 05 và xây dựng lại RAG pipeline chuẩn hóa, bảo mật, có Citation mapping và bộ unit test offline hoàn chỉnh. Không chỉnh sửa code hay dữ liệu của Buổi 05 và Buổi 06.

---

## 3. Sơ đồ RAG Pipeline

```text
Chunks JSON (Buổi 05)
       │
       ▼
 [ 1. Loader & Validator ] ──(Chặn lỗi schema/duplicate)
       │
       ▼
 [ 2. Gemini Embedding ] ──(Tạo vector & validate NaN/Inf/Zero)
       │
       ▼
 [ 3. ChromaDB Persistent Client ] ──(Cosine metric: nhnn-<strat>-<dim>-<hash>)
       │
       ▼
 [ 4. Semantic Retrieval ] ──(Query Top-K & Cosine Distance)
       │
       ▼
 [ 5. Confidence Gate ] ──(Lọc distance <= RAG_MAX_DISTANCE)
       ├── (Không đạt) ──► status: insufficient_evidence
       └── (Đạt)
            │
            ▼
 [ 6. Grounding Prompt ] ──(Bọc thẻ <EVIDENCE_DATA> chống Injection)
            │
            ▼
 [ 7. Gemini LLM Call ] ──► status: retrieval_only (nếu lỗi)
            │
            ▼
 [ 8. Citation Mapping ] ──(Thay [E1] -> [Nguồn: ..., tr. N, chunk: ...])
            │
            ▼
 [ 9. Streamlit UI / CLI ] ──(Hiển thị Answer, Citations & Evidence)
```

---

## 4. Cấu trúc thư mục Dự án

```text
rag_foundation/buoi_07/
├── SPEC_buoi_07.md         # Tài liệu quy chuẩn Agent Specification (12 mục contract)
├── Buoi_07.md             # Tài liệu hướng dẫn thực hành Buổi 07
├── rag.py                 # Core RAG Pipeline module (Loader, Indexer, Query Engine)
├── app.py                 # Streamlit Web Application Interface
├── requirements.txt       # Danh sách thư viện phụ thuộc
├── .env.example           # File mẫu biến môi trường
├── .env                   # Biến môi trường thực tế (Gitignored)
├── .gitignore             # Cấu hình GitIgnore
├── README.md              # Tài liệu hướng dẫn sử dụng & nghiệm thu
├── storage/               # Lưu trữ ChromaDB persistent database
│   ├── chroma/            # Dữ liệu ChromaDB sqlite & vectors
│   └── .gitkeep
└── tests/                 # Thư mục unit test tự động (33 test cases)
    ├── __init__.py
    ├── test_loader.py
    ├── test_indexing.py
    ├── test_query_pipeline.py
    └── fixtures/
        └── chunks_sample.json
```

---

## 5. Điều kiện đầu vào

Dữ liệu chunks JSON được đọc từ:
`rag_foundation/buoi_05/output/chunks/`

Yêu cầu các file chứa danh sách chunk object chứa đầy đủ các trường:
`chunk_id`, `strategy`, `source`, `page_start`, `page_end`, `text`.

---

## 6. Hướng dẫn sử dụng Python Interpreter (`.venv`)

Dự án sử dụng trực tiếp môi trường ảo của Buổi 05.

- **Windows PowerShell:**
  `rag_foundation/buoi_05/.venv/Scripts/python.exe`
- **Linux / macOS:**
  `rag_foundation/buoi_05/.venv/bin/python`

---

## 7. Cài đặt Dependencies

Chạy lệnh cài đặt các package trong `requirements.txt` bằng đúng interpreter Buổi 05:

- **Windows:**
  ```powershell
  & "rag_foundation/buoi_05/.venv/Scripts/python.exe" -m pip install -r rag_foundation/buoi_07/requirements.txt
  ```
- **Linux/macOS:**
  ```bash
  rag_foundation/buoi_05/.venv/bin/python -m pip install -r rag_foundation/buoi_07/requirements.txt
  ```

---

## 8. Cấu hình Biến môi trường (`.env`)

Sao chép từ `.env.example` để tạo `.env`:

- **Windows:**
  ```powershell
  Copy-Item rag_foundation/buoi_07/.env.example rag_foundation/buoi_07/.env
  ```
- **Linux/macOS:**
  ```bash
  cp rag_foundation/buoi_07/.env.example rag_foundation/buoi_07/.env
  ```

Điền `GEMINI_API_KEY=<KEY_CỦA_BẠN>` vào file `rag_foundation/buoi_07/.env`.

---

## 9. Giải thích các Biến Môi Trường

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `GEMINI_API_KEY` | API Key kết nối Google Gemini API | *(Cần điền)* |
| `GEMINI_EMBEDDING_MODEL` | Tên mô hình tạo vector embedding | `gemini-embedding-2` |
| `GEMINI_EMBEDDING_DIM` | Số chiều của vector embedding (128 - 3072) | `768` |
| `GEMINI_GENERATION_MODEL` | Tên mô hình LLM tổng hợp câu trả lời | `gemini-3.5-flash-lite` |
| `DEFAULT_TOP_K` | Số lượng chunk truy xuất mặc định (1 - 20) | `5` |
| `RAG_MAX_DISTANCE` | Ngưỡng Cosine Distance tối đa chấp nhận (Confidence Gate) | `0.45` |

---

## 10. Lệnh Validate Chunks JSON (`validate`)

Kiểm tra cú pháp và thống kê dữ liệu chunks mà không can thiệp database:

```powershell
& "rag_foundation/buoi_05/.venv/Scripts/python.exe" rag_foundation/buoi_07/rag.py validate --strategy hierarchical
```

---

## 11. Lệnh Kiểm Tra Trạng Thái (`status`)

Hiển thị thông tin cấu hình và trạng thái Read-only của Chroma collection:

```powershell
& "rag_foundation/buoi_05/.venv/Scripts/python.exe" rag_foundation/buoi_07/rag.py status --strategy hierarchical
```

---

## 12. Lệnh Indexing Dữ Liệu (`index`)

Tạo vector embedding và upsert dữ liệu vào ChromaDB:

```powershell
& "rag_foundation/buoi_05/.venv/Scripts/python.exe" rag_foundation/buoi_07/rag.py index --strategy hierarchical
```

---

## 13. Lệnh Reset Collection (`index --reset`)

Xóa và khởi tạo lại collection tương ứng trước khi index:

```powershell
& "rag_foundation/buoi_05/.venv/Scripts/python.exe" rag_foundation/buoi_07/rag.py index --strategy hierarchical --reset
```

---

## 14. Lệnh Truy Vấn CLI (`query`)

Truy vấn semantic và tổng hợp câu trả lời qua CLI:

```powershell
& "rag_foundation/buoi_05/.venv/Scripts/python.exe" rag_foundation/buoi_07/rag.py query --strategy hierarchical --top-k 5 --question "Cơ cấu lại thời hạn trả nợ được quy định như thế nào?"
```

---

## 15. Lệnh Chạy Unit Test Tự Động (`unittest`)

Chạy toàn bộ 33 test cases offline:

- **Windows:**
  ```powershell
  & "rag_foundation/buoi_05/.venv/Scripts/python.exe" -m unittest discover -s rag_foundation/buoi_07/tests -v
  ```
- **Linux/macOS:**
  ```bash
  rag_foundation/buoi_05/.venv/bin/python -m unittest discover -s rag_foundation/buoi_07/tests -v
  ```

---

## 16. Lệnh Khởi Chạy Giao Diện Web Streamlit (`app.py`)

- **Windows:**
  ```powershell
  & "rag_foundation/buoi_05/.venv/Scripts/python.exe" -m streamlit run rag_foundation/buoi_07/app.py
  ```
- **Linux/macOS:**
  ```bash
  rag_foundation/buoi_05/.venv/bin/python -m streamlit run rag_foundation/buoi_07/app.py
  ```

---

## 17. Giải Thích Thuật Ngữ RAG

- **Strategy:** Phương pháp phân đoạn tài liệu (`fixed-size`, `semantic`, `hierarchical`).
- **Embedding Model & Dimension:** Mô hình chuyển đổi văn bản thành vector (mặc định 768 chiều).
- **Collection Identity:** Định danh collection độc lập (`nhnn-<strategy>-<dimension>-<model_hash>`) để tránh nạp nhầm vector không tương thích.
- **Top-K:** Số lượng bằng chứng có khoảng cách gần nhất được lấy ra từ database.
- **Cosine Distance:** Thước đo khoảng cách giữa 2 vector. Khoảng cách **càng nhỏ** thể hiện độ tương đồng **càng cao** (0.0 là trùng khớp hoàn toàn).
- **RAG_MAX_DISTANCE:** Ngưỡng lọc bằng chứng. Chỉ các bằng chứng có `distance <= RAG_MAX_DISTANCE` mới được gọi là `accepted`.
- **Confidence Gate:** Tầng kiểm duyệt bằng chứng. Nếu không có bằng chứng nào đạt ngưỡng, hệ thống từ chối gọi LLM và trả lời không đủ thông tin.
- **Retrieval-Only:** Trạng thái khi đã tìm thấy bằng chứng nhưng quá trình gọi LLM bị lỗi hoặc trả về text rỗng.
- **Citation Mapping:** Quá trình tự động thay thế nhãn `[E1]` trong câu trả lời thành chuỗi trích dẫn chứa tên file, trang và chunk_id lấy từ metadata thật.

---

## 18. Cách Dừng Streamlit

Tại cửa sổ Terminal đang chạy ứng dụng Streamlit, nhấn tổ hợp phím **`Ctrl + C`** để dừng ứng dụng.

---

## 19. Hướng Dẫn Xử Lý Lỗi (Troubleshooting)

1. **Lỗi `ModuleNotFoundError`:** Đảm bảo bạn đang chạy bằng đúng Python interpreter của venv (`rag_foundation/buoi_05/.venv/`).
2. **Thiếu API Key:** Kiểm tra file `rag_foundation/buoi_07/.env` đã có dòng `GEMINI_API_KEY=AQ...` hay chưa.
3. **Collection Rỗng (0 Record):** Chạy lại lệnh `index` cho strategy tương ứng trước khi `query`.
4. **Metadata Mismatch Error:** Nếu thay đổi Embedding Model hoặc Dimension, hãy chạy lệnh `index --reset` để tạo lại collection.
5. **Lỗi Rate Limit (429 RESOURCE_EXHAUSTED):** Hệ thống đã tự động cài đặt cơ chế chờ 15s-60s và pacing 0.6s/request để phù hợp với tài khoản Gemini API Free Tier.

---

## 20. Giới Hạn Của Bản Demo

- Phụ thuộc vào hạn ngạch (quota) của tài khoản Gemini API Free Tier (100 requests/phút).
- Database lưu trữ cục bộ dưới dạng SQLite/HNSW index qua ChromaDB.
- Chỉ hỗ trợ truy vấn đơn lượt (Single-turn QA), không lưu lịch sử hội thoại nhiều lượt.

---

## 21. Cảnh Báo An Toàn & Bảo Mật

> [!WARNING]
> 1. **Không phải tư vấn pháp lý:** Câu trả lời tổng hợp từ AI chỉ mang tính chất tham khảo nghiệp vụ, không thay thế cho văn bản quy phạm pháp luật chính thức.
> 2. **Hiệu chỉnh Ngưỡng:** Ngưỡng `RAG_MAX_DISTANCE = 0.45` là ngưỡng thử nghiệm. Cần hiệu chỉnh lại tùy theo tập dữ liệu thực tế.
> 3. **Bảo mật Dữ liệu:** Khi thực hiện Index và Query, nội dung chunk sẽ được gửi tới Google Gemini API. Chỉ nạp các tài liệu mà tổ chức cho phép gửi tới dịch vụ cloud bên ngoài.

---

## 22. Kế Hoạch Kiểm Thử Thủ Công (Manual Test Plan)

Thực hiện kiểm thử 3 câu hỏi nghiệp vụ trên giao diện Streamlit hoặc CLI:

### Câu A (Nội dung thuộc tài liệu):
- **Câu hỏi:** `Cơ cấu lại thời hạn trả nợ được quy định như thế nào?`
- **Kỳ vọng:** Trạng thái `answered`, trích xuất đúng các bằng chứng từ Thông tư 02/2023/TT-NHNN và trích dẫn chuẩn `[Nguồn: TT_02_2023_NHNN.pdf, tr. ..., chunk: ...]`.

### Câu B (Nội dung thuộc tài liệu):
- **Câu hỏi:** `Việc phân loại nợ và trích lập dự phòng được thực hiện như thế nào?`
- **Kỳ vọng:** Trạng thái `answered`, trích xuất các bằng chứng từ Thông tư 39/2016/TT-NHNN và Thông tư 02/2023/TT-NHNN kèm trích dẫn nguồn chi tiết.

### Câu C (Ngoại phạm vi tài liệu):
- **Câu hỏi:** `Ngân hàng nào có lãi suất tiết kiệm cao nhất hôm nay?`
- **Kỳ vọng:** Do dữ liệu không chứa thông tin lãi suất tiết kiệm hôm nay, khoảng cách Cosine Distance sẽ vượt ngưỡng `RAG_MAX_DISTANCE`. Confidence Gate chặn không gọi LLM và trả về thông báo:
  > *"Không tìm thấy đủ thông tin liên quan trong tài liệu đã cung cấp."*
- **Lưu ý:** Không tự bịa đặt tên ngân hàng hay số liệu lãi suất. Nếu câu hỏi C vẫn vượt qua gate, ghi nhận là false positive của retrieval/threshold mà không can thiệp sửa câu trả lời thủ công.
