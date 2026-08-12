"""
Bài thực hành 1: Phân tách dữ liệu (Chunking), Tạo Vector nhúng (Embeddings) và Nạp dữ liệu vào Cơ sở dữ liệu đồ thị Neo4j

Các bước thực hiện:
1. Phân tích HTML, Làm sạch và Phân tách cấu trúc phân cấp (Hierarchical Parent-Child Chunking).
2. Tạo Vector Nhúng (Dense Embeddings) bằng mô hình `thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5` trên CPU.
3. Cấu hình kết nối Cơ sở dữ liệu Neo4j (`kb-hops`).
4. Nạp dữ liệu siêu dữ liệu (Document), phân đoạn (Chunk), vector nhúng và các mối quan hệ (PART_OF, PARENT_OF, NEXT, CAN_CU, THAY_THE, HOP_NHAT, ...).
5. Kiểm tra và xác minh kết quả trên Neo4j.
"""

import os
import csv
import re
import sys
from bs4 import BeautifulSoup
from tqdm import tqdm

# Cấu hình UTF-8 cho Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

csv.field_size_limit(sys.maxsize)

# --- THÔNG SỐ CẤU HÌNH NEO4J & MODEL ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Vinh1989")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "kb-hops")

EMBEDDING_MODEL_NAME = "thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_FILE = os.path.join(BASE_DIR, "metadata.csv")
CONTENT_FILE = os.path.join(BASE_DIR, "content.csv")
RELATIONSHIPS_FILE = os.path.join(BASE_DIR, "relationships.csv")


# ==========================================
# BƯỚC 1: LÀM SẠCH HTML & CHUNKING PHÂN CẤP
# ==========================================

