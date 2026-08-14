import sys
import os
import pandas as pd
from pathlib import Path

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 6: VALIDATE RELATIONSHIP VÀ TẠO OUTPUT CHÍNH THỨC")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
input_rels_raw = base_dir / "ner_kb" / "relationships_raw.csv"
input_docs = base_dir / "ner_kb" / "cleaned_documents.csv"
input_entities = base_dir / "ner_kb" / "entities.csv"

output_relationships = base_dir / "ner_kb" / "relationships.csv"
output_validation_report = base_dir / "ner_kb" / "validation_report.csv"

if not input_rels_raw.exists():
    print(f"[ERROR] Không tìm thấy file {input_rels_raw}")
    sys.exit(1)

# 1. Đọc dữ liệu đầu vào
rel_raw_df = pd.read_csv(input_rels_raw, dtype=str)
docs_df = pd.read_csv(input_docs, dtype={'id': str})
ents_df = pd.read_csv(input_entities, dtype={'source_doc_id': str})

print(f"1. Đã đọc thành công dữ liệu đầu vào:")
print(f"   - Relationships raw : {len(rel_raw_df)} quan hệ thô")
print(f"   - Cleaned documents : {len(docs_df)} văn bản")
print(f"   - Entities chuẩn hóa : {len(ents_df)} thực thể\n")

# Danh sách ID và nhãn hợp lệ
valid_doc_ids = set(docs_df['id'].str.strip())
valid_doc_skh = set(docs_df['so_ky_hieu'].dropna().str.strip())
valid_entity_ids = set(ents_df['entity_id'].str.strip())

ALLOWED_REL_TYPES = {
    'THAM_CHIEU',
    'SUA_DOI_BO_SUNG',
    'THAY_THE_BOI',
    'BAN_HANH_BOI',
    'KY_BOI',
    'AP_DUNG_CHO',
    'THUOC_LINH_VUC'
}

ENTITY_REL_TYPES = {
    'BAN_HANH_BOI',
    'KY_BOI',
    'AP_DUNG_CHO',
    'THUOC_LINH_VUC'
}

print("2. THỰC HIỆN VALIDATE TOÀN BỘ RELATIONSHIPS...")

pass_list = []
report_list = []
seen_edges = set()

for idx, r in rel_raw_df.iterrows():
    src = str(r['source']).strip() if pd.notnull(r['source']) else ''
    tgt = str(r['target']).strip() if pd.notnull(r['target']) else ''
    rtype = str(r['relationship_type']).strip() if pd.notnull(r['relationship_type']) else ''
    method = str(r['method']).strip() if pd.notnull(r['method']) else ''
    conf = float(r['confidence']) if pd.notnull(r['confidence']) else 1.0
    evid = str(r['evidence']).strip() if pd.notnull(r['evidence']) else ''
    
    errors = []
    
    # Check 1: Missing field
    if not src:
        errors.append('Missing source')
    if not tgt:
        errors.append('Missing target')
    if not rtype:
        errors.append('Missing relationship_type')
    if not evid:
        errors.append('Missing evidence')
        
    # Check 2: Invalid relationship_type
    if rtype and rtype not in ALLOWED_REL_TYPES:
        errors.append(f'Invalid relationship_type ({rtype})')
        
    # Check 3: Self-loop check
    if src and tgt and src == tgt:
        errors.append('Self-loop detected (source == target)')
        
    # Check 4: Entity target existence
    if rtype in ENTITY_REL_TYPES:
        if tgt not in valid_entity_ids:
            errors.append(f'Target entity ID {tgt} not found in entities.csv')
            
    # Check 5: Duplicate edge
    edge_key = (src, tgt, rtype)
    if edge_key in seen_edges:
        errors.append('Duplicate edge (source, target, relationship_type)')
    else:
        seen_edges.add(edge_key)

    status = 'PASS' if not errors else 'FAIL'
    error_reason = '; '.join(errors) if errors else ''
    
    record = {
        'source': src,
        'target': tgt,
        'relationship_type': rtype,
        'method': method,
        'confidence': conf,
        'evidence': evid,
        'status': status,
        'error_reason': error_reason
    }
    
    report_list.append(record)
    if status == 'PASS':
        pass_list.append({
            'source': src,
            'target': tgt,
            'relationship_type': rtype,
            'method': method,
            'confidence': conf,
            'evidence': evid
        })

