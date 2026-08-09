"""
Ứng dụng Streamlit Demo — Advanced RAG & Hybrid Retrieval Workshop (Buổi 08).

Giao diện 4 Tab chuyên sâu:
1. Hỏi đáp Advanced RAG (Grounding & Citation mapping)
2. So sánh Retrieval (Side-by-side 4 retrieval modes, KHÔNG gọi LLM)
3. Pipeline Trace (Trực quan hóa luồng dữ liệu & Latency từng tầng)
4. Đánh giá (Đọc báo cáo đo lường Hit Rate, MRR, NDCG từ reports/)
"""

import sys
import os
import json
import time
from pathlib import Path
import streamlit as st

# Import public APIs từ baseline rag.py và advanced_rag.py
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
import rag
import advanced_rag


def get_cached_status(strategy: str):
    """Nạp trạng thái hệ thống Read-Only trực tiếp từ ChromaDB."""
    return advanced_rag.get_advanced_status(strategy=strategy)


def main():
    st.set_page_config(
        page_title="Advanced RAG Workshop — Buổi 08",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Styling giao diện hiện đại & chỉn chu
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #64748B;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 12px 16px;
            text-align: center;
        }
        .metric-card .title {
            font-size: 0.85rem;
            color: #64748B;
            font-weight: 600;
        }
        .metric-card .value {
            font-size: 1.5rem;
            color: #0F172A;
            font-weight: 700;
        }
        .status-badge-answered {
            background-color: #DCFCE7;
            color: #166534;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
        }
        .status-badge-insufficient {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
        }
        .status-badge-warning {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">🚀 Advanced RAG & Multilingual Hybrid Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Hệ thống RAG nâng cao kết hợp Lexical (BM25), Semantic Vector (Gemini), Reciprocal Rank Fusion (RRF) và Cross-Encoder Reranker.</div>', unsafe_allow_html=True)

    # Nạp cấu hình từ .env
    try:
        config = advanced_rag.load_advanced_config()
    except Exception as e:
        st.error(f"⚠️ Lỗi cấu hình hệ thống: {e}")
        st.stop()

    # SIDEBAR CONTROL PANEL
    with st.sidebar:
        st.header("⚙️ Cấu Hình RAG Pipeline")

        strategy = st.selectbox(
            "Chiến lược Chunking (Strategy)",
            options=list(rag.VALID_STRATEGIES),
            index=0,
            help="Chiến lược cắt nhỏ văn bản từ Buổi 05"
        )

        mode = st.selectbox(
            "Chế độ Retrieval (Mode)",
            options=["hybrid_rerank", "hybrid", "semantic", "bm25"],
            index=0,
            help="hybrid_rerank là chế độ nâng cao mặc định"
        )

        st.divider()
        st.subheader("🔍 Tham Số Retrieval & RRF")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(f"**BM25 Candidates**: `{config['BM25_CANDIDATES']}`")
            st.markdown(f"**RRF $K$**: `{config['RRF_K']}`")
            st.markdown(f"**BM25 Weight**: `{config['RRF_BM25_WEIGHT']}`")
        with col_s2:
            st.markdown(f"**Semantic Candidates**: `{config['SEMANTIC_CANDIDATES']}`")
            st.markdown(f"**Final Top-K**: `{config['FINAL_TOP_K']}`")
            st.markdown(f"**Semantic Weight**: `{config['RRF_SEMANTIC_WEIGHT']}`")

        st.divider()
        st.subheader("🎯 Cross-Encoder Reranker")
        st.markdown(f"**Model**: `{config['RERANKER_MODEL']}`")
        st.markdown(f"**Device**: `{config['RERANK_DEVICE']}`")
        st.markdown(f"**Rerank Candidates**: `{config['RERANK_CANDIDATES']}`")
        st.markdown(f"**Min Score Threshold**: `{config['RERANK_MIN_SCORE']}`")

        # Nạp trạng thái hệ thống Read-Only
        sys_status = get_cached_status(strategy)
        st.divider()
        st.subheader("📊 Trạng Thái Hệ Thống (Read-Only)")
        st.markdown(f"- Corpus Size: **{sys_status['corpus_size']} chunks**")
        st.markdown(f"- BM25 Ready: **{'✅ Có' if sys_status['bm25_ready'] else '❌ Chưa'}**")
        st.markdown(f"- Chroma Collection: **{sys_status['semantic_collection']}**")
        st.markdown(f"- DB Records: **{sys_status['collection_count']} chunks** ({'✅ Exists' if sys_status['collection_exists'] else '⚠️ Not Index'})")
        st.markdown(f"- Reranker Cache: **{'✅ Cached' if sys_status['reranker_cached'] else '⏳ Not Cached'}**")
        st.markdown(f"- API Key Status: **{'✅ Configured' if sys_status['api_key_configured'] else '❌ Missing Key'}**")

    # KHỞI TẠO TAB
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Hỏi đáp Advanced RAG",
        "⚖️ So sánh Retrieval",
        "📊 Pipeline Trace",
        "📈 Đánh giá Performance"
    ])

    # Session State
    if "last_query_result" not in st.session_state:
        st.session_state.last_query_result = None
    if "last_compare_result" not in st.session_state:
        st.session_state.last_compare_result = None

    # =========================================================================
    # TAB 1 — HỎI ĐÁP ADVANCED RAG
    # =========================================================================
    with tab1:
        st.markdown("### 💬 Hỏi Đáp Pháp Lý Với Grounding & Citations")

        # Gợi ý câu hỏi mẫu
        sample_questions = [
            "Điều kiện để tổ chức tín dụng cơ cấu lại thời hạn trả nợ là gì?",
            "Quy định về trích lập dự phòng rủi ro đối với số dư nợ được cơ cấu lại?",
            "Thời gian cơ cấu lại thời hạn trả nợ tối đa là bao nhiêu tháng?"
        ]
        selected_sample = st.selectbox("💡 Chọn câu hỏi mẫu:", ["-- Tự nhập câu hỏi --"] + sample_questions)

        default_q = "" if selected_sample == "-- Tự nhập câu hỏi --" else selected_sample
        user_query = st.text_input("Nhập câu hỏi của bạn:", value=default_q, placeholder="Ví dụ: Quy định cơ cấu lại thời hạn trả nợ...")

        col_b1, col_b2 = st.columns([1, 4])
        with col_b1:
            run_btn = st.button("🚀 Gửi Câu Hỏi", type="primary", use_container_width=True)

        if run_btn:
            if not user_query.strip():
                st.warning("⚠️ Vui lòng nhập nội dung câu hỏi trước khi gửi.")
            else:
                with st.spinner("⏳ Đang xử lý qua Pipeline Advanced RAG (BM25 ➔ Semantic ➔ RRF ➔ Reranker ➔ LLM)..."):
                    # Kiểm tra an toàn trước khi gọi
                    if mode in ["semantic", "hybrid", "hybrid_rerank"] and not sys_status["collection_exists"]:
                        st.error("⚠️ Chỉ mục Semantic Index chưa tồn tại trong ChromaDB!")
                        st.info("💡 **Hướng dẫn khởi tạo**: Mở Terminal và chạy lệnh:\n`python advanced_rag.py prepare-semantic --strategy " + strategy + "`")
                    else:
                        try:
                            res = advanced_rag.query_advanced_rag(
                                question=user_query,
                                mode=mode,
                                strategy=strategy,
                                config=config
                            )
                            st.session_state.last_query_result = res
                        except Exception as ex:
                            st.error(f"❌ Lỗi thực thi RAG Pipeline: {ex}")

        # Hiển thị kết quả query gần nhất
        q_res = st.session_state.last_query_result
        if q_res:
            st.divider()

            # Status Banner
            status_code = q_res["status"]
            if status_code == "answered":
                st.markdown(f"**Trạng Thái**: <span class='status-badge-answered'>✅ ANSWERED (Đã trả lời với trích dẫn)</span>", unsafe_allow_html=True)
            elif status_code == "insufficient_evidence":
                st.markdown(f"**Trạng Thái**: <span class='status-badge-insufficient'>⚠️ INSUFFICIENT EVIDENCE (Không đủ bằng chứng tin cậy)</span>", unsafe_allow_html=True)
            elif status_code == "reranker_unavailable":
                st.markdown(f"**Trạng Thái**: <span class='status-badge-warning'>❌ RERANKER UNAVAILABLE (Mô hình Reranker không sẵn sàng)</span>", unsafe_allow_html=True)
                st.info("💡 **Hướng dẫn**: Để tải mô hình Reranker, hãy chạy lệnh:\n`python advanced_rag.py rerank --strategy " + strategy + " --question \"test\"`")
            else:
                st.markdown(f"**Trạng Thái**: <span class='status-badge-warning'>⚠️ RETRIEVAL ONLY (Chỉ trả lời tầng Retrieval)</span>", unsafe_allow_html=True)

            # Câu trả lời & Trích dẫn
            st.markdown("#### 📝 Câu Trả Lời (Generated Answer):")
            if q_res["answer"]:
                st.write(q_res["answer"])
            else:
                st.info("Không có câu trả lời được sinh ra.")

            if q_res["citations"]:
                st.markdown("#### 📌 Trích Dẫn Chi Tiết (Citations Mapping):")
                for cit in q_res["citations"]:
                    page_str = rag.format_page_str(cit["page_start"], cit["page_end"])
                    st.markdown(f"- **{cit['label']}** ➔ File: `{cit['source']}` ({page_str}) | `Chunk ID`: `{cit['chunk_id']}`")

            if q_res["warnings"]:
                with st.expander("⚠️ Danh Sách Cảnh Báo (Warnings)", expanded=False):
                    for w in q_res["warnings"]:
                        st.caption(f"• {w}")

            # Danh sách Evidence Cards
            st.markdown("#### 📂 Danh Sách Bằng Chứng (Evidence Cards):")
            for cand in q_res["evidence"]:
                acc_label = "🟢 ACCEPTED" if cand["accepted"] else "🔴 REJECTED"
                page_str = rag.format_page_str(cand["page_start"], cand["page_end"])

                with st.expander(f"Chunk `{cand['chunk_id']}` | {acc_label} | Source: {cand['source']} ({page_str})"):
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.markdown(f"**BM25 Rank**: `{cand['bm25_rank']}`")
                        st.markdown(f"**BM25 Score**: `{cand['bm25_score']}`")
                    with col_m2:
                        st.markdown(f"**Semantic Rank**: `{cand['semantic_rank']}`")
                        st.markdown(f"**Cosine Distance**: `{cand['semantic_distance']}`")
                    with col_m3:
                        st.markdown(f"**Fused Rank**: `{cand['fused_rank']}`")
                        st.markdown(f"**RRF Score**: `{cand['rrf_score']}`")
                    with col_m4:
                        change_str = f"+{cand['rank_change']}" if cand['rank_change'] and cand['rank_change'] > 0 else str(cand['rank_change'])
                        st.markdown(f"**Rerank Rank**: `{cand['rerank_rank']}` (`{change_str}`)")
                        st.markdown(f"**Rerank Score (Sigmoid)**: `{cand['rerank_score']}`")

                    st.markdown("**Nội dung văn bản (Text):**")
                    st.text_area("Content", value=cand["text"], height=120, disabled=True, key=f"ev_text_{cand['chunk_id']}")

    # =========================================================================
    # TAB 2 — SO SÁNH RETRIEVAL
    # =========================================================================
    with tab2:
        st.markdown("### ⚖️ So Sánh Trực Quan Thứ Hạng Giữa Các Mode Retrieval")
        st.info("Chế độ so sánh giúp người học quan sát trực tiếp vị trí thay đổi của từng chunk qua 4 giai đoạn (BM25 ➔ Semantic ➔ Hybrid RRF ➔ Cross-Encoder Reranker). **Tuyệt đối không gọi LLM generation.**")

        comp_query = st.text_input("Nhập câu hỏi để so sánh 4 mode:", value=user_query if user_query else "Điều 7 quy định gì?", key="comp_query_input")
        comp_btn = st.button("📊 Chạy So Sánh Retrieval", type="secondary")

        if comp_btn:
            if not comp_query.strip():
                st.warning("⚠️ Vui lòng nhập câu hỏi.")
            else:
                with st.spinner("⏳ Đang truy vấn song song qua 4 mode retrieval..."):
                    try:
                        c_res = advanced_rag.compare_retrieval_modes(
                            question=comp_query,
                            strategy=strategy,
                            config=config
                        )
                        st.session_state.last_compare_result = c_res
                    except Exception as ex:
                        st.error(f"❌ Lỗi so sánh: {ex}")

        c_res = st.session_state.last_compare_result
        if c_res:
            st.divider()
            st.markdown(f"**Câu hỏi**: `{c_res['question']}` | **Strategy**: `{c_res['strategy']}`")

            # Bảng so sánh tổng hợp
            st.markdown("#### 📋 Bảng So Sánh Vị Trí Xếp Hạng (Ranks Matrix)")
            table_data = []
            for row in c_res["comparison_rows"]:
                table_data.append({
                    "Chunk ID": row["chunk_id"],
                    "Source": f"{row['source']} ({rag.format_page_str(row['page_start'], row['page_end'])})",
                    "BM25 Rank": row["ranks"].get("bm25", "-"),
                    "Semantic Rank": row["ranks"].get("semantic", "-"),
                    "Fused Rank (RRF)": row["ranks"].get("hybrid", "-"),
                    "Rerank Rank": row["ranks"].get("hybrid_rerank", "-")
                })
            st.dataframe(table_data, use_container_width=True)

            # Latency per mode
            st.markdown("#### ⏱️ Thời Gian Xử Lý Latency (ms):")
            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            with col_l1:
                st.metric("BM25 Latency", f"{c_res['latencies_ms']['bm25']} ms")
            with col_l2:
                st.metric("Semantic Latency", f"{c_res['latencies_ms']['semantic']} ms")
            with col_l3:
                st.metric("Hybrid RRF Latency", f"{c_res['latencies_ms']['hybrid']} ms")
            with col_l4:
                st.metric("Reranker Latency", f"{c_res['latencies_ms']['hybrid_rerank']} ms")

    # =========================================================================
    # TAB 3 — PIPELINE TRACE
    # =========================================================================
    with tab3:
        st.markdown("### 📊 Trực Quan Hoá Pipeline Execution Trace")

        if not st.session_state.last_query_result:
            st.info("💡 Hãy thực hiện một câu hỏi tại **Tab 1 — Hỏi đáp Advanced RAG** để xem vết xử lý pipeline chi tiết.")
        else:
            q_res = st.session_state.last_query_result
            tr = q_res["trace"]

            st.markdown("#### 🔄 Luồng Luân Chuyển Dữ Liệu Qua Các Tầng:")
            col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
            with col_t1:
                st.markdown(f'<div class="metric-card"><div class="title">1. BM25 Candidates</div><div class="value">{tr["bm25_candidates"]}</div></div>', unsafe_allow_html=True)
            with col_t2:
                st.markdown(f'<div class="metric-card"><div class="title">2. Semantic Candidates</div><div class="value">{tr["semantic_candidates"]}</div></div>', unsafe_allow_html=True)
            with col_t3:
                st.markdown(f'<div class="metric-card"><div class="title">3. Union / Overlap</div><div class="value">{tr["union"]} / {tr["overlap"]}</div></div>', unsafe_allow_html=True)
            with col_t4:
                st.markdown(f'<div class="metric-card"><div class="title">4. Reranked Subset</div><div class="value">{tr["reranked"]}</div></div>', unsafe_allow_html=True)
            with col_t5:
                st.markdown(f'<div class="metric-card"><div class="title">5. Accepted Evidence</div><div class="value">{tr["accepted"]}</div></div>', unsafe_allow_html=True)

            st.divider()
            st.markdown("#### ⚡ Latency Chi Tiết Từng Giai Đoạn (ms):")
            lat = tr["latency_ms"]
            col_lat1, col_lat2, col_lat3, col_lat4, col_lat5, col_lat6 = st.columns(6)
            with col_lat1:
                st.metric("BM25", f"{lat.get('bm25', 0.0)} ms")
            with col_lat2:
                st.metric("Semantic", f"{lat.get('semantic', 0.0)} ms")
            with col_lat3:
                st.metric("Fusion (RRF)", f"{lat.get('fusion', 0.0)} ms")
            with col_lat4:
                st.metric("Rerank", f"{lat.get('rerank', 0.0)} ms")
            with col_lat5:
                st.metric("LLM Gen", f"{lat.get('generation', 0.0)} ms")
            with col_lat6:
                st.metric("Total", f"{lat.get('total', 0.0)} ms")

            st.divider()
            st.markdown("#### 📘 Chú Thích Thang Đo & Thuật Toán:")
            st.markdown(r"""
            1. **BM25 Score**: Điểm số tần suất từ khóa BM25Okapi (Điểm số cao hơn đại diện cho độ khớp từ khóa tốt hơn).
            2. **Cosine Distance**: Khoảng cách góc giữa 2 vector embedding Gemini 768d (Khoảng cách **thấp hơn** đại diện cho độ tương đồng ngữ nghĩa cao hơn).
            3. **RRF Score**: Điểm số dung hợp dựa trên vị trí thứ hạng $1/(K + rank)$.
            4. **Rerank Score (Sigmoid)**: Điểm số tương quan từ mô hình Cross-Encoder $\sigma(\text{logit}) \in [0.0, 1.0]$. *(Lưu ý: Rerank Score là điểm chuẩn hóa của mô hình, không đại diện cho xác suất thống kê đúng/sai).*
            """)

    # =========================================================================
    # TAB 4 — ĐÁNH GIÁ PERFORMANCE
    # =========================================================================
    with tab4:
        st.markdown("### 📈 Đánh Giá Chất Lượng RAG Metrics")
        st.info("Tab này đọc báo cáo đánh giá tự động đã được xuất ra file JSON trong thư mục `reports/` (do script `evaluate.py` sinh ra). **Không tự chạy hàng loạt API khi mở ứng dụng.**")

        eval_report_file = BASE_DIR / "reports" / "eval_results.json"

        if not eval_report_file.exists():
            st.warning("⚠️ Chưa tìm thấy file báo cáo đánh giá `reports/eval_results.json`!")
            st.markdown("""
            **Hướng dẫn sinh báo cáo**:
            1. Đảm bảo file `eval/questions.json` đã được gắn nhãn Gold Standard.
            2. Mở Terminal và chạy script đánh giá:
               ```bash
               python evaluate.py
               ```
            3. Quay lại trang này để xem bảng chỉ số so sánh giữa Baseline Semantic và Advanced RAG!
            """)
        else:
            try:
                with open(eval_report_file, "r", encoding="utf-8") as f:
                    eval_data = json.load(f)

                if eval_data.get("has_unreviewed_questions", False):
                    st.warning("⚠️ Cảnh báo: Bộ câu hỏi đánh giá vẫn còn chứa câu hỏi có nhãn `needs_human_review=true`. Kết quả dưới đây chỉ mang tính chất tham khảo!")

                st.markdown("#### 📊 Bảng So Sánh Chỉ Số Retrieval Metrics:")
                st.json(eval_data.get("metrics_summary", {}))

            except Exception as ex:
                st.error(f"❌ Lỗi đọc file báo cáo đánh giá: {ex}")


if __name__ == "__main__":
    main()
