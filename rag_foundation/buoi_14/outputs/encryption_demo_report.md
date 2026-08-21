# Báo cáo Demo Mã hóa Cục bộ (Local Encryption Demo Report) — Buổi 17

## 1. Mục tiêu & Phạm vi Thực hành

Báo cáo này trình bày kết quả thử nghiệm giải pháp mã hóa dữ liệu lưu trữ cục bộ (Data-at-Rest Encryption) cho tệp nhật ký truy vết Audit Trail (`audit_log.jsonl`).

> [!NOTE]
> Mục tiêu bài thực hành là minh họa nguyên lý bảo vệ dữ liệu ở trạng thái lưu trữ (Data-at-Rest) ở cấp độ giáo trình/demo, hoàn toàn **không tuyên bố sẵn sàng cho môi trường sản xuất (Production-Ready)**.

---

## 2. Kết quả Thực hiện & Thử nghiệm

### 2.1. Cấu hình Bảo mật Khóa (Key Management)
- **Không hard-code khóa**: Khóa mã hóa đối xứng Fernet (AES-128-CBC + HMAC-SHA256) được sinh động và nạp từ tệp `secret.key`.
- **Cấu hình Git Ignore**: Đã thêm pattern `*.key` vào tệp [`.gitignore`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/.gitignore) để đảm bảo tệp khóa bảo mật không bị commit lên kho mã nguồn.

### 2.2. Tiến trình Mã hóa & Giải mã
- **Tệp nguồn (Source Audit Log)**: `outputs/audit_log.jsonl` (Kích thước: 2,338 bytes)
- **Tệp đã mã hóa (Encrypted File)**: `outputs/audit_log.jsonl.enc` (Kích thước: 3,212 bytes)
- **Tệp giải mã (Decrypted File)**: `outputs/audit_log_decrypted.jsonl` (Kích thước: 2,338 bytes)
- **Dữ liệu nguồn**: 100% không bị thay đổi hay chỉnh sửa.

### 2.3. Kết quả So khớp (Byte-for-Byte Verification)
- Nội dung tệp giải mã `audit_log_decrypted.jsonl` trùng khớp **100% từng byte** so với tệp audit log ban đầu.

---

## 3. Lưu ý Quan trọng đối với Hệ thống Thực tế (Production Architecture)

Trong các hệ thống ngân hàng và kiểm soát tuân thủ thực tế (Enterprise/Production Systems), mã hóa cục bộ đơn giản bằng Fernet chưa đủ điều kiện vận hành. Một kiến trúc chuẩn Production đòi hỏi tích hợp các cơ chế bảo mật toàn diện:

1. **Kiểm soát Khóa Tập trung (KMS / HSM)**:
   - Khóa không được lưu dưới dạng file phẳng (`.key`) trên server ứng dụng.
   - Phải nạp và quản lý qua dịch vụ KMS chuyên dụng (AWS KMS, Azure Key Vault, HashiCorp Vault) hoặc thiết bị phần cứng bảo mật HSM (Hardware Security Module).
2. **Mã hóa Đường truyền (TLS / mTLS)**:
   - Toàn bộ dữ liệu di chuyển giữa Client, Streamlit Web App, RAG Pipeline và Neo4j / Vector Store phải được mã hóa đường truyền (Data-in-Transit) bằng TLS 1.3 / mTLS.
3. **Xoay vòng Khóa Tự động (Key Rotation)**:
   - Khóa mã hóa phải được tự động xoay vòng định kỳ (ví dụ 90 ngày) và hỗ trợ quản lý nhiều phiên bản khóa (Envelope Encryption / Master Key - Data Key).
4. **Sao lưu & Phục hồi An toàn (Encrypted Backups)**:
   - Các bản sao lưu dữ liệu và audit log phải được mã hóa trước khi đẩy lên bộ nhớ phụ hoặc Tape/Cloud Storage, kết hợp chính sách WORM (Write Once Read Many).
5. **Kiểm soát Truy cập & Phân quyền IAM (Identity & Access Management)**:
   - Áp dụng nguyên tắc quyền tối thiểu (Least Privilege) cho dịch vụ đọc/ghi khóa mã hóa và file audit.

---

ENCRYPT: PASS
DECRYPT MATCH: PASS
PRODUCTION READY: NO
