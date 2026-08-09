# BUỔI 08 — ADVANCED RAG & HYBRID RETRIEVAL WORKSHOP

---

## 📌 1. Mục Tiêu Dự Án & Sự Khác Biệt Buổi 07 vs Buổi 08

Dự án **Buổi 08** phát triển hệ thống **Advanced RAG (Retrieval-Augmented Generation)** nâng cao, giải quyết triệt để các hạn chế của **Baseline Semantic RAG (Buổi 07)** đối với văn bản pháp lý tiếng Việt.

### ⚖️ So Sánh Buổi 07 vs Buổi 08

| Đặc điểm / Hạng mục | Buổi 07 (Baseline Semantic RAG) | Buổi 08 (Advanced Hybrid RAG) |
|---|---|---|
| **Cơ chế Retrieval** | Thuần túy Semantic Vector Search (ChromaDB Cosine) | **Hybrid Search**: BM25 Lexical + Semantic Vector + RRF Fusion |
| **Bảo toàn Số hiệu / Ký tự** | Dễ bị bỏ sót số Điều/Khoản nếu từ vựng ít xuất hiện trong vector | **Tuyệt đối**: BM25 Tokenizer bảo toàn chính xác từng số Điều, Khoản |
| **Dung hợp Thứ hạng** | Không có dung hợp (Chỉ lấy theo Cosine Distance) | **Reciprocal Rank Fusion (RRF)** dung hợp 2 thang đo không cần min-max |
| **Tầng Xếp hạng lại** | Không có Reranker | **Cross-Encoder Reranker** (`BAAI/bge-reranker-v2-m3`) |
| **Confidence Gating** | Gating cố định theo Cosine Distance | Gating theo Reranker Sigmoid Score (`RERANK_MIN_SCORE`) |
| **Trích dẫn Evidence** | Nhãn trích dẫn cơ bản | Mapping nhãn `[E1]`, `[E2]` chính xác sang metadata thật (`source`, `page`, `chunk_id`) |
| **Giao diện & Chẩn đoán** | Form QA đơn giản | **Streamlit 4 Tab**: Hỏi đáp, So sánh 4 Mode, Pipeline Trace, Metrics |

---

## 🏗️ 2. Sơ Đồ Kiến Trúc Hệ Thống (Architecture Diagram)

```
                            [ User Query ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
[ BM25 Lexical Engine ]                           [ Semantic Vector Engine ]
(Tokenizer tiếng Việt NFC)                        (Gemini 768d Cosine Search)
         │                                                 │
   Top-K BM25 Candidates                            Top-K Semantic Candidates
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  ▼
                    [ Reciprocal Rank Fusion (RRF) ]
                    rrf_score = w1/(k+r1) + w2/(k+r2)
                                  │
                        Fused Top-K Candidates
                                  │
                                  ▼
                [ Cross-Encoder Reranker Stage ]
             (BAAI/bge-reranker-v2-m3 / PyTorch)
                                  │
                    Sigmoid Score >= RERANK_MIN_SCORE
                                  │
                       Accepted Evidences Only
                                  │
                                  ▼
                 [ Gemini LLM Grounded Generation ]
                                  │
                 [ Citation Mapping [E1] -> Metadata ]
                                  │
                       [ Final RAG Answer ]
```

---

## 📂 3. Cấu Trúc Dự Án `rag_foundation/buoi_08/`

```
rag_foundation/buoi_08/
├── SPEC_buoi_08.md              # Đặc tả kỹ thuật 12 tiêu chuẩn Advanced RAG
├── README.md                    # Tài liệu hướng dẫn & nghiệm thu dự án
├── requirements.txt             # Khai báo thư viện phụ thuộc trực tiếp
├── .env.example                 # Mẫu file cấu hình môi trường (.env)
├── .gitignore                   # Cấu hình bỏ qua .env, storage/, reports/
├── rag.py                       # [BASELINE] Sao chép từ Buổi 07 (Read-only reference)
├── advanced_rag.py              # [CORE] Engine BM25, Semantic, RRF, Reranker, Answer Pipeline
├── evaluate.py                  # [EVAL] Module đánh giá Recall@K, MRR@K, nDCG@K, Latency
├── app.py                       # [UI] Giao diện Streamlit Demo 4 Tab chuyên sâu
├── eval/
│   └── questions.json           # Tập 8 câu hỏi đánh giá Gold Standard mẫu
├── tests/
│   ├── __init__.py
│   ├── test_bm25.py             # Unit tests cho Tokenizer & BM25 Engine
│   ├── test_semantic.py         # Unit tests cho Semantic Retrieval & Status
│   ├── test_hybrid.py           # Unit tests cho RRF Fusion & Hybrid Search
│   ├── test_reranker.py         # Unit tests cho Cross-Encoder Reranker Stage
│   ├── test_answer.py           # Unit tests cho Answer Pipeline & Citations
│   ├── test_evaluator.py        # Unit tests cho công thức toán học Metrics
│   └── fixtures/
│       └── chunks_advanced_sample.json # Fixture 8 chunks tiếng Việt mẫu
├── reports/
│   └── eval_results.json        # Báo cáo JSON xuất kết quả đánh giá thực tế
└── storage/
    ├── chroma/                  # Thư mục lưu trữ Vector DB Chroma local
    └── huggingface/             # Thư mục cache trọng số mô hình Reranker local
```

