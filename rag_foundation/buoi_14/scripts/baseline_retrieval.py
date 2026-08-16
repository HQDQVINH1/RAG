#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: baseline_retrieval.py
Mục đích: Chạy thử nghiệm 2 baseline retrieval độc lập: BM25-only và Dense-only.
Cách dùng:
    python scripts/baseline_retrieval.py --query "phê duyệt khoản vay" --top-k 5
"""

import os
import sys
import argparse
import pandas as pd

# Thêm thư mục gốc buoi_14 vào sys.path để import module src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever


def print_results(header: str, results: list):
    """
    In kết quả tìm kiếm theo định dạng chuẩn hóa.
    """
    print("\n" + "=" * 60)
    print(header)
    print("=" * 60)
    
    if not results:
        print("Không tìm thấy kết quả phù hợp.")
        return
        
    for res in results:
        print(f"Rank {res['rank']} | Score: {res['retrieval_score']:.4f} | Chunk ID: {res['chunk_id']} (Doc ID: {res['document_id']})")
        print(f"  Citation : {res['citation']}")
        snippet = res['text'].replace('\n', ' ')
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        print(f"  Snippet  : {snippet}")
        print("-" * 60)


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    parser = argparse.ArgumentParser(description="Baseline Retrieval (BM25 vs Dense)")
    parser.add_argument("--query", type=str, required=True, help="Câu hỏi/truy vấn tìm kiếm")
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả trả về (mặc định: 5)")
    args = parser.parse_args()
    
    corpus_csv = os.path.join(project_root, 'data', 'processed', 'chunks_normalized.csv')
    if not os.path.exists(corpus_csv):
        print(f"Lỗi: Không tìm thấy file corpus tại {corpus_csv}. Vui lòng chạy scripts/prepare_corpus.py trước.")
        sys.exit(1)
        
    print(f"Đang đọc corpus từ: {corpus_csv}")
    corpus_df = pd.read_csv(corpus_csv, encoding='utf-8')
    
    # 1. Khởi tạo & tìm kiếm BM25
    print("\n[BM25] Đang khởi tạo chỉ mục lexical BM25...")
    bm25_retriever = BM25Retriever(corpus_df)
    bm25_results = bm25_retriever.search(args.query, top_k=args.top_k)
    
    # 2. Khởi tạo & tìm kiếm Dense
    cache_dir = os.path.join(project_root, 'cache')
    dense_retriever = DenseRetriever(
        corpus_df,
        model_name="bkai-foundation-models/vietnamese-bi-encoder",
        cache_dir=cache_dir
    )
    dense_results = dense_retriever.search(args.query, top_k=args.top_k)
    
    # 3. In kết quả theo đúng yêu cầu format
    print(f"\nTRUY VẤN: \"{args.query}\" (Top-{args.top_k})")
    print_results("BM25 RESULTS", bm25_results)
    print_results("DENSE RESULTS", dense_results)


if __name__ == '__main__':
    main()
