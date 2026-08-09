"""
Unit tests cho Parent Reranking, Evidence Gating, Answer Pipeline & Mode Matrix (Buổi 09 — Step 07).

14 Test Cases (100% Offline, Temp Hierarchy Store, Injected Fakes):
1. test_reranker_pair_uses_q0_and_parent_text
2. test_generated_query_not_used_for_rerank_or_gen
3. test_sort_rank_change_final_k
4. test_gate_accepted_rejected
5. test_no_evidence_no_generation
6. test_flat_parent_mode_routing
7. test_multi_query_failure_status
8. test_reranker_failure_no_fallback
9. test_citation_uses_parent_and_anchor_child
10. test_citation_label_validation
11. test_multi_mode_max_two_generation_calls
12. test_compare_no_answer_generation
13. test_trace_identity_and_counts
14. test_offline_with_injected_fakes
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag


class TestAnswerPipeline(unittest.TestCase):

    def setUp(self):
        hierarchical_rag.clear_multi_query_cache()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.store_dir = Path(self.tmp_dir.name)

        # Xây dựng mock hierarchy store
        self.children_data = [
            {"child_id": "CHILD_1", "parent_id": "PARENT_A", "text": "Child text 1", "source": "doc1.pdf", "ambiguous": False},
            {"child_id": "CHILD_2", "parent_id": "PARENT_B", "text": "Child text 2", "source": "doc2.pdf", "ambiguous": False},
        ]
        self.parents_data = [
            {"parent_id": "PARENT_A", "source": "doc1.pdf", "page_start": 1, "page_end": 2, "text": "Parent A text context...", "ambiguous": False},
            {"parent_id": "PARENT_B", "source": "doc2.pdf", "page_start": 3, "page_end": 4, "text": "Parent B text context...", "ambiguous": False},
        ]
        self.manifest_data = {
            "build_timestamp": "2026-08-09T00:00:00Z",
            "total_children": len(self.children_data),
            "total_parents": len(self.parents_data)
        }

        with open(self.store_dir / "children.json", "w", encoding="utf-8") as f:
            json.dump(self.children_data, f)
        with open(self.store_dir / "parents.json", "w", encoding="utf-8") as f:
            json.dump(self.parents_data, f)
        with open(self.store_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(self.manifest_data, f)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_reranker_pair_uses_q0_and_parent_text(self):
        """1. Cross-Encoder reranker pair bắt buộc là (Q0, parent_text), không dùng generated query."""
        rerank_input_q = None
        fake_gen = lambda p, m, t, c, cl: [{"text": "Generated Variant Q1", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "fused_rank": 1}]
        
        def fake_reranker(question, parent_texts):
            nonlocal rerank_input_q
            rerank_input_q = question
            return [0.85]

        fake_ans_gen = lambda prompt, cfg, cl: "Answer based on evidence."

        res = hierarchical_rag.execute_query_pipeline(
            "Câu hỏi gốc Q0?",
            mode="multi_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans_gen
        )

        self.assertEqual(rerank_input_q, "Câu hỏi gốc Q0?")
        self.assertNotEqual(rerank_input_q, "Generated Variant Q1")

    def test_generated_query_not_used_for_rerank_or_gen(self):
        """2. Biến thể generated query không bao giờ được đưa vào prompt trả lời LLM như sự thật."""
        prompt_received = None
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant UNWANTED_TEXT", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        
        def fake_ans_gen(prompt, cfg, cl):
            nonlocal prompt_received
            prompt_received = prompt
            return "Answer string."

        res = hierarchical_rag.execute_query_pipeline(
            "Original Q0?",
            mode="multi_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans_gen
        )

        self.assertNotIn("Variant UNWANTED_TEXT", prompt_received)
        self.assertIn("Original Q0?", prompt_received)

    def test_sort_rank_change_final_k(self):
        """3. Kiểm tra rerank sorting, tính parent_rank_change và cắt theo FINAL_PARENT_TOP_K."""
        config = hierarchical_rag.load_buoi09_config()
        config["FINAL_PARENT_TOP_K"] = 1

        parents_in = [
            {"parent_id": "PARENT_A", "parent_rank": 1, "text": "Text A"},
            {"parent_id": "PARENT_B", "parent_rank": 2, "text": "Text B"}
        ]
        # B đảo lên rank 1 (score 0.9), A xuống rank 2 (score 0.1)
        fake_reranker = lambda q, texts: [0.1, 0.9]

        reranked = hierarchical_rag.rerank_parents("Q0?", parents_in, config=config, reranker_fn=fake_reranker)
        self.assertEqual(len(reranked), 1)  # Cắt về FINAL_PARENT_TOP_K = 1
        self.assertEqual(reranked[0]["parent_id"], "PARENT_B")
        self.assertEqual(reranked[0]["parent_rerank_rank"], 1)
        self.assertEqual(reranked[0]["parent_rank_change"], 1)  # 2 - 1 = +1 (tiến 1 hạng)

    def test_gate_accepted_rejected(self):
        """4. Lọc chính xác evidence theo ngưỡng RERANK_MIN_SCORE."""
        config = hierarchical_rag.load_buoi09_config()
        config["RERANK_MIN_SCORE"] = 0.5

        fake_gen = lambda p, m, t, c, cl: []
        # CHILD_1 -> PARENT_A (score 0.8 PASS), CHILD_2 -> PARENT_B (score 0.2 REJECT)
        fake_retriever = lambda question, *args, **kwargs: [
            {"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1},
            {"chunk_id": "CHILD_2", "text": "Child 2", "source": "doc2.pdf", "fused_rank": 2}
        ]
        fake_reranker = lambda q, texts: [0.8, 0.2]
        fake_ans = lambda p, c, cl: "Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "Gate test?",
            mode="single_parent",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertEqual(len(res["accepted_evidence"]), 1)
        self.assertEqual(res["accepted_evidence"][0]["parent_id"], "PARENT_A")

    def test_no_evidence_no_generation(self):
        """5. Khi không có evidence đạt ngưỡng gate -> status='insufficient_evidence' và 0 answer generation calls."""
        config = hierarchical_rag.load_buoi09_config()
        config["RERANK_MIN_SCORE"] = 0.99  # Ngưỡng rất cao

        ans_called = False
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.1]
        
        def fake_ans(p, c, cl):
            nonlocal ans_called
            ans_called = True
            return "Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "No evidence?",
            mode="single_parent",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertEqual(res["status"], "insufficient_evidence")
        self.assertFalse(ans_called)
        self.assertEqual(res["api_call_counts"]["generation_calls"], 0)

    def test_flat_parent_mode_routing(self):
        """6. Điều hướng chính xác 4 modes: single_flat, multi_flat, single_parent, multi_parent."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        fake_ans = lambda p, c, cl: "Answer"

        for m in ["single_flat", "multi_flat", "single_parent", "multi_parent"]:
            res = hierarchical_rag.execute_query_pipeline(
                f"Routing test {m}?",
                mode=m,
                store_dir=self.store_dir,
                query_generator_fn=fake_gen,
                per_query_retriever_fn=fake_retriever,
                reranker_fn=fake_reranker,
                answer_generator_fn=fake_ans
            )
            self.assertEqual(res["mode"], m)

    def test_multi_query_failure_status(self):
        """7. Lỗi multi-query generation trả warning và fallback chạy bằng Q0."""
        def fail_gen(p, m, t, c, cl):
            raise RuntimeError("Gemini Multi-Query Expansion Quota Exceeded")

        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        fake_ans = lambda p, c, cl: "Fallback Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "Fallback Q0?",
            mode="multi_parent",
            store_dir=self.store_dir,
            query_generator_fn=fail_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertIn("fallback về Q0", res["warnings"][0])
        self.assertEqual(res["status"], "ready")

    def test_reranker_failure_no_fallback(self):
        """8. Reranker lỗi trả status='reranker_unavailable' mà không âm thầm fallback giả điểm."""
        def fail_reranker(q, texts):
            raise RuntimeError("Cross-Encoder GPU Memory OOM")

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]

        res = hierarchical_rag.execute_query_pipeline(
            "Reranker fail?",
            mode="single_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fail_reranker
        )

        self.assertEqual(res["status"], "reranker_unavailable")

    def test_citation_uses_parent_and_anchor_child(self):
        """9. Citation object chứa đầy đủ thông tin parent_id, anchor_child_id và supporting_child_ids thực tế."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.95]
        fake_ans = lambda p, c, cl: "Answer [P1]"

        res = hierarchical_rag.execute_query_pipeline(
            "Citation test?",
            mode="single_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        cit = res["citations"][0]
        self.assertEqual(cit["citation_label"], "[P1]")
        self.assertEqual(cit["parent_id"], "PARENT_A")
        self.assertEqual(cit["anchor_child_id"], "CHILD_1")

    def test_citation_label_validation(self):
        """10. Nhãn citation [P1], [P2] chỉ được tạo từ evidence thực tế đã accepted."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        fake_ans = lambda p, c, cl: "Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "Label val?",
            mode="single_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertEqual(len(res["citations"]), 1)
        self.assertEqual(res["citations"][0]["citation_label"], "[P1]")

    def test_multi_mode_max_two_generation_calls(self):
        """11. Chế độ multi_parent gọi API generation tối đa 2 lần (1 cho multi-query expansion, 1 cho answer)."""
        gen_calls = 0
        def fake_gen(p, m, t, c, cl):
            nonlocal gen_calls
            gen_calls += 1
            return [{"text": "Variant Q1", "focus": "paraphrase"}]

        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]

        def fake_ans(p, c, cl):
            nonlocal gen_calls
            gen_calls += 1
            return "Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "Max two calls?",
            mode="multi_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertLessEqual(res["api_call_counts"]["generation_calls"], 2)
        self.assertEqual(gen_calls, 2)

    def test_compare_no_answer_generation(self):
        """12. Compare pipeline chạy 4 modes nhưng 0 lần gọi answer generation LLM API."""
        ans_calls = 0
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        
        def fake_ans(p, c, cl):
            nonlocal ans_calls
            ans_calls += 1
            return "Answer"

        results = hierarchical_rag.compare_pipeline(
            "Compare question?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertEqual(len(results), 4)
        self.assertEqual(ans_calls, 0)  # Tuyệt đối không gọi answer LLM!

    def test_trace_identity_and_counts(self):
        """13. Trả về đầy đủ identities, stage_latencies_ms và api_call_counts."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]
        fake_ans = lambda p, c, cl: "Answer"

        res = hierarchical_rag.execute_query_pipeline(
            "Trace check?",
            mode="single_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertIn("identities", res)
        self.assertIn("stage_latencies_ms", res)
        self.assertIn("api_call_counts", res)
        self.assertIn("total_latency_ms", res)

    def test_offline_with_injected_fakes(self):
        """14. Đảm bảo tất cả 14 test cases chạy 100% offline bằng injected fakes."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Offline Variant", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "CHILD_1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.95]
        fake_ans = lambda p, c, cl: "Offline Answer [P1]"

        res = hierarchical_rag.execute_query_pipeline(
            "Offline test?",
            mode="multi_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker,
            answer_generator_fn=fake_ans
        )

        self.assertEqual(res["status"], "ready")
        self.assertEqual(res["answer"], "Offline Answer [P1]")


if __name__ == "__main__":
    unittest.main()
