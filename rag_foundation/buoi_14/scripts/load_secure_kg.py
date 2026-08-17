"""
buoi_14/scripts/load_secure_kg.py
---------------------------------
Script nạp thông tin phân quyền (allowed_roles) từ chunks_secure.csv
vào cơ sở dữ liệu đồ thị Neo4j.

Yêu cầu:
1. Đọc cấu hình từ .env
2. Cập nhật thuộc tính allowed_roles (dạng List of Strings) vào các node DieuKhoan và VanBan.
3. Không DETACH DELETE đồ thị. Đánh dấu lab_session = "buoi_15".
4. Kiểm thử đếm số node có allowed_roles và truy vấn mẫu 1 VanBan + DieuKhoan liên kết.
"""

import sys
import json
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env configuration
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Vinh1989")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "chunks_secure.csv"
LAB_SESSION = "buoi_15"

def load_secure_kg():
    from neo4j import GraphDatabase
    
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    print(f"Reading secured dataset from: {INPUT_CSV}")
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")
        
    df = pd.read_csv(INPUT_CSV, encoding='utf-8')
    print(f"Loaded {len(df)} secure chunks.")
    
    with driver.session(database=NEO4J_DATABASE) as session:
        # 1. Update allowed_roles on DieuKhoan nodes
        print("[1/3] Updating allowed_roles on DieuKhoan nodes...")
        updated_dieukhoan = 0
        for _, row in df.iterrows():
            cid = str(row['chunk_id'])
            doc_id = str(row['document_id'])
            roles_raw = row['allowed_roles']
            roles_list = json.loads(roles_raw) if isinstance(roles_raw, str) else list(roles_raw)
            
            session.run("""
                MERGE (d:DieuKhoan {id: $cid})
                SET d.allowed_roles = $roles,
                    d.document_id = $doc_id,
                    d.lab_session = $lab_session
                WITH d
                MERGE (v:VanBan {id: $doc_id})
                MERGE (v)-[r:CONTAINS]->(d)
                SET r.lab_session = $lab_session
            """, {
                'cid': cid,
                'doc_id': doc_id,
                'roles': roles_list,
                'lab_session': LAB_SESSION
            })
            updated_dieukhoan += 1
            
        print(f"-> Updated {updated_dieukhoan} DieuKhoan nodes.")
        
        # 2. Update allowed_roles on VanBan nodes based on contained DieuKhoan nodes
        print("[2/3] Aggregating allowed_roles to VanBan nodes...")
        session.run("""
            MATCH (v:VanBan)-[:CONTAINS]->(d:DieuKhoan)
            WHERE d.allowed_roles IS NOT NULL
            UNWIND d.allowed_roles AS role
            WITH v, collect(DISTINCT role) AS doc_roles
            SET v.allowed_roles = doc_roles,
                v.lab_session = $lab_session
        """, {'lab_session': LAB_SESSION})
        print("-> Aggregated allowed_roles on VanBan nodes.")
        
        # 3. Validation queries
        print("\n[3/3] --- VERIFICATION & AUDIT ---")
        
        # Count nodes with allowed_roles
        res_dk = session.run("""
            MATCH (d:DieuKhoan)
            WHERE d.allowed_roles IS NOT NULL
            RETURN count(d) AS count
        """).single()['count']
        
        res_vb = session.run("""
            MATCH (v:VanBan)
            WHERE v.allowed_roles IS NOT NULL
            RETURN count(v) AS count
        """).single()['count']
        
        print(f"- DieuKhoan nodes with allowed_roles: {res_dk}")
        print(f"- VanBan nodes with allowed_roles   : {res_vb}")
        
        # Sample inspection query
        sample = session.run("""
            MATCH (v:VanBan)-[:CONTAINS]->(d:DieuKhoan)
            WHERE v.allowed_roles IS NOT NULL AND d.allowed_roles IS NOT NULL
            RETURN v.id AS doc_id, v.title AS doc_title, v.allowed_roles AS doc_roles,
                   collect({id: d.id, roles: d.allowed_roles})[0..3] AS sample_clauses
            LIMIT 1
        """).single()
        
        if sample:
            print("\n- Sample VanBan and linked DieuKhoan inspection:")
            print(f"  * Document ID   : {sample['doc_id']}")
            print(f"  * Document Title: {sample['doc_title']}")
            print(f"  * VanBan Roles  : {sample['doc_roles']}")
            print("  * Linked DieuKhoan Sample:")
            for dk in sample['sample_clauses']:
                print(f"    - Clause ID: {dk['id']}, Roles: {dk['roles']}")
                
    driver.close()
    print("\nSecure Graph Loading completed successfully!")

if __name__ == "__main__":
    load_secure_kg()
