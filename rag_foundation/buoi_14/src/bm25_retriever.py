#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BM25 Retriever Module cho Buổi 14.
Thực hiện BM25 lexical search trên tập corpus chunks_normalized.csv.
"""

import re
import pandas as pd
from rank_bm25 import BM25Okapi


def tokenize_vietnamese_text(text: str) -> list:
    """
    Tokenizer giữ nguyên:
    - Mã văn bản (vd: 01/2014/TT-NHNN, 44/2014/TT-NHNN)
    - Số điều / số khoản (vd: điều 1, khoản 2)
    - Từ tiếng Việt và ký tự đặc thù pháp lý
    """
    if not text or not isinstance(text, str):
        return []
    
    # Chuyển về chữ thường
    text_lower = text.lower()
    
    # Tách từ dựa trên các ký tự khoảng trắng và dấu câu thông thường
    # Giữ lại chữ cái, chữ số, dấu gạch chéo (/), gạch ngang (-), gạch dưới (_)
    tokens = re.findall(r'[\w/%\-]+', text_lower)
    return tokens


class BM25Retriever:
    def __init__(self, corpus_df: pd.DataFrame):
        """
        Khởi tạo BM25Retriever với DataFrame corpus chuẩn hóa.
        """
        self.corpus_df = corpus_df.copy()
        self.corpus_df['chunk_id'] = self.corpus_df['chunk_id'].astype(str)
        self.corpus_df['document_id'] = self.corpus_df['document_id'].astype(str)
        
        # Tokenize từng chunk text
        self.tokenized_corpus = [
            tokenize_vietnamese_text(str(doc_text))
            for doc_text in self.corpus_df['text']
        ]
        
        # Khởi tạo mô hình BM25Okapi
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def generate_citation(self, row: pd.Series) -> str:
        """
        Tạo trích dẫn (citation) chuẩn dựa trên metadata thật.
        """
        title = str(row.get('title', '')).strip()
        so_ky_hieu = str(row.get('so_ky_hieu', '')).strip()
        raw_article = row.get('article', '')
        article = '' if pd.isna(raw_article) or str(raw_article).strip().lower() == 'nan' else str(raw_article).strip()
        chunk_id = str(row.get('chunk_id', '')).strip()
        
        doc_ref = so_ky_hieu if (so_ky_hieu and so_ky_hieu.lower() != 'nan') else title
        if article:
            return f"[{doc_ref} | {article} | {chunk_id}]"
        else:
            return f"[{doc_ref} | {chunk_id}]"

    def search(self, query: str, top_k: int = 5) -> list:
        """
        Thực hiện BM25 Search cho truy vấn `query`.
        Trả về danh sách dicts theo schema thống nhất:
        [rank, chunk_id, document_id, text, retrieval_score, retrieval_method, citation]
        """
        tokenized_query = tokenize_vietnamese_text(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Lấy top_k chỉ số có điểm cao nhất
        top_indices = scores.argsort()[::-1][:top_k]
        
        results = []
        for rank_idx, idx in enumerate(top_indices, start=1):
            score = float(scores[idx])
            row = self.corpus_df.iloc[idx]
            
            results.append({
                'rank': rank_idx,
                'chunk_id': str(row['chunk_id']),
                'document_id': str(row['document_id']),
                'text': str(row['text']),
                'retrieval_score': round(score, 4),
                'retrieval_method': 'bm25',
                'citation': self.generate_citation(row)
            })
            
        return results
