#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import subprocess
from pathlib import Path


def ffmpeg_tile(list_file: Path, out_file: Path):
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vf",
        "scale=224:168,tile=4x4:padding=2:margin=2",
        "-frames:v",
        "1",
        "-q:v",
        "4",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)


def write_concat_list(paths: list[Path], out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{p}'\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--images-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    master = Path(args.master)
    images_dir = Path(args.images_dir)
    out_dir = Path(args.out_dir)
    figures_dir = out_dir / "figures"
    lists_dir = figures_dir / "lists"

    with master.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    def valid_paths(rows_subset):
        out = []
        for r in rows_subset:
            p = images_dir / r["image"]
            if p.exists():
                out.append(p)
        return out

    groups = {
        "preview_random_16": rows,
        "preview_train_16": [r for r in rows if r["split"] == "train_silver"],
        "preview_test_16": [r for r in rows if r["split"] == "test_gold"],
        "preview_lb1_16": [r for r in rows if r["has_clinical"] == "1" and r.get("LB", "") == "1"],
        "preview_lb0_16": [r for r in rows if r["has_clinical"] == "1" and r.get("LB", "") == "0"],
    }

    for k in ["0", "1", "2", "3", "4"]:
        groups[f"preview_exp{k}_16"] = [r for r in rows if r.get("EXP_silver", "") == k]
    for k in ["0", "1", "2", "3"]:
        groups[f"preview_icm{k}_16"] = [r for r in rows if r.get("ICM_silver", "") == k]
    for k in ["0", "1", "2", "3"]:
        groups[f"preview_te{k}_16"] = [r for r in rows if r.get("TE_silver", "") == k]

    rng = random.Random(args.seed)
    summary = {}

    for name, rows_subset in groups.items():
        candidates = valid_paths(rows_subset)
        if not candidates:
            continue

        # deterministic sampling
        cands = sorted(str(p) for p in candidates)
        sample_n = min(16, len(cands))
        sampled = rng.sample(cands, sample_n)
        sampled_paths = [Path(x) for x in sampled]

        list_file = lists_dir / f"{name}.txt"
        out_img = figures_dir / f"{name}.jpg"
        write_concat_list(sampled_paths, list_file)
        ffmpeg_tile(list_file, out_img)

        summary[name] = {
            "population": len(cands),
            "sample_n": sample_n,
            "list_file": str(list_file),
            "image_file": str(out_img),
        }

    with (out_dir / "readme_visual_panels.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
