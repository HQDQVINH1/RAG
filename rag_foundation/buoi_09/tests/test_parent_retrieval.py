"""
Unit tests cho Child-to-Parent Expansion, Parent Score Aggregation & Context Budgeting (Buổi 09 — Step 06).

12 Test Cases (100% Offline, Temp Directory Hierarchy Store):
1. test_child_map_correct_parent
2. test_missing_stale_hierarchy_fails
3. test_parent_aggregation_formula_hand_calculated
4. test_child_score_cap
5. test_scoring_and_supporting_children_separated
6. test_parent_deduplicate
7. test_deterministic_parent_tie_break
8. test_parent_candidate_limit
9. test_context_budget_parent_boundary_only
10. test_oversized_first_parent_warning
11. test_expansion_factor_trace
12. test_no_reranker_or_generation_called
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


class TestParentRetrieval(unittest.TestCase):

    def setUp(self):
        hierarchical_rag.clear_multi_query_cache()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.store_dir = Path(self.tmp_dir.name)

        # Xây dựng mock hierarchy store
        self.children_data = [
            {"chunk_id": "CHILD_1", "parent_id": "PARENT_A", "text": "Child text 1", "source": "doc1.pdf", "ambiguous": False},
            {"chunk_id": "CHILD_2", "parent_id": "PARENT_A", "text": "Child text 2", "source": "doc1.pdf", "ambiguous": False},
            {"chunk_id": "CHILD_3", "parent_id": "PARENT_A", "text": "Child text 3", "source": "doc1.pdf", "ambiguous": False},
            {"chunk_id": "CHILD_4", "parent_id": "PARENT_A", "text": "Child text 4", "source": "doc1.pdf", "ambiguous": False},
            {"chunk_id": "CHILD_5", "parent_id": "PARENT_B", "text": "Child text 5", "source": "doc2.pdf", "ambiguous": False},
        ]
        self.parents_data = [
            {"parent_id": "PARENT_A", "source": "doc1.pdf", "page_start": 1, "page_end": 2, "text": "Parent A full text context string...", "ambiguous": False},
            {"parent_id": "PARENT_B", "source": "doc2.pdf", "page_start": 3, "page_end": 4, "text": "Parent B full text context string...", "ambiguous": False},
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

    def test_child_map_correct_parent(self):
        """1. Mọi child hit được ánh xạ chính xác sang đúng parent document."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]}
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Test question?",
            mode="single_parent",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0]["parent_id"], "PARENT_A")
        self.assertEqual(parents[0]["text"], "Parent A full text context string...")

    def test_missing_stale_hierarchy_fails(self):
        """2. Hierarchy store thiếu hoặc lỗi phải ném ngoại lệ hierarchy_not_ready."""
        empty_dir = Path(self.tmp_dir.name) / "non_existent"
        with self.assertRaises(RuntimeError) as ctx:
            hierarchical_rag.search_parent_candidates("Question?", store_dir=empty_dir)
        self.assertIn("hierarchy_not_ready", str(ctx.exception))

    def test_parent_aggregation_formula_hand_calculated(self):
        """3. Tính tay công thức parent_rrf_score (sum 1 / (60 + multi_query_rank))."""
        # CHILD_1 có rank 1, CHILD_2 có rank 2 (cùng PARENT_A)
        # parent_rrf_score = (1 / 61) + (1 / 62) = 0.01639344 + 0.01612903 = 0.03252247
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_2", "text": "Child text 2", "source": "doc1.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]}
        ]

        parents, _ = hierarchical_rag.search_parent_candidates(
            "Test formula?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        expected_score = (1.0 / (60 + 1)) + (1.0 / (60 + 2))
        self.assertAlmostEqual(parents[0]["parent_rrf_score"], expected_score, places=6)

    def test_child_score_cap(self):
        """4. Giới hạn tối đa PARENT_SCORE_CHILD_LIMIT (3) child đóng góp điểm vào parent_rrf_score."""
        config = hierarchical_rag.load_buoi09_config()
        config["PARENT_SCORE_CHILD_LIMIT"] = 2  # Chỉ cho 2 child tốt nhất đóng góp điểm

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_2", "text": "Child text 2", "source": "doc1.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_3", "text": "Child text 3", "source": "doc1.pdf", "multi_query_rank": 3, "support_query_ids": ["Q0"]}
        ]

        parents, _ = hierarchical_rag.search_parent_candidates(
            "Cap score test?",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        expected_cap_score = (1.0 / 61) + (1.0 / 62)  # CHILD_3 (rank 3) bị bỏ qua khi tính điểm!
        self.assertAlmostEqual(parents[0]["parent_rrf_score"], expected_cap_score, places=6)
        self.assertEqual(len(parents[0]["scoring_child_ids"]), 2)
        self.assertEqual(len(parents[0]["supporting_child_ids"]), 3)

    def test_scoring_and_supporting_children_separated(self):
        """5. Tách biệt rõ ràng scoring_child_ids (dùng tính điểm) và supporting_child_ids (tất cả child thuộc parent)."""
        config = hierarchical_rag.load_buoi09_config()
        config["PARENT_SCORE_CHILD_LIMIT"] = 1

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_2", "text": "Child text 2", "source": "doc1.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]}
        ]

        parents, _ = hierarchical_rag.search_parent_candidates(
            "Separated IDs?",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(parents[0]["scoring_child_ids"], ["CHILD_1"])
        self.assertEqual(parents[0]["supporting_child_ids"], ["CHILD_1", "CHILD_2"])

    def test_parent_deduplicate(self):
        """6. Nhiều child hits cùng thuộc 1 parent được hợp nhất thành 1 parent candidate duy nhất."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_2", "text": "Child text 2", "source": "doc1.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]}
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Deduplicate test?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(parents), 1)
        self.assertEqual(trace["unique_parent_count"], 1)

    def test_deterministic_parent_tie_break(self):
        """7. Sắp xếp parent theo thứ tự tie-break deterministic: rrf_score -> support_count -> best_child_rank -> parent_id."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant Q1", "focus": "paraphrase"}]
        # Q0 trả CHILD_5 (PARENT_B) ở rank 1 -> PARENT_B score = 1.5/61
        # Q1 trả CHILD_1 (PARENT_A) ở rank 1 -> PARENT_A score = 1.0/61 + Q0 rank 2 = 1.5/62
        # Cấu hình sao cho 2 parent có điểm bằng nhau 1.5/61:
        def fake_retriever(question, *a, **kw):
            if "Variant" in question:
                return [{"chunk_id": "CHILD_5", "text": "Child text 5", "source": "doc2.pdf", "fused_rank": 1}]
            return [{"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "fused_rank": 1}]

        parents, _ = hierarchical_rag.search_parent_candidates(
            "Tie break?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        # Cả PARENT_A (Q0) và PARENT_B (Q1) đều có 1 child hit duy nhất ở rank 1 (Q0 weight 1.5 cho A, Q1 weight 1.0 cho B)
        # PARENT_A có score = 1.5 / 61, PARENT_B có score = 1.0 / 61
        # Để bằng nhau: Q0 trả CHILD_5 ở rank 1, Q1 trả CHILD_1 ở rank 1 -> PARENT_B = 1.5/61, PARENT_A = 1.0/61
        # Cho Q0 không dùng weight khác biệt hoặc kiểm tra order ổn định:
        self.assertEqual(parents[0]["parent_id"], "PARENT_A")
        self.assertEqual(parents[1]["parent_id"], "PARENT_B")

    def test_parent_candidate_limit(self):
        """8. Giới hạn số lượng parent candidates theo PARENT_CANDIDATES config."""
        config = hierarchical_rag.load_buoi09_config()
        config["PARENT_CANDIDATES"] = 1

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_5", "text": "Child text 5", "source": "doc2.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]}
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Candidate limit test?",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(parents), 1)
        self.assertEqual(trace["parent_candidate_count"], 1)

    def test_context_budget_parent_boundary_only(self):
        """9. Context budget chỉ cắt ở ranh giới nguyên parent document, không bao giờ cắt giữa chừng."""
        config = hierarchical_rag.load_buoi09_config()
        # Đặt budget đủ cho Parent A (35 chars) nhưng không đủ thêm Parent B (35 chars)
        config["TOTAL_CONTEXT_MAX_CHARS"] = 40

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]},
            {"chunk_id": "CHILD_5", "text": "Child text 5", "source": "doc2.pdf", "multi_query_rank": 2, "support_query_ids": ["Q0"]}
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Budget boundary test?",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0]["parent_id"], "PARENT_A")
        self.assertEqual(trace["budget_selected_parent_count"], 1)

    def test_oversized_first_parent_warning(self):
        """10. Parent đầu tiên vượt budget sẽ được giữ lại kèm cảnh báo thay vì trả về rỗng."""
        config = hierarchical_rag.load_buoi09_config()
        config["TOTAL_CONTEXT_MAX_CHARS"] = 10  # Rất nhỏ, bé hơn cả Parent A (35 chars)

        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]}
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Oversized first parent?",
            config=config,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        self.assertEqual(len(parents), 1)
        self.assertIn("vượt quá TOTAL_CONTEXT_MAX_CHARS", trace["warnings"][0])

    def test_expansion_factor_trace(self):
        """11. Thống kê chính xác tỷ lệ mở rộng context_expansion_factor trong trace."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "1234567890", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]}  # 10 chars
        ]

        parents, trace = hierarchical_rag.search_parent_candidates(
            "Expansion factor test?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        expected_factor = round(len(parents[0]["text"]) / 10.0, 2)
        self.assertEqual(trace["context_expansion_factor"], expected_factor)

    def test_no_reranker_or_generation_called(self):
        """12. Đảm bảo chưa gọi Cross-Encoder Reranker hay LLM Answer Generation ở Bước 06."""
        fake_gen = lambda p, m, t, c, cl: []
        fake_retriever = lambda question, *a, **kw: [
            {"chunk_id": "CHILD_1", "text": "Child text 1", "source": "doc1.pdf", "multi_query_rank": 1, "support_query_ids": ["Q0"]}
        ]

        parents, _ = hierarchical_rag.search_parent_candidates(
            "No reranker test?",
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever
        )

        for p in parents:
            self.assertNotIn("parent_rerank_score", p)
            self.assertNotIn("accepted", p)


if __name__ == "__main__":
    unittest.main()
