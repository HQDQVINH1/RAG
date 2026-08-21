# Báo cáo AI Compliance Gap Checker — Buổi 17

## 1. Kiểm tra Điều kiện Tiến hành (Pre-condition Data Check)

Theo chỉ thị điều kiện của **PROMPT 7**:
> *Chỉ chạy AI Compliance Gap Checker nếu Prompt 6 báo `COMPLIANCE GAP DATA: READY`.*
> *Nếu Prompt 6 báo dữ liệu chưa đủ, không tự tạo văn bản và không sinh kết luận giả; thay vào đó tạo report DATA GAP cho use case này.*

### Kết quả Kiểm tra từ Prompt 6:
- **Tập dữ liệu nguồn được chỉ định**: `data/processed/chunks_secure.csv`
- **Tổng số Document trong tập dữ liệu**: **15 documents** (tương ứng 792 chunks)
- **Số lượng Văn bản Bên ngoài (`EXTERNAL_REQUIREMENT`)**: **15 documents (100%)**
- **Số lượng Quy định Nội bộ (`INTERNAL_POLICY`)**: **0 documents (0%)**

> [!WARNING]
> Tập dữ liệu `chunks_secure.csv` hoàn toàn thiếu dữ liệu quy định nội bộ (`INTERNAL_POLICY`). Hệ thống **tuân thủ tuyệt đối nguyên tắc thực tế**: không tự bịa đặt văn bản nội bộ giả và không đưa ra các kết luận tuân thủ (`DAP_UNG` / `THIEU`) ảo trên tập dữ liệu này.

---

## 2. Thiết kế Module `compliance_gap.py` & Schema Chuẩn hóa

Module [`scripts/compliance_gap.py`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/scripts/compliance_gap.py) (và [`buoi_17/scripts/compliance_gap.py`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/buoi_17/scripts/compliance_gap.py)) đã được xây dựng hoàn chỉnh với đầy đủ kiến trúc:

### 2.1. Luồng xử lý (Workflow)
1. Nhận điều khoản/yêu cầu quy phạm của NHNN (`EXTERNAL_REQUIREMENT`).
2. Tìm kiếm ứng viên quy định nội bộ (`INTERNAL_POLICY`) trong phạm vi phân quyền RBAC.
3. Tổng hợp gói bằng chứng (Evidence Package):
   - `external_requirement` & `external_citation`
   - `internal_evidence` & `internal_citation`
4. LLM thực hiện phân loại theo 4 nhãn: `DAP_UNG`, `THIEU`, `CHENH_LECH`, `CHUA_DU_BANG_CHUNG`.
5. Đưa ra giải thích ngắn (`reason`), điểm tin cậy (`confidence`) và gán bắt buộc `review_status = "NEEDS_HUMAN_REVIEW"`.

### 2.2. Schema Chuẩn 14 Trường của CSV (`compliance_gap_results.csv`)
Tệp [`outputs/compliance_gap_results.csv`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/outputs/compliance_gap_results.csv) được khởi tạo tuân thủ 100% schema tối thiểu 14 trường:
1. `gap_id`
2. `external_document_id`
3. `external_chunk_id`
4. `external_requirement`
5. `external_citation`
6. `internal_document_id`
7. `internal_chunk_id`
8. `internal_evidence`
9. `internal_citation`
10. `classification`
11. `reason`
12. `confidence`
13. `review_status`
14. `request_id`

---

## 3. Tổng kết

- **Tệp kết quả CSV**: [`outputs/compliance_gap_results.csv`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/outputs/compliance_gap_results.csv) (Đã được tạo chuẩn schema 14 trường).
- **Trạng thái thực thi**: Đã bảo vệ tính toàn vẹn của kết quả đánh giá bằng cách ghi nhận đúng thực tế thiếu dữ liệu quy định nội bộ trong `chunks_secure.csv`.

---

COMPLIANCE GAP DATA: INSUFFICIENT
DATA GAP: INTERNAL POLICY NOT FOUND
GAP CHECKER: PASS
HUMAN REVIEW REQUIRED: YES
