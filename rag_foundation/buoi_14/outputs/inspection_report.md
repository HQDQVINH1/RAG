# BÁO CÁO KIỂM TRA DỰ ÁN VÀ DỮ LIỆU BAN ĐẦU (INSPECTION REPORT) - BUỔI 14

**Ngày thực hiện:** 2026-08-17  
**Thực hiện bởi:** AI Coding Agent (Antigravity)  
**Phạm vi:** Buổi 14 — Hybrid Search + Reranking + Mini Knowledge Graph  

---

## 1. Cấu trúc thư mục `buoi_14/` và Code hiện có

### 1.1 Danh sách file hiện có trong `buoi_14/`
- `.md`: `buoi14.md`
- `.py`: *Chưa có file code Python nào.*
- `.csv`: *Chưa có file CSV nào.*
- `.json`: *Chưa có file JSON nào.*
- `requirements.txt`: *Chưa có.*
- `.env`: *Chưa có.*
- `.venv`: Đã khởi tạo môi trường ảo Python làm việc riêng tại `buoi_14/.venv`.

### 1.2 Kiểm tra an toàn Code hiện có
- **File thực thi:** Không có file `.py` nào trong `buoi_14/`.
- **Quét lệnh nguy hiểm (`os.remove`, `shutil.rmtree`, `open(..., "w")`, `DELETE`, `DROP`, `DETACH DELETE`):** Không phát hiện câu lệnh phá hủy hay xóa dữ liệu nào.
- **Thao tác phá dữ liệu:** Chưa thực hiện bất kỳ lệnh sửa/xóa/đè dữ liệu nào.

---

## 2. Kiểm tra trực tiếp 3 file Dữ liệu Nguồn (`../kb+hops/`)

Cả 3 file nguồn nằm tại thư mục nguồn liên kết `../kb+hops/` đều đã được đọc trực tiếp và phân tích cấu trúc schema.

### 2.1 File `metadata.csv`
- **Đường dẫn:** `../kb+hops/metadata.csv`
- **Số dòng (Rows):** 15
- **Số cột (Columns):** 17
- **Tên các cột:** `id`, `title`, `so_ky_hieu`, `ngay_ban_hanh`, `loai_van_ban`, `ngay_co_hieu_luc`, `ngay_het_hieu_luc`, `nguon_thu_thap`, `ngay_dang_cong_bao`, `nganh`, `linh_vuc`, `co_quan_ban_hanh`, `chuc_danh`, `nguoi_ky`, `pham_vi`, `thong_tin_ap_dung`, `tinh_trang_hieu_luc`
- **Encoding:** `UTF-8`
- **Dòng trùng lặp (Duplicates):** 0 dòng.
- **Giá trị khuyết (Null values):**
  - `ngay_co_hieu_luc`: 1 null
  - `ngay_het_hieu_luc`: 14 nulls
  - `nguon_thu_thap`: 5 nulls
  - `ngay_dang_cong_bao`: 11 nulls
  - `nganh`: 3 nulls
  - `linh_vuc`: 2 nulls
  - `thong_tin_ap_dung`: 15 nulls (hoàn toàn rỗng)
  - Các cột khác (`id`, `title`, `so_ky_hieu`, `loai_van_ban`, `co_quan_ban_hanh`, `chuc_danh`, `nguoi_ky`, `pham_vi`, `tinh_trang_hieu_luc`): 0 null.
- **Khóa có thể sử dụng (Primary Key):** `id` (15 giá trị duy nhất, dạng chuỗi ID văn bản). Ngoài ra `so_ky_hieu` có 15 giá trị duy nhất.
- **Trường text phù hợp retrieval:** `title` (Tên/tiêu đề văn bản quy phạm pháp luật).
- **Metadata phù hợp citation:** `id`, `so_ky_hieu`, `title`, `loai_van_ban`, `co_quan_ban_hanh`, `ngay_ban_hanh`, `tinh_trang_hieu_luc`.

