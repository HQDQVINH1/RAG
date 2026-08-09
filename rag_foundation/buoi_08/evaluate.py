"""
Module Evaluate RAG (Buổi 08) — Đánh Giá Chất Lượng Retrieval Metrics.

Tính toán các chỉ số:
1. Recall@K
2. MRR@K (Mean Reciprocal Rank@K)
3. nDCG@K (Normalized Discounted Cumulative Gain@K với Binary Relevance)
4. Latency Mean & P50 (Median)

Quy tắc:
- Không gọi LLM generation trong quá trình đánh giá.
- Nếu tập câu hỏi còn nhãn needs_human_review=true, báo warning và không tuyên bố winner.
- Xuất báo cáo JSON ra thư mục reports/eval_results.json kèm timestamp & metadata.
"""

import sys
import os
import math
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import rag
import advanced_rag


def compute_recall_at_k(retrieved_ids: List[str], gold_ids: List[str], k: int) -> float:
    """Tính chỉ số Recall@K (0.0 đến 1.0)."""
    if not gold_ids:
        return 1.0 if not retrieved_ids[:k] else 0.0
    top_k_ids = set(retrieved_ids[:k])
    hits = top_k_ids.intersection(set(gold_ids))
    return len(hits) / len(gold_ids)


def compute_mrr_at_k(retrieved_ids: List[str], gold_ids: List[str], k: int) -> float:
    """Tính chỉ số MRR@K (Reciprocal Rank của nhãn đúng đầu tiên trong Top-K)."""
    if not gold_ids:
        return 0.0
    gold_set = set(gold_ids)
    for rank, cid in enumerate(retrieved_ids[:k], start=1):
        if cid in gold_set:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_ids: List[str], gold_ids: List[str], k: int) -> float:
    """Tính chỉ số nDCG@K với Binary Relevance (0.0 đến 1.0)."""
    if not gold_ids:
        return 0.0
    top_k_ids = retrieved_ids[:k]
    gold_set = set(gold_ids)

    # DCG@K
    dcg = 0.0
    for rank, cid in enumerate(top_k_ids, start=1):
        rel = 1.0 if cid in gold_set else 0.0
        dcg += rel / math.log2(rank + 1)

    # IDCG@K
    ideal_hits = min(len(gold_ids), k)
    idcg = 0.0
    for rank in range(1, ideal_hits + 1):
        idcg += 1.0 / math.log2(rank + 1)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def compute_p50(values: List[float]) -> float:
    """Tính trung vị (P50)."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    else:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def load_eval_questions(eval_file: Path) -> List[Dict[str, Any]]:
    """Đọc bộ câu hỏi đánh giá từ eval/questions.json."""
    if not eval_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file câu hỏi đánh giá: {eval_file}")
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("File questions.json phải chứa một JSON array.")
    return data


def run_evaluation(
    eval_file: Optional[Path] = None,
    strategy: str = "hierarchical",
    top_k: int = 5,
    modes: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    storage_dir: Optional[Path] = None,
    genai_client: Optional[Any] = None,
    input_dir: Optional[Path] = None,
    reranker_fn: Optional[Callable[..., List[float]]] = None
) -> Dict[str, Any]:
    """
    Quy trình đánh giá chất lượng RAG Metrics tự động (Contract Bước 10).
    TUYỆT ĐỐI KHÔNG GỌI LLM GENERATION.
    """
    if config is None:
        config = advanced_rag.load_advanced_config()

    if eval_file is None:
        eval_file = BASE_DIR / "eval" / "questions.json"

    if input_dir is None:
        input_dir = rag.DEFAULT_INPUT_DIR

    if modes is None:
        modes = ["bm25", "semantic", "hybrid", "hybrid_rerank"]

    questions = load_eval_questions(eval_file)

    has_unreviewed = any(q.get("needs_human_review", False) for q in questions)
    warnings = []

    if has_unreviewed:
        warnings.append("CẢNH BÁO: Bộ câu hỏi còn câu chứa 'needs_human_review: true'. Kết quả không dùng để tuyên bố chiến thắng chính thức.")

    # Chuẩn bị dữ liệu lưu trữ kết quả từng mode
    mode_metrics: Dict[str, Dict[str, Any]] = {}
    per_query_details: List[Dict[str, Any]] = []

    for m in modes:
        mode_metrics[m] = {
            "recalls": [],
            "mrrs": [],
            "ndcgs": [],
            "latencies": [],
            "errors": 0
        }

    # Đọc chunks cho BM25 & Hybrid
    chunks, _ = rag.load_chunks(Path(input_dir), strategy)

    for q_item in questions:
        qid = q_item.get("query_id", "Q_UNK")
        q_text = q_item.get("question", "")
        gold_ids = q_item.get("relevant_chunk_ids", [])

        query_record = {
            "query_id": qid,
            "question": q_text,
            "gold_relevant_chunk_ids": gold_ids,
            "scope": q_item.get("scope", "in_scope"),
            "needs_human_review": q_item.get("needs_human_review", False),
            "results_by_mode": {}
        }

        for m in modes:
            t0 = time.perf_counter()
            retrieved_ids = []
            error_msg = None

            try:
                if m == "bm25":
                    res = advanced_rag.search_bm25(q_text, chunks, candidate_k=top_k)
                    retrieved_ids = [r["chunk_id"] for r in res]
                elif m == "semantic":
                    res = advanced_rag.search_semantic(q_text, strategy=strategy, candidate_k=top_k, config=config, storage_dir=storage_dir, genai_client=genai_client)
                    retrieved_ids = [r["chunk_id"] for r in res]
                elif m == "hybrid":
                    h_res = advanced_rag.search_hybrid(q_text, strategy=strategy, candidate_k=top_k, config=config, storage_dir=storage_dir, genai_client=genai_client, input_dir=input_dir)
                    retrieved_ids = [r["chunk_id"] for r in h_res["fused_candidates"]]
                elif m == "hybrid_rerank":
                    hr_res = advanced_rag.search_hybrid_rerank(q_text, strategy=strategy, candidate_k=config["RERANK_CANDIDATES"], config=config, storage_dir=storage_dir, genai_client=genai_client, input_dir=input_dir, reranker_fn=reranker_fn)
                    retrieved_ids = [r["chunk_id"] for r in hr_res["reranked_candidates"][:top_k]]
            except Exception as ex:
                error_msg = str(ex)
                mode_metrics[m]["errors"] += 1

            t1 = time.perf_counter()
            latency_ms = round((t1 - t0) * 1000, 2)

            rec = compute_recall_at_k(retrieved_ids, gold_ids, top_k)
            mrr = compute_mrr_at_k(retrieved_ids, gold_ids, top_k)
            ndcg = compute_ndcg_at_k(retrieved_ids, gold_ids, top_k)

            mode_metrics[m]["recalls"].append(rec)
            mode_metrics[m]["mrrs"].append(mrr)
            mode_metrics[m]["ndcgs"].append(ndcg)
            mode_metrics[m]["latencies"].append(latency_ms)

            query_record["results_by_mode"][m] = {
                "retrieved_chunk_ids": retrieved_ids,
                "recall_at_k": round(rec, 4),
                "mrr_at_k": round(mrr, 4),
                "ndcg_at_k": round(ndcg, 4),
                "latency_ms": latency_ms,
                "error": error_msg
            }

        per_query_details.append(query_record)

    # Tính tổng hợp chỉ số trung bình & p50 cho từng mode
    summary: Dict[str, Dict[str, Any]] = {}
    for m in modes:
        m_recalls = mode_metrics[m]["recalls"]
        m_mrrs = mode_metrics[m]["mrrs"]
        m_ndcgs = mode_metrics[m]["ndcgs"]
        m_lats = mode_metrics[m]["latencies"]

        summary[m] = {
            f"Recall@{top_k}": round(sum(m_recalls) / len(m_recalls), 4) if m_recalls else 0.0,
            f"MRR@{top_k}": round(sum(m_mrrs) / len(m_mrrs), 4) if m_mrrs else 0.0,
            f"nDCG@{top_k}": round(sum(m_ndcgs) / len(m_ndcgs), 4) if m_ndcgs else 0.0,
            "Latency_Mean_ms": round(sum(m_lats) / len(m_lats), 2) if m_lats else 0.0,
            "Latency_P50_ms": round(compute_p50(m_lats), 2) if m_lats else 0.0,
            "Error_Count": mode_metrics[m]["errors"]
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "strategy": strategy,
        "eval_k": top_k,
        "total_questions": len(questions),
        "has_unreviewed_questions": has_unreviewed,
        "warnings": warnings,
        "model_identity": {
            "embedding_model": config["GEMINI_EMBEDDING_MODEL"],
            "reranker_model": config["RERANKER_MODEL"],
            "device": config["RERANK_DEVICE"]
        },
        "metrics_summary": summary,
        "per_query_details": per_query_details
    }

    # Xuất file báo cáo JSON
    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_file = reports_dir / "eval_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    report["report_path"] = str(out_file)
    return report


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Advanced RAG Evaluator CLI (Buổi 08)")
    parser.add_argument(
        "--strategy",
        type=str,
        default="hierarchical",
        choices=list(rag.VALID_STRATEGIES),
        help="Chiến lược chunking cần đánh giá"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Top-K ứng viên đánh giá"
    )
    parser.add_argument(
        "--eval-file",
        type=str,
        default=str(BASE_DIR / "eval" / "questions.json"),
        help="Đường dẫn file câu hỏi eval"
    )

    args = parser.parse_args()

    print("==================================================")
    print("BẮT ĐẦU ĐÁNH GIÁ CHẤT LƯỢNG RAG METRICS")
    print("==================================================")
    print(f"File câu hỏi : {args.eval_file}")
    print(f"Chiến lược   : {args.strategy}")
    print(f"Top-K        : {args.k}")
    print("--------------------------------------------------")

    try:
        report = run_evaluation(
            eval_file=Path(args.eval_file),
            strategy=args.strategy,
            top_k=args.k
        )
        print("KẾT QUẢ ĐÁNH GIÁ TỔNG HỢP:")
        print(json.dumps(report["metrics_summary"], ensure_ascii=False, indent=2))
        print("--------------------------------------------------")
        print(f"✅ Đã xuất file báo cáo tại: {report['report_path']}")
        if report["has_unreviewed_questions"]:
            print("⚠️ CẢNH BÁO: Bộ câu hỏi chứa nhãn 'needs_human_review: true'. Không tuyên bố winner chính thức.")
        print("==================================================")
    except Exception as e:
        print(f"❌ LỖI ĐÁNH GIÁ EVALUATION: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
