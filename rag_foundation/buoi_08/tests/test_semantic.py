"""
Unit tests cho Semantic Candidate Retrieval & Status Read-Only (Buổi 08 - Bước 05).
Mock embedding API & ChromaDB temporary client.
"""

import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Thêm đường dẫn buoi_08 vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import chromadb
import advanced_rag
import rag


class TestSemanticRetrieval(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "chroma"

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
            "RERANK_CANDIDATES": 20,
            "FINAL_TOP_K": 5,
            "RERANKER_MODEL": "BAAI/bge-reranker-v2-m3",
            "RERANKER_MAX_LENGTH": 512,
            "RERANK_BATCH_SIZE": 4,
            "RERANK_MIN_SCORE": 0.50,
            "RERANK_DEVICE": "auto"
        }

        # Mock GenAI client cho embedding (trả về vector 768 float hợp lệ)
        self.mock_genai_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]
        self.mock_genai_client.models.embed_content.return_value = mock_response

        # Khởi tạo Chroma collection mẫu với 3 records
        client = rag.get_chroma_client(self.storage_dir)
        collection = rag.get_or_create_rag_collection(client, "hierarchical", self.mock_config)

        ids = ["CHK_001", "CHK_002", "CHK_003"]
        documents = [
            "Quy định về cơ cấu lại thời hạn trả nợ.",
            "Điều kiện gia hạn nợ gốc và hoãn trả lãi vay.",
            "Quy trình cấp giấy phép lái xe."
        ]
        embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        metadatas = [
            {"source": "TT_02.pdf", "page_start": 1, "page_end": 1, "chunk_id": "CHK_001", "strategy": "hierarchical"},
            {"source": "TT_02.pdf", "page_start": 2, "page_end": 2, "chunk_id": "CHK_002", "strategy": "hierarchical"},
            {"source": "TRAFFIC.pdf", "page_start": 5, "page_end": 5, "chunk_id": "CHK_003", "strategy": "hierarchical"}
        ]
        collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_semantic_top_k_count_and_order(self):
        """1. Semantic retrieval trả về đúng số lượng top_k và giữ đúng thứ tự xếp hạng của Chroma."""
        results = advanced_rag.search_semantic(
            question="thời hạn trả nợ",
            strategy="hierarchical",
            candidate_k=2,
            config=self.mock_config,
            storage_dir=self.storage_dir,
            genai_client=self.mock_genai_client
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["semantic_rank"], 1)
        self.assertEqual(results[1]["semantic_rank"], 2)
        self.assertLessEqual(results[0]["semantic_distance"], results[1]["semantic_distance"])

    def test_semantic_metadata_complete(self):
        """2. Candidates chứa đầy đủ thông tin metadata cần thiết."""
        results = advanced_rag.search_semantic(
            question="điều kiện gia hạn nợ",
            strategy="hierarchical",
            candidate_k=1,
            config=self.mock_config,
            storage_dir=self.storage_dir,
            genai_client=self.mock_genai_client
        )
        self.assertEqual(len(results), 1)
        cand = results[0]
        self.assertIn("chunk_id", cand)
        self.assertIn("text", cand)
        self.assertIn("source", cand)
        self.assertIn("page_start", cand)
        self.assertIn("page_end", cand)
        self.assertIn("semantic_rank", cand)
        self.assertIn("semantic_distance", cand)

    def test_collection_mismatch_blocked(self):
        """3. Chặn không cho truy vấn nếu cấu hình metadata collection bị sai lệch."""
        mismatch_config = dict(self.mock_config)
        mismatch_config["GEMINI_EMBEDDING_DIM"] = 512  # Mismatch dim (768 vs 512)

        with self.assertRaises(ValueError):
            advanced_rag.search_semantic(
                question="test mismatch",
                strategy="hierarchical",
                candidate_k=2,
                config=mismatch_config,
                storage_dir=self.storage_dir,
                genai_client=self.mock_genai_client
            )

    def test_status_does_not_create_collection(self):
        """4. Hàm status hoạt động Read-Only, không tự ý tạo collection mới trong Chroma."""
        client = chromadb.PersistentClient(path=str(self.storage_dir))
        colls_before = [c.name for c in client.list_collections()]

        # Gọi status với strategy không tồn tại
        st_info = advanced_rag.get_advanced_status(strategy="semantic", storage_dir=self.storage_dir)

        colls_after = [c.name for c in client.list_collections()]
        self.assertEqual(colls_before, colls_after)
        self.assertFalse(st_info["collection_exists"])

    def test_missing_api_key_fails(self):
        """5. Báo lỗi rõ ràng khi thiếu GEMINI_API_KEY, không tạo vector giả."""
        no_key_config = dict(self.mock_config)
        no_key_config["GEMINI_API_KEY"] = ""

        with self.assertRaises(ValueError):
            advanced_rag.search_semantic(
                question="thời hạn trả nợ",
                strategy="hierarchical",
                candidate_k=2,
                config=no_key_config,
                storage_dir=self.storage_dir,
                genai_client=None
            )

    def test_no_generation_called(self):
        """6. Đảm bảo không có bất kỳ lệnh gọi LLM generation nào trong bước semantic retrieval."""
        results = advanced_rag.search_semantic(
            question="thời hạn trả nợ",
            strategy="hierarchical",
            candidate_k=3,
            config=self.mock_config,
            storage_dir=self.storage_dir,
            genai_client=self.mock_genai_client
        )
        self.assertGreater(len(results), 0)
        # Verify call_count của generate_content là 0 (chỉ embed_content được gọi)
        self.assertEqual(self.mock_genai_client.models.generate_content.call_count, 0)


if __name__ == "__main__":
    unittest.main()
