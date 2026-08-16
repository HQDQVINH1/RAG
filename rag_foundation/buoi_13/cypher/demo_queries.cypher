// =================================================================
// DEMO CYPHER QUERIES FOR WIKI RISK GRAPH
// =================================================================

// -----------------------------------------------------------------
// Query A: Xem toàn bộ Graph (View full graph)
// -----------------------------------------------------------------
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100;


// -----------------------------------------------------------------
// Query B: Tìm tất cả kiểm soát (KiemSoat) giảm thiểu một rủi ro (RuiRo)
// Ví dụ: Tra cứu kiểm soát cho rủi ro RR-001
// -----------------------------------------------------------------
MATCH (k:KiemSoat)-[r:MITIGATES]->(rr:RuiRo {id: 'RR-001'})
RETURN k.id AS ControlID, 
       k.name AS ControlName, 
       k.effectiveness AS Effectiveness,
       r.evidence_quote AS Evidence, 
       rr.id AS RiskID, 
       rr.name AS RiskName;


// -----------------------------------------------------------------
// Query C: Tìm tất cả sự kiện (SuKienRuiRo) phát sinh từ một rủi ro (RuiRo)
// Ví dụ: Tra cứu sự kiện thực tế của rủi ro RR-001
// -----------------------------------------------------------------
MATCH (rr:RuiRo {id: 'RR-001'})-[r:OBSERVED_AS]->(sk:SuKienRuiRo)
RETURN rr.id AS RiskID, 
       rr.name AS RiskName, 
       sk.id AS EventID, 
       sk.description AS EventDescription, 
       sk.loss_amount_vnd AS FinancialLossVND, 
       sk.occurred_at AS OccurredDate;


// -----------------------------------------------------------------
// Query D: Tìm đường truyền đầy đủ: KiemSoat -> RuiRo -> SuKienRuiRo
// (Duyệt toàn bộ chuỗi từ biện pháp ngăn ngừa đến tổn thất thực tế)
// -----------------------------------------------------------------
MATCH path = (k:KiemSoat)-[:MITIGATES]->(rr:RuiRo)-[:OBSERVED_AS]->(sk:SuKienRuiRo)
RETURN path
LIMIT 20;


// -----------------------------------------------------------------
// Query E: Tìm các rủi ro chưa có bất kỳ kiểm soát nào giảm thiểu (Unmitigated Risks)
// -----------------------------------------------------------------
MATCH (rr:RuiRo)
WHERE NOT (:KiemSoat)-[:MITIGATES]->(rr)
RETURN rr.id AS UnmitigatedRiskID, 
       rr.name AS RiskName, 
       rr.category AS Category, 
       rr.residual_level AS ResidualRiskLevel,
       rr.owner_unit_id AS OwnerUnit;


// -----------------------------------------------------------------
// Query F: Tìm tất cả các mối quan hệ chưa được xác minh (verification_status <> 'VERIFIED')
// -----------------------------------------------------------------
MATCH (a)-[r]->(b)
WHERE r.verification_status <> 'VERIFIED' OR r.verification_status IS NULL
RETURN a.id AS SourceID, 
       type(r) AS RelationshipType, 
       b.id AS TargetID, 
       r.verification_status AS VerificationStatus,
       r.evidence_quote AS EvidenceQuote;
