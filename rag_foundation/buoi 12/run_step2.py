import sys
import os
import re
import pandas as pd
from pathlib import Path

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 2: RULE-BASED CANDIDATE EXTRACTION")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
input_file = base_dir / "ner_kb" / "cleaned_documents.csv"
output_file = base_dir / "ner_kb" / "relation_candidates.csv"

if not input_file.exists():
    print(f"[ERROR] Không tìm thấy file {input_file}")
    sys.exit(1)

# 1. Đọc cleaned_documents.csv bằng pandas
df = pd.read_csv(input_file, dtype={'id': str})
print(f"1. Đã đọc {len(df)} văn bản từ {input_file.name}\n")

# Regex nhận diện Số ký hiệu văn bản pháp luật Việt Nam
DOC_REGEX = r'\b\d+(?:/\d{4})?/[A-ZĐÂÊÔƯa-zđâêôư0-9-]+\b'

# Danh sách trigger ưu tiên
triggers_order = [
    ('Căn cứ', [r'\bcăn cứ\b']),
    ('Sửa đổi, bổ sung', [r'\bsửa đổi,\s*bổ sung\b', r'\bsửa đổi\b', r'\bbổ sung\b']),
    ('Bãi bỏ', [r'\bbãi bỏ\b']),
    ('Thay thế', [r'\bthay thế\b']),
    ('Hướng dẫn', [r'\bhướng dẫn\b']),
    ('Quy định tại', [r'\bquy định tại\b']),
    ('Thông tư', [r'\bthông tư\b']),
    ('Nghị định', [r'\bnghị định\b']),
    ('Luật', [r'\bluật\b']),
    ('Quyết định', [r'\bquyết định\b']),
    ('Văn bản hợp nhất', [r'\bvăn bản hợp nhất\b']),
]

candidates = []

print("2. ĐANG TRÍCH XUẤT CANDIDATES...")

for _, row in df.iterrows():
    source_id = str(row['id']).strip()
    source_so = str(row['so_ky_hieu']).strip() if pd.notnull(row['so_ky_hieu']) else ""
    content_text = str(row['content_clean']) if pd.notnull(row['content_clean']) else ""
    
    lines = [line.strip() for line in content_text.splitlines() if line.strip()]
    num_lines = len(lines)
    
    for i, line in enumerate(lines):
        matches = re.findall(DOC_REGEX, line)
        if not matches:
            continue
            
        # Kết hợp dòng trước và dòng sau (nếu có) để ngữ cảnh (evidence) được đầy đủ
        context_parts = []
        if i > 0 and len(lines[i-1]) < 80:
            context_parts.append(lines[i-1])
        context_parts.append(line)
        if i < num_lines - 1 and len(lines[i+1]) < 80:
            context_parts.append(lines[i+1])
            
        full_context = " ".join(context_parts)
        context_lower = full_context.lower()
        
        for match in matches:
            target_so = match.rstrip('.').strip()
            
            # Loại bỏ các chuỗi không phải số ký hiệu chuẩn (phần hậu tố phải chứa chữ cái)
            parts = target_so.split('/')
            if len(parts) < 2 or not re.search(r'[A-ZĐÂÊÔƯa-zđâêôư]', parts[-1]):
                continue
                
            # 5. Loại candidate tự tham chiếu chính văn bản hiện tại
            if source_so and target_so == source_so:
                continue
                
            # Xác định trigger có trong context
            found_trigger = 'Tham chiếu'
            for trig_name, trig_patterns in triggers_order:
                if any(re.search(pat, context_lower) for pat in trig_patterns):
                    found_trigger = trig_name
                    break
            
            # Tạo evidence xoay quanh target_so để đảm bảo target_so luôn có trong evidence
            target_pos = full_context.find(target_so)
            if target_pos != -1:
                start_pos = max(0, target_pos - 120)
                end_pos = min(len(full_context), target_pos + len(target_so) + 120)
                prefix = "..." if start_pos > 0 else ""
                suffix = "..." if end_pos < len(full_context) else ""
                evidence_str = prefix + full_context[start_pos:end_pos] + suffix
            else:
                evidence_str = full_context[:250]
            
            candidates.append({
                'source_id': source_id,
                'source_so_ky_hieu': source_so,
                'target_so_ky_hieu': target_so,
                'trigger': found_trigger,
                'evidence': evidence_str
            })

cand_df = pd.DataFrame(candidates)
print(f"   - Tổng số candidate thu được (trước khi dedup): {len(cand_df)}")

# 6. Loại duplicate candidate
cand_df = cand_df.drop_duplicates(subset=['source_id', 'target_so_ky_hieu', 'trigger', 'evidence'])

# Loại trùng lặp cùng source, target và trigger
cand_df = cand_df.drop_duplicates(subset=['source_id', 'target_so_ky_hieu', 'trigger'])

print(f"   - Tổng số candidate thu được (sau khi dedup): {len(cand_df)}\n")

# 8. Lưu ner_kb/relation_candidates.csv
cand_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"3. ĐÃ LƯU FILE RESULT: {output_file.relative_to(base_dir)}\n")

# 9. In thống kê
print("4. THỐNG KÊ KẾT QUẢ TRÍCH XUẤT CANDIDATE:")
print(f"   - Tổng số candidate duy nhất : {len(cand_df)}")
print("\n   - Số candidate phân theo trigger:")
trigger_counts = cand_df['trigger'].value_counts()
for trig, cnt in trigger_counts.items():
    print(f"     + {trig:<20}: {cnt} candidate(s)")

print("\n5. HIỂN THỊ 10 CANDIDATE MẪU:\n")
sample_df = cand_df.head(10)
for idx, (_, r) in enumerate(sample_df.iterrows(), 1):
    print(f"Mẫu {idx}:")
    print(f"  Source ID        : {r['source_id']}")
    print(f"  Source Số ký hiệu: {r['source_so_ky_hieu']}")
    print(f"  Target Số ký hiệu: {r['target_so_ky_hieu']}")
    print(f"  Trigger          : {r['trigger']}")
    print(f"  Evidence         : {r['evidence']}")
    print("-" * 55)

# 10. Kiểm tra Điều kiện PASS
pass_file_exists = output_file.exists()
pass_no_dups = not cand_df.duplicated(subset=['source_id', 'target_so_ky_hieu', 'trigger']).any()
pass_evidence_not_empty = (cand_df['evidence'].str.strip().str.len() > 0).all()

# Verify target actually appears in evidence
target_in_evidence = True
mismatches_cnt = 0
for _, r in cand_df.iterrows():
    if r['target_so_ky_hieu'] not in r['evidence']:
        target_in_evidence = False
        mismatches_cnt += 1

is_pass = pass_file_exists and pass_no_dups and pass_evidence_not_empty and target_in_evidence

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 2")
print("=" * 60)
print(f"[{'PASS' if pass_file_exists else 'FAIL'}] File relation_candidates.csv tồn tại")
print(f"[{'PASS' if pass_no_dups else 'FAIL'}] Không có duplicate rõ ràng ({len(cand_df)} unique candidates)")
print(f"[{'PASS' if pass_evidence_not_empty else 'FAIL'}] evidence không rỗng (100% valid)")
print(f"[{'PASS' if target_in_evidence else 'FAIL'}] Target thực sự xuất hiện trong evidence ({'100% valid' if target_in_evidence else f'{mismatches_cnt} mismatches'})")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 2: PASS. Đã sẵn sàng cho Bước 3.")
else:
    print("KẾT LUẬN BƯỚC 2: FAIL. Cần kiểm tra lại trích xuất candidate.")
print("=" * 60 + "\n")
