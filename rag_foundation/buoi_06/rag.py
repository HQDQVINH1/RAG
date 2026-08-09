import os
import glob
import json
import sqlite3
from dotenv import load_dotenv

# Path to buoi_05 chunks directory
CHUNKS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "buoi_05", "output", "chunks")
)

def get_gemini_client():
    """Lấy client Gemini từ google-genai nếu có GEMINI_API_KEY."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def embed_text(client, text):
    """Tạo vector embedding (384 chiều) bằng Gemini."""
    if not client:
        return None
    try:
        from google.genai import types
        res = client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=384)
        )
        return res.embeddings[0].values
    except Exception:
        return None

def get_db():
    """Kết nối PostgreSQL (rag_db), nếu thất bại thì chuyển sang SQLite local (.db)."""
    load_dotenv()
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "rag_db")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "")

    try:
        import psycopg
        conn_str = f"host={pg_host} port={pg_port} dbname={pg_db} user={pg_user}"
        if pg_pass:
            conn_str += f" password={pg_pass}"
        conn = psycopg.connect(conn_str, autocommit=True)
        db_type = "PostgreSQL"
    except Exception:
        os.makedirs("storage", exist_ok=True)
        db_path = os.path.abspath("storage/rag_storage.db")
        conn = sqlite3.connect(db_path)
        db_type = "SQLite (.db)"

    # Khởi tạo bảng nếu chưa có
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                source TEXT,
                strategy TEXT,
                page_start INTEGER,
                page_end INTEGER,
                text TEXT
            )
        """)
        if db_type == "SQLite (.db)":
            conn.commit()

    return conn, db_type

def get_chroma_collection():
    """Khởi tạo ChromaDB PersistentClient lưu tại storage/chroma/."""
    import chromadb
    os.makedirs("storage/chroma", exist_ok=True)
    chroma_client = chromadb.PersistentClient(path="storage/chroma")
    return chroma_client.get_or_create_collection(name="rag_chunks")

def index():
    """
    Đọc toàn bộ file JSON trong buoi_05/output/chunks/,
    tạo embedding (384 chiều) và lưu vào Database + ChromaDB.
    """
    conn, db_type = get_db()
    collection = get_chroma_collection()
    client = get_gemini_client()

    json_files = glob.glob(os.path.join(CHUNKS_DIR, "*.json"))
    total_indexed = 0
    sources = set()

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        chunks = data.get("chunks", [])
        if not chunks:
            continue

        for item in chunks:
            chunk_id = item.get("chunk_id")
            text = item.get("text", "")
            source = item.get("source", "")
            strategy = item.get("strategy", "")
            page_start = item.get("page_start", 0)
            page_end = item.get("page_end", 0)

            if not chunk_id or not text:
                continue

            sources.add(source)

            # 1. Tạo embedding bằng Gemini (384 chiều)
            emb = embed_text(client, text)

            # 2. Lưu text vào PostgreSQL hoặc SQLite
            with conn.cursor() as cur:
                if db_type == "PostgreSQL":
                    cur.execute("""
                        INSERT INTO chunks (chunk_id, source, strategy, page_start, page_end, text)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET text = EXCLUDED.text
                    """, (chunk_id, source, strategy, page_start, page_end, text))
                else:
                    cur.execute("""
                        INSERT OR REPLACE INTO chunks (chunk_id, source, strategy, page_start, page_end, text)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (chunk_id, source, strategy, page_start, page_end, text))
                    conn.commit()

            # 3. Lưu embedding vào ChromaDB
            meta = {"source": source, "strategy": strategy, "page_start": page_start, "page_end": page_end}
            if emb:
                collection.upsert(ids=[chunk_id], embeddings=[emb], documents=[text], metadatas=[meta])
            else:
                # Nếu không có Gemini API Key, ChromaDB tự động dùng embedding mặc định (MiniLM-L6-v2 384d)
                collection.upsert(ids=[chunk_id], documents=[text], metadatas=[meta])

            total_indexed += 1

    conn.close()
    return {
        "status": "success",
        "indexed_chunks": total_indexed,
        "document_count": len(sources),
        "storage_type": db_type
    }

def ask(question, k=3):
    """
    Nhận câu hỏi, tìm kiếm top-k chunk phù hợp từ ChromaDB,
    truy vấn text từ DB và dùng Gemini sinh câu trả lời.
    """
    collection = get_chroma_collection()
    conn, db_type = get_db()
    client = get_gemini_client()

    # 1. Embedding câu hỏi với Gemini (384 chiều) nếu có client
    query_emb = embed_text(client, question)

    # 2. Retrieval top-k từ ChromaDB
    if query_emb:
        results = collection.query(query_embeddings=[query_emb], n_results=k)
    else:
        results = collection.query(query_texts=[question], n_results=k)

    retrieved_ids = results.get("ids", [[]])[0]
    retrieved_chunks = []

    # 3. Lấy text tương ứng từ Database (PostgreSQL / SQLite)
    for cid in retrieved_ids:
        with conn.cursor() as cur:
            if db_type == "PostgreSQL":
                cur.execute("SELECT chunk_id, source, strategy, page_start, page_end, text FROM chunks WHERE chunk_id = %s", (cid,))
            else:
                cur.execute("SELECT chunk_id, source, strategy, page_start, page_end, text FROM chunks WHERE chunk_id = ?", (cid,))
            row = cur.fetchone()
            if row:
                retrieved_chunks.append({
                    "chunk_id": row[0],
                    "source": row[1],
                    "strategy": row[2],
                    "page_start": row[3],
                    "page_end": row[4],
                    "text": row[5]
                })

    conn.close()

    # 4. Nếu thiếu GEMINI_API_KEY: trả về kết quả retrieval, không gọi LLM
    if not client:
        return {
            "question": question,
            "answer": "(Không có GEMINI_API_KEY - Hiển thị kết quả tìm kiếm Retrieval)",
            "chunks": retrieved_chunks
        }

    # 5. Gửi cho Gemini (gemini-flash-lite-latest) để sinh câu trả lời
    context_str = "\n\n---\n\n".join([f"[{c['source']} - Trang {c['page_start']}]\n{c['text']}" for c in retrieved_chunks])
    prompt = f"""Dựa vào các đoạn văn bản trích dẫn dưới đây để trả lời câu hỏi. Trả lời chính xác, ngắn gọn.

Bối cảnh:
---
{context_str}
---

Câu hỏi: {question}
Trả lời:"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt
        )
        answer = response.text
    except Exception as e:
        answer = f"Lỗi gọi Gemini LLM: {str(e)}"

    return {
        "question": question,
        "answer": answer,
        "chunks": retrieved_chunks
    }

def status():
    """Trả về số lượng document, số lượng chunk và loại Database lưu trữ."""
    conn, db_type = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT source) FROM chunks")
        row = cur.fetchone()
        chunk_count = row[0] if row else 0
        doc_count = row[1] if row else 0
    conn.close()

    return {
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "storage_type": db_type
    }
