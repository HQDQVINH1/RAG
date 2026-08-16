# BUỔI 14 — Hybrid Search + Reranking + Mini Knowledge Graph

Thư mục này chứa toàn bộ tài nguyên, mã nguồn, dữ liệu xử lý, truy vấn Cypher, ứng dụng Streamlit và báo cáo cho **Buổi 14**.

---

## 1. Cấu trúc thư mục

```text
buoi_14/
├── .env                        # Cấu hình biến môi trường (Neo4j Credentials)
├── .venv/                      # Virtual environment riêng cho Buổi 14
├── app.py                      # Giao diện Web App Streamlit trực quan (Prompt 8)
├── cache/                      # Thư mục lưu cache vector embedding (dense_embeddings_*.pkl)
├── cypher/
│   ├── schema.cypher           # Constraints & Indexes cho Knowledge Graph
│   └── demo_queries.cypher     # Các câu truy vấn Cypher trực quan minh họa
├── data/
│   ├── eval/
│   │   └── questions.csv       # Bộ 10 câu hỏi đánh giá thực nghiệm (Prompt 5)
│   └── processed/
│       └── chunks_normalized.csv # Corpus đã chuẩn hóa (792 chunks từ 15 văn bản)
├── outputs/
│   ├── inspection_report.md    # Báo cáo Pre-check (Prompt 0)
│   ├── retrieval_examples.md   # Báo cáo ví dụ minh họa 4 giai đoạn (Prompt 2, 3 & 4)
│   ├── retrieval_comparison.csv# Bảng kết quả chi tiết từng câu hỏi (Prompt 5)
│   ├── evaluation_report.md    # Báo cáo đánh giá các chỉ số Hit@k và MRR (Prompt 5)
│   └── kg_build_report.md      # Báo cáo nạp Knowledge Graph mini vào Neo4j (Prompt 6)
├── requirements.txt            # Danh sách thư viện phụ thuộc của dự án
├── scripts/
│   ├── prepare_corpus.py       # Script chuẩn hóa corpus (Prompt 1)
│   ├── baseline_retrieval.py   # Script CLI chạy thử nghiệm BM25 & Dense baseline (Prompt 2)
│   ├── hybrid_search.py        # Script CLI chạy thử nghiệm Hybrid Search RRF (Prompt 3)
│   ├── rerank.py               # Script CLI chạy thử nghiệm Cross-Encoder Reranker (Prompt 4)
│   ├── run_evaluation.py       # Script chạy ví dụ minh họa 4 giai đoạn (Prompt 2, 3 & 4)
│   ├── compare_retrieval.py    # Script chạy tự động bộ Đánh giá 4 cấu hình (Prompt 5)
│   ├── load_mini_kg.py         # Script nạp Knowledge Graph mini vào Neo4j (Prompt 6)
│   └── query_demo.py           # Script CLI Demo tích hợp Pipeline RAG & GRAPH HINTS (Prompt 7)
├── src/
│   ├── __init__.py
│   ├── bm25_retriever.py       # Module BM25 Lexical Retriever
│   ├── dense_retriever.py      # Module Dense Vector Retriever (bkai-foundation-models)
│   ├── hybrid_retriever.py     # Module Hybrid Retriever (Reciprocal Rank Fusion RRF)
│   ├── reranker.py             # Module Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)
│   └── unified_retriever.py    # Module Unified Retriever kết nối 4 phương pháp & Graph Hints (Prompt 7)
├── README.md                   # Tài liệu hướng dẫn thực chạy
└── buoi14.md                   # Hướng dẫn chi tiết Buổi 14
```

---

## 2. Hướng dẫn thiết lập môi trường & Chạy ứng dụng

### Step 1: Kích hoạt môi trường ảo Python
```bash
cd rag_foundation/buoi_14
.\.venv\Scripts\Activate.ps1
```

### Step 2: Cài đặt gói phụ thuộc từ `requirements.txt`
```bash
.\.venv\Scripts\pip install -r requirements.txt
```

