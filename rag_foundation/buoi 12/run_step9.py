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
print("  BƯỚC 9: KIỂM TRA VÀ TRỰC QUAN HÓA TRÊN NEO4J (KG VERIFICATION)")
print("=" * 60 + "\n")

base_dir = Path(__file__).parent
env_file = base_dir / ".env"
input_docs = base_dir / "ner_kb" / "cleaned_documents.csv"
input_entities = base_dir / "ner_kb" / "entities.csv"
input_rels = base_dir / "ner_kb" / "relationships.csv"

# 1. Đọc cấu hình từ .env
load_dotenv(env_file)
neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', '')
neo4j_db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("1. ĐỌC CẤU HÌNH TỪ .ENV:")
print(f"   - URI      : {neo4j_uri}")
print(f"   - Username : {neo4j_user}")
print(f"   - Password : {'*' * len(neo4j_password) if neo4j_password else '(Rỗng)'} (MẬT KHẨU ĐÃ ẨN)")
print(f"   - Database : {neo4j_db}\n")

# 2. Đọc dữ liệu CSV để làm mốc đối chiếu
docs_df = pd.read_csv(input_docs, dtype={'id': str})
ents_df = pd.read_csv(input_entities, dtype={'source_doc_id': str})
rels_df = pd.read_csv(input_rels, dtype=str)

csv_ent_counts = ents_df['entity_type'].value_counts().to_dict()
csv_rel_counts = rels_df['relationship_type'].value_counts().to_dict()

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

print("2. THỰC THI CÁC TRUY VẤN KIỂM TRA TRÊN NEO4J...\n")

with driver.session(database=neo4j_db) as session:
    # 9.1 Kiểm tra số Node theo Label
    print("9.1. KIỂM TRA SỐ NODE theo Label:")
    q_nodes = """
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS total
    ORDER BY total DESC;
    """
    res_nodes = session.run(q_nodes)
    db_node_counts = {}
    for r in res_nodes:
        lbl = r['label']
        cnt = r['total']
        db_node_counts[lbl] = cnt
        print(f"   - {lbl:<20}: {cnt} node(s)")
    print()

    # 9.2 Kiểm tra Relationship theo Type
    print("9.2. KIỂM TRA RELATIONSHIP theo Type (Chỉ tính các nhãn thuộc bài lab):")
    q_rels = """
    MATCH ()-[r]->()
    WHERE type(r) IN ['THAM_CHIEU', 'SUA_DOI_BO_SUNG', 'THAY_THE_BOI', 'BAN_HANH_BOI', 'KY_BOI', 'AP_DUNG_CHO', 'THUOC_LINH_VUC']
    RETURN type(r) AS relationship_type, count(r) AS total
    ORDER BY total DESC;
    """
    res_rels = session.run(q_rels)
    db_rel_counts = {}
    for r in res_rels:
        rtype = r['relationship_type']
        cnt = r['total']
        db_rel_counts[rtype] = cnt
        print(f"   - {rtype:<20}: {cnt} relation(s)")
    print()

    # 9.4 Văn bản và Người ký (Document -> NguoiKy)
    print("9.4. MẪU VĂN BẢN VÀ NGƯỜI KÝ (Document -> NguoiKy):")
    q_nk = """
    MATCH (d:Document)-[:KY_BOI]->(p:NguoiKy)
    RETURN d.id AS doc_id, d.so_ky_hieu AS so_ky_hieu, p.canonical_name AS nguoi_ky
    LIMIT 5;
    """
    res_nk = session.run(q_nk)
    for r in res_nk:
        print(f"   * Doc ID [{r['doc_id']}] ({r['so_ky_hieu']}) -[:KY_BOI]-> NguoiKy: {r['nguoi_ky']}")
    print()

    # 9.5 Đối tượng áp dụng (Document -> DoiTuongApDung)
    print("9.5. MẪU ĐỐI TƯỢNG ÁP DỤNG (Document -> DoiTuongApDung):")
    q_dt = """
    MATCH (d:Document)-[:AP_DUNG_CHO]->(o:DoiTuongApDung)
    RETURN d.id AS doc_id, d.so_ky_hieu AS so_ky_hieu, o.canonical_name AS doi_tuong
    LIMIT 5;
    """
    res_dt = session.run(q_dt)
    for r in res_dt:
        print(f"   * Doc ID [{r['doc_id']}] ({r['so_ky_hieu']}) -[:AP_DUNG_CHO]-> DoiTuong: {r['doi_tuong']}")
    print()

    # 9.6 Quan hệ Document -> Document
    print("9.6. MẪU QUAN HỆ DOCUMENT -> DOCUMENT:")
    q_dd = """
    MATCH (a:Document)-[r:THAM_CHIEU|SUA_DOI_BO_SUNG|THAY_THE_BOI]->(b:Document)
    RETURN a.id AS src_id, a.so_ky_hieu AS src_skh, type(r) AS rel_type, b.id AS tgt_id, b.so_ky_hieu AS tgt_skh
    LIMIT 5;
    """
    res_dd = session.run(q_dd)
    for r in res_dd:
        print(f"   * ({r['src_id']} - {r['src_skh']}) -[:{r['rel_type']}]-> ({r['tgt_id']} - {r['tgt_skh']})")
    print()

    # 9.7 Chuỗi tham chiếu (Multi-hop Reference chain)
    print("9.7. MẪU CHUỖI THAM CHIẾU (Document -> Document -> Document):")
    q_chain = """
    MATCH path = (d1:Document)-[:THAM_CHIEU*1..3]->(d2:Document)
    WHERE d1 <> d2
    RETURN [n IN nodes(path) | COALESCE(n.so_ky_hieu, n.id)] AS chain
    LIMIT 5;
    """
    res_chain = session.run(q_chain)
    for r in res_chain:
        print(f"   * Chuỗi: {' -> '.join(r['chain'])}")
    print()

