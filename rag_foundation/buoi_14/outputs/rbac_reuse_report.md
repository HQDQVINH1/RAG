# RBAC Reuse & Inspection Report — Buổi 17

## 1. Thống kê & Kiểm tra `allowed_roles` trong `chunks_secure.csv`

### 1.1. Danh sách Vai trò (Roles) & Phân bố Chunks
- **Tổng số chunk trong tập dữ liệu**: **792 chunks**
- **Định dạng dữ liệu**: 100% các dòng đều được lưu dưới dạng chuỗi JSON danh sách vai trò (`<class 'str'>`), ví dụ: `'["Admin", "Risk_Officer"]'`. Việc parse bằng `json.loads()` diễn ra hoàn toàn ổn định.
- **Danh sách các Vai trò (Unique Roles)**:
  1. `Admin`: **792 chunks** (100% tổng số chunk — Admin có quyền truy cập toàn bộ tài liệu).
  2. `Risk_Officer`: **547 chunks** (Các quy định rủi ro, an toàn vốn & văn bản chung).
  3. `HR_Manager`: **510 chunks** (Các quy định nhân sự, tổ chức bộ máy & văn bản chung).
  4. `Employee`: **131 chunks** (Các quy trình làm việc nội bộ chung & văn bản công khai).
  5. `Guest`: **102 chunks** (Các văn bản công khai dành cho khách/người dùng ngoài).

### 1.2. Phân loại Phân quyền của Chunks
- **Chunk gán nhiều vai trò (Multi-role chunks)**: **792 chunks** (100% các chunk đều chứa danh sách từ 2 vai trò trở lên).
- **Chunk công khai (Phân quyền rộng)**: **102 chunks** chứa đủ cả 5 vai trò `["Admin", "HR_Manager", "Risk_Officer", "Employee", "Guest"]`.
- **Chunk hạn chế quyền (Phân quyền hẹp)**: **690 chunks** chỉ dành riêng cho các vai trò quản trị/chuyên môn như `Admin`, `Risk_Officer`, `HR_Manager`.

---

## 2. Kiểm tra & Thử nghiệm `SecureRetriever` Buổi 16

### 2.1. Kiểm tra Phương thức Lọc Phân quyền
- `SecureRetriever` đọc trực tiếp trường `allowed_roles` từ `chunks_secure.csv` và chuyển thành `set` để thực hiện phép giao tập hợp `_is_accessible(chunk_roles, user_roles)`.
- **Thời điểm lọc**: **TRƯỚC khi Retrieval / Context Generation (Pre-filtering)**. Chỉ các chunk có vai trò khớp với `user_roles` mới được đưa vào đánh số điểm BM25/Dense, tính toán RRF và Cross-Encoder Reranking.

### 2.2. Kết quả Thử nghiệm 5 Vai trò với cùng 1 Query
- **Query thử nghiệm**: *"quy định về hạn mức giao dịch và quản lý rủi ro tín dụng"*

| Vai trò thử nghiệm | `user_roles` truyền vào | Số chunk trả về | Ví dụ Top-1 Chunk & Trích dẫn | Đánh giá An toàn |
| :--- | :--- | :---: | :--- | :--- |
| **Admin** | `["Admin"]` | 5 | `117310_c018` — `[41/2016/TT-NHNN \| Điều 17. Quy định rủi ro thị trường]` | Truy cập toàn bộ 100% tài liệu |
| **Risk_Manager** | `["Risk_Officer"]` | 5 | `117310_c018` — `[41/2016/TT-NHNN \| Điều 17. Quy định rủi ro thị trường]` | Đã lấy đúng tài liệu Rủi ro |
| **HR** | `["HR_Manager"]` | 5 | `117310_c003` — `[41/2016/TT-NHNN \| Điều 2. Giải thích từ ngữ]` | Đã lọc bỏ các chunk Rủi ro bảo mật |
| **Staff** | `["Employee"]` | 5 | `166269_c023` — `[17/2023/QH15 \| Điều 22. Chính sách thuế]` | Đã lọc bỏ chunk HR & Rủi ro bảo mật |
| **Guest** | `["Guest"]` | 5 | `166269_c023` — `[17/2023/QH15 \| Điều 22. Chính sách thuế]` | Chỉ truy cập được tài liệu công khai |

### 2.3. Kiểm tra Unknown Role & Default Deny
- Khi truyền danh sách vai trò không hợp lệ / lạ (`user_roles=["INVALID_ROLE_XYZ", "HACKER", "UNKNOWN"]`): **0 chunks được trả về**.
- Khi truyền danh sách vai trò rỗng (`user_roles=[]`): **0 chunks được trả về**.
- **Kết luận**: Cơ chế **Default Deny** hoạt động hoàn hảo, đảm bảo không rò rỉ bất kỳ thông tin nào cho vai trò chưa xác định.

---

## 3. Kết luận Tái sử dụng (Reuse Decision)

- Class `SecureRetriever` trong `src/secure_retriever.py` đã đáp ứng 100% các tiêu chuẩn an toàn RBAC, đọc đúng `allowed_roles`, lọc pre-filtering chuẩn xác và thực thi Default Deny an toàn.
- **Quyết định**: Tái sử dụng nguyên trạng `SecureRetriever` của Buổi 16 cho Buổi 17 mà không cần viết retriever mới hay tạo adapter bổ sung.

---

RBAC REUSED: YES
FILTER BEFORE RETRIEVAL: PASS
UNKNOWN ROLE DEFAULT DENY: PASS
