"""
buoi_17/scripts/encryption_demo.py
----------------------------------
Demo mã hóa dữ liệu cục bộ (Data-at-Rest Encryption) cho tệp nhật ký Audit Trail.
Sử dụng Fernet (Symmetric Encryption - AES-128-CBC) từ thư viện `cryptography`.

LƯU Ý: Đây là demo minh họa bảo vệ dữ liệu at-rest ở cấp độ cục bộ (educational demo).
Trong hệ thống thực tế (Production Systems), cần áp dụng KMS (AWS KMS / Azure Key Vault / HashiCorp Vault),
Hardware Security Modules (HSM), mã hóa đường truyền TLS/mTLS, key rotation tự động và kiểm soát IAM.
"""

import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

def get_or_create_key(key_path: Path) -> bytes:
    """
    Nạp khóa từ tệp key_path hoặc tạo khóa mới nếu chưa có.
    Khóa không được hard-code trực tiếp trong mã nguồn.
    """
    if key_path.exists():
        with open(key_path, "rb") as f:
            return f.read().strip()
    else:
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        print(f"[Encryption] Đã tạo khóa mã hóa mới tại: {key_path}")
        return key

def encrypt_file(source_path: Path, enc_path: Path, fernet: Fernet) -> int:
    """
    Mã hóa tệp nguồn sang tệp mã hóa .enc
    """
    with open(source_path, "rb") as f:
        data = f.read()
    encrypted_data = fernet.encrypt(data)
    with open(enc_path, "wb") as f:
        f.write(encrypted_data)
    print(f"[Encryption] Đã mã hóa {len(data)} bytes -> {len(encrypted_data)} bytes tại {enc_path.name}")
    return len(encrypted_data)

def decrypt_file(enc_path: Path, dec_path: Path, fernet: Fernet) -> int:
    """
    Giải mã tệp .enc sang tệp giải mã
    """
    with open(enc_path, "rb") as f:
        encrypted_data = f.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(dec_path, "wb") as f:
        f.write(decrypted_data)
    print(f"[Encryption] Đã giải mã {len(encrypted_data)} bytes -> {len(decrypted_data)} bytes tại {dec_path.name}")
    return len(decrypted_data)

def run_demo():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    key_path = project_root / "secret.key"
    source_path = project_root / "outputs" / "audit_log.jsonl"
    enc_path = project_root / "outputs" / "audit_log.jsonl.enc"
    dec_path = project_root / "outputs" / "audit_log_decrypted.jsonl"
    
    if not source_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp audit nguồn: {source_path}")
        
    # 1. Nạp/tạo key
    key = get_or_create_key(key_path)
    fernet = Fernet(key)
    
    # 2. Đọc dữ liệu gốc
    with open(source_path, "rb") as f:
        original_bytes = f.read()
        
    # 3. Mã hóa
    enc_size = encrypt_file(source_path, enc_path, fernet)
    
    # 4. Giải mã
    dec_size = decrypt_file(enc_path, dec_path, fernet)
    
    # 5. So khớp dữ liệu
    with open(dec_path, "rb") as f:
        decrypted_bytes = f.read()
        
    is_match = (original_bytes == decrypted_bytes)
    
    print("\n=== KẾT QUẢ SO KHỚP MÃ HÓA / GIẢI MÃ ===")
    print(f"Kích thước gốc:      {len(original_bytes)} bytes")
    print(f"Kích thước mã hóa:   {enc_size} bytes")
    print(f"Kích thước giải mã: {len(decrypted_bytes)} bytes")
    print(f"Dữ liệu gốc và giải mã khớp 100%: {is_match}")
    
    return {
        "encrypt_pass": enc_path.exists() and enc_size > 0,
        "decrypt_match": is_match,
        "original_size": len(original_bytes),
        "encrypted_size": enc_size
    }

if __name__ == "__main__":
    run_demo()
