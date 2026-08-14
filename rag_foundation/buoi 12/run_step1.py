import sys
import os
import re
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 1: KIỂM TRA DỮ LIỆU VÀ LÀM SẠCH HTML")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
meta_file = base_dir / "ner_kb" / "metadata.csv"
content_file = base_dir / "ner_kb" / "content.csv"
output_file = base_dir / "ner_kb" / "cleaned_documents.csv"

# 1. Đọc hai file bằng pandas
meta_df = pd.read_csv(meta_file, dtype={'id': str})
content_df = pd.read_csv(content_file, dtype={'id': str})

# 2. Kiểm tra số dòng, số cột
print("1. KÍCH THƯỚC DỮ LIỆU ĐẦU VÀO:")
print(f"   - metadata.csv : {meta_df.shape[0]} dòng, {meta_df.shape[1]} cột")
print(f"   - content.csv  : {content_df.shape[0]} dòng, {content_df.shape[1]} cột\n")

# 3. Kiểm tra duplicate id
meta_dups = meta_df['id'].duplicated().sum()
content_dups = content_df['id'].duplicated().sum()
total_dups = meta_dups + content_dups
print("2. KIỂM TRA DUPLICATE ID:")
print(f"   - Số duplicate ID trong metadata.csv : {meta_dups}")
print(f"   - Số duplicate ID trong content.csv  : {content_dups}\n")

# 4. Kiểm tra ID mismatch giữa hai file
meta_ids = set(meta_df['id'].dropna())
content_ids = set(content_df['id'].dropna())
only_in_meta = meta_ids - content_ids
only_in_content = content_ids - meta_ids
id_mismatch_count = len(only_in_meta) + len(only_in_content)
print("3. KIỂM TRA ID MISMATCH:")
print(f"   - ID chỉ có ở metadata.csv : {len(only_in_meta)} {only_in_meta if only_in_meta else ''}")
print(f"   - ID chỉ có ở content.csv  : {len(only_in_content)} {only_in_content if only_in_content else ''}")
print(f"   - Tổng số ID mismatch      : {id_mismatch_count}\n")

# 5. Ghép dữ liệu theo id
merged_df = pd.merge(meta_df, content_df, on='id', how='inner')
print("4. KẾT QUẢ MERGE DỮ LIỆU:")
print(f"   - Số dòng sau khi merge: {len(merged_df)}\n")

# 6 & 7. Thống kê missing values và các giá trị chưa chuẩn
print("5. THỐNG KÊ MISSING VALUES VÀ GIÁ TRỊ CHƯA CHUẨN TRONG METADATA:")
missing_report = {}
for col in meta_df.columns:
    if col == 'id':
        continue
    null_cnt = merged_df[col].isnull().sum()
    empty_cnt = (merged_df[col].astype(str).str.strip() == '').sum()
    chua_pl_cnt = (merged_df[col].astype(str).str.strip() == 'Chưa phân loại').sum()
    total_unstandard = null_cnt + empty_cnt + chua_pl_cnt
    if total_unstandard > 0:
        missing_report[col] = {
            'NULL': null_cnt,
            'Empty': empty_cnt,
            'Chưa phân loại': chua_pl_cnt,
            'Total': total_unstandard
        }
        print(f"   - Cột '{col}': {null_cnt} NULL, {empty_cnt} Rỗng, {chua_pl_cnt} 'Chưa phân loại'")

if not missing_report:
    print("   - Không có missing value hoặc giá trị chưa chuẩn nào.\n")
else:
    print()

# 8, 9, 10. Làm sạch content_html bằng BeautifulSoup
def clean_html_content(html_str):
    if not isinstance(html_str, str) or not html_str.strip():
        return ""
    
    soup = BeautifulSoup(html_str, "html.parser")
    
    # Loai bo cac the script, style
    for elem in soup(["script", "style"]):
        elem.decompose()
    
    # Lay text nguyen ban tu HTML
    raw_text = soup.get_text(separator="\n")
    
    # Chuan hoa whitespace: thay non-breaking space, strip line, bo qua line rong dư thừa
    lines = []
    for line in raw_text.splitlines():
        cleaned_line = line.replace('\xa0', ' ').strip()
        if cleaned_line:
            lines.append(cleaned_line)
    
    clean_text = "\n".join(lines)
    return clean_text

print("6. THỰC HIỆN LÀM SẠCH CONTENT_HTML...")
merged_df['content_clean'] = merged_df['content_html'].apply(clean_html_content)

# Kiểm tra sự tồn tại của cụm từ pháp lý quan trọng
legal_keywords = ["Căn cứ", "Sửa đổi, bổ sung", "bãi bỏ", "thay thế"]
print("\n   - Kiểm tra các cụm từ pháp lý quan trọng trong content_clean:")
for kw in legal_keywords:
    cnt = merged_df['content_clean'].str.contains(re.escape(kw), case=False, regex=True).sum()
    print(f"     + Cụm '{kw}': xuất hiện trong {cnt}/{len(merged_df)} văn bản")

# 12. Lưu ner_kb/cleaned_documents.csv
merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n7. ĐÃ LƯU FILE KẾT QUẢ: {output_file.relative_to(base_dir)}\n")

# 13. In 2 mẫu content_html và content_clean
print("8. HIỂN THỊ 2 MẪU SO SÁNH (CONTENT_HTML VS CONTENT_CLEAN):\n")

for i in range(min(2, len(merged_df))):
    doc_id = merged_df.iloc[i]['id']
    title = merged_df.iloc[i]['title']
    html_sample = merged_df.iloc[i]['content_html']
    clean_sample = merged_df.iloc[i]['content_clean']
    
    print(f"--- MẪU {i+1} (ID: {doc_id} - {title}) ---")
    print("HTML GỐC (500 ký tự đầu):")
    print(html_sample[:500] + ("..." if len(html_sample) > 500 else ""))
    print("\nCONTENT_CLEAN (500 ký tự đầu):")
    print(clean_sample[:500] + ("..." if len(clean_sample) > 500 else ""))
    print("-" * 50 + "\n")

# 14. Kiểm tra điều kiện PASS
pass_file_exists = output_file.exists()
pass_doc_count = len(merged_df) == len(meta_df)
pass_no_lost_id = id_mismatch_count == 0 and total_dups == 0
pass_not_empty = (merged_df['content_clean'].str.len() > 100).all()

is_pass = pass_file_exists and pass_doc_count and pass_no_lost_id and pass_not_empty

print("=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 1")
print("=" * 60)
print(f"[{'PASS' if pass_file_exists else 'FAIL'}] File cleaned_documents.csv tồn tại")
print(f"[{'PASS' if pass_doc_count else 'FAIL'}] Đủ số document tương ứng đầu vào ({len(merged_df)}/{len(meta_df)})")
print(f"[{'PASS' if pass_no_lost_id else 'FAIL'}] Không mất ID / Không duplicate ID (Mismatch: {id_mismatch_count}, Dups: {total_dups})")
print(f"[{'PASS' if pass_not_empty else 'FAIL'}] content_clean không rỗng bất thường")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 1: PASS. Đã sẵn sàng cho Bước 2.")
else:
    print("KẾT LUẬN BƯỚC 1: FAIL. Cần kiểm tra lại dữ liệu.")
print("=" * 60 + "\n")
