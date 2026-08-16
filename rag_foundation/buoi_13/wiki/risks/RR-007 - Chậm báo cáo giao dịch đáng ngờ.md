---
id: RR-007
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-007: Chậm báo cáo giao dịch đáng ngờ

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-007`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro tuan thu
- **Đơn vị quản lý (owner_unit_id)**: `DV-COMPLIANCE`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Theo dõi cảnh báo AML không kịp thời

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Khối lượng cảnh báo vượt năng lực xử lý
- **Sự kiện (Event)**: Báo cáo giao dịch đáng ngờ nộp muộn
- **Hậu quả (Impact)**: Chế tài và rủi ro pháp lý

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-007 - Theo dõi SLA xử lý cảnh báo AML]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: theo dõi SLA giảm nguy cơ báo cáo muộn
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-007 - Báo cáo giao dịch đáng ngờ nộp quá hạn nội bộ]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện báo cáo AML muộn
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
