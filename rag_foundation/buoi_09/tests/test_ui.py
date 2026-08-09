"""
Unit tests cho UI Helper Functions của ứng dụng Streamlit (Buổi 09 — Step 08).
100% Thuần Python, 100% Offline, Không gọi Browser, Network hoặc Model real.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import app


class TestUIHelpers(unittest.TestCase):

    def test_build_query_child_matrix_data(self):
        """1. Kiểm tra tạo ma trận Query - Child data."""
        queries = [
            {"query_id": "Q0", "text": "Câu hỏi gốc", "origin": "original"},
            {"query_id": "Q1", "text": "Biến thể Q1", "origin": "generated"}
        ]
        child_hits = [
            {
                "child_id": "CHILD_1",
                "multi_query_rank": 1,
                "multi_query_rrf_score": 0.0325,
                "support_query_count": 2,
                "per_query_ranks": {"Q0": 1, "Q1": 2}
            },
            {
                "child_id": "CHILD_2",
                "multi_query_rank": 2,
                "multi_query_rrf_score": 0.0163,
                "support_query_count": 1,
                "per_query_ranks": {"Q0": 2}
            }
        ]

        matrix = app.build_query_child_matrix_data(child_hits, queries)
        self.assertEqual(len(matrix), 2)
        self.assertEqual(matrix[0]["Child Candidate ID"], "CHILD_1")
        self.assertEqual(matrix[0]["Q0"], "#1")
        self.assertEqual(matrix[0]["Q1"], "#2")
        self.assertEqual(matrix[1]["Q1"], "—")  # Q1 không truy vấn được CHILD_2

    def test_build_parent_tree_data(self):
        """2. Kiểm tra chuẩn hóa cấu trúc cây Parent - Child."""
        parents = [
            {
                "parent_id": "PARENT_A",
                "parent_rank": 1,
                "parent_rerank_rank": 1,
                "parent_rank_change": 0,
                "parent_rrf_score": 0.0163,
                "parent_rerank_score": 0.8542,
                "source": "doc1.pdf",
                "page_start": 1,
                "page_end": 2,
                "text": "Parent text...",
                "anchor_child_id": "CHILD_1",
                "scoring_child_ids": ["CHILD_1"],
                "supporting_child_ids": ["CHILD_1"],
                "support_query_ids": ["Q0", "Q1"],
                "ambiguous": False,
                "warnings": [],
                "child_hits_detail": []
            }
        ]

        tree = app.build_parent_tree_data(parents)
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["parent_id"], "PARENT_A")
        self.assertEqual(tree[0]["parent_rerank_score"], 0.8542)
        self.assertEqual(tree[0]["page_range"], "Trang 1-2")

    def test_build_mode_comparison_row(self):
        """3. Kiểm tra chuẩn hóa 1 hàng dữ liệu so sánh cho Mode."""
        res_mock = {
            "status": "ready",
            "accepted_evidence": [
                {"parent_id": "PARENT_A", "text": "Parent A text context sample..."}
            ],
            "child_hits": [{"child_id": "C1", "text": "Child 1"}],
            "parent_candidates": [{"parent_id": "PARENT_A"}],
            "total_latency_ms": 1250.5,
            "api_call_counts": {"generation_calls": 2, "embedding_calls": 4}
        }

        row = app.build_mode_comparison_row("multi_parent", res_mock)
        self.assertEqual(row["Mode"], "multi_parent")
        self.assertEqual(row["Status"], "ready")
        self.assertEqual(row["Accepted Evidence Count"], 1)
        self.assertEqual(row["Gen Calls"], 2)
        self.assertEqual(row["Embedding Calls"], 4)

    def test_format_citation_display(self):
        """4. Kiểm tra định dạng hiển thị Citation."""
        cit = {
            "citation_label": "[P1]",
            "source": "TT_39_2016_NHNN.pdf",
            "page_start": 5,
            "page_end": 6,
            "parent_id": "PARENT_A",
            "anchor_child_id": "CHILD_1",
            "parent_rerank_score": 0.9123,
            "ambiguous": True
        }

        display_str = app.format_citation_display(cit)
        self.assertIn("[P1]", display_str)
        self.assertIn("TT_39_2016_NHNN.pdf", display_str)
        self.assertIn("PARENT_A", display_str)
        self.assertIn("CHILD_1", display_str)
        self.assertIn("Ambiguity", display_str)

    def test_map_error_ux_message(self):
        """5. Kiểm tra ánh xạ thông điệp lỗi UX thân thiện."""
        title, detail, fix = app.map_error_ux_message("insufficient_evidence")
        self.assertIn("Không Tìm Thấy Căn Cứ", title)
        self.assertIn("RERANK_MIN_SCORE", fix)

        title_unk, detail_unk, fix_unk = app.map_error_ux_message("unknown_error_code")
        self.assertEqual(title_unk, "Lỗi Không Xác Định")


if __name__ == "__main__":
    unittest.main()
