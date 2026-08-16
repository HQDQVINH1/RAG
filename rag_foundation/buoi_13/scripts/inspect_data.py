import csv
import sys
from pathlib import Path

# Đảm bảo in UTF-8 không bị lỗi trên Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def inspect():
    # Target directory relative to script or execution directory
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    files = {
        "risk_profiles_seed.csv": {
            "path": data_dir / "risk_profiles_seed.csv",
            "pk": ["id"],
            "fk": {"owner_unit_id": "Unit (Master data - CHƯA CÓ)"}
        },
        "controls_seed.csv": {
            "path": data_dir / "controls_seed.csv",
            "pk": ["id"],
            "fk": {"owner_role_id": "Role (Master data - CHƯA CÓ)"}
        },
        "risk_events_seed.csv": {
            "path": data_dir / "risk_events_seed.csv",
            "pk": ["id"],
            "fk": {"risk_id": "risk_profiles_seed.csv (id)"}
        },
        "relationships_seed.csv": {
            "path": data_dir / "relationships_seed.csv",
            "pk": ["source_id", "relationship_type", "target_id"],
            "fk": {
                "source_id": "controls_seed.csv / risk_profiles_seed.csv",
                "target_id": "risk_profiles_seed.csv / risk_events_seed.csv"
            }
        }
    }

    print("=" * 80)
    print("BÁO CÁO KIỂM TRA DỮ LIỆU SEED (INSPECT DATA REPORT)")
    print("=" * 80)

    loaded_ids = {}

    for fname, info in files.items():
        filepath = info["path"]
        print(f"\n--- FILE: {fname} ---")
        if not filepath.exists():
            print(f"ERROR: File không tồn tại tại {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames
            rows = list(reader)

        row_count = len(rows)
        print(f"- Path: {filepath}")
        print(f"- Số dòng dữ liệu (Rows): {row_count}")
        print(f"- Tên các cột ({len(columns)} cột): {', '.join(columns)}")
        print(f"- Khóa chính dự kiến: {', '.join(info['pk'])}")

        # Track IDs for FK verification
        if fname in ["risk_profiles_seed.csv", "controls_seed.csv", "risk_events_seed.csv"]:
            ids = [r["id"] for r in rows if "id" in r]
            loaded_ids[fname] = set(ids)

        # Check Nulls
        null_counts = {col: 0 for col in columns}
        for r in rows:
            for col in columns:
                val = r[col]
                if val is None or val.strip() == "":
                    null_counts[col] += 1
        
        nulls_filtered = {k: v for k, v in null_counts.items() if v > 0}
        print(f"- Số giá trị NULL/Rỗng theo cột: {nulls_filtered if nulls_filtered else 'Không có (0 null)'}")

        # Check Duplicates (by PK)
        pk_cols = info["pk"]
        seen_pks = set()
        duplicate_count = 0
        for r in rows:
            pk_val = tuple(r[c] for c in pk_cols)
            if pk_val in seen_pks:
                duplicate_count += 1
            else:
                seen_pks.add(pk_val)
        print(f"- Trùng lặp (Duplicates according to PK): {duplicate_count}")

        # Specific analysis per file
        if fname == "relationships_seed.csv":
            rel_types = set(r["relationship_type"] for r in rows)
            print(f"- Các loại relationship_type: {list(rel_types)}")
            
            # Count by type
            rel_type_counts = {}
            for r in rows:
                t = r["relationship_type"]
                rel_type_counts[t] = rel_type_counts.get(t, 0) + 1
            print(f"  + Thống kê số lượng theo type: {rel_type_counts}")

    print("\n" + "=" * 80)
    print("KIỂM TRA KHÓA THAM CHIẾU VÀ LIÊN KẾT (FOREIGN KEY & REFERENCE INTEGRITY)")
    print("=" * 80)

    # Check risk_events_seed -> risk_profiles_seed
    with open(files["risk_events_seed.csv"]["path"], "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        missing_risk_ids = [r["risk_id"] for r in rows if r["risk_id"] not in loaded_ids["risk_profiles_seed.csv"]]
        print(f"\n1. risk_events_seed.csv -> risk_profiles_seed.csv:")
        print(f"   - risk_id bị thiếu trong risk_profiles: {missing_risk_ids if missing_risk_ids else 'Không có (Tất cả hợp lệ)'}")

    # Check relationships_seed
    with open(files["relationships_seed.csv"]["path"], "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
        missing_sources = []
        missing_targets = []

        mitigates_sources = set()
        mitigates_targets = set()
        observed_sources = set()
        observed_targets = set()

        for r in rows:
            rel_type = r["relationship_type"]
            src = r["source_id"]
            tgt = r["target_id"]

            if rel_type == "MITIGATES":
                mitigates_sources.add(src)
                mitigates_targets.add(tgt)
                if src not in loaded_ids["controls_seed.csv"]:
                    missing_sources.append((src, rel_type))
                if tgt not in loaded_ids["risk_profiles_seed.csv"]:
                    missing_targets.append((tgt, rel_type))
            elif rel_type == "OBSERVED_AS":
                observed_sources.add(src)
                observed_targets.add(tgt)
                if src not in loaded_ids["risk_profiles_seed.csv"]:
                    missing_sources.append((src, rel_type))
                if tgt not in loaded_ids["risk_events_seed.csv"]:
                    missing_targets.append((tgt, rel_type))

        print(f"\n2. relationships_seed.csv:")
        print(f"   - source_id không tồn tại: {missing_sources if missing_sources else 'Không có (Tất cả hợp lệ)'}")
        print(f"   - target_id không tồn tại: {missing_targets if missing_targets else 'Không có (Tất cả hợp lệ)'}")

    print("\n" + "=" * 80)
    print("PHÁT HIỆN DỮ LIỆU THIẾU THỰC TẾ (MISSING MASTER DATA & UNCOVERED NODES)")
    print("=" * 80)

    # Owner units check
    with open(files["risk_profiles_seed.csv"]["path"], "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        units = set(r["owner_unit_id"] for r in rows if r["owner_unit_id"])
        print(f"\n1. Danh sách owner_unit_id trong risk_profiles: {sorted(list(units))}")
        print("   => CẢNH BÁO: Chưa có master data file cho Đơn vị (e.g. units_seed.csv)")

    # Owner roles check
    with open(files["controls_seed.csv"]["path"], "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        roles = set(r["owner_role_id"] for r in rows if r["owner_role_id"])
        print(f"\n2. Danh sách owner_role_id trong controls: {sorted(list(roles))}")
        print("   => CẢNH BÁO: Chưa có master data file cho Vai trò (e.g. roles_seed.csv)")

    # Uncovered risks check
    all_risks = loaded_ids["risk_profiles_seed.csv"]
    unmitigated_risks = all_risks - mitigates_targets
    unobserved_risks = all_risks - observed_sources

    print(f"\n3. Rủi ro (RuiRo) không có Kiểm soát (MITIGATES): {sorted(list(unmitigated_risks)) if unmitigated_risks else 'Không có'}")
    print(f"4. Rủi ro (RuiRo) không có Sự kiện (OBSERVED_AS): {sorted(list(unobserved_risks)) if unobserved_risks else 'Không có'}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    inspect()