### 2.2 File `content.csv`
- **Đường dẫn:** `../kb+hops/content.csv`
- **Số dòng (Rows):** 15
- **Số cột (Columns):** 2
- **Tên các cột:** `id`, `content_html`
- **Encoding:** `UTF-8`
- **Dòng trùng lặp (Duplicates):** 0 dòng.
- **Giá trị khuyết (Null values):** 0 null.
- **Khóa có thể sử dụng (Foreign Key):** `id` (15 giá trị duy nhất, khớp 1-1 với `id` trong `metadata.csv`).
- **Trường text phù hợp retrieval:** `content_html` (Toàn bộ nội dung văn bản dưới dạng HTML chứa các Điều/Khoản). Đây là nguồn dữ liệu chính để trích xuất chunk / điều khoản phục vụ BM25 & Dense Search.
- **Metadata phù hợp citation:** `id` (dùng để join với `metadata.csv` trích xuất thông tin trích dẫn).

### 2.3 File `relationships.csv`
- **Đường dẫn:** `../kb+hops/relationships.csv`
- **Số dòng (Rows):** 8
- **Số cột (Columns):** 4
- **Tên các cột:** `doc_id`, `other_doc_id`, `relationship`, `relationship_type`
- **Encoding:** `UTF-8`
- **Dòng trùng lặp (Duplicates):** 0 dòng.
- **Giá trị khuyết (Null values):** 0 null.
- **Khóa có thể sử dụng (Foreign Keys):** `doc_id` và `other_doc_id` (liên kết đến `id` của văn bản trong `metadata.csv` và `content.csv`). *Lưu ý kiểu dữ liệu: `doc_id` là string, `other_doc_id` là integer/string, cần ép kiểu đồng nhất khi xây Knowledge Graph.*
- **Trường text phù hợp retrieval:** `relationship` (Mô tả quan hệ tiếng Việt như "Sửa đổi, bổ sung", "Căn cứ", "Bị thay thế") và `relationship_type` (Mã quan hệ: `SUA_DOI_BO_SUNG`, `CAN_CU`, `BI_THAY_THE`).
- **Metadata phù hợp citation:** `relationship_type`, `relationship` (phục vụ mô hình hóa quan hệ giữa các nút văn bản trong Neo4j).

---

## 3. Kiểm tra Môi trường Python (Environment Verification)

- **Python Version:** Python 3.14.6
- **Virtual Environment:** `buoi_14/.venv` (Hoạt động tốt)
- **Kiểm tra `pandas`:** Đã cài đặt `pandas` (v3.0.5) và test import thành công.
- **Dữ liệu nguồn:** Đã bảo vệ nguyên vẹn 3 file nguồn trong `../kb+hops/`, không sửa/xóa/ghi đè.

---

## 4. Rủi ro tiềm ẩn & Biện pháp kiểm soát

1. **Khác biệt kiểu dữ liệu ID giữa các bảng:**
   - Trong `relationships.csv`, `doc_id` ở dạng chuỗi (vd `"169221"`), trong khi `other_doc_id` có thể nạp ở dạng số nguyên (vd `44209`).
   - *Biện pháp:* Đảm bảo cast toàn bộ `doc_id` và `other_doc_id` về kiểu string khi join dữ liệu hoặc tạo Node trong Neo4j.
2. **Nội dung HTML trong `content.csv`:**
   - Cột `content_html` chứa mã HTML. Nếu dùng trực tiếp cho BM25 hoặc Dense Embedding sẽ bị lẫn các thẻ HTML (`<p>`, `<table>`, `<tr>`, `<td>`, v.v.).
   - *Biện pháp:* Ở bước tiếp theo (Prompt 1), sẽ cần dùng parser (như `BeautifulSoup`) để trích xuất text sạch và chia nhỏ theo cấu trúc Điều/Khoản.

---

## 5. Kết luận Pre-Check

Môi trường, cấu trúc thư mục và dữ liệu đầu vào hoàn toàn sẵn sàng cho các bước tiếp theo.
