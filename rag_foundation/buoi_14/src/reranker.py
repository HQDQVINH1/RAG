#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reranker Module cho Buổi 14.
Sử dụng Cross-Encoder để tái xếp hạng (re-rank) tập ứng viên Top-N từ Hybrid Search.
"""

import os
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Khởi tạo Cross-Encoder Reranker.
        - `model_name`: Tên mô hình CrossEncoder (mặc định 'cross-encoder/ms-marco-MiniLM-L-6-v2').
        """
        self.model_name = model_name
        print(f"[Reranker] Đang tải mô hình Cross-Encoder: {self.model_name}...")
        
        try:
            self.model = CrossEncoder(self.model_name, local_files_only=True)
            print(f"[Reranker] Đã load mô hình offline thành công: {self.model_name}")
        except Exception:
            self.model = CrossEncoder(self.model_name)
            print(f"[Reranker] Đã kết nối và load mô hình: {self.model_name}")

    def rerank(self, query: str, hybrid_candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Tái xếp hạng danh sách ứng viên `hybrid_candidates` dựa trên Cross-Encoder score.
        - `hybrid_candidates`: Danh sách ứng viên từ Hybrid Search (chứa final_rank ban đầu làm hybrid_rank).
        - `top_k`: Số lượng kết quả sau khi rerank.
        """
        if not hybrid_candidates:
            return []
            
        # Chuẩn bị cặp (query, candidate_text)
        pairs = [(query, cand['text']) for cand in hybrid_candidates]
        
        # Dự đoán điểm Relevance bằng Cross-Encoder
        scores = self.model.predict(pairs)
        
        # Tạo danh sách ứng viên đính kèm điểm rerank score
        reranked_items = []
        for idx, cand in enumerate(hybrid_candidates):
            rerank_score = float(scores[idx])
            item = cand.copy()
            item['hybrid_rank'] = cand.get('final_rank', idx + 1)
            item['hybrid_score'] = cand.get('rrf_score', 0.0)
            item['rerank_score'] = round(rerank_score, 4)
            reranked_items.append(item)
            
        # Sắp xếp giảm dần theo rerank_score
        reranked_items.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Gán final_rank mới sau khi rerank
        final_top_k = []
        for rank_idx, item in enumerate(reranked_items[:top_k], start=1):
            item_copy = item.copy()
            item_copy['final_rank'] = rank_idx
            final_top_k.append(item_copy)
            
        return final_top_k
