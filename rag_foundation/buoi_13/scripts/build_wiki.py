import csv
import re
import sys
from pathlib import Path

# Fix UTF-8 encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def sanitize_filename(name: str) -> str:
    """Loại bỏ hoặc thay thế các ký tự không hợp lệ trong tên file Windows."""
    for char in r'\/:*?"<>|':
        name = name.replace(char, '-')
    # Chuẩn hóa khoảng trắng
    return ' '.join(name.split()).strip()

def build_wiki():
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "outputs"
    wiki_dir = base_dir / "wiki"

    risks_dir = wiki_dir / "risks"
    controls_dir = wiki_dir / "controls"
    events_dir = wiki_dir / "events"

    for d in [wiki_dir, risks_dir, controls_dir, events_dir]:
        d.mkdir(parents=True, exist_ok=True)

    entities_file = output_dir / "entities.csv"
    relations_file = output_dir / "relations.csv"

    if not entities_file.exists() or not relations_file.exists():
        print("ERROR: Không tìm thấy entities.csv hoặc relations.csv trong thư mục outputs/!")
        print("Vui lòng chạy script scripts/build_entities.py trước.")
        return

    # 1. Load Entities
    entities = {}
    with open(entities_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row["id"]
            # Đặt tên tiêu đề an toàn cho file và wikilink
            title_name = row.get("name", "").strip()
            if not title_name or title_name == eid:
                title_name = row.get("description", "").strip()
            
            clean_title = sanitize_filename(title_name)
            page_title = f"{eid} - {clean_title}" if clean_title else eid
            
            row["page_title"] = page_title
            entities[eid] = row

    # 2. Load Relations
    # Structure:
    # outgoing_relations[source_id] = list of relation dicts
    # incoming_relations[target_id] = list of relation dicts
    outgoing_relations = {}
    incoming_relations = {}

    with open(relations_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row["source_id"]
            tgt = row["target_id"]

            if src not in outgoing_relations:
                outgoing_relations[src] = []
            outgoing_relations[src].append(row)

            if tgt not in incoming_relations:
                incoming_relations[tgt] = []
            incoming_relations[tgt].append(row)

    created_files = []
    total_wikilinks = 0

    def count_and_write(filepath: Path, content: str):
        nonlocal total_wikilinks
        # Dem so wikilink [[...]] trong content
        links = re.findall(r'\[\[(.*?)\]\]', content)
        total_wikilinks += len(links)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        created_files.append(filepath)

    # 3. Generate Wiki Pages for RuiRo
    for eid, entity in entities.items():
        if entity["type"] == "RuiRo":
            filename = f"{entity['page_title']}.md"
            filepath = risks_dir / filename

            # Incoming MITIGATES (Controls)
            incoming = incoming_relations.get(eid, [])
            mitigating_controls = [r for r in incoming if r["relationship_type"] == "MITIGATES"]

            # Outgoing OBSERVED_AS (Events)
            outgoing = outgoing_relations.get(eid, [])
            observed_events = [r for r in outgoing if r["relationship_type"] == "OBSERVED_AS"]

            content = f"""---
id: {entity['id']}
type: {entity['type']}
verification_status: {entity['verification_status']}
data_origin: {entity['data_origin']}
---

# {entity['id']}: {entity['name']}

## 1. Thông tin tổng quan
- **Mã hồ sơ**: `{entity['id']}`
- **Loại Entity**: `{entity['type']}`
- **Danh mục (Category)**: {entity.get('category', '')}
- **Đơn vị quản lý (owner_unit_id)**: `{entity.get('owner_unit_id', '')}`
- **Mức rủi ro tiềm tàng (Inherent Level)**: {entity.get('inherent_level', '')}
- **Mức rủi ro còn lại (Residual Level)**: {entity.get('residual_level', '')}

## 2. Mô tả chi tiết
{entity.get('description', '')}

### Diễn giải cấu trúc rủi ro:
- **Nguyên nhân (Cause)**: {entity.get('cause', '')}
- **Sự kiện (Event)**: {entity.get('event', '')}
- **Hậu quả (Impact)**: {entity.get('impact', '')}

---

## 3. Kiểm soát giảm thiểu (MITIGATES)
"""
            if mitigating_controls:
                for r in mitigating_controls:
                    c_id = r["source_id"]
                    c_entity = entities.get(c_id)
                    c_link = f"[[{c_entity['page_title']}]]" if c_entity else f"[[{c_id}]]"
                    content += f"""- {c_link}
  - **Loại quan hệ (relationship_type)**: `{r['relationship_type']}`
  - **Bằng chứng (evidence_quote)**: {r.get('evidence_quote', '')}
  - **Trạng thái xác minh**: `{r.get('verification_status', '')}`
  - **Độ tin cậy (confidence)**: `{r.get('confidence', '')}`
"""
            else:
                content += "_Chưa có kiểm soát giảm thiểu được ghi nhận cho rủi ro này._\n"

            content += "\n---\n\n## 4. Sự kiện rủi ro liên quan (OBSERVED_AS)\n"
            if observed_events:
                for r in observed_events:
                    e_id = r["target_id"]
                    e_entity = entities.get(e_id)
                    e_link = f"[[{e_entity['page_title']}]]" if e_entity else f"[[{e_id}]]"
                    content += f"""- {e_link}
  - **Loại quan hệ (relationship_type)**: `{r['relationship_type']}`
  - **Bằng chứng (evidence_quote)**: {r.get('evidence_quote', '')}
  - **Trạng thái xác minh**: `{r.get('verification_status', '')}`
  - **Độ tin cậy (confidence)**: `{r.get('confidence', '')}`
"""
            else:
                content += "_Chưa ghi nhận sự kiện rủi ro thực tế nào._\n"

            content += f"\n---\n*Trở về [[Home|Trang chủ Wiki Risk Graph]]*\n"
            count_and_write(filepath, content)

    # 4. Generate Wiki Pages for KiemSoat
    for eid, entity in entities.items():
        if entity["type"] == "KiemSoat":
            filename = f"{entity['page_title']}.md"
            filepath = controls_dir / filename

            # Outgoing MITIGATES (Risks)
            outgoing = outgoing_relations.get(eid, [])
            mitigated_risks = [r for r in outgoing if r["relationship_type"] == "MITIGATES"]

            content = f"""---
id: {entity['id']}
type: {entity['type']}
verification_status: {entity['verification_status']}
data_origin: {entity['data_origin']}
---

# {entity['id']}: {entity['name']}

## 1. Thông tin kiểm soát
- **Mã kiểm soát**: `{entity['id']}`
- **Loại Entity**: `{entity['type']}`
- **Loại kiểm soát (Control Type)**: {entity.get('control_type', '')}
- **Tần suất thực hiện (Frequency)**: {entity.get('frequency', '')}
- **Đánh giá hiệu quả (Effectiveness)**: {entity.get('effectiveness', '')}
- **Vai trò chịu trách nhiệm (owner_role_id)**: `{entity.get('owner_role_id', '')}`

---

## 2. Rủi ro được giảm thiểu (MITIGATES)
"""
            if mitigated_risks:
                for r in mitigated_risks:
                    r_id = r["target_id"]
                    r_entity = entities.get(r_id)
                    r_link = f"[[{r_entity['page_title']}]]" if r_entity else f"[[{r_id}]]"
                    content += f"""- {r_link}
  - **Loại quan hệ (relationship_type)**: `{r['relationship_type']}`
  - **Bằng chứng (evidence_quote)**: {r.get('evidence_quote', '')}
  - **Trạng thái xác minh**: `{r.get('verification_status', '')}`
  - **Độ tin cậy (confidence)**: `{r.get('confidence', '')}`
"""
            else:
                content += "_Kiểm soát này chưa được gắn với rủi ro nào._\n"

            content += f"\n---\n*Trở về [[Home|Trang chủ Wiki Risk Graph]]*\n"
            count_and_write(filepath, content)

    # 5. Generate Wiki Pages for SuKienRuiRo
    for eid, entity in entities.items():
        if entity["type"] == "SuKienRuiRo":
            filename = f"{entity['page_title']}.md"
            filepath = events_dir / filename

            # Incoming OBSERVED_AS (Risks)
            incoming = incoming_relations.get(eid, [])
            observed_from_risks = [r for r in incoming if r["relationship_type"] == "OBSERVED_AS"]

            # Format loss amount
            loss_str = "0 VND"
            if entity.get("loss_amount_vnd"):
                try:
                    val = float(entity.get("loss_amount_vnd"))
                    loss_str = f"{val:,.0f} VND"
                except ValueError:
                    loss_str = f"{entity.get('loss_amount_vnd')} VND"

            content = f"""---
id: {entity['id']}
type: {entity['type']}
verification_status: {entity['verification_status']}
data_origin: {entity['data_origin']}
---

# {entity['id']}: {entity['description']}

## 1. Chi tiết sự kiện rủi ro
- **Mã sự kiện**: `{entity['id']}`
- **Loại Entity**: `{entity['type']}`
- **Mô tả sự kiện**: {entity.get('description', '')}
- **Thời điểm xảy ra (Occurred At)**: {entity.get('occurred_at', '')}
- **Thời điểm phát hiện (Discovered At)**: {entity.get('discovered_at', '')}
- **Mức độ tổn thất (Severity)**: {entity.get('severity', '')}
- **Giá trị tổn thất tài chính**: `{loss_str}`

---

## 2. Rủi ro tương ứng (OBSERVED_AS)
"""
            if observed_from_risks:
                for r in observed_from_risks:
                    r_id = r["source_id"]
                    r_entity = entities.get(r_id)
                    r_link = f"[[{r_entity['page_title']}]]" if r_entity else f"[[{r_id}]]"
                    content += f"""- {r_link}
  - **Loại quan hệ (relationship_type)**: `{r['relationship_type']}`
  - **Bằng chứng (evidence_quote)**: {r.get('evidence_quote', '')}
  - **Trạng thái xác minh**: `{r.get('verification_status', '')}`
  - **Độ tin cậy (confidence)**: `{r.get('confidence', '')}`
"""
            else:
                content += "_Sự kiện này chưa được gắn với hồ sơ rủi ro tương ứng._\n"

            content += f"\n---\n*Trở về [[Home|Trang chủ Wiki Risk Graph]]*\n"
            count_and_write(filepath, content)

    # 6. Generate wiki/Home.md
    home_path = wiki_dir / "Home.md"
    
    # Calculate counts
    risk_entities = [e for e in entities.values() if e["type"] == "RuiRo"]
    control_entities = [e for e in entities.values() if e["type"] == "KiemSoat"]
    event_entities = [e for e in entities.values() if e["type"] == "SuKienRuiRo"]

    home_content = f"""# 🛡️ Wiki Risk Graph - Trang chủ Quản trị Rủi ro

Đóng vai trò là trung tâm tri thức đồ thị rủi ro (Risk Knowledge Graph Wiki), kết nối **Kiểm soát**, **Hồ sơ Rủi ro** và **Sự kiện Rủi ro thực tế**.

---

## 📊 Thống kê mạng lưới (Graph Overview)

- **Tổng số Nodes (Thực thể)**: `{len(entities)}`
  - 🔴 **Hồ sơ Rủi ro (RuiRo)**: `{len(risk_entities)}` trang
  - 🟢 **Biện pháp Kiểm soát (KiemSoat)**: `{len(control_entities)}` trang
  - 🟡 **Sự kiện Rủi ro (SuKienRuiRo)**: `{len(event_entities)}` trang
- **Tổng số Edges (Mối quan hệ)**: `{sum(len(v) for v in outgoing_relations.values())}`
  - `MITIGATES` (`KiemSoat` -> `RuiRo`): `{sum(1 for rels in outgoing_relations.values() for r in rels if r['relationship_type'] == 'MITIGATES')}`
  - `OBSERVED_AS` (`RuiRo` -> `SuKienRuiRo`): `{sum(1 for rels in outgoing_relations.values() for r in rels if r['relationship_type'] == 'OBSERVED_AS')}`

---

## 📌 Danh mục Thực thể

### 1. Danh sách Hồ sơ Rủi ro (RuiRo)
"""
    for r in risk_entities:
        home_content += f"- [[{r['page_title']}]] - *{r['name']}* (Mức rủi ro còn lại: {r.get('residual_level', 'N/A')})\n"

    home_content += "\n### 2. Danh sách Biện pháp Kiểm soát (KiemSoat)\n"
    for c in control_entities:
        home_content += f"- [[{c['page_title']}]] - *{c['name']}* (Loại: {c.get('control_type', 'N/A')})\n"

    home_content += "\n### 3. Danh sách Sự kiện Rủi ro (SuKienRuiRo)\n"
    for e in event_entities:
        home_content += f"- [[{e['page_title']}]] - *{e['description']}* (Mức độ: {e.get('severity', 'N/A')})\n"

    home_content += """
---
*Hệ thống được tạo tự động bởi AI Coding Agent - Wiki Risk Graph Builder.*
"""
    count_and_write(home_path, home_content)

    print("=" * 80)
    print("BÁO CÁO KẾT QUẢ BUILD WIKI MARKDOWN")
    print("=" * 80)
    print(f"✓ Thư mục đích: {wiki_dir}")
    print(f"✓ Tổng số trang Wiki đã sinh: {len(created_files)} (gồm Home.md + 34 entity pages)")
    print(f"  + Trang Home: 1")
    print(f"  + wiki/risks/: {len(risk_entities)} trang")
    print(f"  + wiki/controls/: {len(control_entities)} trang")
    print(f"  + wiki/events/: {len(event_entities)} trang")
    print(f"✓ Tổng số Obsidian Wikilink [[...]] đã tạo: {total_wikilinks}")

    print("\n--- VÍ DỤ ĐƯỜNG ĐI TRUY VẾT DỮ LIỆU (KiemSoat -> RuiRo -> SuKienRuiRo) ---")
    # Finding an example path: KS-001 -> RR-001 -> SK-001
    ks_example = entities.get("KS-001")
    rr_example = entities.get("RR-001")
    sk_example = entities.get("SK-001")

    if ks_example and rr_example and sk_example:
        print(f"1. Node Kiểm soát: [[{ks_example['page_title']}]]")
        print(f"   └── (MITIGATES) ──> 2. Node Rủi ro: [[{rr_example['page_title']}]]")
        print(f"                       └── (OBSERVED_AS) ──> 3. Node Sự kiện: [[{sk_example['page_title']}]]")

    print("=" * 80)

if __name__ == "__main__":
    build_wiki()
