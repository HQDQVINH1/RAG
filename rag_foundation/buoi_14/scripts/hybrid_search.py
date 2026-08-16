#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: hybrid_search.py
Mục đích: Chạy thử nghiệm Hybrid Search (BM25 + Dense kết hợp bằng Reciprocal Rank Fusion RRF).
Cách dùng:
    python scripts/hybrid_search.py --query "..." --candidate-k 20 --top-k 5
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


def print_hybrid_table(results: list):
    """
    In bảng kết quả Hybrid Search theo chuẩn định dạng yêu cầu:
    Rank | Chunk | BM25 rank | Dense rank | RRF | Citation
    """
    print("\n============================================================")
    print("HYBRID RESULTS")
    print("============================================================")
    print(f"{'Rank':<5} | {'Chunk':<12} | {'BM25 rank':<10} | {'Dense rank':<10} | {'RRF':<8} | {'Citation'}")
    print("-" * 80)
    
    for r in results:
        bm25_str = str(r['bm25_rank'])
        dense_str = str(r['dense_rank'])
        print(f"{r['final_rank']:<5} | {r['chunk_id']:<12} | {bm25_str:<10} | {dense_str:<10} | {r['rrf_score']:<8.5f} | {r['citation']}")
    print("-" * 80 + "\n")


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description="Hybrid Search (BM25 + Dense RRF Fusion)")
    parser.add_argument("--query", type=str, required=True, help="Câu hỏi/truy vấn tìm kiếm")
    parser.add_argument("--candidate-k", type=int, default=20, help="Số ứng viên lấy từ từng retriever độc lập (mặc định: 20)")
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả trả về cuối cùng (mặc định: 5)")
    args = parser.parse_args()
    
    corpus_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    if not os.path.exists(corpus_csv):
        print(f"Lỗi: Không tìm thấy file corpus tại {corpus_csv}. Vui lòng chạy scripts/prepare_corpus.py trước.")
        sys.exit(1)
        
    corpus_df = pd.read_csv(corpus_csv, encoding='utf-8')
    
    print("[1/3] Khởi tạo BM25 Retriever...")
    bm25 = BM25Retriever(corpus_df)
    
    print("[2/3] Khởi tạo Dense Retriever (sử dụng cache local)...")
    cache_dir = os.path.join(project_root, 'cache')
    dense = DenseRetriever(corpus_df, model_name="bkai-foundation-models/vietnamese-bi-encoder", cache_dir=cache_dir)
    
    print("[3/3] Kết hợp Hybrid Search bằng RRF...")
    hybrid = HybridRetriever(bm25, dense)
    results = hybrid.search(args.query, candidate_k=args.candidate_k, top_k=args.top_k)
    
    print(f"\nTRUY VẤN: \"{args.query}\" (Candidate-K={args.candidate_k}, Top-K={args.top_k})")
    print_hybrid_table(results)


if __name__ == '__main__':
    main()