def clean_html_to_elements(html_content: str):
    """
    Làm sạch nội dung HTML, trích xuất danh sách các phần tử văn bản (đoạn văn, bảng biểu)
    mà vẫn giữ nguyên luồng đọc và cấu trúc.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Loại bỏ thẻ script, style, inline style cồng kềnh
    for s in soup(['script', 'style', 'meta', 'link']):
        s.decompose()
        
    elements = []
    
    # Trích xuất các thẻ p, h1, h2, h3, h4, table
    for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'table', 'div']):
        # Nếu là table, chuyển thành văn bản hoặc giữ cấu trúc cơ bản
        if tag.name == 'table':
            text = tag.get_text(separator=' | ', strip=True)
        else:
            text = tag.get_text(separator=' ', strip=True)
            
        # Làm sạch ký tự khoảng trắng đặc biệt (&nbsp; / \xa0)
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text:
            # Loại bỏ trùng lặp liên tiếp nếu thẻ div bọc thẻ p
            if elements and elements[-1][1] == text:
                continue
            elements.append((tag.name, text))
            
    return elements


def chunk_document_hierarchical(doc_id: str, elements: list):
    """
    Phân tách các phần tử văn bản thành cấu trúc phân cấp (Hierarchical Chunking):
    Chương ➔ Mục ➔ Điều ➔ Đoạn/Khoản/Bảng
    """
    chunks = []
    
    current_chuong_id = None
    current_muc_id = None
    current_dieu_id = None
    
    # Pattern khớp các tiêu đề phân cấp pháp luật Việt Nam
    chuong_pattern = re.compile(r'^(Chương\s+[IVXLCDM\d]+[.:]?\s*.*)', re.IGNORECASE)
    muc_pattern = re.compile(r'^(Mục\s+\d+[.:]?\s*.*)', re.IGNORECASE)
    dieu_pattern = re.compile(r'^(Điều\s+\d+[.:]?\s*.*)', re.IGNORECASE)
    
    chunk_idx = 0
    prev_chunk_id = None
    
    for tag_name, text in elements:
        chunk_idx += 1
        chunk_id = f"{doc_id}_chunk_{chunk_idx}"
        
        chuong_match = chuong_pattern.match(text)
        muc_match = muc_pattern.match(text)
        dieu_match = dieu_pattern.match(text)
        
        if chuong_match:
            chunk_type = "CHAPTER"
            title = text
            parent_id = None  # Cha trực tiếp là Document
            current_chuong_id = chunk_id
            current_muc_id = None
            current_dieu_id = None
        elif muc_match:
            chunk_type = "SECTION"
            title = text
            parent_id = current_chuong_id
            current_muc_id = chunk_id
            current_dieu_id = None
        elif dieu_match:
            chunk_type = "ARTICLE"
            title = text
            if current_muc_id:
                parent_id = current_muc_id
            elif current_chuong_id:
                parent_id = current_chuong_id
            else:
                parent_id = None
            current_dieu_id = chunk_id
        else:
            chunk_type = "CLAUSE"
            title = text[:60] + "..." if len(text) > 60 else text
            if current_dieu_id:
                parent_id = current_dieu_id
            elif current_muc_id:
                parent_id = current_muc_id
            elif current_chuong_id:
                parent_id = current_chuong_id
            else:
                parent_id = None
                
        chunk_obj = {
            "id": chunk_id,
            "doc_id": str(doc_id),
            "type": chunk_type,
            "title": title,
            "text": text,
            "parent_id": parent_id,
            "next_id": None
        }
        
        chunks.append(chunk_obj)
        
        # Liên kết quan hệ NEXT với chunk phía trước
        if len(chunks) > 1:
            chunks[-2]["next_id"] = chunk_id
            
    return chunks


# ==========================================
# BƯỚC 2: TẠO VECTOR NHÚNG (EMBEDDING)
# ==========================================

def generate_embeddings(chunks: list, model_name: str = EMBEDDING_MODEL_NAME):
    """
    Sử dụng SentenceTransformers với mô hình tiếng Việt chuyên dụng trên PyTorch CPU.
    """
    print(f"\n[Bước 2] Đang tải mô hình nhúng HuggingFace: {model_name} (chạy trên CPU)...")
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(model_name, device="cpu")
    
    texts = [c["text"] for c in chunks]
    print(f"Đang tạo vector nhúng cho {len(texts)} phân đoạn chunks...")
    
    # Embed theo batch
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    
    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[idx].tolist()
        
    print("-> Đã tạo xong toàn bộ Vector nhúng (kích thước 384 chiều).")
    return chunks


# ==========================================
# BƯỚC 3 & 4: CẤU HÌNH & NẠP DỮ LIỆU VÀO NEO4J
# ==========================================

def load_data_to_neo4j(metadata_rows, relationship_rows, all_chunks):
    """
    Nạp dữ liệu vào cơ sở dữ liệu Neo4j.
    """
    from neo4j import GraphDatabase
    
    print(f"\n[Bước 3] Kết nối tới Neo4j Database tại {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Kiểm tra kết nối và tạo database nếu được phép
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.run("RETURN 1")
        target_db = NEO4J_DATABASE
    except Exception as e:
        print(f"Lưu ý: Không thể truy cập DB '{NEO4J_DATABASE}' trực tiếp ({e}). Sử dụng DB mặc định 'neo4j'.")
        target_db = "neo4j"
        
    print(f"[Bước 4] Đang nạp dữ liệu vào Neo4j DB '{target_db}'...")
    
    with driver.session(database=target_db) as session:
        # 1. Tạo Constraints / Indexes
        print("  - Tạo Unique Constraints & Indexes...")
        session.run("CREATE CONSTRAINT doc_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
        session.run("CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
        
        # Tạo Vector Index cho Neo4j
        try:
            vector_index_query = """
            CREATE VECTOR INDEX `chunk_vector_index` IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {indexConfig: {
             `vector.similarity_function`: 'cosine',
             `vector.dimensions`: 384
            }}
            """
            session.run(vector_index_query)
            print("  - Đã khởi tạo Vector Index `chunk_vector_index` (Cosine, 384 dim).")
        except Exception as ve:
            print(f"  - Cảnh báo khởi tạo Vector Index: {ve}")

        # 2. Nạp nút Document từ metadata.csv
        print(f"  - Đang nạp {len(metadata_rows)} nút Document...")
        doc_cypher = """
        UNWIND $rows AS row
        MERGE (d:Document {id: toString(row.id)})
        SET d.title = row.title,
            d.so_ky_hieu = row.so_ky_hieu,
            d.ngay_ban_hanh = row.ngay_ban_hanh,
            d.loai_van_ban = row.loai_van_ban,
            d.ngay_co_hieu_luc = row.ngay_co_hieu_luc,
            d.co_quan_ban_hanh = row.co_quan_ban_hanh,
            d.nguoi_ky = row.nguoi_ky,
            d.linh_vuc = row.linh_vuc,
            d.tinh_trang_hieu_luc = row.tinh_trang_hieu_luc
        """
        session.run(doc_cypher, rows=metadata_rows)

        # 3. Nạp Quan hệ giữa các Document từ relationships.csv
        print(f"  - Đang nạp {len(relationship_rows)} quan hệ giữa các tài liệu Document...")
        for rel in relationship_rows:
            doc_id = str(rel["doc_id"])
            other_doc_id = str(rel["other_doc_id"])
            rel_type = rel["relationship_type"].strip().upper()
            
            # Map Cypher rel type an toàn
            rel_cypher = f"""
            MATCH (d1:Document {{id: $doc_id}})
            MATCH (d2:Document {{id: $other_doc_id}})
            MERGE (d1)-[:`{rel_type}`]->(d2)
            """
            session.run(rel_cypher, doc_id=doc_id, other_doc_id=other_doc_id)

        # 4. Nạp nút Chunk & Quan hệ PART_OF
        print(f"  - Đang nạp {len(all_chunks)} nút Chunk và quan hệ [:PART_OF] tới Document...")
        chunk_batch_size = 200
        for i in range(0, len(all_chunks), chunk_batch_size):
            batch = all_chunks[i:i + chunk_batch_size]
            chunk_cypher = """
            UNWIND $batch AS item
            MERGE (c:Chunk {id: item.id})
            SET c.doc_id = item.doc_id,
                c.type = item.type,
                c.title = item.title,
                c.text = item.text,
                c.embedding = item.embedding
            WITH c, item
            MATCH (d:Document {id: item.doc_id})
            MERGE (c)-[:PART_OF]->(d)
            """
            session.run(chunk_cypher, batch=batch)

        # 5. Nạp quan hệ PARENT_OF (Cấu trúc phân cấp Cha-Con)
        print("  - Đang nạp quan hệ phân cấp [:PARENT_OF]...")
        parent_batch = [
            {"child_id": c["id"], "parent_id": c["parent_id"]}
            for c in all_chunks if c["parent_id"] is not None
        ]
        if parent_batch:
            parent_cypher = """
            UNWIND $batch AS item
            MATCH (parent:Chunk {id: item.parent_id})
            MATCH (child:Chunk {id: item.child_id})
            MERGE (parent)-[:PARENT_OF]->(child)
            """
            session.run(parent_cypher, batch=parent_batch)

        # 6. Nạp quan hệ NEXT (Trình tự đọc tuần tự)
        print("  - Đang nạp quan hệ chuỗi trình tự [:NEXT]...")
        next_batch = [
            {"curr_id": c["id"], "next_id": c["next_id"]}
            for c in all_chunks if c["next_id"] is not None
        ]
        if next_batch:
            next_cypher = """
            UNWIND $batch AS item
            MATCH (curr:Chunk {id: item.curr_id})
            MATCH (next_c:Chunk {id: item.next_id})
            MERGE (curr)-[:NEXT]->(next_c)
            """
            session.run(next_cypher, batch=next_batch)

    driver.close()
    print("-> Đã nạp thành công toàn bộ dữ liệu vào Neo4j!")


# ==========================================
# BƯỚC 5: KIỂM TRA VÀ XÁC MINH
# ==========================================

def verify_neo4j_data():
    """
    Xác minh số lượng nút và mối quan hệ trên Neo4j theo đúng yêu cầu Bước 5.
    """
    from neo4j import GraphDatabase
    
    print("\n[Bước 5] Kiểm tra và Xác minh Dữ liệu trên Neo4j Database...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        session = driver.session(database=NEO4J_DATABASE)
        session.run("RETURN 1")
        target_db = NEO4J_DATABASE
    except Exception:
        target_db = "neo4j"
        
    with driver.session(database=target_db) as session:
        # 1. Kiểm tra số nút Document (Kỳ vọng: 15)
        num_docs = session.run("MATCH (d:Document) RETURN count(d) AS cnt").single()["cnt"]
        
        # 2. Kiểm tra số quan hệ giữa Document (Kỳ vọng: 8)
        num_doc_rels = session.run("MATCH (d1:Document)-[r]->(d2:Document) RETURN count(r) AS cnt").single()["cnt"]
        
        # 3. Thống kê Chunk & Quan hệ
        num_chunks = session.run("MATCH (c:Chunk) RETURN count(c) AS cnt").single()["cnt"]
        num_part_of = session.run("MATCH ()-[r:PART_OF]->() RETURN count(r) AS cnt").single()["cnt"]
        num_parent_of = session.run("MATCH ()-[r:PARENT_OF]->() RETURN count(r) AS cnt").single()["cnt"]
        num_next = session.run("MATCH ()-[r:NEXT]->() RETURN count(r) AS cnt").single()["cnt"]
        
        print("=" * 60)
        print("KẾT QUẢ XÁC MINH NEO4J:")
        print(f"  - Số lượng nút Document (Cần 15): {num_docs} {'✓' if num_docs == 15 else '✗'}")
        print(f"  - Số lượng quan hệ giữa Document (Cần 8): {num_doc_rels} {'✓' if num_doc_rels == 8 else '✗'}")
        print(f"  - Số lượng nút Chunk: {num_chunks}")
        print(f"  - Số lượng quan hệ [:PART_OF]: {num_part_of}")
        print(f"  - Số lượng quan hệ [:PARENT_OF]: {num_parent_of}")
        print(f"  - Số lượng quan hệ [:NEXT]: {num_next}")
        print("=" * 60)

    driver.close()


# ==========================================
# CHƯƠNG TRÌNH CHÍNH (MAIN EXECUTION)
# ==========================================

def main():
    print("==========================================================================")
    print("  BÀI THỰC HÀNH 1: CHUNKING, VECTOR EMBEDDINGS & NẠP DỮ LIỆU NEO4J  ")
    print("==========================================================================")
    
    # 1. Đọc metadata.csv
    print(f"\n- Đang đọc siêu dữ liệu từ {METADATA_FILE}...")
    metadata_rows = []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata_rows.append(row)
    print(f"  -> Tìm thấy {len(metadata_rows)} tài liệu.")

    # 2. Đọc relationships.csv
    print(f"- Đang đọc các quan hệ tài liệu từ {RELATIONSHIPS_FILE}...")
    relationship_rows = []
    with open(RELATIONSHIPS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            relationship_rows.append(row)
    print(f"  -> Tìm thấy {len(relationship_rows)} quan hệ giữa các tài liệu.")

    # 3. Đọc content.csv & thực hiện Chunking
    print(f"\n[Bước 1] Đang phân tách văn bản HTML từ {CONTENT_FILE}...")
    all_chunks = []
    sample_demo_done = False
    
    with open(CONTENT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row["id"]
            html_content = row["content_html"]
            
            # Làm sạch HTML
            elements = clean_html_to_elements(html_content)
            
            # Hierarchical Chunking
            doc_chunks = chunk_document_hierarchical(doc_id, elements)
            all_chunks.extend(doc_chunks)
            
            # IN MÀN HÌNH MINH HỌA TRỰC QUAN MẪU PHÂN TÁCH (Yêu cầu Bước 1)
            if not sample_demo_done and len(doc_chunks) > 5:
                sample_demo_done = True
                print("\n" + "*" * 70)
                print(f"MINH HỌA KẾT QUẢ PHÂN TÁCH MẪU (Document ID: {doc_id}):")
                print("*" * 70)
                for c in doc_chunks[:10]:
                    print(f"  • ID: {c['id']:<18} | Loại: {c['type']:<10} | Cha: {str(c['parent_id']):<18}")
                    print(f"    Nội dung sạch: {c['text'][:100]}...\n")
                print("*" * 70 + "\n")

    print(f"-> Tổng số phân đoạn Chunks được tạo ra: {len(all_chunks)}")

    # 4. Tạo Vector Nhúng (Bước 2)
    all_chunks = generate_embeddings(all_chunks)

    # 5. Cấu hình & Nạp vào Neo4j (Bước 3 & 4)
    load_data_to_neo4j(metadata_rows, relationship_rows, all_chunks)

    # 6. Kiểm tra & Xác minh (Bước 5)
    verify_neo4j_data()

    print("\n✓ HOÀN THÀNH BÀI THỰC HÀNH 1 THÀNH CÔNG!")


if __name__ == "__main__":
    main()
