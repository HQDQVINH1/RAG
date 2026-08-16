# BÁO CÁO XÂY DỰNG KNOWLEDGE GRAPH MINI (KG BUILD REPORT - PROMPT 6)

**Ngày thực hiện:** 2026-08-17  
**Phạm vi Lab Session:** `buoi_14`  
**Trạng thái Neo4j:** ONLINE (Đã kết nối và nạp thành công)  

---

## 1. ONTOLOGY MVP MÔ HÌNH HÓA

```text
(:VanBan {id, title, document_type, status, so_ky_hieu, lab_session})
    │
    ├── [:CONTAINS {lab_session}] ──► (:DieuKhoan {id, document_id, text, article, lab_session})
    │                                    │
    │                                    └── [:NEXT {lab_session}] ──► (:DieuKhoan)
    │
    └── [:SUA_DOI_BO_SUNG / :CAN_CU / :BI_THAY_THE {lab_session}] ──► (:VanBan)
```

## 2. THỐNG KÊ GRAPH TRONG NEO4J DATABASE

### Node Counts theo Label:
| Node Label | Số lượng Node |
|:---|---:|
| `:VanBan` | 15 |
| `:DieuKhoan` | 792 |


### Relationship Counts theo Type:
| Relationship Type | Số lượng Cạnh |
|:---|---:|
| `:CONTAINS` | 792 |
| `:THAY_THE` | 1 |
| `:CAN_CU` | 4 |
| `:SUA_DOI_BO_SUNG` | 1 |
| `:HOP_NHAT` | 1 |
| `:VAN_BAN_BO_SUNG` | 1 |
| `:NEXT` | 777 |


**Số Node cô lập (Orphan Nodes):** 0 node  

---

## 3. CYPHER QUERY DEMO SẴN SÀNG

- Các file Cypher schema và demo query đã được lưu tại:
  - [`buoi_14/cypher/schema.cypher`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/cypher/schema.cypher)
  - [`buoi_14/cypher/demo_queries.cypher`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/cypher/demo_queries.cypher)
