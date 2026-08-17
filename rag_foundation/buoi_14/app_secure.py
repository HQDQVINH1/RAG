#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Web App cho Buổi 15: RBAC Secure RAG Search
Chạy ứng dụng:
    streamlit run app_secure.py
"""

import os
import sys
import json
import pandas as pd
import streamlit as st
from pathlib import Path

# Thêm project root vào sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.secure_retriever import SecureRetriever
from src.config import ROLES

# 1. Cấu hình Trang Streamlit
st.set_page_config(
    page_title="RBAC Secure RAG — Buổi 15",
    page_icon="🛡️",
    layout="wide"
)

# 2. Khởi tạo Cached Secure Retriever (chỉ load 1 lần)
@st.cache_resource
def get_secure_retriever():
    corpus_csv = project_root / "data" / "processed" / "chunks_secure.csv"
    cache_dir = project_root / "cache"
    if not corpus_csv.exists():
        st.error(f"Không tìm thấy file corpus bảo mật tại `{corpus_csv}`. Vui lòng chạy `python scripts/assign_security_tags.py` trước.")
        st.stop()
    return SecureRetriever(str(corpus_csv), str(cache_dir))

# Header ứng dụng
st.title("🛡️ RBAC Secure RAG Search — Buổi 15")
st.caption("Hệ thống Tìm kiếm An toàn: Kiểm soát Truy cập theo Vai trò (Role-Based Access Control) ở mức Dữ liệu và Graph")

st.markdown("---")

# 3. Sidebar Cấu hình & Chọn Vai trò (Impersonation)
with st.sidebar:
    st.header("👤 Phân quyền Người dùng (RBAC)")
    
    selected_roles = st.multiselect(
        "Vai trò của bạn (Your Roles):",
        options=ROLES,
        default=["Guest"],
        help="Lựa chọn một hoặc nhiều vai trò để đóng vai (Impersonate) truy vấn hệ thống"
    )
    
    if not selected_roles:
        st.warning("⚠️ Vui lòng chọn ít nhất 1 vai trò để thực hiện tìm kiếm!")
    
    st.markdown("---")
    st.header("⚙️ Cấu hình Retrieval")
    
    method_display = st.radio(
        "Phương pháp Retrieval (Method):",
        options=["BM25", "Dense", "Hybrid", "Hybrid + Rerank", "Graph (Neo4j)"],
        index=3,
        help="Thử nghiệm lọc bảo mật trên các tầng tìm kiếm"
    )
    
    method_map = {
        "BM25": "bm25",
        "Dense": "dense",
        "Hybrid": "hybrid",
        "Hybrid + Rerank": "hybrid_rerank",
        "Graph (Neo4j)": "graph_neo4j"
    }
    selected_method = method_map[method_display]
    
    top_k = st.slider("Số lượng kết quả trả về (Top-k):", min_value=1, max_value=20, value=5)
    candidate_k = st.slider("Số lượng ứng viên rút trích (Candidate-K):", min_value=10, max_value=50, value=20)
    
    st.markdown("---")
    st.markdown("### 📌 Cấu hình Vai trò Đang hoạt động")
    for r in ROLES:
        status = "✅ ACTIVE" if r in selected_roles else "❌ DISABLED"
        st.caption(f"- **{r}:** {status}")

# 4. Form Nhập Câu Hỏi
with st.form(key="search_form"):
    query_input = st.text_input(
        "Nhập câu hỏi tìm kiếm:",
        value="Quy định về kỷ luật lao động và bí mật kho tiền",
        placeholder="Nhập câu hỏi nghiệp vụ..."
    )
    submit_button = st.form_submit_button(label="🔍 Tìm kiếm An toàn", use_container_width=True)

# 5. Xử lý khi nhấn nút Tìm kiếm
if submit_button or query_input:
    if not selected_roles:
        st.error("Vui lòng chọn ít nhất một vai trò ở Sidebar để tiếp tục.")
    elif not query_input.strip():
        st.warning("Vui lòng nhập câu hỏi tìm kiếm.")
    else:
        retriever = get_secure_retriever()
        
        with st.spinner(f"Đang thực thi Secure Retrieval cho vai trò: {selected_roles}..."):
            # Lấy kết quả đã lọc theo user_roles
            results = retriever.retrieve(
                query=query_input,
                user_roles=selected_roles,
                method=selected_method,
                top_k=top_k,
                candidate_k=candidate_k
            )
            
            # Tính toán thống kê tài liệu bị ẩn (Unrestricted vs Restricted)
            if selected_method != "graph_neo4j":
                all_roles_unrestricted = ROLES  # Tất cả vai trò (Admin level)
                unrestricted_results = retriever.retrieve(
                    query=query_input,
                    user_roles=all_roles_unrestricted,
                    method=selected_method,
                    top_k=candidate_k,
                    candidate_k=candidate_k
                )
                filtered_out_count = max(0, len(unrestricted_results) - len(results))
            else:
                filtered_out_count = 0
                
            graph_hints = retriever.get_graph_hints(results, user_roles=selected_roles)
            
        # Thông báo kết quả và thống kê lọc bảo mật
        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            st.success(f"Đã tìm thấy **{len(results)}** kết quả phù hợp cho vai trò **{selected_roles}**!")
        with col_res2:
            if filtered_out_count > 0:
                st.warning(f"🔒 Đã ẩn **{filtered_out_count}** kết quả không đủ quyền.")
            else:
                st.info("🔓 0 kết quả bị ẩn do quyền.")

        # Tab Hiển thị
        st.subheader(f"📋 Kết quả Top-{top_k} ({method_display})")
        
        if not results:
            st.warning("Không tìm thấy kết quả nào phù hợp với vai trò của bạn hoặc tài liệu bị hạn chế truy cập.")
        else:
            for idx, item in enumerate(results, start=1):
                rank = item.get('final_rank', item.get('rank', idx))
                score = item.get('score', 0.0)
                cid = item['chunk_id']
                doc_id = item['document_id']
                citation = item['citation']
                text = item['text']
                allowed = item.get('allowed_roles', [])
                
                with st.expander(f"**#{rank}** | Chunk: `{cid}` | Quyền xem: `{allowed}` | Score: `{score:.4f}`", expanded=(idx == 1)):
                    st.markdown(f"**Trích dẫn (Citation):** `{citation}`")
                    st.markdown(f"**Chunk ID:** `{cid}` &nbsp;|&nbsp; **Document ID:** `{doc_id}` &nbsp;|&nbsp; **Score:** `{score:.5f}`")
                    st.markdown(f"🔒 **Quyền truy cập (Allowed Roles):** `{allowed}`")
                    
                    if selected_method in ["hybrid", "hybrid_rerank"]:
                        bm25_r = item.get('bm25_rank', '-')
                        dense_r = item.get('dense_rank', '-')
                        rrf_s = item.get('rrf_score', 0.0)
                        st.info(f"📊 **Rank Fusion:** BM25 Rank: `{bm25_r}` | Dense Rank: `{dense_r}` | RRF Score: `{rrf_s:.5f}`")
                        
                    st.markdown("**Nội dung văn bản:**")
                    st.code(text, language=None)

        # Tab So sánh BEFORE vs AFTER Rerank (nếu chọn Hybrid + Rerank)
        if selected_method == "hybrid_rerank" and results:
            st.markdown("---")
            st.subheader("🔄 So sánh Thứ hạng Bảo mật: BEFORE vs AFTER RERANK")
            
            col1, col2 = st.columns(2)
            hybrid_cands = retriever.search_hybrid(query_input, user_roles=selected_roles, candidate_k=candidate_k, top_k=top_k)
            
            with col1:
                st.markdown("#### 1. BEFORE RERANK (Hybrid RRF - Pre-Filtered)")
                df_before = pd.DataFrame([
                    {
                        'Rank': r['final_rank'],
                        'Chunk ID': r['chunk_id'],
                        'Allowed Roles': r['allowed_roles'],
                        'RRF Score': round(r['rrf_score'], 5)
                    }
                    for r in hybrid_cands
                ])
                st.dataframe(df_before, use_container_width=True)
                
            with col2:
                st.markdown("#### 2. AFTER RERANK (Cross-Encoder - Pre-Filtered)")
                df_after = pd.DataFrame([
                    {
                        'Rank': r['final_rank'],
                        'Chunk ID': r['chunk_id'],
                        'Hybrid Rank': r.get('hybrid_rank', '-'),
                        'Allowed Roles': r.get('allowed_roles', []),
                        'Rerank Score': round(r['rerank_score'], 4)
                    }
                    for r in results
                ])
                st.dataframe(df_after, use_container_width=True)

        # Tab Graph Hints Bảo mật
        st.markdown("---")
        st.subheader("🌐 Secure Graph Hints (Thông tin Đồ thị theo Phân quyền)")
        st.markdown(f"- **Số bản ghi Neo4j khớp với quyền {selected_roles}:** `{graph_hints['records_count']}`")
        if graph_hints['hints']:
            st.dataframe(pd.DataFrame(graph_hints['hints']), use_container_width=True)
        else:
            st.info("Không có thông tin đồ thị trực tiếp hoặc người dùng không có quyền xem thông tin liên quan.")
