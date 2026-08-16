#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: query_demo.py
Mục đích: CLI Demo tích hợp thống nhất toàn bộ pipeline RAG Buổi 14 và trích xuất GRAPH HINTS.
Cách dùng:
    python scripts/query_demo.py --query "..." --method hybrid_rerank --top-k 5
"""

import os
import sys
import argparse

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.unified_retriever import UnifiedRetriever


def print_terminal_demo(query: str, method: str, results: list, graph_hints: dict):
    """
    In kết quả demo terminal trực quan, định dạng sinh động cho học viên.
    """
    print("\n" + "=" * 75)
    print(f"RAG PIPELINE DEMO — METHOD: [{method.upper()}]")
    print("=" * 75)
    print(f"CÂU HỎI: \"{query}\"\n")
    
    print(f"{'RANK':<5} | {'CHUNK ID':<12} | {'SCORE':<10} | {'CITATION'}")
    print("-" * 75)
    
    for r in results:
        rank = r.get('final_rank', r.get('rank'))
        score = r.get('score', 0.0)
        cid = r['chunk_id']
        citation = r['citation']
        
        print(f"{rank:<5} | {cid:<12} | {score:<10.4f} | {citation}")
        
        # Nếu là hybrid_rerank -> in thêm chi tiết điểm hybrid và rerank
        if method == "hybrid_rerank" and 'hybrid_score' in r:
            h_rank = r.get('hybrid_rank', '-')
            h_score = r.get('hybrid_score', 0.0)
            print(f"      └─ [Hybrid Rank: {h_rank} | RRF Score: {h_score:.5f} | Rerank Score: {score:.4f}]")
            
        snippet = r['text'].replace('\n', ' ').strip()
        if len(snippet) > 160:
            snippet = snippet[:160] + "..."
        print(f"      └─ Snippet: {snippet}\n")
        
    print("=" * 75)
    print("GRAPH HINTS (Đường dẫn tích hợp Graph RAG cho bài sau)")
    print("=" * 75)
    print(f"• Document IDs Retrieved : {graph_hints['retrieved_document_ids']}")
    print(f"• Chunk IDs Retrieved    : {graph_hints['retrieved_chunk_ids']}")
    print(f"• Trạng thái Neo4j      : {graph_hints['neo4j_status']}")
    print(f"• Direct Relations ({len(graph_hints['direct_relations'])} quan hệ 1-hop liên quan):")
    
    if graph_hints['direct_relations']:
        for rel in graph_hints['direct_relations']:
            desc_str = f" ({rel['description']})" if rel['description'] else ""
            print(f"   └─ Doc `{rel['source']}` -[:{rel['relation']}]-> Doc `{rel['target']}`{desc_str}")
    else:
        print("   └─ Không có quan hệ trực tiếp 1-hop nào giữa các văn bản này.")
    print("=" * 75 + "\n")


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description="Unified RAG Pipeline Demo & Graph Hints")
    parser.add_argument("--query", type=str, required=True, help="Câu hỏi tìm kiếm")
    parser.add_argument("--method", type=str, default="hybrid_rerank", choices=["bm25", "dense", "hybrid", "hybrid_rerank"], help="Phương pháp retrieval")
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả trả về cuối cùng")
    parser.add_argument("--candidate-k", type=int, default=20, help="Số ứng viên rút trích trước fusion/rerank")
    args = parser.parse_args()
    
    corpus_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    cache_dir = os.path.join(project_root, 'cache')
    
    if not os.path.exists(corpus_csv):
        print(f"Lỗi: Không tìm thấy corpus tại {corpus_csv}. Vui lòng chạy scripts/prepare_corpus.py trước.")
        sys.exit(1)
        
    retriever = UnifiedRetriever(corpus_csv, cache_dir)
    results = retriever.retrieve(args.query, method=args.method, top_k=args.top_k, candidate_k=args.candidate_k)
    graph_hints = retriever.get_graph_hints(results)
    
    print_terminal_demo(args.query, args.method, results, graph_hints)


if __name__ == '__main__':
    main()
