"""
buoi_14/scripts/assign_security_tags.py
---------------------------------------
Script phân loại dữ liệu và gán tag phân quyền truy cập (allowed_roles)
cho các đoạn văn bản (chunks) từ chunks_normalized.csv.
Lưu kết quả vào chunks_secure.csv.
"""

import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Input & Output paths
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "chunks_normalized.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "chunks_secure.csv"

# Keyword definitions for classification
HR_KEYWORDS = [
    'nhân sự', 'lương thưởng', 'tuyển dụng', 'bổ nhiệm', 'kỷ luật',
    'bảo hiểm', 'lao động', 'tiền lương', 'bảo hiểm xã hội', 'chế độ'
]

RISK_KEYWORDS = [
    'tín dụng', 'rủi ro', 'hạn mức', 'phê duyệt', 'cho vay',
    'an toàn vốn', 'dự trữ ngoại hối', 'ngoại hối', 'đầu tư gián tiếp',
    'quản lý rủi ro', 'hồ sơ, thủ tục cấp giấy phép'
]

GUEST_KEYWORDS = [
    'nội quy', 'hợp tác xã', 'quản lý tiền mặt', 'quy định chung', 'giao nhận'
]

def classify_chunk(row):
    """
    Phân loại từng chunk dựa trên tiêu đề, số ký hiệu và nội dung văn bản.
    Trả về danh sách allowed_roles dưới dạng JSON string.
    """
    text_content = f"{row.get('title', '')} {row.get('so_ky_hieu', '')} {row.get('text', '')}".lower()
    
    has_hr = any(kw in text_content for kw in HR_KEYWORDS)
    has_risk = any(kw in text_content for kw in RISK_KEYWORDS)
    has_guest = any(kw in text_content for kw in GUEST_KEYWORDS)
    
    if has_hr and not has_risk:
        # Nhóm tài liệu Nhân sự -> Admin và HR_Manager
        roles = ["Admin", "HR_Manager"]
    elif has_risk and not has_hr:
        # Nhóm tài liệu Tín dụng & Rủi ro -> Admin và Risk_Officer
        roles = ["Admin", "Risk_Officer"]
    elif has_hr and has_risk:
        # Tài liệu liên quan cả Nhân sự và Rủi ro -> Admin, HR_Manager, Risk_Officer
        roles = ["Admin", "HR_Manager", "Risk_Officer"]
    elif has_guest:
        # Tài liệu công khai/quy định chung -> Tất cả vai trò kể cả Guest
        roles = ["Admin", "HR_Manager", "Risk_Officer", "Employee", "Guest"]
    else:
        # Quy định nội bộ chung -> Tất cả cán bộ nhân viên ngoại trừ Guest
        roles = ["Admin", "HR_Manager", "Risk_Officer", "Employee"]
        
    return json.dumps(roles, ensure_ascii=False)

def main():
    print(f"Loading normalized dataset from: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
        
    df = pd.read_csv(INPUT_FILE, encoding='utf-8')
    print(f"Loaded {len(df)} chunks.")
    
    # Apply classification
    df['allowed_roles'] = df.apply(classify_chunk, axis=1)
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"Saved secured dataset to: {OUTPUT_FILE}")
    
    # Validation checks
    print("\n--- VALIDATION & STATISTICS ---")
    null_count = df['allowed_roles'].isnull().sum()
    empty_count = (df['allowed_roles'] == '[]').sum()
    print(f"- Null allowed_roles rows: {null_count}")
    print(f"- Empty allowed_roles rows: {empty_count}")
    assert null_count == 0 and empty_count == 0, "Validation failed: Some rows have invalid allowed_roles!"
    
    # Statistical breakdown
    stats = df['allowed_roles'].value_counts()
    print("\n- Statistical distribution of permission groups:")
    for roles_str, count in stats.items():
        roles_list = json.loads(roles_str)
        print(f"  * Roles: {roles_list} -> {count} chunks ({count/len(df)*100:.1f}%)")
        
    # Representative samples
    print("\n- Sample Chunks for Representative Security Levels:")
    categories = [
        ("HR Restricted Level", ["Admin", "HR_Manager"]),
        ("Risk Restricted Level", ["Admin", "Risk_Officer"]),
        ("Internal Employee Level", ["Admin", "HR_Manager", "Risk_Officer", "Employee"])
    ]
    
    for label, target_roles in categories:
        sample = df[df['allowed_roles'] == json.dumps(target_roles, ensure_ascii=False)]
        if not sample.empty:
            first_row = sample.iloc[0]
            print(f"\n  [{label}]")
            print(f"  Chunk ID   : {first_row['chunk_id']}")
            print(f"  Doc ID     : {first_row['document_id']}")
            print(f"  Title      : {first_row['title']}")
            print(f"  Roles Tag  : {first_row['allowed_roles']}")
            print(f"  Snippet    : {str(first_row['text'])[:120]}...")

if __name__ == "__main__":
    main()
