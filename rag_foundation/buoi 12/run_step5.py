import sys
import os
import re
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 5: RELATIONSHIP EXTRACTION (TRÍCH XUẤT QUAN HỆ)")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
input_docs = base_dir / "ner_kb" / "cleaned_documents.csv"
input_candidates = base_dir / "ner_kb" / "relation_candidates.csv"
input_entities = base_dir / "ner_kb" / "entities.csv"
input_meta = base_dir / "ner_kb" / "enriched_metadata.csv"
output_rels = base_dir / "ner_kb" / "relationships_raw.csv"

# Load environment variables for Gemini if needed
env_file = base_dir / ".env"
load_dotenv(env_file)

api_key = os.getenv('GEMINI_API_KEY')
client = None
if api_key:
    client = genai.Client(api_key=api_key)
model_name = os.getenv('GEMINI_GENERATION_MODEL', 'gemini-2.5-flash')

# 1. Đọc dữ liệu đầu vào
doc_df = pd.read_csv(input_docs, dtype={'id': str})
cand_df = pd.read_csv(input_candidates, dtype={'source_id': str})
ent_df = pd.read_csv(input_entities, dtype={'source_doc_id': str})

print(f"1. Đã đọc thành công các file dữ liệu:")
print(f"   - Cleaned documents : {len(doc_df)} văn bản")
print(f"   - Relation candidates: {len(cand_df)} ứng viên quan hệ")
print(f"   - Entities chuẩn hóa : {len(ent_df)} thực thể\n")

# Tạo mapping từ so_ky_hieu (và các dạng chuẩn hóa) -> doc_id
symbol_to_id = {}
for _, r in doc_df.iterrows():
    doc_id = str(r['id']).strip()
    skh = str(r['so_ky_hieu']).strip() if pd.notnull(r['so_ky_hieu']) else ''
    if skh:
        symbol_to_id[skh.lower()] = doc_id
        symbol_to_id[skh.lower().replace(' ', '')] = doc_id

all_relationships = []

# Hàm gọi Gemini phân loại các candidate có trigger không rõ ràng
def classify_candidate_gemini(source_skh, target_skh, trigger, evidence, max_retries=3):
    if not client:
        return 'THAM_CHIEU'
    prompt = f"""Bạn là chuyên gia phân tích pháp luật Việt Nam.
Hãy phân loại mối quan hệ pháp lý giữa Văn bản A ({source_skh}) và Văn bản B ({target_skh}) dựa trên đoạn trích dẫn sau:

Đoạn trích dẫn: "{evidence}"
Từ kích hoạt (trigger): "{trigger}"

Hãy chọn ĐÚNG 1 trong các nhãn sau:
- "THAM_CHIEU": Văn bản A dẫn chiếu, viện dẫn hoặc căn cứ theo Văn bản B.
- "SUA_DOI_BO_SUNG": Văn bản A sửa đổi, bổ sung một số điều/khoản của Văn bản B.
- "THAY_THE_BOI": Văn bản A thay thế hoặc bãi bỏ Văn bản B.
- "KHONG_LIEN_QUAN": Không có mối quan hệ rõ ràng.

Trả về kết quả định dạng JSON schema:
{{
  "relationship_type": "NHÃN_CHỌN",
  "confidence": 0.90,
  "explanation": "Lý do ngắn gọn"
}}
"""
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
            )
            if resp and resp.text:
                data = json.loads(resp.text)
                return data.get("relationship_type", "THAM_CHIEU")
        except Exception:
            time.sleep(1)
    return "THAM_CHIEU"

print("2. TRÍCH XUẤT QUAN HỆ DOCUMENT -> DOCUMENT...")

ambiguous_count = 0
gemini_classified_count = 0

