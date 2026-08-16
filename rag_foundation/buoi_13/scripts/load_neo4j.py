import csv
import os
import sys
from pathlib import Path

# Fix UTF-8 encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_env_file(env_path: Path):
    """Đọc file .env đơn giản nếu chưa có python-dotenv."""
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

def main():
    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / ".env"
    load_env_file(env_file)

    # 1. Kiểm tra thư viện neo4j
    try:
        from neo4j import GraphDatabase, exceptions
    except ImportError:
        print("=" * 80)
        print("⚠️ CẢNH BÁO: CHƯA CÀI ĐẶT THƯ VIỆN PYTHON NEO4J DRIVER")
        print("=" * 80)
        print("Để kết nối và đẩy dữ liệu vào Neo4j, vui lòng chạy lệnh sau:")
        print("   pip install neo4j python-dotenv")
        print("\nCác file Wiki Markdown đã được tạo hoàn chỉnh và không bị ảnh hưởng.")
        print("=" * 80)
        return

    # 2. Đọc cấu hình từ môi trường / .env
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    if not password:
        print("=" * 80)
        print("⚠️ CẢNH BÁO: CHƯA CẤU HÌNH NEO4J_PASSWORD")
        print("=" * 80)
        print("Vui lòng tạo file .env tại thư mục gốc project với nội dung mẫu:")
        print("   NEO4J_URI=bolt://localhost:7687")
        print("   NEO4J_USER=neo4j")
        print("   NEO4J_PASSWORD=your_password_here")
        print("   NEO4J_DATABASE=neo4j")
        print("=" * 80)

    print("=" * 80)
    print("NẠP DỮ LIỆU WIKI RISK GRAPH VÀO NEO4J DATABASE")
    print("=" * 80)
    print(f"- URI: {uri}")
    print(f"- User: {user}")
    print(f"- Database: {database}")

    # 3. Kết nối Neo4j
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("✓ Kết nối Neo4j Database thành công!")
    except Exception as e:
        print(f"\n❌ KHÔNG THỂ KẾT NỐI ĐẾN NEO4J tại {uri}")
        print(f"Chi tiết lỗi: {e}")
        print("\nHƯỚNG DẪN XỬ LÝ:")
        print("1. Kiểm tra Neo4j Server (Neo4j Desktop hoặc Docker container) đã được bật chưa.")
        print("2. Chạy Neo4j bằng Docker (nếu chưa có):")
        print("   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:latest")
        print("3. Cập nhật mật khẩu tương ứng vào file .env")
        print("4. Chạy lại script: python scripts/load_neo4j.py")
        print("\n*Lưu ý: Lỗi kết nối Neo4j không làm ảnh hưởng đến dữ liệu Wiki Markdown trong Obsidian.*")
        print("=" * 80)
        return

    output_dir = base_dir / "outputs"
    entities_file = output_dir / "entities.csv"
    relations_file = output_dir / "relations.csv"

    if not entities_file.exists() or not relations_file.exists():
        print(f"❌ Không tìm thấy entities.csv hoặc relations.csv tại {output_dir}")
        driver.close()
        return

    # 4. Nạp schema / constraints
    schema_file = base_dir / "cypher" / "schema.cypher"
    if schema_file.exists():
        print("\n--- 1. ĐANG THIẾT LẬP SCHEMA & CONSTRAINTS ---")
        schema_cypher = schema_file.read_text(encoding="utf-8")
        queries = [q.strip() for q in schema_cypher.split(";") if q.strip() and not q.strip().startswith("//")]
        with driver.session(database=database) as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as ex:
                    print(f"Lỗi khi chạy query schema: {ex}")
        print("✓ Đã khởi tạo xong Constraint & Index.")

    # 5. Nạp Entities (Nodes) bằng MERGE parameterized query
    print("\n--- 2. ĐANG NẠP ENTITIES (NODES) ---")
    nodes_loaded = 0

    cypher_ruiro = """
    MERGE (r:RuiRo {id: $id})
    SET r.name = $name,
        r.description = $description,
        r.category = $category,
        r.cause = $cause,
        r.event = $event,
        r.impact = $impact,
        r.inherent_level = $inherent_level,
        r.residual_level = $residual_level,
        r.owner_unit_id = $owner_unit_id,
        r.data_origin = $data_origin,
        r.verification_status = $verification_status,
        r.source_file = $source_file
    """

    cypher_kiemsoat = """
    MERGE (k:KiemSoat {id: $id})
    SET k.name = $name,
        k.description = $description,
        k.control_type = $control_type,
        k.frequency = $frequency,
        k.owner_role_id = $owner_role_id,
        k.effectiveness = $effectiveness,
        k.data_origin = $data_origin,
        k.verification_status = $verification_status,
        k.source_file = $source_file
    """

    cypher_sukien = """
    MERGE (s:SuKienRuiRo {id: $id})
    SET s.description = $description,
        s.risk_id = $risk_id,
        s.occurred_at = $occurred_at,
        s.discovered_at = $discovered_at,
        s.severity = $severity,
        s.loss_amount_vnd = toFloat($loss_amount_vnd),
        s.data_origin = $data_origin,
        s.verification_status = $verification_status,
        s.source_file = $source_file
    """

    with open(entities_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with driver.session(database=database) as session:
            for row in reader:
                etype = row["type"]
                if etype == "RuiRo":
                    session.run(cypher_ruiro, **row)
                elif etype == "KiemSoat":
                    session.run(cypher_kiemsoat, **row)
                elif etype == "SuKienRuiRo":
                    session.run(cypher_sukien, **row)
                nodes_loaded += 1

    print(f"✓ Đã nạp thành công {nodes_loaded} Nodes vào Neo4j (dùng MERGE không bị duplicate).")

    # 6. Nạp Relations (Edges) bằng MERGE parameterized query
    print("\n--- 3. ĐANG NẠP RELATIONS (EDGES) ---")
    edges_loaded = 0

    cypher_mitigates = """
    MATCH (k:KiemSoat {id: $source_id})
    MATCH (r:RuiRo {id: $target_id})
    MERGE (k)-[rel:MITIGATES]->(r)
    SET rel.source = $source,
        rel.evidence_quote = $evidence_quote,
        rel.confidence = toFloat($confidence),
        rel.verification_status = $verification_status,
        rel.data_origin = $data_origin
    """

    cypher_observed = """
    MATCH (r:RuiRo {id: $source_id})
    MATCH (s:SuKienRuiRo {id: $target_id})
    MERGE (r)-[rel:OBSERVED_AS]->(s)
    SET rel.source = $source,
        rel.evidence_quote = $evidence_quote,
        rel.confidence = toFloat($confidence),
        rel.verification_status = $verification_status,
        rel.data_origin = $data_origin
    """

    with open(relations_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with driver.session(database=database) as session:
            for row in reader:
                rel_type = row["relationship_type"]
                if rel_type == "MITIGATES":
                    session.run(cypher_mitigates, **row)
                elif rel_type == "OBSERVED_AS":
                    session.run(cypher_observed, **row)
                edges_loaded += 1

    print(f"✓ Đã nạp thành công {edges_loaded} Edges vào Neo4j (dùng MERGE không bị duplicate).")

    driver.close()
    print("\n" + "=" * 80)
    print("HOÀN THÀNH NẠP DỮ LIỆU NEO4J!")
    print("=" * 80)

if __name__ == "__main__":
    main()
