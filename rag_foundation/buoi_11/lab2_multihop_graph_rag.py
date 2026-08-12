"""
Bài thực hành 2: Tìm kiếm Đồ thị RAG Đa bước (Multi-hop Graph RAG) & Hỏi Đáp (QA) với LLM Gemini API

Tệp script này triển khai hoàn chỉnh:
- BƯỚC 1: Kết nối Cơ sở dữ liệu Neo4j.
- BƯỚC 2: Truy vấn Vector (0-hop) và Mở rộng Đồ thị Đa bước (Multi-hop Graph Traversal N-hops).
- BƯỚC 3: Tích hợp Ngữ cảnh và Gọi LLM (Gemini API) với System Prompt chuẩn hóa Grounding & Citation Mapping.
"""

import os
import sys
import time
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from google import genai

# Cấu hình UTF-8 cho Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- NẠP CẤU HÌNH TỪ .ENV ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Vinh1989")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash").strip()

EMBEDDING_MODEL_NAME = "thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5"


# ==============================================================================
# BƯỚC 3: PROMPT HỆ THỐNG (SYSTEM PROMPT DESIGN FOR LLM)
# ==============================================================================
SYSTEM_PROMPT = """Bạn là trợ lý Chuyên gia Pháp lý AI cao cấp chuyên phân tích văn bản quy phạm pháp luật Việt Nam dựa trên Cơ sở dữ liệu Đồ thị Multi-Hop Graph RAG.

### THÔNG TIN VỀ CẤU TRÚC DỮ LIỆU ĐỒ THỊ (GRAPH SCHEMA):
1. **Nút Document**: Đại diện cho văn bản luật gốc (Ví dụ: Thông tư, Nghị định, Luật).
2. **Nút Chunk**: Đại diện cho từng phân đoạn văn bản được chia nhỏ theo cấu trúc phân cấp (Chương ➔ Mục ➔ Điều ➔ Khoản).
3. **Mối quan hệ**:
   - `[:PART_OF]`: Phân đoạn Chunk thuộc về Document.
   - `[:PARENT_OF]`: Quan hệ phân cấp Cha - Con giữa các tiêu đề và nội dung khoản.
   - `[:NEXT]`: Trình tự đọc tuần tự giữa các đoạn.
   - `[:CAN_CU]`, `[:THAY_THE]`, `[:HOP_NHAT]`, `[:SUA_DOI]`, `[:BO_SUNG]`: Mối quan hệ đa bước (Multi-hop) nối giữa các văn bản luật liên quan.

### NGUYÊN TẮC TRẢ LỜI NGHIÊM NGẶT (GROUNDING RULES):
1. **Chỉ sử dụng ngữ cảnh được cung cấp**: Bạn CHỈ ĐƯỢC trả lời dựa hoàn toàn trên thông tin trong khối [NGỮ CẢNH TRUY VẤN GRAPH RAG] bên dưới.
2. **Không tự suy đoán hoặc sáng tạo ngoài ngữ cảnh**: Nếu khối ngữ cảnh KHÔNG chứa đủ thông tin để trả lời câu hỏi, bạn BẮT BUỘC phải trả lời chính xác câu sau:
   "Dữ liệu được cung cấp không chứa đủ thông tin để trả lời câu hỏi này."
3. **Trích dẫn nguồn minh bạch (Citation Mapping)**: Cuối mỗi ý hoặc câu trả lời, bạn phải ghi rõ trích dẫn theo định dạng: `[Nguồn: <Tên_Văn_Bản>, <Số_Ký_Hiệu>, Chunk: <Chunk_ID>]`.
4. **Trình bày chuyên nghiệp**: Sử dụng định dạng Markdown rõ ràng, hành văn chuẩn mực pháp lý.
"""


