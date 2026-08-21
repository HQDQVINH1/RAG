"""
buoi_17/scripts/internal_lookup.py
----------------------------------
Use Case 1: AI Tra cứu Quy định Nội bộ có Phân quyền (RBAC) + Audit Trail.

Yêu cầu cốt lõi:
- RBAC pre-filtering trước khi tạo context cho LLM.
- LLM chỉ được phép trả lời dựa trên ngữ cảnh đã qua lọc quyền.
- Nếu ngữ cảnh không đủ hoặc không có quyền: Trả câu thông báo chuẩn:
  "Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."
- Nghiêm cấm bịa đặt kiến thức ngoài context hay tự tạo citation giả.
- Tự động ghi vết Audit Log cho mọi request.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from dotenv import load_dotenv

# Path setup
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

# Load .env
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)

from scripts.secure_retrieval_adapter import SecureRetrievalAdapter
from scripts.audit_logger import AuditLogger

FALLBACK_MESSAGE = "Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."

class InternalPolicyLookup:
    def __init__(self, corpus_path: Optional[str] = None, cache_dir: Optional[str] = None):
        self.adapter = SecureRetrievalAdapter(corpus_path=corpus_path, cache_dir=cache_dir)
        self.logger = AuditLogger(log_file_path=PROJECT_ROOT / "outputs" / "audit_log.jsonl")
        
        # Init LLM Client (Gemini GenAI Client fallback to OpenAI)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("HF_TOKEN")
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
        self.genai_client = None
        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[InternalLookup] Google GenAI init warning: {e}")

    def generate_llm_answer(self, question: str, context: str) -> str:
        """
        Gọi LLM để trả lời câu hỏi dựa trên Context đã lọc RBAC.
        """
        system_prompt = (
            "Bạn là trợ lý AI chuyên gia tra cứu quy định và chính sách nội bộ ngân hàng.\n"
            "NGUYÊN TẮC BẮT BUỘC:\n"
            "1. Chỉ sử dụng duy nhất các thông tin có trong phần 'NGỮ CẢNH TÀI LIỆU' dưới đây để trả lời câu hỏi.\n"
            "2. Tuyệt đối KHÔNG sử dụng kiến thức bên ngoài context để tự bù đắp thông tin.\n"
            "3. Mỗi ý trả lời phải dẫn nguồn trích dẫn chính xác theo định dạng trích dẫn có sẵn trong context (ví dụ [41/2016/TT-NHNN | Điều 6...]).\n"
            "4. Tuyệt đối KHÔNG tự bịa đặt câu trích dẫn hoặc thông tin không có trong ngữ cảnh.\n"
            "5. Nếu thông tin trong ngữ cảnh KHÔNG ĐỦ để trả lời câu hỏi một cách đầy đủ và chính xác, "
            f"bạn MUST trả lời duy nhất câu sau: \"{FALLBACK_MESSAGE}\"\n"
        )
        
        user_prompt = f"NGỮ CẢNH TÀI LIỆU:\n{context}\n\nCÂU HỎI:\n{question}\n\nCÂU TRẢ LỜI (kèm trích dẫn):"
        
        if self.genai_client:
            try:
                response = self.genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                return response.text.strip()
            except Exception as e:
                print(f"[InternalLookup] LLM generation error: {e}")
                
        return f"{FALLBACK_MESSAGE}"

    def query(self, question: str, user_role: Union[str, List[str]], top_k: int = 5, user_id_demo: str = "usr_demo_01") -> Dict[str, Any]:
        """
        Thực hiện tra cứu chính sách nội bộ có phân quyền và ghi log Audit Trail.
        """
        roles_list = [user_role] if isinstance(user_role, str) else list(user_role)
        
        # 1. Secure Retrieval (Pre-filtering RBAC)
        retrieved_chunks = self.adapter.retrieve(
            query=question,
            user_roles=roles_list,
            method="hybrid_rerank",
            top_k=top_k
        )
        
        # Calculate denied count for audit logging
        total_corpus_size = len(self.adapter.retriever.corpus_df)
        accessible_count = sum(1 for _, row in self.adapter.retriever.corpus_df.iterrows() 
                              if bool(set(row['allowed_roles_list']).intersection(set(roles_list))))
        denied_count = total_corpus_size - accessible_count
        
        # 2. Process results
        if not retrieved_chunks:
            answer = FALLBACK_MESSAGE
            citations = []
            doc_ids = []
            chunk_ids = []
            status = "DENIED"
        else:
            # Check if any chunk actually contains answer context
            context_str = self.adapter.build_context(retrieved_chunks)
            answer = self.generate_llm_answer(question, context_str)
            
            citations = [c['citation'] for c in retrieved_chunks]
            doc_ids = sorted(list(set([c['document_id'] for c in retrieved_chunks if c.get('document_id')])))
            chunk_ids = [c['chunk_id'] for c in retrieved_chunks]
            
            if FALLBACK_MESSAGE in answer:
                status = "INSUFFICIENT_CONTEXT"
            else:
                status = "SUCCESS"

        # 3. Log Audit Trail Event
        audit_entry = self.logger.log_event(
            user_id_demo=user_id_demo,
            user_role=roles_list,
            action="INTERNAL_LOOKUP",
            query=question,
            retrieval_method="hybrid_rerank",
            retrieved_chunks=retrieved_chunks,
            rbac_denied_candidates_count=denied_count,
            status=status
        )
        
        output_payload = {
            "request_id": audit_entry["request_id"],
            "question": question,
            "user_role": roles_list,
            "access_scope": roles_list,
            "answer": answer,
            "citations": citations if status != "DENIED" and answer != FALLBACK_MESSAGE else [],
            "document_ids": doc_ids if status != "DENIED" and answer != FALLBACK_MESSAGE else [],
            "chunk_ids": chunk_ids if status != "DENIED" and answer != FALLBACK_MESSAGE else [],
            "status": status
        }
        
        return output_payload

if __name__ == "__main__":
    lookup = InternalPolicyLookup()
    res = lookup.query("Quy định về tỷ lệ an toàn vốn", user_role="Risk_Officer")
    print(json.dumps(res, indent=2, ensure_ascii=False))
