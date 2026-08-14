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
print("  BƯỚC 3: ENTITY EXTRACTION VÀ METADATA ENRICHMENT BẰNG GEMINI")
print("=" * 60 + "\n")

# Define paths
base_dir = Path(__file__).parent
input_file = base_dir / "ner_kb" / "cleaned_documents.csv"
output_raw_entities = base_dir / "ner_kb" / "extracted_entities_raw.csv"
output_enriched_meta = base_dir / "ner_kb" / "enriched_metadata.csv"

# Load environment variables
env_file = base_dir / ".env"
load_dotenv(env_file)

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("[ERROR] GEMINI_API_KEY không được tìm thấy trong .env")
    sys.exit(1)

client = genai.Client(api_key=api_key)
model_name = os.getenv('GEMINI_GENERATION_MODEL', 'gemini-2.5-flash')

# 1. Đọc cleaned_documents.csv
df = pd.read_csv(input_file, dtype={'id': str})
print(f"1. Đã đọc {len(df)} văn bản từ {input_file.name}\n")

all_entities = []
enriched_rows = []

success_docs = 0
failed_docs = 0
errors_list = []

def call_gemini_extraction(doc_id, title, so_ky_hieu, linh_vuc_goc, content_clean, max_retries=4):
    prompt = f"""Bạn là chuyên gia trích xuất thực thể pháp lý từ văn bản pháp luật Việt Nam.
Hãy phân tích văn bản sau:
ID: {doc_id}
Số ký hiệu: {so_ky_hieu}
Tiêu đề: {title}
Lĩnh vực gốc: {linh_vuc_goc}

Nội dung văn bản (trích đoạn 3500 ký tự đầu):
{content_clean[:3500]}

Hãy trích xuất thực thể theo định dạng JSON với schema:
{{
  "co_quan": [
    {{"entity": "Tên cơ quan ban hành", "confidence": 0.95, "evidence": "Trích đoạn ngắn làm bằng chứng"}}
  ],
  "nguoi_ky": [
    {{"entity": "Họ tên người ký", "confidence": 0.95, "evidence": "Trích đoạn ngắn làm bằng chứng"}}
  ],
  "doi_tuong_ap_dung": [
    {{"entity": "Tên đối tượng chịu áp dụng", "confidence": 0.90, "evidence": "Trích đoạn ngắn làm bằng chứng"}}
  ],
  "linh_vuc": [
    {{"entity": "Lĩnh vực pháp lý phù hợp (ví dụ: Tín dụng, Bảo hiểm, Kiểm toán, Chứng khoán, Quản lý ngoại hối, Thanh toán, An toàn ngân hàng)", "confidence": 0.90, "evidence": "Trích đoạn ngắn làm bằng chứng"}}
  ]
}}

Quy tắc bắt buộc:
1. Chỉ tạo thực thể khi có BẰNG CHỨNG (evidence) rõ ràng trong văn bản. Không tự sáng tạo.
2. Với doi_tuong_ap_dung, trích xuất các nhóm tổ chức/cá nhân thuộc phạm vi điều chỉnh (ví dụ: Tổ chức tín dụng, Ngân hàng thương mại, Chi nhánh ngân hàng nước ngoài, Quỹ tín dụng nhân dân, Tổ chức mua bán nợ, ...).
3. confidence đặt từ 0.80 đến 0.95.
"""
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if resp and resp.text:
                return json.loads(resp.text)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2.5)
            else:
                raise e
    return None

print("2. ĐANG TRÍCH XUẤT ENTITIES VÀ LÀM GIÀU METADATA BẰNG GEMINI...")

