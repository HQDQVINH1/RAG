---
id: RR-005
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-005: Gián đoạn dịch vụ ngân hàng số

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-005`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro cong nghe thong tin
- **Đơn vị quản lý (owner_unit_id)**: `DV-IT`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Cao
- **Mức rủi ro còn lại (Residual Level)**: Trung binh

## 2. Mô tả chi tiết
Hệ thống thanh toán trực tuyến không sẵn sàng

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Kế hoạch năng lực và dự phòng chưa đầy đủ
- **Sự kiện (Event)**: Dịch vụ ngân hàng số bị gián đoạn
- **Hậu quả (Impact)**: Mất doanh thu và khiếu nại khách hàng

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-005 - Kiểm thử khả năng chịu tải và chuyển đổi dự phòng]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: kiểm thử dự phòng giảm gián đoạn dịch vụ
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-005 - Dịch vụ ngân hàng số gián đoạn trong giờ cao điểm]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện gián đoạn dịch vụ
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
