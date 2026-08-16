---
id: RR-004
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-004: Lộ thông tin khách hàng

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-004`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro cong nghe thong tin
- **Đơn vị quản lý (owner_unit_id)**: `DV-IT`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Quyền truy cập dữ liệu không được kiểm soát phù hợp

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Cấp quyền vượt nhu cầu công việc
- **Sự kiện (Event)**: Dữ liệu khách hàng bị truy cập hoặc chia sẻ trái phép
- **Hậu quả (Impact)**: Vi phạm bảo mật và tổn hại uy tín

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-004 - Rà soát quyền truy cập định kỳ]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: rà soát quyền hạn giảm lộ dữ liệu
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-004 - Tài khoản có quyền truy cập dữ liệu vượt phạm vi công việc]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện quyền truy cập quá mức
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
