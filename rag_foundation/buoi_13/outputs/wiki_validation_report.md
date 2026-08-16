# 📋 Báo cáo kiểm thử Wiki Risk Graph (Wiki Validation Report)

- **Thời gian thực hiện**: 2026-08-16
- **Thư mục kiểm tra**: `wiki/`
- **File dữ liệu chuẩn hóa**: `outputs/entities.csv`, `outputs/relations.csv`

---

## 📊 1. Thống kê tổng quan (Summary Statistics)

| Tiêu chí | Kết quả | Trạng thái |
| :--- | :---: | :---: |
| **Tổng số file Markdown trong `wiki/`** | **35** | `OK` |
| **Tổng số Wikilink (`[[...]]`)** | **112** | `OK` |
| **Wikilink trỏ tới trang không tồn tại (Broken Links)** | **0** | ✓ ĐẠT |
| **Entity bị trùng ID trong `entities.csv`** | **0** | ✓ ĐẠT |
| **Trang có ID không khớp `entities.csv`** | **0** | ✓ ĐẠT |
| **Relation có Source/Target không tồn tại** | **0** | ✓ ĐẠT |
| **Rủi ro (`RuiRo`) không có Kiểm soát (`KiemSoat`)** | **2** | ⚠️ *Dữ liệu nghiệp vụ* |
| **Rủi ro (`RuiRo`) không có Sự kiện (`SuKienRuiRo`)** | **0** | ⚠️ *Dữ liệu nghiệp vụ* |
| **Trang cô lập (Orphan Pages - 0 in & 0 out)** | **0** | ✓ ĐẠT |

---

## 🔍 2. Chi tiết kết quả kiểm tra 9 mục

### 1. Tổng số file Markdown
- Số lượng: **35 file** (gồm `Home.md` + 12 risks + 10 controls + 12 events).

### 2. Tổng số Wikilink
- Số lượng: **112 wikilink** được khởi tạo.

### 3. Wikilink bị hỏng (Broken Links)
✓ **HOÀN HẢO**: `0` broken link. Tất cả wikilink đều trỏ chính xác đến các trang tồn tại trong Wiki.

### 4. Entity trùng lặp ID (Duplicate IDs)
✓ **HOÀN HẢO**: `0` entity bị trùng ID.

### 5. Trang Wiki có ID không tồn tại trong `entities.csv`
✓ **HOÀN HẢO**: `0` trang bị lệch ID với `entities.csv`.

### 6. Relation trỏ đến Source/Target không tồn tại
✓ **HOÀN HẢO**: `0` relation bị lỗi liên kết source/target.

### 7. Rủi ro (`RuiRo`) chưa có Biện pháp Kiểm soát (`KiemSoat`)
⚠️ **Phát hiện 2 Rủi ro chưa có Kiểm soát giảm thiểu (MITIGATES):**
- `RR-011`: Nhà cung cấp công nghệ không đáp ứng cam kết
- `RR-012`: Xung đột lợi ích trong mua sắm

> 💡 *Phân loại*: Đây là **LỖI DỮ LIỆU GỐC (Data Quality)** - Hai hồ sơ rủi ro này chưa được xây dựng biện pháp kiểm soát giảm thiểu trong file `relationships_seed.csv` gốc. Mã chương trình đã ghi nhận đúng thực tế dữ liệu mà không tự ý sửa hay bịa đặt quan hệ.

### 8. Rủi ro (`RuiRo`) chưa có Sự kiện Rủi ro (`SuKienRuiRo`)
✓ **HOÀN HẢO**: Tất cả 12 rủi ro đều đã có sự kiện rủi ro thực tế được ghi nhận (`OBSERVED_AS`).

### 9. Trang cô lập (Orphan Pages)
✓ **HOÀN HẢO**: `0` trang cô lập. Tất cả 34 trang entity đều được liên kết 2 chiều từ `Home.md` và giữa các thực thể liên quan.

---

## 🎯 3. Kết luận phân loại Lỗi (Classification of Findings)

1. **Lỗi Mã Chương Trình (Program Code Errors)**: **`0 LỖI`**
   - Script `build_wiki.py` hoạt động hoàn hảo: `0` broken link, `0` orphan page, `0` duplicate ID, `0` mismatch entity.
2. **Lỗi Dữ Liệu Gốc (Data Quality Findings)**: **`2 CẢNH BÁO`**
   - **`RR-011`** (*Nhà cung cấp công nghệ không đáp ứng cam kết*) chưa có `KiemSoat` giảm thiểu.
   - **`RR-012`** (*Xung đột lợi ích trong mua sắm*) chưa có `KiemSoat` giảm thiểu.
   - *Tuân thủ nguyên tắc không tự bịa quan hệ để lấp khoảng trống dữ liệu.*

---
*Báo cáo được khởi tạo tự động bởi `scripts/validate_wiki.py`.*
