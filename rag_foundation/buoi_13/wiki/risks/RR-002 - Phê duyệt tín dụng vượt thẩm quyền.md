---
id: RR-002
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-002: Phê duyệt tín dụng vượt thẩm quyền

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-002`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro tin dung
- **Đơn vị quản lý (owner_unit_id)**: `DV-CREDIT`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Kiểm tra hạn mức phê duyệt không hiệu lực

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Phân quyền trên hệ thống không cập nhật
- **Sự kiện (Event)**: Khoản vay được phê duyệt vượt thẩm quyền
- **Hậu quả (Impact)**: Tăng nợ xấu và vi phạm quy định

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-002 - Kiểm tra hạn mức phê duyệt trên hệ thống]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: kiểm tra hạn mức ngăn phê duyệt vượt thẩm quyền
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-002 - Hồ sơ tín dụng được phê duyệt vượt hạn mức của người phê duyệt]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện vượt thẩm quyền
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
