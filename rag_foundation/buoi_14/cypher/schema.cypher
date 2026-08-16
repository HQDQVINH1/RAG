// ============================================================
// SCHEMA & CONSTRAINTS CHO KNOWLEDGE GRAPH MINI (BUỔI 14)
// ============================================================

// 1. Ràng buộc duy nhất (Unique Constraints) cho Node VanBan
CREATE CONSTRAINT constraint_vanban_id IF NOT EXISTS 
FOR (v:VanBan) REQUIRE v.id IS UNIQUE;

// 2. Ràng buộc duy nhất (Unique Constraints) cho Node DieuKhoan
CREATE CONSTRAINT constraint_dieukhoan_id IF NOT EXISTS 
FOR (d:DieuKhoan) REQUIRE d.id IS UNIQUE;

// 3. Chỉ mục (Index) theo lab_session để truy vấn và dọn dẹp dữ liệu an toàn
CREATE INDEX index_vanban_lab IF NOT EXISTS 
FOR (v:VanBan) ON (v.lab_session);

CREATE INDEX index_dieukhoan_lab IF NOT EXISTS 
FOR (d:DieuKhoan) ON (d.lab_session);
