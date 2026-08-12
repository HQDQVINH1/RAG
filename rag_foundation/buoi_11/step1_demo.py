"""
BƯỚC 1: Phân tích HTML, Làm sạch và Phân tách cấu trúc phân cấp (Chunking)

File demo này tập trung thực hiện và minh họa trực quan Bước 1:
- Làm sạch nội dung HTML (loại bỏ style, script, HTML tags cồng kềnh).
- Phân tách văn bản thành cấu trúc phân cấp Cha-Con (Document -> Chương -> Mục -> Điều -> Đoạn/Khoản).
- Thiết lập quan hệ PART_OF (con -> Document), PARENT_OF (cấp cha -> cấp con), và NEXT (trình tự đọc).
- In ra màn hình console kết quả phân tách mẫu trực quan.
"""

import csv
import re
import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

csv.field_size_limit(sys.maxsize)

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_FILE = os.path.join(BASE_DIR, "content.csv")

def clean_html(html_str):
    """Làm sạch HTML nhưng giữ lại cấu trúc văn bản."""
    soup = BeautifulSoup(html_str, 'html.parser')
    for s in soup(['script', 'style', 'meta', 'link']):
        s.decompose()
        
    elements = []
    for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'table']):
        if tag.name == 'table':
            text = tag.get_text(separator=' | ', strip=True)
        else:
            text = tag.get_text(separator=' ', strip=True)
            
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text:
            if elements and elements[-1][1] == text:
                continue
            elements.append((tag.name, text))
    return elements

def chunk_hierarchical(doc_id, elements):
    """
    Phân tách phân cấp:
    Document -> Chapter -> Section -> Article -> Clause
    """
    chunks = []
    current_chuong = None
    current_muc = None
    current_dieu = None
    
    chuong_pattern = re.compile(r'^(Chương\s+[IVXLCDM\d]+[.:]?\s*.*)', re.IGNORECASE)
    muc_pattern = re.compile(r'^(Mục\s+\d+[.:]?\s*.*)', re.IGNORECASE)
    dieu_pattern = re.compile(r'^(Điều\s+\d+[.:]?\s*.*)', re.IGNORECASE)
    
    chunk_idx = 0
    prev_chunk_id = None
    
    for tag_name, text in elements:
        chunk_idx += 1
        chunk_id = f"chunk_{doc_id}_{chunk_idx}"
        
        chuong_m = chuong_pattern.match(text)
        muc_m = muc_pattern.match(text)
        dieu_m = dieu_pattern.match(text)
        
        if chuong_m:
            chunk_type = "CHAPTER"
            title = text
            parent_id = f"doc_{doc_id}" # PART_OF doc
            current_chuong = chunk_id
            current_muc = None
            current_dieu = None
        elif muc_m:
            chunk_type = "SECTION"
            title = text
            parent_id = current_chuong if current_chuong else f"doc_{doc_id}"
            current_muc = chunk_id
            current_dieu = None
        elif dieu_m:
            chunk_type = "ARTICLE"
            title = text
            if current_muc:
                parent_id = current_muc
            elif current_chuong:
                parent_id = current_chuong
            else:
                parent_id = f"doc_{doc_id}"
            current_dieu = chunk_id
        else:
            chunk_type = "CLAUSE"
            title = text[:50] + "..." if len(text) > 50 else text
            if current_dieu:
                parent_id = current_dieu
            elif current_muc:
                parent_id = current_muc
            elif current_chuong:
                parent_id = current_chuong
            else:
                parent_id = f"doc_{doc_id}"
                
        chunk = {
            "id": chunk_id,
            "doc_id": doc_id,
            "type": chunk_type,
            "title": title,
            "clean_text": text,
            "parent_id": parent_id,
            "prev_id": prev_chunk_id,
            "next_id": None
        }
        
        chunks.append(chunk)
        
        if len(chunks) > 1:
            chunks[-2]["next_id"] = chunk_id
            
        prev_chunk_id = chunk_id
        
    return chunks

def main():
    print("=" * 80)
    print("  BƯỚC 1: DEMO THUẬT TOÁN LÀM SẠCH HTML & PHÂN TÁCH CẤU TRÚC PHÂN CẤP (CHUNKING)")
    print("=" * 80)
    
    with open(CONTENT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        total_docs = 0
        total_chunks = 0
        
        for row in reader:
            doc_id = row["id"]
            html_raw = row["content_html"]
            total_docs += 1
            
            # 1. Cleaning
            elements = clean_html(html_raw)
            # 2. Chunking
            chunks = chunk_hierarchical(doc_id, elements)
            total_chunks += len(chunks)
            
            # In mẫu chi tiết văn bản đầu tiên (Doc ID: 44209 - Thông tư 01/2014/TT-NHNN)
            if total_docs == 1:
                print(f"\n[VĂN BẢN MẪU] Document ID: {doc_id}")
                print(f"Kích thước HTML gốc: {len(html_raw):,} ký tự")
                print(f"Số lượng phần tử trích xuất sạch: {len(elements)}")
                print(f"Số lượng phân đoạn Chunks được phân tách: {len(chunks)}")
                print("-" * 80)
                print(f"{'Chunk ID':<20} | {'Loại (Type)':<10} | {'Cấp Cha (Parent)':<20} | {'Trình tự Kế tiếp (NEXT)':<20}")
                print("-" * 80)
                
                for c in chunks[:15]:
                    p_id = c['parent_id'] if c['parent_id'] else "None"
                    n_id = c['next_id'] if c['next_id'] else "None"
                    print(f"{c['id']:<20} | {c['type']:<10} | {p_id:<20} | {n_id:<20}")
                    print(f"   ↳ Nội dung sạch: {c['clean_text'][:90]}...")
                    print("-" * 80)

    print("\n" + "=" * 80)
    print(f"TỔNG KẾT BƯỚC 1:")
    print(f"  - Số lượng tài liệu đã phân tích: {total_docs}")
    print(f"  - Tổng số Chunks được tạo ra trên 15 tài liệu: {total_chunks}")
    print(f"  - Các nút HTML cồng kềnh đã được loại bỏ, chỉ giữ lại `clean_text` và `title`.")
    print(f"  - Quan hệ [:PART_OF] liên kết trực tiếp tất cả chunk về nút gốc Document ({'doc_<id>'}).")
    print(f"  - Quan hệ [:PARENT_OF] liên kết cây phân cấp (Chương ➔ Mục ➔ Điều ➔ Khoản).")
    print(f"  - Quan hệ [:NEXT] nối các chunk anh em theo đúng thứ tự đọc.")
    print("=" * 80)

if __name__ == "__main__":
    main()
