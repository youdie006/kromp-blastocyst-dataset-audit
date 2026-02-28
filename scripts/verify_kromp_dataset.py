#!/usr/bin/env python3
"""Verify basic structural properties of the Kromp blastocyst dataset zip."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from pathlib import Path


def parse_semicolon_csv(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as f:
        text = f.read().decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    header = rows[0]
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    return header, data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="Path to Blastocyst_Dataset.zip")
    args = ap.parse_args()

    zpath = Path(args.zip)
    if not zpath.exists():
        raise SystemExit(f"Zip not found: {zpath}")

    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()

        image_files = [n for n in names if n.startswith("Images/") and n.lower().endswith(".png")]
        image_basenames = {n.split("/", 1)[1] for n in image_files}

        # Gardner split files
        g_train_h, g_train_rows = parse_semicolon_csv(zf, "Gardner_train_silver.csv")
        g_test_h, g_test_rows = parse_semicolon_csv(zf, "Gardner_test_gold_onlyGardnerScores.csv")

        # Clinical annotations
        c_h, c_rows = parse_semicolon_csv(zf, "Clincial_annotations.csv")
        clinical_images = [r[0] for r in c_rows if r]

        missing_in_images = sorted(set(clinical_images) - image_basenames)
        name_pattern = re.compile(r"^\d+_\d+\.png$")
        nonstandard_names = [x for x in clinical_images if not name_pattern.match(x)]

        result = {
            "zip_path": str(zpath),
            "counts": {
                "images_png": len(image_files),
                "gardner_train_silver_rows": len(g_train_rows),
                "gardner_test_gold_rows": len(g_test_rows),
                "sum_train_plus_test": len(g_train_rows) + len(g_test_rows),
                "clinical_rows": len(c_rows),
            },
            "headers": {
                "gardner_train_silver": g_train_h,
                "gardner_test_gold_only": g_test_h,
                "clinical": c_h,
            },
            "clinical_checks": {
                "required_columns_present": {
                    k: (k in c_h) for k in ["Age", "AMH", "Endo", "SS", "HA", "LB"]
                },
                "clinical_images_unique": len(set(clinical_images)),
                "clinical_image_names_missing_in_image_folder": missing_in_images,
                "nonstandard_name_examples": nonstandard_names[:10],
            },
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