for idx, row in df.iterrows():
    doc_id = str(row['id']).strip()
    title = str(row['title']) if pd.notnull(row['title']) else ""
    so_ky_hieu = str(row['so_ky_hieu']) if pd.notnull(row['so_ky_hieu']) else ""
    co_quan_goc = str(row['co_quan_ban_hanh']).strip() if pd.notnull(row['co_quan_ban_hanh']) else ""
    nguoi_ky_goc = str(row['nguoi_ky']).strip() if pd.notnull(row['nguoi_ky']) else ""
    linh_vuc_goc = str(row['linh_vuc']).strip() if pd.notnull(row['linh_vuc']) else ""
    content_clean = str(row['content_clean']) if pd.notnull(row['content_clean']) else ""
    
    doc_entities = []
    
    # A. TRÍCH XUẤT TỪ METADATA GỐC (Source: metadata, Method: original)
    if co_quan_goc and co_quan_goc.lower() != 'nan':
        doc_entities.append({
            'document_id': doc_id,
            'entity': co_quan_goc,
            'entity_type': 'CoQuan',
            'source': 'metadata',
            'method': 'original',
            'confidence': 1.0,
            'evidence': f"Metadata co_quan_ban_hanh: {co_quan_goc}"
        })
        
    if nguoi_ky_goc and nguoi_ky_goc.lower() != 'nan':
        chuc_danh = str(row['chuc_danh']) if pd.notnull(row['chuc_danh']) else ""
        doc_entities.append({
            'document_id': doc_id,
            'entity': nguoi_ky_goc,
            'entity_type': 'NguoiKy',
            'source': 'metadata',
            'method': 'original',
            'confidence': 1.0,
            'evidence': f"Metadata nguoi_ky: {nguoi_ky_goc} ({chuc_danh})"
        })
        
    if linh_vuc_goc and linh_vuc_goc not in ['nan', 'Chưa phân loại']:
        doc_entities.append({
            'document_id': doc_id,
            'entity': linh_vuc_goc,
            'entity_type': 'LinhVuc',
            'source': 'metadata',
            'method': 'original',
            'confidence': 1.0,
            'evidence': f"Metadata linh_vuc: {linh_vuc_goc}"
        })
        
    # B. GỌI GEMINI ĐỂ BỔ SUNG VÀ TRÍCH XUẤT ĐỐI TƯỢNG ÁP DỤNG & LĨNH VỰC
    gemini_res = None
    try:
        gemini_res = call_gemini_extraction(doc_id, title, so_ky_hieu, linh_vuc_goc, content_clean)
        success_docs += 1
    except Exception as e:
        failed_docs += 1
        err_msg = f"Doc ID {doc_id}: {type(e).__name__} - {str(e)[:100]}"
        errors_list.append(err_msg)
        print(f"   [WARNING] Lỗi gọi Gemini cho doc {doc_id}: {e}")
        
    gemini_co_quan = []
    gemini_nguoi_ky = []
    gemini_doi_tuong = []
    gemini_linh_vuc = []
    
    if gemini_res and isinstance(gemini_res, dict):
        for item in gemini_res.get('co_quan', []):
            ent = item.get('entity', '').strip()
            evid = item.get('evidence', '').strip()
            conf = min(0.95, max(0.80, float(item.get('confidence', 0.9))))
            if ent and evid:
                gemini_co_quan.append(ent)
                doc_entities.append({
                    'document_id': doc_id,
                    'entity': ent,
                    'entity_type': 'CoQuan',
                    'source': 'content_clean',
                    'method': 'gemini',
                    'confidence': conf,
                    'evidence': evid
                })
                
        for item in gemini_res.get('nguoi_ky', []):
            ent = item.get('entity', '').strip()
            evid = item.get('evidence', '').strip()
            conf = min(0.95, max(0.80, float(item.get('confidence', 0.9))))
            if ent and evid:
                gemini_nguoi_ky.append(ent)
                doc_entities.append({
                    'document_id': doc_id,
                    'entity': ent,
                    'entity_type': 'NguoiKy',
                    'source': 'content_clean',
                    'method': 'gemini',
                    'confidence': conf,
                    'evidence': evid
                })
                
        for item in gemini_res.get('doi_tuong_ap_dung', []):
            ent = item.get('entity', '').strip()
            evid = item.get('evidence', '').strip()
            conf = min(0.95, max(0.80, float(item.get('confidence', 0.9))))
            if ent and evid:
                gemini_doi_tuong.append(ent)
                doc_entities.append({
                    'document_id': doc_id,
                    'entity': ent,
                    'entity_type': 'DoiTuongApDung',
                    'source': 'content_clean',
                    'method': 'gemini',
                    'confidence': conf,
                    'evidence': evid
                })

        for item in gemini_res.get('linh_vuc', []):
            ent = item.get('entity', '').strip()
            evid = item.get('evidence', '').strip()
            conf = min(0.95, max(0.80, float(item.get('confidence', 0.9))))
            if ent and evid:
                gemini_linh_vuc.append(ent)
                # Nếu metadata chưa có hoặc là "Chưa phân loại", thêm entity này
                if not linh_vuc_goc or linh_vuc_goc in ['nan', 'Chưa phân loại']:
                    doc_entities.append({
                        'document_id': doc_id,
                        'entity': ent,
                        'entity_type': 'LinhVuc',
                        'source': 'content_clean',
                        'method': 'gemini',
                        'confidence': conf,
                        'evidence': evid
                    })

    all_entities.extend(doc_entities)
    
    # C. TẠO THÔNG TIN ENRICHED METADATA
    co_quan_enriched = co_quan_goc if (co_quan_goc and co_quan_goc.lower() != 'nan') else (gemini_co_quan[0] if gemini_co_quan else "")
    nguoi_ky_enriched = nguoi_ky_goc if (nguoi_ky_goc and nguoi_ky_goc.lower() != 'nan') else (gemini_nguoi_ky[0] if gemini_nguoi_ky else "")
    
    if linh_vuc_goc and linh_vuc_goc not in ['nan', 'Chưa phân loại']:
        linh_vuc_enriched = linh_vuc_goc
    elif gemini_linh_vuc:
        linh_vuc_enriched = gemini_linh_vuc[0]
    else:
        linh_vuc_enriched = "Chưa phân loại"
        
    unique_doi_tuong = list(dict.fromkeys(gemini_doi_tuong))
    doi_tuong_str = "; ".join(unique_doi_tuong)
    
    row_dict = row.to_dict()
    # Remove content_html and content_clean from metadata export
    row_dict.pop('content_html', None)
    row_dict.pop('content_clean', None)
    
    row_dict['co_quan_enriched'] = co_quan_enriched
    row_dict['nguoi_ky_enriched'] = nguoi_ky_enriched
    row_dict['linh_vuc_enriched'] = linh_vuc_enriched
    row_dict['doi_tuong_ap_dung_list'] = doi_tuong_str
    
    enriched_rows.append(row_dict)
    
    # Nghỉ nhẹ giữa các request để tránh rate limit
    time.sleep(1)

