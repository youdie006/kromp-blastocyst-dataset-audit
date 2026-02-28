#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import struct
from collections import Counter, defaultdict
from pathlib import Path


def png_size(path: Path):
    with path.open("rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not PNG: {path}")
        length = struct.unpack(">I", f.read(4))[0]
        chunk = f.read(4)
        if chunk != b"IHDR":
            raise ValueError(f"Missing IHDR: {path}")
        data = f.read(length)
        width, height = struct.unpack(">II", data[:8])
        return width, height


def quantile(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    idx = int(round((len(s) - 1) * q))
    return s[idx]


def make_concat_list(paths, out_txt: Path):
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    with out_txt.open("w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{p}'\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True, help="master_final_clean.csv")
    ap.add_argument("--images-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    master = Path(args.master)
    images_dir = Path(args.images_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with master.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    # Basic counters
    split_counts = Counter(r["split"] for r in rows)
    clinical_rows = [r for r in rows if r["has_clinical"] == "1"]
    lb_counts = Counter(r["LB"] for r in clinical_rows)

    # Patient-level counts
    patient_counter = Counter(r["patient_id"] for r in rows if r["patient_id"] != "")
    imgs_per_patient = list(patient_counter.values())

    # Image metadata scan
    inventory = []
    dim_counter = Counter()
    sizes = []
    missing_files = []

    for r in rows:
        img_name = r["image"]
        p = images_dir / img_name
        if not p.exists():
            missing_files.append(img_name)
            continue
        w, h = png_size(p)
        sz = p.stat().st_size
        dim_counter[f"{w}x{h}"] += 1
        sizes.append(sz)
        inventory.append([
            img_name,
            r["patient_id"],
            r["split"],
            r["has_clinical"],
            r.get("LB", ""),
            w,
            h,
            sz,
        ])

    # write inventory csv
    inv_csv = out_dir / "image_inventory_stats.csv"
    with inv_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["image", "patient_id", "split", "has_clinical", "LB", "width", "height", "file_size_bytes"])
        w.writerows(inventory)

    # Sampling for figure grids
    rng = random.Random(args.seed)

    all_images = [str(images_dir / r["image"]) for r in rows if (images_dir / r["image"]).exists()]
    sample_all = rng.sample(all_images, min(64, len(all_images)))

    lb1 = [str(images_dir / r["image"]) for r in clinical_rows if r.get("LB", "") == "1" and (images_dir / r["image"]).exists()]
    lb0 = [str(images_dir / r["image"]) for r in clinical_rows if r.get("LB", "") == "0" and (images_dir / r["image"]).exists()]
    sample_lb1 = rng.sample(lb1, min(64, len(lb1)))
    sample_lb0 = rng.sample(lb0, min(64, len(lb0)))

    lists_dir = out_dir / "figures" / "lists"
    make_concat_list(sample_all, lists_dir / "sample_all_64.txt")
    make_concat_list(sample_lb1, lists_dir / "sample_lb1_64.txt")
    make_concat_list(sample_lb0, lists_dir / "sample_lb0_64.txt")

    report = {
        "n_rows_master": len(rows),
        "n_images_found": len(inventory),
        "n_missing_files": len(missing_files),
        "split_counts": dict(split_counts),
        "clinical_rows": len(clinical_rows),
        "lb_counts": dict(lb_counts),
        "patient_count": len(patient_counter),
        "images_per_patient": {
            "min": min(imgs_per_patient) if imgs_per_patient else None,
            "p50": quantile(imgs_per_patient, 0.5),
            "p90": quantile(imgs_per_patient, 0.9),
            "max": max(imgs_per_patient) if imgs_per_patient else None,
            "mean": round(sum(imgs_per_patient) / len(imgs_per_patient), 3) if imgs_per_patient else None,
        },
        "resolution_top": dim_counter.most_common(10),
        "file_size_bytes": {
            "min": min(sizes) if sizes else None,
            "p50": quantile(sizes, 0.5),
            "p90": quantile(sizes, 0.9),
            "p95": quantile(sizes, 0.95),
            "max": max(sizes) if sizes else None,
            "mean": round(sum(sizes) / len(sizes), 2) if sizes else None,
        },
        "figure_list_files": {
            "all_64": str(lists_dir / "sample_all_64.txt"),
            "lb1_64": str(lists_dir / "sample_lb1_64.txt"),
            "lb0_64": str(lists_dir / "sample_lb0_64.txt"),
        },
    }

    with (out_dir / "rich_image_analysis_summary.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # markdown report
    md = []
    md.append("# Rich Image Analysis Report (Kromp Dataset)")
    md.append("")
    md.append("## Summary")
    md.append(f"- master rows: {report['n_rows_master']}")
    md.append(f"- image files found: {report['n_images_found']}")
    md.append(f"- missing files: {report['n_missing_files']}")
    md.append(f"- split counts: {report['split_counts']}")
    md.append(f"- clinical rows: {report['clinical_rows']}")
    md.append(f"- LB counts: {report['lb_counts']}")
    md.append("")
    md.append("## Patient-level distribution")
    for k, v in report["images_per_patient"].items():
        md.append(f"- images_per_patient_{k}: {v}")
    md.append("")
    md.append("## Resolution (top)")
    for k, v in report["resolution_top"]:
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## File size (bytes)")
    for k, v in report["file_size_bytes"].items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Generated figure list files")
    md.append(f"- all: `{report['figure_list_files']['all_64']}`")
    md.append(f"- LB=1: `{report['figure_list_files']['lb1_64']}`")
    md.append(f"- LB=0: `{report['figure_list_files']['lb0_64']}`")
    md.append("")
    md.append("## Notes")
    md.append("- Contact-sheet figure PNGs are generated separately via ffmpeg from the list files.")

    with (out_dir / "Rich_Image_Analysis_Report.md").open("w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
