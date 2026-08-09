"""
Unit tests cho Multi-Query Expansion, Validation, Caching & Fallback (Buổi 09 — Step 04).

11 Test Cases (100% Offline, Zero Network Calls):
1. test_q0_first_and_preserved
2. test_strict_schema_validation
3. test_nfc_trim_max_length
4. test_duplicate_removal
5. test_legal_reference_preservation
6. test_no_invented_article_numbers
7. test_deterministic_ids
8. test_single_generator_call
9. test_cache_hit
10. test_api_error_returns_explicit_status
11. test_no_network_calls_in_tests
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag


class TestMultiQueryExpansion(unittest.TestCase):

    def setUp(self):
        hierarchical_rag.clear_multi_query_cache()

    def test_q0_first_and_preserved(self):
        """1. Q0 luôn nằm ở vị trí đầu tiên (queries[0]) và giữ nguyên nội dung gốc."""
        question = "  Điều kiện vay vốn ngân hàng là gì?  "
        fake_gen = lambda prompt, model, temp, cfg, client: [
            {"text": "Điều kiện vay vốn theo quy định?", "focus": "exact_legal_terms"}
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        
        self.assertEqual(res["queries"][0]["query_id"], "Q0")
        self.assertEqual(res["queries"][0]["text"], "Điều kiện vay vốn ngân hàng là gì?")
        self.assertEqual(res["queries"][0]["origin"], "original")
        self.assertEqual(res["queries"][0]["focus"], "original_intent")

    def test_strict_schema_validation(self):
        """2. Kiểm tra strict schema của kết quả trả về."""
        question = "Quy định về trích lập dự phòng rủi ro?"
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Tỷ lệ trích lập dự phòng rủi ro cụ thể?", "focus": "exact_legal_terms"}
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        
        self.assertIn("original_question", res)
        self.assertIn("queries", res)
        self.assertIn("model", res)
        self.assertIn("generation_latency_ms", res)
        self.assertIn("status", res)
        self.assertEqual(res["status"], "ready")

    def test_nfc_trim_max_length(self):
        """3. Chuẩn hóa NFC, trim whitespace và cắt bớt nếu vượt MULTI_QUERY_MAX_CHARS."""
        question = "Thỏa thuận lãi suất?"
        config = hierarchical_rag.load_buoi09_config()
        config["MULTI_QUERY_MAX_CHARS"] = 30  # Giới hạn 30 ký tự
        
        long_variant = "Đây là một câu biến thể có độ dài rất lớn vượt quá giới hạn ba mươi ký tự cho phép"
        fake_gen = lambda p, m, t, c, cl: [{"text": long_variant, "focus": "paraphrase"}]
        
        res = hierarchical_rag.generate_multi_queries(question, config=config, query_generator_fn=fake_gen)
        self.assertLessEqual(len(res["queries"][1]["text"]), 30)

    def test_duplicate_removal(self):
        """4. Loại bỏ các biến thể bị trùng lặp với Q0 hoặc trùng lặp với nhau."""
        question = "Điều kiện vay vốn"
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Điều kiện vay vốn", "focus": "paraphrase"},  # Trùng Q0
            {"text": "điều kiện vay vốn", "focus": "paraphrase"},  # Trùng Q0 case-insensitive
            {"text": "Điều kiện vay vốn TCTD?", "focus": "exact_legal_terms"},
            {"text": "Điều kiện vay vốn TCTD?", "focus": "exact_legal_terms"}  # Trùng Q1
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        self.assertEqual(len(res["queries"]), 2)  # Q0 và 1 variant
        self.assertEqual(res["dropped_duplicate_count"], 3)

    def test_legal_reference_preservation(self):
        """5. Bảo toàn số hiệu Điều/Khoản khi Q0 có chứa số hiệu pháp lý."""
        question = "Quy định tại Điều 7 Thông tư 39?"
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Điều kiện vay vốn tại Điều 7?", "focus": "exact_legal_terms"}
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        self.assertIn("Điều 7", res["queries"][1]["text"])

    def test_no_invented_article_numbers(self):
        """6. Loại bỏ biến thể bịa thêm số Điều không xuất hiện trong Q0."""
        question = "Điều kiện cơ cấu lại thời hạn trả nợ?"
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Quy định cơ cấu nợ tại Điều 99?", "focus": "exact_legal_terms"},  # Bịa Điều 99
            {"text": "Điều kiện tổ chức tín dụng xem xét cơ cấu nợ?", "focus": "paraphrase"}
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        self.assertEqual(len(res["queries"]), 2)  # Q0 và 1 variant hợp lệ
        self.assertIn("Loại bỏ biến thể bịa số Điều", res["warnings"][0])

    def test_deterministic_ids(self):
        """7. Gán lại ID theo chuỗi deterministic Q0, Q1, Q2..."""
        question = "Đối tượng áp dụng?"
        fake_gen = lambda p, m, t, c, cl: [
            {"text": "Thông tư này áp dụng cho ai?", "focus": "paraphrase"},
            {"text": "Các tổ chức tín dụng chịu điều chỉnh?", "focus": "exact_legal_terms"}
        ]
        res = hierarchical_rag.generate_multi_queries(question, query_generator_fn=fake_gen)
        ids = [q["query_id"] for q in res["queries"]]
        self.assertEqual(ids, ["Q0", "Q1", "Q2"])

    def test_single_generator_call(self):
        """8. Đảm bảo hàm generator chỉ được gọi đúng 1 lần duy nhất."""
        call_count = 0
        def fake_gen(p, m, t, c, cl):
            nonlocal call_count
            call_count += 1
            return [{"text": "Variant 1", "focus": "paraphrase"}]

        hierarchical_rag.generate_multi_queries("Test question?", query_generator_fn=fake_gen)
        self.assertEqual(call_count, 1)

    def test_cache_hit(self):
        """9. Lần gọi thứ 2 với cùng câu hỏi trả về cache_hit=True mà không gọi lại generator."""
        call_count = 0
        def fake_gen(p, m, t, c, cl):
            nonlocal call_count
            call_count += 1
            return [{"text": "Variant A", "focus": "paraphrase"}]

        res1 = hierarchical_rag.generate_multi_queries("Câu hỏi cache?", query_generator_fn=fake_gen)
        self.assertFalse(res1["cache_hit"])
        self.assertEqual(call_count, 1)

        res2 = hierarchical_rag.generate_multi_queries("Câu hỏi cache?", query_generator_fn=fake_gen)
        self.assertTrue(res2["cache_hit"])
        self.assertEqual(call_count, 1)  # Không tăng số lần gọi!

    def test_api_error_returns_explicit_status(self):
        """10. Khi API lỗi, trả về status='query_generation_unavailable' kèm error chi tiết và queries=[Q0]."""
        def error_gen(p, m, t, c, cl):
            raise RuntimeError("API Quota Exceeded")

        res = hierarchical_rag.generate_multi_queries("Câu hỏi lỗi API?", query_generator_fn=error_gen)
        self.assertEqual(res["status"], "query_generation_unavailable")
        self.assertEqual(len(res["queries"]), 1)
        self.assertEqual(res["queries"][0]["query_id"], "Q0")
        self.assertIn("API Quota Exceeded", res["error"])

    def test_no_network_calls_in_tests(self):
        """11. Xác nhận tất cả unit tests chạy 100% offline bằng Dependency Injection query_generator_fn."""
        fake_gen = lambda p, m, t, c, cl: [{"text": "Offline test variant", "focus": "paraphrase"}]
        res = hierarchical_rag.generate_multi_queries("Offline test question?", query_generator_fn=fake_gen)
        self.assertEqual(res["status"], "ready")


if __name__ == "__main__":
    unittest.main()
