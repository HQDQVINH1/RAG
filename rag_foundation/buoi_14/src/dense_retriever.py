#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dense Retriever Module cho Buổi 14.
Thực hiện Dense Vector Retrieval sử dụng SentenceTransformers + Caching.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


class DenseRetriever:
    def __init__(self, corpus_df: pd.DataFrame, model_name: str = "bkai-foundation-models/vietnamese-bi-encoder", cache_dir: str = "cache"):
        """
        Khởi tạo DenseRetriever.
        - `model_name`: Mô hình embedding tiếng Việt/đa ngôn ngữ.
        - `cache_dir`: Thư mục lưu cache embeddings.
        """
        self.corpus_df = corpus_df.copy()
        self.corpus_df['chunk_id'] = self.corpus_df['chunk_id'].astype(str)
        self.corpus_df['document_id'] = self.corpus_df['document_id'].astype(str)
        
        self.model_name = model_name
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Đường dẫn lưu cache embedding
        sanitized_model_name = model_name.replace('/', '_')
        self.cache_file = os.path.join(self.cache_dir, f"dense_embeddings_{sanitized_model_name}.pkl")
        
        print(f"[DenseRetriever] Khởi tạo mô hình: {self.model_name}...")
        try:
            self.model = SentenceTransformer(self.model_name, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(self.model_name)
        
        # Load hoặc tạo mới embeddings
        self.embeddings = self._get_or_create_embeddings()

    def _get_or_create_embeddings(self) -> np.ndarray:
        """
        Kiểm tra cache: nếu có sẵn cache embeddings cho corpus hiện tại thì load,
        ngược lại mã hóa toàn bộ corpus và lưu cache.
        """
        chunk_ids = list(self.corpus_df['chunk_id'])
        
        if os.path.exists(self.cache_file):
            print(f"[DenseRetriever] Đang load embeddings từ cache: {self.cache_file}")
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    
                # Kiểm tra cache có khớp với chunk_ids hiện tại không
                if cache_data.get('chunk_ids') == chunk_ids:
                    print(f"[DenseRetriever] Load cache thành công ({len(cache_data['embeddings'])} vectors).")
                    return cache_data['embeddings']
                else:
                    print("[DenseRetriever] Cache không khớp với corpus hiện tại, tiến hành tạo lại cache...")
            except Exception as e:
                print(f"[DenseRetriever] Lỗi khi đọc cache: {e}, tạo lại cache...")

        print(f"[DenseRetriever] Đang tạo vector embedding cho {len(self.corpus_df)} chunks...")
        texts = list(self.corpus_df['text'])
        
        # Encode và normalize vector
        embeddings = self.model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Lưu vào cache file
        cache_data = {
            'chunk_ids': chunk_ids,
            'embeddings': embeddings
        }
        with open(self.cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"[DenseRetriever] Đã lưu cache embeddings tại: {self.cache_file}")
        
        return embeddings

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
        Thực hiện Dense Vector Search cho truy vấn `query`.
        Trả về danh sách dicts theo schema thống nhất:
        [rank, chunk_id, document_id, text, retrieval_score, retrieval_method, citation]
        """
        query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # Cosine similarity (do cả vector corpus và query vector đã normalized -> dùng dot product)
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Top_k chỉ số có điểm tương đồng cao nhất
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for rank_idx, idx in enumerate(top_indices, start=1):
            score = float(similarities[idx])
            row = self.corpus_df.iloc[idx]
            
            results.append({
                'rank': rank_idx,
                'chunk_id': str(row['chunk_id']),
                'document_id': str(row['document_id']),
                'text': str(row['text']),
                'retrieval_score': round(score, 4),
                'retrieval_method': 'dense',
                'citation': self.generate_citation(row)
            })
            
        return results
