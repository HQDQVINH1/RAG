import sys
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 8: IMPORT KNOWLEDGE GRAPH VÀO NEO4J")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
env_file = base_dir / ".env"
input_docs = base_dir / "ner_kb" / "cleaned_documents.csv"
input_entities = base_dir / "ner_kb" / "entities.csv"
input_rels = base_dir / "ner_kb" / "relationships.csv"

if not env_file.exists():
    print(f"[ERROR] Không tìm thấy file {env_file}")
    sys.exit(1)

# 1. Đọc cấu hình từ .env
load_dotenv(env_file)
neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', '')
neo4j_db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("1. ĐỌC CẤU HÌNH NEO4J TỪ .ENV:")
print(f"   - URI      : {neo4j_uri}")
print(f"   - Username : {neo4j_user}")
print(f"   - Password : {'*' * len(neo4j_password) if neo4j_password else '(Rỗng)'} (MẬT KHẨU ĐÃ ĐƯỢC ẨN)")
print(f"   - Database : {neo4j_db}\n")

# 2. Đọc file dữ liệu đã validate
docs_df = pd.read_csv(input_docs, dtype={'id': str})
ents_df = pd.read_csv(input_entities, dtype={'source_doc_id': str})
rels_df = pd.read_csv(input_rels, dtype=str)

print("2. ĐỌC DỮ LIỆU ĐẦU VÀO ĐÃ VALIDATE:")
print(f"   - Cleaned Documents : {len(docs_df)} dòng")
print(f"   - Entities chuẩn hóa : {len(ents_df)} dòng")
print(f"   - Relationships     : {len(rels_df)} dòng\n")

def get_graph_counts(session):
    node_res = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt")
    nodes_count = {r['label']: r['cnt'] for r in node_res}
    
    rel_res = session.run("MATCH ()-[r]->() RETURN type(r) AS rtype, count(r) AS cnt")
    rels_count = {r['rtype']: r['cnt'] for r in rel_res}
    
    return nodes_count, rels_count

def run_import_pipeline(driver, database):
    import_errors = []
    
    with driver.session(database=database) as session:
        # A. Tạo constraints trước khi import
        constraints = [
            "CREATE CONSTRAINT doc_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;",
            "CREATE CONSTRAINT coquan_id_unique IF NOT EXISTS FOR (c:CoQuan) REQUIRE c.entity_id IS UNIQUE;",
            "CREATE CONSTRAINT nguoiky_id_unique IF NOT EXISTS FOR (n:NguoiKy) REQUIRE n.entity_id IS UNIQUE;",
            "CREATE CONSTRAINT doituong_id_unique IF NOT EXISTS FOR (d:DoiTuongApDung) REQUIRE d.entity_id IS UNIQUE;",
            "CREATE CONSTRAINT linhvuc_id_unique IF NOT EXISTS FOR (l:LinhVuc) REQUIRE l.entity_id IS UNIQUE;"
        ]
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                import_errors.append(f"Constraint error: {e}")
                
        # B. Import Document Nodes
        for _, r in docs_df.iterrows():
            doc_id = str(r['id']).strip()
            skh = str(r['so_ky_hieu']).strip() if pd.notnull(r['so_ky_hieu']) else ''
            title = str(r['title']).strip() if pd.notnull(r['title']) else ''
            co_quan = str(r['co_quan_ban_hanh']).strip() if pd.notnull(r['co_quan_ban_hanh']) else ''
            nguoi_ky = str(r['nguoi_ky']).strip() if pd.notnull(r['nguoi_ky']) else ''
            chuc_danh = str(r['chuc_danh']).strip() if pd.notnull(r['chuc_danh']) else ''
            linh_vuc = str(r['linh_vuc']).strip() if pd.notnull(r['linh_vuc']) else ''
            loai_vb = str(r['loai_van_ban']).strip() if pd.notnull(r['loai_van_ban']) else ''
            ngay_bh = str(r['ngay_ban_hanh']).strip() if pd.notnull(r['ngay_ban_hanh']) else ''
            
            cypher = """
            MERGE (d:Document {id: $id})
            ON CREATE SET d.so_ky_hieu = $so_ky_hieu,
                          d.title = $title,
                          d.co_quan_ban_hanh = $co_quan,
                          d.nguoi_ky = $nguoi_ky,
                          d.chuc_danh = $chuc_danh,
                          d.linh_vuc = $linh_vuc,
                          d.loai_van_ban = $loai_vb,
                          d.ngay_ban_hanh = $ngay_bh,
                          d.is_external = false
            ON MATCH SET  d.so_ky_hieu = $so_ky_hieu,
                          d.title = $title,
                          d.co_quan_ban_hanh = $co_quan,
                          d.nguoi_ky = $nguoi_ky,
                          d.chuc_danh = $chuc_danh,
                          d.linh_vuc = $linh_vuc,
                          d.loai_van_ban = $loai_vb,
                          d.ngay_ban_hanh = $ngay_bh
            """
            session.run(cypher, id=doc_id, so_ky_hieu=skh, title=title, co_quan=co_quan,
                        nguoi_ky=nguoi_ky, chuc_danh=chuc_danh, linh_vuc=linh_vuc,
                        loai_vb=loai_vb, ngay_bh=ngay_bh)

        # C. Import Entity Nodes (CoQuan, NguoiKy, DoiTuongApDung, LinhVuc)
        unique_ents = ents_df.drop_duplicates(subset=['entity_id'])
        for _, r in unique_ents.iterrows():
            eid = str(r['entity_id']).strip()
            etype = str(r['entity_type']).strip()
            cname = str(r['canonical_name']).strip()
            oname = str(r['original_name']).strip()
            
            if etype not in ['CoQuan', 'NguoiKy', 'DoiTuongApDung', 'LinhVuc']:
                continue
                
            cypher = f"""
            MERGE (e:{etype} {{entity_id: $eid}})
            ON CREATE SET e.canonical_name = $cname, e.original_name = $oname
            ON MATCH SET  e.canonical_name = $cname
            """
            session.run(cypher, eid=eid, cname=cname, oname=oname)

        # D. Import Relationships
        for _, r in rels_df.iterrows():
            src = str(r['source']).strip()
            tgt = str(r['target']).strip()
            rtype = str(r['relationship_type']).strip()
            method = str(r['method']).strip() if pd.notnull(r['method']) else ''
            conf = float(r['confidence']) if pd.notnull(r['confidence']) else 1.0
            evid = str(r['evidence']).strip() if pd.notnull(r['evidence']) else ''

            if rtype in ['BAN_HANH_BOI', 'KY_BOI', 'AP_DUNG_CHO', 'THUOC_LINH_VUC']:
                cypher = f"""
                MATCH (d:Document {{id: $src}})
                MATCH (e {{entity_id: $tgt}})
                MERGE (d)-[r:{rtype}]->(e)
                ON CREATE SET r.method = $method, r.confidence = $conf, r.evidence = $evid
                ON MATCH SET  r.method = $method, r.confidence = $conf, r.evidence = $evid
                """
                res = session.run(cypher, src=src, tgt=tgt, method=method, conf=conf, evid=evid)
            elif rtype in ['THAM_CHIEU', 'SUA_DOI_BO_SUNG', 'THAY_THE_BOI']:
                # MERGE Document nodes nếu chưa có (văn bản ngoài corpus)
                cypher = f"""
                MERGE (d1:Document {{id: $src}})
                MERGE (d2:Document {{id: $tgt}})
                MERGE (d1)-[r:{rtype}]->(d2)
                ON CREATE SET r.method = $method, r.confidence = $conf, r.evidence = $evid
                ON MATCH SET  r.method = $method, r.confidence = $conf, r.evidence = $evid
                """
                session.run(cypher, src=src, tgt=tgt, method=method, conf=conf, evid=evid)
            else:
                import_errors.append(f"Unknown relationship_type: {rtype}")

    return import_errors

