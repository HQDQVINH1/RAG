"""
Bài thực hành 2 - Bước 2: Truy vấn Vector và Mối quan hệ Đa bước (Multi-hop Graph RAG)

Tệp script này triển khai hoàn chỉnh Bước 2:
1. Chuyển đổi câu hỏi của người dùng thành vector nhúng bằng mô hình tiếng Việt `thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5`.
2. Tìm kiếm vector trong Neo4j (`chunk_vector_index`) để lấy ra top-K phân đoạn khớp nhất.
3. Duyệt đồ thị đa bước (Multi-hop Graph Traversal) qua các mối quan hệ giữa các tài liệu (`CAN_CU`, `THAY_THE`, `HOP_NHAT`, ...).
4. Xây dựng khối ngữ cảnh (Context) linh hoạt theo số bước nhảy N-hops chỉ định (0-hop, 1-hop, 2-hops).
"""

import os
import sys
import time
from typing import List, Dict, Any, Tuple
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Cấu hình UTF-8 cho Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- CẤU HÌNH THÔNG SỐ NEO4J & MODEL ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Vinh1989")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "kb-hops")

EMBEDDING_MODEL_NAME = "thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5"


class MultiHopGraphRAG:
    """
    Lớp quản lý truy vấn Vector & Đồ thị Đa bước (Multi-hop Graph RAG Engine).
    """

    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.model = None
        self.target_db = None

    def initialize(self):
        """Khởi tạo mô hình Embedding và kết nối Neo4j."""
        print("=" * 80)
        print("  KHỞI TẠO HỆ THỐNG TRUY VẤN ĐỒ THỊ ĐA BƯỚC (MULTI-HOP GRAPH RAG)")
        print("=" * 80)

        # 1. Tải mô hình Embedding
        print(f"\n1. Đang tải mô hình Embedding tiếng Việt: '{EMBEDDING_MODEL_NAME}'...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
        print("   ✓ Đã tải xong mô hình Embedding!")

        # 2. Kết nối Neo4j Driver
        print(f"\n2. Đang kết nối tới Neo4j Server tại {self.uri}...")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()
        print("   ✓ Đã kết nối thành công tới Neo4j Server!")

        # 3. Xác định database khả dụng
        try:
            with self.driver.session(database=NEO4J_DATABASE) as session:
                session.run("RETURN 1")
            self.target_db = NEO4J_DATABASE
        except Exception:
            self.target_db = "neo4j"

        print(f"   ✓ Sử dụng Cơ sở dữ liệu: '{self.target_db}'")

    def close(self):
        """Đóng kết nối Neo4j Driver."""
        if self.driver:
            self.driver.close()

    def generate_embedding(self, text: str) -> List[float]:
        """Chuyển đổi chuỗi văn bản/câu hỏi thành vector nhúng 384 chiều."""
        emb = self.model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    def search_direct_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Thực hiện tìm kiếm Vector trong Neo4j (Vector Index `chunk_vector_index`).
        Trả về top-K Chunks khớp trực nhất với câu hỏi.
        """
        cypher_query = """
        CALL db.index.vector.queryNodes('chunk_vector_index', $top_k, $vector)
        YIELD node, score
        MATCH (node)-[:PART_OF]->(d:Document)
        RETURN 
            node.id AS chunk_id,
            node.type AS chunk_type,
            node.title AS chunk_title,
            node.text AS chunk_text,
            d.id AS doc_id,
            d.title AS doc_title,
            d.so_ky_hieu AS so_ky_hieu,
            score AS similarity_score
        """
        with self.driver.session(database=self.target_db) as session:
            result = session.run(cypher_query, top_k=top_k, vector=query_vector)
            return [record.data() for record in result]

    def expand_multihop_documents(self, source_doc_ids: List[str], hops: int = 1) -> List[Dict[str, Any]]:
        """
        Duyệt đồ thị đa bước (Multi-hop Traversal) từ danh sách tài liệu gốc (source_doc_ids)
        qua các mối quan hệ giữa các Document (ví dụ: CAN_CU, THAY_THE, HOP_NHAT, SUA_DOI,...).
        """
        if hops <= 0 or not source_doc_ids:
            return []

        # Cypher traversal động cho N-hops
        cypher_query = f"""
        MATCH (d1:Document) WHERE d1.id IN $doc_ids
        MATCH path = (d1)-[r*1..{hops}]-(d2:Document)
        WHERE d1 <> d2
        WITH d1, d2, relationships(path) AS rels, length(path) AS distance
        RETURN DISTINCT
            d1.id AS source_doc_id,
            d1.title AS source_doc_title,
            d2.id AS connected_doc_id,
            d2.title AS connected_doc_title,
            d2.so_ky_hieu AS connected_so_ky_hieu,
            [x IN rels | type(x)] AS relationship_path,
            distance
        ORDER BY distance ASC
        """
        with self.driver.session(database=self.target_db) as session:
            result = session.run(cypher_query, doc_ids=source_doc_ids)
            return [record.data() for record in result]

    def get_chunks_from_documents(self, doc_ids: List[str], max_chunks_per_doc: int = 3) -> List[Dict[str, Any]]:
        """
        Lấy các phân đoạn văn bản tiêu biểu (Chunks) từ danh sách tài liệu liên quan được duyệt đa bước.
        """
        if not doc_ids:
            return []

        cypher_query = """
        UNWIND $doc_ids AS did
        MATCH (c:Chunk)-[:PART_OF]->(d:Document {id: did})
        WITH d, c ORDER BY c.id ASC
        WITH d, collect(c)[..$max_chunks] AS doc_chunks
        UNWIND doc_chunks AS chunk
        RETURN
            chunk.id AS chunk_id,
            chunk.type AS chunk_type,
            chunk.title AS chunk_title,
            chunk.text AS chunk_text,
            d.id AS doc_id,
            d.title AS doc_title,
            d.so_ky_hieu AS so_ky_hieu
        """
        with self.driver.session(database=self.target_db) as session:
            result = session.run(cypher_query, doc_ids=doc_ids, max_chunks=max_chunks_per_doc)
            return [record.data() for record in result]

    def retrieve_multihop_context(self, question: str, top_k: int = 3, hops: int = 1) -> Dict[str, Any]:
        """
        HÀM CHÍNH BƯỚC 2: Xây dựng ngữ cảnh RAG Đa bước (Multi-hop Context Pipeline)
        - Encode câu hỏi
        - Vector search lấy top-K chunks gốc
        - Multi-hop graph expansion duyệt các tài liệu liên quan N-hops
        - Tổng hợp ngữ cảnh & trích dẫn chứng minh
        """
        start_time = time.time()

        # 1. Tạo vector nhúng cho câu hỏi
        query_vector = self.generate_embedding(question)

        # 2. Vector Search (0-hop direct chunks)
        direct_chunks = self.search_direct_chunks(query_vector, top_k=top_k)

        # Trích xuất danh sách các doc_id gốc
        direct_doc_ids = list(dict.fromkeys([c["doc_id"] for c in direct_chunks]))

        # 3. Graph Multi-hop Expansion (N-hops)
        multihop_connections = []
        multihop_chunks = []

        if hops > 0 and direct_doc_ids:
            multihop_connections = self.expand_multihop_documents(direct_doc_ids, hops=hops)
            connected_doc_ids = list(dict.fromkeys([
                c["connected_doc_id"] for c in multihop_connections if c["connected_doc_id"] not in direct_doc_ids
            ]))
            if connected_doc_ids:
                multihop_chunks = self.get_chunks_from_documents(connected_doc_ids, max_chunks_per_doc=2)

        elapsed_time = time.time() - start_time

        # 4. Đóng gói kết quả ngữ cảnh
        return {
            "question": question,
            "top_k": top_k,
            "hops": hops,
            "elapsed_time_sec": round(elapsed_time, 3),
            "direct_chunks": direct_chunks,
            "direct_doc_ids": direct_doc_ids,
            "multihop_connections": multihop_connections,
            "multihop_chunks": multihop_chunks,
        }


def print_retrieval_report(result: Dict[str, Any]):
    """In báo cáo kết quả truy vấn đa bước trực quan ra màn hình Console."""
    print("\n" + "=" * 80)
    print(f"  BÁO CÁO TRUY VẤN GRAPH RAG ĐA BƯỚC (HOPS = {result['hops']})")
    print("=" * 80)
    print(f"❓ CÂU HỎI: \"{result['question']}\"")
    print(f"⏱️  Thời gian xử lý: {result['elapsed_time_sec']} giây")
    print("-" * 80)

    # 1. Hiển thị Chunks Trực Tiếp (Vector Search - 0 Hop)
    print(f"\n📌 1. KẾT QUẢ TÌM KIẾM VECTOR TRỰC TIẾP ({len(result['direct_chunks'])} Chunks):")
    for idx, c in enumerate(result['direct_chunks'], start=1):
        print(f"  [Chunk {idx}] ID: {c['chunk_id']} | Độ tương đồng (Score): {c['similarity_score']:.4f}")
        print(f"    • Tài liệu gốc: Document {c['doc_id']} - {c['doc_title']}")
        print(f"    • Nội dung: {c['chunk_text'][:120]}...")
        print("-" * 60)

    # 2. Hiển thị Quan hệ Đa bước (Multi-hop Expansion)
    if result['hops'] > 0:
        print(f"\n🌐 2. MỞ RỘNG ĐỒ THỊ ĐA BƯỚC (MULTI-HOP EXPANSION - {result['hops']} HOPS):")
        if not result['multihop_connections']:
            print("  (Không tìm thấy liên kết tài liệu đa bước nào từ các tài liệu gốc)")
        else:
            for idx, rel in enumerate(result['multihop_connections'], start=1):
                path_str = " -> ".join(rel['relationship_path'])
                print(f"  [Liên kết {idx}] Doc {rel['source_doc_id']} ==({path_str})==> Doc {rel['connected_doc_id']}")
                print(f"    • Tài liệu liên quan: {rel['connected_doc_title']}")
                print("-" * 60)

        print(f"\n📚 3. CHUNKS THU THẬP TỪ CÁC TÀI LIỆU ĐA BƯỚC ({len(result['multihop_chunks'])} Chunks):")
        for idx, mc in enumerate(result['multihop_chunks'], start=1):
            print(f"  [Hop-Chunk {idx}] ID: {mc['chunk_id']} | Từ Doc {mc['doc_id']}")
            print(f"    • Nội dung: {mc['chunk_text'][:120]}...")
            print("-" * 60)
    else:
        print("\n⚙️  Chế độ 0-Hop (Chỉ sử dụng ngữ cảnh trực tiếp từ Vector Search).")

    print("=" * 80)


def main():
    rag_engine = MultiHopGraphRAG()
    try:
        rag_engine.initialize()

        # Các câu hỏi thử nghiệm đại diện Bước 2
        test_questions = [
            "Quy định về giao nhận, bảo quản, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước",
            "Căn cứ pháp lý và các văn bản sửa đổi bổ sung quy định cho vay đối với khách hàng"
        ]

        for q in test_questions:
            print("\n" + "►" * 40 + " THỬ NGHIỆM TRUY VẤN " + "◄" * 40)

            # Chạy thử với Hops = 0 và Hops = 1 để so sánh
            res_0_hop = rag_engine.retrieve_multihop_context(q, top_k=3, hops=0)
            print_retrieval_report(res_0_hop)

            res_1_hop = rag_engine.retrieve_multihop_context(q, top_k=3, hops=1)
            print_retrieval_report(res_1_hop)

    except Exception as e:
        print(f"\n✗ LỖI THỰC THI BƯỚC 2: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rag_engine.close()


if __name__ == "__main__":
    main()
