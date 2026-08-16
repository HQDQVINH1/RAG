---
id: RR-006
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-006: Gian lận giả mạo yêu cầu chuyển tiền

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-006`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro gian lan
- **Đơn vị quản lý (owner_unit_id)**: `DV-OPS`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Nhận diện và xác thực yêu cầu chưa đủ mạnh

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Nhân viên không xác minh kênh liên lạc
- **Sự kiện (Event)**: Yêu cầu chuyển tiền giả mạo được xử lý
- **Hậu quả (Impact)**: Tổn thất tài chính

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-006 - Xác thực hai kênh với lệnh chuyển tiền ngoại lệ]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: xác thực hai kênh giảm gian lận chuyển tiền
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-006 - Yêu cầu chuyển tiền giả mạo được xử lý trước khi bị thu hồi]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện giả mạo chuyển tiền
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
