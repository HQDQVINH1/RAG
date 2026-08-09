"""
Unit tests cho Data Loader & Validator (Bước 04/08).
Kiểm thử các mục 1-9 và 38 theo SPEC.
"""

import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Setup module import path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag import load_chunks, validate_chunk


class TestDataLoaderAndValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_load_json_list(self):
        """1. Loader đọc JSON list hợp lệ."""
        file_path = self.temp_dir / "chunks_list.json"
        data = [
            {
                "chunk_id": "c1",
                "strategy": "hierarchical",
                "source": "doc.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "Nội dung 1"
            }
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        chunks, stats = load_chunks(file_path, strategy="hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(stats["valid_chunks"], 1)
        self.assertEqual(chunks[0]["chunk_id"], "c1")

    def test_02_load_json_object_with_chunks_key(self):
        """2. Loader đọc object có field `chunks`."""
        file_path = self.temp_dir / "chunks_obj.json"
        data = {
            "source": "doc.pdf",
            "chunks": [
                {
                    "chunk_id": "c2",
                    "strategy": "hierarchical",
                    "source": "doc.pdf",
                    "page_start": 2,
                    "page_end": 3,
                    "text": "Nội dung 2"
                }
            ]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        chunks, stats = load_chunks(file_path, strategy="hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "c2")

    def test_03_filter_exact_strategy(self):
        """3. Chỉ lấy đúng strategy được chọn."""
        file_path = self.temp_dir / "chunks_multi_strat.json"
        data = [
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "T1"},
            {"chunk_id": "c2", "strategy": "semantic", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "T2"},
            {"chunk_id": "c3", "strategy": "fixed-size", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "T3"}
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        chunks_h, stats_h = load_chunks(file_path, strategy="hierarchical")
        self.assertEqual(len(chunks_h), 1)
        self.assertEqual(chunks_h[0]["strategy"], "hierarchical")

        chunks_s, stats_s = load_chunks(file_path, strategy="semantic")
        self.assertEqual(len(chunks_s), 1)
        self.assertEqual(chunks_s[0]["strategy"], "semantic")

    def test_04_missing_required_field_fails(self):
        """4. Thiếu field bắt buộc phải fail."""
        bad_record = {"strategy": "hierarchical", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "T1"}
        with self.assertRaises(ValueError) as cm:
            validate_chunk(bad_record, "test.json", 1)
        self.assertIn("Thiếu field 'chunk_id'", str(cm.exception))

    def test_05_field_wrong_type_fails(self):
        """5. Field sai kiểu dữ liệu phải fail."""
        bad_record = {"chunk_id": 12345, "strategy": "hierarchical", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "T1"}
        with self.assertRaises(ValueError) as cm:
            validate_chunk(bad_record, "test.json", 1)
        self.assertIn("phải là string", str(cm.exception))

    def test_06_boolean_page_number_fails(self):
        """6. Boolean không được chấp nhận làm page number."""
        bad_record = {"chunk_id": "c1", "strategy": "hierarchical", "source": "d.pdf", "page_start": True, "page_end": 1, "text": "T1"}
        with self.assertRaises(ValueError) as cm:
            validate_chunk(bad_record, "test.json", 1)
        self.assertIn("không chấp nhận boolean", str(cm.exception))

    def test_07_page_start_greater_than_page_end_fails(self):
        """7. page_start > page_end phải fail."""
        bad_record = {"chunk_id": "c1", "strategy": "hierarchical", "source": "d.pdf", "page_start": 5, "page_end": 2, "text": "T1"}
        with self.assertRaises(ValueError) as cm:
            validate_chunk(bad_record, "test.json", 1)
        self.assertIn("page_start (5) lớn hơn page_end (2)", str(cm.exception))

    def test_08_empty_text_skipped_and_counted(self):
        """8. Text rỗng bị bỏ qua và thống kê đúng."""
        file_path = self.temp_dir / "chunks_empty_text.json"
        data = [
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "  \n  "},
            {"chunk_id": "c2", "strategy": "hierarchical", "source": "d.pdf", "page_start": 1, "page_end": 1, "text": "Hợp lệ"}
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        chunks, stats = load_chunks(file_path, strategy="hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(stats["empty_text_skipped"], 1)
        self.assertEqual(stats["valid_chunks"], 1)

    def test_09_duplicate_chunk_id_fails(self):
        """9. Duplicate chunk_id phải fail và báo vị trí."""
        file_path = self.temp_dir / "chunks_dup.json"
        data = [
            {"chunk_id": "dup1", "strategy": "hierarchical", "source": "d1.pdf", "page_start": 1, "page_end": 1, "text": "T1"},
            {"chunk_id": "dup1", "strategy": "hierarchical", "source": "d2.pdf", "page_start": 2, "page_end": 2, "text": "T2"}
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with self.assertRaises(ValueError) as cm:
            load_chunks(file_path, strategy="hierarchical")
        self.assertIn("Lỗi trùng lặp chunk_id 'dup1'", str(cm.exception))

    def test_38_non_dict_record_fails(self):
        """38. Loader chặn record không phải JSON object (như int, str, list)."""
        with self.assertRaises(ValueError) as cm:
            validate_chunk("chuoi_truc_tiep", "test.json", 1)
        self.assertIn("Record phải là JSON object (dict)", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            validate_chunk([1, 2, 3], "test.json", 1)
        self.assertIn("Record phải là JSON object (dict)", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
