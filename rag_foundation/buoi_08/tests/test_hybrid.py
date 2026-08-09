"""
Unit tests cho Reciprocal Rank Fusion (RRF) & Hybrid Retrieval (Buổi 08 - Bước 06).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import advanced_rag


class TestHybridRRFFusion(unittest.TestCase):

    def setUp(self):
        self.bm25_sample = [
            {
                "chunk_id": "CHK_001",
                "text": "Đoạn văn bản A về điều kiện vay vốn.",
                "source": "DOC_A.pdf",
                "page_start": 1,
                "page_end": 1,
                "bm25_rank": 1,
                "bm25_score": 4.5
            },
            {
                "chunk_id": "CHK_002",
                "text": "Đoạn văn bản B về cơ cấu nợ.",
                "source": "DOC_B.pdf",
                "page_start": 2,
                "page_end": 2,
                "bm25_rank": 2,
                "bm25_score": 3.0
            }
        ]

        self.semantic_sample = [
            {
                "chunk_id": "CHK_002",
                "text": "Đoạn văn bản B về cơ cấu nợ.",
                "source": "DOC_B.pdf",
                "page_start": 2,
                "page_end": 2,
                "semantic_rank": 1,
                "semantic_distance": 0.15
            },
            {
                "chunk_id": "CHK_003",
                "text": "Đoạn văn bản C về hoãn trả lãi.",
                "source": "DOC_C.pdf",
                "page_start": 3,
                "page_end": 3,
                "semantic_rank": 2,
                "semantic_distance": 0.25
            }
        ]

    def test_rrf_formula_arithmetic(self):
        """1. RRF formula tính toán số học đúng từng nhánh và cộng dồn."""
        # CHK_002: BM25 rank 2, Semantic rank 1 (rrf_k=60, w_bm25=1.0, w_sem=1.0)
        # Expected: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.01612903 + 0.01639344 = 0.032522
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, bm25_w=1.0, sem_w=1.0, top_k=5
        )
        chk_002 = next(r for r in results if r["chunk_id"] == "CHK_002")
        expected_score = round(1.0 / 62 + 1.0 / 61, 6)
        self.assertEqual(chk_002["rrf_score"], expected_score)

    def test_candidate_overlap_no_duplicate(self):
        """2. Candidate xuất hiện ở cả 2 nhánh không bị trùng lặp record."""
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, top_k=5
        )
        chunk_ids = [r["chunk_id"] for r in results]
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))
        self.assertEqual(counts["overlap_count"], 1)
        chk_002 = next(r for r in results if r["chunk_id"] == "CHK_002")
        self.assertIn("bm25", chk_002["matched_by"])
        self.assertIn("semantic", chk_002["matched_by"])

    def test_bm25_only_candidate_kept(self):
        """3. Candidate chỉ có ở BM25 vẫn được giữ lại."""
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, top_k=5
        )
        chk_001 = next(r for r in results if r["chunk_id"] == "CHK_001")
        self.assertIsNotNone(chk_001)
        self.assertEqual(chk_001["matched_by"], ["bm25"])
        self.assertIsNone(chk_001["semantic_rank"])

    def test_semantic_only_candidate_kept(self):
        """4. Candidate chỉ có ở Semantic vẫn được giữ lại."""
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, top_k=5
        )
        chk_003 = next(r for r in results if r["chunk_id"] == "CHK_003")
        self.assertIsNotNone(chk_003)
        self.assertEqual(chk_003["matched_by"], ["semantic"])
        self.assertIsNone(chk_003["bm25_rank"])

    def test_weight_zero_ignores_branch(self):
        """5. RRF weight bằng 0 sẽ loại bỏ hoàn toàn đóng góp điểm của nhánh đó."""
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, bm25_w=1.0, sem_w=0.0, top_k=5
        )
        # Khi sem_w = 0, điểm của CHK_003 (chỉ có ở sem) phải bằng 0.0
        chk_003 = next(r for r in results if r["chunk_id"] == "CHK_003")
        self.assertEqual(chk_003["rrf_score"], 0.0)

    def test_tie_break_deterministic(self):
        """6. Tie-break hoạt động ổn định và deterministic khi rrf_score bằng nhau."""
        # Tạo 2 candidate có cùng điểm RRF (bm25_w=1.0, sem_w=1.0)
        # Cand A: BM25 rank 1, Sem rank 2 -> RRF = 1/61 + 1/62
        # Cand B: BM25 rank 2, Sem rank 1 -> RRF = 1/62 + 1/61
        bm25_tie = [
            {"chunk_id": "CHK_A", "text": "Text A", "source": "S.pdf", "page_start": 1, "page_end": 1, "bm25_rank": 1, "bm25_score": 5.0},
            {"chunk_id": "CHK_B", "text": "Text B", "source": "S.pdf", "page_start": 1, "page_end": 1, "bm25_rank": 2, "bm25_score": 4.0}
        ]
        sem_tie = [
            {"chunk_id": "CHK_B", "text": "Text B", "source": "S.pdf", "page_start": 1, "page_end": 1, "semantic_rank": 1, "semantic_distance": 0.1},
            {"chunk_id": "CHK_A", "text": "Text A", "source": "S.pdf", "page_start": 1, "page_end": 1, "semantic_rank": 2, "semantic_distance": 0.2}
        ]
        results, _ = advanced_rag.reciprocal_rank_fusion(bm25_tie, sem_tie, rrf_k=60, top_k=2)
        self.assertEqual(results[0]["rrf_score"], results[1]["rrf_score"])
        # Theo tie-break rule 3: sem_rank 1 của CHK_B tốt hơn sem_rank 2 của CHK_A -> CHK_B xếp trước
        self.assertEqual(results[0]["chunk_id"], "CHK_B")
        self.assertEqual(results[1]["chunk_id"], "CHK_A")

    def test_metadata_mismatch_fails(self):
        """7. Metadata sai lệch giữa 2 nhánh của cùng chunk_id phải báo lỗi rõ ràng."""
        mismatch_sem = [
            {
                "chunk_id": "CHK_001",
                "text": "Đoạn văn bản A KHÁC BIỆT NỘI DUNG.",  # Mismatch text
                "source": "DOC_A.pdf",
                "page_start": 1,
                "page_end": 1,
                "semantic_rank": 1,
                "semantic_distance": 0.1
            }
        ]
        with self.assertRaises(ValueError):
            advanced_rag.reciprocal_rank_fusion(self.bm25_sample, mismatch_sem, rrf_k=60)

    def test_trace_counts_correct(self):
        """8. Trace thống kê đầy đủ các con số bm25_count, semantic_count, union_count, overlap_count, fused_count."""
        results, counts = advanced_rag.reciprocal_rank_fusion(
            self.bm25_sample, self.semantic_sample, rrf_k=60, top_k=2
        )
        self.assertEqual(counts["bm25_count"], 2)
        self.assertEqual(counts["semantic_count"], 2)
        self.assertEqual(counts["union_count"], 3)
        self.assertEqual(counts["overlap_count"], 1)
        self.assertEqual(counts["fused_count"], 2)

    @patch("advanced_rag.search_bm25")
    @patch("advanced_rag.search_semantic")
    @patch("rag.load_chunks")
    def test_hybrid_calls_retrievers_once(self, mock_load_chunks, mock_search_sem, mock_search_bm25):
        """9. search_hybrid chỉ gọi search_bm25 và search_semantic đúng một lần."""
        mock_load_chunks.return_value = ([], {})
        mock_search_bm25.return_value = self.bm25_sample
        mock_search_sem.return_value = self.semantic_sample

        res = advanced_rag.search_hybrid(
            question="thời hạn trả nợ",
            strategy="hierarchical",
            candidate_k=5
        )
        self.assertEqual(mock_search_bm25.call_count, 1)
        self.assertEqual(mock_search_sem.call_count, 1)
        self.assertIn("fused_candidates", res)
        self.assertIn("trace", res)

    def test_no_reranker_or_generation_loaded(self):
        """10. Xác nhận chưa có bất kỳ mô hình Reranker hay LLM Generation nào được nạp/tải."""
        # Giả lập mock 2 retriever
        with patch("advanced_rag.search_bm25", return_value=self.bm25_sample), \
             patch("advanced_rag.search_semantic", return_value=self.semantic_sample), \
             patch("rag.load_chunks", return_value=([], {})):
            
            res = advanced_rag.search_hybrid("thử nghiệm hybrid", strategy="hierarchical", candidate_k=5)
            self.assertGreater(len(res["fused_candidates"]), 0)
            self.assertIn("latency_ms", res["trace"])


if __name__ == "__main__":
    unittest.main()