### Step 3: Chuẩn hóa Corpus (Prompt 1)
```bash
.\.venv\Scripts\python scripts/prepare_corpus.py
```

### Step 4: Chạy thử nghiệm CLI (Prompt 2, 3, 4, 5, 6, 7)
```bash
# Baseline BM25 & Dense (Prompt 2)
.\.venv\Scripts\python scripts/baseline_retrieval.py --query "Quy định bảo quản tiền mặt theo 01/2014/TT-NHNN" --top-k 5

# Hybrid Search RRF (Prompt 3)
.\.venv\Scripts\python scripts/hybrid_search.py --query "Quy định bảo quản tiền mặt theo 01/2014/TT-NHNN" --candidate-k 20 --top-k 5

# Reranker (Prompt 4)
.\.venv\Scripts\python scripts/rerank.py --query "Quy định bảo quản tài sản quý và giấy tờ có giá theo 01/2014/TT-NHNN" --candidate-k 20 --top-k 5

# Đánh giá 4 cấu hình (Prompt 5)
.\.venv\Scripts\python scripts/compare_retrieval.py

# Nạp Knowledge Graph vào Neo4j (Prompt 6)
.\.venv\Scripts\python scripts/load_mini_kg.py

# Unified CLI & Graph Hints (Prompt 7)
.\.venv\Scripts\python scripts/query_demo.py --query "Quy định bảo quản tài sản quý và giấy tờ có giá theo 01/2014/TT-NHNN" --method hybrid_rerank --top-k 5
```

---

## 3. Hướng dẫn Sử dụng Giao diện Web App Streamlit (`app.py`)

### 3.1 Lệnh khởi chạy Web App (Prompt 8)
```bash
.\.venv\Scripts\streamlit run app.py
```
> **URL truy cập local:** `http://localhost:8501`  
> **URL mạng nội bộ:** `http://192.168.31.50:8501`

### 3.2 Lệnh dừng Web App Streamlit
Trong cửa sổ Terminal đang chạy Streamlit, nhấn tổ hợp phím: `Ctrl + C`.

### 3.3 Hướng dẫn chọn Phương pháp Tìm kiếm (Method Selection)
Tại thanh Menu bên trái (Sidebar), người dùng có thể chọn 1 trong 4 chế độ:
- **BM25:** Tìm kiếm theo từ khóa exact match (Lexical BM25).
- **Dense:** Tìm kiếm ngữ nghĩa vector embedding (`bkai-foundation-models/vietnamese-bi-encoder`).
- **Hybrid:** Hợp nhất kết quả từ BM25 và Dense bằng thuật toán Reciprocal Rank Fusion (RRF $k=60$).
- **Hybrid + Rerank:** Chuỗi luồng hoàn chỉnh: *Hybrid Search (Candidate-K=20) $\rightarrow$ Cross-Encoder Reranker $\rightarrow$ Top-k*.

### 3.4 Ý nghĩa các trường kết quả hiển thị trên Giao diện
- **Rank:** Thứ hạng ưu tiên cuối cùng của đoạn văn bản.
- **Chunk ID:** Định danh duy nhất của đoạn văn bản (vd `44209_c012`).
- **Document ID:** ID của văn bản quy phạm pháp luật gốc (vd `44209`).
- **Score:** Điểm số tương thích (BM25 score, Cosine similarity, RRF score hoặc Cross-Encoder Rerank score).
- **Citation:** Chuỗi trích dẫn nguồn chuẩn hóa `[Số ký hiệu | Điều X | Chunk_ID]`.
- **BEFORE RERANK vs AFTER RERANK:** Bảng so sánh thứ hạng trực quan giúp học viên quan sát sự dịch chuyển thứ hạng của từng chunk trước và sau khi đi qua mô hình Cross-Encoder Reranker.
- **Graph Hints:** Danh sách ID văn bản, ID chunk và các mối quan hệ pháp lý 1-hop trực tiếp (`SUA_DOI_BO_SUNG`, `CAN_CU`, `BI_THAY_THE`) phục vụ định hướng sang buổi thực hành Graph RAG tiếp theo.
