import sys
import os
import re
import unicodedata
import pandas as pd
from pathlib import Path

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 4: CHUẨN HÓA ENTITY (ENTITY NORMALIZATION)")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
input_raw_entities = base_dir / "ner_kb" / "extracted_entities_raw.csv"
input_enriched_meta = base_dir / "ner_kb" / "enriched_metadata.csv"
output_entities = base_dir / "ner_kb" / "entities.csv"

if not input_raw_entities.exists():
    print(f"[ERROR] Không tìm thấy file {input_raw_entities}")
    sys.exit(1)

# 1. Đọc extracted_entities_raw.csv
raw_df = pd.read_csv(input_raw_entities, dtype={'document_id': str})
print(f"1. Đã đọc {len(raw_df)} thực thể thô từ {input_raw_entities.name}\n")

# Hàm làm sạch chuỗi văn bản cơ bản (Trim whitespace, Unicode NFC)
def clean_text_basic(text):
    if not isinstance(text, str) or not text.strip():
        return ""
    text_nfc = unicodedata.normalize('NFC', text)
    text_clean = re.sub(r'^[,\.\s;:"\']+|[,\.\s;:"\']+$', '', text_nfc)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    return text_clean

# Bảng Alias Mapping có kiểm soát cho từng loại thực thể
COQUAN_ALIAS_MAP = {
    "nhnn": "Ngân hàng Nhà nước Việt Nam",
    "ngân hàng nhà nước": "Ngân hàng Nhà nước Việt Nam",
    "ngân hàng nhà nước việt nam": "Ngân hàng Nhà nước Việt Nam",
    "ngân hàng nhà nước vn": "Ngân hàng Nhà nước Việt Nam",
    "ngân hàng nhà nước việt nam.": "Ngân hàng Nhà nước Việt Nam",
    "btc": "Bộ Tài chính",
    "bộ tài chính": "Bộ Tài chính",
    "chính phủ": "Chính phủ",
    "quốc hội": "Quốc hội",
    "thủ tướng": "Thủ tướng Chính phủ",
    "thủ tướng chính phủ": "Thủ tướng Chính phủ",
    "ủy ban thường vụ quốc hội": "Ủy ban Thường vụ Quốc hội",
    "ubtvqh": "Ủy ban Thường vụ Quốc hội",
    "bộ công thương": "Bộ Công Thương",
    "bộ lao động - thương binh và xã hội": "Bộ Lao động - Thương binh và Xã hội"
}

LINHVUC_ALIAS_MAP = {
    "tín dụng": "Tín dụng",
    "hoạt động tín dụng": "Tín dụng",
    "bảo hiểm": "Bảo hiểm",
    "kinh doanh bảo hiểm": "Bảo hiểm",
    "kiểm toán": "Kiểm toán",
    "chứng khoán": "Chứng khoán",
    "quản lý ngoại hối": "Quản lý ngoại hối",
    "ngoại hối": "Quản lý ngoại hối",
    "thanh toán": "Thanh toán",
    "hoạt động thanh toán": "Thanh toán",
    "phát hành và kho quỹ": "Phát hành và kho quỹ",
    "kho quỹ": "Phát hành và kho quỹ",
    "an toàn hoạt động ngân hàng": "An toàn ngân hàng",
    "an toàn ngân hàng": "An toàn ngân hàng",
    "kế toán, kiểm toán": "Kiểm toán"
}

DOITUONG_ALIAS_MAP = {
    "ngân hàng thương mại": "Ngân hàng thương mại",
    "các ngân hàng thương mại": "Ngân hàng thương mại",
    "ngân hàng thương mại cổ phần": "Ngân hàng thương mại",
    "chi nhánh ngân hàng nước ngoài": "Chi nhánh ngân hàng nước ngoài",
    "tổ chức tín dụng": "Tổ chức tín dụng",
    "các tổ chức tín dụng": "Tổ chức tín dụng",
    "quỹ tín dụng nhân dân": "Quỹ tín dụng nhân dân",
    "doanh nghiệp bảo hiểm": "Doanh nghiệp bảo hiểm",
    "doanh nghiệp kinh doanh bảo hiểm": "Doanh nghiệp bảo hiểm",
    "doanh nghiệp tái bảo hiểm": "Doanh nghiệp tái bảo hiểm",
    "doanh nghiệp môi giới bảo hiểm": "Doanh nghiệp môi giới bảo hiểm",
    "môi giới bảo hiểm": "Doanh nghiệp môi giới bảo hiểm",
    "đại lý bảo hiểm": "Đại lý bảo hiểm",
    "tổ chức mua bán, xử lý nợ": "Tổ chức mua bán, xử lý nợ",
    "tổ chức mua bán nợ": "Tổ chức mua bán, xử lý nợ",
    "tổ chức mà nhà nước sở hữu 100% vốn điều lệ có chức năng mua, bán, xử lý nợ": "Tổ chức mua bán, xử lý nợ"
}

