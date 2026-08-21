# Use Case 1 Demo Report — AI Tra cứu Quy định Nội bộ có Phân quyền (RBAC)

## 1. Kiến trúc & Quy trình Thực thi (Pipeline Design)

Use Case 1 thực thi quy trình tra cứu chính sách nội bộ an toàn tuân thủ các nguyên tắc:
1. **Lọc Phân quyền An toàn (RBAC Pre-filtering)**: Sử dụng `SecureRetrievalAdapter` để bảo đảm tài liệu không có quyền bị loại bỏ hoàn toàn trước khi tạo ngữ cảnh cho LLM.
2. **Strict LLM Context Prompting**: Ép buộc LLM chỉ trả lời dựa vào thông tin có trong ngữ cảnh đã qua lọc quyền, tuyệt đối không dùng kiến thức bên ngoài hay tự bịa trích dẫn.
3. **Fallback An toàn**: Nếu ngữ cảnh không đủ hoặc người dùng không có quyền, hệ thống tự động trả lời câu thông báo chuẩn:
   > *"Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."*
4. **Tự động Ghi vết (Audit Logging)**: Mọi yêu cầu (kể cả yêu cầu bị từ chối) đều được ghi vết vào `outputs/audit_log.jsonl` kèm theo `request_id`, `user_role`, `citation_ids` và `status`.

---

## 2. Kết quả Chạy Demo 3 Use Cases Chi tiết

### Use Case 1.1: Truy vấn Hợp lệ có Quyền Cấp cao (Authorized Query — Risk Officer)
- **Mã yêu cầu (Request ID)**: `req-cae1a5c2`
- **Người dùng / Vai trò**: `usr_risk_01` (`["Risk_Officer"]`)
- **Câu hỏi**: *"Tỷ lệ an toàn vốn tối thiểu được quy định là bao nhiêu và cách xác định tài sản tính theo rủi ro tín dụng?"*
- **Trạng thái**: **`SUCCESS`**
- **Câu trả lời sinh bởi LLM**:
  > Tỷ lệ an toàn vốn tối thiểu được quy định như sau:
  > - Ngân hàng không có công ty con, chi nhánh ngân hàng nước ngoài phải duy trì tỷ lệ an toàn vốn tối thiểu 8% `[41/2016/TT-NHNN | Điều 6. Tỷ lệ an toàn vốn | 117310_c007]`.
  > - Ngân hàng có công ty con phải duy trì tỷ lệ an toàn vốn xác định trên cơ sở báo cáo tài chính của ngân hàng tối thiểu 8% và tỷ lệ an toàn vốn hợp nhất tối thiểu 8% `[41/2016/TT-NHNN | Điều 6. Tỷ lệ an toàn vốn | 117310_c007]`.
  > - Ngân hàng Nhà nước có thể yêu cầu duy trì tỷ lệ an toàn vốn cao hơn tùy tình hình an toàn hoạt động `[41/2016/TT-NHNN | Điều 6. Tỷ lệ an toàn vốn | 117310_c007]`.
- **Trích dẫn (Citations)**:
  - `[41/2016/TT-NHNN | Điều 6. Tỷ lệ an toàn vốn | 117310_c007]`
  - `[41/2016/TT-NHNN | Điều 7. Vốn tự có | 117310_c008]`
  - `[41/2016/TT-NHNN | Điều 3. Cơ cấu tổ chức và kiểm toán nội bộ... | 117310_c004]`
- **Mã Chunk / Document**: Chunk `117310_c007`, Document `117310`

---

### Use Case 1.2: Truy vấn Bị từ chối do Không đủ Quyền (Unauthorized Query — Guest)
- **Mã yêu cầu (Request ID)**: `req-bbf67be7`
- **Người dùng / Vai trò**: `usr_guest_99` (`["Guest"]`)
- **Câu hỏi**: *"Chi tiết quy định và quy trình xác định trạng thái rủi ro để tính vốn yêu cầu cho rủi ro thị trường theo Điều 17 Thông tư 41?"*
- **Trạng thái**: **`DENIED / INSUFFICIENT_CONTEXT`**
- **Câu trả lời sinh bởi LLM**:
  > **"Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."**
- **Trích dẫn (Citations)**: `[]` (Không có bất kỳ trích dẫn nào được trả về).
- **Mã Chunk / Document**: `[]` (Không rò rỉ bất kỳ thông tin nhạy cảm nào).

---

### Use Case 1.3: Truy vấn Nội bộ Thường (Normal Internal Query — Employee)
- **Mã yêu cầu (Request ID)**: `req-cbf9f385`
- **Người dùng / Vai trò**: `usr_staff_05` (`["Employee"]`)
- **Câu hỏi**: *"Chính sách ưu đãi về thuế, phí và lệ phí đối với hợp tác xã theo quy định tại Luật 17/2023/QH15?"*
- **Trạng thái**: **`SUCCESS`**
- **Câu trả lời sinh bởi LLM**:
  > Theo Luật Hợp tác xã số 17/2023/QH15, các chính sách ưu đãi về thuế, phí và lệ phí bao gồm:
  > 1. Được hưởng mức ưu đãi thuế, phí và lệ phí cao nhất trong cùng lĩnh vực, ngành, nghề và địa bàn `[17/2023/QH15 | Điều 22 | 166269_c023]`.
  > 2. Không thu lệ phí đăng ký đối với tổ hợp tác, không thu phí công bố nội dung đăng ký `[17/2023/QH15 | Điều 22 | 166269_c023]`.
  > 3. Miễn, giảm thuế TNDN đối với thu nhập từ giao dịch nội bộ và các hoạt động liên kết chuỗi giá trị `[17/2023/QH15 | Điều 22 | 166269_c023]`.
  > 4. Miễn thuế TNDN đối với phần thu nhập hình thành quỹ chung không chia và tài sản chung không chia `[17/2023/QH15 | Điều 22 | 166269_c023]`.
- **Trích dẫn (Citations)**:
  - `[17/2023/QH15 | Điều 22. Chính sách thuế, phí và lệ phí | 166269_c023]`
- **Mã Chunk / Document**: Chunk `166269_c023`, Document `166269`

---

## 3. Tổng kết Đánh giá Tiêu chuẩn

| Tiêu chuẩn Kiểm tra | Trạng thái | Diễn giải Chi tiết |
| :--- | :---: | :--- |
| **CITATION** | **PASS** | Câu trả lời thành công luôn kèm trích dẫn chính xác; request bị từ chối trả trích dẫn rỗng |
| **RBAC** | **PASS** | Đã loại bỏ tài liệu không có quyền trước khi vào LLM; `Guest` bị chặn 100% không rò rỉ context |
| **AUDIT** | **PASS** | Tất cả 3 request (kể cả request DENIED) được ghi vết đầy đủ vào `audit_log.jsonl` kèm ISO timestamp |

---

CITATION: PASS
RBAC: PASS
AUDIT: PASS