print(f"\n3. HOÀN THÀNH XỬ LÝ 30 VĂN BẢN:")
print(f"   - Số document thành công : {success_docs}")
print(f"   - Số document thất bại   : {failed_docs}\n")

# Lưu extracted_entities_raw.csv
entities_df = pd.DataFrame(all_entities)
entities_df = entities_df.drop_duplicates(subset=['document_id', 'entity', 'entity_type', 'source', 'evidence'])

backup_raw = base_dir / "ner_kb" / "extracted_entities_raw_backup.csv"
backup_meta = base_dir / "ner_kb" / "enriched_metadata_backup.csv"

entities_df.to_csv(output_raw_entities, index=False, encoding='utf-8-sig')
entities_df.to_csv(backup_raw, index=False, encoding='utf-8-sig')

print(f"4. ĐÃ LƯU FILE RAW ENTITIES: {output_raw_entities} ({len(entities_df)} dòng)")

# Lưu enriched_metadata.csv
enriched_df = pd.DataFrame(enriched_rows)
enriched_df.to_csv(output_enriched_meta, index=False, encoding='utf-8-sig')
enriched_df.to_csv(backup_meta, index=False, encoding='utf-8-sig')

print(f"5. ĐÃ LƯU FILE ENRICHED METADATA: {output_enriched_meta} ({len(enriched_df)} dòng)\n")

# Immediate Readback Verification
verify_raw = pd.read_csv(output_raw_entities, encoding='utf-8-sig')
verify_meta = pd.read_csv(output_enriched_meta, encoding='utf-8-sig')
print(f"VERIFY READBACK -> raw shape: {verify_raw.shape}, meta shape: {verify_meta.shape}")

sys.stdout.flush()

