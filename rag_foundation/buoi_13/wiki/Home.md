# 🛡️ Wiki Risk Graph - Trang chủ Quản trị Rủi ro

Đóng vai trò là trung tâm tri thức đồ thị rủi ro (Risk Knowledge Graph Wiki), kết nối **Kiểm soát**, **Hồ sơ Rủi ro** và **Sự kiện Rủi ro thực tế**.

---

## 📊 Thống kê mạng lưới (Graph Overview)

- **Tổng số Nodes (Thực thể)**: `34`
  - 🔴 **Hồ sơ Rủi ro (RuiRo)**: `12` trang
  - 🟢 **Biện pháp Kiểm soát (KiemSoat)**: `10` trang
  - 🟡 **Sự kiện Rủi ro (SuKienRuiRo)**: `12` trang
- **Tổng số Edges (Mối quan hệ)**: `22`
  - `MITIGATES` (`KiemSoat` -> `RuiRo`): `10`
  - `OBSERVED_AS` (`RuiRo` -> `SuKienRuiRo`): `12`

---

## 📌 Danh mục Thực thể

### 1. Danh sách Hồ sơ Rủi ro (RuiRo)
- [[RR-001 - Giao dịch chuyển tiền bị hạch toán sai]] - *Giao dịch chuyển tiền bị hạch toán sai* (Mức rủi ro còn lại: Trung binh)
- [[RR-002 - Phê duyệt tín dụng vượt thẩm quyền]] - *Phê duyệt tín dụng vượt thẩm quyền* (Mức rủi ro còn lại: Trung binh)
- [[RR-003 - Giải ngân thiếu hồ sơ bảo đảm]] - *Giải ngân thiếu hồ sơ bảo đảm* (Mức rủi ro còn lại: Trung binh)
- [[RR-004 - Lộ thông tin khách hàng]] - *Lộ thông tin khách hàng* (Mức rủi ro còn lại: Trung binh)
- [[RR-005 - Gián đoạn dịch vụ ngân hàng số]] - *Gián đoạn dịch vụ ngân hàng số* (Mức rủi ro còn lại: Trung binh)
- [[RR-006 - Gian lận giả mạo yêu cầu chuyển tiền]] - *Gian lận giả mạo yêu cầu chuyển tiền* (Mức rủi ro còn lại: Trung binh)
- [[RR-007 - Chậm báo cáo giao dịch đáng ngờ]] - *Chậm báo cáo giao dịch đáng ngờ* (Mức rủi ro còn lại: Trung binh)
- [[RR-008 - Định giá tài sản bảo đảm không chính xác]] - *Định giá tài sản bảo đảm không chính xác* (Mức rủi ro còn lại: Trung binh)
- [[RR-009 - Không phát hiện giao dịch bất thường]] - *Không phát hiện giao dịch bất thường* (Mức rủi ro còn lại: Trung binh)
- [[RR-010 - Sai lệch số liệu báo cáo quản trị]] - *Sai lệch số liệu báo cáo quản trị* (Mức rủi ro còn lại: Thap)
- [[RR-011 - Nhà cung cấp công nghệ không đáp ứng cam kết]] - *Nhà cung cấp công nghệ không đáp ứng cam kết* (Mức rủi ro còn lại: Trung binh)
- [[RR-012 - Xung đột lợi ích trong mua sắm]] - *Xung đột lợi ích trong mua sắm* (Mức rủi ro còn lại: Thap)

