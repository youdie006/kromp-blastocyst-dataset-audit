#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

MONTH_MAP = {
    "Jan": 1,
    "Jän": 1,
    "Feb": 2,
    "Mär": 3,
    "Mar": 3,
    "Apr": 4,
    "Mai": 5,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Okt": 10,
    "Oct": 10,
    "Nov": 11,
    "Dez": 12,
    "Dec": 12,
}

RE_NUM = re.compile(r"^\d+(?:\.\d+)?$")
RE_MONTH_PREFIX = re.compile(r"^([A-Za-zÄÖÜäöü]+)\.(\d{1,2})$")
RE_MONTH_SUFFIX = re.compile(r"^(\d{1,2})\.([A-Za-zÄÖÜäöü]+)$")


def parse_int(v: str):
    v = (v or "").strip()
    if v == "":
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def parse_float(v: str):
    v = (v or "").strip()
    if v == "":
        return None
    v = v.replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def parse_amh(v: str):
    raw = (v or "").strip()
    if raw == "":
        return None, "missing"

    v2 = raw.replace(",", ".")
    if RE_NUM.match(v2):
        return float(v2), "numeric"

    m = RE_MONTH_PREFIX.match(raw)
    if m and m.group(1) in MONTH_MAP:
        month = MONTH_MAP[m.group(1)]
        frac = m.group(2).zfill(2)
        return float(f"{month}.{frac}"), "month_prefix"

    m = RE_MONTH_SUFFIX.match(raw)
    if m and m.group(2) in MONTH_MAP:
        integer = int(m.group(1))
        month = MONTH_MAP[m.group(2)]
        return float(f"{integer}.{month:02d}"), "month_suffix"

    return None, "unparsed"


def parse_split_labels(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    imgs = [r["image_resolved"] for r in rows]
    cnt = Counter(imgs)
    duplicates = {k: v for k, v in cnt.items() if v > 1}
    return set(imgs), duplicates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Kromp_Prepared_Data base path")
    args = ap.parse_args()

    base = Path(args.base)
    manifests = base / "prepared" / "manifests"
    final_dir = base / "prepared" / "final"
    reports = base / "reports"
    final_dir.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    train_set, train_dups = parse_split_labels(manifests / "gardner_train_silver_manifest.csv")
    test_set, test_dups = parse_split_labels(manifests / "gardner_test_gold_manifest.csv")

    with (manifests / "master_table.csv").open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    amh_status_counter = Counter()
    lb_counter = Counter()

    for r in rows:
        has_clinical = r["has_clinical"] == "1"

        amh_clean, amh_status = parse_amh(r["AMH"])
        age_clean = parse_int(r["Age"])
        endo_clean = parse_float(r["Endo"])
        coc_clean = parse_int(r["COC"])
        mii_clean = parse_int(r["MII"])
        ss_clean = parse_int(r["SS"])
        ha_clean = parse_int(r["HA"])
        lb_clean = parse_int(r["LB"])

        if has_clinical:
            amh_status_counter[amh_status] += 1
            lb_counter[str(lb_clean)] += 1

        split = r["split"]
        split_valid = 1 if split in {"train_silver", "test_gold"} else 0

        has_multimodal_core = 1 if has_clinical and (age_clean is not None) and (endo_clean is not None) and (lb_clean is not None) else 0
        has_multimodal_full = 1 if has_clinical and (age_clean is not None) and (endo_clean is not None) and (amh_clean is not None) and (lb_clean is not None) else 0

        out_rows.append({
            "image": r["image"],
            "image_path": r["image_path"],
            "patient_id": r["patient_id"],
            "split": split,
            "split_valid": str(split_valid),
            "has_clinical": r["has_clinical"],
            "EXP_silver": r["EXP_silver"],
            "ICM_silver": r["ICM_silver"],
            "TE_silver": r["TE_silver"],
            "EXP_gold": r["EXP_gold"],
            "ICM_gold": r["ICM_gold"],
            "TE_gold": r["TE_gold"],
            "AMH_raw": r["AMH"],
            "AMH_clean": "" if amh_clean is None else f"{amh_clean:.2f}",
            "AMH_clean_status": amh_status,
            "Age": "" if age_clean is None else str(age_clean),
            "Endo": "" if endo_clean is None else f"{endo_clean:.2f}",
            "COC": "" if coc_clean is None else str(coc_clean),
            "MII": "" if mii_clean is None else str(mii_clean),
            "SS": "" if ss_clean is None else str(ss_clean),
            "HA": "" if ha_clean is None else str(ha_clean),
            "LB": "" if lb_clean is None else str(lb_clean),
            "has_multimodal_core": str(has_multimodal_core),
            "has_multimodal_full": str(has_multimodal_full),
        })

    # write master final
    fieldnames = list(out_rows[0].keys()) if out_rows else []
    with (final_dir / "master_final_clean.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    # write clinical final
    clinical_rows = [r for r in out_rows if r["has_clinical"] == "1"]
    with (final_dir / "clinical_final_clean.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clinical_rows)

    split_counter = Counter(r["split"] for r in out_rows if r["has_clinical"] == "1")

    amh_clean_vals = [float(r["AMH_clean"]) for r in clinical_rows if r["AMH_clean"] != ""]
    out_of_range = [x for x in amh_clean_vals if (x < 0.08 or x > 19.40)]

    summary = {
        "rows": {
            "master_total": len(out_rows),
            "clinical_total": len(clinical_rows),
            "split_valid_total": sum(1 for r in out_rows if r["split_valid"] == "1"),
            "split_unassigned_total": sum(1 for r in out_rows if r["split"] == "unassigned"),
            "clinical_split": dict(split_counter),
        },
        "split_quality": {
            "train_unique": len(train_set),
            "test_unique": len(test_set),
            "train_duplicates": train_dups,
            "test_duplicates": test_dups,
        },
        "clinical_cleaning": {
            "AMH_status": dict(amh_status_counter),
            "AMH_clean_non_missing": len(amh_clean_vals),
            "AMH_clean_missing": len(clinical_rows) - len(amh_clean_vals),
            "AMH_out_of_range_count": len(out_of_range),
            "AMH_min": min(amh_clean_vals) if amh_clean_vals else None,
            "AMH_max": max(amh_clean_vals) if amh_clean_vals else None,
            "LB_distribution": dict(lb_counter),
            "has_multimodal_core": sum(1 for r in clinical_rows if r["has_multimodal_core"] == "1"),
            "has_multimodal_full": sum(1 for r in clinical_rows if r["has_multimodal_full"] == "1"),
        },
    }

    with (reports / "final_cleaning_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    md = []
    md.append("# Kromp Final Cleaning Summary")
    md.append("")
    md.append("## Row-level summary")
    for k, v in summary["rows"].items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Split quality")
    md.append(f"- train_unique: {summary['split_quality']['train_unique']}")
    md.append(f"- test_unique: {summary['split_quality']['test_unique']}")
    md.append(f"- train_duplicates: {summary['split_quality']['train_duplicates']}")
    md.append(f"- test_duplicates: {summary['split_quality']['test_duplicates']}")
    md.append("")
    md.append("## Clinical cleaning")
    for k, v in summary["clinical_cleaning"].items():
        md.append(f"- {k}: {v}")

    with (reports / "final_cleaning_summary.md").open("w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
