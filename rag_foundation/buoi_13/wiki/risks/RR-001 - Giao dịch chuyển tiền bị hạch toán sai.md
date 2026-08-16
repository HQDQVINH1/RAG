---
id: RR-001
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-001: Giao dịch chuyển tiền bị hạch toán sai

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-001`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro van hanh
- **Đơn vị quản lý (owner_unit_id)**: `DV-OPS`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Đối soát giao dịch cuối ngày không đầy đủ

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Thiếu đối chiếu giữa hệ thống thanh toán và sổ cái
- **Sự kiện (Event)**: Giao dịch được ghi nhận sai trạng thái
- **Hậu quả (Impact)**: Tổn thất tài chính và khiếu nại khách hàng

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-001 - Đối soát tự động giao dịch và sổ cái]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: đối soát tự động giảm nguy cơ hạch toán sai
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-001 - Sai lệch trạng thái giao dịch được phát hiện khi đối soát cuối ngày]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện đối soát giao dịch
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
