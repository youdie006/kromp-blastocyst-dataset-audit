#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path


def read_semicolon_csv(path: Path):
    encodings = ["utf-8-sig", "cp1252", "latin-1"]
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                rows = list(csv.reader(f, delimiter=";"))
            header = rows[0]
            data = [r for r in rows[1:] if any(c.strip() for c in r)]
            return header, data
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError(f"Failed to read CSV: {path}")


def resolve_name(name: str, image_set: set[str]) -> tuple[str, str]:
    name = name.strip()
    if name in image_set:
        return name, "exact"

    m = re.match(r"^(\d+)_(\d+)\.png$", name)
    if not m:
        return "", "unparsed"

    a = int(m.group(1))
    b = int(m.group(2))

    candidates = [
        f"{a}_{b}.png",
        f"{a}_{b:02d}.png",
        f"{a:04d}_{b}.png",
        f"{a:04d}_{b:02d}.png",
    ]

    # unique-preserving
    seen = set()
    uniq = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)

    for c in uniq:
        if c in image_set:
            return c, "normalized"

    return "", "missing"


def patient_id_from_image(name: str) -> str:
    m = re.match(r"^(\d+)_\d+\.png$", name)
    return m.group(1) if m else ""


def write_csv(path: Path, header: list[str], rows: list[list[str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    zpath = Path(args.zip)
    out = Path(args.out)
    extracted = out / "raw" / "extracted"
    manifests = out / "prepared" / "manifests"
    reports = out / "reports"

    extracted.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    # Extract only if key file missing
    key_file = extracted / "Gardner_train_silver.csv"
    if not key_file.exists():
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(extracted)

    image_dir = extracted / "Images"
    image_files = sorted(p.name for p in image_dir.glob("*.png"))
    image_set = set(image_files)

    train_h, train_rows_raw = read_semicolon_csv(extracted / "Gardner_train_silver.csv")
    test_h, test_rows_raw = read_semicolon_csv(extracted / "Gardner_test_gold_onlyGardnerScores.csv")
    clin_h, clin_rows_raw = read_semicolon_csv(extracted / "Clincial_annotations.csv")

    # Normalize train
    train_rows = []
    train_missing = []
    for r in train_rows_raw:
        img_raw = r[0].strip()
        img, status = resolve_name(img_raw, image_set)
        if not img:
            train_missing.append(img_raw)
            continue
        train_rows.append([
            img_raw, img, status,
            r[1].strip(), r[2].strip(), r[3].strip(),
            str(image_dir / img),
            patient_id_from_image(img),
        ])

    # Normalize test
    test_rows = []
    test_missing = []
    for r in test_rows_raw:
        # handle potential trailing empty column
        rr = r + [""] * (5 - len(r))
        img_raw = rr[0].strip()
        img, status = resolve_name(img_raw, image_set)
        if not img:
            test_missing.append(img_raw)
            continue
        test_rows.append([
            img_raw, img, status,
            rr[1].strip(), rr[2].strip(), rr[3].strip(),
            str(image_dir / img),
            patient_id_from_image(img),
        ])

    # Normalize clinical
    clin_rows = []
    clin_missing = []
    for r in clin_rows_raw:
        rr = r + [""] * (14 - len(r))
        img_raw = rr[0].strip()
        img, status = resolve_name(img_raw, image_set)
        if not img:
            clin_missing.append(img_raw)
            continue
        clin_rows.append([
            img_raw, img, status,
            rr[1].strip(), rr[2].strip(), rr[3].strip(), rr[4].strip(), rr[5].strip(),
            rr[6].strip(), rr[7].strip(), rr[8].strip(), rr[9].strip(), rr[10].strip(),
            rr[11].strip(), rr[12].strip(), rr[13].strip(),
            str(image_dir / img),
            patient_id_from_image(img),
        ])

    # Write manifest files
    write_csv(
        manifests / "gardner_train_silver_manifest.csv",
        [
            "image_original", "image_resolved", "name_resolution",
            "EXP_silver", "ICM_silver", "TE_silver",
            "image_path", "patient_id",
        ],
        train_rows,
    )

    write_csv(
        manifests / "gardner_test_gold_manifest.csv",
        [
            "image_original", "image_resolved", "name_resolution",
            "EXP_gold", "ICM_gold", "TE_gold",
            "image_path", "patient_id",
        ],
        test_rows,
    )

    write_csv(
        manifests / "clinical_manifest.csv",
        [
            "image_original", "image_resolved", "name_resolution",
            "Fond", "d", "EXP_silver", "ICM_silver", "TE_silver",
            "AMH", "Age", "Endo", "COC", "MII", "SS", "HA", "LB",
            "image_path", "patient_id",
        ],
        clin_rows,
    )

    # Build master table across all images
    train_map = {r[1]: r for r in train_rows}
    test_map = {r[1]: r for r in test_rows}
    clin_map = {r[1]: r for r in clin_rows}

    master_rows = []
    for img in image_files:
        tr = train_map.get(img)
        te = test_map.get(img)
        cl = clin_map.get(img)
        split = ""
        if tr:
            split = "train_silver"
        elif te:
            split = "test_gold"
        else:
            split = "unassigned"

        master_rows.append([
            img,
            str(image_dir / img),
            patient_id_from_image(img),
            split,
            tr[3] if tr else "", tr[4] if tr else "", tr[5] if tr else "",
            te[3] if te else "", te[4] if te else "", te[5] if te else "",
            cl[8] if cl else "", cl[9] if cl else "", cl[10] if cl else "",
            cl[11] if cl else "", cl[12] if cl else "",
            cl[13] if cl else "", cl[14] if cl else "", cl[15] if cl else "",
            "1" if cl else "0",
        ])

    write_csv(
        manifests / "master_table.csv",
        [
            "image",
            "image_path",
            "patient_id",
            "split",
            "EXP_silver",
            "ICM_silver",
            "TE_silver",
            "EXP_gold",
            "ICM_gold",
            "TE_gold",
            "AMH",
            "Age",
            "Endo",
            "COC",
            "MII",
            "SS",
            "HA",
            "LB",
            "has_clinical",
        ],
        master_rows,
    )

    summary = {
        "paths": {
            "zip": str(zpath),
            "extracted": str(extracted),
            "manifests": str(manifests),
        },
        "counts": {
            "images_total": len(image_files),
            "train_rows_raw": len(train_rows_raw),
            "train_rows_resolved": len(train_rows),
            "train_rows_missing": len(train_missing),
            "test_rows_raw": len(test_rows_raw),
            "test_rows_resolved": len(test_rows),
            "test_rows_missing": len(test_missing),
            "clinical_rows_raw": len(clin_rows_raw),
            "clinical_rows_resolved": len(clin_rows),
            "clinical_rows_missing": len(clin_missing),
            "master_rows": len(master_rows),
            "clinical_overlap_train": len(set(train_map) & set(clin_map)),
            "clinical_overlap_test": len(set(test_map) & set(clin_map)),
        },
        "missing_examples": {
            "train": train_missing[:20],
            "test": test_missing[:20],
            "clinical": clin_missing[:20],
        },
    }

    with open(reports / "prepare_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # human-readable markdown summary
    md = []
    md.append("# Kromp Dataset Preparation Summary")
    md.append("")
    md.append("## Counts")
    for k, v in summary["counts"].items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Notes")
    if clin_missing:
        md.append(f"- clinical missing rows after normalization: {len(clin_missing)}")
    else:
        md.append("- all clinical filenames were resolved to existing images (exact or normalized).")
    md.append("- master table includes all 2,344 images with split and optional clinical columns.")

    with open(reports / "prepare_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