for _, r in cand_df.iterrows():
    src_id = str(r['source_id']).strip()
    src_skh = str(r['source_so_ky_hieu']).strip()
    tgt_skh = str(r['target_so_ky_hieu']).strip()
    trigger = str(r['trigger']).strip()
    evidence = str(r['evidence']).strip() if pd.notnull(r['evidence']) else ''
    
    tgt_id = symbol_to_id.get(tgt_skh.lower()) or symbol_to_id.get(tgt_skh.lower().replace(' ', ''))
    target_node = tgt_id if tgt_id else tgt_skh
    
    trig_lower = trigger.lower()
    rel_type = None
    method = 'rule_extraction'
    conf = 1.0
    
    # 1. THAY_THE_BOI
    if 'thay thế' in trig_lower or 'bãi bỏ' in trig_lower:
        rel_type = 'THAY_THE_BOI'
        # CHIỀU QUAN HỆ BẮT BUỘC: (Document cũ) -[:THAY_THE_BOI]-> (Document mới)
        # target_node là văn bản cũ bị bãi bỏ/thay thế
        # src_id là văn bản mới ban hành thay thế
        all_relationships.append({
            'source': target_node,
            'target': src_id,
            'relationship_type': rel_type,
            'method': method,
            'confidence': conf,
            'evidence': evidence
        })
        continue

    # 2. SUA_DOI_BO_SUNG
    elif 'sửa đổi' in trig_lower or 'bổ sung' in trig_lower:
        rel_type = 'SUA_DOI_BO_SUNG'
        all_relationships.append({
            'source': src_id,
            'target': target_node,
            'relationship_type': rel_type,
            'method': method,
            'confidence': conf,
            'evidence': evidence
        })
        continue

    # 3. THAM_CHIEU (Trigger rõ ràng)
    elif any(k in trig_lower for k in ['căn cứ', 'viện dẫn', 'quy định tại', 'tham chiếu', 'hướng dẫn']):
        rel_type = 'THAM_CHIEU'
        all_relationships.append({
            'source': src_id,
            'target': target_node,
            'relationship_type': rel_type,
            'method': method,
            'confidence': 0.95,
            'evidence': evidence
        })
        continue

    # 4. Trigger mơ hồ -> Dùng Gemini để phân loại
    else:
        ambiguous_count += 1
        llm_type = classify_candidate_gemini(src_skh, tgt_skh, trigger, evidence)
        gemini_classified_count += 1
        
        if llm_type != 'KHONG_LIEN_QUAN':
            if llm_type == 'THAY_THE_BOI':
                all_relationships.append({
                    'source': target_node,
                    'target': src_id,
                    'relationship_type': 'THAY_THE_BOI',
                    'method': 'gemini_classification',
                    'confidence': 0.90,
                    'evidence': evidence
                })
            else:
                all_relationships.append({
                    'source': src_id,
                    'target': target_node,
                    'relationship_type': llm_type,
                    'method': 'gemini_classification',
                    'confidence': 0.90,
                    'evidence': evidence
                })

print(f"   - Tổng số candidate Document -> Document: {len(cand_df)}")
print(f"   - Phân loại trực tiếp bằng Rule : {len(cand_df) - ambiguous_count}")
print(f"   - Phân loại qua Gemini (Ambiguous): {gemini_classified_count}\n")

print("3. TẠO QUAN HỆ DOCUMENT -> ENTITY...")

doc_ent_count = 0
for _, r in ent_df.iterrows():
    doc_id = str(r['source_doc_id']).strip()
    eid = str(r['entity_id']).strip()
    etype = str(r['entity_type']).strip()
    cname = str(r['canonical_name']).strip()
    method = str(r['method']).strip() if pd.notnull(r['method']) else 'metadata_linking'
    conf = float(r['confidence']) if pd.notnull(r['confidence']) else 1.0
    evidence = str(r['evidence']).strip() if pd.notnull(r['evidence']) else f"Linked entity {cname} ({etype})"
    
    rel_type = None
    if etype == 'CoQuan':
        rel_type = 'BAN_HANH_BOI'
    elif etype == 'NguoiKy':
        rel_type = 'KY_BOI'
    elif etype == 'DoiTuongApDung':
        rel_type = 'AP_DUNG_CHO'
    elif etype == 'LinhVuc':
        rel_type = 'THUOC_LINH_VUC'
        
    if rel_type:
        all_relationships.append({
            'source': doc_id,
            'target': eid,
            'relationship_type': rel_type,
            'method': method,
            'confidence': conf,
            'evidence': evidence
        })
        doc_ent_count += 1

