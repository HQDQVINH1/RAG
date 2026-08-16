#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: prepare_corpus.py
Mục đích: Chuẩn hóa corpus dữ liệu RAG cho Buổi 14 (Hybrid Search + Reranking + Mini Knowledge Graph).
Đọc dữ liệu từ ../kb+hops/ (metadata.csv, content.csv, relationships.csv)
Tạo file đầu ra: data/processed/chunks_normalized.csv
"""

import os
import re
import sys
import pandas as pd
from bs4 import BeautifulSoup

def clean_text(text: str) -> str:
    """
    Chuẩn hóa chuỗi văn bản:
    - Loại bỏ ký tự thừa, dồn khoảng trắng
    - Giữ nguyên số hiệu Điều, Khoản, mã văn bản
    - Không stemming quá mức
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Loại bỏ khoảng trắng thừa trên mỗi dòng
    lines = [line.strip() for line in text.split('\n')]
    # Loại bỏ dòng rỗng liên tiếp
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            # Thay thế nhiều khoảng trắng ngang bằng 1 khoảng trắng
            line_clean = re.sub(r'[ \t]+', ' ', line)
            cleaned_lines.append(line_clean)
            prev_empty = False
            
    return '\n'.join(cleaned_lines).strip()

def parse_html_to_chunks(html_content: str, doc_id: str, doc_meta: dict) -> list:
    """
    Trích xuất các đoạn văn bản (chunks) từ HTML theo cấu trúc Điều/Khoản/Chương/Mục.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n')
    raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    chunks = []
    current_chapter = ''
    current_section = ''
    current_article = ''
    current_chunk_lines = []
    chunk_idx = 0
    
    title = str(doc_meta.get('title', ''))
    doc_type = str(doc_meta.get('loai_van_ban', ''))
    so_ky_hieu = str(doc_meta.get('so_ky_hieu', ''))
    effective_date = str(doc_meta.get('ngay_co_hieu_luc', '')) if pd.notnull(doc_meta.get('ngay_co_hieu_luc')) else str(doc_meta.get('ngay_ban_hanh', ''))
    status = str(doc_meta.get('tinh_trang_hieu_luc', ''))
    
    for line in raw_lines:
        # Kiểm tra tiêu đề Chương
        if re.match(r'^(Chương|CHƯƠNG)\s+[0-9IVXLCDM]+', line):
            current_chapter = line
        # Kiểm tra tiêu đề Mục
        elif re.match(r'^(Mục|MỤC)\s+\d+', line):
            current_section = line
        # Kiểm tra tiêu đề Điều
        elif re.match(r'^Điều\s+\d+[\.\:]?', line, re.IGNORECASE):
            if current_chunk_lines:
                chunk_text = clean_text('\n'.join(current_chunk_lines))
                if chunk_text:
                    chunk_idx += 1
                    chunks.append({
                        'chunk_id': f"{doc_id}_c{chunk_idx:03d}",
                        'document_id': doc_id,
                        'text': chunk_text,
                        'source_file': 'content.csv',
                        'title': title,
                        'so_ky_hieu': so_ky_hieu,
                        'document_type': doc_type,
                        'chapter': current_chapter,
                        'section': current_section,
                        'article': current_article,
                        'clause': '',
                        'effective_date': effective_date,
                        'status': status
                    })
            current_article = line
            current_chunk_lines = [line]
        else:
            current_chunk_lines.append(line)
            
    # Thêm chunk cuối cùng của văn bản
    if current_chunk_lines:
        chunk_text = clean_text('\n'.join(current_chunk_lines))
        if chunk_text:
            chunk_idx += 1
            chunks.append({
                'chunk_id': f"{doc_id}_c{chunk_idx:03d}",
                'document_id': doc_id,
                'text': chunk_text,
                'source_file': 'content.csv',
                'title': title,
                'so_ky_hieu': so_ky_hieu,
                'document_type': doc_type,
                'chapter': current_chapter,
                'section': current_section,
                'article': current_article,
                'clause': '',
                'effective_date': effective_date,
                'status': status
            })
            
    return chunks

def main():
    # Đảm bảo stdout hỗ trợ utf-8 trên Windows console
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    kb_dir = os.path.abspath(os.path.join(project_root, '..', 'kb+hops'))
    
    metadata_path = os.path.join(kb_dir, 'metadata.csv')
    content_path = os.path.join(kb_dir, 'content.csv')
    
    output_dir = os.path.join(project_root, 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, 'chunks_normalized.csv')
    
    print(f"Đọc dữ liệu nguồn từ: {kb_dir}")
    df_meta = pd.read_csv(metadata_path, encoding='utf-8')
    df_content = pd.read_csv(content_path, encoding='utf-8')
    
    # Ép kiểu id thành string đồng nhất
    df_meta['id'] = df_meta['id'].astype(str)
    df_content['id'] = df_content['id'].astype(str)
    
    meta_dict = df_meta.set_index('id').to_dict(orient='index')
    
    all_chunks = []
    for _, row in df_content.iterrows():
        doc_id = str(row['id'])
        doc_meta = meta_dict.get(doc_id, {})
        chunks = parse_html_to_chunks(str(row['content_html']), doc_id, doc_meta)
        all_chunks.extend(chunks)
        
    df_chunks = pd.DataFrame(all_chunks)
    
    # Kiểm tra các chỉ số yêu cầu
    total_chunks = len(df_chunks)
    total_docs = df_chunks['document_id'].nunique()
    missing_text_count = int(df_chunks['text'].isnull().sum() + (df_chunks['text'] == '').sum())
    duplicate_chunks = int(df_chunks['chunk_id'].duplicated().sum())
    
    # Ghi ra file CSV chuẩn hóa
    df_chunks.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Đã lưu corpus chuẩn hóa tại: {output_csv}\n")
    
    # In kết quả thống kê
    print("=" * 50)
    print("KẾT QUẢ CHUẨN HÓA CORPUS (PROMPT 1)")
    print("=" * 50)
    print(f"Tổng số chunk: {total_chunks}")
    print(f"Số document: {total_docs}")
    print(f"Số chunk thiếu text: {missing_text_count}")
    print(f"Duplicate (chunk_id): {duplicate_chunks}")
    print("-" * 50)
    print("3 SAMPLE RECORDS:")
    for idx, record in enumerate(df_chunks.head(3).to_dict(orient='records'), start=1):
        print(f"\n--- Sample {idx} ---")
        print(f"chunk_id     : {record['chunk_id']}")
        print(f"document_id  : {record['document_id']}")
        print(f"title        : {record['title']}")
        print(f"article      : {record['article']}")
        print(f"effective_date: {record['effective_date']}")
        print(f"text snippet : {repr(record['text'][:150])}...")

if __name__ == '__main__':
    main()
