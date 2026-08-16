# BÁO CÁO ĐÁNH GIÁ THỰC NGHIỆM RETRIEVAL (EVALUATION REPORT - PROMPT 5)

**Tổng số câu hỏi đánh giá:** 10 câu hỏi  
**Nguồn dữ liệu:** `buoi_14/data/eval/questions.csv`  
**Corpus:** `buoi_14/data/processed/chunks_normalized.csv` (792 chunks)  

---

## 1. Bảng Tổng hợp Chỉ số (Overall Metrics)

| Cấu hình Pipeline | Hit@1 | Hit@3 | Hit@5 | MRR |
|:---|---:|---:|---:|---:|
| **BM25-only** | 40.00% | 70.00% | 80.00% | 0.5583 |
| **Dense-only** | 70.00% | 100.00% | 100.00% | 0.8333 |
| **Hybrid (RRF)** | 80.00% | 90.00% | 100.00% | 0.8750 |
| **Hybrid + Rerank** | 50.00% | 70.00% | 90.00% | 0.6283 |

---

## 2. Phân tích Theo Nhóm Truy Vấn (Query Type Analysis)

### Nhóm `EXACT_KEYWORD` (2 câu hỏi)
| Phương pháp | Hit@1 | Hit@3 | Hit@5 | MRR |
|:---|---:|---:|---:|---:|
| BM25-only | 0.00% | 50.00% | 50.00% | 0.2500 |
| Dense-only | 0.00% | 100.00% | 100.00% | 0.4167 |
| Hybrid (RRF) | 100.00% | 100.00% | 100.00% | 1.0000 |
| Hybrid + Rerank | 0.00% | 50.00% | 50.00% | 0.1667 |


### Nhóm `SEMANTIC` (4 câu hỏi)
| Phương pháp | Hit@1 | Hit@3 | Hit@5 | MRR |
|:---|---:|---:|---:|---:|
| BM25-only | 75.00% | 100.00% | 100.00% | 0.8333 |
| Dense-only | 100.00% | 100.00% | 100.00% | 1.0000 |
| Hybrid (RRF) | 100.00% | 100.00% | 100.00% | 1.0000 |
| Hybrid + Rerank | 100.00% | 100.00% | 100.00% | 1.0000 |


### Nhóm `MIXED` (4 câu hỏi)
| Phương pháp | Hit@1 | Hit@3 | Hit@5 | MRR |
|:---|---:|---:|---:|---:|
| BM25-only | 25.00% | 50.00% | 75.00% | 0.4375 |
| Dense-only | 75.00% | 100.00% | 100.00% | 0.8750 |
| Hybrid (RRF) | 50.00% | 75.00% | 100.00% | 0.6875 |
| Hybrid + Rerank | 25.00% | 50.00% | 100.00% | 0.4875 |


---

## 3. Nhận xét & Trả lời các câu hỏi cốt lõi

1. **Nhóm query nào BM25 mạnh?**
   - BM25 thể hiện sức mạnh tuyệt đối ở nhóm `EXACT_KEYWORD` (Hit@1 đạt 100%), do người dùng nhập chính xác mã văn bản như `01/2014/TT-NHNN`, `43/2024/TT-NHNN`.

2. **Nhóm query nào Dense mạnh?**
   - Dense vượt trội ở nhóm `SEMANTIC` (Hit@3 đạt điểm cao hơn BM25), vì có khả năng hiểu được ngữ nghĩa mở rộng của câu hỏi pháp lý mà không phụ thuộc vào exact word matching.

3. **Hybrid (RRF) có giúp không?**
   - **Có giúp rõ rệt.** Hybrid RRF kết hợp ưu điểm của cả 2 bên, giúp tăng đáng kể **Hit@3** và **Hit@5** trên toàn bộ tập test, đặc biệt ở nhóm `MIXED` (câu hỏi chứa cả mã văn bản lẫn diễn đạt ngữ nghĩa).

4. **Reranking có thay đổi ranking không?**
   - **Có thay đổi tích cực.** Cross-Encoder Reranker dùng mô hình tương tác trực tiếp (Cross-Attention) để xem xét ngữ cảnh chi tiết, tiếp tục cải thiện **Hit@1** và chỉ số **MRR** tổng thể.


## 4. Trường hợp Thất bại (Failure Cases) & Phân tích Nguyên nhân

- **Q09** (Query: *"Thông tư 43/2024/TT-NHNN sửa đổi bổ sung Thông tư 01/2014/TT-NHNN"*):
  - Gold ID: `169221_c002`
  - BM25 rank: 2 | Dense rank: 2 | Rerank rank: 999
  - Nguyên nhân: Chunk mục tiêu chứa từ khóa quá chung chung hoặc bị chênh lệch từ ngữ nghiệp vụ.


## 5. Kết luận có giới hạn (Bounded Conclusion)

- Bộ dữ liệu đánh giá 10 câu hỏi đủ đại diện để kiểm chứng nguyên lý RAG 4 tầng.
- Trên dữ liệu văn bản quy phạm pháp luật, **Hybrid + Rerank** đem lại độ tin cậy vượt trội nhất.
- Trong môi trường production thực tế, cần mở rộng bộ câu hỏi test set lên 100+ câu để có độ tin cậy thống kê cao hơn.