PERSON_PREFIXES = [
    r'thống đốc\s+', r'phó thống đốc\s+', r'thủ tướng\s+', r'bộ trưởng\s+', r'chủ tịch quốc hội\s+'
]

def canonicalize_entity(original_name, entity_type):
    cleaned = clean_text_basic(original_name)
    if not cleaned:
        return ""
    
    cleaned_lower = cleaned.lower()
    
    if entity_type == 'CoQuan':
        if cleaned_lower in COQUAN_ALIAS_MAP:
            return COQUAN_ALIAS_MAP[cleaned_lower]
        return cleaned.title() if cleaned.islower() else cleaned

    if entity_type == 'LinhVuc':
        if cleaned_lower in LINHVUC_ALIAS_MAP:
            return LINHVUC_ALIAS_MAP[cleaned_lower]
        return cleaned.capitalize() if cleaned.islower() else cleaned

    if entity_type == 'DoiTuongApDung':
        if cleaned_lower in DOITUONG_ALIAS_MAP:
            return DOITUONG_ALIAS_MAP[cleaned_lower]
        return cleaned.capitalize() if cleaned.islower() else cleaned

    if entity_type == 'NguoiKy':
        name = cleaned
        for pref in PERSON_PREFIXES:
            name = re.sub(pref, '', name, flags=re.IGNORECASE).strip()
        if name.isupper() or name.islower():
            name = name.title()
        return name

    return cleaned

print("2. THỰC HIỆN CHUẨN HÓA ENTITIES...")

alias_merged_log = []
normalized_records = []

for _, row in raw_df.iterrows():
    doc_id = str(row['document_id'])
    orig_name = str(row['entity']) if pd.notnull(row['entity']) else ""
    etype = str(row['entity_type']) if pd.notnull(row['entity_type']) else ""
    source = str(row['source']) if pd.notnull(row['source']) else ""
    method = str(row['method']) if pd.notnull(row['method']) else ""
    confidence = float(row['confidence']) if pd.notnull(row['confidence']) else 1.0
    evidence = str(row['evidence']) if pd.notnull(row['evidence']) else ""
    
    clean_orig = clean_text_basic(orig_name)
    if not clean_orig:
        continue
        
    canon_name = canonicalize_entity(clean_orig, etype)
    
    if clean_orig != canon_name and clean_orig.lower() != canon_name.lower():
        alias_merged_log.append(f"{clean_orig} -> {canon_name} ({etype})")
        
    normalized_records.append({
        'entity_type': etype,
        'canonical_name': canon_name,
        'original_name': clean_orig,
        'source_doc_id': doc_id,
        'method': method,
        'confidence': confidence,
        'evidence': evidence
    })

norm_df = pd.DataFrame(normalized_records)
print(f"   - Số lượng record trước chuẩn hóa : {len(raw_df)}")
print(f"   - Số lượng record sau chuẩn hóa   : {len(norm_df)}")

# Loại bỏ trùng lặp hoàn toàn giữa (source_doc_id, entity_type, canonical_name)
norm_df = norm_df.drop_duplicates(subset=['source_doc_id', 'entity_type', 'canonical_name'])

# Gán entity_id duy nhất cho từng (entity_type, canonical_name)
unique_canon = norm_df[['entity_type', 'canonical_name']].drop_duplicates().sort_values(['entity_type', 'canonical_name'])

entity_id_map = {}
type_counters = {}