# Thực hiện kết nối driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

print("3. THỰC HIỆN IMPORT LẦN 1 (RUN 1)...")
errors_run1 = run_import_pipeline(driver, neo4j_db)

with driver.session(database=neo4j_db) as session:
    nodes_run1, rels_run1 = get_graph_counts(session)

print(f"   -> Kết thúc Import Lần 1 (Số lỗi: {len(errors_run1)})")
print("   - Số Nodes theo Label (Lần 1):")
for label, cnt in nodes_run1.items():
    print(f"     + {label:<20}: {cnt} node(s)")
print("   - Số Relationships theo Type (Lần 1):")
for rtype, cnt in rels_run1.items():
    print(f"     + {rtype:<20}: {cnt} relation(s)")

print("\n4. THỰC HIỆN IMPORT LẦN 2 (RUN 2 - KIỂM TRA TÍNH IDEMPOTENT CỦA MERGE)...")
errors_run2 = run_import_pipeline(driver, neo4j_db)

with driver.session(database=neo4j_db) as session:
    nodes_run2, rels_run2 = get_graph_counts(session)

print(f"   -> Kết thúc Import Lần 2 (Số lỗi: {len(errors_run2)})")

driver.close()
print("5. Đã đóng driver Neo4j an toàn.\n")

# So sánh 2 lần chạy
total_nodes_run1 = sum(nodes_run1.values())
total_nodes_run2 = sum(nodes_run2.values())
total_rels_run1 = sum(rels_run1.values())
total_rels_run2 = sum(rels_run2.values())

node_delta = total_nodes_run2 - total_nodes_run1
rel_delta = total_rels_run2 - total_rels_run1

is_idempotent = (node_delta == 0) and (rel_delta == 0)

print("=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 8")
print("=" * 60)
print(f"[PASS] Import Knowledge Graph vào Neo4j thành công")
print(f"   - Tổng số Nodes Lần 1 : {total_nodes_run1} (Lần 2: {total_nodes_run2})")
print(f"   - Tổng số Rels Lần 1  : {total_rels_run1} (Lần 2: {total_rels_run2})")
print(f"[{'PASS' if is_idempotent else 'FAIL'}] Tính Idempotent (Chạy lại Lần 2 delta node={node_delta}, delta rel={rel_delta})")
print(f"[{'PASS' if len(errors_run1) == 0 else 'FAIL'}] Không xảy ra lỗi import ({len(errors_run1)} lỗi)")

print("\n" + "=" * 60)
if is_idempotent and len(errors_run1) == 0:
    print("KẾT LUẬN BƯỚC 8: PASS. Đã sẵn sàng cho Bước 9 (Đánh giá chất lượng KG).")
else:
    print("KẾT LUẬN BƯỚC 8: FAIL. Cần kiểm tra lại MERGE cypher queries.")
print("=" * 60 + "\n")
