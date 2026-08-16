// ============================================================
// DEMO QUERIES TRỰC QUAN CHO KNOWLEDGE GRAPH MINI (BUỔI 14)
// ============================================================

// ------------------------------------------------------------
// Query A: Xem toàn bộ Sub-graph của Buổi 14
// ------------------------------------------------------------
MATCH (n {lab_session: "buoi_14"})-[r]->(m {lab_session: "buoi_14"})
RETURN n, r, m
LIMIT 100;

// ------------------------------------------------------------
// Query B: Truy vấn mối quan hệ giữa Văn bản và các Điều khoản trực thuộc
// ------------------------------------------------------------
MATCH (v:VanBan {lab_session: "buoi_14"})-[:CONTAINS]->(d:DieuKhoan {lab_session: "buoi_14"})
RETURN v.id AS Document_ID, v.title AS Ten_Van_Ban, count(d) AS So_Luong_Dieu_Khoan
ORDER BY So_Luong_Dieu_Khoan DESC;

// ------------------------------------------------------------
// Query C: Xem quan hệ pháp lý giữa các Văn bản (Sửa đổi, Căn cứ, Bị thay thế)
// ------------------------------------------------------------
MATCH (v1:VanBan {lab_session: "buoi_14"})-[r]->(v2:VanBan {lab_session: "buoi_14"})
WHERE type(r) IN ["SUA_DOI_BO_SUNG", "CAN_CU", "BI_THAY_THE"]
RETURN v1.id AS Source_Doc, v1.title AS Source_Title, type(r) AS Relationship_Type, r.relationship_desc AS Desc, v2.id AS Target_Doc, v2.title AS Target_Title;

// ------------------------------------------------------------
// Query D: Truy vấn chuỗi điều khoản kế tiếp (NEXT relationship)
// ------------------------------------------------------------
MATCH p=(d1:DieuKhoan {lab_session: "buoi_14"})-[:NEXT*1..3]->(d2:DieuKhoan {lab_session: "buoi_14"})
RETURN p
LIMIT 10;

// ------------------------------------------------------------
// Query E: Kiểm tra Node cô lập (Orphan Nodes)
// ------------------------------------------------------------
MATCH (n {lab_session: "buoi_14"})
WHERE NOT (n)-[]-()
RETURN n;
