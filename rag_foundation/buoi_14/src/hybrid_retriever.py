#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hybrid Retriever Module cho Buổi 14.
Kết hợp BM25 Retriever và Dense Retriever sử dụng phương pháp Reciprocal Rank Fusion (RRF).
"""

import pandas as pd
from typing import List, Dict, Any
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever


class HybridRetriever:
    def __init__(self, bm25_retriever: BM25Retriever, dense_retriever: DenseRetriever):
        """
        Khởi tạo HybridRetriever với 2 retriever BM25 và Dense đã được load cùng corpus.
        """
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever

    def search(self, query: str, candidate_k: int = 20, top_k: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Thực hiện Hybrid Search bằng Reciprocal Rank Fusion (RRF).
        - `candidate_k`: Số lượng ứng viên lấy ra từ từng retriever độc lập (Top-N).
        - `top_k`: Số lượng ứng viên kết quả cuối cùng.
        - `rrf_k`: Hằng số làm mượt RRF (mặc định k=60).
        """
        # 1. Lấy Top-N ứng viên từ BM25 và Dense
        bm25_candidates = self.bm25_retriever.search(query, top_k=candidate_k)
        dense_candidates = self.dense_retriever.search(query, top_k=candidate_k)
        
        # 2. Xây dựng tra cứu thứ hạng và thông tin chunk
        chunk_info_map = {}
        bm25_ranks = {}
        dense_ranks = {}
        
        for cand in bm25_candidates:
            cid = cand['chunk_id']
            bm25_ranks[cid] = cand['rank']
            if cid not in chunk_info_map:
                chunk_info_map[cid] = {
                    'chunk_id': cid,
                    'document_id': cand['document_id'],
                    'text': cand['text'],
                    'citation': cand['citation']
                }
                
        for cand in dense_candidates:
            cid = cand['chunk_id']
            dense_ranks[cid] = cand['rank']
            if cid not in chunk_info_map:
                chunk_info_map[cid] = {
                    'chunk_id': cid,
                    'document_id': cand['document_id'],
                    'text': cand['text'],
                    'citation': cand['citation']
                }
                
        # 3. Tính điểm RRF cho từng chunk duy nhất
        all_chunk_ids = set(bm25_ranks.keys()).union(set(dense_ranks.keys()))
        fusion_results = []
        
        for cid in all_chunk_ids:
            b_rank = bm25_ranks.get(cid)
            d_rank = dense_ranks.get(cid)
            
            rrf_score = 0.0
            if b_rank is not None:
                rrf_score += 1.0 / (rrf_k + b_rank)
            if d_rank is not None:
                rrf_score += 1.0 / (rrf_k + d_rank)
                
            info = chunk_info_map[cid]
            fusion_results.append({
                'chunk_id': cid,
                'document_id': info['document_id'],
                'text': info['text'],
                'citation': info['citation'],
                'bm25_rank': b_rank if b_rank is not None else '-',
                'dense_rank': d_rank if d_rank is not None else '-',
                'rrf_score': rrf_score
            })
            
        # 4. Sắp xếp giảm dần theo rrf_score
        fusion_results.sort(key=lambda x: x['rrf_score'], reverse=True)
        
        # 5. Gán final_rank và cắt top_k
        final_top_k = []
        for rank_idx, item in enumerate(fusion_results[:top_k], start=1):
            item_copy = item.copy()
            item_copy['final_rank'] = rank_idx
            item_copy['rrf_score'] = round(item_copy['rrf_score'], 5)
            final_top_k.append(item_copy)
            
        return final_top_k
