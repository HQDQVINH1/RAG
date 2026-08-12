"""
Giao diện Web Streamlit cho Hệ thống Multi-hop Graph RAG - Buổi 11
"""

import os
import sys
import time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Cấu hình UTF-8 cho Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import core RAG engine từ lab2_multihop_graph_rag.py
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from lab2_multihop_graph_rag import MultiHopGraphRAG

# Page Configuration
st.set_page_config(
    page_title="Multi-hop Graph RAG | Buổi 11",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Vanilla CSS)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        padding: 24px 32px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .main-header p {
        color: #94a3b8;
        margin-top: 8px;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    .status-card {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 10px;
        padding: 12px 16px;
        color: #065f46;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .badge-relationship {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        margin-right: 6px;
    }
    .chunk-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .chunk-box-multihop {
        border-left-color: #8b5cf6;
        background: #faf5ff;
    }
    .stat-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag_engine():
    """Khởi tạo duy nhất 1 lần RAG engine."""
    engine = MultiHopGraphRAG()
    engine.initialize()
    return engine

try:
    rag_engine = get_rag_engine()
    engine_error = None
except Exception as e:
    rag_engine = None
    engine_error = str(e)

# ==============================================================================
# SIDEBAR
# ==============================================================================
st.sidebar.title("⚙️ Cấu hình Hệ thống")

if rag_engine and not engine_error:
    st.sidebar.markdown("""
    <div class="status-card">
        🟢 Neo4j: 15 Văn bản | 8,739 Chunks
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.error(f"Lỗi kết nối: {engine_error}")

st.sidebar.subheader("🔍 Tham số Truy xuất")

top_k = st.sidebar.slider(
    "Số lượng Chunk trực tiếp (Top-K):",
    min_value=1, max_value=10, value=3,
    help="Số lượng phân đoạn văn bản thu thập từ Vector Search trực tiếp"
)

num_hops = st.sidebar.slider(
    "Số bước nhảy Đồ thị (Num Hops):",
    min_value=0, max_value=3, value=1,
    help="0: Chỉ lấy ngữ cảnh trực tiếp. 1-3: Mở rộng sang các văn bản liên quan"
)

max_chunks_per_doc = st.sidebar.slider(
    "Số Chunk mỗi văn bản liên quan:",
    min_value=1, max_value=5, value=2,
    help="Số phân đoạn tối đa trích xuất từ mỗi văn bản ở bước nhảy đa bước"
)

allowed_relationships = st.sidebar.multiselect(
    "Mối quan hệ cho phép duyệt:",
    options=["CAN_CU", "THAY_THE", "HOP_NHAT", "SUA_DOI_BO_SUNG", "VAN_BAN_BO_SUNG"],
    default=["CAN_CU", "THAY_THE", "HOP_NHAT", "SUA_DOI_BO_SUNG", "VAN_BAN_BO_SUNG"],
    help="Các loại liên kết giữa văn bản luật được phép duyệt"
)

st.sidebar.divider()
st.sidebar.subheader("🤖 Tham số Mô hình LLM")

model_choice = st.sidebar.selectbox(
    "Mô hình Gemini:",
    options=["gemini-2.5-flash", "gemini-3.5-flash-lite"],
    index=1
)


# ==============================================================================
# MAIN PAGE HEADER
# ==============================================================================
st.markdown("""
<div class="main-header">
    <h1>⚖️ Hệ thống Multi-hop Graph RAG - Hỏi Đáp Pháp Luật</h1>
    <p>Bài thực hành 2 - Buổi 11 | Kết hợp Tìm kiếm Vector (MSMARCO), Đồ thị Tri thức Đa bước Neo4j và Gemini 2.5 Flash LLM</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Hỏi đáp Tương tác (QA)",
    "📊 So sánh Đa bước (0 Hop vs 1 Hop)",
    "📝 5 Câu hỏi Kiểm thử Đề bài",
    "📊 Khám phá Đồ thị Tri thức"
])


