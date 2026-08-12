import os
import json
from pathlib import Path
import streamlit as st

# Config page
st.set_page_config(
    page_title="RAG Foundation - Visualizer Buổi 05",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Vanilla CSS for rich UI aesthetics)
st.markdown("""
<style>
    /* Dark / Sleek Gradient Styling */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #e0e6ed;
        margin-top: 8px;
        font-size: 1.05rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.88rem;
        color: #64748b;
        font-weight: 500;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-fixed { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .badge-semantic { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-hierarchical { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-ocr { background-color: #fce7f3; color: #9d174d; border: 1px solid #fbcfe8; }
    .badge-pymupdf { background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
    .chunk-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        transition: all 0.2s ease;
    }
    .chunk-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left-color: #2563eb;
    }
    .chunk-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
    }
    .chunk-id {
        font-family: monospace;
        font-weight: 700;
        color: #0f172a;
    }
    .chunk-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #334155;
        white-space: pre-wrap;
        background: #fafafa;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #f1f5f9;
    }
    .meta-tag {
        font-size: 0.82rem;
        color: #64748b;
        background: #f1f5f9;
        padding: 2px 8px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Path settings
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
DATADEMO_DIR = BASE_DIR / "datademo"

def load_output_files():
    """Find all processed chunk JSON files in output/ directory."""
    if not OUTPUT_DIR.exists():
        return {}
    chunk_files = list(OUTPUT_DIR.glob("chunks_*.json")) + list((OUTPUT_DIR / "chunks").glob("chunks_*.json"))
    seen = set()
    unique_chunk_files = []
    for cf in chunk_files:
        if cf.resolve() not in seen:
            seen.add(cf.resolve())
            unique_chunk_files.append(cf)

    data_map = {}
    for cf in unique_chunk_files:
        try:
            with open(cf, "r", encoding="utf-8") as f:
                data = json.load(f)
                source_name = data.get("source", cf.stem.replace("chunks_", "") + ".pdf")
                raw_filename = f"raw_ocr_{Path(source_name).stem}.json"
                raw_file = cf.parent / raw_filename
                if not raw_file.exists():
                    raw_file = OUTPUT_DIR / raw_filename
                data_map[source_name] = {
                    "chunk_file": cf,
                    "raw_file": raw_file,
                    "data": data
                }
        except Exception as e:
            st.error(f"Lỗi đọc file {cf.name}: {str(e)}")
    return data_map

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🔍 RAG Foundation - Visualizer Buổi 05</h1>
    <p>Trực quan hóa luồng trích xuất PDF → OCR (PyMuPDF / LlamaParse) → Phân đoạn 3 Chiến lược Chunking</p>
</div>
""", unsafe_allow_html=True)

data_map = load_output_files()

if not data_map:
    st.warning("⚠️ Chưa tìm thấy dữ liệu kết quả trong thư mục `output/`!")
    st.info("💡 Vui lòng chạy lệnh sau để sinh dữ liệu trước khi xem UI:\n```powershell\n.venv\\Scripts\\python.exe src/process_rag.py --write\n```")
    st.stop()

# Sidebar Controls
st.sidebar.header("⚙️ Điều khiển & Bộ lọc")

selected_doc_name = st.sidebar.selectbox(
    "📄 Chọn Tài liệu PDF",
    options=list(data_map.keys())
)

selected_info = data_map[selected_doc_name]
doc_data = selected_info["data"]
chunks = doc_data.get("chunks", [])
stats = doc_data.get("statistics", {})

# Strategy Filter
strategy_options = ["Tất cả", "Fixed-size", "Semantic", "Hierarchical"]
selected_strategy = st.sidebar.radio("✂️ Chọn Chiến lược Chunking", strategy_options)

# Keyword Filter
search_keyword = st.sidebar.text_input("🔎 Tìm kiếm từ khóa trong text chunk", "").strip().lower()

# Filter Chunks
filtered_chunks = []
for c in chunks:
    strat = c.get("strategy", "").lower()
    if selected_strategy != "Tất cả":
        if selected_strategy.lower() not in strat:
            continue
    if search_keyword:
        if search_keyword not in c.get("text", "").lower():
            continue
    filtered_chunks.append(c)

# Sidebar Stats Info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Tổng số chunk hiển thị:** `{len(filtered_chunks)} / {len(chunks)}`")

# Load raw OCR file if present
raw_ocr_data = {}
if selected_info["raw_file"].exists():
    try:
        with open(selected_info["raw_file"], "r", encoding="utf-8") as f:
            raw_ocr_data = json.load(f)
    except Exception:
        pass

ocr_used = doc_data.get("chunks", [{}])[0].get("ocr_used", False) if chunks else False

