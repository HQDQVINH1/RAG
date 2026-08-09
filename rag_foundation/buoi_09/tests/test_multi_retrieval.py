"""
Unit tests cho Multi-Query Hybrid Fan-Out Retrieval & Cross-Query RRF Fusion (Buổi 09 — Step 05).

12 Test Cases (100% Offline, Zero Network Calls, Dependency Injection):
1. test_mq_rrf_hand_calculated
2. test_original_and_variant_weights
3. test_deduplicate_union
4. test_missing_query_contribution
5. test_support_query_count_and_ids
6. test_metadata_mismatch_fails
7. test_deterministic_tie_break
8. test_each_query_calls_hybrid_once
9. test_no_reranker_or_generation_called
10. test_q0_failure_and_partial_status
11. test_trace_metrics_schema
12. test_offline_with_fake_retriever_and_generator
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag


class TestMultiQueryRetrieval(unittest.TestCase):

    def setUp(self):
        hierarchical_rag.clear_multi_query_cache()

    def test_mq_rrf_hand_calculated(self):
        """1. Kiểm tra công thức RRF 2 tầng (Cross-Query RRF) bằng ví dụ tính tay."""
        # Q0 (weight=1.5): child_A ở inner rank 1 -> 1.5 / (60 + 1) = 1.5 / 61 = 0.02459016
        # Q1 (weight=1.0): child_A ở inner rank 2 -> 1.0 / (60 + 2) = 1.0 / 62 = 0.01612903
        # Tổng score = 0.02459016 + 0.01612903 = 0.04071919
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            if "Variant" in question:
                return [{"chunk_id": "CHILD_A", "text": "Content A", "source": "A.pdf", "fused_rank": 2}]
            return [{"chunk_id": "CHILD_A", "text": "Content A", "source": "A.pdf", "fused_rank": 1}]

        hits, trace = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        expected_score = (1.5 / (60 + 1)) + (1.0 / (60 + 2))
        self.assertAlmostEqual(hits[0]["multi_query_rrf_score"], expected_score, places=6)

    def test_original_and_variant_weights(self):
        """2. Áp dụng đúng MULTI_QUERY_ORIGINAL_WEIGHT (1.5) cho Q0 và MULTI_QUERY_VARIANT_WEIGHT (1.0) cho Q1..Qn."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        
        # Q0 trả CHILD_0 ở rank 1, Q1 trả CHILD_1 ở rank 1
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            if "Variant" in question:
                return [{"chunk_id": "CHILD_1", "text": "Content 1", "source": "1.pdf", "fused_rank": 1}]
            return [{"chunk_id": "CHILD_0", "text": "Content 0", "source": "0.pdf", "fused_rank": 1}]

        hits, _ = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        score_q0 = 1.5 / (60 + 1)
        score_q1 = 1.0 / (60 + 1)
        
        hit_0 = [h for h in hits if h["child_id"] == "CHILD_0"][0]
        hit_1 = [h for h in hits if h["child_id"] == "CHILD_1"][0]
        
        self.assertAlmostEqual(hit_0["multi_query_rrf_score"], score_q0, places=6)
        self.assertAlmostEqual(hit_1["multi_query_rrf_score"], score_q1, places=6)
        self.assertGreater(hit_0["multi_query_rrf_score"], hit_1["multi_query_rrf_score"])

    def test_deduplicate_union(self):
        """3. Union hợp nhất kết quả giữa các queries mà không làm trùng lặp child record."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        
        # Cả Q0 và Q1 đều tìm thấy CHILD_A
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            return [{"chunk_id": "CHILD_A", "text": "Content A", "source": "A.pdf", "fused_rank": 1}]

        hits, trace = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(hits), 1)
        self.assertEqual(trace["union_child_count"], 1)

    def test_missing_query_contribution(self):
        """4. Child không xuất hiện ở 1 query sẽ đóng góp 0 điểm cho query đó mà không gây lỗi."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            if "Variant" in question:
                return [{"chunk_id": "CHILD_B", "text": "Content B", "source": "B.pdf", "fused_rank": 1}]
            return [{"chunk_id": "CHILD_A", "text": "Content A", "source": "A.pdf", "fused_rank": 1}]

        hits, _ = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        hit_a = [h for h in hits if h["child_id"] == "CHILD_A"][0]
        self.assertIn("Q0", hit_a["per_query_ranks"])
        self.assertNotIn("Q1", hit_a["per_query_ranks"])

    def test_support_query_count_and_ids(self):
        """5. Đếm chính xác support_query_count và danh sách support_query_ids sắp xếp theo thứ tự Q0, Q1, Q2."""
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Variant Q1", "focus": "paraphrase"},
            {"text": "Variant Q2", "focus": "exact_legal_terms"}
        ]
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            if "Q2" in question or "exact" in question:
                return [{"chunk_id": "CHILD_X", "text": "Content X", "source": "X.pdf", "fused_rank": 1}]
            return [{"chunk_id": "CHILD_X", "text": "Content X", "source": "X.pdf", "fused_rank": 1}]

        hits, _ = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        hit_x = hits[0]
        self.assertEqual(hit_x["support_query_count"], 3)
        self.assertEqual(hit_x["support_query_ids"], ["Q0", "Q1", "Q2"])

    def test_metadata_mismatch_fails(self):
        """6. Báo lỗi ValueError nếu cùng 1 child_id nhưng có metadata (text/source) sai lệch giữa các query."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            if "Variant" in question:
                return [{"chunk_id": "CHILD_A", "text": "Content MISMATCH", "source": "A.pdf", "fused_rank": 1}]
            return [{"chunk_id": "CHILD_A", "text": "Content ORIGINAL", "source": "A.pdf", "fused_rank": 1}]

        with self.assertRaises(ValueError):
            hierarchical_rag.search_multi_query_child_hits(
                "Question Q0?",
                query_generator_fn=fake_gen,
                per_query_retriever_fn=fake_retriever
            )

    def test_deterministic_tie_break(self):
        """7. Đảm bảo tie-break ổn định: multi_query_rrf_score (giảm) -> support_count (giảm) -> best_rank (tăng) -> child_id."""
        fake_gen = lambda p, m, t, c, cl: []
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            return [
                {"chunk_id": "CHILD_B", "text": "Content B", "source": "B.pdf", "fused_rank": 1},
                {"chunk_id": "CHILD_A", "text": "Content A", "source": "A.pdf", "fused_rank": 1}
            ]

        hits, _ = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(hits[0]["child_id"], "CHILD_A")
        self.assertEqual(hits[1]["child_id"], "CHILD_B")

    def test_each_query_calls_hybrid_once(self):
        """8. Mỗi query trong tập Multi-Query chỉ gọi hàm hybrid retriever đúng 1 lần."""
        call_count = 0
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Variant Q1", "focus": "paraphrase"},
            {"text": "Variant Q2", "focus": "exact_legal_terms"}
        ]
        
        def fake_retriever(question, strategy, candidate_k, config, chunks, storage_dir, genai_client):
            nonlocal call_count
            call_count += 1
            return [{"chunk_id": f"CHILD_{call_count}", "text": "Content", "source": "S.pdf", "fused_rank": 1}]

        hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(call_count, 3)  # Q0, Q1, Q2

    def test_no_reranker_or_generation_called(self):
        """9. Xác nhận chưa gọi bất kỳ Cross-Encoder Reranker hay LLM Answer Generation nào."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Text", "source": "S.pdf", "fused_rank": 1}]

        hits, trace = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        for h in hits:
            self.assertNotIn("rerank_score", h)
            self.assertNotIn("accepted", h)

    def test_q0_failure_and_partial_status(self):
        """10. Lỗi Q0 làm sập pipeline; Lỗi generated query trả status='multi_query_partial'."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant FAIL", "focus": "paraphrase"}]
        
        def fail_q1_retriever(question, *args, **kwargs):
            if "FAIL" in question:
                raise RuntimeError("Q1 Chroma DB Timeout")
            return [{"chunk_id": "CHILD_0", "text": "Text 0", "source": "0.pdf", "fused_rank": 1}]

        hits, trace = hierarchical_rag.search_multi_query_child_hits(
            "Question Q0?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fail_q1_retriever
        )

        self.assertEqual(trace["status"], "multi_query_partial")
        self.assertIn("Q1", trace["failed_query_ids"])

        # Q0 Lỗi -> Raise RuntimeError
        def fail_q0_retriever(question, *args, **kwargs):
            raise RuntimeError("Q0 Fatal Search Error")

        with self.assertRaises(RuntimeError):
            hierarchical_rag.search_multi_query_child_hits(
                "Fatal Question?",
                query_generator_fn=fake_gen,
                per_query_retriever_fn=fail_q0_retriever
            )

    def test_trace_metrics_schema(self):
        """11. Đảm bảo cấu trúc trace chứa đầy đủ các trường đếm latency, count, overlap_distribution."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant 1", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Text", "source": "S.pdf", "fused_rank": 1}]

        _, trace = hierarchical_rag.search_multi_query_child_hits(
            "Test Question?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertIn("requested_query_count", trace)
        self.assertIn("executed_query_count", trace)
        self.assertIn("successful_query_count", trace)
        self.assertIn("union_child_count", trace)
        self.assertIn("overlap_distribution", trace)
        self.assertIn("fusion_latency_ms", trace)
        self.assertIn("gemini_expansion_call_count", trace)

    def test_offline_with_fake_retriever_and_generator(self):
        """12. Đảm bảo tất cả test cases chạy 100% offline bằng fake generator và fake retriever."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Offline Variant", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_OFFLINE", "text": "Offline Text", "source": "O.pdf", "fused_rank": 1}]

        hits, trace = hierarchical_rag.search_multi_query_child_hits(
            "Offline Question?",
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(trace["status"], "ready")
        self.assertEqual(hits[0]["child_id"], "CHILD_OFFLINE")


if __name__ == "__main__":
    unittest.main()
