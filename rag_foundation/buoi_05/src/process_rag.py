import os
import sys
import json
import argparse
import asyncio
from pathlib import Path

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add src directory to python sys.path if needed
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ocr_processor import process_pdf_document
from chunking_strategies import (
    fixed_size_chunking,
    semantic_chunking,
    hierarchical_chunking,
    compute_chunk_stats
)

async def run_pipeline(pdf_path: Path, write_to_disk: bool = False):
    print("=" * 80)
    print(f">>> CHẠY LUỒNG XỬ LÝ RAG CHO FILE: {pdf_path.name} <<<")
    print("=" * 80)
    
    # 1. Read & Process PDF with PyMuPDF / LlamaParse OCR
    doc_data = await process_pdf_document(str(pdf_path))
    
    # 2. Run 3 Chunking Strategies
    fixed_chunks = fixed_size_chunking(doc_data, chunk_size=500, overlap=50)
    semantic_chunks = semantic_chunking(doc_data, target_size=500)
    hierarchical_chunks = hierarchical_chunking(doc_data)
    
    # 3. Calculate Statistics
    stats_fixed = compute_chunk_stats(fixed_chunks)
    stats_semantic = compute_chunk_stats(semantic_chunks)
    stats_hierarchical = compute_chunk_stats(hierarchical_chunks)
    
    print("\n" + "-" * 70)
    print(f" BÁO CÁO THỐNG KÊ CHUNKING — {pdf_path.name}")
    print("-" * 70)
    print(f"{'Chiến lược Chunking':<25} | {'Số lượng':<8} | {'Độ dài Min':<10} | {'Độ dài Max':<10} | {'Trung bình':<10}")
    print("-" * 70)
    print(f"{'Fixed-size (500/50)':<25} | {stats_fixed['count']:<8} | {stats_fixed['min_len']:<10} | {stats_fixed['max_len']:<10} | {stats_fixed['avg_len']:<10}")
    print(f"{'Semantic (Đoạn/Ngắt câu)':<25} | {stats_semantic['count']:<8} | {stats_semantic['min_len']:<10} | {stats_semantic['max_len']:<10} | {stats_semantic['avg_len']:<10}")
    print(f"{'Hierarchical (Chương/Điều)':<25} | {stats_hierarchical['count']:<8} | {stats_hierarchical['min_len']:<10} | {stats_hierarchical['max_len']:<10} | {stats_hierarchical['avg_len']:<10}")
    print("-" * 70)
    
    # 4. Show metadata example of first chunk
    sample_chunk = None
    if hierarchical_chunks:
        sample_chunk = hierarchical_chunks[0]
    elif semantic_chunks:
        sample_chunk = semantic_chunks[0]
    elif fixed_chunks:
        sample_chunk = fixed_chunks[0]
        
    if sample_chunk:
        print("\n>>> VÍ DỤ METADATA MỘT CHUNK TRÍCH XUẤT <<<")
        print(json.dumps(sample_chunk, ensure_ascii=False, indent=2))
        
    # 5. Output handling (--write or --dry-run)
    if write_to_disk:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        raw_out_path = output_dir / f"raw_ocr_{pdf_path.stem}.json"
        chunks_out_path = output_dir / f"chunks_{pdf_path.stem}.json"
        
        all_chunks = fixed_chunks + semantic_chunks + hierarchical_chunks
        
        with open(raw_out_path, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
        with open(chunks_out_path, "w", encoding="utf-8") as f:
            json.dump({
                "source": pdf_path.name,
                "statistics": {
                    "fixed_size": stats_fixed,
                    "semantic": stats_semantic,
                    "hierarchical": stats_hierarchical
                },
                "chunks": all_chunks
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\n[THÀNH CÔNG] Đã ghi dữ liệu kết quả ra thư mục output:")
        print(f" - Raw text/OCR: {raw_out_path.name}")
        print(f" - Chunks data: {chunks_out_path.name}")
    else:
        print("\n[DRY-RUN MODE] Chạy thử thành công. Không ghi dữ liệu ra đĩa.")

async def main():
    parser = argparse.ArgumentParser(description="Chạy luồng OCR & Chunking cho tài liệu RAG Buổi 5")
    parser.add_argument("--write", action="store_true", help="Ghi kết quả ra thư mục output/")
    parser.add_argument("--dry-run", action="store_true", help="Chạy kiểm thử không ghi đĩa (mặc định)")
    parser.add_argument("--pdf", type=str, default="", help="Đường dẫn file PDF cụ thể trong datademo/")
    
    args = parser.parse_args()
    
    # Root directory for Buoi 05
    buoi_05_dir = Path(__file__).parent.parent
    datademo_dir = buoi_05_dir / "datademo"
    
    if args.pdf:
        target_pdf = Path(args.pdf)
        if not target_pdf.is_absolute():
            target_pdf = datademo_dir / args.pdf
        pdf_files = [target_pdf]
    else:
        pdf_files = list(datademo_dir.glob("*.pdf"))
        
    if not pdf_files:
        print(f"[LỖI] Không tìm thấy file PDF nào trong thư mục {datademo_dir}")
        sys.exit(1)
        
    write_flag = args.write
    
    for pdf in pdf_files:
        if not pdf.exists():
            print(f"[CẢNH BÁO] Không tìm thấy file: {pdf}")
            continue
        try:
            await run_pipeline(pdf, write_to_disk=write_flag)
        except Exception as e:
            print(f"[LỖI XỬ LÝ] Gặp lỗi khi xử lý file {pdf.name}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
