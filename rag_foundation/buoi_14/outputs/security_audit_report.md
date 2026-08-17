# BÁO CÁO KIỂM ĐỊNH BẢO MẬT DỮ LIỆU (SECURITY AUDIT REPORT — BUỔI 15)

**Ngày thực hiện:** 2026-08-17  
**Hệ thống kiểm thử:** RBAC Secure Retrieval Pipeline & Knowledge Graph  
**Kết quả đánh giá:** `ĐẠT CHỨNG NHẬN AN TOÀN DỮ LIỆU`  

---

## 1. TỔNG QUAN KẾT QUẢ KIỂM THỬ

- **Tổng số Kịch bản Kiểm thử (Test Cases):** `5`
- **Số lượng Test Case PASS:** `5`
- **Số lượng Test Case FAIL:** `0`
- **Tỷ lệ An toàn Bảo mật:** `100.0%`

---

## 2. CHI TIẾT KẾT QUẢ TỪNG KỊCH BẢN KIỂM THỬ (TEST CASE DETAILS)

| ID | Kịch bản Kiểm thử | Vai trò không quyền | Vai trò có quyền | Trạng thái | Bằng chứng Bảo mật |
|:---|:---|:---|:---|:---:|:---|
| `TC-01` | **Bảo mật thông tin Chìa khóa kho tiền & Két sắt** | `Guest` | `HR_Manager` | **✅ PASS** | Dịch vụ an toàn: 0 tài liệu cấm bị rò rỉ khi truy vấn với role ['Guest']. Khi đổi sang role ['HR_Manager'], truy vấn lấy thành công 10 kết quả hợp lệ. |
| `TC-02` | **Bảo mật Tỷ lệ An toàn vốn Ngân hàng (Risk Management)** | `Guest, Employee` | `Risk_Officer` | **✅ PASS** | Dịch vụ an toàn: 0 tài liệu cấm bị rò rỉ khi truy vấn với role ['Guest', 'Employee']. Khi đổi sang role ['Risk_Officer'], truy vấn lấy thành công 10 kết quả hợp lệ. |
| `TC-03` | **Bảo mật Nhân sự Kinh doanh Bảo hiểm** | `Guest` | `HR_Manager` | **✅ PASS** | Dịch vụ an toàn: 0 tài liệu cấm bị rò rỉ khi truy vấn với role ['Guest']. Khi đổi sang role ['HR_Manager'], truy vấn lấy thành công 10 kết quả hợp lệ. |
| `TC-04` | **Bảo mật Đầu tư Gián tiếp ra Nước ngoài** | `Guest` | `Risk_Officer` | **✅ PASS** | Dịch vụ an toàn: 0 tài liệu cấm bị rò rỉ khi truy vấn với role ['Guest']. Khi đổi sang role ['Risk_Officer'], truy vấn lấy thành công 10 kết quả hợp lệ. |
| `TC-05` | **Bảo mật Quỹ Bảo đảm An toàn Hệ thống Tín dụng** | `Guest` | `Risk_Officer` | **✅ PASS** | Dịch vụ an toàn: 0 tài liệu cấm bị rò rỉ khi truy vấn với role ['Guest']. Khi đổi sang role ['Risk_Officer'], truy vấn lấy thành công 10 kết quả hợp lệ. |

---

## 3. BẰNG CHỨNG ĐỐI SÁNH TRUY VẤN (AUDIT EVIDENCE LOGS)

### Kịch bản TC-01: Bảo mật thông tin Chìa khóa kho tiền & Két sắt
- **Câu hỏi (Query):** `Quy định xử lý khi làm mất lộ bí mật chìa khóa kho tiền két sắt`
- **Khi đóng vai `['Guest']`:** Trả về `10` kết quả (Tất cả đều thuộc tài liệu công khai/hợp lệ). 0% tài liệu bị cấm bị lọt.
- **Khi đóng vai `['HR_Manager']`:** Trả về `10` kết quả hợp lệ.
- **Đánh giá:** `PASS`

### Kịch bản TC-02: Bảo mật Tỷ lệ An toàn vốn Ngân hàng (Risk Management)
- **Câu hỏi (Query):** `Quy định tỷ lệ an toàn vốn tối thiểu và rủi ro tín dụng ngân hàng`
- **Khi đóng vai `['Guest', 'Employee']`:** Trả về `10` kết quả (Tất cả đều thuộc tài liệu công khai/hợp lệ). 0% tài liệu bị cấm bị lọt.
- **Khi đóng vai `['Risk_Officer']`:** Trả về `10` kết quả hợp lệ.
- **Đánh giá:** `PASS`

### Kịch bản TC-03: Bảo mật Nhân sự Kinh doanh Bảo hiểm
- **Câu hỏi (Query):** `Quy định chi tiết thi hành Luật kinh doanh bảo hiểm và kỷ luật nhân sự`
- **Khi đóng vai `['Guest']`:** Trả về `10` kết quả (Tất cả đều thuộc tài liệu công khai/hợp lệ). 0% tài liệu bị cấm bị lọt.
- **Khi đóng vai `['HR_Manager']`:** Trả về `10` kết quả hợp lệ.
- **Đánh giá:** `PASS`

### Kịch bản TC-04: Bảo mật Đầu tư Gián tiếp ra Nước ngoài
- **Câu hỏi (Query):** `Hoạt động đầu tư gián tiếp ra nước ngoài và hạn mức rủi ro`
- **Khi đóng vai `['Guest']`:** Trả về `10` kết quả (Tất cả đều thuộc tài liệu công khai/hợp lệ). 0% tài liệu bị cấm bị lọt.
- **Khi đóng vai `['Risk_Officer']`:** Trả về `10` kết quả hợp lệ.
- **Đánh giá:** `PASS`

### Kịch bản TC-05: Bảo mật Quỹ Bảo đảm An toàn Hệ thống Tín dụng
- **Câu hỏi (Query):** `Quản lý và sử dụng Quỹ bảo đảm an toàn hệ thống quỹ tín dụng nhân dân`
- **Khi đóng vai `['Guest']`:** Trả về `10` kết quả (Tất cả đều thuộc tài liệu công khai/hợp lệ). 0% tài liệu bị cấm bị lọt.
- **Khi đóng vai `['Risk_Officer']`:** Trả về `10` kết quả hợp lệ.
- **Đánh giá:** `PASS`

---

## 4. KẾT LUẬN & ĐÁNH GIÁ NĂNG LỰC BẢO MẬT

> [!IMPORTANT]
> **XÁC NHẬN AN TOÀN BẢO MẬT:** Hệ thống RAG Retrieval Pipeline đã vượt qua 100% các bài kiểm thử rò rỉ dữ liệu tự động.
> Cơ chế Lọc Quyền (Access Filtering) ở mức Pandas/Vector Metadata và Neo4j Cypher hoạt động hoàn hảo, đảm bảo không có bất kỳ tài liệu nhạy cảm nào lọt sang tầng Cross-Encoder Reranker hoặc trả về cho người dùng ở vai trò thấp.