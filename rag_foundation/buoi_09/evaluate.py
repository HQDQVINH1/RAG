"""
Module Đánh Giá Hiệu Năng RAG Buổi 09 — Multi-Query & Parent-Child Hierarchical RAG Evaluator.

So sánh 4 Modes Retrieval-Only:
1. single_flat
2. multi_flat
3. single_parent
4. multi_parent

Tính toán các chỉ số:
- Child Recall@K
- Parent Recall@K
- MRR@K
- nDCG@K (Binary Relevance)
- Latency (mean, p50)
- Context Chars & Expansion Factor
- Generation Calls Count & Embedding Calls Count
"""

import sys
import os
import json
import math
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag
import advanced_rag


def calculate_mrr(retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
    """Tính chỉ số MRR@K (Mean Reciprocal Rank)."""
    if not ground_truth_ids or not retrieved_ids:
        return 0.0
    gt_set = set(ground_truth_ids)
    for idx, item_id in enumerate(retrieved_ids, start=1):
        if item_id in gt_set:
            return 1.0 / idx
    return 0.0


def calculate_ndcg(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
    """Tính chỉ số nDCG@K với binary relevance (0 hoặc 1)."""
    if not ground_truth_ids or not retrieved_ids:
        return 0.0
    gt_set = set(ground_truth_ids)
    retrieved_k = retrieved_ids[:k]
    
    dcg = 0.0
    for idx, item_id in enumerate(retrieved_k, start=1):
        if item_id in gt_set:
            dcg += 1.0 / math.log2(idx + 1)

    ideal_hits = min(len(gt_set), k)
    idcg = sum(1.0 / math.log2(idx + 1) for idx in range(1, ideal_hits + 1))
    
    return dcg / idcg if idcg > 0 else 0.0


def calculate_recall(retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
    """Tính chỉ số Recall@K."""
    if not ground_truth_ids:
        return 1.0  # Cho câu hỏi out_of_scope
    if not retrieved_ids:
        return 0.0
    gt_set = set(ground_truth_ids)
    hits = sum(1 for item_id in retrieved_ids if item_id in gt_set)
    return hits / len(gt_set)


def run_evaluation(
    dataset_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
    store_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Thực thi đánh giá benchmark toàn bộ câu hỏi trong dataset trên 4 modes.
    """
    if config is None:
        config = hierarchical_rag.load_buoi09_config()
    if dataset_path is None:
        dataset_path = BASE_DIR / "eval" / "questions.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dataset tại {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    # Validate Parent & Child IDs với Hierarchy Store hiện tại
    h_status = hierarchical_rag.get_hierarchy_status(store_dir=store_dir)
    if not h_status["hierarchy_store_exists"]:
        raise RuntimeError("hierarchy_not_ready: Registry Hierarchy Store chưa khởi tạo.")

    store_dir_path = store_dir or (BASE_DIR / "storage" / "hierarchy")
    with open(store_dir_path / "children.json", "r", encoding="utf-8") as f:
        children_data = json.load(f)
    with open(store_dir_path / "parents.json", "r", encoding="utf-8") as f:
        parents_data = json.load(f)

    valid_child_ids = {c["child_id"] for c in children_data}
    valid_parent_ids = {p["parent_id"] for p in parents_data}

    for item in questions_data:
        for cid in item.get("relevant_child_ids", []):
            if cid not in valid_child_ids:
                raise ValueError(f"Stale Child ID '{cid}' trong dataset không tồn tại trong Hierarchy Store!")
        for pid in item.get("relevant_parent_ids", []):
            if pid not in valid_parent_ids:
                raise ValueError(f"Stale Parent ID '{pid}' trong dataset không tồn tại trong Hierarchy Store!")

    modes = ["single_flat", "multi_flat", "single_parent", "multi_parent"]
    mode_eval_results = {m: [] for m in modes}
    has_human_review_warning = any(item.get("needs_human_review", False) for item in questions_data)

    print("=" * 60)
    print("STARTING BENCHMARK EVALUATION ACROSS 4 MODES")
    print(f"Total Questions: {len(questions_data)} | Modes: {modes}")
    print("=" * 60)

    for q_item in questions_data:
        q_id = q_item["question_id"]
        q_text = q_item["question"]
        gt_children = q_item.get("relevant_child_ids", [])
        gt_parents = q_item.get("relevant_parent_ids", [])

        print(f"Evaluating Question [{q_id}]: {q_text[:50]}...")

        for m in modes:
            res = hierarchical_rag.execute_query_pipeline(
                question=q_text,
                mode=m,
                config=config,
                store_dir=store_dir,
                compare_only=True,
                **kwargs
            )

            # Thu thập retrieved child & parent IDs
            ret_children = [c.get("child_id", c.get("chunk_id")) for c in res.get("child_hits", [])]
            ret_parents = [p["parent_id"] for p in res.get("parent_candidates", [])]

            if "flat" in m:
                # Flat mode: map retrieved child hits sang parent IDs để so sánh công bằng
                ret_parents_from_child = []
                for c in res.get("child_hits", []):
                    pid = c.get("parent_id")
                    if pid and pid not in ret_parents_from_child:
                        ret_parents_from_child.append(pid)
                ret_parents = ret_parents_from_child

            child_recall = calculate_recall(ret_children, gt_children)
            parent_recall = calculate_recall(ret_parents, gt_parents)
            parent_mrr = calculate_mrr(ret_parents, gt_parents)
            parent_ndcg = calculate_ndcg(ret_parents, gt_parents, k=config["FINAL_PARENT_TOP_K"])

            accepted = res.get("accepted_evidence", [])
            total_chars = sum(len(ev.get("text", "")) for ev in accepted)
            child_chars = sum(len(c.get("text", "")) for c in res.get("child_hits", []))
            exp_factor = round(total_chars / max(child_chars, 1), 2) if child_chars > 0 else 1.0

            q_res = {
                "question_id": q_id,
                "question_type": q_item.get("question_type"),
                "status": res.get("status"),
                "child_recall": child_recall,
                "parent_recall": parent_recall,
                "parent_mrr": parent_mrr,
                "parent_ndcg": parent_ndcg,
                "retrieved_child_count": len(ret_children),
                "retrieved_parent_count": len(ret_parents),
                "context_chars": total_chars,
                "expansion_factor": exp_factor,
                "latency_ms": res.get("total_latency_ms", 0.0),
                "generation_calls": res.get("api_call_counts", {}).get("generation_calls", 0),
                "embedding_calls": res.get("api_call_counts", {}).get("embedding_calls", 0)
            }

            mode_eval_results[m].append(q_res)

    # Tính toán chỉ số tổng hợp (Aggregated Metrics per Mode)
    aggregate_summary = {}
    for m in modes:
        items = mode_eval_results[m]
        latencies = [it["latency_ms"] for it in items]
        
        aggregate_summary[m] = {
            "mean_child_recall": round(float(np.mean([it["child_recall"] for it in items])), 4),
            "mean_parent_recall": round(float(np.mean([it["parent_recall"] for it in items])), 4),
            "mean_parent_mrr": round(float(np.mean([it["parent_mrr"] for it in items])), 4),
            "mean_parent_ndcg": round(float(np.mean([it["parent_ndcg"] for it in items])), 4),
            "mean_context_chars": round(float(np.mean([it["context_chars"] for it in items])), 1),
            "mean_expansion_factor": round(float(np.mean([it["expansion_factor"] for it in items])), 2),
            "mean_latency_ms": round(float(np.mean(latencies)), 2),
            "p50_latency_ms": round(float(np.percentile(latencies, 50)), 2),
            "total_generation_calls": sum(it["generation_calls"] for it in items),
            "total_embedding_calls": sum(it["embedding_calls"] for it in items)
        }

    timestamp_str = datetime.now(timezone.utc).isoformat()
    report_dict = {
        "timestamp": timestamp_str,
        "identities": {
            "strategy": "hierarchical",
            "generation_model": config["GEMINI_GENERATION_MODEL"],
            "embedding_model": config["GEMINI_EMBEDDING_MODEL"],
            "reranker_model": config.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
            "corpus": "Văn bản quy phạm pháp luật Ngân hàng Nhà nước"
        },
        "total_questions": len(questions_data),
        "needs_human_review": has_human_review_warning,
        "aggregate_summary_per_mode": aggregate_summary,
        "per_question_results": mode_eval_results,
        "warnings": [
            "Tập dữ liệu Gold Labels chứa nhãn cần duyệt thủ công (needs_human_review = True)."
        ] if has_human_review_warning else []
    }

    # Lưu báo cáo JSON atomically
    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_filename = f"eval_report_{int(time.time())}.json"
    report_file_path = reports_dir / report_filename
    latest_file_path = reports_dir / "latest_report.json"

    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)

    with open(latest_file_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"EVALUATION COMPLETE! Report saved to {report_file_path}")
    print("=" * 60)

    return report_dict


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run_evaluation()
