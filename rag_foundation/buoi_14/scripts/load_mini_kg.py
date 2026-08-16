#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: load_mini_kg.py
Mục đích: Xây dựng Knowledge Graph mini cho Buổi 14 và nạp vào Neo4j Database.
Nguồn dữ liệu:
- ../kb+hops/metadata.csv
- ../kb+hops/relationships.csv
- data/processed/chunks_normalized.csv

An toàn Neo4j:
- Dùng MERGE theo ID
- Parameterized Cypher
- Mọi node/relationship đều đính kèm `lab_session = "buoi_14"`
- Tuyệt đối không xóa toàn bộ database (không dùng MATCH (n) DETACH DELETE n)
- Đọc credentials từ file .env
"""

import os
import re
import sys
import pandas as pd
from dotenv import load_dotenv

# Load .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Vinh1989")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

LAB_SESSION = "buoi_14"


def check_neo4j_connection():
    """Kiểm tra kết nối tới Neo4j database."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        driver.close()
        return True, None
    except Exception as e:
        return False, str(e)


def build_kg_report(online: bool, err_msg: str = None, stats: dict = None):
    """Tạo báo cáo xây dựng Knowledge Graph tại outputs/kg_build_report.md."""
    report_path = os.path.join(project_root, 'outputs', 'kg_build_report.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    lines = []
    lines.append("# BÁO CÁO XÂY DỰNG KNOWLEDGE GRAPH MINI (KG BUILD REPORT - PROMPT 6)\n")
    lines.append(f"**Ngày thực hiện:** 2026-08-17  ")
    lines.append(f"**Phạm vi Lab Session:** `{LAB_SESSION}`  ")
    lines.append(f"**Trạng thái Neo4j:** {'ONLINE (Đã kết nối và nạp thành công)' if online else 'OFFLINE (Chưa bật service Neo4j)'}  \n")
    lines.append("---\n")
    
    lines.append("## 1. ONTOLOGY MVP MÔ HÌNH HÓA\n")
    lines.append("```text")
    lines.append("(:VanBan {id, title, document_type, status, so_ky_hieu, lab_session})")
    lines.append("    │")
    lines.append("    ├── [:CONTAINS {lab_session}] ──► (:DieuKhoan {id, document_id, text, article, lab_session})")
    lines.append("    │                                    │")
    lines.append("    │                                    └── [:NEXT {lab_session}] ──► (:DieuKhoan)")
    lines.append("    │")
    lines.append("    └── [:SUA_DOI_BO_SUNG / :CAN_CU / :BI_THAY_THE {lab_session}] ──► (:VanBan)")
    lines.append("```\n")
    
    if online and stats:
        lines.append("## 2. THỐNG KÊ GRAPH TRONG NEO4J DATABASE\n")
        lines.append("### Node Counts theo Label:")
        lines.append("| Node Label | Số lượng Node |")
        lines.append("|:---|---:|")
        for label, count in stats.get('nodes', {}).items():
            lines.append(f"| `:{label}` | {count} |")
        lines.append("\n")
        
        lines.append("### Relationship Counts theo Type:")
        lines.append("| Relationship Type | Số lượng Cạnh |")
        lines.append("|:---|---:|")
        for rtype, count in stats.get('relationships', {}).items():
            lines.append(f"| `:{rtype}` | {count} |")
        lines.append("\n")
        
        lines.append(f"**Số Node cô lập (Orphan Nodes):** {stats.get('orphan_nodes', 0)} node  \n")
        lines.append("---\n")
        lines.append("## 3. CYPHER QUERY DEMO SẴN SÀNG\n")
        lines.append("- Các file Cypher schema và demo query đã được lưu tại:\n"
                     "  - [`buoi_14/cypher/schema.cypher`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/cypher/schema.cypher)\n"
                     "  - [`buoi_14/cypher/demo_queries.cypher`](file:///d:/OneDrive/1.%20Hoc%20tap%20nghien%20cuu/AI%20cho%20KTGS/Thuc%20hanh/RAG/rag_foundation/buoi_14/cypher/demo_queries.cypher)\n")
    else:
        lines.append("## 2. THÔNG TIN HƯỚNG DẪN KÍCH HOẠT NEO4J\n")
        lines.append(f"**Lỗi kết nối:** `{err_msg}`\n\n")
        lines.append("### Hướng dẫn khởi chạy Neo4j bằng Docker / Desktop:\n")
        lines.append("1. **Chạy bằng Docker (Khuyên dùng):**\n"
                     "   ```bash\n"
                     "   docker run -d --name neo4j-buoi14 \\\n"
                     "     -p 7474:7474 -p 7687:7687 \\\n"
                     "     -e NEO4J_AUTH=neo4j/Vinh1989 \\\n"
                     "     neo4j:latest\n"
                     "   ```\n\n"
                     "2. **Hoặc bật Neo4j Desktop / Windows Service:**\n"
                     "   - Mở **Neo4j Desktop** và nhấn **Start** database.\n"
                     "   - Đảm bảo URI `bolt://localhost:7687` và mật khẩu khớp với file `.env`.\n\n"
                     "3. **Sau khi bật Neo4j, chạy lại lệnh nạp:**\n"
                     "   ```bash\n"
                     "   .\\.venv\\Scripts\\python scripts/load_mini_kg.py\n"
                     "   ```\n")
        lines.append("> *Lưu ý: Môi trường Retrieval (BM25, Dense, Hybrid, Rerank) hoạt động hoàn toàn độc lập và không bị ảnh hưởng khi Neo4j ở trạng thái Offline.*\n")
        
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print(f"Đã lưu báo cáo Knowledge Graph tại: {report_path}")


def load_data_to_neo4j():
    """Thực hiện kết nối và nạp dữ liệu vào Neo4j."""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    metadata_csv = os.path.join(project_root, '..', 'kb+hops', 'metadata.csv')
    relationships_csv = os.path.join(project_root, '..', 'kb+hops', 'relationships.csv')
    chunks_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    
    df_meta = pd.read_csv(metadata_csv, encoding='utf-8')
    df_rel = pd.read_csv(relationships_csv, encoding='utf-8')
    df_chunks = pd.read_csv(chunks_csv, encoding='utf-8')
    
    with driver.session(database=NEO4J_DATABASE) as session:
        # 1. Tạo Constraint & Index từ schema.cypher
        print("[1/5] Tạo Constraints & Indexes...")
        session.run("CREATE CONSTRAINT constraint_vanban_id IF NOT EXISTS FOR (v:VanBan) REQUIRE v.id IS UNIQUE")
        session.run("CREATE CONSTRAINT constraint_dieukhoan_id IF NOT EXISTS FOR (d:DieuKhoan) REQUIRE d.id IS UNIQUE")
        session.run("CREATE INDEX index_vanban_lab IF NOT EXISTS FOR (v:VanBan) ON (v.lab_session)")
        session.run("CREATE INDEX index_dieukhoan_lab IF NOT EXISTS FOR (d:DieuKhoan) ON (d.lab_session)")
        
        # Dọn dẹp cạnh thử nghiệm cũ nếu có
        session.run("MATCH (n {lab_session: $lab})-[r]->(m {lab_session: $lab}) WHERE type(r) STARTS WITH '_' DELETE r", {'lab': LAB_SESSION})
        
        # 2. Nạp Node VanBan từ metadata.csv
        print(f"[2/5] Nạp {len(df_meta)} Node VanBan...")
        for _, row in df_meta.iterrows():
            session.run("""
                MERGE (v:VanBan {id: $id})
                SET v.title = $title,
                    v.so_ky_hieu = $so_ky_hieu,
                    v.document_type = $document_type,
                    v.status = $status,
                    v.effective_date = $effective_date,
                    v.lab_session = $lab_session
            """, {
                'id': str(row['id']),
                'title': str(row.get('title', '')),
                'so_ky_hieu': str(row.get('so_ky_hieu', '')),
                'document_type': str(row.get('loai_van_ban', '')),
                'status': str(row.get('tinh_trang_hieu_luc', '')),
                'effective_date': str(row.get('ngay_co_hieu_luc', '') if pd.notnull(row.get('ngay_co_hieu_luc')) else row.get('ngay_ban_hanh', '')),
                'lab_session': LAB_SESSION
            })
            
        # 3. Nạp Node DieuKhoan & Quan hệ CONTAINS từ chunks_normalized.csv
        print(f"[3/5] Nạp {len(df_chunks)} Node DieuKhoan & Quan hệ CONTAINS...")
        for _, row in df_chunks.iterrows():
            cid = str(row['chunk_id'])
            doc_id = str(row['document_id'])
            
            session.run("""
                MERGE (d:DieuKhoan {id: $cid})
                SET d.document_id = $doc_id,
                    d.text = $text,
                    d.article = $article,
                    d.chapter = $chapter,
                    d.section = $section,
                    d.lab_session = $lab_session
                WITH d
                MERGE (v:VanBan {id: $doc_id})
                MERGE (v)-[r:CONTAINS]->(d)
                SET r.lab_session = $lab_session
            """, {
                'cid': cid,
                'doc_id': doc_id,
                'text': str(row.get('text', '')),
                'article': str(row.get('article', '')),
                'chapter': str(row.get('chapter', '')),
                'section': str(row.get('section', '')),
                'lab_session': LAB_SESSION
            })
            
        # 4. Nạp Quan hệ cấu trúc NEXT giữa các DieuKhoan kế tiếp trong cùng văn bản
        print("[4/5] Nạp Quan hệ NEXT cho chuỗi Điều khoản...")
        grouped = df_chunks.groupby('document_id')
        for doc_id, group in grouped:
            chunk_ids = list(group['chunk_id'])
            for i in range(len(chunk_ids) - 1):
                session.run("""
                    MATCH (d1:DieuKhoan {id: $cid1}), (d2:DieuKhoan {id: $cid2})
                    MERGE (d1)-[r:NEXT]->(d2)
                    SET r.lab_session = $lab_session
                """, {
                    'cid1': str(chunk_ids[i]),
                    'cid2': str(chunk_ids[i+1]),
                    'lab_session': LAB_SESSION
                })
                
        # 5. Nạp Quan hệ giữa các Văn bản từ relationships.csv
        print(f"[5/5] Nạp {len(df_rel)} Quan hệ giữa các Văn bản...")
        for _, row in df_rel.iterrows():
            rel_type = str(row['relationship_type']).upper().strip()
            rel_type = re.sub(r'[^A-Z0-9_]', '_', rel_type)
            
            session.run(f"""
                MERGE (v1:VanBan {{id: $doc_id}})
                MERGE (v2:VanBan {{id: $other_doc_id}})
                MERGE (v1)-[r:{rel_type}]->(v2)
                SET r.relationship_desc = $relationship_desc,
                    r.source_file = "relationships.csv",
                    r.lab_session = $lab_session
            """, {
                'doc_id': str(row['doc_id']),
                'other_doc_id': str(row['other_doc_id']),
                'relationship_desc': str(row.get('relationship', '')),
                'lab_session': LAB_SESSION
            })
            
        # 6. Thu thập thống kê
        node_counts = session.run("""
            MATCH (n {lab_session: $lab})
            RETURN labels(n)[0] AS label, count(n) AS count
        """, {'lab': LAB_SESSION}).data()
        
        rel_counts = session.run("""
            MATCH ()-[r {lab_session: $lab}]->()
            RETURN type(r) AS rel_type, count(r) AS count
        """, {'lab': LAB_SESSION}).data()
        
        orphans = session.run("""
            MATCH (n {lab_session: $lab})
            WHERE NOT (n)-[]-()
            RETURN count(n) AS orphan_count
        """, {'lab': LAB_SESSION}).single()['orphan_count']
        
        stats = {
            'nodes': {row['label']: row['count'] for row in node_counts},
            'relationships': {row['rel_type']: row['count'] for row in rel_counts},
            'orphan_nodes': orphans
        }
        
    driver.close()
    return stats


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("============================================================")
    print("KNOWLEDGE GRAPH MINI BUILDER (PROMPT 6)")
    print("============================================================")
    print(f"Neo4j URI     : {NEO4J_URI}")
    print(f"Neo4j User    : {NEO4J_USER}")
    print(f"Lab Session   : {LAB_SESSION}\n")
    
    online, err = check_neo4j_connection()
    
    if not online:
        print("[!] Neo4j Database hiện chưa chạy hoặc từ chối kết nối.")
        print(f"Lỗi chi tiết: {err}\n")
        print("Hướng dẫn khởi chạy Neo4j:")
        print("1. Chạy Docker:")
        print("   docker run -d --name neo4j-buoi14 -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/Vinh1989 neo4j:latest")
        print("2. Hoặc bật Neo4j Desktop local service.")
        print("Báo cáo kiểm tra và hướng dẫn đã được ghi ra: outputs/kg_build_report.md\n")
        build_kg_report(online=False, err_msg=err)
    else:
        print("[+] Đã kết nối thành công tới Neo4j Database!")
        print("Tiến hành nạp ONTOLOGY MVP...")
        stats = load_data_to_neo4j()
        print("\n[+] ĐÃ NẠP THÀNH CÔNG KNOWLEDGE GRAPH MINI VÀO NEO4J!")
        print("Thống kê Graph:")
        print("  - Nodes        :", stats['nodes'])
        print("  - Relationships:", stats['relationships'])
        print("  - Orphan Nodes :", stats['orphan_nodes'])
        build_kg_report(online=True, stats=stats)


if __name__ == '__main__':
    main()