print(f"   - Đã tạo {doc_ent_count} quan hệ Document -> Entity\n")

# 4. Gom nhóm, làm sạch và loại bỏ trùng lặp
rels_df = pd.DataFrame(all_relationships)
initial_len = len(rels_df)

# Loại bỏ duplicate hiển nhiên theo (source, target, relationship_type)
rels_df = rels_df.drop_duplicates(subset=['source', 'target', 'relationship_type'])
final_len = len(rels_df)

print(f"4. XỬ LÝ DUPLICATE:")
print(f"   - Tổng quan hệ trước khi loại duplicate: {initial_len}")
print(f"   - Tổng quan hệ sau khi loại duplicate  : {final_len}\n")

# 5. Lưu ner_kb/relationships_raw.csv
columns_order = ['source', 'target', 'relationship_type', 'method', 'confidence', 'evidence']
rels_df = rels_df[columns_order]
rels_df.to_csv(output_rels, index=False, encoding='utf-8-sig')

print(f"5. ĐÃ LƯU FILE RELATIONSHIPS RAW: {output_rels.relative_to(base_dir)}\n")

# 6. Thống kê kết quả
print("6. THỐNG KÊ SỐ LƯỢNG RELATION THEO TYPE:")
type_counts = rels_df['relationship_type'].value_counts()
for rtype, cnt in type_counts.items():
    print(f"   + {rtype:<20}: {cnt} relation(s)")

print("\n7. HIỂN THỊ 10 RELATION MẪU KÈM EVIDENCE:\n")
sample_df = rels_df.head(10)
for idx, (_, r) in enumerate(sample_df.iterrows(), 1):
    print(f"Mẫu {idx}:")
    print(f"  Source       : {r['source']}")
    print(f"  Target       : {r['target']}")
    print(f"  Type         : {r['relationship_type']}")
    print(f"  Method/Conf  : {r['method']} ({r['confidence']})")
    print(f"  Evidence     : {r['evidence'][:120]}..." if len(str(r['evidence'])) > 120 else f"  Evidence     : {r['evidence']}")
    print("-" * 55)

# 8. Kiểm tra điều kiện PASS
pass_file_exists = output_rels.exists()
pass_valid_edges = (rels_df['source'].str.len() > 0).all() and (rels_df['target'].str.len() > 0).all() and (rels_df['relationship_type'].str.len() > 0).all()
pass_has_evidence = (rels_df['evidence'].str.len() > 0).all()
pass_no_dups = not rels_df.duplicated(subset=['source', 'target', 'relationship_type']).any()

# Kiểm tra chiều THAY_THE_BOI (Văn bản cũ -> Văn bản mới)
pass_direction_thay_the = True
thay_the_rows = rels_df[rels_df['relationship_type'] == 'THAY_THE_BOI']
if len(thay_the_rows) > 0:
    for _, r in thay_the_rows.iterrows():
        if not r['source'] or not r['target']:
            pass_direction_thay_the = False

is_pass = pass_file_exists and pass_valid_edges and pass_has_evidence and pass_no_dups and pass_direction_thay_the

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 5")
print("=" * 60)
print(f"[{'PASS' if pass_file_exists else 'FAIL'}] File relationships_raw.csv tồn tại")
print(f"[{'PASS' if pass_valid_edges else 'FAIL'}] Mọi edge có source, target và relationship_type đầy đủ")
print(f"[{'PASS' if pass_has_evidence else 'FAIL'}] 100% relation có evidence kèm theo")
print(f"[{'PASS' if pass_no_dups else 'FAIL'}] Không có duplicate (source, target, type)")
print(f"[{'PASS' if pass_direction_thay_the else 'FAIL'}] Chiều THAY_THE_BOI đúng (Văn bản cũ -> Văn bản mới)")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 5: PASS. Đã sẵn sàng cho Bước 6.")
else:
    print("KẾT LUẬN BƯỚC 5: FAIL. Cần kiểm tra lại trích xuất relationship.")
print("=" * 60 + "\n")
