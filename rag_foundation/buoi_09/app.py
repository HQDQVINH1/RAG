"""
Streamlit Web Application cho Hierarchical Advanced RAG (Buổi 09).
Multi-Query Fan-Out & Parent-Child Explorer Architecture.

Run command:
python -m streamlit run app.py
"""

import sys
import os
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag
import advanced_rag
import rag


# ==============================================================================
# UI HELPER FUNCTIONS (PURE PYTHON - 100% UNIT TESTABLE WITHOUT STREAMLIT)
# ==============================================================================

def build_query_child_matrix_data(child_hits: List[Dict[str, Any]], queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Xây dựng bảng ma trận Query - Child (Hàng là Child, Cột là các Query Q0..Qn).
    """
    if not child_hits or not queries:
        return []

    q_ids = [q["query_id"] for q in queries]
    matrix_rows = []

    for c in child_hits:
        cid = c.get("child_id", c.get("chunk_id", "N/A"))
        row = {
            "MQ-Rank": f"#{c.get('multi_query_rank', 0)}",
            "Child Candidate ID": cid,
            "MQ-RRF Score": f"{c.get('multi_query_rrf_score', 0.0):.6f}",
            "Support Count": c.get("support_query_count", 0),
        }

        per_ranks = c.get("per_query_ranks", {})
        for qid in q_ids:
            if qid in per_ranks:
                row[qid] = f"#{per_ranks[qid]}"
            else:
                row[qid] = "—"

        matrix_rows.append(row)

    return matrix_rows


def build_parent_tree_data(parent_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Xây dựng dữ liệu cấu trúc cây Parent - Child dạng hierarchical tree.
    """
    tree_nodes = []
    for p in parent_candidates:
        node = {
            "parent_id": p["parent_id"],
            "parent_rank": p.get("parent_rank", 0),
            "parent_rerank_rank": p.get("parent_rerank_rank", p.get("parent_rank", 0)),
            "parent_rank_change": p.get("parent_rank_change", 0),
            "parent_rrf_score": round(p.get("parent_rrf_score", 0.0), 6),
            "parent_rerank_score": round(p.get("parent_rerank_score", 0.0), 4),
            "source": p.get("source", ""),
            "page_range": f"Trang {p.get('page_start', 1)}-{p.get('page_end', 1)}",
            "text_length": len(p.get("text", "")),
            "anchor_child_id": p.get("anchor_child_id", ""),
            "scoring_child_ids": p.get("scoring_child_ids", []),
            "supporting_child_ids": p.get("supporting_child_ids", []),
            "support_query_ids": p.get("support_query_ids", []),
            "ambiguous": p.get("ambiguous", False),
            "warnings": p.get("warnings", []),
            "text": p.get("text", ""),
            "child_hits_detail": p.get("child_hits_detail", [])
        }
        tree_nodes.append(node)
    return tree_nodes


def build_mode_comparison_row(mode: str, res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa 1 hàng dữ liệu so sánh cho 1 Mode.
    """
    status = res.get("status", "unknown")
    accepted = res.get("accepted_evidence", [])
    unit_type = "Parent" if "parent" in mode else "Child"
    
    ev_ids = []
    for ev in accepted:
        if "parent_id" in ev:
            ev_ids.append(ev["parent_id"])
        else:
            ev_ids.append(ev.get("child_id", ev.get("chunk_id")))

    ev_str = ", ".join(ev_ids[:3]) + ("..." if len(ev_ids) > 3 else "")

    child_count = len(res.get("child_hits", []))
    parent_count = len(res.get("parent_candidates", []))

    total_chars = sum(len(ev.get("text", "")) for ev in accepted)
    child_chars = sum(len(c.get("text", "")) for c in res.get("child_hits", []))
    exp_factor = round(total_chars / max(child_chars, 1), 2) if child_chars > 0 else 1.0

    return {
        "Mode": mode,
        "Status": status,
        "Unit Type": unit_type,
        "Accepted Evidence Count": len(accepted),
        "Evidence Preview": ev_str,
        "Retrieved Children": child_count,
        "Expanded Parents": parent_count,
        "Context Chars": total_chars,
        "Expansion Factor": f"{exp_factor}x",
        "Latency (ms)": round(res.get("total_latency_ms", 0.0), 2),
        "Gen Calls": res.get("api_call_counts", {}).get("generation_calls", 0),
        "Embedding Calls": res.get("api_call_counts", {}).get("embedding_calls", 0)
    }


def format_citation_display(citation: Dict[str, Any]) -> str:
    """
    Định dạng hiển thị trích dẫn citation dạng Markdown đẹp mắt.
    """
    label = citation.get("citation_label", "[P1]")
    source = citation.get("source", "")
    p_start = citation.get("page_start", 1)
    p_end = citation.get("page_end", 1)
    pid = citation.get("parent_id", "")
    cid = citation.get("anchor_child_id", citation.get("child_id", ""))
    score = citation.get("parent_rerank_score", citation.get("rerank_score", 0.0))

    out = f"**{label} Nguồn: `{source}` (Trang {p_start}-{p_end})**\n"
    if pid:
        out += f"- **Parent ID**: `{pid}` | **Rerank Score**: `{score:.4f}`\n"
    if cid:
        out += f"- **Anchor Child ID**: `{cid}`\n"
    if citation.get("ambiguous"):
        out += f"- ⚠️ **Cảnh báo Ambiguity**: Trích dẫn chứa điều khoản sửa đổi/xung đột!\n"
    return out


def map_error_ux_message(status_code: str) -> Tuple[str, str, str]:
    """
    Ánh xạ mã trạng thái lỗi sang thông điệp UX thân thiện và hướng dẫn xử lý.
    Trả về: (tiêu đề, nội dung chi tiết, hướng khắc phục)
    """
    error_map = {
        "hierarchy_not_ready": (
            "Hierarchy Registry Chưa Khởi Tạo",
            "Hệ thống chưa tìm thấy file phân cấp children.json và parents.json trong storage/hierarchy/.",
            "Hãy nhấn nút 'Build Hierarchy Store' ở Sidebar để khởi tạo phân cấp văn bản pháp luật."
        ),
        "collection_not_ready": (
            "ChromaDB Collection Chưa Tồn Tại",
            "Cơ sở dữ liệu Vector ChromaDB chưa được indexing cho chiến lược này.",
            "Hãy chạy câu lệnh 'python advanced_rag.py prepare-semantic' để index tài liệu."
        ),
        "query_generation_unavailable": (
            "Không Thể Sinh Biến Thể Multi-Query",
            "Gemini API gặp sự cố hoặc vượt quota hạn mức khi sinh câu hỏi mở rộng.",
            "Hệ thống đã tự động chuyển hướng an toàn sang chế độ Q0 (Original Question)."
        ),
        "multi_query_partial": (
            "Một Số Query Gặp Lỗi Retrieval",
            "Một hoặc nhiều câu hỏi biến thể gặp sự cố khi tìm kiếm trong ChromaDB.",
            "Kết quả hiển thị được tổng hợp từ các Query thành công còn lại."
        ),
        "reranker_unavailable": (
            "Cross-Encoder Reranker Không Khả Dụng",
            "Mô hình BAAI/bge-reranker-v2-m3 gặp sự cố bộ nhớ GPU/CPU hoặc chưa được tải thành công.",
            "Hãy kiểm tra kết nối mạng hoặc bộ nhớ thiết bị để tải mô hình Reranker."
        ),
        "insufficient_evidence": (
            "Không Tìm Thấy Căn Cứ Pháp Lý Đạt Ngưỡng",
            "Không có đoạn văn bản pháp luật nào đạt điểm số Rerank tối thiểu (RERANK_MIN_SCORE).",
            "Hãy hạ thấp ngưỡng RERANK_MIN_SCORE ở Sidebar hoặc đổi sang chế độ multi_parent."
        ),
        "generation_error": (
            "Lỗi Gọi Gemini API (API Error / Quota Limit)",
            "Gặp sự cố khi gọi Gemini API để tạo Embeddings hoặc sinh câu trả lời.",
            "Nếu gặp lỗi 429 RESOURCE_EXHAUSTED, hãy chờ 30-60 giây để hết thời gian rate limit API Key của bạn."
        )
    }

    return error_map.get(
        status_code,
        ("Lỗi Không Xác Định", f"Trạng thái lỗi: {status_code}", "Hãy kiểm tra nhật ký log để biết chi tiết.")
    )


def safe_dataframe(df: pd.DataFrame):
    """Render dataframe không bị cảnh báo deprecation trên Streamlit 1.42+."""
    import streamlit as st
    try:
        st.dataframe(df, width="stretch")
    except Exception:
        try:
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.dataframe(df)


def safe_button(label: str, type: str = "primary") -> bool:
    """Render button không bị cảnh báo deprecation trên Streamlit 1.42+."""
    import streamlit as st
    try:
        return st.button(label, type=type, width="stretch")
    except Exception:
        try:
            return st.button(label, type=type, use_container_width=True)
        except Exception:
            return st.button(label, type=type)


# ==============================================================================
# STREAMLIT UI RENDER ENGINE
# ==============================================================================

def render_streamlit_app():
    """Hàm render chính cho ứng dụng Streamlit Buổi 09."""
    import streamlit as st

    st.set_page_config(
        page_title="RAG Foundation — Buổi 09: Multi-query & Parent–Child Retrieval",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 1. Header & Title
    st.title("⚖️ RAG Foundation — Buổi 09: Multi-query & Parent–Child Retrieval")
    st.caption("🚀 Pipeline: `Query fan-out` ➔ `Hybrid per query` ➔ `Cross-query RRF` ➔ `Parent expansion` ➔ `Parent rerank` ➔ `Answer Generation`")

    # 2. Sidebar Configurations
    st.sidebar.header("⚙️ Cấu Hình Pipeline Runtime")

    config = hierarchical_rag.load_buoi09_config()

    mode_selected = st.sidebar.selectbox(
        "Chế độ truy vấn (Mode)",
        options=["multi_parent", "single_parent", "multi_flat", "single_flat"],
        index=0,
        help="multi_parent: Q0+Variants ➔ MQ-RRF ➔ Parent Rerank"
    )

    st.sidebar.subheader("🎛️ Thông Số Thuật Toán")
    mq_count = st.sidebar.slider("MULTI_QUERY_COUNT", min_value=1, max_value=5, value=config["MULTI_QUERY_COUNT"])
    per_q_cands = st.sidebar.slider("PER_QUERY_CANDIDATES", min_value=5, max_value=50, value=config["PER_QUERY_CANDIDATES"])
    parent_cands = st.sidebar.slider("PARENT_CANDIDATES", min_value=3, max_value=20, value=config["PARENT_CANDIDATES"])
    final_top_k = st.sidebar.slider("FINAL_PARENT_TOP_K", min_value=1, max_value=10, value=config["FINAL_PARENT_TOP_K"])
    min_score = st.sidebar.slider("RERANK_MIN_SCORE", min_value=0.0, max_value=1.0, value=config["RERANK_MIN_SCORE"], step=0.05)

    # Runtime config object
    runtime_config = dict(config)
    runtime_config["MULTI_QUERY_COUNT"] = mq_count
    runtime_config["PER_QUERY_CANDIDATES"] = per_q_cands
    runtime_config["PARENT_CANDIDATES"] = parent_cands
    runtime_config["FINAL_PARENT_TOP_K"] = final_top_k
    runtime_config["RERANK_MIN_SCORE"] = min_score

    # Sidebar Diagnostics
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Trạng Thái Hệ Thống")

    has_api_key = bool(config.get("GEMINI_API_KEY", "").strip())
    st.sidebar.markdown(f"**Gemini API Key**: {'✅ Đã cấu hình' if has_api_key else '❌ Chưa có (.env)'}")
    st.sidebar.text(f"Strategy: hierarchical (Cố định)")
    st.sidebar.text(f"Generation: {config['GEMINI_GENERATION_MODEL']}")
    st.sidebar.text(f"Embedding : {config['GEMINI_EMBEDDING_MODEL']}")
    st.sidebar.text(f"Reranker  : {config.get('RERANKER_MODEL', config.get('RERANKER_MODEL_NAME', 'BAAI/bge-reranker-v2-m3'))}")

    # Hierarchy Store Status
    h_status = hierarchical_rag.get_hierarchy_status()
    st.sidebar.markdown("---")
    st.sidebar.subheader("📦 Hierarchy Registry Store")
    if h_status["hierarchy_store_exists"]:
        st.sidebar.success(f"Status: READY\n- Children: {h_status['total_children']}\n- Parents: {h_status['total_parents']}\n- Ambiguous: {h_status['manifest'].get('ambiguous_child_count', 0)}")
    else:
        st.sidebar.error("Status: MISSING / NOT READY")
        if st.sidebar.button("🔨 Build Hierarchy Store"):
            with st.spinner("Đang xây dựng Hierarchy Store atomically..."):
                res = hierarchical_rag.build_and_save_hierarchy_store(config=runtime_config)
                st.sidebar.success(f"Xây dựng thành công! Total Parents: {res['manifest']['total_parents']}")
                st.rerun()

    # 3. Main Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Ask Advanced RAG",
        "🔀 Query Fan-out",
        "📦 Parent–Child Explorer",
        "📊 Mode Comparison",
        "📈 Evaluation Reports"
    ])

    # Session State Initialization
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None
    if "last_question" not in st.session_state:
        st.session_state["last_question"] = ""

    # ==========================================================================
    # TAB 1 — ASK ADVANCED RAG
    # ==========================================================================
    with tab1:
        st.subheader("Hỏi Đáp Pháp Luật Ngân Hàng Nhà Nước (Multi-Query Parent-Child RAG)")
        
        user_query = st.text_area(
            "Nhập câu hỏi pháp lý của bạn:",
            value=st.session_state.get("last_question", "Điều kiện vay vốn và các trường hợp nhu cầu vốn không được cho vay được quy định thế nào?"),
            height=100
        )

        col_btn, col_mode_info = st.columns([1, 4])
        with col_btn:
            run_btn = safe_button("🚀 Chạy RAG Pipeline", type="primary")

        if run_btn and user_query.strip():
            st.session_state["last_question"] = user_query.strip()
            with st.spinner(f"Đang xử lý luồng {mode_selected}..."):
                res = hierarchical_rag.execute_query_pipeline(
                    question=user_query.strip(),
                    mode=mode_selected,
                    config=runtime_config
                )
                st.session_state["last_result"] = res

        res = st.session_state.get("last_result")
        if res:
            st.markdown("---")
            # Latency Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Trạng Thái (Status)", res.get("status", "N/A"))
            m2.metric("Tổng Thời Gian (Latency)", f"{res.get('total_latency_ms', 0):.1f} ms")
            m3.metric("Generation Calls", f"{res.get('api_call_counts', {}).get('generation_calls', 0)} / 2 max")
            m4.metric("Embedding Calls", f"{res.get('api_call_counts', {}).get('embedding_calls', 0)}")

            # Status / Error Handling UI
            status = res.get("status")
            if status != "ready":
                title, detail, fix = map_error_ux_message(status)
                err_text = res.get("error", detail)
                st.error(f"**{title}**: {err_text}\n\n👉 **Hướng xử lý**: {fix}")

            # Answer Section
            st.subheader("💡 Câu Trả Lời (Generated Answer)")
            if res.get("answer"):
                st.markdown(res["answer"])
            else:
                st.info("Chưa có câu trả lời được sinh ra.")

            # Citations Section
            st.markdown("---")
            st.subheader("📑 Trích Dẫn Căn Cứ Pháp Lý (Accepted Citations)")
            citations = res.get("citations", [])
            if citations:
                for cit in citations:
                    with st.expander(f"{cit['citation_label']} {cit['source']} (Score: {cit.get('parent_rerank_score', cit.get('rerank_score', 0.0)):.4f})"):
                        st.markdown(format_citation_display(cit))
            else:
                st.warning("Không có căn cứ trích dẫn nào vượt qua ngưỡng RERANK_MIN_SCORE.")

            # Warnings Section
            if res.get("warnings"):
                st.warning("**Cảnh báo từ hệ thống**:\n" + "\n".join([f"- {w}" for w in res["warnings"]]))

    # ==========================================================================
    # TAB 2 — QUERY FAN-OUT & MATRIX
    # ==========================================================================
    with tab2:
        st.subheader("🔀 Multi-Query Fan-Out & Ma Trận Query-Child")
        res = st.session_state.get("last_result")

        if res and res.get("query_set"):
            qset = res["query_set"]
            queries = qset.get("queries", [])
            st.markdown(f"**Mô hình sinh Query**: `{qset.get('model')}` | **Latency**: `{qset.get('generation_latency_ms')} ms` | **Cache Hit**: `{qset.get('cache_hit')}`")

            # Cards cho Q0..Qn
            cols = st.columns(len(queries))
            for idx, q in enumerate(queries):
                with cols[idx]:
                    is_q0 = q["origin"] == "original"
                    card_title = f"🌟 {q['query_id']} (Original)" if is_q0 else f"🔹 {q['query_id']} (Generated)"
                    st.markdown(f"#### {card_title}")
                    
                    # Tính toán result count hỗ trợ cho query này
                    qid = q["query_id"]
                    q_hit_count = sum(1 for c in res.get("child_hits", []) if qid in c.get("per_query_ranks", {}))
                    
                    card_md = (
                        f"**Text**: {q['text']}\n\n"
                        f"• **Origin**: `{q['origin']}`\n"
                        f"• **Focus**: `{q.get('focus', 'N/A')}`\n"
                        f"• **Status**: `{qset.get('status', 'ready')}`\n"
                        f"• **Retrieved Hits**: `{q_hit_count}`\n"
                        f"• **Latency**: `{qset.get('generation_latency_ms', 0.0):.1f} ms`"
                    )
                    st.info(card_md)

            # Ma trận Query - Child
            st.markdown("---")
            st.subheader("📊 Ma Trận Hợp Nhất Cross-Query RRF (Query - Child Matrix)")
            child_hits = res.get("child_hits", [])
            matrix_data = build_query_child_matrix_data(child_hits, queries)

            if matrix_data:
                df_matrix = pd.DataFrame(matrix_data)
                safe_dataframe(df_matrix)
            else:
                st.info("Chưa có dữ liệu ma trận child hits.")
        else:
            st.info("Hãy thực thi RAG Query ở Tab 1 để xem phân tích Multi-Query Fan-Out.")

    # ==========================================================================
    # TAB 3 — PARENT-CHILD EXPLORER
    # ==========================================================================
    with tab3:
        st.subheader("📦 Cây Phân Cấp Parent–Child & Biến Động Thứ Hạng (Rank Movement)")
        res = st.session_state.get("last_result")

        if res and res.get("parent_candidates"):
            parents = res["parent_candidates"]
            tree_nodes = build_parent_tree_data(parents)

            for p in tree_nodes:
                change_str = ""
                if p["parent_rank_change"] > 0:
                    change_str = f"🟢 ▲+{p['parent_rank_change']}"
                elif p["parent_rank_change"] < 0:
                    change_str = f"🔴 ▼{p['parent_rank_change']}"
                else:
                    change_str = "⚪ 0"

                title = f"📦 #{p['parent_rerank_rank']} [{p['parent_id']}] | Rerank Score: {p['parent_rerank_score']} | Rank: #{p['parent_rank']} ➔ #{p['parent_rerank_rank']} ({change_str})"
                
                with st.expander(title):
                    st.markdown(f"**Nguồn**: `{p['source']}` ({p['page_range']}) | **Kích thước**: `{p['text_length']} chars`")
                    st.markdown(f"**Parent RRF Score**: `{p['parent_rrf_score']}` | **Parent Rerank Score**: `{p['parent_rerank_score']}`")
                    st.markdown(f"**Scoring Child IDs**: `{p['scoring_child_ids']}`")
                    st.markdown(f"**Supporting Queries**: `{p['support_query_ids']}`")

                    if p["ambiguous"]:
                        st.warning("⚠️ **Ambiguous Warning**: Khối Parent này chứa các điều khoản trích dẫn sửa đổi/xung đột.")

                    st.markdown("#### 📄 Danh Sách Child Chunks Thuộc Parent:")
                    for c in p["child_hits_detail"]:
                        q_str = ", ".join(c.get("support_query_ids", []))
                        st.text(f"  └── CHILD [{c['child_id']}] (MQ-Rank #{c['multi_query_rank']}, Score: {c['multi_query_rrf_score']:.6f}) | Queries: [{q_str}]")

                    st.markdown("#### 📜 Nội Dung Parent Context:")
                    st.text_area("Parent Full Text", value=p["text"], height=150, key=f"text_{p['parent_id']}")
        else:
            st.info("Hãy thực thi RAG Query ở chế độ Parent (multi_parent hoặc single_parent) ở Tab 1 để khám phá Parent-Child Tree.")

    # ==========================================================================
    # TAB 4 — MODE COMPARISON
    # ==========================================================================
    with tab4:
        st.subheader("📊 So Sánh Hiệu Năng & Kết Quả Giữa 4 Chế Độ (Mode Comparison)")
        st.caption("Chạy so sánh Retrieval-Only (0 LLM Answer Calls) cho câu hỏi hiện tại.")

        comp_query = st.text_input(
            "Câu hỏi thử nghiệm so sánh:",
            value=st.session_state.get("last_question", "Điều kiện vay vốn và các nhu cầu vốn không được cho vay được quy định thế nào?")
        )

        if st.button("🔬 Chạy Benchmark So Sánh 4 Modes", type="secondary"):
            with st.spinner("Đang thực thi benchmark 4 modes (retrieval-only)..."):
                comp_results = hierarchical_rag.compare_pipeline(
                    question=comp_query.strip(),
                    config=runtime_config
                )

                rows = [build_mode_comparison_row(m, r) for m, r in comp_results.items()]
                df_comp = pd.DataFrame(rows)
                safe_dataframe(df_comp)

                st.success("Hoàn tất benchmark so sánh! (0 lần gọi Answer Generation LLM API)")

    # ==========================================================================
    # TAB 5 — EVALUATION REPORTS
    # ==========================================================================
    with tab5:
        st.subheader("📈 Báo Cáo Đánh Giá Chất Lượng Offline Evaluation")
        
        eval_report_path = BASE_DIR / "reports" / "latest_report.json"
        if not eval_report_path.exists():
            eval_report_path = BASE_DIR / "reports" / "eval_results.json"

        if eval_report_path.exists():
            try:
                with open(eval_report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                
                st.markdown(f"**Báo cáo mới nhất**: `{report.get('timestamp')}` | **Số câu hỏi eval**: `{report.get('total_questions')}`")

                summary = report.get("aggregate_summary_per_mode", {})
                mp_stats = summary.get("multi_parent", {})

                e1, e2, e3, e4 = st.columns(4)
                e1.metric("Child Recall@K", f"{mp_stats.get('mean_child_recall', 0.0):.4f}")
                e2.metric("Parent Recall@K", f"{mp_stats.get('mean_parent_recall', 0.0):.4f}")
                e3.metric("MRR@K", f"{mp_stats.get('mean_parent_mrr', 0.0):.4f}")
                e4.metric("nDCG@K", f"{mp_stats.get('mean_parent_ndcg', 0.0):.4f}")

                if report.get("needs_human_review"):
                    st.warning("⚠️ **Warning**: Báo cáo có chứa nhãn Gold Labels chưa được duyệt thủ công (needs_human_review = True).")

                if summary:
                    st.markdown("#### Bảng So Sánh Số Liệu Eval Chi Tiết 4 Modes:")
                    rows = []
                    for m, stats in summary.items():
                        r = {"Mode": m}
                        r.update(stats)
                        rows.append(r)
                    safe_dataframe(pd.DataFrame(rows))

            except Exception as e:
                st.error(f"Không thể đọc file báo cáo evaluation: {e}")
        else:
            st.info("Chưa có báo cáo evaluation offline nào trong thư mục `reports/`. Hãy chạy `python evaluate.py` để tạo báo cáo.")


if __name__ == "__main__":
    render_streamlit_app()
