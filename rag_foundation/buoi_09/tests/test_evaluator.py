"""
Unit tests cho Module Evaluate & Evaluation Report (Buổi 09 — Step 09).
100% Offline, Temp Hierarchy Store, Injected Fakes.
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import evaluate


class TestEvaluator(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.store_dir = Path(self.tmp_dir.name)

        # Xây dựng mock hierarchy store
        self.children_data = [
            {"child_id": "C1", "parent_id": "P1", "text": "Text 1", "source": "doc1.pdf"},
            {"child_id": "C2", "parent_id": "P2", "text": "Text 2", "source": "doc2.pdf"},
        ]
        self.parents_data = [
            {"parent_id": "P1", "source": "doc1.pdf", "text": "Parent 1 text"},
            {"parent_id": "P2", "source": "doc2.pdf", "text": "Parent 2 text"},
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

        # Mock dataset
        self.dataset_data = [
            {
                "question_id": "Q01",
                "question": "Test question?",
                "question_type": "exact",
                "relevant_child_ids": ["C1"],
                "relevant_parent_ids": ["P1"],
                "needs_human_review": True
            }
        ]
        self.dataset_path = self.store_dir / "test_questions.json"
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            json.dump(self.dataset_data, f)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_mrr_ndcg_recall_math(self):
        """1. Kiểm tra tính chính xác của công thức MRR, nDCG, Recall."""
        gt = ["P1", "P2"]
        retrieved = ["P3", "P1", "P4"]

        # P1 ở rank 2 -> MRR = 1/2 = 0.5
        mrr = evaluate.calculate_mrr(retrieved, gt)
        self.assertEqual(mrr, 0.5)

        # Recall = 1 hit / 2 gt = 0.5
        rec = evaluate.calculate_recall(retrieved, gt)
        self.assertEqual(rec, 0.5)

        # nDCG calculation
        ndcg = evaluate.calculate_ndcg(retrieved, gt, k=3)
        self.assertGreater(ndcg, 0.0)
        self.assertLessEqual(ndcg, 1.0)

    def test_evaluate_stale_id_detection(self):
        """2. Phát hiện Stale Child/Parent ID trong dataset không tồn tại trong Hierarchy Store."""
        stale_dataset = [
            {
                "question_id": "Q_STALE",
                "question": "Stale question?",
                "question_type": "exact",
                "relevant_child_ids": ["INVALID_CHILD_ID"],
                "relevant_parent_ids": ["P1"],
                "needs_human_review": False
            }
        ]
        stale_path = self.store_dir / "stale_questions.json"
        with open(stale_path, "w", encoding="utf-8") as f:
            json.dump(stale_dataset, f)

        with self.assertRaises(ValueError) as ctx:
            evaluate.run_evaluation(dataset_path=stale_path, store_dir=self.store_dir)
        self.assertIn("Stale Child ID", str(ctx.exception))

    def test_run_evaluation_offline_fakes(self):
        """3. Chạy evaluation hoàn chỉnh bằng injected fakes và kiểm tra báo cáo JSON trả về."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Variant", "focus": "paraphrase"}]
        fake_retriever = lambda question, *args, **kwargs: [{"chunk_id": "C1", "text": "Child 1", "source": "doc1.pdf", "fused_rank": 1}]
        fake_reranker = lambda q, texts: [0.9]

        report = evaluate.run_evaluation(
            dataset_path=self.dataset_path,
            store_dir=self.store_dir,
            query_generator_fn=fake_gen,
            per_query_retriever_fn=fake_retriever,
            reranker_fn=fake_reranker
        )

        self.assertIn("aggregate_summary_per_mode", report)
        self.assertTrue(report["needs_human_review"])
        self.assertIn("single_parent", report["aggregate_summary_per_mode"])

        # Kiểm tra file latest_report.json đã được tạo
        latest_file = BASE_DIR / "reports" / "latest_report.json"
        self.assertTrue(latest_file.exists())


if __name__ == "__main__":
    unittest.main()
