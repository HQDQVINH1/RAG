"""
Hierarchical & Multi-Query Advanced RAG Engine (Buổi 09).

Mô tả:
Module mở rộng cho Buổi 09 triển khai:
1. Load & Validate Cấu hình Multi-Query & Parent-Child
2. Hierarchy Registry Builder (Deterministic Child-to-Parent Mapper)
3. Atomic Hierarchy Store (children.json, parents.json, manifest.json)
4. Read-Only Status & Audit Diagnostics
5. CLI Commands: hierarchy-audit, build-hierarchy, hierarchy-status
"""

import sys
import os
import re
import math
import time
import json
import hashlib
import argparse
import datetime
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set, Callable
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import rag
import advanced_rag

HIERARCHY_STORE_DIR = BASE_DIR / "storage" / "hierarchy"
CHILDREN_FILE = HIERARCHY_STORE_DIR / "children.json"
PARENTS_FILE = HIERARCHY_STORE_DIR / "parents.json"
MANIFEST_FILE = HIERARCHY_STORE_DIR / "manifest.json"

# REGEX PATTERNS
RE_CHAPTER = re.compile(
    r"^(?:##\s*|\*\*|#\s*)?(Chương|Chuong)\s+([IVXLCDM0-9]+)[\.\:]?\s*(.*)",
    re.IGNORECASE | re.UNICODE
)
RE_ARTICLE_HEADING = re.compile(
    r"^(?:##\s*|\*\*|#\s*)?(Điều|Djeu|Dieu)\s+([0-9]+)[\.\:]?\s*(.*)",
    re.IGNORECASE | re.UNICODE
)
RE_ARTICLE_INLINE = re.compile(
    r"(?:Điều|Djeu|Dieu)\s+([0-9]+)",
    re.IGNORECASE | re.UNICODE
)
RE_CLAUSE = re.compile(
    r"^(?:Khoản|Khoan)\s+([0-9]+)",
    re.IGNORECASE | re.UNICODE
)
RE_POINT = re.compile(
    r"^(?:Điểm|Diem)\s+([a-zđàáảãạăằắẳẵặâtầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ])",
    re.IGNORECASE | re.UNICODE
)


def load_buoi09_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load và validate cấu hình Buổi 09 từ file .env.
    Lấy mặc định file .env nằm cùng thư mục với hierarchical_rag.py.
    """
    if env_path is None:
        env_path = BASE_DIR / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

    def get_int(key: str, default: int) -> int:
        val = os.getenv(key)
        return int(val) if val is not None and val.strip() != "" else default

    def get_float(key: str, default: float) -> float:
        val = os.getenv(key)
        return float(val) if val is not None and val.strip() != "" else default

    def get_str(key: str, default: str) -> str:
        val = os.getenv(key)
        return val.strip() if val is not None and val.strip() != "" else default

    config = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "GEMINI_EMBEDDING_MODEL": get_str("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"),
        "GEMINI_EMBEDDING_DIM": get_int("GEMINI_EMBEDDING_DIM", 768),
        "GEMINI_GENERATION_MODEL": get_str("GEMINI_GENERATION_MODEL", "gemini-3.5-flash-lite"),
        "RAG_MAX_DISTANCE": get_float("RAG_MAX_DISTANCE", 0.45),
        "BM25_CANDIDATES": get_int("BM25_CANDIDATES", 20),
        "SEMANTIC_CANDIDATES": get_int("SEMANTIC_CANDIDATES", 20),
        "RRF_K": get_int("RRF_K", 60),
        "RRF_BM25_WEIGHT": get_float("RRF_BM25_WEIGHT", 1.0),
        "RRF_SEMANTIC_WEIGHT": get_float("RRF_SEMANTIC_WEIGHT", 1.0),
        "RERANKER_MODEL": get_str("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
        "RERANKER_MAX_LENGTH": get_int("RERANKER_MAX_LENGTH", 512),
        "RERANK_BATCH_SIZE": get_int("RERANK_BATCH_SIZE", 4),
        "RERANK_MIN_SCORE": get_float("RERANK_MIN_SCORE", 0.50),
        "RERANK_DEVICE": get_str("RERANK_DEVICE", "auto"),
        # Multi-Query Expansion Config
        "MULTI_QUERY_COUNT": get_int("MULTI_QUERY_COUNT", 3),
        "MULTI_QUERY_MAX_CHARS": get_int("MULTI_QUERY_MAX_CHARS", 300),
        "MULTI_QUERY_TEMPERATURE": get_float("MULTI_QUERY_TEMPERATURE", 0.2),
        "MULTI_QUERY_ORIGINAL_WEIGHT": get_float("MULTI_QUERY_ORIGINAL_WEIGHT", 1.5),
        "MULTI_QUERY_VARIANT_WEIGHT": get_float("MULTI_QUERY_VARIANT_WEIGHT", 1.0),
        "MULTI_QUERY_RRF_K": get_int("MULTI_QUERY_RRF_K", 60),
        # Parent-Child & Aggregation Config
        "PER_QUERY_CANDIDATES": get_int("PER_QUERY_CANDIDATES", 12),
        "PARENT_MAX_CHARS": get_int("PARENT_MAX_CHARS", 6000),
        "PARENT_SCORE_CHILD_LIMIT": get_int("PARENT_SCORE_CHILD_LIMIT", 3),
        "PARENT_RRF_K": get_int("PARENT_RRF_K", 60),
        "PARENT_CANDIDATES": get_int("PARENT_CANDIDATES", 10),
        "FINAL_PARENT_TOP_K": get_int("FINAL_PARENT_TOP_K", 3),
        "TOTAL_CONTEXT_MAX_CHARS": get_int("TOTAL_CONTEXT_MAX_CHARS", 16000)
    }

    # Validation Rules
    if not (1 <= config["MULTI_QUERY_COUNT"] <= 5):
        raise ValueError(f"MULTI_QUERY_COUNT phải từ 1 đến 5 (hiện tại: {config['MULTI_QUERY_COUNT']})")
    if not (50 <= config["MULTI_QUERY_MAX_CHARS"] <= 1000):
        raise ValueError(f"MULTI_QUERY_MAX_CHARS phải từ 50 đến 1000 (hiện tại: {config['MULTI_QUERY_MAX_CHARS']})")
    if not (0.0 <= config["MULTI_QUERY_TEMPERATURE"] <= 1.0):
        raise ValueError(f"MULTI_QUERY_TEMPERATURE phải từ 0.0 đến 1.0 (hiện tại: {config['MULTI_QUERY_TEMPERATURE']})")
    if config["MULTI_QUERY_ORIGINAL_WEIGHT"] < 0 or config["MULTI_QUERY_VARIANT_WEIGHT"] < 0:
        raise ValueError("Multi-query weights phải là số không âm.")
    if config["MULTI_QUERY_ORIGINAL_WEIGHT"] == 0 and config["MULTI_QUERY_VARIANT_WEIGHT"] == 0:
        raise ValueError("MULTI_QUERY_ORIGINAL_WEIGHT và MULTI_QUERY_VARIANT_WEIGHT không được đồng thời bằng 0.")
    if config["MULTI_QUERY_RRF_K"] <= 0:
        raise ValueError("MULTI_QUERY_RRF_K phải là số nguyên dương.")

    for k in ["PER_QUERY_CANDIDATES", "BM25_CANDIDATES", "SEMANTIC_CANDIDATES", "PARENT_CANDIDATES"]:
        if not (1 <= config[k] <= 100):
            raise ValueError(f"{k} phải từ 1 đến 100 (hiện tại: {config[k]})")

    if not (1000 <= config["PARENT_MAX_CHARS"] <= 20000):
        raise ValueError(f"PARENT_MAX_CHARS phải từ 1000 đến 20000 (hiện tại: {config['PARENT_MAX_CHARS']})")
    if not (1 <= config["PARENT_SCORE_CHILD_LIMIT"] <= 20):
        raise ValueError(f"PARENT_SCORE_CHILD_LIMIT phải từ 1 đến 20 (hiện tại: {config['PARENT_SCORE_CHILD_LIMIT']})")
    if config["FINAL_PARENT_TOP_K"] > config["PARENT_CANDIDATES"]:
        raise ValueError(f"FINAL_PARENT_TOP_K ({config['FINAL_PARENT_TOP_K']}) không được lớn hơn PARENT_CANDIDATES ({config['PARENT_CANDIDATES']})")
    if config["TOTAL_CONTEXT_MAX_CHARS"] < config["PARENT_MAX_CHARS"]:
        raise ValueError(f"TOTAL_CONTEXT_MAX_CHARS ({config['TOTAL_CONTEXT_MAX_CHARS']}) không được nhỏ hơn PARENT_MAX_CHARS ({config['PARENT_MAX_CHARS']})")

    if not config["GEMINI_EMBEDDING_MODEL"] or not config["GEMINI_GENERATION_MODEL"] or not config["RERANKER_MODEL"]:
        raise ValueError("Tên mô hình embedding, generation hoặc reranker không được để rỗng.")

    return config


def parse_chunk_sequence_num(chunk_id: str) -> int:
    """Rút trích phần sequence số ở cuối chunk_id để sắp xếp số học chuẩn."""
    match = re.search(r"(\d+)$", str(chunk_id))
    if match:
        return int(match.group(1))
    return 0


def resolve_child_hierarchy(
    chunks: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Xác định cấu trúc phân cấp Parent-Child deterministic cho danh sách child chunks.
    Ưu tiên: 1. Metadata -> 2. Heading Inferred -> 3. Carry Forward -> 4. Document Fallback.
    """
    seen_ids = set()
    for c in chunks:
        cid = c.get("chunk_id")
        if not cid:
            raise ValueError("Phát hiện chunk thiếu trường 'chunk_id'.")
        if cid in seen_ids:
            raise ValueError(f"Lỗi Duplicate chunk_id: '{cid}' xuất hiện nhiều hơn 1 lần.")
        seen_ids.add(cid)

        pstart = c.get("page_start")
        pend = c.get("page_end")
        txt = c.get("text")
        if txt is None or not str(txt).strip():
            raise ValueError(f"Lỗi invalid chunk text tại chunk_id '{cid}'.")
        if pstart is not None and pend is not None and pstart > pend:
            raise ValueError(f"Lỗi invalid page range (page_start {pstart} > page_end {pend}) tại chunk_id '{cid}'.")

    # Nhóm theo source
    grouped = {}
    for c in chunks:
        src = c.get("source", "UNKNOWN.pdf")
        grouped.setdefault(src, []).append(c)

    resolved_children = []
    resolution_counts = {
        "metadata": 0,
        "heading_inferred": 0,
        "carried_forward": 0,
        "document_fallback": 0
    }

    for src in sorted(grouped.keys()):
        src_chunks = grouped[src]
        # Sắp xếp child theo phần sequence số cuối của chunk_id (numeric sort)
        src_chunks.sort(key=lambda x: parse_chunk_sequence_num(x["chunk_id"]))

        current_chapter: Optional[str] = None
        current_article: Optional[str] = None

        for c in src_chunks:
            cid = c["chunk_id"]
            txt = c["text"]
            st = c.get("structure")
            warnings = []
            ambiguous = False
            resolution_method = "document_fallback"

            chapter_label: Optional[str] = None
            article_label: Optional[str] = None
            clause_label: Optional[str] = None
            point_label: Optional[str] = None

            # 1. Kiểm tra Metadata hợp lệ
            meta_has_art = False
            if st and isinstance(st, dict):
                art_meta = st.get("article")
                chap_meta = st.get("chapter")
                if art_meta:
                    article_label = str(art_meta).strip()
                    meta_has_art = True
                if chap_meta:
                    chapter_label = str(chap_meta).strip()

            # 2. Kiểm tra Heading ở đầu chunk (line đầu tiên)
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            first_line = lines[0] if lines else ""
            second_line = lines[1] if len(lines) > 1 else ""

            heading_chap_match = RE_CHAPTER.search(first_line) or RE_CHAPTER.search(second_line)
            heading_art_match = RE_ARTICLE_HEADING.search(first_line) or RE_ARTICLE_HEADING.search(second_line)

            if heading_chap_match:
                chap_num = heading_chap_match.group(2)
                chap_title = heading_chap_match.group(3).strip()
                inferred_chap = f"Chương {chap_num}" + (f". {chap_title}" if chap_title else "")
                if chapter_label and chapter_label != inferred_chap:
                    ambiguous = True
                    warnings.append(f"Xung đột Chapter metadata ('{chapter_label}') với heading ('{inferred_chap}')")
                chapter_label = inferred_chap

            if heading_art_match:
                art_num = heading_art_match.group(2)
                art_title = heading_art_match.group(3).strip()
                inferred_art = f"Điều {art_num}" + (f". {art_title}" if art_title else "")
                if article_label and article_label != inferred_art:
                    ambiguous = True
                    warnings.append(f"Xung đột Article metadata ('{article_label}') với heading ('{inferred_art}')")
                article_label = inferred_art

            # Quyết định Resolution Method
            if meta_has_art:
                resolution_method = "metadata"
            elif heading_art_match:
                resolution_method = "heading_inferred"
            elif current_article:
                article_label = current_article
                if not chapter_label and current_chapter:
                    chapter_label = current_chapter
                resolution_method = "carried_forward"
            else:
                article_label = "CHUA_XAC_DINH"
                resolution_method = "document_fallback"

            # Cập nhật State cho Carry Forward trong cùng source
            if chapter_label:
                current_chapter = chapter_label
            if article_label and article_label != "CHUA_XAC_DINH":
                current_article = article_label

            # Kiểm tra Khoản / Điểm
            for l in lines[:3]:
                cl_match = RE_CLAUSE.search(l)
                if cl_match:
                    clause_label = f"Khoản {cl_match.group(1)}"
                    break
            for l in lines[:5]:
                pt_match = RE_POINT.search(l)
                if pt_match:
                    point_label = f"Điểm {pt_match.group(1)}"
                    break

            # Kiểm tra nhiều Điều được trích dẫn/sửa đổi trong cùng chunk
            inline_articles = RE_ARTICLE_INLINE.findall(txt)
            if len(set(inline_articles)) > 1:
                ambiguous = True
                warnings.append(f"Chunk chứa {len(set(inline_articles))} Điều được trích dẫn/sửa đổi: {sorted(list(set(inline_articles)))}")

            resolution_counts[resolution_method] += 1

            struct_path = {
                "chapter": chapter_label,
                "article": article_label,
                "clause": clause_label,
                "point": point_label
            }

            resolved_child = {
                "child_id": cid,
                "parent_id": None,  # Sẽ được điền sau khi build parents
                "source": c.get("source", "UNKNOWN.pdf"),
                "page_start": c.get("page_start", 1),
                "page_end": c.get("page_end", 1),
                "text": txt,
                "structural_path": struct_path,
                "resolution_method": resolution_method,
                "ambiguous": ambiguous,
                "warnings": warnings
            }
            resolved_children.append(resolved_child)

    return resolved_children, resolution_counts


