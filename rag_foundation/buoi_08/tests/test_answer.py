"""
Unit tests cho Grounding, Citation Mapping & Answer Pipeline (Buổi 08 - Bước 08).
Tất cả boundary (Gemini API & Reranker model) được mock 100% offline.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import advanced_rag


class TestAnswerPipeline(unittest.TestCase):

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

        self.mock_fused_sample = [
            {
                "chunk_id": "CHK_001",
                "text": "Nội dung điều kiện cơ cấu nợ.",
                "source": "TT_02.pdf",
                "page_start": 1,
                "page_end": 1,
                "bm25_rank": 1,
                "bm25_score": 4.0,
                "semantic_rank": 1,
                "semantic_distance": 0.20,
                "rrf_score": 0.032,
                "fused_rank": 1,
                "matched_by": ["bm25", "semantic"]
            },
            {
                "chunk_id": "CHK_002",
                "text": "Nội dung quy định giữ nguyên nhóm nợ.",
                "source": "TT_02.pdf",
                "page_start": 2,
                "page_end": 2,
                "bm25_rank": 2,
                "bm25_score": 3.0,
                "semantic_rank": 2,
                "semantic_distance": 0.25,
                "rrf_score": 0.031,
                "fused_rank": 2,
                "matched_by": ["bm25", "semantic"]
            }
        ]

    @patch("advanced_rag.search_hybrid_rerank")
    def test_gating_filters_rejected_evidence(self, mock_search_hr):
        """1. Candidate bị từ chối do rerank_score < RERANK_MIN_SCORE bị loại khỏi context prompt."""
        reranked_sample = [
            dict(self.mock_fused_sample[0], rerank_score=0.80, rerank_raw_score=1.38, rerank_rank=1, rank_change=0),
            dict(self.mock_fused_sample[1], rerank_score=0.20, rerank_raw_score=-1.38, rerank_rank=2, rank_change=0)
        ]
        mock_search_hr.return_value = {
            "fused_candidates": self.mock_fused_sample,
            "reranked_candidates": reranked_sample,
            "trace": {
                "bm25_candidate_count": 2, "semantic_candidate_count": 2, "overlap_count": 2,
                "union_count": 2, "latency_ms": {"bm25": 1.0, "semantic": 1.0, "fusion": 1.0, "rerank": 1.0},
                "rerank": {"rerank_candidate_count": 2}
            }
        }

        mock_genai_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Điều kiện cơ cấu nợ [E1]."
        mock_genai_client.models.generate_content.return_value = mock_resp

        res = advanced_rag.query_advanced_rag(
            question="điều kiện cơ cấu",
            mode="hybrid_rerank",
            config=self.mock_config,
            genai_client=mock_genai_client
        )

        self.assertEqual(res["status"], "answered")
        self.assertEqual(res["trace"]["accepted"], 1)
        # Verify context trong prompt chỉ chứa [E1] (CHK_001), không chứa [E2] Nguồn
        prompt_sent = mock_genai_client.models.generate_content.call_args[1]["contents"]
        self.assertIn("[E1] Nguồn:", prompt_sent)
        self.assertNotIn("[E2] Nguồn:", prompt_sent)

    @patch("advanced_rag.search_hybrid_rerank")
    def test_insufficient_evidence_status(self, mock_search_hr):
        """2. Khi không có evidence nào đạt gating (0 accepted), trả về status='insufficient_evidence' và KHÔNG gọi LLM."""
        reranked_low_score = [
            dict(self.mock_fused_sample[0], rerank_score=0.10, rerank_raw_score=-2.0, rerank_rank=1, rank_change=0)
        ]
        mock_search_hr.return_value = {
            "fused_candidates": self.mock_fused_sample,
            "reranked_candidates": reranked_low_score,
            "trace": {
                "bm25_candidate_count": 2, "semantic_candidate_count": 2, "overlap_count": 2,
                "union_count": 2, "latency_ms": {"bm25": 1.0, "semantic": 1.0, "fusion": 1.0, "rerank": 1.0},
                "rerank": {"rerank_candidate_count": 1}
            }
        }

        mock_genai_client = MagicMock()

        res = advanced_rag.query_advanced_rag(
            question="câu hỏi ngoài phạm vi",
            mode="hybrid_rerank",
            config=self.mock_config,
            genai_client=mock_genai_client
        )

        self.assertEqual(res["status"], "insufficient_evidence")
        self.assertFalse(res["trace"]["generation_called"])
        self.assertEqual(mock_genai_client.models.generate_content.call_count, 0)

    @patch("advanced_rag.search_hybrid_rerank")
    def test_citation_mapping_to_real_metadata(self, mock_search_hr):
        """3. Nhãn [E1] được map chuẩn xác sang metadata thật; nhãn giả [E99] sinh warning."""
        reranked_sample = [
            dict(self.mock_fused_sample[0], rerank_score=0.90, rerank_raw_score=2.0, rerank_rank=1, rank_change=0)
        ]
        mock_search_hr.return_value = {
            "fused_candidates": self.mock_fused_sample,
            "reranked_candidates": reranked_sample,
            "trace": {
                "bm25_candidate_count": 1, "semantic_candidate_count": 1, "overlap_count": 1,
                "union_count": 1, "latency_ms": {"bm25": 1.0, "semantic": 1.0, "fusion": 1.0, "rerank": 1.0},
                "rerank": {"rerank_candidate_count": 1}
            }
        }

        mock_genai_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Theo quy định [E1], thông tin khác [E99]."
        mock_genai_client.models.generate_content.return_value = mock_resp

        res = advanced_rag.query_advanced_rag(
            question="quy định",
            mode="hybrid_rerank",
            config=self.mock_config,
            genai_client=mock_genai_client
        )

        self.assertEqual(res["status"], "answered")
        self.assertEqual(len(res["citations"]), 1)
        self.assertEqual(res["citations"][0]["label"], "[E1]")
        self.assertEqual(res["citations"][0]["chunk_id"], "CHK_001")
        self.assertEqual(res["citations"][0]["source"], "TT_02.pdf")
        self.assertTrue(any("[E99]" in w for w in res["warnings"]))

    @patch("advanced_rag.search_hybrid_rerank")
    def test_generation_called_max_once(self, mock_search_hr):
        """4. Hàm generate_content chỉ được gọi tối đa đúng 1 lần trong 1 lượt query."""
        reranked_sample = [
            dict(self.mock_fused_sample[0], rerank_score=0.90, rerank_raw_score=2.0, rerank_rank=1, rank_change=0)
        ]
        mock_search_hr.return_value = {
            "fused_candidates": self.mock_fused_sample,
            "reranked_candidates": reranked_sample,
            "trace": {
                "bm25_candidate_count": 1, "semantic_candidate_count": 1, "overlap_count": 1,
                "union_count": 1, "latency_ms": {"bm25": 1.0, "semantic": 1.0, "fusion": 1.0, "rerank": 1.0},
                "rerank": {"rerank_candidate_count": 1}
            }
        }

        mock_genai_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Trả lời [E1]."
        mock_genai_client.models.generate_content.return_value = mock_resp

        res = advanced_rag.query_advanced_rag(
            question="test query max once",
            mode="hybrid_rerank",
            config=self.mock_config,
            genai_client=mock_genai_client
        )
        self.assertEqual(mock_genai_client.models.generate_content.call_count, 1)

    @patch("advanced_rag.search_bm25")
    @patch("advanced_rag.search_semantic")
    @patch("advanced_rag.search_hybrid")
    @patch("advanced_rag.search_hybrid_rerank")
    def test_compare_does_not_call_generation(self, mock_hr, mock_h, mock_sem, mock_bm):
        """5. Lệnh compare_retrieval_modes thực thi so sánh 4 mode mà KHÔNG gọi LLM generation."""
        mock_bm.return_value = self.mock_fused_sample
        mock_sem.return_value = self.mock_fused_sample
        mock_h.return_value = {"fused_candidates": self.mock_fused_sample, "trace": {}}
        mock_hr.return_value = {"reranked_candidates": self.mock_fused_sample, "trace": {}}

        mock_genai_client = MagicMock()

        comp_res = advanced_rag.compare_retrieval_modes(
            question="thử nghiệm compare",
            config=self.mock_config,
            genai_client=mock_genai_client
        )

        self.assertIn("comparison_rows", comp_res)
        self.assertIn("latencies_ms", comp_res)
        self.assertEqual(mock_genai_client.models.generate_content.call_count, 0)

    @patch("advanced_rag.search_hybrid_rerank")
    def test_reranker_unavailable_status(self, mock_search_hr):
        """6. Khi Reranker bị lỗi (thư viện/mô hình), trả về status='reranker_unavailable'."""
        mock_search_hr.side_effect = RuntimeError("reranker_unavailable: Lỗi không tải được weights.")

        res = advanced_rag.query_advanced_rag(
            question="test reranker error",
            mode="hybrid_rerank",
            config=self.mock_config
        )

        self.assertEqual(res["status"], "reranker_unavailable")
        self.assertEqual(res["answer"], "")
        self.assertTrue(any("reranker_unavailable" in w for w in res["warnings"]))

    @patch("advanced_rag.search_hybrid_rerank")
    def test_schema_completeness(self, mock_search_hr):
        """7. Đảm bảo cấu trúc Schema trả về có đầy đủ các trường quy định."""
        reranked_sample = [
            dict(self.mock_fused_sample[0], rerank_score=0.10, rerank_raw_score=-2.0, rerank_rank=1, rank_change=0)
        ]
        mock_search_hr.return_value = {
            "fused_candidates": self.mock_fused_sample,
            "reranked_candidates": reranked_sample,
            "trace": {
                "bm25_candidate_count": 1, "semantic_candidate_count": 1, "overlap_count": 1,
                "union_count": 1, "latency_ms": {"bm25": 1.0, "semantic": 1.0, "fusion": 1.0, "rerank": 1.0},
                "rerank": {"rerank_candidate_count": 1}
            }
        }

        res = advanced_rag.query_advanced_rag(
            question="test schema",
            mode="hybrid_rerank",
            config=self.mock_config
        )
        self.assertIn("status", res)
        self.assertIn("mode", res)
        self.assertIn("question", res)
        self.assertIn("answer", res)
        self.assertIn("evidence", res)
        self.assertIn("citations", res)
        self.assertIn("warnings", res)
        self.assertIn("trace", res)
        self.assertIn("latency_ms", res["trace"])


if __name__ == "__main__":
    unittest.main()