---

## ⚙️ 4. Hướng Dẫn Thiết Lập Môi Trường (Setup)

1. **Sử dụng Môi trường Ảo của Buổi 05**:
   - Python Interpreter: `../buoi_05/.venv/Scripts/python.exe`

2. **Cài đặt Packages**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. **Cấu hình File Môi Trường (`.env`)**:
   - Sao chép `.env.example` thành `.env`:
   ```bash
   cp .env.example .env
   ```
   - Điền `GEMINI_API_KEY` của bạn vào file `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_EMBEDDING_MODEL=gemini-embedding-2
   GEMINI_EMBEDDING_DIM=768
   GEMINI_GENERATION_MODEL=gemini-3.5-flash-lite
   RAG_MAX_DISTANCE=0.45
   BM25_CANDIDATES=20
   SEMANTIC_CANDIDATES=20
   RRF_K=60
   RRF_BM25_WEIGHT=1.0
   RRF_SEMANTIC_WEIGHT=1.0
   RERANK_CANDIDATES=20
   FINAL_TOP_K=5
   RERANKER_MODEL=BAAI/bge-reranker-v2-m3
   RERANKER_MAX_LENGTH=512
   RERANK_BATCH_SIZE=4
   RERANK_MIN_SCORE=0.50
   RERANK_DEVICE=auto
   ```

---

## ⚠️ 5. Cảnh Báo Tài Nguyên Mô Hình Reranker

Mô hình Reranker mặc định **`BAAI/bge-reranker-v2-m3`**:
- **Kích thước file trọng số**: Khoảng 1.1GB – 2.2GB.
- **Yêu cầu hệ thống**: Yêu cầu kết nối Internet cho lần tải đầu tiên, tối thiểu 4GB RAM trống và đĩa cứng khả dụng.
- **Vị trí lưu cache**: `rag_foundation/buoi_08/storage/huggingface/`.
- **Cơ chế Lazy-Loading**: Hệ thống **KHÔNG** tự động tải hay nạp mô hình khi mở app hoặc chạy test. Mô hình chỉ được nạp khi người dùng chủ động thực thi lệnh `rerank` hoặc mode `hybrid_rerank`.

---

## 💻 6. Hướng Dẫn Sử Dụng Các Lệnh CLI Chẩn Đoán (`advanced_rag.py`)

1. **Kiểm tra Trạng thái Hệ thống (Read-Only)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py status --strategy hierarchical
   ```

2. **Khởi tạo Semantic Vector Index (ChromaDB)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py prepare-semantic --strategy hierarchical
   ```

3. **Chẩn đoán BM25 Lexical Retrieval**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py bm25 --strategy hierarchical --question "Điều 7 quy định gì?"
   ```

4. **Chẩn đoán Semantic Vector Retrieval**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py semantic --strategy hierarchical --question "Điều 7 quy định gì?"
   ```

5. **Chẩn đoán Hybrid RRF Retrieval**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py hybrid --strategy hierarchical --question "Điều 7 quy định gì?"
   ```

6. **Chẩn đoán Cross-Encoder Reranker**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py rerank --strategy hierarchical --question "Điều 7 quy định gì?"
   ```

7. **So sánh Thứ hạng giữa 4 Mode Retrieval (Không gọi LLM)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py compare --strategy hierarchical --question "Điều 7 quy định gì?"
   ```

8. **Truy vấn RAG Hoàn chỉnh (Có LLM Grounding & Citations)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe advanced_rag.py query --mode hybrid_rerank --strategy hierarchical --question "Điều kiện cơ cấu lại thời hạn trả nợ là gì?"
   ```

---

## 🧪 7. Lệnh Chạy Unittest, Evaluation & Streamlit

1. **Chạy Toàn Bộ Unit Tests (100% Offline)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
   ```

2. **Chạy Script Đánh Giá Metrics (Xuất JSON ra `reports/`)**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe evaluate.py --strategy hierarchical --k 5
   ```

3. **Khởi Chạy Ứng Dụng Streamlit Web App**:
   ```bash
   ..\buoi_05\.venv\Scripts\python.exe -m streamlit run app.py
   ```

---

## 📊 8. Giải Thích Chi Tiết Các Thang Đo (Metrics & Scores)

1. **BM25 Score**: Điểm số tần suất từ khóa BM25Okapi trên corpus tiếng Việt. **Điểm cao hơn đại diện cho độ khớp từ khóa tốt hơn**.
2. **Cosine Distance**: Khoảng cách góc giữa 2 vector Gemini 768d. **Khoảng cách thấp hơn đại diện cho độ tương đồng ngữ nghĩa cao hơn**.
3. **RRF Score**: Điểm số dung hợp Reciprocal Rank Fusion $1/(K + rank)$. Giải quyết rào cản khác thang đo giữa BM25 Score và Cosine Distance.
4. **Rerank Score (Sigmoid)**: Điểm số tương quan từ mô hình Cross-Encoder $\sigma(\text{logit}) = \frac{1}{1 + e^{-\text{logit}}} \in [0.0, 1.0]$. *(Lưu ý: Rerank Score là điểm chuẩn hóa của mô hình, không đại diện cho xác suất thống kê đúng/sai).*

