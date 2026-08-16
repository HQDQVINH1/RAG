#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: rerank.py
Mục đích: Thực hiện luồng RAG nâng cao: Hybrid Search -> Top-N Candidates -> Cross-Encoder Reranker -> Top-k.
In bảng so sánh thứ tự BEFORE RERANK và AFTER RERANK.
Cách dùng:
    python scripts/rerank.py --query "..." --candidate-k 20 --top-k 5
"""

import os
import sys
import argparse
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker


def print_comparison(before_results: list, after_results: list):
    """
    In danh sách thứ tự ứng viên trước và sau khi Rerank để người học dễ dàng so sánh.
    """
    print("\n" + "=" * 80)
    print("BEFORE RERANK (Hybrid Search Top-K Candidates)")
    print("=" * 80)
    print(f"{'Rank':<5} | {'Chunk ID':<12} | {'Doc ID':<8} | {'RRF Score':<10} | {'Citation'}")
    print("-" * 80)
    for item in before_results:
        print(f"{item['final_rank']:<5} | {item['chunk_id']:<12} | {item['document_id']:<8} | {item['rrf_score']:<10.5f} | {item['citation']}")
        
    print("\n" + "=" * 80)
    print("AFTER RERANK (Cross-Encoder Re-ranked Top-K)")
    print("=" * 80)
    print(f"{'Rank':<5} | {'Chunk ID':<12} | {'Doc ID':<8} | {'H-Rank':<7} | {'Rerank Score':<12} | {'Citation'}")
    print("-" * 80)
    for item in after_results:
        print(f"{item['final_rank']:<5} | {item['chunk_id']:<12} | {item['document_id']:<8} | {item['hybrid_rank']:<7} | {item['rerank_score']:<12.4f} | {item['citation']}")
    print("-" * 80 + "\n")


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description="Hybrid Search + Cross-Encoder Reranking Pipeline")
    parser.add_argument("--query", type=str, required=True, help="Câu hỏi/truy vấn tìm kiếm")
    parser.add_argument("--candidate-k", type=int, default=20, help="Số lượng ứng viên từ Hybrid Search (mặc định: 20)")
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả cuối cùng trả về (mặc định: 5)")
    args = parser.parse_args()
    
    corpus_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    if not os.path.exists(corpus_csv):
        print(f"Lỗi: Không tìm thấy file corpus tại {corpus_csv}. Vui lòng chạy scripts/prepare_corpus.py trước.")
        sys.exit(1)
        
    corpus_df = pd.read_csv(corpus_csv, encoding='utf-8')
    
    print("[1/4] Khởi tạo BM25 Retriever...")
    bm25 = BM25Retriever(corpus_df)
    
    print("[2/4] Khởi tạo Dense Retriever (dùng cache local)...")
    cache_dir = os.path.join(project_root, 'cache')
    dense = DenseRetriever(corpus_df, model_name="bkai-foundation-models/vietnamese-bi-encoder", cache_dir=cache_dir)
    
    print("[3/4] Chạy Hybrid Search (RRF) để rút trích Top-N Candidates...")
    hybrid = HybridRetriever(bm25, dense)
    hybrid_candidates = hybrid.search(args.query, candidate_k=args.candidate_k, top_k=args.candidate_k)
    
    print("[4/4] Khởi tạo và chạy Cross-Encoder Reranker...")
    reranker = Reranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    final_reranked = reranker.rerank(args.query, hybrid_candidates, top_k=args.top_k)
    
    print(f"\nTRUY VẤN: \"{args.query}\" (Candidate-K={args.candidate_k}, Top-K={args.top_k})")
    print_comparison(hybrid_candidates[:args.top_k], final_reranked)


if __name__ == '__main__':
    main()
