import os
import sys
import re
import asyncio
import unicodedata
from pathlib import Path
import fitz  # PyMuPDF
from dotenv import dotenv_values

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Tập hợp các ký tự tiếng Việt có dấu chuẩn Unicode NFC
VIETNAMESE_DIACRITICS = set("áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵđÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴĐ")

def get_api_key() -> str:
    """Reads LLAMA_CLOUD_API_KEY from src/.env without printing secret values."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        config = dotenv_values(env_path)
        key = config.get("LLAMA_CLOUD_API_KEY", "").strip()
        if key and key not in ["'KEY CỦA BẠN'", "KEY CỦA BẠN", "YOUR_API_KEY"]:
            return key
    return os.environ.get("LLAMA_CLOUD_API_KEY", "").strip()

def normalize_nfc(text: str) -> str:
    """Normalize string to Unicode NFC format."""
    if not text:
        return ""
    return unicodedata.normalize('NFC', text)

def is_text_corrupted_or_empty(text: str) -> bool:
    """
    Phát hiện văn bản bị rỗng, lỗi font, mã hóa méo tiếng Việt (như h4n, dqng, ng6n)
    hoặc thiếu hụt dấu tiếng Việt trầm trọng.
    """
    if not text or len(text.strip()) < 15:
        return True
    
    total_len = len(text)
    
    # 1. Kiểm tra ký tự lạ / ký tự không in được
    replacement_count = text.count('\ufffd')
    unprintable_count = sum(1 for c in text if not c.isprintable() and c not in '\n\r\t')
    
    if (replacement_count / total_len) > 0.05 or (unprintable_count / total_len) > 0.05:
        return True

    # 2. Kiểm tra lỗi Font Encoding tiếng Việt (VNI / Identity-H mapping méo sang ký tự số/chữ)
    if total_len > 100:
        diacritics_count = sum(1 for c in text if c in VIETNAMESE_DIACRITICS)
        diacritic_ratio = diacritics_count / total_len
        
        # Mẫu từ bị biến dạng font điển hình: chữ chèn số (ng6n, nu6c, h4n, 14i) hoặc cặp ký tự méo (dqng, nq)
        distortion_patterns = [r'\b[a-zA-Z]+[0-9]+[a-zA-Z]*\b', r'\bdq\w*', r'\bnq\w*']
        distortion_matches = sum(len(re.findall(pat, text)) for pat in distortion_patterns)
        
        # Tiếng Việt chuẩn thường có tỷ lệ dấu > 3%. Nếu < 1.5% hoặc có nhiều mẫu méo font -> Lỗi font
        if diacritic_ratio < 0.015 or distortion_matches >= 4:
            return True
            
    return False

async def ocr_fallback_llamaparse(pdf_path: str, api_key: str) -> str:
    """Fallback OCR processing using LlamaParse from llama-cloud."""
    try:
        from llama_cloud import AsyncLlamaCloud
        client = AsyncLlamaCloud(api_key=api_key)
        
        file_obj = await client.files.create(file=pdf_path, purpose="parse")
        result = await client.parsing.parse(
            file_id=file_obj.id,
            tier="agentic",
            version="latest",
            expand=["markdown_full"]
        )
        return result.markdown_full if result and hasattr(result, 'markdown_full') else ""
    except Exception as e:
        print(f"[CẢNH BÁO OCR] Gọi LlamaParse thất bại đối với {Path(pdf_path).name}: {str(e)}")
        return ""

def extract_pdf_pages(pdf_path: str) -> list[dict]:
    """Extracts text per page using PyMuPDF and validates Vietnamese font quality."""
    doc = fitz.open(pdf_path)
    pages_data = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        raw_text = page.get_text("text")
        cleaned_text = normalize_nfc(raw_text.strip())
        is_bad = is_text_corrupted_or_empty(cleaned_text)
        
        pages_data.append({
            "page": page_idx + 1,
            "text": cleaned_text,
            "quality_ok": not is_bad,
            "ocr_used": False
        })
    doc.close()
    return pages_data

async def process_pdf_document(pdf_path: str, force_ocr: bool = False) -> dict:
    """Processes PDF document with PyMuPDF primary & LlamaParse fallback if corrupt or forced."""
    pdf_file = Path(pdf_path)
    filename = pdf_file.name
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file PDF tại: {pdf_path}")
        
    pages = extract_pdf_pages(pdf_path)
    bad_pages = [p for p in pages if not p["quality_ok"]]
    
    ocr_needed = force_ocr or len(bad_pages) > 0
    all_ok = not ocr_needed
    
    full_text_pages = []
    
    if all_ok:
        print(f"[INFO] File '{filename}': PyMuPDF trích xuất text layer chuẩn tiếng Việt ({len(pages)} trang).")
        for p in pages:
            full_text_pages.append({
                "page": p["page"],
                "text": p["text"],
                "ocr_used": False
            })
    else:
        reason = "Bắt buộc OCR (force_ocr)" if force_ocr else f"Phát hiện {len(bad_pages)}/{len(pages)} trang bị lỗi font/méo chữ tiếng Việt"
        print(f"[INFO] File '{filename}': {reason}. Kích hoạt LlamaParse OCR...")
        api_key = get_api_key()
        if not api_key:
            print(f"[CẢNH BÁO] Không tìm thấy LLAMA_CLOUD_API_KEY hợp lệ trong .env. Dùng text PyMuPDF hiện có kèm cảnh báo.")
            for p in pages:
                full_text_pages.append({
                    "page": p["page"],
                    "text": p["text"] if p["text"] else "[LỖI TRÍCH XUẤT TEXT & THIẾU API KEY OCR]",
                    "ocr_used": False
                })
        else:
            ocr_text = await ocr_fallback_llamaparse(pdf_path, api_key)
            if ocr_text:
                ocr_text_nfc = normalize_nfc(ocr_text)
                print(f"[INFO] File '{filename}': OCR bằng LlamaParse thành công!")
                full_text_pages.append({
                    "page": 1,
                    "text": ocr_text_nfc,
                    "ocr_used": True
                })
            else:
                print(f"[CẢNH BÁO] OCR LlamaParse không trả về dữ liệu. Dùng lại kết quả PyMuPDF.")
                for p in pages:
                    full_text_pages.append({
                        "page": p["page"],
                        "text": p["text"],
                        "ocr_used": False
                    })
                    
    return {
        "source": filename,
        "total_pages": len(pages),
        "ocr_used": len(full_text_pages) > 0 and full_text_pages[0].get("ocr_used", False),
        "pages": full_text_pages
    }
