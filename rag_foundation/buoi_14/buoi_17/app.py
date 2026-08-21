"""
buoi_17/app.py
--------------
Streamlit Web Application cho Buổi 17:
Secure RAG, RBAC Access Control, Audit Trail & AI Compliance Gap Checker.

Chạy ứng dụng:
    streamlit run buoi_17/app.py
"""

import os
import sys
import json
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# Setup sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "buoi_17" else SCRIPT_DIR
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts.internal_lookup import InternalPolicyLookup, FALLBACK_MESSAGE
from scripts.compliance_gap import ComplianceGapChecker
from scripts.audit_logger import AuditLogger

# 1. Page Config
st.set_page_config(
    page_title="Secure RAG & Compliance — Buổi 17",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-left: 5px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 8px;
        color: #f8fafc;
        font-weight: 500;
        margin-bottom: 25px;
    }
    .status-badge-allowed {
        background-color: #16a34a;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .status-badge-denied {
        background-color: #dc2626;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .citation-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 10px 15px;
        margin-bottom: 8px;
    }
    .gap-badge-dapung { background-color: #16a34a; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .gap-badge-thieu { background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .gap-badge-chenhlech { background-color: #d97706; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .gap-badge-chuadu { background-color: #475569; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Mandatory Training Banner
st.markdown(
    '<div class="main-banner">⚠️ <b>Demo đào tạo</b> — Kết quả AI chỉ mang tính chất tham khảo, '
    'mọi kết luận tuân thủ và tra cứu cần được <b>Kiểm toán viên xác minh</b>.</div>',
    unsafe_allow_html=True
)

st.title("🛡️ SECURE RAG & AI COMPLIANCE — BUỔI 17")
st.caption("Hệ thống Tra cứu Quy định Nội bộ phân quyền (RBAC), Audit Trail & Compliance Gap Analysis")
st.markdown("---")

# 2. Sidebar Setup
with st.sidebar:
    st.header("👤 Giả lập Người dùng (Impersonation)")
    
    user_id_demo = st.text_input("User ID Demo:", value="demo_usr_01")
    
    available_roles = ["Admin", "Risk_Officer", "HR_Manager", "Employee", "Guest"]
    selected_roles = st.multiselect(
        "Vai trò người dùng (User Roles):",
        options=available_roles,
        default=["Risk_Officer"],
        help="Lựa chọn một hoặc nhiều vai trò để giả lập kiểm tra RBAC"
    )
    
    if not selected_roles:
        selected_roles = ["Guest"]
        st.warning("⚠️ Chưa chọn role nào, hệ thống mặc định vai trò 'Guest'.")
        
    st.markdown("---")
    st.header("🌐 Trạng thái Hệ thống")
    st.success("✅ Secure Retrieval (Buổi 16): Active")
    st.info("ℹ️ Knowledge Graph (Neo4j): Offline / Graph Not Used for Gap Matching")

# 3. Cached Resources
@st.cache_resource
def get_internal_lookup():
    return InternalPolicyLookup()

@st.cache_resource
def get_gap_checker():
    return ComplianceGapChecker()

lookup_service = get_internal_lookup()
gap_service = get_gap_checker()

# 4. Main Tabs
tab1, tab2, tab3 = st.tabs(["🔍 1. TRA CỨU QUY ĐỊNH NỘI BỘ", "⚖️ 2. COMPLIANCE GAP CHECKER", "📜 3. AUDIT TRAIL"])

# ==============================================================================
# TAB 1: TRA CỨU QUY ĐỊNH NỘI BỘ
# ==============================================================================
with tab1:
    st.subheader("Tra cứu Quy định & Chính sách Nội bộ có Phân quyền")
    
    col_q, col_k = st.columns([4, 1])
    with col_q:
        question = st.text_input(
            "Nhập câu hỏi tra cứu:",
            value="Tỷ lệ an toàn vốn tối thiểu được quy định là bao nhiêu và cách tính?",
            key="lookup_q"
        )
    with col_k:
        top_k = st.slider("Top-K:", min_value=1, max_value=10, value=5, key="lookup_k")
        
    btn_search = st.button("🔍 Tra cứu Quy định", type="primary", use_container_width=True)
    
    if btn_search and question.strip():
        with st.spinner("Đang truy xuất và tổng hợp câu trả lời an toàn..."):
            result = lookup_service.query(
                question=question,
                user_role=selected_roles,
                top_k=top_k,
                user_id_demo=user_id_demo
            )
            
        st.markdown("### Kết quả Tra cứu")
        
        # Access Decision & Request ID Badges
        col_badge1, col_badge2, col_badge3 = st.columns([1, 1, 2])
        with col_badge1:
            if result["status"] == "SUCCESS":
                st.markdown('**Access Decision:** <span class="status-badge-allowed">ALLOWED</span>', unsafe_allow_html=True)
            else:
                st.markdown('**Access Decision:** <span class="status-badge-denied">DENIED / INSUFFICIENT</span>', unsafe_allow_html=True)
        with col_badge2:
            st.info(f"**Request ID:** `{result['request_id']}`")
        with col_badge3:
            st.caption(f"**Phạm vi Quyền (Scope):** `{', '.join(result['access_scope'])}`")
            
        st.markdown("#### 💬 Câu trả lời của AI:")
        if result["answer"] == FALLBACK_MESSAGE or result["status"] == "DENIED":
            st.error(f"⛔ {result['answer']}")
        else:
            st.success(result["answer"])
            
            st.markdown("#### 📚 Trích dẫn & Mã Tài liệu (Citations):")
            if result["citations"]:
                for idx, cit in enumerate(result["citations"], start=1):
                    doc_id = result["document_ids"][idx-1] if idx-1 < len(result["document_ids"]) else "N/A"
                    chunk_id = result["chunk_ids"][idx-1] if idx-1 < len(result["chunk_ids"]) else "N/A"
                    st.markdown(
                        f'<div class="citation-card">'
                        f'<b>Trích dẫn {idx}:</b> {cit}<br>'
                        f'<small>Document ID: <code>{doc_id}</code> | Chunk ID: <code>{chunk_id}</code></small>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Không có trích dẫn nào.")

# ==============================================================================
# TAB 2: COMPLIANCE GAP CHECKER
# ==============================================================================
with tab2:
    st.subheader("AI Compliance Gap Checker — Đối chiếu Quy định NHNN vs Nội bộ")
    
    st.info("Tính năng đối chiếu hai chiều giữa Yêu cầu quy phạm bên ngoài (NHNN/Nhà nước) và Quy định nội bộ (Internal Policy).")
    
    use_internal_policy_data = st.checkbox(
        "Tích hợp Tập Quy định Nội bộ Agribank (`agribank_internal_policies.csv`) để chạy thử nghiệm Gap Analysis",
        value=True,
        help="Nếu bỏ chọn, hệ thống sẽ chạy kiểm tra trên chunks_secure.csv thuần và báo DATA GAP INSUFFICIENT theo nguyên tắc thực tế."
    )
    
    sample_requirements = [
        "Thông tư 41/2016/TT-NHNN Điều 6: Tỷ lệ an toàn vốn tối thiểu phải đạt 8%.",
        "Thông tư 01/2014/TT-NHNN Điều 10: Quy định vận chuyển và bảo quản tài sản quý, tiền mặt.",
        "Thông tư 56/2024/TT-NHNN Điều 14: Hồ sơ đề nghị cấp Giấy phép thành lập chi nhánh."
    ]
    
    selected_req = st.selectbox("Chọn yêu cầu quy phạm bên ngoài mẫu:", sample_requirements)
    
    btn_gap = st.button("⚖️ Chạy AI Compliance Gap Analysis", type="primary")
    
    if btn_gap:
        with st.spinner("Đang phân tích đối chiếu bằng chứng..."):
            if not use_internal_policy_data:
                st.warning("⚠️ **COMPLIANCE GAP DATA: INSUFFICIENT**")
                st.error("❌ **DATA GAP: INTERNAL POLICY NOT FOUND** trong `chunks_secure.csv`.")
                st.caption("Theo nguyên tắc Buổi 17, hệ thống không tự bịa đặt văn bản nội bộ giả và không sinh kết luận tuân thủ ảo.")
            else:
                req_item = {
                    "document_id": "117310",
                    "chunk_id": "117310_c007",
                    "text": selected_req,
                    "citation": f"[{selected_req.split(':')[0]}]"
                }
                gap_result = gap_service.analyze_gap(req_item, user_roles=selected_roles)
                
                st.markdown("### Kết quả Phân tích Gap Tuân thủ")
                
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    cls = gap_result["classification"]
                    if cls == "DAP_UNG":
                        st.markdown('**Phân loại:** <span class="gap-badge-dapung">ĐÁP ỨNG (DAP_UNG)</span>', unsafe_allow_html=True)
                    elif cls == "THIEU":
                        st.markdown('**Phân loại:** <span class="gap-badge-thieu">THIẾU (THIEU)</span>', unsafe_allow_html=True)
                    elif cls == "CHENH_LECH":
                        st.markdown('**Phân loại:** <span class="gap-badge-chenhlech">CHÊNH LỆCH (CHENH_LECH)</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('**Phân loại:** <span class="gap-badge-chuadu">CHƯA ĐỦ BẰNG CHỨNG</span>', unsafe_allow_html=True)
                with col_g2:
                    st.info(f"**Review Status:** `{gap_result['review_status']}`")
                with col_g3:
                    st.metric("Điểm tin cậy (Confidence):", f"{gap_result['confidence']*100:.1f}%")
                    
                st.markdown("#### 📄 Bằng chứng hai phía (Evidence Package):")
                col_ext, col_int = st.columns(2)
                with col_ext:
                    st.markdown(f"**Yêu cầu NHNN ({gap_result['external_citation']}):**")
                    st.write(gap_result["external_requirement"])
                with col_int:
                    st.markdown(f"**Bằng chứng Nội bộ Agribank ({gap_result['internal_citation']}):**")
                    st.write(gap_result["internal_evidence"])
                    
                st.markdown("#### 💡 Lý do phân tích của AI:")
                st.write(gap_result["reason"])

# ==============================================================================
# TAB 3: AUDIT TRAIL
# ==============================================================================
with tab3:
    st.subheader("Nhật ký Truy vết Hệ thống (Audit Trail Log)")
    
    st.caption("Hiển thị nhật ký ghi vết tự động theo định dạng JSON Lines (.jsonl). Bảo đảm không rò rỉ secret / password.")
    
    log_file = PROJECT_ROOT / "outputs" / "audit_log.jsonl"
    
    if not log_file.exists():
        st.info("Chưa có sự kiện audit log nào được ghi.")
    else:
        with open(log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
            
        logs_data = []
        for line in log_lines:
            if line.strip():
                try:
                    logs_data.append(json.loads(line))
                except Exception:
                    pass
                    
        df_logs = pd.DataFrame(logs_data)
        
        if df_logs.empty:
            st.info("Nhật ký rỗng.")
        else:
            st.markdown(f"**Tổng số sự kiện Audit:** `{len(df_logs)}` events")
            
            st.dataframe(
                df_logs[['timestamp', 'request_id', 'user_id_demo', 'user_role', 'action', 'query', 'retrieval_method', 'status']],
                use_container_width=True
            )
            
            st.markdown("#### 🔍 Chi tiết từng sự kiện JSON:")
            for idx, item in enumerate(reversed(logs_data), start=1):
                with st.expander(f"Event #{len(logs_data)-idx+1} | {item.get('timestamp')} | User: {item.get('user_id_demo')} | Status: {item.get('status')}"):
                    st.json(item)
