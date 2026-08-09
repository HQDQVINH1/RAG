"""
Unit tests cho Evaluator Metrics (Recall@K, MRR@K, nDCG@K) (Buổi 08 - Bước 10).
Tất cả công thức được kiểm tra tính toán số học trên các ví dụ nhỏ tính tay.
"""

import sys
import math
import unittest
from pathlib import Path

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import evaluate


class TestEvaluatorMetrics(unittest.TestCase):

    def test_recall_at_k_hand_calculated(self):
        """1. Kiểm tra công thức Recall@K tính tay."""
        gold = ["A", "B"]
        retrieved = ["C", "A", "B", "D"]

        # Top 1 retrieved = ["C"], hits = 0 -> Recall@1 = 0/2 = 0.0
        self.assertEqual(evaluate.compute_recall_at_k(retrieved, gold, k=1), 0.0)

        # Top 2 retrieved = ["C", "A"], hits = {"A"} -> Recall@2 = 1/2 = 0.5
        self.assertEqual(evaluate.compute_recall_at_k(retrieved, gold, k=2), 0.5)

        # Top 3 retrieved = ["C", "A", "B"], hits = {"A", "B"} -> Recall@3 = 2/2 = 1.0
        self.assertEqual(evaluate.compute_recall_at_k(retrieved, gold, k=3), 1.0)

    def test_mrr_at_k_hand_calculated(self):
        """2. Kiểm tra công thức MRR@K (Reciprocal Rank của nhãn đúng đầu tiên)."""
        gold = ["A", "B"]
        retrieved = ["C", "A", "B", "D"]

        # Top 1: ["C"], no gold -> MRR@1 = 0.0
        self.assertEqual(evaluate.compute_mrr_at_k(retrieved, gold, k=1), 0.0)

        # Top 2: ["C", "A"], hit "A" at rank 2 -> MRR@2 = 1/2 = 0.5
        self.assertEqual(evaluate.compute_mrr_at_k(retrieved, gold, k=2), 0.5)

        # Top 3: ["C", "A", "B"], first hit "A" at rank 2 -> MRR@3 = 1/2 = 0.5
        self.assertEqual(evaluate.compute_mrr_at_k(retrieved, gold, k=3), 0.5)

        # Direct hit at rank 1
        self.assertEqual(evaluate.compute_mrr_at_k(["A", "C"], gold, k=2), 1.0)

    def test_ndcg_at_k_hand_calculated(self):
        """3. Kiểm tra công thức nDCG@K tính tay với Binary Relevance."""
        gold = ["A", "B"]
        retrieved = ["C", "A", "B", "D"]

        # k = 3:
        # DCG@3 = 0/log2(2) + 1/log2(3) + 1/log2(4) = 0 + 1/1.5849625 + 1/2.0 = 0.63092975 + 0.5 = 1.13092975
        # IDCG@3 = 1/log2(2) + 1/log2(3) = 1.0 + 0.63092975 = 1.63092975
        # nDCG@3 = 1.13092975 / 1.63092975 = 0.693426

        expected_dcg = 0.0 + (1.0 / math.log2(3)) + (1.0 / math.log2(4))
        expected_idcg = (1.0 / math.log2(2)) + (1.0 / math.log2(3))
        expected_ndcg = expected_dcg / expected_idcg

        calculated_ndcg = evaluate.compute_ndcg_at_k(retrieved, gold, k=3)
        self.assertAlmostEqual(calculated_ndcg, expected_ndcg, places=5)

    def test_ndcg_perfect_score(self):
        """4. nDCG@K phải bằng 1.0 khi danh sách trả về hoàn hảo."""
        gold = ["A", "B"]
        retrieved = ["A", "B", "C"]
        self.assertEqual(evaluate.compute_ndcg_at_k(retrieved, gold, k=2), 1.0)

    def test_p50_calculation(self):
        """5. Kiểm tra tính toán trung vị P50."""
        self.assertEqual(evaluate.compute_p50([10.0, 20.0, 30.0]), 20.0)
        self.assertEqual(evaluate.compute_p50([10.0, 20.0, 30.0, 40.0]), 25.0)


if __name__ == "__main__":
    unittest.main()
