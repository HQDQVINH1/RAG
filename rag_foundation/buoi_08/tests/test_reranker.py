"""
Unit tests cho Multilingual Cross-Encoder Reranker Stage (Buổi 08 - Bước 07).
Tất cả test case sử dụng Dependency Injection (fake reranker_fn) để đảm bảo chạy 100% offline.
"""

import sys
import math
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import advanced_rag


class TestRerankerStage(unittest.TestCase):

    def setUp(self):
        self.mock_config = {
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTesting12345",
            "GEMINI_EMBEDDING_MODEL": "gemini-embedding-2",
            "GEMINI_EMBEDDING_DIM": 768,
            "GEMINI_GENERATION_MODEL": "gemini-3.5-flash-lite",
            "RAG_MAX_DISTANCE": 0.45,
            "BM25_CANDIDATES": 20,
            "SEMANTIC_CANDIDATES": 20,
            "RRF_K": 60,
            "RRF_BM25_WEIGHT": 1.0,
            "RRF_SEMANTIC_WEIGHT": 1.0,
            "RERANK_CANDIDATES": 3,
            "FINAL_TOP_K": 2,
            "RERANKER_MODEL": "BAAI/bge-reranker-v2-m3",
            "RERANKER_MAX_LENGTH": 512,
            "RERANK_BATCH_SIZE": 4,
            "RERANK_MIN_SCORE": 0.50,
            "RERANK_DEVICE": "auto"
        }

        self.fused_sample = [
            {
                "chunk_id": "CHK_001",
                "text": "Nội dung A quy định điều kiện vay vốn.",
                "source": "DOC_A.pdf",
                "page_start": 1,
                "page_end": 1,
                "bm25_rank": 1,
                "semantic_rank": 2,
                "rrf_score": 0.032,
                "fused_rank": 1,
                "matched_by": ["bm25", "semantic"]
            },
            {
                "chunk_id": "CHK_002",
                "text": "Nội dung B quy định cơ cấu lại thời hạn trả nợ.",
                "source": "DOC_B.pdf",
                "page_start": 2,
                "page_end": 2,
                "bm25_rank": 2,
                "semantic_rank": 1,
                "rrf_score": 0.032,
                "fused_rank": 2,
                "matched_by": ["bm25", "semantic"]
            },
            {
                "chunk_id": "CHK_003",
                "text": "Nội dung C về trích lập dự phòng rủi ro.",
                "source": "DOC_C.pdf",
                "page_start": 3,
                "page_end": 3,
                "bm25_rank": 3,
                "semantic_rank": 3,
                "rrf_score": 0.031,
                "fused_rank": 3,
                "matched_by": ["bm25", "semantic"]
            },
            {
                "chunk_id": "CHK_004",
                "text": "Nội dung D ngoài phạm vi.",
                "source": "DOC_D.pdf",
                "page_start": 4,
                "page_end": 4,
                "bm25_rank": 4,
                "semantic_rank": 4,
                "rrf_score": 0.030,
                "fused_rank": 4,
                "matched_by": ["bm25", "semantic"]
            }
        ]

    def test_lazy_loading(self):
        """1. Đảm bảo mô hình Reranker KHÔNG được nạp khi import module hoặc chạy status."""
        self.assertIsNone(advanced_rag.RerankerModelManager._instance)
        # Chạy status read-only
        advanced_rag.get_advanced_status("hierarchical")
        self.assertIsNone(advanced_rag.RerankerModelManager._instance)

    def test_one_pair_per_candidate(self):
        """2. Fake reranker được gọi với đúng 1 cặp (question, candidate_text) cho mỗi ứng viên."""
        mock_fn = MagicMock(return_value=[1.0, 2.0, 0.5])
        results, trace = advanced_rag.rerank_candidates(
            question="cơ cấu nợ",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(mock_fn.call_count, 1)
        pairs_arg = mock_fn.call_args[0][0]
        # candidate subset_k = min(3, 4) = 3 pairs
        self.assertEqual(len(pairs_arg), 3)
        self.assertEqual(pairs_arg[0], ("cơ cấu nợ", "Nội dung A quy định điều kiện vay vốn."))

    def test_batch_preserves_candidate_count(self):
        """3. Quá trình chia batch không làm giảm hay mất số lượng candidate."""
        fake_logits = [0.1, 2.5, -0.5]
        mock_fn = MagicMock(return_value=fake_logits)

        results, trace = advanced_rag.rerank_candidates(
            question="điều kiện",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(trace["rerank_candidate_count"], 3)

    def test_sigmoid_score_calculation(self):
        """4. Chuẩn hóa rerank_score bằng công thức Sigmoid chính xác."""
        logit = 2.0
        mock_fn = MagicMock(return_value=[logit, 0.0, -1.0])

        results, _ = advanced_rag.rerank_candidates(
            question="test sigmoid",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        cand_1 = next(c for c in results if c["rerank_raw_score"] == 2.0)
        expected_sig = round(1.0 / (1.0 + math.exp(-2.0)), 6)
        self.assertEqual(cand_1["rerank_score"], expected_sig)

    def test_sort_and_tie_break(self):
        """5. Sắp xếp đúng theo rerank_score giảm dần -> fused_rank tăng dần -> chunk_id."""
        # Giả lập: CHK_002 logit = 3.0 (cao nhất), CHK_001 logit = 1.0, CHK_003 logit = 1.0 (bằng 001 nhưng fused_rank 3 > 1)
        mock_fn = MagicMock(return_value=[1.0, 3.0, 1.0])

        results, _ = advanced_rag.rerank_candidates(
            question="test sort",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(results[0]["chunk_id"], "CHK_002")  # Score cao nhất
        self.assertEqual(results[1]["chunk_id"], "CHK_001")  # Fused rank 1 nhỏ hơn CHK_003 (Fused rank 3)

    def test_rank_change_calculation(self):
        """6. Kiểm tra tính toán rank_change = fused_rank - rerank_rank chuẩn xác."""
        # CHK_002 từ fused_rank 2 lội ngược dòng lên rerank_rank 1 => rank_change = 2 - 1 = +1
        mock_fn = MagicMock(return_value=[1.0, 5.0, 0.0])

        results, _ = advanced_rag.rerank_candidates(
            question="test rank change",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        chk_002 = results[0]
        self.assertEqual(chk_002["chunk_id"], "CHK_002")
        self.assertEqual(chk_002["fused_rank"], 2)
        self.assertEqual(chk_002["rerank_rank"], 1)
        self.assertEqual(chk_002["rank_change"], 1)

    def test_subset_rerank_limit(self):
        """7. Chỉ rerank tối đa min(RERANK_CANDIDATES, total_candidates)."""
        mock_fn = MagicMock(return_value=[1.0, 2.0, 3.0])
        # mock_config RERANK_CANDIDATES = 3, fused_sample size = 4
        results, trace = advanced_rag.rerank_candidates(
            question="test subset",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(trace["rerank_candidate_count"], 3)

    def test_final_top_k_slice(self):
        """8. Kết quả cuối cùng chỉ cắt lấy FINAL_TOP_K candidates."""
        mock_fn = MagicMock(return_value=[1.0, 2.0, 3.0])
        # mock_config FINAL_TOP_K = 2
        results, trace = advanced_rag.rerank_candidates(
            question="test top k",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(trace["final_count"], 2)

    def test_model_error_raises_exception(self):
        """9. Khi nạp mô hình bị lỗi, phải raise RuntimeError('reranker_unavailable...') chứ không silent fallback."""
        def error_fn(pairs, *args):
            raise RuntimeError("reranker_unavailable: Không thể kết nối Hugging Face Hub.")

        with self.assertRaises(RuntimeError) as ctx:
            advanced_rag.rerank_candidates(
                question="test error",
                fused_candidates=self.fused_sample,
                reranker_fn=error_fn,
                config=self.mock_config
            )
        self.assertIn("reranker_unavailable", str(ctx.exception))

    def test_no_network_or_model_download_in_tests(self):
        """10. Tất cả unit test chạy 100% offline bằng Dependency Injection reranker_fn."""
        mock_fn = MagicMock(return_value=[2.0, 1.0, 0.5])
        results, trace = advanced_rag.rerank_candidates(
            question="offline test",
            fused_candidates=self.fused_sample,
            reranker_fn=mock_fn,
            config=self.mock_config
        )
        self.assertEqual(len(results), 2)
        self.assertIn("latency_ms", trace)
        self.assertIsInstance(trace["latency_ms"], float)


if __name__ == "__main__":
    unittest.main()
