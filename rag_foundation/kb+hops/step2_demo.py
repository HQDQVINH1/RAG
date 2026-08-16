"""
BƯỚC 2: Tạo Vector Nhúng (Dense Embeddings) với PyTorch CPU

Kịch bản này thực hiện và minh họa Bước 2:
1. Kiểm tra môi trường PyTorch (xác nhận đang chạy trên CPU).
2. Tải mô hình tiếng Việt chuyên dụng: `thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5` từ HuggingFace.
3. Mã hóa (encode) các đoạn văn bản pháp luật thu được từ Bước 1 thành Vector nhúng dày đặc (Dense Embeddings).
4. Kiểm tra kích thước Vector (384 chiều) và tính thử nghiệm độ tương đồng Cosine (Cosine Similarity).
"""

import sys
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

MODEL_NAME = "thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5"

def main():
    print("=" * 80)
    print("  BƯỚC 2: KHỞI TẠO VÀ KIỂM TRA MÔ HÌNH VECTOR EMBEDDING TRÊN CPU")
    print("=" * 80)
    
    # 1. Kiểm tra cấu hình PyTorch CPU
    print(f"\n1. KIỂM TRA THIẾT BỊ PHẦN CỨNG:")
    print(f"   - PyTorch Version: {torch.__version__}")
    print(f"   - CUDA Available: {torch.cuda.is_available()}")
    device = "cpu"
    print(f"   - Thiết bị được chỉ định: {device.upper()} (phù hợp điều kiện máy học sinh không có GPU)")
    
    # 2. Tải mô hình SentenceTransformer
    print(f"\n2. TẢI MÔ HÌNH HUGGINGFACE:")
    print(f"   - Mô hình: {MODEL_NAME}")
    print("   - Đang khởi tạo mô hình trên CPU...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("   -> Mô hình đã tải thành công!")

    # 3. Đoạn văn bản mẫu kiểm thử từ Bước 1
    sample_texts = [
        "Chương I QUY ĐỊNH CHUNG - Điều 1. Phạm vi điều chỉnh",
        "Thông tư này quy định về giao nhận, bảo quản, vận chuyển tiền mặt, tài sản quý, giấy tờ có giá",
        "Quy định về cấp Giấy phép lần đầu, cấp đổi Giấy phép của quỹ tín dụng nhân dân"
    ]

    print(f"\n3. TẠO VECTOR NHÚNG MẪU CHO {len(sample_texts)} ĐOẠN VĂN BẢN:")
    embeddings = model.encode(sample_texts, normalize_embeddings=True)

    for idx, (text, emb) in enumerate(zip(sample_texts, embeddings)):
        print(f"\n  • Đoạn {idx+1}: '{text}'")
        print(f"    - Kích thước Vector: {emb.shape}")
        print(f"    - Kiểu dữ liệu: {emb.dtype}")
        print(f"    - 5 giá trị đầu tiên của Vector: {np.round(emb[:5], 4)}")

    # 4. Tính toán độ tương đồng Cosine
    print(f"\n4. ĐÁNH GIÁ ĐỘ TƯƠNG ĐỒNG COSINE GIỮA CÁC VĂN BẢN:")
    cos_sim_1_2 = util.cos_sim(embeddings[0], embeddings[1]).item()
    cos_sim_1_3 = util.cos_sim(embeddings[0], embeddings[2]).item()
    
    print(f"   - Tương đồng giữa Đoạn 1 và Đoạn 2 (Cùng lĩnh vực Giao nhận tiền): {cos_sim_1_2:.4f}")
    print(f"   - Tương đồng giữa Đoạn 1 và Đoạn 3 (Khác lĩnh vực Quỹ TĐND): {cos_sim_1_3:.4f}")

    print("\n" + "=" * 80)
    print("TỔNG KẾT BƯỚC 2:")
    print(f"  - Đã cài đặt và cấu hình thành công PyTorch CPU (`pytorch-cpu`).")
    print(f"  - Đã tích hợp mô hình tiếng Việt chuyên dụng `{MODEL_NAME}`.")
    print(f"  - Kích thước mỗi Vector nhúng: 384 chiều (Float32).")
    print(f"  - Đã chuẩn hóa vector (Normalized) sẵn sàng cho Vector Index Cosine Similarity trong Neo4j.")
    print("=" * 80)

if __name__ == "__main__":
    main()