# Overview Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(chunks)}</div>
        <div class="metric-label">Tổng số Chunk</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{stats.get('fixed_size', {}).get('count', 0)}</div>
        <div class="metric-label">Fixed-size Chunks</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{stats.get('semantic', {}).get('count', 0)}</div>
        <div class="metric-label">Semantic Chunks</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{stats.get('hierarchical', {}).get('count', 0)}</div>
        <div class="metric-label">Hierarchical Chunks</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    ocr_badge = '<span class="badge badge-ocr">LlamaParse OCR</span>' if ocr_used else '<span class="badge badge-pymupdf">PyMuPDF Text Layer</span>'
    st.markdown(f"""
    <div class="metric-card">
        <div style="margin-top:6px;">{ocr_badge}</div>
        <div class="metric-label" style="margin-top:8px;">Phương thức OCR</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📌 1. Danh sách Chunk & Trực quan hóa", "📊 2. So sánh Báo cáo 3 Chiến lược", "📄 3. Văn bản Raw / OCR"])

# TAB 1: LIST & VISUALIZE CHUNKS
with tab1:
    st.subheader(f"Danh sách Chunk — {selected_doc_name}")
    
    if not filtered_chunks:
        st.info("Không tìm thấy chunk nào phù hợp với bộ lọc hiện tại.")
    else:
        for idx, chunk in enumerate(filtered_chunks):
            strat = chunk.get("strategy", "fixed-size")
            c_id = chunk.get("chunk_id", f"chunk_{idx}")
            p_start = chunk.get("page_start", 1)
            p_end = chunk.get("page_end", 1)
            text = chunk.get("text", "")
            c_ocr = chunk.get("ocr_used", False)
            struct_meta = chunk.get("structure_metadata", {})
            
            # Badge selection
            if "fixed" in strat.lower():
                badge_html = '<span class="badge badge-fixed">Fixed-size</span>'
            elif "semantic" in strat.lower():
                badge_html = '<span class="badge badge-semantic">Semantic</span>'
            else:
                badge_html = '<span class="badge badge-hierarchical">Hierarchical</span>'
                
            ocr_meta_badge = '<span class="badge badge-ocr">OCR Used</span>' if c_ocr else '<span class="badge badge-pymupdf">PyMuPDF</span>'
            
            struct_str = ""
            if struct_meta:
                if "warning" in struct_meta:
                    struct_str = f"⚠️ {struct_meta['warning']}"
                else:
                    parts = []
                    if struct_meta.get("chuong"): parts.append(struct_meta['chuong'])
                    if struct_meta.get("dieu"): parts.append(struct_meta['dieu'])
                    if parts:
                        struct_str = " ➔ ".join(parts)
            
            with st.container():
                st.markdown(f"""
                <div class="chunk-card">
                    <div class="chunk-header">
                        <div>
                            {badge_html} {ocr_meta_badge}
                            <span class="chunk-id">{c_id}</span>
                        </div>
                        <div>
                            <span class="meta-tag">Trang {p_start} - {p_end}</span>
                            <span class="meta-tag">Độ dài: {len(text)} ký tự</span>
                        </div>
                    </div>
                    {f'<div style="font-size:0.85rem; color:#b45309; margin-bottom:8px; font-weight:600;">{struct_str}</div>' if struct_str else ''}
                    <div class="chunk-text">{text}</div>
                </div>
                """, unsafe_allow_html=True)

# TAB 2: STRATEGY COMPARISON REPORT
with tab2:
    st.subheader(f"So sánh Báo cáo Thống kê 3 Chiến lược — {selected_doc_name}")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.markdown("### 📈 Bảng Thống kê Chi tiết")
        comp_data = []
        for s_name, s_key in [("Fixed-size (500/50)", "fixed_size"), ("Semantic (Đoạn/Ngắt câu)", "semantic"), ("Hierarchical (Chương/Điều)", "hierarchical")]:
            s_info = stats.get(s_key, {})
            comp_data.append({
                "Chiến lược Chunking": s_name,
                "Số lượng Chunk": s_info.get("count", 0),
                "Độ dài Min (ký tự)": s_info.get("min_len", 0),
                "Độ dài Max (ký tự)": s_info.get("max_len", 0),
                "Trung bình (ký tự)": s_info.get("avg_len", 0.0)
            })
        st.dataframe(comp_data, use_container_width=True)

    with col_b:
        st.markdown("### 📊 Đánh giá & Nhận xét Chiến lược")
        st.markdown("""
        * **Fixed-size Chunking**:
          * *Ưu điểm*: Đơn giản, độ dài cực kỳ đồng đều ($\sim 500$ ký tự), dễ dự đoán token cho Vector DB.
          * *Nhược điểm*: Có thể cắt ngang ý giữa 2 đoạn văn nếu không căn chỉnh khoảng trắng.
        * **Semantic Chunking**:
          * *Ưu điểm*: Bảo tồn trọn vẹn ngữ nghĩa từng đoạn văn, ngắt tự nhiên tại dấu kết đoạn/kết câu.
          * *Nhược điểm*: Độ dài chunk biến thiên lớn tùy theo độ dài đoạn văn trong PDF gốc.
        * **Hierarchical Chunking**:
          * *Ưu điểm*: Giữ trọn cấu trúc phân cấp pháp lý tiếng Việt (Chương → Điều → Khoản), rất phù hợp tra cứu luật.
          * *Nhược điểm*: Phụ thuộc vào chất lượng trích xuất cấu trúc văn bản.
        """)

# TAB 3: RAW OCR TEXT PREVIEW
with tab3:
    st.subheader(f"Văn bản Raw / OCR hoàn chỉnh — {selected_doc_name}")
    
    if raw_ocr_data:
        st.markdown(f"**Tổng số trang:** `{raw_ocr_data.get('total_pages', 0)}` | **Đã qua LlamaParse OCR:** `{raw_ocr_data.get('ocr_used', False)}`")
        pages = raw_ocr_data.get("pages", [])
        
        if len(pages) > 1:
            selected_page_num = st.slider("Chọn trang hiển thị", 1, len(pages), 1)
        else:
            selected_page_num = 1
            
        if pages:
            p_data = pages[selected_page_num - 1]
            st.markdown(f"#### Nội dung Trang {p_data.get('page', selected_page_num)} (Unicode NFC)")
            st.text_area("Văn bản trích xuất", value=p_data.get("text", ""), height=400)
    else:
        st.info("Chưa tìm thấy file raw OCR tương ứng.")
