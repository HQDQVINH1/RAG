"""
buoi_17/scripts/audit_logger.py
-------------------------------
Hệ thống Audit Trail tự động ghi vết mọi truy vấn RAG và quyết định phân quyền (RBAC).
Lưu trữ định dạng JSON Lines (.jsonl).
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class AuditLogger:
    def __init__(self, log_file_path: Optional[Union[str, Path]] = None):
        if log_file_path is None:
            script_dir = Path(__file__).resolve().parent
            project_root = script_dir.parent
            log_file_path = project_root / "outputs" / "audit_log.jsonl"
            
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        user_id_demo: str,
        user_role: Union[str, List[str]],
        action: str,
        query: str,
        retrieval_method: str,
        retrieved_chunks: List[Dict[str, Any]],
        rbac_denied_candidates_count: int = 0,
        status: str = "SUCCESS",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ghi lại một sự kiện audit log vào tệp .jsonl
        """
        if request_id is None:
            request_id = f"req-{uuid.uuid4().hex[:8]}"
            
        # Timestamp UTC
        timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # User roles list
        roles_list = [user_role] if isinstance(user_role, str) else list(user_role)
        
        # Extract IDs
        retrieved_doc_ids = sorted(list(set([str(c.get('document_id', '')) for c in retrieved_chunks if c.get('document_id')])))
        retrieved_chunk_ids = [str(c.get('chunk_id', '')) for c in retrieved_chunks if c.get('chunk_id')]
        citation_ids = [str(c.get('citation', '')) for c in retrieved_chunks if c.get('citation')]
        
        # Automatic DENIED state if no chunks accessible and status was SUCCESS
        if not retrieved_chunks and status == "SUCCESS":
            status = "DENIED"
            
        log_entry = {
            "timestamp": timestamp_utc,
            "request_id": request_id,
            "user_id_demo": user_id_demo,
            "user_role": roles_list,
            "action": action,
            "query": query,
            "retrieval_method": retrieval_method,
            "retrieved_document_ids": retrieved_doc_ids,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "citation_ids": citation_ids,
            "rbac_denied_candidates_count": rbac_denied_candidates_count,
            "status": status
        }
        
        # Write to JSONL file
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
        return log_entry
