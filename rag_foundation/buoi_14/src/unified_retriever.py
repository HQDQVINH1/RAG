#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Retriever Module cho Buổi 14.
Tích hợp thống nhất 4 phương pháp retrieval:
- bm25
- dense
- hybrid
- hybrid_rerank

Đồng thời trích xuất GRAPH HINTS (thông tin định hướng Graph RAG) cho các chunk được kết xuất.
"""

import os
import pandas as pd
from typing import List, Dict, Any
from dotenv import load_dotenv

from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker


class UnifiedRetriever:
    def __init__(self, corpus_path: str, cache_dir: str):
        """
        Khởi tạo Unified Retriever và nạp các retriever thành phần.
        """
        self.corpus_df = pd.read_csv(corpus_path, encoding='utf-8')
        self.cache_dir = cache_dir
        
        print("[UnifiedRetriever] Đang nạp BM25 Retriever...")
        self.bm25 = BM25Retriever(self.corpus_df)
        
        print("[UnifiedRetriever] Đang nạp Dense Retriever (bkai-foundation-models)...")
        self.dense = DenseRetriever(self.corpus_df, model_name="bkai-foundation-models/vietnamese-bi-encoder", cache_dir=cache_dir)
        
        print("[UnifiedRetriever] Đang nạp Hybrid Retriever (RRF)...")
        self.hybrid = HybridRetriever(self.bm25, self.dense)
        
        print("[UnifiedRetriever] Đang nạp Reranker (Cross-Encoder)...")
        self.reranker = Reranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")

    def retrieve(self, question: str, method: str = "hybrid_rerank", top_k: int = 5, candidate_k: int = 20) -> List[Dict[str, Any]]:
        """
        Hàm retrieval thống nhất.
        - `method`: 'bm25', 'dense', 'hybrid', 'hybrid_rerank'
        - `top_k`: Số lượng kết quả trả về
        - `candidate_k`: Số ứng viên rút trích trước khi fusion/rerank
        """
        method = method.lower().strip()
        
        if method == "bm25":
            raw_res = self.bm25.search(question, top_k=top_k)
            for r in raw_res:
                r['score'] = r['retrieval_score']
            return raw_res
            
        elif method == "dense":
            raw_res = self.dense.search(question, top_k=top_k)
            for r in raw_res:
                r['score'] = r['retrieval_score']
            return raw_res
            
        elif method == "hybrid":
            raw_res = self.hybrid.search(question, candidate_k=candidate_k, top_k=top_k)
            for r in raw_res:
                r['score'] = r['rrf_score']
                r['retrieval_method'] = 'hybrid'
            return raw_res
            
        elif method == "hybrid_rerank":
            candidates = self.hybrid.search(question, candidate_k=candidate_k, top_k=candidate_k)
            reranked = self.reranker.rerank(question, candidates, top_k=top_k)
            for r in reranked:
                r['score'] = r['rerank_score']
                r['retrieval_method'] = 'hybrid_rerank'
            return reranked
            
        else:
            raise ValueError(f"Phương pháp không hợp lệ: {method}. Vui lòng chọn trong: ['bm25', 'dense', 'hybrid', 'hybrid_rerank']")

    def get_graph_hints(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trích xuất GRAPH HINTS trực tiếp (1-hop) phục vụ đường dẫn sang Graph RAG bài sau.
        """
        retrieved_doc_ids = sorted(list(set(r['document_id'] for r in results)))
        retrieved_chunk_ids = [r['chunk_id'] for r in results]
        
        # Đọc credentials từ .env
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        load_dotenv(os.path.join(project_root, '.env'))
        
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "Vinh1989")
        
        relations_hint = []
        neo4j_available = False
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            driver.verify_connectivity()
            neo4j_available = True
            
            with driver.session() as session:
                # Truy vấn quan hệ trực tiếp 1-hop giữa các VanBan retrieved
                query = """
                MATCH (v1:VanBan {lab_session: "buoi_14"})-[r]->(v2:VanBan {lab_session: "buoi_14"})
                WHERE v1.id IN $doc_ids OR v2.id IN $doc_ids
                RETURN v1.id AS source_doc, v1.title AS source_title, type(r) AS rel_type, r.relationship_desc AS desc, v2.id AS target_doc, v2.title AS target_title
                """
                records = session.run(query, {'doc_ids': retrieved_doc_ids}).data()
                for rec in records:
                    relations_hint.append({
                        'source': rec['source_doc'],
                        'target': rec['target_doc'],
                        'relation': rec['rel_type'],
                        'description': rec['desc']
                    })
            driver.close()
        except Exception:
            neo4j_available = False
            # Fallback local reading từ relationships.csv nếu Neo4j offline
            rel_csv = os.path.join(project_root, '..', 'kb+hops', 'relationships.csv')
            if os.path.exists(rel_csv):
                df_rel = pd.read_csv(rel_csv, encoding='utf-8')
                for _, row in df_rel.iterrows():
                    d1 = str(row['doc_id'])
                    d2 = str(row['other_doc_id'])
                    if d1 in retrieved_doc_ids or d2 in retrieved_doc_ids:
                        relations_hint.append({
                            'source': d1,
                            'target': d2,
                            'relation': str(row['relationship_type']),
                            'description': str(row.get('relationship', ''))
                        })

        return {
            'retrieved_document_ids': retrieved_doc_ids,
            'retrieved_chunk_ids': retrieved_chunk_ids,
            'neo4j_status': 'CONNECTED' if neo4j_available else 'OFFLINE (Fallback to local CSV)',
            'direct_relations': relations_hint
        }
