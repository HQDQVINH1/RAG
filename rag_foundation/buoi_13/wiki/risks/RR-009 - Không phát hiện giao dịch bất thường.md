---
id: RR-009
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-009: Không phát hiện giao dịch bất thường

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-009`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro gian lan
- **Đơn vị quản lý (owner_unit_id)**: `DV-OPS`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Luật phát hiện gian lận không được cập nhật

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Ngưỡng cảnh báo không phù hợp
- **Sự kiện (Event)**: Giao dịch nghi ngờ không bị chặn kịp thời
- **Hậu quả (Impact)**: Tổn thất tài chính và uy tín

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-009 - Hiệu chỉnh luật phát hiện giao dịch gian lận]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: hiệu chỉnh luật giảm bỏ sót giao dịch bất thường
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-009 - Giao dịch bất thường chỉ bị phát hiện sau khi khách hàng khiếu nại]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện không phát hiện bất thường
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
