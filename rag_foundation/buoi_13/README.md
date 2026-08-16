# 🛡️ Project Wiki Risk Graph - Hướng dẫn thực thi quy trình

Dự án xây dựng **Wiki Tri thức Rủi ro (Risk Knowledge Graph Wiki)** phục vụ đào tạo và quản trị rủi ro.

Mô hình chuyển đổi dữ liệu toàn vẹn:
```text
CSV Seed Data  --->  Chuẩn hóa (Entities & Relations)  --->  Obsidian Wiki Vault  --->  Neo4j Knowledge Graph
```

---

## 📌 Thứ tự thực thi từng bước (Execution Pipeline)

### Bước 1: Kiểm tra dữ liệu Seed ban đầu
Kiểm tra cấu trúc, số dòng, cột, khóa chính, khóa ngoại và phát hiện master data bị thiếu:
```bash
python scripts/inspect_data.py
```

### Bước 2: Chuẩn hóa dữ liệu thành Node & Edge (Entities & Relations)
Chuyển đổi 4 file CSV seed nghiệp vụ thành 2 file dữ liệu chuẩn hóa tại `outputs/entities.csv` và `outputs/relations.csv`:
```bash
python scripts/build_entities.py
```

### Bước 3: Sinh các trang Wiki Markdown cho Obsidian
Tạo cấu trúc cây thư mục `wiki/` gồm `Home.md`, `risks/`, `controls/`, `events/` kèm các Obsidian Wikilinks `[[...]]`:
```bash
python scripts/build_wiki.py
```

### Bước 4: Kiểm thử tự động toàn vẹn Wiki (Wiki Validation)
Chạy script kiểm tra 9 tiêu chí chất lượng (Broken links, Duplicate IDs, Orphan pages, Reference Integrity...):
```bash
python scripts/validate_wiki.py
```
> Kết quả kiểm thử chi tiết được ghi nhận tại [`outputs/wiki_validation_report.md`](outputs/wiki_validation_report.md).

### Bước 5: Trực quan hóa Knowledge Graph bằng Obsidian
1. Mở phần mềm **Obsidian**.
2. Chọn **Open folder as vault**.
3. Trỏ tới thư mục `wiki/` trong project này.
4. Mở trang `Home.md` hoặc bấm `Ctrl + Shift + G` để mở **Graph View**.

---

## 🍃 Bước 6: (Tùy chọn) Nạp dữ liệu vào Neo4j Database

### 1. Cài đặt thư viện Python (nếu chưa có):
```bash
pip install neo4j python-dotenv
```

### 2. Cấu hình biến môi trường:
Tạo file `.env` tại thư mục gốc project (hoặc copy từ `.env.example`):
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j
```

### 3. Thực thi nạp dữ liệu:
```bash
python scripts/load_neo4j.py
```

### 4. Thực thi Cypher queries mẫu:
Mở **Neo4j Browser** (`http://localhost:7474`) và chạy các query được chuẩn bị sẵn tại:
- Constraint & Index: [`cypher/schema.cypher`](cypher/schema.cypher)
- Truy vấn mẫu A đến F: [`cypher/demo_queries.cypher`](cypher/demo_queries.cypher)

---

## 📁 Cấu trúc thư mục dự án

```text
.
├── data/                       # Dữ liệu CSV seed nghiệp vụ gốc
│   ├── risk_profiles_seed.csv
│   ├── controls_seed.csv
│   ├── risk_events_seed.csv
│   └── relationships_seed.csv
├── outputs/                    # Dữ liệu chuẩn hóa & Báo cáo
│   ├── entities.csv
│   ├── relations.csv
│   └── wiki_validation_report.md
├── wiki/                       # Vault Obsidian chứa các trang Markdown
│   ├── Home.md
│   ├── risks/
│   ├── controls/
│   └── events/
├── cypher/                     # Script Cypher cho Neo4j
│   ├── schema.cypher
│   └── demo_queries.cypher
├── scripts/                    # Các kịch bản xử lý tự động
│   ├── inspect_data.py
│   ├── build_entities.py
│   ├── build_wiki.py
│   ├── validate_wiki.py
│   └── load_neo4j.py
├── .env.example                # File cấu hình mẫu môi trường
└── README.md                   # Hướng dẫn quy trình thực thi
```