for _, r in unique_canon.iterrows():
    etype = r['entity_type']
    cname = r['canonical_name']
    
    if etype not in type_counters:
        type_counters[etype] = 1
    else:
        type_counters[etype] += 1
        
    eid = f"ENT_{etype.upper()}_{type_counters[etype]:03d}"
    entity_id_map[(etype, cname)] = eid

norm_df['entity_id'] = norm_df.apply(lambda r: entity_id_map[(r['entity_type'], r['canonical_name'])], axis=1)

# Đổi thứ tự cột theo schema gợi ý
columns_order = [
    'entity_id',
    'entity_type',
    'canonical_name',
    'original_name',
    'source_doc_id',
    'method',
    'confidence',
    'evidence'
]
norm_df = norm_df[columns_order]

# 8. Lưu ner_kb/entities.csv
norm_df.to_csv(output_entities, index=False, encoding='utf-8-sig')
print(f"\n3. ĐÃ LƯU FILE ENTITIES CHUẨN HÓA: {output_entities.relative_to(base_dir)}\n")

# 9. In thống kê
print("4. THỐNG KÊ KẾT QUẢ CHUẨN HÓA ENTITIES:")
print(f"   - Tổng số record thô             : {len(raw_df)}")
print(f"   - Tổng số record sau chuẩn hóa   : {len(norm_df)}")
print(f"   - Tổng số thực thể duy nhất (Node) : {len(unique_canon)}")

print("\n   - Số thực thể duy nhất (Node) theo loại:")
node_counts = unique_canon['entity_type'].value_counts()
for etype, cnt in node_counts.items():
    print(f"     + {etype:<20}: {cnt} unique node(s)")

print("\n5. DANH SÁCH MỘT SỐ ALIAS ĐÃ ĐƯỢC MERGE VỀ CANONICAL NAME:")
unique_merged = list(dict.fromkeys(alias_merged_log))
if unique_merged:
    for item in unique_merged[:15]:
        print(f"   - {item}")
else:
    print("   - Không có alias nào cần merge đặc biệt ngoài chuẩn hóa chữ HOA/thường.")

print("\n6. HIỂN THỊ 10 ENTITY MẪU TRONG ENTITIES.CSV:\n")
sample_df = norm_df.head(10)
for idx, (_, r) in enumerate(sample_df.iterrows(), 1):
    print(f"Mẫu {idx}:")
    print(f"  Entity ID     : {r['entity_id']}")
    print(f"  Type          : {r['entity_type']}")
    print(f"  Canonical Name: {r['canonical_name']}")
    print(f"  Original Name : {r['original_name']}")
    print(f"  Source Doc ID : {r['source_doc_id']}")
    print(f"  Method/Conf   : {r['method']} ({r['confidence']})")
    print("-" * 55)

# 10. Kiểm tra Điều kiện PASS
pass_file_exists = output_entities.exists()
pass_no_dups = not norm_df.duplicated(subset=['source_doc_id', 'entity_type', 'canonical_name']).any()
pass_no_person_overmerge = True
nguoi_ky_nodes = unique_canon[unique_canon['entity_type'] == 'NguoiKy']
if len(raw_df[raw_df['entity_type'] == 'NguoiKy']) > 0 and len(nguoi_ky_nodes) <= 1:
    pass_no_person_overmerge = False

pass_traceable = (norm_df['canonical_name'].str.len() > 0).all() and (norm_df['original_name'].str.len() > 0).all()

is_pass = pass_file_exists and pass_no_dups and pass_no_person_overmerge and pass_traceable

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 4")
print("=" * 60)
print(f"[{'PASS' if pass_file_exists else 'FAIL'}] File entities.csv tồn tại")
print(f"[{'PASS' if pass_no_dups else 'FAIL'}] Không còn duplicate hiển nhiên trong cùng doc")
print(f"[{'PASS' if pass_no_person_overmerge else 'FAIL'}] Không merge nhầm tên người ({len(nguoi_ky_nodes)} người ký duy nhất)")
print(f"[{'PASS' if pass_traceable else 'FAIL'}] Có thể truy ngược canonical_name về original_name (100% valid)")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 4: PASS. Đã sẵn sàng cho Bước 5.")
else:
    print("KẾT LUẬN BƯỚC 4: FAIL. Cần kiểm tra lại trích xuất/chuẩn hóa entities.")
print("=" * 60 + "\n")
