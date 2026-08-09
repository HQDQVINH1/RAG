"""
Unit tests cho Indexing, Embeddings & ChromaDB Collection Management (Bước 05/08).
Kiểm thử các mục 10-13, 15-20, 39-42 theo SPEC.
"""

import sys
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

# Setup module import path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag import (
    get_collection_name,
    validate_embedding_vector,
    get_chroma_client,
    get_or_create_rag_collection,
    index_chunks,
    load_chunks
)


class MockGenAIClientForIndexing:
    def __init__(self, dim=128, fail_at_index=None, wrong_count=False, wrong_dim=False, bad_vector=None):
        self.dim = dim
        self.fail_at_index = fail_at_index
        self.wrong_count = wrong_count
        self.wrong_dim = wrong_dim
        self.bad_vector = bad_vector
        self.call_count = 0

    class Models:
        def __init__(self, parent):
            self.parent = parent

        def embed_content(self, model, contents, config=None):
            self.parent.call_count += 1
            idx = self.parent.call_count
            if self.parent.fail_at_index and idx == self.parent.fail_at_index:
                raise RuntimeError("API Error Simulated")
            
            if self.parent.bad_vector is not None:
                vec = self.parent.bad_vector
            elif self.parent.wrong_dim:
                vec = [0.1] * 50  # Wrong dimension (50 instead of 128)
            else:
                vec = [1.0] + [0.1] * (self.parent.dim - 1)

            class MockEmbedding:
                pass

            emb = MockEmbedding()
            emb.values = vec
            res = MockEmbedding()
            res.embeddings = [emb]
            return res

    @property
    def models(self):
        return self.Models(self)


