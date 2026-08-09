"""
Giao diện Web Streamlit cho RAG Agent System - Buổi 07.

Chỉ sử dụng các hàm public từ rag.py. Không viết lại logic RAG trong app.py.
"""

from pathlib import Path
import streamlit as st

from rag import (
    BASE_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_STORAGE_DIR,
    VALID_STRATEGIES,
    load_config,
    get_collection_name,
    get_chroma_client,
    index_chunks,
    query_rag,
    format_page_str,
)

# Page configuration
st.set_page_config(
    page_title="RAG Agent System - Buổi 07",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State initialization
if "last_index_res" not in st.session_state:
    st.session_state["last_index_res"] = None
if "last_query_res" not in st.session_state:
    st.session_state["last_query_res"] = None

# Load configuration safely
try:
    config = load_config()
    has_api_key = bool(config["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Lỗi đọc cấu hình .env: {e}")
    st.stop()

# ==============================================================================
# SIDEBAR
# ==============================================================================
st.sidebar.title("⚙️ Cấu Hình RAG Pipeline")

strategy = st.sidebar.selectbox(
    "Chiến lược Chunking (Strategy):",
    options=sorted(list(VALID_STRATEGIES)),
    index=sorted(list(VALID_STRATEGIES)).index("hierarchical") if "hierarchical" in VALID_STRATEGIES else 0
)

top_k = st.sidebar.slider(
    "Số lượng kết quả truy xuất (Top K):",
    min_value=1,
    max_value=10,
    value=config.get("DEFAULT_TOP_K", 5)
)

st.sidebar.divider()
st.sidebar.subheader("📊 Trạng Thái Hệ Thống (Read-only)")

# Read-only collection status
coll_name = get_collection_name(strategy, config["GEMINI_EMBEDDING_MODEL"], config["GEMINI_EMBEDDING_DIM"])
coll_exists = False
rec_count = 0

try:
    if DEFAULT_STORAGE_DIR.exists():
        client = get_chroma_client(DEFAULT_STORAGE_DIR)
        existing_colls = [c.name for c in client.list_collections()]
        if coll_name in existing_colls:
            coll_exists = True
            coll = client.get_collection(name=coll_name, embedding_function=None)
            rec_count = coll.count()
except Exception as e:
    st.sidebar.error(f"Lỗi đọc trạng thái ChromaDB: {e}")

st.sidebar.write(f"**GEMINI_API_KEY:** {'✅ Có' if has_api_key else '❌ Thiếu'}")
st.sidebar.write(f"**Embedding Model:** `{config['GEMINI_EMBEDDING_MODEL']}`")
st.sidebar.write(f"**Dimension:** `{config['GEMINI_EMBEDDING_DIM']}`")
st.sidebar.write(f"**Generation Model:** `{config['GEMINI_GENERATION_MODEL']}`")
st.sidebar.write(f"**Collection Name:** `{coll_name}`")
st.sidebar.write(f"**Collection Tồn Tại:** {'✅ Có' if coll_exists else '❌ Chưa'}")
st.sidebar.write(f"**Số Chunk Trong DB:** `{rec_count}`")
st.sidebar.write(f"**RAG_MAX_DISTANCE:** `{config['RAG_MAX_DISTANCE']}`")

# ==============================================================================
# MAIN PAGE
# ==============================================================================
st.title("🤖 RAG Agent System - Buổi 07")
st.caption("Hệ thống Retrieval-Augmented Generation hoàn chỉnh tích hợp Gemini API, ChromaDB Persistent Store & Citation Mapping.")

tab1, tab2 = st.tabs(["❓ Truy Vấn Hỏi Đáp", "📥 Indexing Dữ Liệu"])

# ------------------------------------------------------------------------------
# TAB 1: TRUY VẤN HỎI ĐÁP
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("💬 Đặt Câu Hỏi Nghiệp Vụ")
    
    question_input = st.text_area(
        "Nhập câu hỏi của bạn (tối đa 2000 ký tự):",
        placeholder="Ví dụ: Quy định về kiểm soát và quản lý rủi ro ngân hàng như thế nào?",
        height=100
    )
    
    btn_query = st.button("🚀 Gửi Câu Hỏi", type="primary", use_container_width=True)

    if btn_query:
        if not question_input.strip():
            st.warning("⚠️ Vui lòng nhập nội dung câu hỏi trước khi gửi.")
        elif not has_api_key:
            st.error("❌ Thiếu GEMINI_API_KEY trong file `.env`. Hãy bổ sung API key để thực hiện truy vấn.")
        elif not coll_exists:
            st.warning(f"⚠️ Collection `{coll_name}` chưa tồn tại. Hãy chuyển sang tab 'Indexing Dữ Liệu' để khởi tạo.")
        elif rec_count == 0:
            st.warning(f"⚠️ Collection `{coll_name}` hiện tại rỗng (0 record). Hãy chạy lệnh Index dữ liệu trước.")
        else:
            with st.spinner("🔍 Đang tìm kiếm bằng chứng và tổng hợp câu trả lời từ Gemini LLM..."):
                try:
                    res = query_rag(
                        question=question_input,
                        strategy=strategy,
                        top_k=top_k,
                        config=config,
                        storage_dir=DEFAULT_STORAGE_DIR
                    )
                    st.session_state["last_query_res"] = res
                except Exception as e:
                    cleaned_err = str(e).split("GEMINI_API_KEY")[0]
                    st.error(f"❌ Lỗi khi thực hiện truy vấn: {cleaned_err}")

    # Display Query Results
    res = st.session_state.get("last_query_res")
    if res:
        st.divider()
        
        status_code = res.get("status")
        if status_code == "answered":
            st.success("✅ **Đã tìm thấy bằng chứng và tổng hợp câu trả lời thành công.**")
        elif status_code == "insufficient_evidence":
            st.warning("⚠️ **Không tìm thấy đủ thông tin liên quan trong tài liệu đã cung cấp.** (Tất cả bằng chứng truy xuất đều vượt ngưỡng RAG_MAX_DISTANCE).")
        elif status_code == "retrieval_only":
            st.info("ℹ️ **Đã truy xuất được nguồn tham khảo nhưng chưa thể tổng hợp câu trả lời.**")

        # Answer Section
        st.markdown("### 📝 Câu Trả Lời")
        st.markdown(res["answer"])

        # Warnings Section
        if res.get("warnings"):
            for w in res["warnings"]:
                st.warning(f"⚠️ {w}")

        # Citations Section
        if res.get("citations"):
            st.markdown("#### 📌 Danh Sách Trích Dẫn (Citations)")
            for cit in res["citations"]:
                page_text = format_page_str(cit["page_start"], cit["page_end"])
                st.write(f"- **[{cit['evidence_id']}]** `{cit['source']}` – {page_text} (Chunk: `{cit['chunk_id']}`)")

        # Evidence Section
        st.divider()
        st.markdown("### 📚 Nguồn Tham Khảo (Evidence)")
        st.caption("Khoảng cách Cosine Distance thể hiện độ tương đồng vector (Distance càng thấp càng liên quan). Ngưỡng chấp nhận: `RAG_MAX_DISTANCE <= 0.45`.")

        evidences = res.get("evidence", [])
        if not evidences:
            st.info("Chưa có bằng chứng nào được truy xuất.")
        else:
            for ev in evidences:
                page_text = format_page_str(ev["page_start"], ev["page_end"])
                status_tag = "✅ HỢP LỆ" if ev["accepted"] else "❌ BỎ QUA (VƯỢT THRESHOLD)"
                
                expander_title = f"{status_tag} | {ev['source']} – {page_text} – Chunk: {ev['chunk_id']} (Distance: {ev['distance']})"
                
                with st.expander(expander_title, expanded=ev["accepted"]):
                    col_a, col_b, col_c = st.columns(3)
                    col_a.write(f"**Bằng chứng ID:** `{ev['evidence_id']}`")
                    col_b.write(f"**Trạng thái Gate:** {'Đạt ngưỡng' if ev['accepted'] else 'Vượt ngưỡng RAG_MAX_DISTANCE'}")
                    col_c.write(f"**Cosine Distance:** `{ev['distance']}`")
                    
                    st.markdown("**Nội dung Chunk:**")
                    st.text(ev["text"])

# ------------------------------------------------------------------------------
# TAB 2: INDEXING DỮ LIỆU
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("📥 Index Dữ Liệu Chunks Vào ChromaDB")
    st.write(f"Thực hiện đọc các file JSON từ `rag_foundation/buoi_05/output/chunks/` thuộc strategy **`{strategy}`**, tạo embeddings bằng Gemini API và nạp vào ChromaDB.")

    if not has_api_key:
        st.error("❌ Thiếu GEMINI_API_KEY trong file `.env`. Hãy bổ sung API key để thực hiện Indexing.")

    reset_chk = st.checkbox("🔄 Reset (Xóa và tạo lại) collection trước khi index", value=False)
    btn_index = st.button("⚡ Thực Hiện Indexing Dữ Liệu", type="secondary", use_container_width=True)

    if btn_index:
        if not has_api_key:
            st.error("❌ Không thể chạy Indexing do thiếu GEMINI_API_KEY trong file `.env`.")
        else:
            with st.spinner(f"⏳ Đang tạo vector embedding cho strategy '{strategy}' và nạp vào ChromaDB (Có thể mất từ 1-2 phút do rate limit pacing)..."):
                try:
                    index_res = index_chunks(
                        input_path=DEFAULT_INPUT_DIR,
                        strategy=strategy,
                        config=config,
                        reset=reset_chk,
                        storage_dir=DEFAULT_STORAGE_DIR
                    )
                    st.session_state["last_index_res"] = index_res
                    st.success("🎉 **Indexing dữ liệu thành công!**")
                    st.rerun()
                except Exception as e:
                    cleaned_err = str(e).split("GEMINI_API_KEY")[0]
                    st.error(f"❌ Lỗi khi thực hiện Indexing: {cleaned_err}")

    # Display Last Index Result
    last_idx = st.session_state.get("last_index_res")
    if last_idx:
        st.info("📊 **Kết Quả Indexing Gần Nhất:**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Collection", last_idx["collection_name"])
        col2.metric("Số Chunk Vừa Index", last_idx["indexed_count"])
        col3.metric("Tổng Record Trong DB", last_idx["total_in_collection"])