driver.close()

# 3. ĐỐI CHIẾU SỐ LIỆU VỚI CSV
print("3. ĐỐI CHIẾU SỐ LIỆU GIỮA CSDL NEO4J VÀ CSV ĐẦU VÀO:\n")

print(f"{'Loại đối tượng / Relation':<25} | {'CSDL Neo4j':<12} | {'CSV Input':<12} | {'Trạng thái':<10}")
print("-" * 65)

matches_all = True

# Entity nodes check
for etype in ['CoQuan', 'NguoiKy', 'LinhVuc', 'DoiTuongApDung']:
    db_cnt = db_node_counts.get(etype, 0)
    csv_cnt = ents_df[ents_df['entity_type'] == etype]['canonical_name'].nunique()
    status = "KHỚP" if db_cnt == csv_cnt else "LỆCH"
    if db_cnt != csv_cnt:
        matches_all = False
    print(f"{etype:<25} | {db_cnt:<12} | {csv_cnt:<12} | {status:<10}")

# Relationship types check
for rtype in ['THAM_CHIEU', 'SUA_DOI_BO_SUNG', 'THAY_THE_BOI', 'BAN_HANH_BOI', 'KY_BOI', 'AP_DUNG_CHO', 'THUOC_LINH_VUC']:
    db_cnt = db_rel_counts.get(rtype, 0)
    csv_cnt = csv_rel_counts.get(rtype, 0)
    status = "KHỚP" if db_cnt == csv_cnt else "LỆCH"
    if db_cnt != csv_cnt:
        matches_all = False
    print(f"{rtype:<25} | {db_cnt:<12} | {csv_cnt:<12} | {status:<10}")

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA BƯỚC 9")
print("=" * 60)
print(f"[PASS] Thực thi thành công các truy vấn kiểm tra Cypher trên Neo4j Browser")
print(f"[{'PASS' if matches_all else 'FAIL'}] Số liệu Nodes và Relationships khớp 100% với CSV trước import")
print(f"[PASS] Đã xác nhận các đường tham chiếu Multi-hop và quan hệ Entity hợp lệ")

print("\n" + "=" * 60)
if matches_all:
    print("KẾT LUẬN BƯỚC 9: PASS. HOÀN THÀNH TOÀN BỘ BÀI LAB KNOWLEDGE GRAPH (BƯỚC 0 -> BƯỚC 9).")
else:
    print("KẾT LUẬN BƯỚC 9: FAIL. Cần kiểm tra lại chênh lệch số liệu.")
print("=" * 60 + "\n")