### 2. Danh sách Biện pháp Kiểm soát (KiemSoat)
- [[KS-001 - Đối soát tự động giao dịch và sổ cái]] - *Đối soát tự động giao dịch và sổ cái* (Loại: Detective)
- [[KS-002 - Kiểm tra hạn mức phê duyệt trên hệ thống]] - *Kiểm tra hạn mức phê duyệt trên hệ thống* (Loại: Preventive)
- [[KS-003 - Checklist điều kiện giải ngân bắt buộc]] - *Checklist điều kiện giải ngân bắt buộc* (Loại: Preventive)
- [[KS-004 - Rà soát quyền truy cập định kỳ]] - *Rà soát quyền truy cập định kỳ* (Loại: Preventive)
- [[KS-005 - Kiểm thử khả năng chịu tải và chuyển đổi dự phòng]] - *Kiểm thử khả năng chịu tải và chuyển đổi dự phòng* (Loại: Preventive)
- [[KS-006 - Xác thực hai kênh với lệnh chuyển tiền ngoại lệ]] - *Xác thực hai kênh với lệnh chuyển tiền ngoại lệ* (Loại: Preventive)
- [[KS-007 - Theo dõi SLA xử lý cảnh báo AML]] - *Theo dõi SLA xử lý cảnh báo AML* (Loại: Detective)
- [[KS-008 - Rà soát độc lập định giá tài sản bảo đảm]] - *Rà soát độc lập định giá tài sản bảo đảm* (Loại: Detective)
- [[KS-009 - Hiệu chỉnh luật phát hiện giao dịch gian lận]] - *Hiệu chỉnh luật phát hiện giao dịch gian lận* (Loại: Preventive)
- [[KS-010 - Đối chiếu dữ liệu nguồn trước khi phát hành báo cáo]] - *Đối chiếu dữ liệu nguồn trước khi phát hành báo cáo* (Loại: Detective)

### 3. Danh sách Sự kiện Rủi ro (SuKienRuiRo)
- [[SK-001 - Sai lệch trạng thái giao dịch được phát hiện khi đối soát cuối ngày]] - *Sai lệch trạng thái giao dịch được phát hiện khi đối soát cuối ngày* (Mức độ: Trung binh)
- [[SK-002 - Hồ sơ tín dụng được phê duyệt vượt hạn mức của người phê duyệt]] - *Hồ sơ tín dụng được phê duyệt vượt hạn mức của người phê duyệt* (Mức độ: Cao)
- [[SK-003 - Giải ngân trước khi hoàn thiện chứng từ bảo đảm]] - *Giải ngân trước khi hoàn thiện chứng từ bảo đảm* (Mức độ: Cao)
- [[SK-004 - Tài khoản có quyền truy cập dữ liệu vượt phạm vi công việc]] - *Tài khoản có quyền truy cập dữ liệu vượt phạm vi công việc* (Mức độ: Cao)
- [[SK-005 - Dịch vụ ngân hàng số gián đoạn trong giờ cao điểm]] - *Dịch vụ ngân hàng số gián đoạn trong giờ cao điểm* (Mức độ: Cao)
- [[SK-006 - Yêu cầu chuyển tiền giả mạo được xử lý trước khi bị thu hồi]] - *Yêu cầu chuyển tiền giả mạo được xử lý trước khi bị thu hồi* (Mức độ: Cao)
- [[SK-007 - Báo cáo giao dịch đáng ngờ nộp quá hạn nội bộ]] - *Báo cáo giao dịch đáng ngờ nộp quá hạn nội bộ* (Mức độ: Trung binh)
- [[SK-008 - Rà soát phát hiện giá trị tài sản bảo đảm đã hết hiệu lực]] - *Rà soát phát hiện giá trị tài sản bảo đảm đã hết hiệu lực* (Mức độ: Cao)
- [[SK-009 - Giao dịch bất thường chỉ bị phát hiện sau khi khách hàng khiếu nại]] - *Giao dịch bất thường chỉ bị phát hiện sau khi khách hàng khiếu nại* (Mức độ: Cao)
- [[SK-010 - Báo cáo quản trị sử dụng dữ liệu nguồn chưa đối chiếu]] - *Báo cáo quản trị sử dụng dữ liệu nguồn chưa đối chiếu* (Mức độ: Trung binh)
- [[SK-011 - Nhà cung cấp chậm khôi phục dịch vụ so với SLA]] - *Nhà cung cấp chậm khôi phục dịch vụ so với SLA* (Mức độ: Trung binh)
- [[SK-012 - Kiểm tra sau mua sắm phát hiện thiếu kê khai xung đột lợi ích]] - *Kiểm tra sau mua sắm phát hiện thiếu kê khai xung đột lợi ích* (Mức độ: Trung binh)

---
*Hệ thống được tạo tự động bởi AI Coding Agent - Wiki Risk Graph Builder.*
