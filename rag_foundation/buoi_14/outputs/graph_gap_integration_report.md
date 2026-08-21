# Báo cáo Kiểm tra & Đánh giá Vai trò Knowledge Graph cho Gap Analysis — Buổi 17

## 1. Khảo sát Cấu trúc & Loại Quan hệ (Relationship Types) trong Neo4j

Đã kiểm tra cấu trúc Knowledge Graph hiện có trong cơ sở dữ liệu Neo4j và tệp sơ đồ Cypher (`cypher/schema.cypher`, `cypher/demo_queries.cypher`, `scripts/load_secure_kg.py`).

### Phân loại các Loại Mối quan hệ (Relationships) Đang Tồn tại:

1. **Quan hệ Cấu trúc Nội bộ Văn bản (Structural Hierarchy)**:
   - **`:CONTAINS`**: Mối quan hệ phân cấp giữa Node Văn bản và các Node Điều khoản trực thuộc (`(v:VanBan)-[:CONTAINS]->(d:DieuKhoan)`).
   - **`:NEXT`**: Mối quan hệ nối tiếp theo thứ tự văn bản giữa các Điều khoản liền kề (`(d1:DieuKhoan)-[:NEXT]->(d2:DieuKhoan)`).
   - *Đánh giá*: Chỉ giúp truy vết cấu trúc văn bản đơn lẻ, **không giúp tìm kiếm đối chiếu sang văn bản khác**.

2. **Quan hệ Tham chiếu Pháp lý Bên ngoài (Legal Metadata Relations)**:
   - **`:SUA_DOI_BO_SUNG`**, **`:CAN_CU`**, **`:BI_THAY_THE`**: Mối quan hệ nối giữa các văn bản quy phạm pháp luật bên ngoài với nhau (`(v1:VanBan)-[:CAN_CU]->(v2:VanBan)`).
   - *Đánh giá*: Giúp theo dõi lịch sử văn bản luật bên ngoài, **không chứa các liên kết ánh xạ sang quy định nội bộ**.

3. **Quan hệ Ánh xạ giữa Yêu cầu Bên ngoài & Quy định Nội bộ**:
   - **KHÔNG TỒN TẠI (Non-existent)**: Đồ thị hiện tại chưa có các cạnh ánh xạ chuyên môn giữa điều khoản NHNN và quy định nội bộ ngân hàng (ví dụ `:IMPLEMENTS_POLICY` hay `:COMPLIES_WITH`).
   - Tuân thủ nghiêm ngặt nguyên tắc: **Không tự ý tạo edge ảo (Không bịa edge trong KG)**.

---

## 2. Đánh giá Khả năng Tích hợp vào Compliance Gap Checker

### Định vị Năng lực từng Thành phần trong Hệ thống:
- **Hybrid Search (BM25 + Dense) + Cross-Encoder Rerank**: Tìm kiếm nội dung liên quan nhất dựa trên ngữ nghĩa tự do giữa yêu cầu bên ngoài và quy định nội bộ.
- **Knowledge Graph (KG)**: Mở rộng tìm kiếm theo các quan hệ cấu trúc/lịch sử pháp lý đã biết trước.
- **Compliance Gap Checker**: Thực hiện đối chiếu so sánh bằng chứng (Evidence Comparison).

### Kết luận Đánh giá:
Do Knowledge Graph hiện tại không chứa các quan hệ nối giữa điều khoản bên ngoài và quy định nội bộ, việc mở rộng ứng viên bằng Graph không mang lại giá trị gia tăng cho bài toán Compliance Gap Matching. 

Do đó, hệ thống giữ nguyên luồng truy xuất bằng **Hybrid Search (BM25 + Dense) + Reranking** làm động cơ tìm kiếm ứng viên chuẩn xác duy nhất cho Compliance Gap Checker.

---

## 3. Tổng kết & Kết luận

GRAPH USED: NO
GRAPH NOT USED FOR GAP MATCHING

**Lý do**: Đồ thị Neo4j hiện tại chỉ chứa các quan hệ cấu trúc văn bản (`CONTAINS`, `NEXT`) và quan hệ tham chiếu văn bản luật bên ngoài (`CAN_CU`, `SUA_DOI_BO_SUNG`), thiếu các cạnh ánh xạ ngữ nghĩa trực tiếp giữa yêu cầu NHNN và điều khoản quy định nội bộ ngân hàng. Do đó, bài toán tìm kiếm ứng viên đối chiếu Gap sử dụng tối ưu cơ chế Hybrid Search + Reranking.
