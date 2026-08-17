"""
buoi_14/src/secure_retriever.py
-------------------------------
Secure Retrieval Pipeline cho Buổi 15.
Tích hợp kiểm soát truy cập dựa trên vai trò (RBAC) cho các phương thức retrieval:
- BM25 Search (lọc quyền)
- Dense Search (lọc quyền)
- Hybrid Search (RRF trên ứng viên đã lọc quyền)
- Hybrid Rerank (Cross-Encoder trên ứng viên đã lọc quyền)
- Graph Retrieval (Neo4j Cypher filtering với `WHERE any(role IN d.allowed_roles WHERE role IN $user_roles)`)
"""

import os
import json
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any, Union

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv

from src.bm25_retriever import BM25Retriever, tokenize_vietnamese_text
from src.dense_retriever import DenseRetriever
from src.reranker import Reranker
from src.config import get_neo4j_config, VALID_ROLES

class SecureRetriever:
    def __init__(self, corpus_path: str = None, cache_dir: str = None):
        """
        Khởi tạo SecureRetriever với dữ liệu chunks_secure.csv
        """
        project_root = Path(__file__).resolve().parent.parent
        
        if corpus_path is None:
            corpus_path = project_root / "data" / "processed" / "chunks_secure.csv"
        if cache_dir is None:
            cache_dir = project_root / "cache"
            
        self.corpus_path = Path(corpus_path)
        self.cache_dir = Path(cache_dir)
        
        print(f"[SecureRetriever] Đang nạp dữ liệu bảo mật từ: {self.corpus_path}")
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file dữ liệu bảo mật: {self.corpus_path}")
            
        self.corpus_df = pd.read_csv(self.corpus_path, encoding='utf-8')
        
        # Parse allowed_roles sang python list và set để kiểm tra nhanh O(1)
        def parse_roles(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return [r.strip() for r in val.split(',')]
            elif isinstance(val, list):
                return val
            return []

        self.corpus_df['allowed_roles_list'] = self.corpus_df['allowed_roles'].apply(parse_roles)
        self.corpus_df['allowed_roles_set'] = self.corpus_df['allowed_roles_list'].apply(set)
        
        # Khởi tạo các retriever thành phần
        print("[SecureRetriever] Khởi tạo BM25 Retriever...")
        self.bm25 = BM25Retriever(self.corpus_df)
        
        print("[SecureRetriever] Khởi tạo Dense Retriever...")
        self.dense = DenseRetriever(self.corpus_df, cache_dir=str(self.cache_dir))
        
        print("[SecureRetriever] Khởi tạo Cross-Encoder Reranker...")
        self.reranker = Reranker()
        
        # Cấu hình Neo4j
        self.neo4j_config = get_neo4j_config()

    def _is_accessible(self, chunk_roles_set: set, user_roles: List[str]) -> bool:
        """
        Kiểm tra xem chunk có thể truy cập bởi user_roles không.
        Trả về True nếu user_roles và chunk_roles có ít nhất 1 role chung.
        """
        if not user_roles:
            return False
        return bool(chunk_roles_set.intersection(set(user_roles)))

    def search_bm25(self, query: str, user_roles: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        BM25 Search có lọc quyền bảo mật.
        """
        tokenized_query = tokenize_vietnamese_text(query)
        scores = self.bm25.bm25.get_scores(tokenized_query)
        sorted_indices = scores.argsort()[::-1]
        
        results = []
        rank = 1
        for idx in sorted_indices:
            row = self.corpus_df.iloc[idx]
            if self._is_accessible(row['allowed_roles_set'], user_roles):
                score = float(scores[idx])
                results.append({
                    'rank': rank,
                    'final_rank': rank,
                    'chunk_id': str(row['chunk_id']),
                    'document_id': str(row['document_id']),
                    'text': str(row['text']),
                    'allowed_roles': row['allowed_roles_list'],
                    'retrieval_score': round(score, 4),
                    'score': round(score, 4),
                    'retrieval_method': 'bm25',
                    'citation': self.bm25.generate_citation(row)
                })
                rank += 1
                if len(results) >= top_k:
                    break
        return results

    def search_dense(self, query: str, user_roles: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Dense Search có lọc quyền bảo mật.
        """
        query_vector = self.dense.model.encode([query], normalize_embeddings=True)[0]
        scores = np.dot(self.dense.embeddings, query_vector)
        sorted_indices = scores.argsort()[::-1]
        
        results = []
        rank = 1
        for idx in sorted_indices:
            row = self.corpus_df.iloc[idx]
            if self._is_accessible(row['allowed_roles_set'], user_roles):
                score = float(scores[idx])
                results.append({
                    'rank': rank,
                    'final_rank': rank,
                    'chunk_id': str(row['chunk_id']),
                    'document_id': str(row['document_id']),
                    'text': str(row['text']),
                    'allowed_roles': row['allowed_roles_list'],
                    'retrieval_score': round(score, 4),
                    'score': round(score, 4),
                    'retrieval_method': 'dense',
                    'citation': self.dense.generate_citation(row)
                })
                rank += 1
                if len(results) >= top_k:
                    break
        return results

    def search_hybrid(self, query: str, user_roles: List[str], candidate_k: int = 20, top_k: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Hybrid Search (RRF) chỉ làm việc trên ứng viên đã vượt qua lọc quyền.
        """
        bm25_cands = self.search_bm25(query, user_roles=user_roles, top_k=candidate_k)
        dense_cands = self.search_dense(query, user_roles=user_roles, top_k=candidate_k)
        
        chunk_map = {}
        bm25_ranks = {}
        dense_ranks = {}
        
        for cand in bm25_cands:
            cid = cand['chunk_id']
            bm25_ranks[cid] = cand['rank']
            if cid not in chunk_map:
                chunk_map[cid] = cand
                
        for cand in dense_cands:
            cid = cand['chunk_id']
            dense_ranks[cid] = cand['rank']
            if cid not in chunk_map:
                chunk_map[cid] = cand
                
        all_cids = set(bm25_ranks.keys()).union(set(dense_ranks.keys()))
        fusion_results = []
        
        for cid in all_cids:
            b_rank = bm25_ranks.get(cid)
            d_rank = dense_ranks.get(cid)
            
            rrf_score = 0.0
            if b_rank is not None:
                rrf_score += 1.0 / (rrf_k + b_rank)
            if d_rank is not None:
                rrf_score += 1.0 / (rrf_k + d_rank)
                
            base_info = chunk_map[cid]
            fusion_results.append({
                'chunk_id': cid,
                'document_id': base_info['document_id'],
                'text': base_info['text'],
                'allowed_roles': base_info['allowed_roles'],
                'citation': base_info['citation'],
                'bm25_rank': b_rank if b_rank is not None else '-',
                'dense_rank': d_rank if d_rank is not None else '-',
                'rrf_score': rrf_score
            })
            
        fusion_results.sort(key=lambda x: x['rrf_score'], reverse=True)
        
        final_results = []
        for rank_idx, item in enumerate(fusion_results[:top_k], start=1):
            item_copy = item.copy()
            item_copy['rank'] = rank_idx
            item_copy['final_rank'] = rank_idx
            item_copy['score'] = round(item_copy['rrf_score'], 5)
            item_copy['retrieval_method'] = 'hybrid'
            final_results.append(item_copy)
            
        return final_results

    def search_hybrid_rerank(self, query: str, user_roles: List[str], candidate_k: int = 20, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid Rerank: Cross-Encoder chỉ tái xếp hạng các ứng viên đã được lọc quyền.
        """
        candidates = self.search_hybrid(query, user_roles=user_roles, candidate_k=candidate_k, top_k=candidate_k)
        if not candidates:
            return []
            
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        for r in reranked:
            r['score'] = r['rerank_score']
            r['retrieval_method'] = 'hybrid_rerank'
            # Đảm bảo allowed_roles được giữ nguyên
            if 'allowed_roles' not in r and 'allowed_roles_list' in r:
                r['allowed_roles'] = r['allowed_roles_list']
        return reranked

    def retrieve(self, query: str, user_roles: List[str], method: str = "hybrid_rerank", top_k: int = 5, candidate_k: int = 20) -> List[Dict[str, Any]]:
        """
        Hàm retrieval thống nhất nhận hai tham số bắt buộc `query` và `user_roles`.
        """
        if not user_roles:
            raise ValueError("Tham số `user_roles` là bắt buộc và không được để trống!")
            
        method = method.lower().strip()
        if method == "bm25":
            return self.search_bm25(query, user_roles=user_roles, top_k=top_k)
        elif method == "dense":
            return self.search_dense(query, user_roles=user_roles, top_k=top_k)
        elif method == "hybrid":
            return self.search_hybrid(query, user_roles=user_roles, candidate_k=candidate_k, top_k=top_k)
        elif method == "hybrid_rerank":
            return self.search_hybrid_rerank(query, user_roles=user_roles, candidate_k=candidate_k, top_k=top_k)
        elif method == "graph_neo4j":
            return self.retrieve_graph(query, user_roles=user_roles, top_k=top_k)
        else:
            raise ValueError(f"Phương pháp retrieval không hợp lệ: {method}")

    def retrieve_graph(self, query: str, user_roles: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Graph Retrieval an toàn từ Neo4j với điều kiện Cypher lọc quyền truy cập:
        WHERE any(role IN d.allowed_roles WHERE role IN $user_roles)
        """
        from neo4j import GraphDatabase
        
        uri = self.neo4j_config['uri']
        user = self.neo4j_config['user']
        password = self.neo4j_config['password']
        database = self.neo4j_config['database']
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        keywords = [k for k in tokenize_vietnamese_text(query) if len(k) > 2]
        
        cypher_query = """
        MATCH (v:VanBan)-[:CONTAINS]->(d:DieuKhoan)
        WHERE any(role IN d.allowed_roles WHERE role IN $user_roles)
          AND ANY(kw IN $keywords WHERE toLower(d.text) CONTAINS kw OR toLower(v.title) CONTAINS kw)
        RETURN d.id AS chunk_id, d.document_id AS document_id, d.text AS text,
               d.allowed_roles AS allowed_roles, v.title AS title, v.so_ky_hieu AS so_ky_hieu, d.article AS article
        LIMIT $top_k
        """
        
        results = []
        with driver.session(database=database) as session:
            records = session.run(cypher_query, {
                'user_roles': user_roles,
                'keywords': keywords,
                'top_k': top_k
            }).data()
            
            for idx, r in enumerate(records, start=1):
                doc_ref = r.get('so_ky_hieu') if r.get('so_ky_hieu') else r.get('title')
                article = r.get('article', '')
                citation = f"[{doc_ref} | {article} | {r['chunk_id']}]" if article else f"[{doc_ref} | {r['chunk_id']}]"
                
                results.append({
                    'rank': idx,
                    'final_rank': idx,
                    'chunk_id': r['chunk_id'],
                    'document_id': r['document_id'],
                    'text': r['text'],
                    'allowed_roles': r['allowed_roles'],
                    'score': 1.0,
                    'retrieval_method': 'graph_neo4j',
                    'citation': citation
                })
                
        driver.close()
        return results

    def get_graph_hints(self, results: List[Dict[str, Any]], user_roles: List[str]) -> Dict[str, Any]:
        """
        Lấy Graph hints từ Neo4j cho danh sách kết quả, lọc tuyệt đối theo user_roles.
        Trả về dữ liệu nguyên thủy (primitive string/dict) tương thích 100% với PyArrow/Streamlit.
        """
        if not results:
            return {
                'retrieved_document_ids': [],
                'retrieved_chunk_ids': [],
                'neo4j_status': 'NO_RESULTS',
                'direct_relations': [],
                'records_count': 0
            }
            
        retrieved_chunk_ids = [r['chunk_id'] for r in results]
        retrieved_doc_ids = sorted(list(set(r['document_id'] for r in results)))
        
        from neo4j import GraphDatabase
        
        uri = self.neo4j_config['uri']
        user = self.neo4j_config['user']
        password = self.neo4j_config['password']
        database = self.neo4j_config['database']
        
        relations_hint = []
        neo4j_available = False
        
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            neo4j_available = True
            
            cypher = """
            MATCH (v1:VanBan)-[r]->(v2:VanBan)
            WHERE (v1.id IN $doc_ids OR v2.id IN $doc_ids)
              AND any(role IN v1.allowed_roles WHERE role IN $user_roles)
              AND any(role IN v2.allowed_roles WHERE role IN $user_roles)
            RETURN v1.id AS source_doc, v1.title AS source_title,
                   type(r) AS rel_type, r.relationship_desc AS desc,
                   v2.id AS target_doc, v2.title AS target_title,
                   v1.allowed_roles AS v1_roles
            """
            
            with driver.session(database=database) as session:
                records = session.run(cypher, {'doc_ids': retrieved_doc_ids, 'user_roles': user_roles}).data()
                for rec in records:
                    relations_hint.append({
                        'Source Doc': str(rec.get('source_doc', '')),
                        'Source Title': str(rec.get('source_title', ''))[:40] + '...',
                        'Relation': str(rec.get('rel_type', '')),
                        'Description': str(rec.get('desc', '')) if rec.get('desc') else '-',
                        'Target Doc': str(rec.get('target_doc', '')),
                        'Target Title': str(rec.get('target_title', ''))[:40] + '...',
                        'Allowed Roles': str(rec.get('v1_roles', []))
                    })
            driver.close()
        except Exception:
            neo4j_available = False
            
        return {
            'retrieved_document_ids': retrieved_doc_ids,
            'retrieved_chunk_ids': retrieved_chunk_ids,
            'neo4j_status': 'CONNECTED' if neo4j_available else 'OFFLINE/NO_HINTS',
            'direct_relations': relations_hint,
            'records_count': len(relations_hint)
        }

if __name__ == "__main__":
    sr = SecureRetriever()
    print("\n--- TEST SEARCH DEMO ---")
    
    q_hr = "Quy định về kỷ luật lao động và bí mật kho tiền"
    print(f"\nQuery: '{q_hr}'")
    
    print("\n[Role: Guest]")
    res_guest = sr.retrieve(q_hr, user_roles=["Guest"], method="hybrid_rerank", top_k=3)
    for r in res_guest:
        print(f" - [{r['rank']}] {r['chunk_id']} | Roles: {r['allowed_roles']} | Score: {r['score']}")
        
    print("\n[Role: HR_Manager]")
    res_hr = sr.retrieve(q_hr, user_roles=["HR_Manager"], method="hybrid_rerank", top_k=3)
    for r in res_hr:
        print(f" - [{r['rank']}] {r['chunk_id']} | Roles: {r['allowed_roles']} | Score: {r['score']}")
