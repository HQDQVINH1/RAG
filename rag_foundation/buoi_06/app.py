import os
import streamlit as st
from dotenv import load_dotenv
import rag

# Configuration
load_dotenv()
st.set_page_config(
    page_title="RAG Demo - Buổi 06",
    page_icon="🔍",
    layout="wide"
)

# --- SIDEBAR ---
st.sidebar.title("🛠️ Trạng thái Hệ thống")

# 1. Gemini API Key Status
api_key = os.getenv("GEMINI_API_KEY", "").strip()
if api_key:
    st.sidebar.success("🔑 Gemini API Key: **Đã cấu hình**")
else:
    st.sidebar.warning("⚠️ Gemini API Key: **Thiếu** (Chỉ cho phép Retrieval)")

# 2. Database Status & Info
status_data = rag.status()
storage_type = status_data.get("storage_type", "Unknown")

if "PostgreSQL" in storage_type:
    st.sidebar.success("🐘 PostgreSQL: **Đã kết nối** (`rag_db`)")
else:
    st.sidebar.info(f"📁 Database: **{storage_type}**")

# 3. ChromaDB Status
st.sidebar.success("📦 ChromaDB: **Embedded Local** (`storage/chroma/`)")

st.sidebar.divider()
st.sidebar.markdown(f"📄 **Số lượng Document:** `{status_data.get('doc_count', 0)}`")
st.sidebar.markdown(f"🧩 **Tổng số Chunks:** `{status_data.get('chunk_count', 0)}`")


# --- MAIN AREA ---
st.title("📚 RAG Search & Question Answering System")
st.caption("Project Demo Workshop RAG Foundation - Buổi 06")

# Nút Indexing
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🚀 Nút Indexing Data", type="primary", use_container_width=True):
        with st.spinner("Đang đọc JSON, tạo embedding và lưu trữ..."):
            res = rag.index()
            st.success(f"Đã index thành công {res.get('indexed_chunks', 0)} chunks vào {res.get('storage_type')}!")
            st.rerun()

st.divider()

# Input câu hỏi và tham số Top-K
question = st.text_input("❓ Nhập câu hỏi của bạn:", placeholder="Ví dụ: Quy định về cơ cấu lại thời hạn trả nợ như thế nào?")
top_k = st.slider("🎯 Tham số Top-K (Số lượng chunk trích xuất):", min_value=1, max_value=10, value=3)

if st.button("🔎 Gửi câu hỏi", use_container_width=True) and question.strip():
    with st.spinner("Đang thực hiện Retrieval & Sinh câu trả lời..."):
        result = rag.ask(question, k=top_k)

        # Hiển thị câu trả lời (Answer)
        st.subheader("💡 Câu trả lời (Answer):")
        st.info(result.get("answer", ""))

        # Hiển thị kết quả Top-K Chunks
        retrieved_chunks = result.get("chunks", [])
        st.subheader(f"📋 Top-{len(retrieved_chunks)} Chunks được trích xuất:")

        if not retrieved_chunks:
            st.warning("Không tìm thấy chunk phù hợp.")
        else:
            for i, chunk in enumerate(retrieved_chunks, 1):
                with st.expander(f"Chunk #{i} | Nguồn: {chunk.get('source')} (Trang {chunk.get('page_start')}-{chunk.get('page_end')})"):
                    st.markdown(f"**ID:** `{chunk.get('chunk_id')}` | **Strategy:** `{chunk.get('strategy')}`")
                    st.text_area(
                        label=f"Nội dung Chunk #{i}:",
                        value=chunk.get("text", ""),
                        height=160,
                        key=f"chunk_view_{i}"
                    )