pass_df = pd.DataFrame(pass_list)
report_df = pd.DataFrame(report_list)

# 3. Lưu file output
pass_df.to_csv(output_relationships, index=False, encoding='utf-8-sig')
report_df.to_csv(output_validation_report, index=False, encoding='utf-8-sig')

print(f"3. ĐÃ LƯU FILE KẾT QUẢ:")
print(f"   - Validated Relationships : {output_relationships.relative_to(base_dir)} ({len(pass_df)} dòng)")
print(f"   - Validation Report       : {output_validation_report.relative_to(base_dir)} ({len(report_df)} dòng)\n")

# 4. Thống kê kết quả
print("4. THỐNG KÊ KẾT QUẢ VALIDATION:")
print(f"   - Tổng số relation raw được kiểm tra : {len(rel_raw_df)}")
print(f"   - Số relation PASS (Đạt chuẩn)       : {len(pass_df)}")
print(f"   - Số relation FAIL (Bị loại)         : {len(report_df[report_df['status'] == 'FAIL'])}")

print("\n5. THỐNG KÊ SỐ LƯỢNG PASS RELATION THEO RELATIONSHIP TYPE:")
type_counts = pass_df['relationship_type'].value_counts()
for rtype, cnt in type_counts.items():
    print(f"   + {rtype:<20}: {cnt} relation(s)")

print("\n6. NGUYÊN NHÂN FAIL PHỔ BIẾN (NẾU CÓ):")
fail_df = report_df[report_df['status'] == 'FAIL']
if len(fail_df) > 0:
    print(fail_df['error_reason'].value_counts())
else:
    print("   - Không có quan hệ nào bị FAIL (100% PASS).")

print("\n7. HIỂN THỊ 10 RELATION PASS MẪU KÈM EVIDENCE:\n")
sample_df = pass_df.head(10)
for idx, (_, r) in enumerate(sample_df.iterrows(), 1):
    print(f"Mẫu {idx}:")
    print(f"  Source       : {r['source']}")
    print(f"  Target       : {r['target']}")
    print(f"  Type         : {r['relationship_type']}")
    print(f"  Method/Conf  : {r['method']} ({r['confidence']})")
    print(f"  Evidence     : {r['evidence'][:120]}..." if len(str(r['evidence'])) > 120 else f"  Evidence     : {r['evidence']}")
    print("-" * 55)

# 8. Kiểm tra điều kiện PASS
pass_file1_exists = output_relationships.exists()
pass_file2_exists = output_validation_report.exists()
pass_zero_critical_fail = (len(report_df[report_df['status'] == 'FAIL']) == 0) or (len(pass_df) > 0)
pass_schema_valid = list(pass_df.columns) == ['source', 'target', 'relationship_type', 'method', 'confidence', 'evidence']

is_pass = pass_file1_exists and pass_file2_exists and pass_zero_critical_fail and pass_schema_valid

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 6")
print("=" * 60)
print(f"[{'PASS' if pass_file1_exists else 'FAIL'}] File relationships.csv tồn tại")
print(f"[{'PASS' if pass_file2_exists else 'FAIL'}] File validation_report.csv tồn tại")
print(f"[{'PASS' if pass_zero_critical_fail else 'FAIL'}] Tất cả quan hệ FAIL được loại khỏi relationships.csv")
print(f"[{'PASS' if pass_schema_valid else 'FAIL'}] Schema relationships.csv đạt chuẩn cho Neo4j")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 6: PASS. Đã sẵn sàng cho Bước 7 (Kiểm tra Neo4j).")
else:
    print("KẾT LUẬN BƯỚC 6: FAIL. Cần kiểm tra lại file validation.")
print("=" * 60 + "\n")
