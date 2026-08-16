---
id: RR-010
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# RR-010: Sai lệch số liệu báo cáo quản trị

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `RR-010`
- **Loại Entity**: `RuiRo`
- **Danh mục (Category)**: Rui ro bao cao
- **Đơn vị quản lý (owner_unit_id)**: `DV-FINANCE`
- **Mức rủi ro tiềm tàng (Inherent Level)**: Trung binh
- **Mức rủi ro còn lại (Residual Level)**: Thap

## 2. Mô tả chi tiết
Dữ liệu nguồn không được đối chiếu

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: Thay đổi dữ liệu không có kiểm soát
- **Sự kiện (Event)**: Báo cáo quản trị có số liệu sai
- **Hậu quả (Impact)**: Quyết định quản trị sai lệch

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
- [[KS-010 - Đối chiếu dữ liệu nguồn trước khi phát hành báo cáo]]
  - **Loại quan hệ (relationship_type)**: `MITIGATES`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: đối chiếu nguồn giảm sai lệch báo cáo
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---

## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)
- [[SK-010 - Báo cáo quản trị sử dụng dữ liệu nguồn chưa đối chiếu]]
  - **Loại quan hệ (relationship_type)**: `OBSERVED_AS`
  - **Bằng chứng (evidence_quote)**: Dữ liệu mô phỏng: sự kiện sai lệch báo cáo
  - **Trạng thái xác minh**: `VERIFIED`
  - **Độ tin cậy (confidence)**: `1.0`

---
*Trở về [[Home|Trang chủ Wiki Risk Graph]]*
