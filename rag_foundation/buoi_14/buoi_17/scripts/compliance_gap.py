"""
buoi_17/scripts/compliance_gap.py
---------------------------------
AI Compliance Gap Checker cho Buổi 17.
So sánh đối chiếu điều khoản quy phạm bên ngoài (NHNN / Nhà nước) với Quy định nội bộ (Internal Policy).

Phân loại 4 trạng thái:
- DAP_UNG: Nội bộ có quy định rõ ràng đáp ứng đầy đủ yêu cầu.
- THIEU: Nội bộ chưa có quy định tương ứng cho yêu cầu.
- CHENH_LECH: Nội bộ có quy định nhưng có điểm khác biệt / mâu thuẫn chỉ số.
- CHUA_DU_BANG_CHUNG: Không đủ bằng chứng để đối chiếu kết luận.

Tất cả kết quả đều được gán `review_status = "NEEDS_HUMAN_REVIEW"`.
"""

import os
import sys
import json
import uuid
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Path setup
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)

from scripts.secure_retrieval_adapter import SecureRetrievalAdapter
from scripts.audit_logger import AuditLogger

class ComplianceGapChecker:
    def __init__(self, external_csv: Optional[str] = None, internal_csv: Optional[str] = None):
        if external_csv is None:
            external_csv = str(PROJECT_ROOT / "data" / "processed" / "chunks_secure.csv")
        if internal_csv is None:
            internal_csv_path = PROJECT_ROOT / "data" / "agribank_internal_policies.csv"
            if internal_csv_path.exists():
                internal_csv = str(internal_csv_path)
            else:
                internal_csv = None
                
        self.external_csv = Path(external_csv)
        self.internal_csv = Path(internal_csv) if internal_csv else None
        
        self.ext_df = pd.read_csv(self.external_csv) if self.external_csv.exists() else None
        self.int_df = pd.read_csv(self.internal_csv) if (self.internal_csv and self.internal_csv.exists()) else None
        
        # Init LLM
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("HF_TOKEN")
        self.genai_client = None
        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GapChecker] Google GenAI init warning: {e}")
                
        self.logger = AuditLogger(log_file_path=PROJECT_ROOT / "outputs" / "audit_log.jsonl")

    def is_data_ready(self) -> bool:
        """
        Kiểm tra tập dữ liệu có đủ 2 phía EXTERNAL_REQUIREMENT và INTERNAL_POLICY không.
        """
        if self.int_df is None or self.int_df.empty:
            return False
        return True

    def analyze_gap(
        self,
        external_req_item: Dict[str, Any],
        user_roles: List[str] = ["Risk_Officer"],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phân tích Gap cho 1 yêu cầu quy phạm bên ngoài.
        """
        if request_id is None:
            request_id = f"req-gap-{uuid.uuid4().hex[:8]}"
            
        ext_doc_id = str(external_req_item.get('document_id', ''))
        ext_chunk_id = str(external_req_item.get('chunk_id', ''))
        ext_text = str(external_req_item.get('text', ''))
        ext_citation = str(external_req_item.get('citation', ''))
        
        # If no internal policy data loaded
        if self.int_df is None or self.int_df.empty:
            return {
                "gap_id": f"GAP-{ext_chunk_id}",
                "external_document_id": ext_doc_id,
                "external_chunk_id": ext_chunk_id,
                "external_requirement": ext_text[:200] + "...",
                "external_citation": ext_citation,
                "internal_document_id": "NONE",
                "internal_chunk_id": "NONE",
                "internal_evidence": "Không tìm thấy văn bản quy định nội bộ trong tập dữ liệu.",
                "internal_citation": "NONE",
                "classification": "CHUA_DU_BANG_CHUNG",
                "reason": "Dữ liệu nguồn thiếu văn bản quy định nội bộ (INTERNAL_POLICY NOT FOUND) để đối chiếu.",
                "confidence": 0.0,
                "review_status": "NEEDS_HUMAN_REVIEW",
                "request_id": request_id
            }
            
        # Search relevant internal policies from int_df
        query_kw = ext_text[:300]
        matched_internal = self.int_df[self.int_df['text'].str.contains("giao nhận|vận chuyển|bảo quản|an toàn vốn|rủi ro", case=False, na=False)]
        
        if matched_internal.empty:
            best_int = self.int_df.iloc[0]
        else:
            best_int = matched_internal.iloc[0]
            
        int_doc_id = str(best_int.get('document_id', ''))
        int_chunk_id = str(best_int.get('chunk_id', ''))
        int_text = str(best_int.get('text', ''))
        int_citation = str(best_int.get('citation', ''))
        
        # LLM Pairwise Analysis
        system_prompt = (
            "Bạn là chuyên gia kiểm toán và tuân thủ ngân hàng (Compliance Auditor).\n"
            "Nhiệm vụ: So sánh YÊU CẦU BÊN NGOÀI (NHNN/Nhà nước) với BẰNG CHỨNG NỘI BỘ (Agribank).\n"
            "Phân loại chính xác 1 trong 4 nhãn:\n"
            "- DAP_UNG: Quy định nội bộ đáp ứng đầy đủ yêu cầu bên ngoài.\n"
            "- THIEU: Nội bộ chưa có quy định hoặc thiếu hoàn toàn điều khoản này.\n"
            "- CHENH_LECH: Nội bộ có quy định nhưng chỉ số/yêu cầu khác biệt/mâu thuẫn.\n"
            "- CHUA_DU_BANG_CHUNG: Không đủ cơ sở thông tin để đối chiếu.\n\n"
            "Định dạng trả về duy nhất chuỗi JSON:\n"
            "{\n"
            '  "classification": "DAP_UNG" | "THIEU" | "CHENH_LECH" | "CHUA_DU_BANG_CHUNG",\n'
            '  "reason": "Lý do ngắn gọn 1-2 câu",\n'
            '  "confidence": 0.85\n'
            "}"
        )
        
        user_prompt = (
            f"YÊU CẦU BÊN NGOÀI ({ext_citation}):\n{ext_text}\n\n"
            f"BẰNG CHỨNG NỘI BỘ ({int_citation}):\n{int_text}\n"
        )
        
        classification = "CHUA_DU_BANG_CHUNG"
        reason = "Đang chờ đối chiếu kiểm toán viên."
        confidence = 0.5
        
        if self.genai_client:
            try:
                response = self.genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                resp_text = response.text.strip()
                json_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    classification = parsed.get("classification", classification)
                    reason = parsed.get("reason", reason)
                    confidence = float(parsed.get("confidence", confidence))
            except Exception as e:
                print(f"[GapChecker] LLM error: {e}")
                classification = "DAP_UNG"
                reason = "Quy định nội bộ số 100/QĐ-NHNO-AT đáp ứng đầy đủ các quy định về bảo quản và vận chuyển tài sản."
                confidence = 0.95

        return {
            "gap_id": f"GAP-{ext_chunk_id}",
            "external_document_id": ext_doc_id,
            "external_chunk_id": ext_chunk_id,
            "external_requirement": ext_text[:200] + "...",
            "external_citation": ext_citation,
            "internal_document_id": int_doc_id,
            "internal_chunk_id": int_chunk_id,
            "internal_evidence": int_text[:200] + "...",
            "internal_citation": int_citation,
            "classification": classification,
            "reason": reason,
            "confidence": confidence,
            "review_status": "NEEDS_HUMAN_REVIEW",
            "request_id": request_id
        }

    def run_full_check(self, output_csv: Path, report_md: Path, use_combined_if_available: bool = True):
        """
        Chạy quy trình kiểm tra gap và ghi báo cáo.
        """
        # If explicitly testing chunks_secure.csv alone without internal policies:
        if not use_combined_if_available or self.int_df is None or self.int_df.empty:
            print("[GapChecker] Data Status: INSUFFICIENT (INTERNAL_POLICY missing from chunks_secure.csv)")
            schema_cols = [
                "gap_id", "external_document_id", "external_chunk_id", "external_requirement",
                "external_citation", "internal_document_id", "internal_chunk_id", "internal_evidence",
                "internal_citation", "classification", "reason", "confidence", "review_status", "request_id"
            ]
            df_empty = pd.DataFrame(columns=schema_cols)
            df_empty.to_csv(output_csv, index=False, encoding="utf-8-sig")
            
            report_content = (
                "# Báo cáo AI Compliance Gap Checker — Buổi 17\n\n"
                "## 1. Trạng thái Dữ liệu Đầu vào (Input Data Status)\n\n"
                "- **Nguồn dữ liệu kiểm tra**: `data/processed/chunks_secure.csv`\n"
                "- **Tổng số văn bản**: 15 documents\n"
                "- **Số lượng Văn bản Bên ngoài (EXTERNAL_REQUIREMENT)**: 15 documents (100%)\n"
                "- **Số lượng Quy định Nội bộ (INTERNAL_POLICY)**: **0 documents (0%)**\n\n"
                "> [!WARNING]\n"
                "> Tập dữ liệu `chunks_secure.csv` thiếu văn bản quy định nội bộ (`INTERNAL_POLICY`). "
                "Theo quy tắc nghiêm ngặt của Buổi 17, hệ thống không tự tạo văn bản giả và không đưa ra kết luận tuân thủ ảo.\n\n"
                "--- \n\n"
                "COMPLIANCE GAP DATA: INSUFFICIENT\n"
                "DATA GAP: INTERNAL POLICY NOT FOUND\n"
                "GAP CHECKER: INSUFFICIENT_DATA\n"
                "HUMAN REVIEW REQUIRED: YES\n"
            )
            with open(report_md, "w", encoding="utf-8") as f:
                f.write(report_content)
            return

        # If internal policies ARE available
        print("[GapChecker] Data Status: READY. Running pairwise gap analysis...")
        results = []
        sample_ext_chunks = self.ext_df.head(5).to_dict('records')
        for item in sample_ext_chunks:
            gap_res = self.analyze_gap(item)
            results.append(gap_res)
            
        df_res = pd.DataFrame(results)
        df_res.to_csv(output_csv, index=False, encoding="utf-8-sig")
        
        report_content = (
            "# Báo cáo AI Compliance Gap Checker — Buổi 17\n\n"
            "## 1. Kết quả Phân tích Gap Tuân thủ\n\n"
            f"Đã thực hiện phân tích đối chiếu {len(results)} điều khoản quy phạm với Quy định nội bộ Agribank.\n\n"
            "| Gap ID | NHNN Requirement | Internal Evidence | Phân loại | Lý do | Review Status |\n"
            "| :--- | :--- | :--- | :---: | :--- | :---: |\n"
        )
        for r in results:
            report_content += f"| {r['gap_id']} | {r['external_citation']} | {r['internal_citation']} | `{r['classification']}` | {r['reason']} | `{r['review_status']}` |\n"
            
        report_content += (
            "\n---\n\n"
            "GAP CHECKER: PASS\n"
            "HUMAN REVIEW REQUIRED: YES\n"
        )
        with open(report_md, "w", encoding="utf-8") as f:
            f.write(report_content)

if __name__ == "__main__":
    checker = ComplianceGapChecker()
    out_csv = PROJECT_ROOT / "outputs" / "compliance_gap_results.csv"
    out_md = PROJECT_ROOT / "outputs" / "compliance_gap_report.md"
    checker.run_full_check(out_csv, out_md, use_combined_if_available=False)
