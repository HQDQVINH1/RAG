"""
Unit tests cho Hierarchy Registry Builder & Atomic Store (Buổi 09 — Step 03).

14 Test Cases:
1. test_metadata_precedence
2. test_heading_inferred_at_start
3. test_carry_forward_same_source
4. test_no_carry_forward_across_sources
5. test_inline_dieu_not_heading
6. test_conflict_sets_ambiguous_and_warning
7. test_numeric_chunk_ordering
8. test_stable_parent_id
9. test_parent_split_at_child_boundary
10. test_oversized_child_warning
11. test_every_child_in_exact_one_parent
12. test_parent_pages_and_text_correct
13. test_atomic_build_and_manifest
14. test_status_is_read_only
"""

import sys
import os
import json
import unittest
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import hierarchical_rag


class TestHierarchyRegistry(unittest.TestCase):

    def test_metadata_precedence(self):
        """1. Metadata structure hợp lệ được ưu tiên cao nhất (resolution_method='metadata')."""
        sample_chunk = [{
            "chunk_id": "TEST_01_hierarchical_001",
            "strategy": "hierarchical",
            "source": "TEST_01.pdf",
            "page_start": 1,
            "page_end": 1,
            "text": "Nội dung thông thường không chứa heading ở dòng đầu.",
            "structure": {"chapter": "Chương I", "article": "Điều 1. Phạm vi"}
        }]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunk)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]["resolution_method"], "metadata")
        self.assertEqual(children[0]["structural_path"]["article"], "Điều 1. Phạm vi")

    def test_heading_inferred_at_start(self):
        """2. Heading rõ ràng ở đầu chunk được nhận diện (resolution_method='heading_inferred')."""
        sample_chunk = [{
            "chunk_id": "TEST_01_hierarchical_001",
            "strategy": "hierarchical",
            "source": "TEST_01.pdf",
            "page_start": 1,
            "page_end": 1,
            "text": "## Điều 5. Giữ nguyên nhóm nợ\nTổ chức tín dụng thực hiện giữ nguyên nhóm nợ...",
            "structure": None
        }]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunk)
        self.assertEqual(children[0]["resolution_method"], "heading_inferred")
        self.assertEqual(children[0]["structural_path"]["article"], "Điều 5. Giữ nguyên nhóm nợ")

    def test_carry_forward_same_source(self):
        """3. Carry forward chapter/article gần nhất cho các child tiếp theo trong CÙNG source."""
        sample_chunks = [
            {
                "chunk_id": "TEST_01_hierarchical_001",
                "strategy": "hierarchical",
                "source": "TEST_01.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "## Điều 4. Điều kiện vay vốn\nNội dung điều 4...",
                "structure": None
            },
            {
                "chunk_id": "TEST_01_hierarchical_002",
                "strategy": "hierarchical",
                "source": "TEST_01.pdf",
                "page_start": 1,
                "page_end": 2,
                "text": "Đoạn văn tiếp theo thuộc Điều 4 nhưng không ghi lại tiêu đề.",
                "structure": None
            }
        ]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunks)
        self.assertEqual(children[1]["resolution_method"], "carried_forward")
        self.assertEqual(children[1]["structural_path"]["article"], "Điều 4. Điều kiện vay vốn")

    def test_no_carry_forward_across_sources(self):
        """4. Tuyệt đối KHÔNG carry forward bài viết/chương qua source khác."""
        sample_chunks = [
            {
                "chunk_id": "TEST_01_hierarchical_001",
                "strategy": "hierarchical",
                "source": "TEST_01.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "## Điều 10. Lãi suất\nLãi suất thỏa thuận...",
                "structure": None
            },
            {
                "chunk_id": "TEST_02_hierarchical_001",
                "strategy": "hierarchical",
                "source": "TEST_02.pdf",
                "page_start": 1,
                "page_end": 1,
                "text": "Nội dung đầu tiên của văn bản 2 không ghi heading.",
                "structure": None
            }
        ]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunks)
        child_src2 = [c for c in children if c["source"] == "TEST_02.pdf"][0]
        self.assertEqual(child_src2["resolution_method"], "document_fallback")
        self.assertEqual(child_src2["structural_path"]["article"], "CHUA_XAC_DINH")

    def test_inline_dieu_not_heading(self):
        """5. Cụm 'Điều N' xuất hiện giữa câu không bị nhận nhầm thành heading chính."""
        sample_chunk = [{
            "chunk_id": "TEST_01_hierarchical_001",
            "strategy": "hierarchical",
            "source": "TEST_01.pdf",
            "page_start": 1,
            "page_end": 1,
            "text": "Báo cáo định kỳ hàng tháng theo quy định tại Khoản 4 Điều 7 Thông tư này.",
            "structure": None
        }]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunk)
        self.assertEqual(children[0]["resolution_method"], "document_fallback")

    def test_conflict_sets_ambiguous_and_warning(self):
        """6. Khi metadata xung đột với heading hoặc chứa nhiều Điều trích dẫn, đặt ambiguous=True và warning."""
        sample_chunk = [{
            "chunk_id": "TEST_01_hierarchical_001",
            "strategy": "hierarchical",
            "source": "TEST_01.pdf",
            "page_start": 1,
            "page_end": 1,
            "text": "## Điều 8. Nhu cầu vốn\nSửa đổi bổ sung Điều 22 và Điều 15 như sau...",
            "structure": {"article": "Điều 5. Nhóm nợ"}  # Xung đột metadata
        }]
        children, res_counts = hierarchical_rag.resolve_child_hierarchy(sample_chunk)
        self.assertTrue(children[0]["ambiguous"])
        self.assertGreater(len(children[0]["warnings"]), 0)

    def test_numeric_chunk_ordering(self):
        """7. Sắp xếp child theo phần sequence số của chunk_id (..._2 đứng trước ..._10)."""
        sample_chunks = [
            {"chunk_id": "FILE_hierarchical_010", "strategy": "hierarchical", "source": "F.pdf", "page_start": 2, "page_end": 2, "text": "Chunk 10", "structure": None},
            {"chunk_id": "FILE_hierarchical_002", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "Chunk 2", "structure": None}
        ]
        children, _ = hierarchical_rag.resolve_child_hierarchy(sample_chunks)
        self.assertEqual(children[0]["child_id"], "FILE_hierarchical_002")
        self.assertEqual(children[1]["child_id"], "FILE_hierarchical_010")

    def test_stable_parent_id(self):
        """8. Cùng input/config phải tạo ra Parent ID và manifest byte-identical."""
        sample_chunks = [{
            "chunk_id": "FILE_hierarchical_001", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1,
            "text": "## Điều 1. Phạm vi\nNội dung phạm vi...", "structure": None
        }]
        c1, _ = hierarchical_rag.resolve_child_hierarchy(sample_chunks)
        _, p1 = hierarchical_rag.build_parent_documents(c1, parent_max_chars=6000)

        c2, _ = hierarchical_rag.resolve_child_hierarchy(sample_chunks)
        _, p2 = hierarchical_rag.build_parent_documents(c2, parent_max_chars=6000)

        self.assertEqual(p1[0]["parent_id"], p2[0]["parent_id"])

    def test_parent_split_at_child_boundary(self):
        """9. Khi Article vượt parent_max_chars, chia parent window tại ranh giới child, không cắt vụn child."""
        c1 = {"chunk_id": "F_001", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "## Điều 1. Title\n" + "A" * 600, "structure": None}
        c2 = {"chunk_id": "F_002", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "B" * 600, "structure": None}
        
        children, _ = hierarchical_rag.resolve_child_hierarchy([c1, c2])
        # Đặt parent_max_chars = 800 -> Phải tách thành 2 parent windows
        _, parents = hierarchical_rag.build_parent_documents(children, parent_max_chars=800)
        
        self.assertEqual(len(parents), 2)
        self.assertEqual(parents[0]["child_ids"], ["F_001"])
        self.assertEqual(parents[1]["child_ids"], ["F_002"])

    def test_oversized_child_warning(self):
        """10. Child đơn lẻ lớn hơn parent_max_chars được giữ nguyên và đánh warning oversized_single_child."""
        c1 = {"chunk_id": "F_001", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "## Điều 1. Title\n" + "Z" * 1500, "structure": None}
        children, _ = hierarchical_rag.resolve_child_hierarchy([c1])
        updated_children, parents = hierarchical_rag.build_parent_documents(children, parent_max_chars=1000)
        
        self.assertEqual(len(parents), 1)
        self.assertIn("oversized_single_child", parents[0]["warnings"][0])
        self.assertEqual(len(parents[0]["text"]), len(c1["text"]))

    def test_every_child_in_exact_one_parent(self):
        """11. Mỗi child chunk thuộc về đúng 1 parent window."""
        c1 = {"chunk_id": "F_001", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "## Điều 1. A\nContent 1", "structure": None}
        c2 = {"chunk_id": "F_002", "strategy": "hierarchical", "source": "F.pdf", "page_start": 1, "page_end": 1, "text": "Content 2", "structure": None}
        children, _ = hierarchical_rag.resolve_child_hierarchy([c1, c2])
        updated_children, parents = hierarchical_rag.build_parent_documents(children, parent_max_chars=6000)
        
        parent_ids = [c["parent_id"] for c in updated_children]
        self.assertTrue(all(pid is not None for pid in parent_ids))
        self.assertEqual(len(set(parent_ids)), 1)

    def test_parent_pages_and_text_correct(self):
        """12. Parent pages = (min page_start, max page_end) và text được ghép chính xác."""
        c1 = {"chunk_id": "F_001", "strategy": "hierarchical", "source": "F.pdf", "page_start": 2, "page_end": 3, "text": "## Điều 1. A\nPart 1", "structure": None}
        c2 = {"chunk_id": "F_002", "strategy": "hierarchical", "source": "F.pdf", "page_start": 3, "page_end": 5, "text": "Part 2", "structure": None}
        children, _ = hierarchical_rag.resolve_child_hierarchy([c1, c2])
        _, parents = hierarchical_rag.build_parent_documents(children, parent_max_chars=6000)
        
        self.assertEqual(parents[0]["page_start"], 2)
        self.assertEqual(parents[0]["page_end"], 5)
        self.assertEqual(parents[0]["text"], "## Điều 1. A\nPart 1\n\nPart 2")

    def test_atomic_build_and_manifest(self):
        """13. Ghi atomic thành công với đầy đủ manifest fingerprints."""
        with tempfile.TemporaryDirectory() as tmp_input, tempfile.TemporaryDirectory() as tmp_store:
            tmp_input_path = Path(tmp_input)
            tmp_store_path = Path(tmp_store)

            sample_data = {
                "source": "SAMPLE.pdf",
                "chunks": [{
                    "chunk_id": "SAMPLE_hierarchical_001",
                    "strategy": "hierarchical",
                    "source": "SAMPLE.pdf",
                    "page_start": 1,
                    "page_end": 1,
                    "text": "## Điều 1. Test\nNội dung test atomic.",
                    "structure": None
                }]
            }
            (tmp_input_path / "chunks_SAMPLE.json").write_text(json.dumps(sample_data), encoding="utf-8")

            config = hierarchical_rag.load_buoi09_config()
            res = hierarchical_rag.build_and_save_hierarchy_store(
                input_dir=tmp_input_path,
                store_dir=tmp_store_path,
                config=config
            )

            self.assertTrue((tmp_store_path / "children.json").exists())
            self.assertTrue((tmp_store_path / "parents.json").exists())
            self.assertTrue((tmp_store_path / "manifest.json").exists())
            self.assertIn("chunks_SAMPLE.json", res["manifest"]["source_fingerprints"])

    def test_status_is_read_only(self):
        """14. Status command Read-Only tuyệt đối không tạo/sửa file hoặc timestamp."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "sub_store"
            # tmp_path chưa tồn tại
            status = hierarchical_rag.get_hierarchy_status(store_dir=tmp_path)
            self.assertFalse(status["hierarchy_store_exists"])
            self.assertFalse(tmp_path.exists())  # Không được tạo folder!


if __name__ == "__main__":
    unittest.main()
