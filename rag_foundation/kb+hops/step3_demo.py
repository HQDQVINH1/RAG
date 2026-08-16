"""
BƯỚC 3: Cấu hình và Kiểm tra Kết nối Cơ sở dữ liệu Neo4j

Kịch bản này hỗ trợ:
1. Thử kết nối tới Neo4j Instance qua giao thức Bolt (`bolt://localhost:7687`).
2. Kiểm tra xác thực Tài khoản `neo4j` và Mật khẩu `Vinh1989`.
3. Kiểm tra sự tồn tại của Database `kb-hops` hoặc DB mặc định `neo4j`.
"""

import sys
from neo4j import GraphDatabase

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Vinh1989"
NEO4J_DATABASE = "kb-hops"

def test_connection():
    print("=" * 80)
    print("  BƯỚC 3: CẤU HÌNH VÀ KIỂM TRA KẾT NỐI CƠ SỞ DỮ LIỆU NEO4J")
    print("=" * 80)
    print(f"\nThông số cấu hình kết nối:")
    print(f"  • Bolt URI: {NEO4J_URI}")
    print(f"  • User:     {NEO4J_USER}")
    print(f"  • Password: {'*' * len(NEO4J_PASSWORD)}")
    print(f"  • Database: {NEO4J_DATABASE}")
    print("-" * 80)
    print("Đang thử kết nối tới Neo4j Server...")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("\n✓ KẾT NỐI THÀNH CÔNG TỚI NEO4J SERVER!")
        
        # Kiểm tra truy vấn hệ thống
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("RETURN 'Neo4j Connected Successfully!' AS msg").single()
            print(f"  • Kết quả truy vấn thử nghiệm trên DB '{NEO4J_DATABASE}': {result['msg']}")
            
        driver.close()
        return True
    except Exception as e:
        print("\n✗ KHÔNG THỂ KẾT NỐI TỚI NEO4J SERVER!")
        print(f"  Chi tiết lỗi: {e}")
        print("\nHƯỚNG DẪN KHẮC PHỤC:")
        print("  1. Mở ứng dụng Neo4j Desktop 2.0 trên máy của bạn.")
        print("  2. Nhấn nút 'START' để khởi động Instance DBMS (chờ đèn báo chuyển màu Xanh).")
        print("  3. Sau khi khởi động xong, chạy lại kịch bản này hoặc chạy `lab1_chunking_embeddings_neo4j.py`.")
        return False

if __name__ == "__main__":
    test_connection()
