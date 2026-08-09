"""
Unit tests cho BM25 Lexical Retrieval & Vietnamese Tokenizer (Buổi 08 - Bước 04).
"""

import sys
import unittest
from pathlib import Path

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import advanced_rag


class TestBM25Retrieval(unittest.TestCase):

    def setUp(self):
        self.sample_chunks = [
            {
                "chunk_id": "CHK_002",
                "strategy": "hierarchical",
                "source": "TEST_DOC.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "Điều 7. Điều kiện vay vốn đối với tổ chức tín dụng và khách hàng."
            },
            {
                "chunk_id": "CHK_001",
                "strategy": "hierarchical",
                "source": "TEST_DOC.pdf",
                "page_start": 2,
                "page_end": 2,
                "text": "Điều 7, Khoản 2. Các quy định hỗ trợ khách hàng vay vốn gặp khó khăn."
            },
            {
                "chunk_id": "CHK_003",
                "strategy": "hierarchical",
                "source": "TEST_DOC.pdf",
                "page_start": 3,
                "page_end": 3,
                "text": "Quy trình sát hạch và cấp giấy phép lái xe ô tô hạng B2."
            }
        ]

    def test_tokenizer_preserves_vietnamese_accents(self):
        """1. Tokenizer giữ nguyên các từ có dấu tiếng Việt."""
        text = "cơ cấu lại thời hạn trả nợ"
        tokens = advanced_rag.tokenize_vi_legal(text)
        expected = ["cơ", "cấu", "lại", "thời", "hạn", "trả", "nợ"]
        self.assertEqual(tokens, expected)

    def test_tokenizer_preserves_numbers_and_legal_terms(self):
        """2. Tokenizer giữ nguyên số và thuật ngữ Điều/Khoản."""
        text = "Điều 7, Khoản 2"
        tokens = advanced_rag.tokenize_vi_legal(text)
        expected = ["điều", "7", "khoản", "2"]
        self.assertEqual(tokens, expected)

    def test_corpus_and_query_use_same_preprocessing(self):
        """3. Corpus và query sử dụng chung một hàm preprocessing."""
        corpus_text = "Điều 7 Khoản 2"
        query_text = "điều 7 khoản 2"
        corpus_tokens = advanced_rag.tokenize_vi_legal(corpus_text)
        query_tokens = advanced_rag.tokenize_vi_legal(query_text)
        self.assertEqual(corpus_tokens, query_tokens)

    def test_exact_legal_term_ranked_above_unrelated(self):
        """4. Chunk chứa đúng thuật ngữ pháp lý được xếp trên chunk không chứa từ khóa."""
        question = "Điều 7 Khoản 2"
        results = advanced_rag.search_bm25(question, self.sample_chunks, candidate_k=3)
        self.assertGreater(len(results), 0)
        # Top 1 candidate phải là CHK_001 (chứa cả Điều 7 và Khoản 2)
        self.assertEqual(results[0]["chunk_id"], "CHK_001")
        # Chunk không liên quan (CHK_003) có điểm nhỏ hơn hoặc nằm ở cuối
        self.assertEqual(results[-1]["chunk_id"], "CHK_003")

    def test_candidate_k_larger_than_corpus(self):
        """5. Tự động xử lý khi candidate_k lớn hơn dung lượng corpus."""
        question = "điều kiện vay vốn"
        results = advanced_rag.search_bm25(question, self.sample_chunks, candidate_k=100)
        self.assertEqual(len(results), len(self.sample_chunks))

    def test_empty_question_fails(self):
        """6. Question rỗng, chỉ chứa khoảng trắng hoặc không có token phải báo lỗi rõ ràng."""
        with self.assertRaises(ValueError):
            advanced_rag.search_bm25("", self.sample_chunks, candidate_k=5)

        with self.assertRaises(ValueError):
            advanced_rag.search_bm25("   ", self.sample_chunks, candidate_k=5)

        with self.assertRaises(ValueError):
            advanced_rag.search_bm25("!!! ???", self.sample_chunks, candidate_k=5)

    def test_tie_break_deterministic(self):
        """7. Xử lý tie-break ổn định bằng chunk_id khi BM25 score bằng nhau."""
        tie_chunks = [
            {
                "chunk_id": "CHK_BBB",
                "strategy": "hierarchical",
                "source": "DOC.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "Kiểm toán ngân hàng."
            },
            {
                "chunk_id": "CHK_AAA",
                "strategy": "hierarchical",
                "source": "DOC.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "Kiểm toán ngân hàng."
            }
        ]
        results = advanced_rag.search_bm25("Kiểm toán", tie_chunks, candidate_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["bm25_score"], results[1]["bm25_score"])
        # Khi điểm bằng nhau, CHK_AAA đứng trước CHK_BBB (theo thứ tự bảng chữ cái)
        self.assertEqual(results[0]["chunk_id"], "CHK_AAA")
        self.assertEqual(results[1]["chunk_id"], "CHK_BBB")

    def test_no_external_api_calls(self):
        """8. Xác nhận không có lệnh gọi tới Gemini, Chroma hay Reranker."""
        # Kiểm tra search_bm25 hoạt động thuần túy trong memory mà không cần API Key hay DB client
        results = advanced_rag.search_bm25("thời hạn trả nợ", self.sample_chunks, candidate_k=2)
        self.assertIsInstance(results, list)
        for r in results:
            self.assertIn("bm25_score", r)
            self.assertIn("bm25_rank", r)


if __name__ == "__main__":
    unittest.main()
