---
id: RR-008
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-008: Định giá tài sản bảo đảm không chính xác

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-008`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro tin dung
- **Đơn vị quản lý (owner_unit_id)**: `DV-CREDIT`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Dữ liệu định giá không độc lập hoặc hết hạn

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Thiếu rà soát lại giá trị tài sản
- **Sự kiện (Event)**: Tài sản bảo đảm được định giá cao hơn thực tế
- **Hậu quả (Impact)**: Tăng tổn thất khi xử lý nợ

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-008 - Rà soát độc lập định giá tài sản bảo đảm]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: rà soát độc lập giảm sai định giá
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-008 - Rà soát phát hiện giá trị tài sản bảo đảm đã hết hiệu lực]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện sai định giá tài sản
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
