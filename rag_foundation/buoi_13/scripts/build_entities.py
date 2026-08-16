import csv
import sys
from pathlib import Path

# Fix UTF-8 encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def build():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    output_dir = base_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    risk_profiles_file = data_dir / "risk_profiles_seed.csv"
    controls_file = data_dir / "controls_seed.csv"
    risk_events_file = data_dir / "risk_events_seed.csv"
    relationships_file = data_dir / "relationships_seed.csv"

    entities = []
    entity_ids = set()

    # 1. Read risk_profiles_seed.csv -> type = RuiRo
    with open(risk_profiles_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row["id"]
            if entity_id in entity_ids:
                print(f"WARNING: Duplicate entity ID {entity_id} found in risk_profiles_seed.csv")
            entity_ids.add(entity_id)

            entities.append({
                "id": entity_id,
                "type": "RuiRo",
                "name": row.get("name", ""),
                "description": row.get("description", ""),
                "source_file": "risk_profiles_seed.csv",
                "data_origin": row.get("data_origin", ""),
                "verification_status": row.get("verification_status", ""),
                # Extended domain attributes
                "category": row.get("category", ""),
                "cause": row.get("cause", ""),
                "event": row.get("event", ""),
                "impact": row.get("impact", ""),
                "inherent_level": row.get("inherent_level", ""),
                "residual_level": row.get("residual_level", ""),
                "owner_unit_id": row.get("owner_unit_id", ""),
                "control_type": "",
                "frequency": "",
                "owner_role_id": "",
                "effectiveness": "",
                "risk_id": "",
                "occurred_at": "",
                "discovered_at": "",
                "severity": "",
                "loss_amount_vnd": ""
            })

    # 2. Read controls_seed.csv -> type = KiemSoat
    with open(controls_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row["id"]
            if entity_id in entity_ids:
                print(f"WARNING: Duplicate entity ID {entity_id} found in controls_seed.csv")
            entity_ids.add(entity_id)

            entities.append({
                "id": entity_id,
                "type": "KiemSoat",
                "name": row.get("name", ""),
                "description": row.get("name", ""),  # Using control name as default description
                "source_file": "controls_seed.csv",
                "data_origin": row.get("data_origin", ""),
                "verification_status": row.get("verification_status", ""),
                # Extended domain attributes
                "category": "",
                "cause": "",
                "event": "",
                "impact": "",
                "inherent_level": "",
                "residual_level": "",
                "owner_unit_id": "",
                "control_type": row.get("control_type", ""),
                "frequency": row.get("frequency", ""),
                "owner_role_id": row.get("owner_role_id", ""),
                "effectiveness": row.get("effectiveness", ""),
                "risk_id": "",
                "occurred_at": "",
                "discovered_at": "",
                "severity": "",
                "loss_amount_vnd": ""
            })

    # 3. Read risk_events_seed.csv -> type = SuKienRuiRo
    with open(risk_events_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row["id"]
            if entity_id in entity_ids:
                print(f"WARNING: Duplicate entity ID {entity_id} found in risk_events_seed.csv")
            entity_ids.add(entity_id)

            entities.append({
                "id": entity_id,
                "type": "SuKienRuiRo",
                "name": row.get("description", ""),  # Using event description as name
                "description": row.get("description", ""),
                "source_file": "risk_events_seed.csv",
                "data_origin": row.get("data_origin", ""),
                "verification_status": row.get("verification_status", ""),
                # Extended domain attributes
                "category": "",
                "cause": "",
                "event": "",
                "impact": "",
                "inherent_level": "",
                "residual_level": "",
                "owner_unit_id": "",
                "control_type": "",
                "frequency": "",
                "owner_role_id": "",
                "effectiveness": "",
                "risk_id": row.get("risk_id", ""),
                "occurred_at": row.get("occurred_at", ""),
                "discovered_at": row.get("discovered_at", ""),
                "severity": row.get("severity", ""),
                "loss_amount_vnd": row.get("loss_amount_vnd", "")
            })

    # Write outputs/entities.csv
    entities_csv_path = output_dir / "entities.csv"
    entity_fieldnames = [
        "id", "type", "name", "description", "source_file", "data_origin", "verification_status",
        "category", "cause", "event", "impact", "inherent_level", "residual_level", "owner_unit_id",
        "control_type", "frequency", "owner_role_id", "effectiveness",
        "risk_id", "occurred_at", "discovered_at", "severity", "loss_amount_vnd"
    ]

    with open(entities_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=entity_fieldnames)
        writer.writeheader()
        writer.writerows(entities)

    print(f"✓ Đã xuất thành công: {entities_csv_path}")

    # 4. Read and build outputs/relations.csv
    relations = []
    orphan_references = []

    with open(relationships_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            src_id = row["source_id"]
            tgt_id = row["target_id"]
            rel_type = row["relationship_type"]

            # Check orphan references against entity_ids
            is_src_valid = src_id in entity_ids
            is_tgt_valid = tgt_id in entity_ids

            if not is_src_valid or not is_tgt_valid:
                orphan_references.append({
                    "row": i,
                    "source_id": src_id,
                    "target_id": tgt_id,
                    "rel_type": rel_type,
                    "source_valid": is_src_valid,
                    "target_valid": is_tgt_valid
                })

            relations.append({
                "source_id": src_id,
                "relationship_type": rel_type,
                "target_id": tgt_id,
                "source": row.get("source", ""),
                "evidence_quote": row.get("evidence_quote", ""),
                "confidence": row.get("confidence", ""),
                "verification_status": row.get("verification_status", ""),
                "data_origin": row.get("data_origin", "")
            })

    relations_csv_path = output_dir / "relations.csv"
    relation_fieldnames = [
        "source_id", "relationship_type", "target_id", "source",
        "evidence_quote", "confidence", "verification_status", "data_origin"
    ]

    with open(relations_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=relation_fieldnames)
        writer.writeheader()
        writer.writerows(relations)

    print(f"✓ Đã xuất thành công: {relations_csv_path}")

    # 5. Report Summary
    print("\n" + "=" * 80)
    print("BÁO CÁO THỐNG KÊ CHUẨN HÓA DỮ LIỆU (ENTITIES & RELATIONS)")
    print("=" * 80)

    # Count entities by type
    type_counts = {}
    for e in entities:
        t = e["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\n1. THỐNG KÊ ENTITIES THEO TYPE:")
    for entity_type, count in type_counts.items():
        print(f"   - {entity_type}: {count} entities")
    print(f"   => TỔNG CỘNG ENTITIES: {len(entities)}")

    # Count relations by relationship_type
    rel_type_counts = {}
    for r in relations:
        rt = r["relationship_type"]
        rel_type_counts[rt] = rel_type_counts.get(rt, 0) + 1

    print("\n2. THỐNG KÊ RELATIONS THEO RELATIONSHIP_TYPE:")
    for rel_type, count in rel_type_counts.items():
        print(f"   - {rel_type}: {count} relations")
    print(f"   => TỔNG CỘNG RELATIONS: {len(relations)}")

    # Report Orphan References
    print("\n3. KIỂM TRA ORPHAN REFERENCES (Khóa tham chiếu bị thiếu):")
    if orphan_references:
        print(f"   ❌ PÁT HIỆN {len(orphan_references)} ORPHAN REFERENCE(S):")
        for orphan in orphan_references:
            print(f"      Dòng {orphan['row']}: source_id='{orphan['source_id']}' (hợp lệ: {orphan['source_valid']}), target_id='{orphan['target_id']}' (hợp lệ: {orphan['target_valid']}) trong quan hệ '{orphan['rel_type']}'")
    else:
        print("   ✓ HOÀN HẢO: Không có orphan reference nào! Tất cả source_id và target_id đều tồn tại trong entities.csv.")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    build()
