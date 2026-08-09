import re
import uuid
from typing import List, Dict, Any

def create_chunk_object(
    strategy: str,
    source: str,
    page_start: int,
    page_end: int,
    text: str,
    ocr_used: bool = False,
    structure_metadata: Dict[str, Any] = None,
    chunk_index: int = 1
) -> Dict[str, Any]:
    """Helper to create standardized Chunk metadata object."""
    return {
        "chunk_id": f"{source}_{strategy}_{chunk_index:03d}",
        "strategy": strategy,
        "source": source,
        "page_start": page_start,
        "page_end": page_end,
        "ocr_used": ocr_used,
        "language": "vi",
        "text": text.strip(),
        "structure_metadata": structure_metadata or {}
    }

def align_to_word_boundary(text: str, index: int) -> int:
    """Adjusts character index lùi về khoảng trắng gần nhất để không cắt ngang giữa từ."""
    if index <= 0:
        return 0
    if index >= len(text):
        return len(text)
    if text[index].isspace() or text[index - 1].isspace():
        return index
    # Tìm vị trí khoảng trắng lùi về trước (tối đa 20 ký tự)
    curr = index
    while curr > 0 and (index - curr) < 20 and not text[curr].isspace():
        curr -= 1
    if text[curr].isspace():
        return curr + 1
    return index

# ----------------------------------------------------
# 1. FIXED-SIZE CHUNKING (Word-Boundary Aware)
# ----------------------------------------------------
def fixed_size_chunking(
    doc_data: Dict[str, Any],
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict[str, Any]]:
    """Fixed-size chunking with character/token overlap aligned to word boundaries."""
    source = doc_data["source"]
    pages = doc_data["pages"]
    chunks = []
    chunk_idx = 1
    
    full_text = ""
    page_map = []
    
    for p in pages:
        p_num = p["page"]
        p_text = p["text"]
        start_offset = len(full_text)
        full_text += p_text + "\n\n"
        end_offset = len(full_text)
        page_map.append((start_offset, end_offset, p_num, p.get("ocr_used", False)))
        
    if not full_text.strip():
        return []
        
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size
        
    start_char = 0
    total_len = len(full_text)
    
    while start_char < total_len:
        # Căn chỉnh điểm bắt đầu tránh ngắt đôi từ
        aligned_start = align_to_word_boundary(full_text, start_char)
        raw_end = min(aligned_start + chunk_size, total_len)
        aligned_end = align_to_word_boundary(full_text, raw_end) if raw_end < total_len else total_len
        
        chunk_str = full_text[aligned_start:aligned_end].strip()
        
        if chunk_str:
            p_start = 1
            p_end = 1
            ocr_flag = False
            for s_off, e_off, p_num, p_ocr in page_map:
                if s_off <= aligned_start < e_off:
                    p_start = p_num
                if s_off < aligned_end <= e_off:
                    p_end = p_num
                if p_ocr:
                    ocr_flag = True
                    
            chunk_obj = create_chunk_object(
                strategy="fixed-size",
                source=source,
                page_start=p_start,
                page_end=max(p_start, p_end),
                text=chunk_str,
                ocr_used=ocr_flag,
                chunk_index=chunk_idx
            )
            chunks.append(chunk_obj)
            chunk_idx += 1
            
        start_char += step
        if aligned_end >= total_len:
            break
            
    return chunks

# ----------------------------------------------------
# 2. SEMANTIC CHUNKING
# ----------------------------------------------------
def semantic_chunking(
    doc_data: Dict[str, Any],
    target_size: int = 500
) -> List[Dict[str, Any]]:
    """Semantic chunking breaking naturally at paragraphs, line breaks, or sentences."""
    source = doc_data["source"]
    pages = doc_data["pages"]
    chunks = []
    chunk_idx = 1
    
    current_chunk_text = ""
    current_page_start = 1
    current_page_end = 1
    current_ocr = False
    
    for p in pages:
        p_num = p["page"]
        p_text = p["text"]
        p_ocr = p.get("ocr_used", False)
        
        paragraphs = [para.strip() for para in re.split(r'\n\s*\n|\r\n\r\n', p_text) if para.strip()]
        
        for para in paragraphs:
            if not current_chunk_text:
                current_page_start = p_num
                current_ocr = p_ocr
                
            current_page_end = p_num
            if p_ocr:
                current_ocr = True
                
            if len(current_chunk_text) + len(para) <= target_size:
                current_chunk_text += ("\n\n" if current_chunk_text else "") + para
            else:
                if current_chunk_text:
                    chunks.append(create_chunk_object(
                        strategy="semantic",
                        source=source,
                        page_start=current_page_start,
                        page_end=current_page_end,
                        text=current_chunk_text,
                        ocr_used=current_ocr,
                        chunk_index=chunk_idx
                    ))
                    chunk_idx += 1
                
                current_chunk_text = para
                current_page_start = p_num
                current_ocr = p_ocr
                
    if current_chunk_text.strip():
        chunks.append(create_chunk_object(
            strategy="semantic",
            source=source,
            page_start=current_page_start,
            page_end=current_page_end,
            text=current_chunk_text,
            ocr_used=current_ocr,
            chunk_index=chunk_idx
        ))
        
    return chunks