# ==============================================================================
# TAB 1: HỎI ĐÁP TƯƠNG TÁC (QA)
# ==============================================================================
with tab1:
    st.subheader("💬 Hỏi Đáp Pháp Luật với Graph RAG Đa bước")
    st.caption("Nhập câu hỏi tra cứu luật. Hệ thống sẽ tự động thực hiện Vector Search, duyệt Đồ thị N bước nhảy để tìm văn bản liên quan và sinh câu trả lời bằng Gemini.")

    st.markdown("**Gợi ý 5 câu hỏi kiểm thử mẫu nhanh (Đề bài Bước 4):**")
    
    if "preset_question" not in st.session_state:
        st.session_state["preset_question"] = ""

    col_q1, col_q2, col_q3 = st.columns(3)
    if col_q1.button("📌 Q1: NĐ 46/2023 thay thế văn bản nào?", use_container_width=True):
        st.session_state["preset_question"] = "Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào, và nghị định bị thay thế đó có nội dung gì nổi bật về kinh doanh bảo hiểm?"
    if col_q2.button("📌 Q2: Văn bản 52/VBHN hợp nhất từ đâu?", use_container_width=True):
        st.session_state["preset_question"] = "Văn bản hợp nhất số 52/VBHN-NHNN được hợp nhất từ văn bản nào, và quy định về hồ sơ, thủ tục cấp giấy phép lần đầu của ngân hàng thương mại gồm những tài liệu gì?"
    if col_q3.button("📌 Q3: TT 01/2025 sửa đổi bổ sung bởi đâu?", use_container_width=True):
        st.session_state["preset_question"] = "Thông tư số 01/2025/TT-NHNN quy định về cấp giấy phép quỹ tín dụng nhân dân được sửa đổi, bổ sung bởi văn bản nào, và những nội dung sửa đổi bổ sung chính là gì?"

    col_q4, col_q5 = st.columns(2)
    if col_q4.button("📌 Q4: Thông tư 41/2016 căn cứ vào luật nào?", use_container_width=True):
        st.session_state["preset_question"] = "Thông tư số 41/2016/TT-NHNN về tỷ lệ an toàn vốn của ngân hàng căn cứ vào luật nào, và luật đó quy định chức năng nhiệm vụ của cơ quan nào?"
    if col_q5.button("📌 Q5: Quy định vận chuyển tiền mặt NHNN?", use_container_width=True):
        st.session_state["preset_question"] = "Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"

    question = st.text_area(
        "Nhập câu hỏi pháp luật:",
        value=st.session_state["preset_question"],
        placeholder="Ví dụ: Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào, và nghị định bị thay thế đó có nội dung gì nổi bật?",
        height=100
    )

    if st.button("🚀 Gửi câu hỏi", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Vui lòng nhập nội dung câu hỏi!")
        elif not rag_engine:
            st.error("Chưa thể kết nối tới Neo4j hoặc Gemini API!")
        else:
            with st.spinner(f"Đang thực hiện Vector Search + Duyệt Đồ thị ({num_hops} Hops) & gọi Gemini LLM..."):
                res = rag_engine.generate_answer_with_llm(question, hops=num_hops, top_k=top_k)
                ret_data = res["retrieved_data"]

            st.markdown("### 💬 Câu Trả Lời Từ Gemini LLM:")
            st.info(res["answer"])

            st.caption(f"⏱️ **Thời gian xử lý**: Retrieval: `{res['retrieval_time_sec']}s` | LLM: `{res['llm_time_sec']}s` | Tổng cộng: `{round(res['retrieval_time_sec'] + res['llm_time_sec'], 3)}s`")

            st.divider()

            # Hiển thị chi tiết ngữ cảnh đã thu thập
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown(f"#### 📌 Phân đoạn trực tiếp Vector Search (Top-{top_k}):")
                for idx, c in enumerate(ret_data["direct_chunks"], start=1):
                    st.markdown(f"""
                    <div class="chunk-box">
                        <strong>[{idx}] {c['doc_title']}</strong><br/>
                        <span style="font-size:0.82rem; color:#64748b;">ID: {c['chunk_id']} | Score: {c['similarity_score']:.4f}</span>
                        <p style="margin-top:6px; font-size:0.9rem;">{c['chunk_text']}</p>
                    </div>
                    """, unsafe_allow_html=True)

            with col_right:
                st.markdown(f"#### 🌐 Phân đoạn đa bước từ Đồ thị ({num_hops} Hops):")
                if not ret_data["multihop_chunks"]:
                    st.write("*(Chưa có hoặc không tìm thấy phân đoạn liên quan đa bước nào)*")
                else:
                    for idx, mc in enumerate(ret_data["multihop_chunks"], start=1):
                        st.markdown(f"""
                        <div class="chunk-box chunk-box-multihop">
                            <strong>[Hop-{idx}] {mc['doc_title']}</strong><br/>
                            <span style="font-size:0.82rem; color:#7c3aed;">ID: {mc['chunk_id']} | Từ Doc {mc['doc_id']}</span>
                            <p style="margin-top:6px; font-size:0.9rem;">{mc['chunk_text']}</p>
                        </div>
                        """, unsafe_allow_html=True)


# ==============================================================================
# TAB 2: SO SÁNH ĐA BƯỚC (0 HOP VS 1 HOP)
# ==============================================================================
with tab2:
    st.subheader("📊 So Sánh Hiệu Quả: 0-Hop (Vector) vs 1-Hop (Graph Multi-hop)")
    st.caption("Chạy cùng 1 câu hỏi ở 2 chế độ để thấy rõ sự khác biệt khi thu thập thêm văn bản liên quan qua liên kết đồ thị.")

    cmp_question = st.text_input(
        "Câu hỏi so sánh:",
        value="Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"
    )

    if st.button("⚡ Chạy so sánh 0-Hop vs 1-Hop", use_container_width=True):
        if not cmp_question.strip():
            st.warning("Vui lòng nhập câu hỏi!")
        elif not rag_engine:
            st.error("Chưa thể kết nối RAG Engine!")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🔹 Chế độ 0-Hop (Chỉ Vector Search)")
                with st.spinner("Đang chạy 0-Hop..."):
                    res_0 = rag_engine.generate_answer_with_llm(cmp_question, hops=0, top_k=top_k)
                st.info(res_0["answer"])
                st.caption(f"⏱️ Retrieval: `{res_0['retrieval_time_sec']}s` | LLM: `{res_0['llm_time_sec']}s` | Chunks: `{len(res_0['retrieved_data']['direct_chunks'])}`")

            time.sleep(2)

            with col2:
                st.markdown("### 🟣 Chế độ 1-Hop (Graph Multi-hop)")
                with st.spinner("Đang chạy 1-Hop..."):
                    res_1 = rag_engine.generate_answer_with_llm(cmp_question, hops=1, top_k=top_k)
                st.success(res_1["answer"])
                st.caption(f"⏱️ Retrieval: `{res_1['retrieval_time_sec']}s` | LLM: `{res_1['llm_time_sec']}s` | Chunks: `{len(res_1['retrieved_data']['direct_chunks']) + len(res_1['retrieved_data']['multihop_chunks'])}`")


# ==============================================================================
# TAB 3: 5 CÂU HỎI KIỂM THỬ ĐỀ BÀI
# ==============================================================================
with tab3:
    st.subheader("📝 5 Câu Hỏi Kiểm Thử Đề Bài Bài 2 - Buổi 11")
    
    test_suite = [
        "1. Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào, và nghị định bị thay thế đó có nội dung gì nổi bật về kinh doanh bảo hiểm?",
        "2. Văn bản hợp nhất số 52/VBHN-NHNN được hợp nhất từ văn bản nào, và quy định về hồ sơ, thủ tục cấp giấy phép lần đầu của ngân hàng thương mại gồm những tài liệu gì?",
        "3. Thông tư số 01/2025/TT-NHNN quy định về cấp giấy phép quỹ tín dụng nhân dân được sửa đổi, bổ sung bởi văn bản nào, và những nội dung sửa đổi bổ sung chính là gì?",
        "4. Thông tư số 41/2016/TT-NHNN về tỷ lệ an toàn vốn của ngân hàng căn cứ vào luật nào, và luật đó quy định chức năng nhiệm vụ của cơ quan nào?",
        "5. Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"
    ]

    selected_test_q = st.selectbox("Chọn câu hỏi kiểm thử:", test_suite)

    if st.button("▶️ Chạy kiểm thử câu hỏi chọn sẵn", type="primary"):
        clean_q = selected_test_q.split(". ", 1)[1] if ". " in selected_test_q else selected_test_q
        with st.spinner("Đang xử lý truy vấn Multi-hop RAG..."):
            res_test = rag_engine.generate_answer_with_llm(clean_q, hops=num_hops, top_k=top_k)
        st.markdown("### 💬 Kết quả từ Gemini LLM:")
        st.info(res_test["answer"])


# ==============================================================================
# TAB 4: KHÁM PHÁ ĐỒ THỊ TRI THỨC
# ==============================================================================
with tab4:
    st.subheader("📊 Thống Kê Cơ Sở Dữ Liệu Đồ Thị Neo4j")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">15</div>
            <div class="stat-label">Tài liệu (Document Nodes)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">8,739</div>
            <div class="stat-label">Phân đoạn (Chunk Nodes)</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">384</div>
            <div class="stat-label">Chiều Vector Embedding</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">8</div>
            <div class="stat-label">Liên kết Văn bản Luật</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🕸️ Các Loại Quan Hệ Đồ Thị Trong Hệ Thống:")
    st.markdown("""
    - `[:PART_OF]`: Liên kết trực tiếp phân đoạn Chunk về Nút Document (8,739 quan hệ).
    - `[:PARENT_OF]`: Cấu trúc phân cấp Chương ➔ Mục ➔ Điều ➔ Khoản (8,387 quan hệ).
    - `[:NEXT]`: Chuỗi đọc tuần tự giữa các đoạn văn bản (8,724 quan hệ).
    - `[:CAN_CU]`, `[:THAY_THE]`, `[:HOP_NHAT]`, `[:SUA_DOI_BO_SUNG]`: Các quan hệ liên kết pháp lý giữa các văn bản luật.
    """)