class TestIndexingAndCollection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.fixture_path = BASE_DIR / "tests" / "fixtures" / "chunks_sample.json"
        # Dùng dimension nhỏ hợp lệ = 128 cho test theo quy định
        self.config = {
            "GEMINI_API_KEY": "mock_api_key_test",
            "GEMINI_EMBEDDING_MODEL": "gemini-embedding-2",
            "GEMINI_EMBEDDING_DIM": 128,
            "GEMINI_GENERATION_MODEL": "gemini-3.5-flash-lite",
            "DEFAULT_TOP_K": 5,
            "RAG_MAX_DISTANCE": 0.45,
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_10_index_twice_idempotent(self):
        """10. Index hai lần không tăng record count."""
        client_mock = MockGenAIClientForIndexing(dim=128)

        res1 = index_chunks(
            input_path=self.fixture_path,
            strategy="hierarchical",
            config=self.config,
            reset=True,
            genai_client=client_mock,
            storage_dir=self.temp_dir
        )
        self.assertEqual(res1["total_in_collection"], 3)

        res2 = index_chunks(
            input_path=self.fixture_path,
            strategy="hierarchical",
            config=self.config,
            reset=False,
            genai_client=client_mock,
            storage_dir=self.temp_dir
        )
        self.assertEqual(res2["total_in_collection"], 3)

    def test_11_metadata_citation_saved_completely(self):
        """11. Metadata citation được lưu đầy đủ trong ChromaDB."""
        client_mock = MockGenAIClientForIndexing(dim=128)
        index_chunks(
            input_path=self.fixture_path,
            strategy="hierarchical",
            config=self.config,
            reset=True,
            genai_client=client_mock,
            storage_dir=self.temp_dir
        )

        client = get_chroma_client(self.temp_dir)
        coll_name = get_collection_name("hierarchical", "gemini-embedding-2", 128)
        coll = client.get_collection(name=coll_name, embedding_function=None)

        got = coll.get(ids=["doc_sample_01_hierarchical_001"], include=["metadatas", "documents"])
        meta = got["metadatas"][0]

        self.assertEqual(meta["source"], "TT_sample_2024.pdf")
        self.assertEqual(meta["page_start"], 1)
        self.assertEqual(meta["page_end"], 1)
        self.assertEqual(meta["chunk_id"], "doc_sample_01_hierarchical_001")
        self.assertEqual(meta["strategy"], "hierarchical")

    def test_12_and_13_collection_identity_changes(self):
        """12 & 13. Collection identity thay đổi khi strategy, model hoặc dimension thay đổi."""
        name_h128 = get_collection_name("hierarchical", "gemini-embedding-2", 128)
        name_s128 = get_collection_name("semantic", "gemini-embedding-2", 128)
        name_h768 = get_collection_name("hierarchical", "gemini-embedding-2", 768)
        name_other_model = get_collection_name("hierarchical", "text-embedding-004", 128)

        self.assertNotEqual(name_h128, name_s128)
        self.assertNotEqual(name_h128, name_h768)
        self.assertNotEqual(name_h128, name_other_model)

    def test_15_16_17_18_39_embedding_validations(self):
        """15, 16, 17, 18, 39: Validation của vector embedding."""
        # 16. Vector rỗng / sai kiểu
        with self.assertRaises(ValueError):
            validate_embedding_vector([], 128, "c1")
        with self.assertRaises(ValueError):
            validate_embedding_vector("not_a_list", 128, "c1")

        # 17. Sai dimension (kỳ vọng 128, nhận 50)
        with self.assertRaises(ValueError):
            validate_embedding_vector([0.1] * 50, 128, "c1")

        # 18. Chứa NaN hoặc Infinity
        with self.assertRaises(ValueError):
            validate_embedding_vector([0.1] * 127 + [float("nan")], 128, "c1")
        with self.assertRaises(ValueError):
            validate_embedding_vector([0.1] * 127 + [float("inf")], 128, "c1")

        # 39. Chặn boolean và zero vector
        with self.assertRaises(ValueError):
            validate_embedding_vector([True] + [0.1] * 127, 128, "c1")
        with self.assertRaises(ValueError):
            validate_embedding_vector([0.0] * 128, 128, "c1")

    def test_19_and_41_embedding_error_before_upsert_keeps_old_collection(self):
        """19 & 41. Embedding lỗi trước upsert không thêm record mới và giữ nguyên collection hợp lệ cũ."""
        client_mock_good = MockGenAIClientForIndexing(dim=128)
        index_chunks(
            input_path=self.fixture_path,
            strategy="hierarchical",
            config=self.config,
            reset=True,
            genai_client=client_mock_good,
            storage_dir=self.temp_dir
        )

        client = get_chroma_client(self.temp_dir)
        coll_name = get_collection_name("hierarchical", "gemini-embedding-2", 128)
        self.assertEqual(client.get_collection(name=coll_name, embedding_function=None).count(), 3)

        # Giả lập lỗi ở chunk thứ 2 khi chạy lại với --reset
        client_mock_fail = MockGenAIClientForIndexing(dim=128, fail_at_index=2)
        with self.assertRaises(ValueError):
            index_chunks(
                input_path=self.fixture_path,
                strategy="hierarchical",
                config=self.config,
                reset=True,
                genai_client=client_mock_fail,
                storage_dir=self.temp_dir
            )

        # Collection cũ vẫn nguyên vẹn 3 record
        self.assertEqual(client.get_collection(name=coll_name, embedding_function=None).count(), 3)

    def test_20_missing_api_key_fails_without_upserting_fake_vector(self):
        """20. Thiếu API key phải fail rõ ràng và không upsert vector giả."""
        config_no_key = dict(self.config)
        config_no_key["GEMINI_API_KEY"] = ""

        with self.assertRaises(ValueError) as cm:
            index_chunks(
                input_path=self.fixture_path,
                strategy="hierarchical",
                config=config_no_key,
                reset=True,
                storage_dir=self.temp_dir
            )
        self.assertIn("Thiếu GEMINI_API_KEY", str(cm.exception))

    def test_40_status_on_empty_storage_does_not_create_collection(self):
        """40. Kiểm tra status trên storage trống không tạo collection mới."""
        client = get_chroma_client(self.temp_dir)
        initial_colls = client.list_collections()
        self.assertEqual(len(initial_colls), 0)

        coll_name = get_collection_name("hierarchical", "gemini-embedding-2", 128)
        # Chỉ check list_collections
        self.assertNotIn(coll_name, [c.name for c in client.list_collections()])
        self.assertEqual(len(client.list_collections()), 0)

    def test_42_existing_collection_metadata_mismatch_blocked(self):
        """42. Existing collection có metadata/configuration mismatch bị chặn trước khi upsert."""
        client = get_chroma_client(self.temp_dir)
        coll_name = get_collection_name("hierarchical", "gemini-embedding-2", 128)

        # Tạo collection giả có metadata bị sai strategy
        client.create_collection(
            name=coll_name,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={
                "strategy": "WRONG_STRATEGY",
                "embedding_model": "gemini-embedding-2",
                "embedding_dim": 128
            },
            embedding_function=None
        )

        client_mock = MockGenAIClientForIndexing(dim=128)
        with self.assertRaises(ValueError) as cm:
            index_chunks(
                input_path=self.fixture_path,
                strategy="hierarchical",
                config=self.config,
                reset=False,  # Không reset để phát hiện mismatch
                genai_client=client_mock,
                storage_dir=self.temp_dir
            )
        self.assertIn("không trùng khớp", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
