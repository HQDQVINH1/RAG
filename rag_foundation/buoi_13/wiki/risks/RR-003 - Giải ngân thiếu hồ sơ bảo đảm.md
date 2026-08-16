---
id: RR-003
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-003: Giải ngân thiếu hồ sơ bảo đảm

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-003`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro tin dung
- **Đơn vị quản lý (owner_unit_id)**: `DV-CREDIT`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Hồ sơ giải ngân chưa đủ điều kiện

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Kiểm tra điều kiện tiên quyết bị bỏ qua
- **Sự kiện (Event)**: Giải ngân khi thiếu chứng từ bắt buộc
- **Hậu quả (Impact)**: Khó thu hồi nợ và vi phạm quy trình

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-003 - Checklist điều kiện giải ngân bắt buộc]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: checklist ngăn giải ngân thiếu hồ sơ
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-003 - Giải ngân trước khi hoàn thiện chứng từ bảo đảm]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện giải ngân thiếu hồ sơ
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