# ----------------------------------------------------
# 3. HIERARCHICAL CHUNKING
# ----------------------------------------------------
def hierarchical_chunking(
    doc_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Hierarchical legal structure chunking: Chương -> Mục -> Điều -> Khoản.
    Emits warning if document lacks structure; never invents false headings.
    Matches variations in font encoding (Chương/Chuong/Chuang, Điều/Dieu/Didu).
    """
    source = doc_data["source"]
    pages = doc_data["pages"]
    chunks = []
    chunk_idx = 1
    
    full_text = "\n".join(p["text"] for p in pages)
    
    chuong_pattern = re.compile(r'(?:^|\b)(?:Chương|Chuong|Chuang)\s+[IVXLCDM\d]+[\.\:\s]', re.IGNORECASE)
    muc_pattern = re.compile(r'(?:^|\b)(?:Mục|Muc)\s+\d+[\.\:\s]', re.IGNORECASE)
    dieu_pattern = re.compile(r'(?:^|\b)(?:Điều|Dieu|Didu)\s+\d+[\.\:\s]', re.IGNORECASE)
    
    matches = list(dieu_pattern.finditer(full_text))
    
    if not matches:
        print(f"[CẢNH BÁO HIERARCHICAL] Văn bản '{source}' không chứa cấu trúc phân cấp (Chương/Mục/Điều) rõ ràng. Giữ nguyên ranh giới đoạn để tránh tạo heading giả.")
        sem_chunks = semantic_chunking(doc_data)
        for sc in sem_chunks:
            sc["strategy"] = "hierarchical"
            sc["chunk_id"] = f"{source}_hierarchical_{chunk_idx:03d}"
            sc["structure_metadata"] = {"warning": "Không tìm thấy cấu trúc Chương/Điều trong văn bản gốc"}
            chunk_idx += 1
        return sem_chunks
        
    current_chuong = ""
    current_muc = ""
    current_dieu = ""
    
    current_chunk_lines = []
    current_page_start = 1
    current_page_end = 1
    current_ocr = False
    
    for p in pages:
        p_num = p["page"]
        p_lines = p["text"].split('\n')
        p_ocr = p.get("ocr_used", False)
        
        for line in p_lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            m_chuong = chuong_pattern.search(line_str)
            m_muc = muc_pattern.search(line_str)
            m_dieu = dieu_pattern.search(line_str)
            
            if m_chuong:
                current_chuong = line_str
            elif m_muc:
                current_muc = line_str
            elif m_dieu:
                if current_chunk_lines:
                    chunk_text = "\n".join(current_chunk_lines)
                    chunks.append(create_chunk_object(
                        strategy="hierarchical",
                        source=source,
                        page_start=current_page_start,
                        page_end=current_page_end,
                        text=chunk_text,
                        ocr_used=current_ocr,
                        structure_metadata={
                            "chuong": current_chuong,
                            "muc": current_muc,
                            "dieu": current_dieu
                        },
                        chunk_index=chunk_idx
                    ))
                    chunk_idx += 1
                    current_chunk_lines = []
                    
                current_dieu = line_str
                current_page_start = p_num
                current_ocr = p_ocr
                
            current_chunk_lines.append(line_str)
            current_page_end = p_num
            if p_ocr:
                current_ocr = True
                
    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines)
        chunks.append(create_chunk_object(
            strategy="hierarchical",
            source=source,
            page_start=current_page_start,
            page_end=current_page_end,
            text=chunk_text,
            ocr_used=current_ocr,
            structure_metadata={
                "chuong": current_chuong,
                "muc": current_muc,
                "dieu": current_dieu
            },
            chunk_index=chunk_idx
        ))
        
    return chunks

# ----------------------------------------------------
# 4. CHUNKING STATISTICS CALCULATOR
# ----------------------------------------------------
def compute_chunk_stats(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute min, max, average length and total count of chunks."""
    if not chunks:
        return {"count": 0, "min_len": 0, "max_len": 0, "avg_len": 0.0}
        
    lengths = [len(c["text"]) for c in chunks]
    return {
        "count": len(chunks),
        "min_len": min(lengths),
        "max_len": max(lengths),
        "avg_len": round(sum(lengths) / len(lengths), 2)
    }
