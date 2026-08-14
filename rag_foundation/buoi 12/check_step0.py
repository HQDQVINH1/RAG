import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

results = {}

# 1. Python check
py_version = sys.version.split()[0]
results['Python'] = (True, f"Python {py_version}")

# 2. Virtual environment check
in_venv = sys.prefix != sys.base_prefix or 'VIRTUAL_ENV' in os.environ
results['Virtual environment'] = (in_venv, f"Venv path: {sys.prefix}" if in_venv else "Not using a virtual environment")

# 3. metadata.csv check
meta_path = Path("ner_kb/metadata.csv")
if not meta_path.exists():
    # Try relative to current script
    meta_path = Path(__file__).parent / "ner_kb" / "metadata.csv"

results['metadata.csv'] = (
    meta_path.exists() and meta_path.stat().st_size > 0,
    f"Found at {meta_path} ({meta_path.stat().st_size} bytes)" if meta_path.exists() else "File not found"
)

# 4. content.csv check
content_path = Path("ner_kb/content.csv")
if not content_path.exists():
    content_path = Path(__file__).parent / "ner_kb" / "content.csv"

results['content.csv'] = (
    content_path.exists() and content_path.stat().st_size > 0,
    f"Found at {content_path} ({content_path.stat().st_size} bytes)" if content_path.exists() else "File not found"
)

# 5. Python packages check
required_packages = ['pandas', 'bs4', 'dotenv', 'google.genai', 'neo4j']
missing_packages = []
imported_packages = []

for pkg in required_packages:
    try:
        __import__(pkg)
        imported_packages.append(pkg)
    except ImportError:
        missing_packages.append(pkg)

if missing_packages:
    results['Python packages'] = (False, f"Missing: {', '.join(missing_packages)}")
else:
    results['Python packages'] = (True, f"All imported: {', '.join(imported_packages)}")

# 6. Gemini configuration check
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key or gemini_key == "YOUR_KEY_HERE":
    results['Gemini configuration'] = (False, "GEMINI_API_KEY is not configured in .env")
else:
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        # Verify client instantiation
        results['Gemini configuration'] = (True, "GEMINI_API_KEY is configured and google.genai Client initialized successfully")
    except Exception as e:
        results['Gemini configuration'] = (False, f"Failed to initialize Gemini client: {e}")

# 7. Neo4j configuration check
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_pass = os.getenv("NEO4J_PASSWORD")
neo4j_db = os.getenv("NEO4J_DATABASE", "neo4j")

if not neo4j_uri or not neo4j_user or not neo4j_pass or neo4j_pass == "YOUR_PASSWORD_HERE":
    results['Neo4j configuration'] = (False, "NEO4J connection settings missing or incomplete in .env")
else:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        driver.verify_connectivity()
        driver.close()
        results['Neo4j configuration'] = (True, f"Successfully connected to Neo4j at {neo4j_uri} (DB: {neo4j_db})")
    except Exception as e:
        results['Neo4j configuration'] = (False, f"Neo4j connection test failed: {e}")

# Print Report (ensuring secrets are NOT printed)
print("\n" + "="*50)
print("  BƯỚC 0: BÁO CÁO KIỂM TRA MÔI TRƯỜNG PROJECT")
print("="*50 + "\n")

all_passed = True
for key, (status, detail) in results.items():
    tag = "[PASS]" if status else "[FAIL]"
    if not status:
        all_passed = False
    print(f"{tag:<7} {key:<22}: {detail}")

print("\n" + "="*50)
if all_passed:
    print("KẾT LUẬN: Môi trường ĐẠT YÊU CẦU (ALL PASS). Có thể chuyển sang Bước 1.")
else:
    print("KẾT LUẬN: Môi trường CHƯA ĐẠT. Vui lòng xử lý các mục [FAIL] trước khi tiếp tục.")
print("="*50 + "\n")
