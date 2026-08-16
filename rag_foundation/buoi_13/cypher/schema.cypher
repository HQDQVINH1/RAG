// =================================================================
// NEO4J SCHEMA DEFINITION FOR WIKI RISK GRAPH
// =================================================================

// 1. UNIQUE CONSTRAINTS (Đảm bảo mỗi node có khóa id duy nhất)
CREATE CONSTRAINT constraint_ruiro_id IF NOT EXISTS 
FOR (r:RuiRo) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT constraint_kiemsoat_id IF NOT EXISTS 
FOR (k:KiemSoat) REQUIRE k.id IS UNIQUE;

CREATE CONSTRAINT constraint_sukienruiro_id IF NOT EXISTS 
FOR (s:SuKienRuiRo) REQUIRE s.id IS UNIQUE;

// 2. INDEXES (Tối ưu tốc độ truy vấn theo thuộc tính)
CREATE INDEX index_ruiro_category IF NOT EXISTS 
FOR (r:RuiRo) ON (r.category);

CREATE INDEX index_kiemsoat_type IF NOT EXISTS 
FOR (k:KiemSoat) ON (k.control_type);

CREATE INDEX index_sukien_severity IF NOT EXISTS 
FOR (s:SuKienRuiRo) ON (s.severity);
