import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("  BƯỚC 7: KIỂM TRA CẤU HÌNH VÀ KẾT NỐI NEO4J")
print("=" * 60 + "\n")

base_dir = Path(__file__).parent
env_file = base_dir / ".env"

if not env_file.exists():
    print(f"[ERROR] Không tìm thấy file {env_file}")
    sys.exit(1)

# 1. Đọc cấu hình từ .env
load_dotenv(env_file)

neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', '')
neo4j_db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("1. ĐỌC CẤU HÌNH TỪ .ENV:")
print(f"   - URI      : {neo4j_uri}")
print(f"   - Username : {neo4j_user}")
print(f"   - Password : {'*' * len(neo4j_password) if neo4j_password else '(Rỗng)'} (MẬT KHẨU ĐÃ ĐƯỢC ẨN)")
print(f"   - Database : {neo4j_db}\n")

# 2. Thử nghiệm kết nối
print("2. ĐANG KIỂM TRA KẾT NỐI TỚI NEO4J...")

driver = None
is_connected = False
error_message = None
db_info = None

try:
    auth = (neo4j_user, neo4j_password)
    driver = GraphDatabase.driver(neo4j_uri, auth=auth)
    
    # Verify connectivity
    driver.verify_connectivity()
    
    # Chạy query đọc đơn giản để kiểm tra database
    with driver.session(database=neo4j_db) as session:
        result = session.run("RETURN 'Connection OK' AS msg, datetime() AS current_time")
        record = result.single()
        msg = record['msg']
        time_str = str(record['current_time'])
        
        # Đọc thông tin version
        sys_info = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS ver, edition")
        sys_rec = sys_info.single()
        db_edition = sys_rec['edition'] if sys_rec else 'Unknown'
        db_ver = sys_rec['ver'] if sys_rec else 'Unknown'
        
        db_info = f"Neo4j {db_edition} (v{db_ver})"

    is_connected = True
    print("   -> Kết nối thành công!")
    print(f"   -> Phản hồi từ server: '{msg}' tại thời điểm {time_str}")
    print(f"   -> Hệ quản trị CSDL: {db_info}\n")

except Exception as e:
    is_connected = False
    error_message = str(e)
    print(f"   [ERROR] Kết nối thất bại: {error_message}\n")

finally:
    if driver:
        driver.close()
        print("3. Đã đóng driver kết nối an toàn.")

# 3. Kết luận
print("\n" + "=" * 60)
print("  KẾT QUẢ KIỂM TRA BƯỚC 7")
print("=" * 60)
print(f"Connection Status : {'PASS' if is_connected else 'FAIL'}")
print(f"Database đang dùng : {neo4j_db} ({db_info if db_info else 'N/A'})")
if not is_connected:
    print(f"Lỗi chi tiết       : {error_message}")

print("\n" + "=" * 60)
if is_connected:
    print("KẾT LUẬN BƯỚC 7: PASS. Đã sẵn sàng cho Bước 8 (Import dữ liệu vào Neo4j).")
else:
    print("KẾT LUẬN BƯỚC 7: FAIL. Vui lòng kiểm tra lại dịch vụ Neo4j hoặc thông tin .env.")
print("=" * 60 + "\n")
