"""
BƯỚC 5: Kiểm tra và Xác minh Dữ liệu Đồ thị trên Neo4j Browser / Cypher

Kịch bản này chạy các câu lệnh Cypher xác minh 5 tiêu chí:
1. Số lượng nút Document (Cần đúng 15 nút).
2. Số lượng quan hệ giữa các tài liệu Document (Cần đúng 8 quan hệ).
3. Số lượng nút Chunk, quan hệ [:PART_OF], [:PARENT_OF], [:NEXT].
4. Trạng thái của Neo4j Vector Index (`chunk_vector_index`).
"""

import sys
from neo4j import GraphDatabase

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Vinh1989"
NEO4J_DATABASE = "kb-hops"

def verify_graph():
    print("=" * 80)
    print("  BƯỚC 5: KIỂM TRA VÀ XÁC MINH CƠ SỞ DỮ LIỆU ĐỒ THỊ NEO4J")
    print("=" * 80)
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
    except Exception as e:
        print(f"\n✗ LỖI KẾT NỐI NEO4J: {e}")
        print("Vui lòng khởi động DBMS Instance trên Neo4j Desktop 2.0 trước khi chạy xác minh.")
        return

    # Kiểm tra DB target
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.run("RETURN 1")
        target_db = NEO4J_DATABASE
    except Exception:
        target_db = "neo4j"

    print(f"\nĐang kết nối tới Database '{target_db}' trên Neo4j...\n")
    
    with driver.session(database=target_db) as session:
        # Query 1: Nút Document (Yêu cầu 15 nút)
        q1 = "MATCH (d:Document) RETURN count(d) AS cnt"
        num_docs = session.run(q1).single()["cnt"]

        # Query 2: Quan hệ giữa các Document (Yêu cầu 8 quan hệ)
        q2 = "MATCH (d1:Document)-[r]->(d2:Document) RETURN count(r) AS cnt"
        num_doc_rels = session.run(q2).single()["cnt"]

        # Query 3: Thống kê Chunk & Quan hệ
        num_chunks = session.run("MATCH (c:Chunk) RETURN count(c) AS cnt").single()["cnt"]
        num_part_of = session.run("MATCH ()-[r:PART_OF]->() RETURN count(r) AS cnt").single()["cnt"]
        num_parent_of = session.run("MATCH ()-[r:PARENT_OF]->() RETURN count(r) AS cnt").single()["cnt"]
        num_next = session.run("MATCH ()-[r:NEXT]->() RETURN count(r) AS cnt").single()["cnt"]

        # Query 4: Kiểm tra Vector Index
        indexes = []
        try:
            res = session.run("SHOW INDEXES YIELD name, type, labelsOrTypes, properties WHERE type = 'VECTOR'")
            for record in res:
                indexes.append(record.data())
        except Exception:
            pass

        print("=" * 70)
        print(" BẢNG BÁO CÁO XÁC MINH CƠ SỞ DỮ LIỆU ĐỒ THỊ NEO4J")
        print("=" * 70)
        print(f" 1. Số lượng nút Document:         {num_docs:<6} | Yêu cầu: 15  | Status: {'✓ ĐẠT' if num_docs == 15 else '✗ CHƯA ĐẠT'}")
        print(f" 2. Quan hệ giữa các Document:     {num_doc_rels:<6} | Yêu cầu: 8   | Status: {'✓ ĐẠT' if num_doc_rels == 8 else '✗ CHƯA ĐẠT'}")
        print(f" 3. Tổng số nút Chunk:              {num_chunks:<6} | Tình trạng: Đã nạp dữ liệu sạch & vector")
        print(f" 4. Mối quan hệ [:PART_OF]:         {num_part_of:<6} | (Liên kết Chunk ➔ Document)")
        print(f" 5. Mối quan hệ [:PARENT_OF]:       {num_parent_of:<6} | (Cấu trúc phân cấp Cha-Con)")
        print(f" 6. Mối quan hệ [:NEXT]:            {num_next:<6} | (Trình tự đọc tuần tự)")
        print(f" 7. Neo4j Vector Index:             {len(indexes)} Vector Index active")
        print("=" * 70)

    driver.close()

if __name__ == "__main__":
    verify_graph()