def build_parent_documents(
    resolved_children: List[Dict[str, Any]],
    parent_max_chars: int = 6000
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Nhóm resolved children thành các Parent Document blocks theo ranh giới Article.
    Tự động chia window nếu Article block quá dài mà không cắt nát child.
    """
    # Nhóm theo (source, article_key)
    article_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for child in resolved_children:
        src = child["source"]
        art_key = child["structural_path"]["article"] or "CHUA_XAC_DINH"
        article_groups.setdefault((src, art_key), []).append(child)

    parent_documents = []
    updated_children = list(resolved_children)
    child_map = {c["child_id"]: c for c in updated_children}

    for (src, art_key), children in article_groups.items():
        # Phân chia thành các Parent Window blocks nếu vượt PARENT_MAX_CHARS
        windows: List[List[Dict[str, Any]]] = []
        current_window: List[Dict[str, Any]] = []
        current_len = 0

        for child in children:
            child_len = len(child["text"])
            if current_window and (current_len + child_len + 2 > parent_max_chars):
                windows.append(current_window)
                current_window = [child]
                current_len = child_len
            else:
                current_window.append(child)
                current_len += child_len + (2 if current_window else 0)

        if current_window:
            windows.append(current_window)

        for win_idx, win_children in enumerate(windows, start=1):
            # Tạo Parent ID Deterministic từ hash (source + art_key + win_idx)
            raw_id_str = f"{src}::{art_key}::win_{win_idx}"
            parent_hash = hashlib.md5(raw_id_str.encode("utf-8")).hexdigest()[:12]
            sanitized_art = re.sub(r"[^\w]+", "_", art_key).strip("_")
            parent_id = f"{src}_parent_{sanitized_art}_{win_idx}_{parent_hash}"

            parent_text_blocks = []
            page_starts = []
            page_ends = []
            ambiguous_child_count = 0
            parent_warnings = []

            for child in win_children:
                child["parent_id"] = parent_id
                child_map[child["child_id"]]["parent_id"] = parent_id
                parent_text_blocks.append(child["text"])
                page_starts.append(child["page_start"])
                page_ends.append(child["page_end"])
                if child.get("ambiguous", False):
                    ambiguous_child_count += 1
                if len(child["text"]) > parent_max_chars:
                    warn_msg = f"oversized_single_child: Child chunk '{child['child_id']}' độ dài {len(child['text'])} chars vượt giới hạn parent_max_chars ({parent_max_chars})"
                    parent_warnings.append(warn_msg)
                    if warn_msg not in child["warnings"]:
                        child["warnings"].append(warn_msg)

            parent_text = "\n\n".join(parent_text_blocks)

            parent_doc = {
                "parent_id": parent_id,
                "source": src,
                "page_start": min(page_starts) if page_starts else 1,
                "page_end": max(page_ends) if page_ends else 1,
                "article_key": art_key,
                "window_index": win_idx,
                "child_ids": [c["child_id"] for c in win_children],
                "text": parent_text,
                "char_count": len(parent_text),
                "ambiguous_child_count": ambiguous_child_count,
                "warnings": parent_warnings
            }
            parent_documents.append(parent_doc)

    return updated_children, parent_documents


def build_and_save_hierarchy_store(
    input_dir: Optional[Path] = None,
    store_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build toàn bộ Hierarchy Registry và ghi Atomically ra storage/hierarchy/.
    Ghi qua temp file rồi atomic replace, không xóa store cũ khi chưa build xong.
    """
    if config is None:
        config = load_buoi09_config()
    if store_dir is None:
        store_dir = HIERARCHY_STORE_DIR

    store_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Chunks
    if input_dir is None:
        input_dir = rag.DEFAULT_INPUT_DIR
    raw_chunks, combined_stats = rag.load_chunks(input_path=input_dir, strategy="hierarchical")

    # 2. Compute Input File Fingerprints
    input_files_fingerprints = {}
    for fpath in sorted(list(input_dir.glob("chunks_*.json"))):
        fhash = hashlib.sha256(fpath.read_bytes()).hexdigest()
        input_files_fingerprints[fpath.name] = fhash

    # 3. Resolve Hierarchy & Build Parents
    resolved_children, res_counts = resolve_child_hierarchy(raw_chunks)
    updated_children, parent_docs = build_parent_documents(
        resolved_children,
        parent_max_chars=config["PARENT_MAX_CHARS"]
    )

    ambiguous_total = sum(1 for c in updated_children if c["ambiguous"])
    warnings_total = sum(len(c["warnings"]) for c in updated_children) + sum(len(p["warnings"]) for p in parent_docs)

    config_str = json.dumps(config, sort_keys=True)
    config_fingerprint = hashlib.sha256(config_str.encode("utf-8")).hexdigest()[:16]

    manifest = {
        "schema_version": "1.0",
        "build_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "strategy": "hierarchical",
        "config_fingerprint": config_fingerprint,
        "source_fingerprints": input_files_fingerprints,
        "total_children": len(updated_children),
        "total_parents": len(parent_docs),
        "ambiguous_child_count": ambiguous_total,
        "warnings_count": warnings_total,
        "resolution_counts": res_counts
    }

    # 4. Atomic Write (Temp file -> Replace)
    def atomic_write_json(target_path: Path, data: Any):
        temp_path = target_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        os.replace(temp_path, target_path)

    atomic_write_json(store_dir / "children.json", updated_children)
    atomic_write_json(store_dir / "parents.json", parent_docs)
    atomic_write_json(store_dir / "manifest.json", manifest)

    return {
        "manifest": manifest,
        "children": updated_children,
        "parents": parent_docs
    }


def get_hierarchy_status(store_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Read-Only Status Diagnostic cho Hierarchy Registry.
    TUYỆT ĐỐI KHÔNG mkdir, KHÔNG tạo file và KHÔNG sửa timestamp.
    """
    if store_dir is None:
        store_dir = HIERARCHY_STORE_DIR

    children_file = store_dir / "children.json"
    parents_file = store_dir / "parents.json"
    manifest_file = store_dir / "manifest.json"

    exists = children_file.exists() and parents_file.exists() and manifest_file.exists()
    if not exists:
        return {
            "hierarchy_store_exists": False,
            "total_children": 0,
            "total_parents": 0,
            "manifest": None
        }

    try:
        with open(manifest_file, "r", encoding="utf-8") as fp:
            manifest = json.load(fp)
        return {
            "hierarchy_store_exists": True,
            "total_children": manifest.get("total_children", 0),
            "total_parents": manifest.get("total_parents", 0),
            "manifest": manifest
        }
    except Exception as e:
        return {
            "hierarchy_store_exists": False,
            "error": str(e),
            "manifest": None
        }


# ==============================================================================
# CLI HANDLERS
# ==============================================================================

def cli_hierarchy_audit():
    """CLI handler: audit hierarchy in-memory mà không ghi đĩa."""
    print("=" * 60)
    print("BÁO CÁO HIERARCHY AUDIT (READ-ONLY IN-MEMORY)")
    print("=" * 60)
    config = load_buoi09_config()
    raw_chunks, combined_stats = rag.load_chunks(strategy="hierarchical")

    resolved_children, res_counts = resolve_child_hierarchy(raw_chunks)
    updated_children, parent_docs = build_parent_documents(
        resolved_children,
        parent_max_chars=config["PARENT_MAX_CHARS"]
    )

    print(f"Tổng số Child Chunks: {len(updated_children)}")
    print(f"Tổng số Parent Docs : {len(parent_docs)}")
    print("-" * 60)
    print("Phân bẽ Resolution Method:")
    for k, v in res_counts.items():
        print(f"  - {k:20s}: {v:3d} ({v/len(updated_children)*100:.1f}%)")

    ambiguous_list = [c for c in updated_children if c["ambiguous"]]
    print("-" * 60)
    print(f"Số Child Chunks Ambiguous : {len(ambiguous_list)}")
    if ambiguous_list:
        print("Ví dụ Ambiguous Child:")
        ex = ambiguous_list[0]
        print(f"  - Child ID  : {ex['child_id']}")
        print(f"  - Source    : {ex['source']}")
        print(f"  - Warnings  : {ex['warnings']}")

    parent_lens = [p["char_count"] for p in parent_docs]
    parent_lens.sort()
    min_l = parent_lens[0] if parent_lens else 0
    med_l = parent_lens[len(parent_lens)//2] if parent_lens else 0
    max_l = parent_lens[-1] if parent_lens else 0

    print("-" * 60)
    print(f"Phân bẽ kích thước Parent (char count): Min={min_l}, Median={med_l}, Max={max_l}")
    print("=" * 60)


def cli_build_hierarchy():
    """CLI handler: build hierarchy và lưu atomically ra storage/hierarchy/."""
    print("=" * 60)
    print("ĐANG THỰC HIỆN BUILD HIERARCHY STORE ATOMICALLY...")
    print("=" * 60)
    config = load_buoi09_config()
    result = build_and_save_hierarchy_store(config=config)
    m = result["manifest"]
    print(f"Build hoàn tất thành công!")
    print(f"  - Manifest Timestamp : {m['build_timestamp']}")
    print(f"  - Total Children     : {m['total_children']}")
    print(f"  - Total Parents      : {m['total_parents']}")
    print(f"  - Ambiguous Children : {m['ambiguous_child_count']}")
    print(f"  - Total Warnings     : {m['warnings_count']}")
    print("=" * 60)


def cli_hierarchy_status():
    """CLI handler: hiển thị trạng thái Hierarchy Registry Store (Read-Only)."""
    print("=" * 60)
    print("TRẠNG THÁI HIERARCHY REGISTRY STORE (READ-ONLY)")
    print("=" * 60)
    status = get_hierarchy_status()
    print(f"Hierarchy Store Exists : {status['hierarchy_store_exists']}")
    print(f"Total Children         : {status['total_children']}")
    print(f"Total Parents          : {status['total_parents']}")
    if status.get("manifest"):
        m = status["manifest"]
        print(f"Build Timestamp        : {m.get('build_timestamp')}")
        print(f"Ambiguous Child Count  : {m.get('ambiguous_child_count', 0)}")
        print(f"Warnings Count         : {m.get('warnings_count', 0)}")
        print(f"Parent Max Chars       : {m.get('parent_max_chars', 12000)}")
    print("=" * 60)



# ==============================================================================
# MULTI-QUERY EXPANSION ENGINE (BUỔI 09 STEP 04)
# ==============================================================================

_MULTI_QUERY_CACHE: Dict[str, Dict[str, Any]] = {}


def clear_multi_query_cache():
    """Xóa cache trong process."""
    global _MULTI_QUERY_CACHE
    _MULTI_QUERY_CACHE.clear()


def normalize_query_key(text: str) -> str:
    """Chuẩn hóa chuỗi để deduplicate: NFC + casefold + collapse whitespace/punctuation."""
    t = unicodedata.normalize("NFC", str(text)).casefold().strip()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def default_gemini_query_generator(
    prompt: str,
    model_name: str,
    temperature: float,
    config: Dict[str, Any],
    genai_client: Optional[Any] = None
) -> List[Dict[str, str]]:
    """Hàm gọi Gemini API thực tế để sinh danh sách variants."""
    from google import genai
    from google.genai import types

    api_key = config.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY để gọi Gemini Multi-Query Expansion.")

    if genai_client is None:
        genai_client = genai.Client(api_key=api_key)

    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=temperature
    )

    response = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=gen_config
            )
            break
        except Exception as ex:
            err_msg = str(ex)
            if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota" in err_msg) and attempt < max_retries - 1:
                wait_seconds = 15
                try:
                    print(f"[GEMINI RATE LIMIT 429] Sinh Multi-Query gặp 429. Tạm dừng 15s rồi tự động thử lại (Lần thử {attempt + 1}/{max_retries})...")
                except Exception:
                    pass
                time.sleep(wait_seconds)
                continue
            raise ex

    if not response or not response.text:
        raise ValueError("Gemini API trả về phản hồi rỗng.")

    res_json = json.loads(response.text)
    if isinstance(res_json, dict) and "queries" in res_json:
        return res_json["queries"]
    elif isinstance(res_json, list):
        return res_json
    else:
        raise ValueError(f"Phản hồi JSON không đúng cấu trúc mong đợi: {response.text[:200]}")


def generate_multi_queries(
    question: str,
    config: Optional[Dict[str, Any]] = None,
    genai_client: Optional[Any] = None,
    query_generator_fn: Optional[Callable[..., List[Dict[str, str]]]] = None
) -> Dict[str, Any]:
    """
    Sinh tập câu hỏi Multi-Query Expansion (Q0 + Q1..Qn) với kiểm soát chặt chẽ.
    """
    t_start = time.perf_counter()
    if config is None:
        config = load_buoi09_config()

    q0_text = unicodedata.normalize("NFC", question or "").strip()
    if not q0_text:
        raise ValueError("Question không được để rỗng.")

    model_name = config["GEMINI_GENERATION_MODEL"]
    max_count = config["MULTI_QUERY_COUNT"]
    max_chars = config["MULTI_QUERY_MAX_CHARS"]
    temperature = config["MULTI_QUERY_TEMPERATURE"]

    # Xây dựng Q0 object
    q0_obj = {
        "query_id": "Q0",
        "text": q0_text,
        "origin": "original",
        "focus": "original_intent"
    }

    # Kiểm tra Cache trong Process
    cache_key_raw = f"{q0_text}::{model_name}::{temperature}::{max_count}::{max_chars}"
    cache_key = hashlib.sha256(cache_key_raw.encode("utf-8")).hexdigest()

    global _MULTI_QUERY_CACHE
    if cache_key in _MULTI_QUERY_CACHE:
        cached_result = dict(_MULTI_QUERY_CACHE[cache_key])
        cached_result["cache_hit"] = True
        return cached_result

    # Kiểm tra các số hiệu Điều/Khoản trong Q0
    q0_articles = set(RE_ARTICLE_INLINE.findall(q0_text))

    # Xây dựng Prompt tiếng Việt
    prompt = (
        f"Bạn là chuyên gia tra cứu văn bản pháp luật Ngân hàng Nhà nước Việt Nam.\n"
        f"Hãy sinh ra từ 1 đến {max_count} biến thể tìm kiếm cho câu hỏi sau (KHÔNG TRẢ LỜI CÂU HỎI):\n"
        f"Câu hỏi gốc: \"{q0_text}\"\n\n"
        f"Yêu cầu:\n"
        f"1. Mỗi biến thể dưới 200 ký tự, tập trung tìm kiếm chính xác các điều khoản pháp lý liên quan.\n"
        f"2. Bao phủ các khía cạnh: thuật ngữ pháp lý chính xác (exact_legal_terms), diễn đạt tương đương (paraphrase), hoặc khía cạnh còn thiếu (missing_aspect).\n"
        f"3. Nếu câu hỏi có chứa số hiệu Điều/Khoản, phải giữ nguyên ít nhất 1 biến thể có số hiệu đó. Tuyệt đối KHÔNG tự bịa số Điều/Khoản không có trong câu hỏi.\n"
        f"4. Trả về đúng JSON format: {{\"queries\": [{{\"text\": \"...\", \"focus\": \"exact_legal_terms\"}}]}}\n"
    )

    try:
        if query_generator_fn is not None:
            raw_variants = query_generator_fn(prompt, model_name, temperature, config, genai_client)
        else:
            raw_variants = default_gemini_query_generator(prompt, model_name, temperature, config, genai_client)
    except Exception as e:
        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "original_question": q0_text,
            "queries": [q0_obj],
            "model": model_name,
            "generation_latency_ms": latency_ms,
            "status": "query_generation_unavailable",
            "cache_hit": False,
            "dropped_duplicate_count": 0,
            "warnings": [f"Lỗi sinh multi-query: {e}"],
            "error": str(e)
        }

    # Validation & Deduplication
    seen_keys = {normalize_query_key(q0_text)}
    validated_queries = [q0_obj]
    dropped_duplicates = 0
    warnings = []

    for v in raw_variants:
        if len(validated_queries) - 1 >= max_count:
            break

        v_text = ""
        v_focus = "paraphrase"
        if isinstance(v, dict):
            v_text = str(v.get("text", "")).strip()
            v_focus = str(v.get("focus", "paraphrase")).strip()
        elif isinstance(v, str):
            v_text = v.strip()

        v_text = unicodedata.normalize("NFC", v_text)

        if not v_text:
            continue

        if len(v_text) > max_chars:
            v_text = v_text[:max_chars].strip()
            warnings.append(f"Cắt bớt biến thể query vượt quá {max_chars} ký tự.")

        # Deduplication Check
        norm_k = normalize_query_key(v_text)
        if norm_k in seen_keys:
            dropped_duplicates += 1
            continue
        seen_keys.add(norm_k)

        # Kiểm tra nếu bịa số Điều không có trong Q0
        v_articles = set(RE_ARTICLE_INLINE.findall(v_text))
        invented_articles = v_articles - q0_articles
        if invented_articles:
            warnings.append(f"Loại bỏ biến thể bịa số Điều không có trong Q0: {sorted(list(invented_articles))}")
            continue

        validated_queries.append({
            "query_id": f"Q{len(validated_queries)}",
            "text": v_text,
            "origin": "generated",
            "focus": v_focus
        })

    # Đảm bảo gán lại ID deterministic Q0, Q1, Q2...
    for idx, q in enumerate(validated_queries):
        q["query_id"] = f"Q{idx}"

    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    result = {
        "original_question": q0_text,
        "queries": validated_queries,
        "model": model_name,
        "generation_latency_ms": latency_ms,
        "status": "ready",
        "cache_hit": False,
        "dropped_duplicate_count": dropped_duplicates,
        "warnings": warnings
    }

    # Lưu Cache
    _MULTI_QUERY_CACHE[cache_key] = result

    return result


def cli_expand_query(question: str):
    """CLI handler: sinh tập Multi-Query Expansion cho 1 câu hỏi."""
    print("=" * 60)
    print("MULTI-QUERY EXPANSION DIAGNOSTIC")
    print("=" * 60)
    config = load_buoi09_config()
    result = generate_multi_queries(question=question, config=config)

    print(f"Câu hỏi gốc: {result['original_question']}")
    print(f"Trạng thái : {result['status']}")
    print(f"Mô hình    : {result['model']}")
    print(f"Latency    : {result['generation_latency_ms']} ms")
    print(f"Cache Hit  : {result['cache_hit']}")
    print(f"Dropped Dup: {result['dropped_duplicate_count']}")
    print("-" * 60)
    print("Danh sách Query Set sinh ra:")
    for q in result["queries"]:
        print(f"  [{q['query_id']}] ({q['origin']}:{q['focus']}) {q['text']}")

    if result.get("warnings"):
        print("-" * 60)
        print("Cảnh báo (Warnings):")
        for w in result["warnings"]:
            print(f"  - {w}")
    print("=" * 60)


# ==============================================================================
# MULTI-QUERY RETRIEVAL & CROSS-QUERY RRF FUSION (BUỔI 09 STEP 05)
# ==============================================================================

def default_per_query_hybrid_retriever(
    question: str,
    strategy: str = "hierarchical",
    candidate_k: int = 12,
    config: Optional[Dict[str, Any]] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    storage_dir: Optional[Path] = None,
    genai_client: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Gói lệnh gọi search_hybrid của Buổi 08 baseline cho 1 query."""
    if storage_dir is None:
        b08_storage = BASE_DIR.parent / "buoi_08" / "storage" / "chroma"
        if b08_storage.exists():
            storage_dir = b08_storage

    res = advanced_rag.search_hybrid(
        question=question,
        strategy=strategy,
        candidate_k=candidate_k,
        config=config,
        storage_dir=storage_dir,
        genai_client=genai_client
    )
    return res.get("fused_candidates", [])


def search_multi_query_child_hits(
    question: str,
    strategy: str = "hierarchical",
    config: Optional[Dict[str, Any]] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    storage_dir: Optional[Path] = None,
    genai_client: Optional[Any] = None,
    query_generator_fn: Optional[Callable[..., List[Dict[str, str]]]] = None,
    per_query_retriever_fn: Optional[Callable[..., List[Dict[str, Any]]]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Tầng 2: Multi-Query Hybrid Fan-Out Retrieval & Cross-Query RRF Fusion.
    
    1. Sinh tập Multi-Query (Q0 + Q1..Qn)
    2. Fan-out per-query Hybrid Search (Inner RRF)
    3. Hợp nhất Cross-Query RRF Fusion theo công thức RRF 2 tầng
    """
    t_start = time.perf_counter()
    if config is None:
        config = load_buoi09_config()

    # 1. Multi-Query Expansion
    query_set_res = generate_multi_queries(
        question=question,
        config=config,
        genai_client=genai_client,
        query_generator_fn=query_generator_fn
    )

    queries = query_set_res["queries"]
    w_original = config["MULTI_QUERY_ORIGINAL_WEIGHT"]
    w_variant = config["MULTI_QUERY_VARIANT_WEIGHT"]
    mq_rrf_k = config["MULTI_QUERY_RRF_K"]
    per_query_k = config["PER_QUERY_CANDIDATES"]

    # Tra cứu các child hits cho từng query
    per_query_hits: Dict[str, List[Dict[str, Any]]] = {}
    per_query_latency: Dict[str, float] = {}
    per_query_counts: Dict[str, int] = {}
    failed_query_ids: List[str] = []
    query_errors: Dict[str, str] = {}

    retriever_fn = per_query_retriever_fn or default_per_query_hybrid_retriever

    for q_obj in queries:
        qid = q_obj["query_id"]
        qtext = q_obj["text"]
        t_q_start = time.perf_counter()

        try:
            hits = retriever_fn(
                question=qtext,
                strategy=strategy,
                candidate_k=per_query_k,
                config=config,
                chunks=chunks,
                storage_dir=storage_dir,
                genai_client=genai_client
            )
            # Lấy tối đa PER_QUERY_CANDIDATES
            hits = hits[:per_query_k]
            # Đảm bảo gán inner fused_rank nếu chưa có
            for idx, h in enumerate(hits, start=1):
                if "fused_rank" not in h:
                    h["fused_rank"] = idx

            per_query_hits[qid] = hits
            per_query_counts[qid] = len(hits)
            per_query_latency[qid] = round((time.perf_counter() - t_q_start) * 1000, 2)
        except Exception as e:
            per_query_latency[qid] = round((time.perf_counter() - t_q_start) * 1000, 2)
            failed_query_ids.append(qid)
            query_errors[qid] = str(e)
            # Nếu Q0 bị lỗi retrieval -> toàn bộ pipeline fail!
            if qid == "Q0":
                raise RuntimeError(f"Q0 Retrieval Error: Không thể truy vấn cho câu hỏi gốc Q0. Chi tiết: {e}")

    # Xử lý Hợp Nhất Cross-Query RRF
    t_fusion_start = time.perf_counter()
    child_store: Dict[str, Dict[str, Any]] = {}

    for q_obj in queries:
        qid = q_obj["query_id"]
        if qid in failed_query_ids:
            continue

        q_weight = w_original if q_obj["origin"] == "original" else w_variant
        hits = per_query_hits.get(qid, [])

        for h in hits:
            cid = h["chunk_id"]
            inner_rank = h["fused_rank"]

            # RRF Contribution cho query này
            contrib = q_weight / (mq_rrf_k + inner_rank)

            if cid not in child_store:
                child_store[cid] = {
                    "child_id": cid,
                    "text": h["text"],
                    "source": h["source"],
                    "page_start": h.get("page_start", 1),
                    "page_end": h.get("page_end", 1),
                    "multi_query_rrf_score": 0.0,
                    "support_query_count": 0,
                    "support_query_ids": [],
                    "per_query_ranks": {},
                    "per_query_trace": {}
                }
            else:
                # Metadata validation check
                existing = child_store[cid]
                if existing["source"] != h["source"] or existing["text"] != h["text"]:
                    raise ValueError(f"Lỗi Metadata Mismatch giữa các queries cho child_id '{cid}'.")

            record = child_store[cid]
            record["multi_query_rrf_score"] += contrib
            record["support_query_count"] += 1
            record["support_query_ids"].append(qid)
            record["per_query_ranks"][qid] = inner_rank
            record["per_query_trace"][qid] = {
                "bm25_rank": h.get("bm25_rank"),
                "semantic_rank": h.get("semantic_rank"),
                "inner_fused_rank": inner_rank
            }

    # Sắp xếp Candidate hợp nhất theo thứ tự tie-break quy định
    child_candidates = list(child_store.values())

    for c in child_candidates:
        c["support_query_ids"].sort(key=lambda qid: int(qid[1:]) if qid[1:].isdigit() else 0)
        c["best_query_rank"] = min(c["per_query_ranks"].values())

    # Sort tie-break:
    # 1. multi_query_rrf_score (giảm)
    # 2. support_query_count (giảm)
    # 3. best_query_rank (tăng)
    # 4. child_id (tăng)
    child_candidates.sort(
        key=lambda c: (
            -c["multi_query_rrf_score"],
            -c["support_query_count"],
            c["best_query_rank"],
            str(c["child_id"])
        )
    )

    # Gán multi_query_rank từ 1 đến N
    for rank, c in enumerate(child_candidates, start=1):
        c["multi_query_rank"] = rank

    fusion_latency_ms = round((time.perf_counter() - t_fusion_start) * 1000, 2)

    # Thống kê Overlap Distribution
    overlap_dist: Dict[str, int] = {}
    for c in child_candidates:
        sup = c["support_query_count"]
        key = f"hit_by_{sup}"
        overlap_dist[key] = overlap_dist.get(key, 0) + 1

    pipeline_status = "ready"
    if failed_query_ids:
        pipeline_status = "multi_query_partial"

    trace = {
        "requested_query_count": len(queries),
        "executed_query_count": len(queries) - len(failed_query_ids),
        "successful_query_count": len(per_query_hits),
        "failed_query_ids": failed_query_ids,
        "query_errors": query_errors,
        "per_query_latency_ms": per_query_latency,
        "per_query_hit_counts": per_query_counts,
        "union_child_count": len(child_candidates),
        "overlap_distribution": overlap_dist,
        "fusion_latency_ms": fusion_latency_ms,
        "gemini_expansion_call_count": 1 if not query_set_res.get("cache_hit") else 0,
        "status": pipeline_status
    }

    return child_candidates, trace


def cli_multi_child(question: str):
    """CLI handler: thực thi Multi-Query Fan-Out Retrieval và Cross-Query RRF Fusion."""
    print("=" * 60)
    print("MULTI-QUERY FAN-OUT RETRIEVAL DIAGNOSTIC")
    print("=" * 60)
    config = load_buoi09_config()
    child_hits, trace = search_multi_query_child_hits(question=question, config=config)

    print(f"Câu hỏi gốc        : {question}")
    print(f"Trạng thái Pipeline: {trace['status']}")
    print(f"Số Query yêu cầu   : {trace['requested_query_count']}")
    print(f"Số Query thành công: {trace['successful_query_count']}")
    print(f"Tổng Union Children : {trace['union_child_count']}")
    print(f"Overlap Distribution: {trace['overlap_distribution']}")
    print("-" * 60)
    print(f"{'MQ-Rank':<8} | {'Child ID':<35} | {'Sup':<4} | {'Queries':<12} | {'RRF Score':<10}")
    print("-" * 78)
    for c in child_hits[:20]:
        q_str = ",".join(c["support_query_ids"])
        print(f"#{c['multi_query_rank']:<7} | {c['child_id']:<35} | {c['support_query_count']:<4} | {q_str:<12} | {c['multi_query_rrf_score']:.6f}")
    print("=" * 60)


# ==============================================================================
# CHILD-TO-PARENT EXPANSION & AGGREGATION ENGINE (BUỔI 09 STEP 06)
# ==============================================================================

def load_hierarchy_store(store_dir: Optional[Path] = None) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """
    Nạp dữ liệu hierarchy registry từ storage/hierarchy/.
    Trả về: (children_dict, parents_dict, manifest)
    
    Ném lỗi hierarchy_not_ready nếu store không tồn tại hoặc bị lỗi.
    """
    if store_dir is None:
        store_dir = HIERARCHY_STORE_DIR

    children_file = store_dir / "children.json"
    parents_file = store_dir / "parents.json"
    manifest_file = store_dir / "manifest.json"

    if not (children_file.exists() and parents_file.exists() and manifest_file.exists()):
        raise RuntimeError("hierarchy_not_ready: Store hierarchy chưa được khởi tạo hoặc thiếu file. Hãy chạy 'build-hierarchy' trước.")

    try:
        with open(children_file, "r", encoding="utf-8") as fp:
            children_list = json.load(fp)
        with open(parents_file, "r", encoding="utf-8") as fp:
            parents_list = json.load(fp)
        with open(manifest_file, "r", encoding="utf-8") as fp:
            manifest = json.load(fp)
    except Exception as e:
        raise RuntimeError(f"hierarchy_not_ready: Không thể đọc file hierarchy store. Chi tiết: {e}")

    children_dict = {c.get("child_id") or c.get("chunk_id"): c for c in children_list}
    parents_dict = {p["parent_id"]: p for p in parents_list}

    return children_dict, parents_dict, manifest


def search_parent_candidates(
    question: str,
    mode: str = "multi_parent",
    strategy: str = "hierarchical",
    config: Optional[Dict[str, Any]] = None,
    store_dir: Optional[Path] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    storage_dir: Optional[Path] = None,
    genai_client: Optional[Any] = None,
    query_generator_fn: Optional[Callable[..., List[Dict[str, str]]]] = None,
    per_query_retriever_fn: Optional[Callable[..., List[Dict[str, Any]]]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Tầng 3: Retrieve Child Hits -> Aggregate Parent Candidates -> Apply Context Budget.
    
    Mode:
    - single_parent: sinh query set chỉ có Q0 rồi child -> parent
    - multi_parent: Q0 + variants rồi child -> parent
    """
    t_start = time.perf_counter()
    if config is None:
        config = load_buoi09_config()

    # Precondition Check: Hierarchy Store phải tồn tại
    children_dict, parents_dict, manifest = load_hierarchy_store(store_dir=store_dir)

    # Đổi mode nếu mode == 'single_parent'
    if mode == "single_parent":
        def single_q0_generator(prompt, model, temp, cfg, client):
            return []  # Không sinh variant, chỉ dùng Q0
        actual_gen_fn = single_q0_generator
    else:
        actual_gen_fn = query_generator_fn

    # 1. Thực thi Child Retrieval (Multi-Query Fan-Out + Cross-Query RRF)
    child_hits, child_trace = search_multi_query_child_hits(
        question=question,
        strategy=strategy,
        config=config,
        chunks=chunks,
        storage_dir=storage_dir,
        genai_client=genai_client,
        query_generator_fn=actual_gen_fn,
        per_query_retriever_fn=per_query_retriever_fn
    )

    parent_rrf_k = config["PARENT_RRF_K"]
    parent_score_child_limit = config["PARENT_SCORE_CHILD_LIMIT"]
    parent_candidates_limit = config["PARENT_CANDIDATES"]
    total_context_max_chars = config["TOTAL_CONTEXT_MAX_CHARS"]

    # 2. Gom nhóm Child Hits theo parent_id
    parent_groups: Dict[str, List[Dict[str, Any]]] = {}

    for c in child_hits:
        cid = c.get("child_id") or c.get("chunk_id")
        c["child_id"] = cid
        if cid not in children_dict:
            raise KeyError(f"Lỗi Hierarchy Registry: Không tìm thấy child_id '{cid}' trong children registry.")

        child_reg = children_dict[cid]
        pid = child_reg.get("parent_id")
        if not pid or pid not in parents_dict:
            raise KeyError(f"Lỗi Hierarchy Registry: Child '{cid}' không có parent_id hợp lệ hoặc parent '{pid}' không tồn tại.")

        if pid not in parent_groups:
            parent_groups[pid] = []
        parent_groups[pid].append(c)

    # 3. Tính Điểm Parent (Parent Score Aggregation)
    parent_candidates: List[Dict[str, Any]] = []

    for pid, children_in_parent in parent_groups.items():
        parent_doc = parents_dict[pid]

        # Sắp xếp child hits theo multi_query_rank tăng dần (rank 1 là tốt nhất)
        sorted_children = sorted(children_in_parent, key=lambda c: c["multi_query_rank"])

        anchor_child = sorted_children[0]
        anchor_child_id = anchor_child["child_id"]

        # Lấy tối đa PARENT_SCORE_CHILD_LIMIT child tốt nhất để tính parent_rrf_score
        scoring_children = sorted_children[:parent_score_child_limit]
        scoring_child_ids = [c["child_id"] for c in scoring_children]

        parent_rrf_score = sum(
            1.0 / (parent_rrf_k + c["multi_query_rank"])
            for c in scoring_children
        )

        supporting_child_ids = [c["child_id"] for c in sorted_children]

        # Tập hợp tất cả unique query IDs hỗ trợ các child của parent này
        sup_queries_set = set()
        for c in sorted_children:
            sup_queries_set.update(c.get("support_query_ids", []))
        support_query_ids = sorted(list(sup_queries_set), key=lambda qid: int(qid[1:]) if qid[1:].isdigit() else 0)

        best_child_rank = sorted_children[0]["multi_query_rank"]

        cand = {
            "parent_id": pid,
            "source": parent_doc["source"],
            "page_start": parent_doc.get("page_start", 1),
            "page_end": parent_doc.get("page_end", 1),
            "structural_path": parent_doc.get("structural_path", {}),
            "text": parent_doc["text"],
            "parent_rrf_score": parent_rrf_score,
            "parent_rank": 0,
            "anchor_child_id": anchor_child_id,
            "scoring_child_ids": scoring_child_ids,
            "supporting_child_ids": supporting_child_ids,
            "support_query_ids": support_query_ids,
            "support_query_count": len(support_query_ids),
            "best_child_rank": best_child_rank,
            "ambiguous": parent_doc.get("ambiguous", False),
            "warnings": list(parent_doc.get("warnings", [])),
            "child_hits_detail": sorted_children
        }
        parent_candidates.append(cand)

    # Sort parent candidates:
    # 1. parent_rrf_score (giảm)
    # 2. support_query_count (giảm)
    # 3. best_child_rank (tăng)
    # 4. parent_id (tăng)
    parent_candidates.sort(
        key=lambda p: (
            -p["parent_rrf_score"],
            -p["support_query_count"],
            p["best_child_rank"],
            str(p["parent_id"])
        )
    )

    # Giữ PARENT_CANDIDATES candidates tốt nhất trước khi rerank
    parents_before_limit_count = len(parent_candidates)
    parent_candidates = parent_candidates[:parent_candidates_limit]

    for rank, p in enumerate(parent_candidates, start=1):
        p["parent_rank"] = rank

    # 4. Áp dụng Context Budgeting
    selected_parents: List[Dict[str, Any]] = []
    current_chars = 0
    warnings: List[str] = []

    for p in parent_candidates:
        p_len = len(p["text"])

        if current_chars + p_len <= total_context_max_chars:
            selected_parents.append(p)
            current_chars += p_len
        else:
            # Oversized First Parent Exception
            if not selected_parents:
                selected_parents.append(p)
                current_chars += p_len
                warnings.append(
                    f"Parent đầu tiên '{p['parent_id']}' ({p_len} chars) vượt quá TOTAL_CONTEXT_MAX_CHARS ({total_context_max_chars}). "
                    "Giữ nguyên parent đầu tiên và thông báo cảnh báo."
                )
            else:
                # Dừng tích lũy khi chạm budget
                break

    # 5. Xây dựng Trace Metrics
    total_child_chars = sum(len(c["text"]) for c in child_hits)
    total_parent_chars = sum(len(p["text"]) for p in selected_parents)
    expansion_factor = round(total_parent_chars / max(total_child_chars, 1), 2)

    mapping_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    trace = {
        "mode": mode,
        "input_child_count": len(child_hits),
        "unique_parent_count": len(parent_groups),
        "parents_before_candidate_limit": parents_before_limit_count,
        "parent_candidate_count": len(parent_candidates),
        "budget_selected_parent_count": len(selected_parents),
        "total_child_chars": total_child_chars,
        "total_parent_chars": total_parent_chars,
        "context_expansion_factor": expansion_factor,
        "ambiguous_parent_count": sum(1 for p in selected_parents if p["ambiguous"]),
        "warning_count": len(warnings),
        "warnings": warnings,
        "mapping_latency_ms": mapping_latency_ms,
        "child_trace": child_trace
    }

    return selected_parents, trace


def cli_parent_retrieve(mode: str, question: str):
    """CLI handler: thực thi Parent Retrieval ('retrieve child, return parent')."""
    print("=" * 60)
    print("PARENT RETRIEVAL DIAGNOSTIC (RETRIEVE CHILD, RETURN PARENT)")
    print("=" * 60)
    config = load_buoi09_config()
    parents, trace = search_parent_candidates(question=question, mode=mode, config=config)

    print(f"Câu hỏi gốc              : {question}")
    print(f"Mode                     : {trace['mode']}")
    print(f"Input Child Hits Count   : {trace['input_child_count']}")
    print(f"Unique Parent Count      : {trace['unique_parent_count']}")
    print(f"Selected Parents (Budget): {trace['budget_selected_parent_count']}")
    print(f"Total Child Chars        : {trace['total_child_chars']} chars")
    print(f"Total Parent Chars       : {trace['total_parent_chars']} chars")
    print(f"Expansion Factor         : {trace['context_expansion_factor']}x")
    print("-" * 60)
    print("CÂU TRÚC MAPPING TREE (PARENT ──► CHILD ──► QUERIES):")
    print("-" * 60)
    for p in parents:
        print(f"📦 PARENT #{p['parent_rank']} [{p['parent_id']}] (RRF Score: {p['parent_rrf_score']:.6f}, Best Child Rank: #{p['best_child_rank']})")
        print(f"   Source: {p['source']} (Trang {p['page_start']}-{p['page_end']}) | Length: {len(p['text'])} chars")
        print(f"   Scoring Child IDs: {p['scoring_child_ids']}")
        for c in p["child_hits_detail"]:
            q_str = ", ".join(c.get("support_query_ids", []))
            ranks_str = ", ".join([f"{k}:{v}" for k, v in c.get("per_query_ranks", {}).items()])
            print(f"   └── 📄 CHILD [{c['child_id']}] (MQ-Rank #{c['multi_query_rank']}, Score: {c['multi_query_rrf_score']:.6f})")
            print(f"       └── Queries: [{q_str}] | Inner Ranks: [{ranks_str}]")
        print("-" * 60)

    if trace.get("warnings"):
        print("Cảnh báo (Warnings):")
        for w in trace["warnings"]:
            print(f"  - {w}")
        print("=" * 60)


# ==============================================================================
# PARENT RERANKING & ANSWER GENERATION PIPELINE (BUỔI 09 STEP 07)
# ==============================================================================

def rerank_parents(
    question: str,
    parents: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
    reranker_fn: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    Rerank danh sách Parent Candidates bằng Cross-Encoder model.
    Input pair bắt buộc là (original_question Q0, parent_text).
    """
    if config is None:
        config = load_buoi09_config()

    if not parents:
        return []

    parent_candidates_limit = config["PARENT_CANDIDATES"]
    final_top_k = config["FINAL_PARENT_TOP_K"]

    # Giới hạn tối đa PARENT_CANDIDATES trước khi rerank
    parents_to_rerank = parents[:parent_candidates_limit]
    parent_texts = [p["text"] for p in parents_to_rerank]

    try:
        if reranker_fn is not None:
            raw_scores = reranker_fn(question, parent_texts)
        else:
            pairs = [(question.strip(), txt) for txt in parent_texts]
            raw_scores = advanced_rag.default_hf_reranker_fn(
                pairs=pairs,
                model_name=config.get("RERANKER_MODEL", config.get("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")),
                max_length=config.get("RERANKER_MAX_LENGTH", 512),
                batch_size=config.get("RERANK_BATCH_SIZE", 4),
                device_setting=config.get("RERANK_DEVICE", "auto")
            )
    except Exception as e:
        raise RuntimeError(f"reranker_unavailable: Lỗi thực thi Cross-Encoder Reranker. Chi tiết: {e}")

    # Gán điểm Sigmoid và tính rank change
    reranked_parents = []
    for idx, p in enumerate(parents_to_rerank):
        if isinstance(raw_scores, list) and len(raw_scores) > idx:
            item_score = raw_scores[idx]
            if isinstance(item_score, dict):
                score_val = float(item_score.get("rerank_score", item_score.get("score", 0.0)))
                raw_val = float(item_score.get("raw_score", score_val))
            else:
                score_val = float(item_score)
                raw_val = score_val
        else:
            score_val = 0.0
            raw_val = 0.0

        p_copy = dict(p)
        p_copy["parent_rerank_raw_score"] = raw_val
        p_copy["parent_rerank_score"] = score_val
        reranked_parents.append(p_copy)

    # Sort theo:
    # 1. parent_rerank_score (giảm)
    # 2. parent_rank ban đầu (tăng)
    # 3. parent_id (tăng)
    reranked_parents.sort(
        key=lambda p: (
            -p["parent_rerank_score"],
            p["parent_rank"],
            str(p["parent_id"])
        )
    )

    # Đánh lại parent_rerank_rank từ 1 đến N
    for r_rank, p in enumerate(reranked_parents, start=1):
        p["parent_rerank_rank"] = r_rank
        p["parent_rank_change"] = p["parent_rank"] - r_rank

    # Chỉ giữ lại FINAL_PARENT_TOP_K sau rerank
    return reranked_parents[:final_top_k]


def execute_query_pipeline(
    question: str,
    mode: str = "multi_parent",
    strategy: str = "hierarchical",
    config: Optional[Dict[str, Any]] = None,
    store_dir: Optional[Path] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    storage_dir: Optional[Path] = None,
    genai_client: Optional[Any] = None,
    query_generator_fn: Optional[Callable] = None,
    per_query_retriever_fn: Optional[Callable] = None,
    reranker_fn: Optional[Callable] = None,
    answer_generator_fn: Optional[Callable] = None,
    compare_only: bool = False
) -> Dict[str, Any]:
    """
    Pipeline hoàn chỉnh cho Buổi 09 hỗ trợ 4 Modes:
    1. single_flat: Q0 -> Hybrid -> Rerank Child
    2. multi_flat: Q0+Variants -> MQ Hybrid Fan-Out -> MQ-RRF -> Rerank Child bằng Q0
    3. single_parent: Q0 -> Hybrid -> Child-to-Parent -> Parent Agg -> Rerank Parent bằng Q0
    4. multi_parent: Q0+Variants -> MQ Hybrid Fan-Out -> MQ-RRF -> Child-to-Parent -> Parent Agg -> Rerank Parent bằng Q0
    """
    t_start = time.perf_counter()
    if config is None:
        config = load_buoi09_config()

    q0_text = unicodedata.normalize("NFC", question or "").strip()
    if not q0_text:
        raise ValueError("Question không được để rỗng.")

    valid_modes = ["single_flat", "multi_flat", "single_parent", "multi_parent"]
    if mode not in valid_modes:
        raise ValueError(f"Mode '{mode}' không hợp lệ. Phải thuộc: {valid_modes}")

    api_call_counts = {"generation_calls": 0, "embedding_calls": 0}
    stage_latencies_ms = {}
    warnings: List[str] = []
    errors: List[str] = []

    # 1. Multi-Query Expansion (nếu mode là multi_*)
    query_set_res = None
    if mode in ["multi_flat", "multi_parent"]:
        t_gen_start = time.perf_counter()
        query_set_res = generate_multi_queries(
            question=q0_text,
            config=config,
            genai_client=genai_client,
            query_generator_fn=query_generator_fn
        )
        stage_latencies_ms["multi_query_expansion"] = round((time.perf_counter() - t_gen_start) * 1000, 2)
        if not query_set_res.get("cache_hit"):
            api_call_counts["generation_calls"] += 1

        if query_set_res.get("status") == "query_generation_unavailable":
            warnings.append("Multi-query generation không khả thi, tự động fallback về Q0.")
    else:
        query_set_res = {
            "original_question": q0_text,
            "queries": [{
                "query_id": "Q0",
                "text": q0_text,
                "origin": "original",
                "focus": "original_intent"
            }],
            "model": config["GEMINI_GENERATION_MODEL"],
            "generation_latency_ms": 0.0,
            "status": "ready",
            "cache_hit": False,
            "dropped_duplicate_count": 0,
            "warnings": []
        }

    # 2. Retrieval Execution
    t_ret_start = time.perf_counter()
    child_hits = []
    parent_candidates = []

    if mode in ["single_parent", "multi_parent"]:
        try:
            parent_candidates, parent_trace = search_parent_candidates(
                question=q0_text,
                mode=mode,
                strategy=strategy,
                config=config,
                store_dir=store_dir,
                chunks=chunks,
                storage_dir=storage_dir,
                genai_client=genai_client,
                query_generator_fn=query_generator_fn,
                per_query_retriever_fn=per_query_retriever_fn
            )
            child_hits = parent_trace.get("child_trace", {}).get("child_hits", [])
        except Exception as e:
            if "hierarchy_not_ready" in str(e):
                return {
                    "status": "hierarchy_not_ready",
                    "mode": mode,
                    "original_question": q0_text,
                    "error": str(e)
                }
            return {
                "status": "generation_error",
                "mode": mode,
                "original_question": q0_text,
                "error": f"Lỗi Retrieval API: {e}",
                "warnings": warnings + [f"Retrieval không thành công do lỗi API: {e}"]
            }
    else:
        # Flat Modes
        try:
            retriever_fn = per_query_retriever_fn or default_per_query_hybrid_retriever
            if mode == "single_flat":
                hits = retriever_fn(
                    question=q0_text,
                    strategy=strategy,
                    candidate_k=config["PER_QUERY_CANDIDATES"],
                    config=config,
                    chunks=chunks,
                    storage_dir=storage_dir,
                    genai_client=genai_client
                )
                for idx, h in enumerate(hits, start=1):
                    h["multi_query_rank"] = idx
                    h["multi_query_rrf_score"] = float(h.get("fused_score", 1.0 / (60 + idx)))
                    h["support_query_ids"] = ["Q0"]
                    h["support_query_count"] = 1
                    h["per_query_ranks"] = {"Q0": idx}
                child_hits = hits
            else: # multi_flat
                child_hits, _ = search_multi_query_child_hits(
                    question=q0_text,
                    strategy=strategy,
                    config=config,
                    chunks=chunks,
                    storage_dir=storage_dir,
                    genai_client=genai_client,
                    query_generator_fn=query_generator_fn,
                    per_query_retriever_fn=per_query_retriever_fn
                )
        except Exception as e:
            return {
                "status": "generation_error",
                "mode": mode,
                "original_question": q0_text,
                "error": f"Lỗi Retrieval API: {e}",
                "warnings": warnings + [f"Retrieval không thành công do lỗi API: {e}"]
            }

    stage_latencies_ms["retrieval"] = round((time.perf_counter() - t_ret_start) * 1000, 2)

    # 3. Cross-Encoder Reranking
    t_rerank_start = time.perf_counter()
    rerank_min_score = config["RERANK_MIN_SCORE"]
    accepted_evidence = []

    if mode in ["single_parent", "multi_parent"]:
        try:
            reranked_parents = rerank_parents(
                question=q0_text,
                parents=parent_candidates,
                config=config,
                reranker_fn=reranker_fn
            )
            stage_latencies_ms["reranking"] = round((time.perf_counter() - t_rerank_start) * 1000, 2)

            # Gate check cho parent mode
            for p in reranked_parents:
                if p["parent_rerank_score"] >= rerank_min_score:
                    accepted_evidence.append(p)

            parent_candidates = reranked_parents
        except Exception as e:
            return {
                "status": "reranker_unavailable",
                "mode": mode,
                "original_question": q0_text,
                "error": f"Lỗi Reranker: {e}"
            }
    else:
        # Rerank Child Chunks cho Flat Modes
        try:
            if reranker_fn is not None:
                scores = reranker_fn(q0_text, [c["text"] for c in child_hits])
            else:
                scores = advanced_rag.rerank_candidates(
                    question=q0_text,
                    candidates=[{"text": c["text"]} for c in child_hits],
                    config=config
                )
            stage_latencies_ms["reranking"] = round((time.perf_counter() - t_rerank_start) * 1000, 2)

            for idx, c in enumerate(child_hits):
                sc = scores[idx] if idx < len(scores) else 0.0
                c["rerank_score"] = float(sc.get("rerank_score", sc) if isinstance(sc, dict) else sc)
                if c["rerank_score"] >= rerank_min_score:
                    accepted_evidence.append(c)

            child_hits.sort(key=lambda c: -c.get("rerank_score", 0.0))
        except Exception as e:
            return {
                "status": "reranker_unavailable",
                "mode": mode,
                "original_question": q0_text,
                "error": f"Lỗi Reranker: {e}"
            }

    # 4. Evidence Gate Verification
    if not accepted_evidence:
        total_lat_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "status": "insufficient_evidence",
            "mode": mode,
            "original_question": q0_text,
            "query_set": query_set_res,
            "child_hits": child_hits[:config.get("TOP_K", config.get("PER_QUERY_CANDIDATES", 12))],
            "parent_candidates": parent_candidates,
            "accepted_evidence": [],
            "answer": "Không tìm thấy căn cứ pháp lý phù hợp trong tài liệu để trả lời câu hỏi.",
            "citations": [],
            "stage_latencies_ms": stage_latencies_ms,
            "api_call_counts": api_call_counts,
            "total_latency_ms": total_lat_ms,
            "warnings": warnings + ["Không có evidence nào vượt qua ngưỡng RERANK_MIN_SCORE."],
            "errors": errors
        }

    # Nếu chỉ chạy COMPARE CLI -> dừng trước tầng Answer Generation
    if compare_only:
        total_lat_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "status": "ready",
            "mode": mode,
            "original_question": q0_text,
            "query_set": query_set_res,
            "child_hits": child_hits[:config.get("TOP_K", config.get("PER_QUERY_CANDIDATES", 12))],
            "parent_candidates": parent_candidates,
            "accepted_evidence": accepted_evidence,
            "answer": None,
            "citations": [],
            "stage_latencies_ms": stage_latencies_ms,
            "api_call_counts": api_call_counts,
            "total_latency_ms": total_lat_ms,
            "warnings": warnings,
            "errors": errors
        }

    # 5. Citation Building & Answer Generation
    t_ans_start = time.perf_counter()
    citations = []
    context_blocks = []

    for idx, ev in enumerate(accepted_evidence, start=1):
        label = f"[P{idx}]"
        if mode in ["single_parent", "multi_parent"]:
            cit = {
                "citation_label": label,
                "evidence_id": f"P{idx}",
                "parent_id": ev["parent_id"],
                "anchor_child_id": ev["anchor_child_id"],
                "supporting_child_ids": ev["supporting_child_ids"],
                "source": ev["source"],
                "page_start": ev.get("page_start", 1),
                "page_end": ev.get("page_end", 1),
                "structural_path": ev.get("structural_path", {}),
                "parent_rerank_score": ev.get("parent_rerank_score", 0.0),
                "ambiguous": ev.get("ambiguous", False),
                "warnings": ev.get("warnings", [])
            }
            context_blocks.append(f"{label} (Nguồn: {ev['source']}, Trang {ev['page_start']}-{ev['page_end']}):\n{ev['text']}")
        else:
            cit = {
                "citation_label": label,
                "evidence_id": f"P{idx}",
                "child_id": ev.get("child_id", ev.get("chunk_id")),
                "source": ev.get("source", ""),
                "page_start": ev.get("page_start", 1),
                "page_end": ev.get("page_end", 1),
                "rerank_score": ev.get("rerank_score", 0.0),
                "ambiguous": ev.get("ambiguous", False),
                "warnings": ev.get("warnings", [])
            }
            context_blocks.append(f"{label} (Nguồn: {ev['source']}, Trang {ev.get('page_start',1)}):\n{ev['text']}")

        citations.append(cit)

    # Prompt tiếng Việt nghiêm ngặt
    combined_context = "\n\n".join(context_blocks)
    answer_prompt = (
        f"Bạn là trợ lý pháp lý chuyên nghiệp của Ngân hàng Nhà nước Việt Nam.\n"
        f"Hãy trả lời câu hỏi sau đây ĐÚNG và CHỈ DỰA TRÊN các trích dẫn tài liệu pháp lý được cung cấp.\n\n"
        f"CÂU HỎI GỐC: {q0_text}\n\n"
        f"TÀI LIỆU CĂN CỨ:\n{combined_context}\n\n"
        f"YÊU CẦU:\n"
        f"1. Tuyệt đối không tự suy diễn hoặc đưa ra tư vấn pháp lý nằm ngoài văn bản.\n"
        f"2. Mỗi nhận định, câu trả lời phải kèm trích dẫn nhãn tương ứng (ví dụ: [P1], [P2]).\n"
        f"3. Nếu thông tin có điểm mâu thuẫn hoặc chưa rõ ràng, phải ghi rõ giới hạn câu trả lời.\n"
    )

    try:
        if answer_generator_fn is not None:
            answer_text = answer_generator_fn(answer_prompt, config, genai_client)
        else:
            from google import genai
            from google.genai import types
            api_key = config.get("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("Thiếu GEMINI_API_KEY để sinh câu trả lời LLM.")
            if genai_client is None:
                genai_client = genai.Client(api_key=api_key)

            gen_config = types.GenerateContentConfig(temperature=0.2)
            resp = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    resp = genai_client.models.generate_content(
                        model=config["GEMINI_GENERATION_MODEL"],
                        contents=answer_prompt,
                        config=gen_config
                    )
                    break
                except Exception as ex:
                    err_msg = str(ex)
                    if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota" in err_msg) and attempt < max_retries - 1:
                        wait_seconds = 15
                        try:
                            print(f"[GEMINI RATE LIMIT 429] Sinh câu trả lời LLM gặp 429. Tạm dừng 15s rồi tự động thử lại (Lần thử {attempt + 1}/{max_retries})...")
                        except Exception:
                            pass
                        time.sleep(wait_seconds)
                        continue
                    raise ex
            answer_text = resp.text if resp else "Không có phản hồi từ Gemini."
        
        api_call_counts["generation_calls"] += 1
    except Exception as e:
        answer_text = f"Không thể sinh câu trả lời do lỗi LLM API: {e}"
        warnings.append(str(e))

    stage_latencies_ms["answer_generation"] = round((time.perf_counter() - t_ans_start) * 1000, 2)
    total_lat_ms = round((time.perf_counter() - t_start) * 1000, 2)

    return {
        "status": "ready",
        "mode": mode,
        "original_question": q0_text,
        "query_set": query_set_res,
        "child_hits": child_hits[:config.get("TOP_K", config.get("PER_QUERY_CANDIDATES", 12))],
        "parent_candidates": parent_candidates,
        "accepted_evidence": accepted_evidence,
        "answer": answer_text,
        "citations": citations,
        "stage_latencies_ms": stage_latencies_ms,
        "api_call_counts": api_call_counts,
        "total_latency_ms": total_lat_ms,
        "identities": {
            "generation_model": config["GEMINI_GENERATION_MODEL"],
            "embedding_model": config["GEMINI_EMBEDDING_MODEL"],
            "reranker_model": config.get("RERANKER_MODEL", config.get("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")),
            "strategy": strategy
        },
        "warnings": warnings,
        "errors": errors
    }


def compare_pipeline(
    question: str,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Dict[str, Any]]:
    """
    Chạy so sánh 4 modes (single_flat, multi_flat, single_parent, multi_parent).
    TUYỆT ĐỐI KHÔNG gọi answer generation LLM API.
    """
    modes = ["single_flat", "multi_flat", "single_parent", "multi_parent"]
    compare_results = {}
    for m in modes:
        res = execute_query_pipeline(
            question=question,
            mode=m,
            config=config,
            compare_only=True,
            **kwargs
        )
        compare_results[m] = res
    return compare_results


def cli_query(mode: str, question: str):
    """CLI handler: thực thi query hoàn chỉnh sinh câu trả lời cho 1 câu hỏi."""
    print("=" * 60)
    print("MULTI-QUERY PARENT-CHILD QUERY EXECUTION")
    print("=" * 60)
    config = load_buoi09_config()
    res = execute_query_pipeline(question=question, mode=mode, config=config)

    print(f"Câu hỏi gốc   : {res['original_question']}")
    print(f"Mode          : {res['mode']}")
    print(f"Trạng thái    : {res['status']}")
    print(f"Gen API Calls : {res.get('api_call_counts', {}).get('generation_calls')}")
    print(f"Total Latency : {res.get('total_latency_ms')} ms")
    print("-" * 60)

    if res.get("query_set") and res["query_set"].get("queries"):
        print("Danh sách Multi-Query Set:")
        for q in res["query_set"]["queries"]:
            print(f"  [{q['query_id']}] ({q['origin']}:{q['focus']}) {q['text']}")
        print("-" * 60)

    if res.get("accepted_evidence"):
        print(f"Accepted Evidence Count: {len(res['accepted_evidence'])}")
        for idx, ev in enumerate(res["accepted_evidence"], start=1):
            if "parent_id" in ev:
                print(f"  [P{idx}] Parent ID: {ev['parent_id']} (Rerank Score: {ev.get('parent_rerank_score', 0.0):.4f})")
            else:
                print(f"  [P{idx}] Child ID : {ev.get('child_id', ev.get('chunk_id'))} (Rerank Score: {ev.get('rerank_score', 0.0):.4f})")
        print("-" * 60)

    print("CÂU TRẢ LỜI (ANSWER):")
    print(res.get("answer", "Chưa có câu trả lời."))
    print("=" * 60)


def cli_compare(question: str):
    """CLI handler: so sánh kết quả 4 modes retrieval/rerank mà không gọi answer generation."""
    print("=" * 60)
    print("FOUR-MODE COMPARISON DIAGNOSTIC (NO ANSWER GENERATION)")
    print("=" * 60)
    config = load_buoi09_config()
    results = compare_pipeline(question=question, config=config)

    print(f"Câu hỏi gốc: {question}")
    print("-" * 60)
    print(f"{'Mode':<15} | {'Status':<22} | {'Evidence':<8} | {'Latency (ms)':<12}")
    print("-" * 65)
    for m, res in results.items():
        ev_count = len(res.get("accepted_evidence", []))
        print(f"{m:<15} | {res['status']:<22} | {ev_count:<8} | {res.get('total_latency_ms', 0):<12.2f}")
    print("=" * 60)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CLI Engine cho Hierarchical Advanced RAG (Buổi 09)")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")

    subparsers.add_parser("hierarchy-audit", help="Chẩn đoán phân cấp Hierarchy in-memory (Read-Only)")
    subparsers.add_parser("build-hierarchy", help="Xây dựng và lưu trữ Hierarchy Store (Atomic)")
    subparsers.add_parser("hierarchy-status", help="Xem trạng thái Hierarchy Store (Read-Only)")

    expand_parser = subparsers.add_parser("expand-query", help="Sinh biến thể Multi-Query cho câu hỏi")
    expand_parser.add_argument("--question", type=str, required=True, help="Câu hỏi cần sinh biến thể")

    child_parser = subparsers.add_parser("multi-child", help="Truy vấn Multi-Query Fan-Out Child Hits")
    child_parser.add_argument("--question", type=str, required=True, help="Câu hỏi cần truy vấn multi-child")

    parent_parser = subparsers.add_parser("parent-retrieve", help="Truy vấn Parent Candidates từ Child Hits")
    parent_parser.add_argument("--question", type=str, required=True, help="Câu hỏi cần truy vấn parent")
    parent_parser.add_argument("--mode", type=str, choices=["single_parent", "multi_parent"], default="multi_parent", help="Chế độ truy vấn parent")

    query_parser = subparsers.add_parser("query", help="Thực thi luồng RAG query hoàn chỉnh")
    query_parser.add_argument("--question", type=str, required=True, help="Câu hỏi cần giải đáp")
    query_parser.add_argument("--mode", type=str, choices=["single_flat", "multi_flat", "single_parent", "multi_parent"], default="multi_parent", help="Chế độ query")

    compare_parser = subparsers.add_parser("compare", help="So sánh 4 modes retrieval/rerank mà không gọi answer LLM")
    compare_parser.add_argument("--question", type=str, required=True, help="Câu hỏi cần so sánh")

    args = parser.parse_args()

    if args.command == "hierarchy-audit":
        cli_hierarchy_audit()
    elif args.command == "build-hierarchy":
        cli_build_hierarchy()
    elif args.command == "hierarchy-status":
        cli_hierarchy_status()
    elif args.command == "expand-query":
        cli_expand_query(args.question)
    elif args.command == "multi-child":
        cli_multi_child(args.question)
    elif args.command == "parent-retrieve":
        cli_parent_retrieve(args.mode, args.question)
    elif args.command == "query":
        cli_query(args.mode, args.question)
    elif args.command == "compare":
        cli_compare(args.question)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()



