#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Web App cho Buổi 14: Hybrid Search + Reranking + Mini Knowledge Graph
Chạy app:
    streamlit run app.py
"""

import os
import sys
import pandas as pd
import streamlit as st

# Thêm project root vào sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.unified_retriever import UnifiedRetriever

# 1. Cấu hình Trang Streamlit
st.set_page_config(
    page_title="RAG Hybrid Search — Buổi 14",
    page_icon="🔍",
    layout="wide"
)

# 2. Khởi tạo Cached Unified Retriever (chỉ load 1 lần)
@st.cache_resource
def get_unified_retriever():
    corpus_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    cache_dir = os.path.join(project_root, 'cache')
    if not os.path.exists(corpus_csv):
        st.error(f"Không tìm thấy file corpus tại `{corpus_csv}`. Vui lòng chạy `python scripts/prepare_corpus.py` trước.")
        st.stop()
    return UnifiedRetriever(corpus_csv, cache_dir)


# Header ứng dụng
st.title("🔍 RAG Hybrid Search — Buổi 14")
st.caption("Hệ thống Tìm kiếm Nâng cao: BM25 Lexical + Dense Vector + RRF Rank Fusion + Cross-Encoder Reranking")

st.markdown("---")

# 3. Sidebar Cấu hình
with st.sidebar:
    st.header("⚙️ Cấu hình Tìm kiếm")
    
    method_display = st.radio(
        "Chọn Phương pháp Retrieval (Method):",
        options=["BM25", "Dense", "Hybrid", "Hybrid + Rerank"],
        index=3,
        help="So sánh hiệu năng giữa các tầng Retrieval"
    )
    
    method_map = {
        "BM25": "bm25",
        "Dense": "dense",
        "Hybrid": "hybrid",
        "Hybrid + Rerank": "hybrid_rerank"
    }
    selected_method = method_map[method_display]
    
    top_k = st.slider("Số lượng kết quả trả về (Top-k):", min_value=1, max_value=20, value=5)
    candidate_k = st.slider("Số lượng ứng viên rút trích (Candidate-K):", min_value=10, max_value=50, value=20)
    
    st.markdown("---")
    st.markdown("### 📌 Thông tin Hệ thống")
    st.markdown("- **Corpus:** 792 Chunks (15 Văn bản)")
    st.markdown("- **Dense Model:** `bkai-foundation-models/vietnamese-bi-encoder`")
    st.markdown("- **Reranker Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`")
    st.markdown("- **Fusion Method:** Reciprocal Rank Fusion (RRF k=60)")

# 4. Form Nhập Câu Hỏi
with st.form(key="search_form"):
    query_input = st.text_input(
        "Nhập câu hỏi tìm kiếm:",
        value="Quy định bảo quản tài sản quý và giấy tờ có giá theo 01/2014/TT-NHNN",
        placeholder="Nhập từ khóa mã văn bản hoặc câu hỏi ngữ nghĩa..."
    )
    submit_button = st.form_submit_button(label="🔍 Tìm kiếm", use_container_width=True)

# 5. Xử lý khi nhấn nút Tìm kiếm
if submit_button or query_input:
    if not query_input.strip():
        st.warning("Vui lòng nhập câu hỏi tìm kiếm.")
    else:
        retriever = get_unified_retriever()
        
        with st.spinner("Đang thực thi Retrieval Pipeline..."):
            results = retriever.retrieve(
                question=query_input,
                method=selected_method,
                top_k=top_k,
                candidate_k=candidate_k
            )
            graph_hints = retriever.get_graph_hints(results)
            
        st.success(f"Đã tìm thấy {len(results)} kết quả phù hợp với phương pháp **{method_display}**!")
        
        # Tap 1: Danh sách Kết quả Chi tiết
        st.subheader(f"📋 Kết quả Top-{top_k} ({method_display})")
        
        for idx, item in enumerate(results, start=1):
            rank = item.get('final_rank', item.get('rank', idx))
            score = item.get('score', 0.0)
            cid = item['chunk_id']
            doc_id = item['document_id']
            citation = item['citation']
            text = item['text']
            
            with st.expander(f"**#{rank}** | Chunk: `{cid}` | Score: `{score:.4f}` | {citation}", expanded=(idx == 1)):
                st.markdown(f"**Trích dẫn (Citation):** `{citation}`")
                st.markdown(f"**Chunk ID:** `{cid}` &nbsp;|&nbsp; **Document ID:** `{doc_id}` &nbsp;|&nbsp; **Score:** `{score:.5f}`")
                
                # Hiển thị thêm thông tin chi tiết với Hybrid
                if selected_method in ["hybrid", "hybrid_rerank"]:
                    bm25_r = item.get('bm25_rank', '-')
                    dense_r = item.get('dense_rank', '-')
                    rrf_s = item.get('rrf_score', 0.0)
                    st.info(f"📊 **Chi tiết Rank Fusion:** BM25 Rank: `{bm25_r}` | Dense Rank: `{dense_r}` | RRF Score: `{rrf_s:.5f}`")
                    
                st.markdown("**Nội dung văn bản:**")
                st.code(text, language=None)
                
        # Tap 2: Bảng so sánh BEFORE RERANK vs AFTER RERANK (dành riêng cho Hybrid + Rerank)
        if selected_method == "hybrid_rerank":
            st.markdown("---")
            st.subheader("🔄 So sánh Thứ hạng: BEFORE RERANK vs AFTER RERANK")
            
            # Lấy tập candidates ban đầu của Hybrid
            hybrid_cands = retriever.hybrid.search(query_input, candidate_k=candidate_k, top_k=top_k)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 1. BEFORE RERANK (Hybrid RRF)")
                df_before = pd.DataFrame([
                    {
                        'Rank': r['final_rank'],
                        'Chunk ID': r['chunk_id'],
                        'RRF Score': round(r['rrf_score'], 5),
                        'Citation': r['citation']
                    }
                    for r in hybrid_cands
                ])
                st.dataframe(df_before, use_container_width=True)
                
            with col2:
                st.markdown("#### 2. AFTER RERANK (Cross-Encoder)")
                df_after = pd.DataFrame([
                    {
                        'Rank': r['final_rank'],
                        'Chunk ID': r['chunk_id'],
                        'Hybrid Rank': r.get('hybrid_rank', '-'),
                        'Rerank Score': round(r['rerank_score'], 4),
                        'Citation': r['citation']
                    }
                    for r in results
                ])
                st.dataframe(df_after, use_container_width=True)

        # Tap 3: Graph Hints
        st.markdown("---")
        st.subheader("🌐 Graph Hints (Thông tin Định hướng Graph RAG)")
        
        st.markdown(f"- **Trạng thái Neo4j Database:** `{graph_hints['neo4j_status']}`")
        st.markdown(f"- **Document IDs Retrieved:** `{graph_hints['retrieved_document_ids']}`")
        st.markdown(f"- **Chunk IDs Retrieved:** `{graph_hints['retrieved_chunk_ids']}`")
        
        if graph_hints['direct_relations']:
            st.markdown(f"**Danh sách {len(graph_hints['direct_relations'])} quan hệ 1-hop trực tiếp liên quan:**")
            df_rel = pd.DataFrame(graph_hints['direct_relations'])
            st.dataframe(df_rel, use_container_width=True)
        else:
            st.info("Không có quan hệ trực tiếp 1-hop nào giữa các văn bản được kết xuất.")
            
        st.caption("💡 *Lưu ý: Để xem toàn bộ sơ đồ Knowledge Graph tương tác full 3D/Graph view, người học vui lòng truy cập Neo4j Browser tại `http://localhost:7474`.*")