---

## 🎯 9. Phân Biệt Candidate $K$ và Final Top-$K$

- **Candidate $K$ (`BM25_CANDIDATES`, `SEMANTIC_CANDIDATES`, `RERANK_CANDIDATES`)**: Số lượng ứng viên được giữ lại ở các tầng trung gian (BM25, Vector Search, RRF) để làm đầu vào cho tầng Rerank tiếp theo (mặc định 20 ứng viên).
- **Final Top-$K$ (`FINAL_TOP_K`)**: Số lượng ứng viên xuất sắc nhất còn lại sau tầng Reranker được đưa vào Prompt làm Context cho LLM trả lời (mặc định 5 ứng viên).

---

## 📈 10. Chỉ Số Đánh Giá (Evaluation Metrics) & Cảnh Báo Gold Labels

1. **Recall@K**: Tỷ lệ tìm thấy các chunk đúng trong Top-$K$.
2. **MRR@K (Mean Reciprocal Rank)**: Điểm vị trí thứ hạng nghịch đảo của chunk đúng đầu tiên trong Top-$K$.
3. **nDCG@K (Normalized Discounted Cumulative Gain)**: Đánh giá chất lượng thứ tự xếp hạng của danh sách trích xuất với Binary Relevance.
4. **Cảnh báo Gold Labels**: Nếu tập `eval/questions.json` chứa câu hỏi có nhãn `"needs_human_review": true`, báo cáo sẽ xuất hiện cảnh báo và **không dùng kết quả này để tuyên bố chiến thắng chính thức** giữa các mode retrieval.

---

## 🛠️ 11. Hướng Dẫn Xử Lý Lỗi (Troubleshooting)

1. **Lỗi tải mô hình Reranker từ Hugging Face**:
   - *Nguyên nhân*: Kết nối Internet chập chờn hoặc hết dung lượng đĩa.
   - *Xử lý*: Kiểm tra kết nối mạng hoặc thử chạy lại lệnh `advanced_rag.py rerank`.
2. **CPU xử lý Reranker bị chậm**:
   - *Xử lý*: Giảm `RERANK_CANDIDATES` xuống 10 hoặc cài đặt PyTorch với CUDA hỗ trợ GPU trong `.env` (`RERANK_DEVICE=cuda`).
3. **Thiếu API Key Gemini**:
   - *Xử lý*: Đảm bảo file `.env` đã khai báo đúng `GEMINI_API_KEY`.

---

## ⚖️ 12. Câu Hỏi So Sánh Thủ Công (Manual Comparison Questions)

Dưới đây là 4 nhóm câu hỏi mẫu được thiết kế để thử nghiệm so sánh hiệu năng giữa 4 mode retrieval:

### A. Câu hỏi khớp chính xác số Điều/Khoản (Exact Legal Reference)
> **Câu hỏi**: *"Điều 7 quy định như thế nào về cơ cấu lại thời hạn trả nợ?"*
> - **Kỳ vọng**: BM25 & Hybrid xếp chunk chứa đúng chữ "Điều 7" lên hàng đầu.

### B. Câu hỏi diễn giải ngữ nghĩa (Paraphrase Semantic)
> **Câu hỏi**: *"Khách hàng gặp khó khăn có thể được điều chỉnh kỳ hạn trả nợ ra sao?"*
> - **Kỳ vọng**: Semantic Vector Search & Hybrid RRF tìm ra các chunk đồng nghĩa dù không chứa cụm từ khóa exact match.

### C. Câu hỏi đa khái niệm (Multi-Concept Query)
> **Câu hỏi**: *"Phân loại nợ và trích lập dự phòng được thực hiện như thế nào?"*
> - **Kỳ vọng**: Reranker xếp hạng lại các chunk thỏa mãn đồng thời cả 2 khái niệm "phân loại nợ" và "trích lập dự phòng".

### D. Câu hỏi ngoài phạm vi tài liệu (Out-of-Scope Query)
> **Câu hỏi**: *"Ngân hàng nào có lãi suất tiết kiệm cao nhất hôm nay?"*
> - **Kỳ vọng**: Confidence Gating từ chối tất cả candidates và trả về trạng thái `insufficient_evidence`.

---

## ⚖️ 13. Tuyên Bố Miễn Trừ Trách Nhiệm (Legal Disclaimer)

Dự án này được xây dựng thuần túy phục vụ cho mục đích thực hành kỹ thuật RAG trong khuôn khổ Workshop. Tất cả câu trả lời do AI sinh ra không cấu thành lời khuyên hay tư vấn pháp lý chính thức. Người dùng cần đối chiếu với các văn bản quy phạm pháp luật do Ngân hàng Nhà nước Việt Nam ban hành.