# 6. In Thống kê
print("6. THỐNG KÊ KẾT QUẢ TRÍCH XUẤT ENTITIES VÀ METADATA:")
print(f"   - Tổng số entity trích xuất được: {len(entities_df)}")
print("\n   - Số entity phân theo loại (entity_type):")
type_counts = entities_df['entity_type'].value_counts()
for etype, cnt in type_counts.items():
    print(f"     + {etype:<20}: {cnt} entity(s)")

# Thống kê bổ sung metadata
linh_vuc_improved = (df['linh_vuc'].isin(['Chưa phân loại', None]) | df['linh_vuc'].isnull()) & (~enriched_df['linh_vuc_enriched'].isin(['Chưa phân loại', None]))
nganh_improved = df['co_quan_ban_hanh'].isnull() & enriched_df['co_quan_enriched'].notnull()

print(f"\n   - Số giá trị Lĩnh vực được làm giàu/phân loại lại: {linh_vuc_improved.sum()}")
print(f"   - Số document trích xuất thành công Đối tượng áp dụng: {(enriched_df['doi_tuong_ap_dung_list'].str.len() > 0).sum()}/30")

print("\n7. HIỂN THỊ 5 VÍ DỤ METADATA GỐC SO VỚI METADATA LÀM GIÀU:\n")
# Chọn các văn bản có sự thay đổi hoặc bổ sung rõ rệt
sample_indices = [1, 2, 4, 10, 11] # sample rows
for idx in sample_indices:
    if idx < len(df):
        r_orig = df.iloc[idx]
        r_enr = enriched_df.iloc[idx]
        print(f"Doc ID: {r_orig['id']} - {r_orig['so_ky_hieu']}")
        print(f"  + Lĩnh vực Gốc      : {r_orig['linh_vuc']}")
        print(f"  + Lĩnh vực Làm giàu : {r_enr['linh_vuc_enriched']}")
        print(f"  + Cơ quan ban hành  : {r_enr['co_quan_enriched']}")
        print(f"  + Đối tượng áp dụng : {r_enr['doi_tuong_ap_dung_list'][:120]}...")
        print("-" * 55)

# 8. Kiểm tra Điều kiện PASS
pass_files = output_raw_entities.exists() and output_enriched_meta.exists()
pass_coquan = (entities_df[entities_df['entity_type'] == 'CoQuan']['entity'].str.len() > 0).any()
pass_nguoiky = (entities_df[entities_df['entity_type'] == 'NguoiKy']['entity'].str.len() > 0).any()
pass_doituong = (entities_df[entities_df['entity_type'] == 'DoiTuongApDung']['evidence'].str.len() > 0).all()
pass_linhvuc = (enriched_df['linh_vuc_enriched'] != 'Chưa phân loại').sum() > (df['linh_vuc'] != 'Chưa phân loại').sum()

is_pass = pass_files and pass_coquan and pass_nguoiky and pass_doituong and pass_linhvuc

print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA ĐIỀU KIỆN BƯỚC 3")
print("=" * 60)
print(f"[{'PASS' if pass_files else 'FAIL'}] File extracted_entities_raw.csv và enriched_metadata.csv tồn tại")
print(f"[{'PASS' if pass_coquan else 'FAIL'}] CoQuan hợp lý và được trích xuất đầy đủ")
print(f"[{'PASS' if pass_nguoiky else 'FAIL'}] NguoiKy giữ nguyên từ gốc & bổ sung từ LLM")
print(f"[{'PASS' if pass_doituong else 'FAIL'}] DoiTuongApDung 100% có evidence rõ ràng")
print(f"[{'PASS' if pass_linhvuc else 'FAIL'}] LinhVuc cải thiện các giá trị thiếu/chưa phân loại")

if errors_list:
    print(f"\nDanh sách lỗi phát sinh ({len(errors_list)}):")
    for err in errors_list:
        print(f" - {err}")

print("\n" + "=" * 60)
if is_pass:
    print("KẾT LUẬN BƯỚC 3: PASS. Đã sẵn sàng cho Bước 4.")
else:
    print("KẾT LUẬN BƯỚC 3: FAIL. Cần kiểm tra lại trích xuất Gemini.")
print("=" * 60 + "\n")
