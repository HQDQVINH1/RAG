"""
buoi_17/scripts/secure_retrieval_adapter.py
--------------------------------------------
Adapter cho SecureRetriever của Buổi 16.
Tái sử dụng SecureRetriever cũ và chuẩn hóa cấu trúc output đầu ra theo tiêu chuẩn Buổi 17:
- rank
- chunk_id
- document_id
- title
- article
- citation
- allowed_roles
- access_decision
- retrieval_method
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Union
import pandas as pd

# Ensure project root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from src.secure_retriever import SecureRetriever

class SecureRetrievalAdapter:
    def __init__(self, corpus_path: str = None, cache_dir: str = None):
        """
        Khởi tạo Adapter bao bọc SecureRetriever từ Buổi 16.
        """
        self.retriever = SecureRetriever(corpus_path=corpus_path, cache_dir=cache_dir)
        # Fast lookup map for metadata
        self.chunk_lookup = {}
        for _, row in self.retriever.corpus_df.iterrows():
            cid = str(row['chunk_id'])
            self.chunk_lookup[cid] = {
                'document_id': str(row.get('document_id', '')),
                'title': str(row.get('title', '')),
                'article': str(row.get('article', '')) if pd.notna(row.get('article')) else '',
                'so_ky_hieu': str(row.get('so_ky_hieu', '')) if pd.notna(row.get('so_ky_hieu')) else '',
                'allowed_roles_list': row.get('allowed_roles_list', []),
                'text': str(row.get('text', ''))
            }

    def retrieve(self, query: str, user_roles: List[str], method: str = "hybrid_rerank", top_k: int = 5, candidate_k: int = 20) -> List[Dict[str, Any]]:
        """
        Gọi SecureRetriever cũ và chuẩn hóa kết quả đầu ra.
        """
        raw_results = self.retriever.retrieve(
            query=query,
            user_roles=user_roles,
            method=method,
            top_k=top_k,
            candidate_k=candidate_k
        )
        
        normalized_results = []
        for idx, item in enumerate(raw_results, start=1):
            cid = str(item.get('chunk_id'))
            doc_meta = self.chunk_lookup.get(cid, {})
            
            title = str(item.get('title') or doc_meta.get('title', ''))
            article = str(item.get('article') or doc_meta.get('article', ''))
            allowed_roles = item.get('allowed_roles') or doc_meta.get('allowed_roles_list', [])
            
            # Access decision is ALLOWED for returned items
            access_decision = "ALLOWED"
            
            # Citation check / format
            citation = item.get('citation')
            if not citation:
                so_ky_hieu = doc_meta.get('so_ky_hieu') or title
                citation = f"[{so_ky_hieu} | {article} | {cid}]" if article else f"[{so_ky_hieu} | {cid}]"
                
            norm_item = {
                'rank': idx,
                'chunk_id': cid,
                'document_id': str(item.get('document_id') or doc_meta.get('document_id', '')),
                'title': title,
                'article': article,
                'citation': str(citation),
                'allowed_roles': allowed_roles if isinstance(allowed_roles, list) else list(allowed_roles),
                'access_decision': access_decision,
                'retrieval_method': str(item.get('retrieval_method', method)),
                'text': str(item.get('text') or doc_meta.get('text', ''))
            }
            normalized_results.append(norm_item)
            
        return normalized_results

    def build_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Xây dựng chuỗi context an toàn cho LLM từ các chunk đã lọc quyền.
        """
        if not retrieved_chunks:
            return "Không tìm thấy tài liệu phù hợp với quyền truy cập của bạn."
            
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            part = f"--- [TÀI LIỆU {idx}] ---\n" \
                   f"Trích dẫn: {chunk['citation']}\n" \
                   f"Mã Chunk: {chunk['chunk_id']}\n" \
                   f"Tiêu đề: {chunk['title']}\n" \
                   f"Nội dung:\n{chunk['text']}\n"
            context_parts.append(part)
            
        return "\n".join(context_parts)