class MultiHopGraphRAG:
    """
    Lớp quản lý RAG Đồ thị Đa bước tích hợp Gemini API.
    """

    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.embedding_model = None
        self.genai_client = None
        self.target_db = None

    def initialize(self):
        """Khởi tạo mô hình Embedding, Gemini Client và kết nối Neo4j."""
        print("=" * 80)
        print("  KHỞI TẠO HỆ THỐNG TRUY VẤN ĐỒ THỊ ĐA BƯỚC (MULTI-HOP GRAPH RAG + LLM)")
        print("=" * 80)

        # 1. Tải mô hình Embedding
        print(f"\n1. Đang tải mô hình Embedding tiếng Việt: '{EMBEDDING_MODEL_NAME}'...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
        print("   ✓ Đã tải xong mô hình Embedding!")

        # 2. Khởi tạo Gemini LLM Client
        if not GEMINI_API_KEY:
            raise ValueError("Thiếu GEMINI_API_KEY trong file .env!")
        print(f"\n2. Đang kết nối Gemini API Client (Model: {GEMINI_GENERATION_MODEL})...")
        self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("   ✓ Đã khởi tạo Gemini Client thành công!")

        # 3. Kết nối Neo4j Driver (Bước 1)
        print(f"\n3. Đang kết nối tới Neo4j Server tại {self.uri}...")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()
        print("   ✓ Đã kết nối thành công tới Neo4j Server!")

        # Xác định database
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
        """Chuyển đổi câu hỏi thành vector nhúng 384 chiều."""
        emb = self.embedding_model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    # ==============================================================================
    # BƯỚC 2: TRUY VẤN VECTOR & MỞ RỘNG ĐỒ THỊ ĐA BƯỚC (MULTI-HOP TRAVERSAL)
    # ==============================================================================
    def search_direct_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm Vector trong Neo4j (0-hop)."""
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
        """Duyệt đồ thị đa bước N-hops từ danh sách tài liệu gốc qua các mối quan hệ liên kết."""
        if hops <= 0 or not source_doc_ids:
            return []

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

    def get_chunks_from_documents(self, doc_ids: List[str], max_chunks_per_doc: int = 2) -> List[Dict[str, Any]]:
        """Lấy các phân đoạn văn bản từ các tài liệu liên quan đa bước."""
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

    def retrieve_multihop_context(self, question: str, top_k: int = 4, hops: int = 1) -> Dict[str, Any]:
        """Tập hợp khối ngữ cảnh truy vấn đa bước."""
        start_time = time.time()
        query_vector = self.generate_embedding(question)
        direct_chunks = self.search_direct_chunks(query_vector, top_k=top_k)
        direct_doc_ids = list(dict.fromkeys([c["doc_id"] for c in direct_chunks]))

        multihop_connections = []
        multihop_chunks = []

        if hops > 0 and direct_doc_ids:
            multihop_connections = self.expand_multihop_documents(direct_doc_ids, hops=hops)
            connected_doc_ids = list(dict.fromkeys([
                c["connected_doc_id"] for c in multihop_connections if c["connected_doc_id"] not in direct_doc_ids
            ]))
            if connected_doc_ids:
                multihop_chunks = self.get_chunks_from_documents(connected_doc_ids, max_chunks_per_doc=2)

        elapsed = time.time() - start_time
        return {
            "question": question,
            "top_k": top_k,
            "hops": hops,
            "elapsed_time_sec": round(elapsed, 3),
            "direct_chunks": direct_chunks,
            "multihop_connections": multihop_connections,
            "multihop_chunks": multihop_chunks,
        }

    # ==============================================================================
    # BƯỚC 3: ĐỊNH DẠNG PROMPT NGỮ CẢNH & GỌI GEMINI LLM
    # ==============================================================================
    def format_context_prompt(self, retrieval_res: Dict[str, Any]) -> str:
        """Định dạng toàn bộ khối ngữ cảnh (Direct + Multi-hop) đưa vào Prompt."""
        context_parts = []

        # 1. Khối Chunks Trực Tiếp (Vector Search - 0 Hop)
        context_parts.append("=== I. PHÂN ĐOẠN TRUY VẤN TRỰC TIẾP (VECTOR SEARCH - 0 HOP) ===")
        for idx, c in enumerate(retrieval_res["direct_chunks"], start=1):
            skh = c.get("so_ky_hieu") or "N/A"
            context_parts.append(
                f"[{idx}] Chunk ID: {c['chunk_id']}\n"
                f"    Nguồn: {c['doc_title']} (Số hiệu: {skh})\n"
                f"    Nội dung: {c['chunk_text']}\n"
            )

        # 2. Khối Quan hệ Đồ thị & Chunks Đa bước (Multi-hop)
        if retrieval_res["hops"] > 0 and retrieval_res["multihop_chunks"]:
            context_parts.append("\n=== II. PHÂN ĐOẠN TỪ CÁC TÀI LIỆU LIÊN QUAN ĐA BƯỚC (MULTI-HOP GRAPH EXPANSION) ===")
            
            # Liệt kê sơ đồ mối quan hệ
            context_parts.append("--- Mối quan hệ đồ thị giữa các văn bản ---")
            for rel in retrieval_res["multihop_connections"]:
                path_str = " -> ".join(rel['relationship_path'])
                context_parts.append(f"  • Doc {rel['source_doc_id']} ==({path_str})==> {rel['connected_doc_title']}")

            context_parts.append("\n--- Nội dung các đoạn văn bản từ tài liệu liên quan ---")
            for idx, mc in enumerate(retrieval_res["multihop_chunks"], start=1):
                skh = mc.get("so_ky_hieu") or "N/A"
                context_parts.append(
                    f"[Hop-{idx}] Chunk ID: {mc['chunk_id']}\n"
                    f"    Nguồn: {mc['doc_title']} (Số hiệu: {skh})\n"
                    f"    Nội dung: {mc['chunk_text']}\n"
                )

        return "\n".join(context_parts)

    def generate_answer_with_llm(
        self, 
        question: str, 
        hops: int = 1, 
        top_k: int = 4,
        item_index: int = 1,
        total_items: int = 1
    ) -> Dict[str, Any]:
        """
        HÀM HOÀN CHỈNH BƯỚC 3:
        1. Truy vấn ngữ cảnh Đa bước (Graph Retrieval)
        2. Tạo Prompt kết hợp System Prompt + Context Block + Question
        3. Gọi Gemini API với cơ chế tự động tạm dừng 60s khi gặp lỗi 429 (Rate Limit / Quota)
        """
        # 1. Truy vấn ngữ cảnh
        retrieved_data = self.retrieve_multihop_context(question, top_k=top_k, hops=hops)
        context_prompt = self.format_context_prompt(retrieved_data)

        # 2. Xây dựng User Prompt đầy đủ
        full_user_prompt = f"""[NGỮ CẢNH TRUY VẤN GRAPH RAG]
{context_prompt}

--------------------------------------------------------------------------------
[CÂU HỎI NGƯỜI DÙNG]
{question}

Vui lòng trả lời câu hỏi dựa trên các nguyên tắc và ngữ cảnh được cung cấp ở trên.
"""

        # 3. Gọi Gemini LLM với vòng lặp tự động tạm dừng 60s khi bị 429
        print(f"\n[TIẾN TRÌNH {item_index}/{total_items}] Đang xử lý item (Hops={hops}): \"{question[:60]}...\"")
        print(f"🤖 Đang gửi yêu cầu tới Gemini LLM ({GEMINI_GENERATION_MODEL})...")
        llm_start = time.time()
        
        response = None
        models_to_try = [GEMINI_GENERATION_MODEL, "gemini-3.5-flash-lite"] if GEMINI_GENERATION_MODEL != "gemini-3.5-flash-lite" else ["gemini-3.5-flash-lite"]
        
        attempt = 0
        while response is None:
            attempt += 1
            for m_name in models_to_try:
                try:
                    response = self.genai_client.models.generate_content(
                        model=m_name,
                        contents=[SYSTEM_PROMPT, full_user_prompt]
                    )
                    print(f"  ✓ [XONG {item_index}/{total_items}] Đã nhận phản hồi thành công từ Gemini LLM (Lần thử {attempt}, Model: {m_name}).")
                    break
                except Exception as ex:
                    err_str = str(ex)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        print(f"\n⚠️ [LỖI 429 RATE LIMIT/QUOTA - ITEM {item_index}/{total_items}] Gặp hạn ngạch Gemini API Free Tier (Model {m_name}).")
                        print(f"   ⏳ Tạm dừng 60 giây để chờ làm mới hạn ngạch...")
                        time.sleep(60)
                        print(f"   🔄 Hết 60s tạm dừng. Tự động tiếp tục xử lý Item {item_index}/{total_items} (Lần thử {attempt + 1})...\n")
                        break  # thử lại vòng lặp ngoài từ đúng item hiện tại
                    elif ("11002" in err_str or "ConnectError" in err_str or "getaddrinfo" in err_str):
                        print(f"\n⚠️ [LỖI MẠNG - ITEM {item_index}/{total_items}] Gián đoạn kết nối DNS. Tạm dừng 10s và thử lại...")
                        time.sleep(10)
                        break
                    else:
                        print(f"\n✗ [LỖI ITEM {item_index}/{total_items}]: {ex}")
                        raise ex

        llm_elapsed = round(time.time() - llm_start, 3)
        answer_text = response.text if (response and hasattr(response, "text")) else str(response)

        return {
            "question": question,
            "hops": hops,
            "answer": answer_text,
            "retrieval_time_sec": retrieved_data["elapsed_time_sec"],
            "llm_time_sec": llm_elapsed,
            "retrieved_data": retrieved_data
        }


def print_qa_result(qa_result: Dict[str, Any]):
    """In kết quả Hỏi-Đáp (QA) hoàn chỉnh với LLM Gemini out màn hình Console."""
    print("\n" + "=" * 80)
    print(f"  KẾT QUẢ HỎI ĐÁP RAG ĐA BƯỚC (HOPS = {qa_result['hops']})")
    print("=" * 80)
    print(f"❓ CÂU HỎI: \"{qa_result['question']}\"")
    print(f"⏱️  Thời gian: Retrieval {qa_result['retrieval_time_sec']}s | LLM {qa_result['llm_time_sec']}s")
    print("-" * 80)
    print("💬 CÂU TRẢ LỜI TỪ GEMINI LLM:\n")
    print(qa_result["answer"])
    print("=" * 80)


def main():
    rag = MultiHopGraphRAG()
    try:
        rag.initialize()

        # Thử nghiệm Bước 3 với các câu hỏi kiểm thử
        sample_question = "Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"
        
        print("\n" + "►" * 35 + " BƯỚC 3: TRUY VẤN HOÀN CHỈNH KẾT HỢP GEMINI LLM " + "◄" * 35)
        
        # Test 1: Hops = 0 (Chỉ lấy tài liệu gốc)
        qa_0_hop = rag.generate_answer_with_llm(sample_question, hops=0)
        print_qa_result(qa_0_hop)

        # Test 2: Hops = 1 (Tích hợp tìm kiếm đa bước)
        qa_1_hop = rag.generate_answer_with_llm(sample_question, hops=1)
        print_qa_result(qa_1_hop)

    except Exception as e:
        print(f"\n✗ LỖI THỰC THI BƯỚC 3: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rag.close()


if __name__ == "__main__":
    main()
