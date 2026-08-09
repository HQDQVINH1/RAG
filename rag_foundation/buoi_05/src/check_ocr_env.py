import sys
import os
import importlib.util
from pathlib import Path

# Configure stdout for UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def check_env_file():
    current_dir = Path(__file__).parent
    env_path = current_dir / ".env"
    if not env_path.exists():
        return False, "File .env khong ton tai"
    
    try:
        from dotenv import dotenv_values
        config = dotenv_values(env_path)
        api_key = config.get("LLAMA_CLOUD_API_KEY", "").strip()
        if not api_key:
            return False, "Thieu bien LLAMA_CLOUD_API_KEY"
        if api_key in ["'KEY CỦA BẠN'", "KEY CỦA BẠN", "YOUR_API_KEY"]:
            return True, "Da co bien LLAMA_CLOUD_API_KEY (gia tri mac dinh)"
        masked = '*' * (len(api_key)-4) + api_key[-4:] if len(api_key) > 4 else '***'
        return True, f"Da cau hinh LLAMA_CLOUD_API_KEY ({masked})"
    except Exception as e:
        return False, f"Loi doc .env: {str(e)}"

def main():
    print("=" * 70)
    print("      KIEM TRA MOI TRUONG XU LY OCR & RAG (BUOI 05)")
    print("=" * 70)
    
    checks = []
    
    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_pass = sys.version_info >= (3, 9)
    checks.append(("Python >= 3.9", f"v{py_ver}", "PASS" if py_pass else "FAIL", "Can cai Python >= 3.9"))
    
    # 2. PyMuPDF (fitz)
    has_fitz = check_package("pymupdf", "fitz")
    checks.append(("PyMuPDF (fitz)", "Da cai" if has_fitz else "Chua cai", "PASS" if has_fitz else "FAIL", "pip install pymupdf"))
    
    # 3. Pillow (PIL)
    has_pil = check_package("pillow", "PIL")
    checks.append(("Pillow (PIL)", "Da cai" if has_pil else "Chua cai", "PASS" if has_pil else "FAIL", "pip install pillow"))
    
    # 4. Llama Cloud (llama_cloud)
    has_llama = check_package("llama-cloud", "llama_cloud")
    checks.append(("Llama Cloud", "Da cai" if has_llama else "Chua cai", "PASS" if has_llama else "FAIL", "pip install llama-cloud"))
    
    # 5. Pydantic
    has_pydantic = check_package("pydantic")
    checks.append(("Pydantic", "Da cai" if has_pydantic else "Chua cai", "PASS" if has_pydantic else "FAIL", "pip install pydantic"))
    
    # 6. Streamlit
    has_streamlit = check_package("streamlit")
    checks.append(("Streamlit", "Da cai" if has_streamlit else "Chua cai", "PASS" if has_streamlit else "FAIL", "pip install streamlit"))
    
    # 7. python-dotenv
    has_dotenv = check_package("python-dotenv", "dotenv")
    checks.append(("python-dotenv", "Da cai" if has_dotenv else "Chua cai", "PASS" if has_dotenv else "FAIL", "pip install python-dotenv"))
    
    # 8. File .env check
    env_pass, env_msg = check_env_file()
    checks.append(("File .env & API Key", env_msg, "PASS" if env_pass else "FAIL", "Tao file src/.env va dien LLAMA_CLOUD_API_KEY"))

    # Print Report Table
    print(f"{'Cong cu / Thanh phan':<25} | {'Trang thai chi tiet':<30} | {'Ket qua':<8}")
    print("-" * 70)
    
    all_pass = True
    for item, status, result, fix_cmd in checks:
        if result == "FAIL":
            all_pass = False
        print(f"{item:<25} | {status:<30} | [{result}]")
        
    print("=" * 70)
    
    if all_pass:
        print(">>> TAT CA THANH PHAN DA SAN SANG CHO BUOI 05! <<<")
    else:
        print(">>> CO THANH PHAN CHUA DAT! HUONG DAN KHAC PHUC: <<<")
        for item, status, result, fix_cmd in checks:
            if result == "FAIL":
                print(f" - {item}: Khac phuc bang lenh -> {fix_cmd}")
    print("=" * 70)

if __name__ == "__main__":
    main()
