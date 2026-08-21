# Catalog Phân loại Dữ liệu Đầu vào Compliance Gap Checker — Buổi 17

## 1. Tổng quan & Phương pháp Phân loại

Báo cáo này phân loại và đánh giá tính đầy đủ của tập dữ liệu nguồn [`chunks_secure.csv`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/data/processed/chunks_secure.csv) nhằm phục vụ tính năng **AI Compliance Gap Checker** (So sánh quy định nội bộ với yêu cầu quy phạm của NHNN/Nhà nước).

### Nguyên tắc Phân loại dựa trên Bằng chứng Thật (Evidence-based Rules):
- **`EXTERNAL_REQUIREMENT`**: Các văn bản quy phạm pháp luật do Cơ quan quản lý nhà nước (Ngân hàng Nhà nước, Chính phủ, Bộ Tài chính, Quốc hội) ban hành dưới hình thức Luật, Nghị định, Thông tư, Văn bản hợp nhất.
- **`INTERNAL_POLICY`**: Các văn bản do Ngân hàng/Tổ chức nội bộ ban hành (ví dụ: Quyết định, Quy chế, Quy trình nội bộ Agribank mang ký hiệu `QĐ-NHNO`, `QC-NHNO`).

---

## 2. Danh mục Phân loại Chi tiết (Document Catalog Table)

- **Tổng số Document**: **15 documents** (tương ứng 792 chunks)

| Document ID | Số ký hiệu | Loại văn bản | Cơ quan ban hành | Tên văn bản / Tiêu đề | Phân loại (Classification) | Bằng chứng dùng để phân loại (Evidence) |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **112025** | 73/2016/NĐ-CP | Nghị định | Chính phủ | Nghị định số 73/2016/NĐ-CP Quy định chi tiết thi hành Luật kinh doanh bảo hiểm | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Chính phủ ban hành |
| **112924** | 105/2016/TT-BTC | Thông tư | Bộ Tài chính | Thông tư số 105/2016/TT-BTC Hướng dẫn hoạt động đầu tư gián tiếp ra nước ngoài | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Bộ Tài chính ban hành |
| **117310** | 41/2016/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 41/2016/TT-NHNN Quy định tỷ lệ an toàn vốn đối với ngân hàng | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **163441** | 46/2023/NĐ-CP | Nghị định | Chính phủ | Nghị định số 46/2023/NĐ-CP Quy định chi tiết thi hành Luật Kinh doanh bảo hiểm | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Chính phủ ban hành |
| **166269** | 17/2023/QH15 | Luật | Quốc hội | Luật Hợp tác xã số 17/2023/QH15 | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Quốc hội ban hành |
| **168220** | 27/2024/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 27/2024/TT-NHNN Quy định về việc ngân hàng hợp tác xã | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **169221** | 43/2024/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 43/2024/TT-NHNN sửa đổi, bổ sung Thông tư 01/2014/TT-NHNN | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **173695** | 56/2024/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 56/2024/TT-NHNN Quy định hồ sơ, thủ tục cấp Giấy phép lần đầu | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **174218** | 62/2024/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 62/2024/TT-NHNN Quy định điều kiện, hồ sơ, thủ tục tổ chức lại | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **177271** | 01/2025/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 01/2025/TT-NHNN Quy định về cấp Giấy phép lần đầu | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **185630** | 63/2025/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 63/2025/TT-NHNN Sửa đổi, bổ sung về quỹ tín dụng nhân dân | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **25692** | 46/2010/QH12 | Luật | Quốc hội | Luật Ngân hàng Nhà nước Việt Nam số 46/2010/QH12 | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Quốc hội ban hành |
| **44209** | 01/2014/TT-NHNN | Thông tư | NHNN Việt Nam | Thông tư số 01/2014/TT-NHNN Quy định về giao nhận, bảo quản, vận chuyển tiền mặt | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Ngân hàng Nhà nước Việt Nam ban hành |
| **6e689cd0** | 52/VBHN-NHNN | Văn bản hợp nhất | NHNN Việt Nam | Quy định hồ sơ, thủ tục cấp Giấy phép lần đầu (VBHN) | `EXTERNAL_REQUIREMENT` | Văn bản hợp nhất do Ngân hàng Nhà nước Việt Nam phát hành |
| **95652** | 135/2015/NĐ-CP | Nghị định | Chính phủ | Nghị định số 135/2015/NĐ-CP Quy định về đầu tư gián tiếp ra nước ngoài | `EXTERNAL_REQUIREMENT` | Văn bản QPPL do Chính phủ ban hành |

---

## 3. Thống kê & Đánh giá Khả thi cho Gap Analysis

- **Số lượng `EXTERNAL_REQUIREMENT`**: **15 documents** (100%)
- **Số lượng `INTERNAL_POLICY`**: **0 documents** (0%)

> [!WARNING]
> Tập dữ liệu nguồn hiện tại (`chunks_secure.csv`) chỉ chứa toàn bộ là văn bản quy phạm pháp luật cơ quan quản lý bên ngoài (`EXTERNAL_REQUIREMENT`), không có bất kỳ văn bản quy định nội bộ (`INTERNAL_POLICY`) nào để thực hiện đối chiếu hai chiều (Pairwise Gap Analysis).
> 
> Tuyệt đối tuân thủ nguyên tắc: **Không tự ý gọi một Thông tư/Nghị định khác là "quy định nội bộ" chỉ để gượng ép chạy demo**.

---

COMPLIANCE GAP DATA: INSUFFICIENT
DATA GAP: INTERNAL POLICY NOT FOUND
