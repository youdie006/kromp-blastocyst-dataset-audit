# Kromp Blastocyst Dataset Audit

Independent verification notes for the public **Kromp blastocyst dataset** used in IVF AI research.

## Scope
This repository verifies key claims from:

- Paper: *An annotated human blastocyst dataset to benchmark deep learning architectures for in vitro fertilization*  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10175281/
- Data DOI (figshare): https://doi.org/10.6084/m9.figshare.20123153.v3
- Split/code repository: https://github.com/software-competence-center-hagenberg/Blastocyst-Dataset

## Key Result (short)
- The core structure is confirmed: 2,344 images and a 2,044/300 silver-train/gold-test split.
- Clinical fields (`Age`, `AMH`, `Endo`, `SS`, `HA`, `LB`) are present.
- A small discrepancy exists in the downloadable clinical CSV row count vs. the paper text (details in report).

See full report:
- [`results/Kromp_Dataset_Verification_Report.md`](results/Kromp_Dataset_Verification_Report.md)


## Quantitative Snapshot (from cleaned master)

| Metric | Value |
|---|---:|
| Total images | 2,344 |
| Split (train_silver / test_gold / unassigned) | 2,043 / 300 / 1 |
| Clinical rows | 754 |
| Live birth labels (LB=1 / LB=0) | 234 / 520 |
| Resolution | 512×384 (all images) |


## Reproducibility Script
Run:

```bash
python scripts/verify_kromp_dataset.py --zip /path/to/Blastocyst_Dataset.zip
```

The script inspects:
- image count in `Images/*.png`
- row counts in Gardner split files
- clinical file columns and row count
- filename consistency between clinical rows and image files
## Data Preparation (local build manifests)

In addition to structural verification, this repo now includes a reproducible preparation script:

```bash
python scripts/prepare_kromp_dataset.py --zip /path/to/Blastocyst_Dataset.zip --out /path/to/output_dir
```

It creates manifest CSV files for:
- Gardner silver-train split
- Gardner gold-test split
- Clinical subset
- Unified master table (all images)

Example output summaries are in:
- `results/prepare_summary_example.json`
- `results/prepare_summary_example.md`

> Note: the original figshare ZIP is not committed. Public PNG images are included under `data/images/`.

## Final Cleaning (clinical + split-quality audit)

A second-stage cleaning script is provided:

```bash
python scripts/final_clean_kromp.py --base /path/to/Kromp_Prepared_Data
```

It produces:
- `prepared/final/master_final_clean.csv`
- `prepared/final/clinical_final_clean.csv`
- `reports/final_cleaning_summary.json`
- `reports/final_cleaning_summary.md`

The script includes:
- AMH normalization for locale/date-like artifacts
- split-quality checks (duplicates/unassigned)
- multimodal-ready row flags


## Image Data Included in Repository

This repository now includes the public image set under:

- `data/images/` (2,344 PNG files)

The image source is the public figshare artifact associated with the Kromp dataset DOI:
- https://doi.org/10.6084/m9.figshare.20123153.v3

A richer image-level analysis is provided in:
- `results/rich_image_analysis/Rich_Image_Analysis_Report.md`
- `results/rich_image_analysis/figures/*.png`


## Visual EDA Gallery

The gallery below is designed to make the repository **immediately interpretable** (not just file-heavy).
All panels are random samples from the corresponding subset (seed-fixed).

### A) Overall / split / outcome panels

| Random (n=16) | Train Silver (n=16) | Test Gold (n=16) |
|---|---|---|
| <img src="results/rich_image_analysis/figures/preview_random_16.jpg" width="300"/> | <img src="results/rich_image_analysis/figures/preview_train_16.jpg" width="300"/> | <img src="results/rich_image_analysis/figures/preview_test_16.jpg" width="300"/> |

| Clinical LB=1 (n=16) | Clinical LB=0 (n=16) |
|---|---|
| <img src="results/rich_image_analysis/figures/preview_lb1_16.jpg" width="300"/> | <img src="results/rich_image_analysis/figures/preview_lb0_16.jpg" width="300"/> |

### B) Expansion (silver label) representative panels

| EXP=0 | EXP=1 | EXP=2 |
|---|---|---|
| <img src="results/rich_image_analysis/figures/preview_exp0_16.jpg" width="260"/> | <img src="results/rich_image_analysis/figures/preview_exp1_16.jpg" width="260"/> | <img src="results/rich_image_analysis/figures/preview_exp2_16.jpg" width="260"/> |

| EXP=3 | EXP=4 |
|---|---|
| <img src="results/rich_image_analysis/figures/preview_exp3_16.jpg" width="300"/> | <img src="results/rich_image_analysis/figures/preview_exp4_16.jpg" width="300"/> |

### C) ICM representative panels

| ICM=0 | ICM=1 | ICM=2 | ICM=3 |
|---|---|---|---|
| <img src="results/rich_image_analysis/figures/preview_icm0_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_icm1_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_icm2_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_icm3_16.jpg" width="220"/> |

### D) TE representative panels

| TE=0 | TE=1 | TE=2 | TE=3 |
|---|---|---|---|
| <img src="results/rich_image_analysis/figures/preview_te0_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_te1_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_te2_16.jpg" width="220"/> | <img src="results/rich_image_analysis/figures/preview_te3_16.jpg" width="220"/> |

### E) Larger 64-image contact sheets

- `results/rich_image_analysis/figures/sample_all_64_grid.png`
- `results/rich_image_analysis/figures/sample_lb1_64_grid.png`
- `results/rich_image_analysis/figures/sample_lb0_64_grid.png`

### Notes
- These panels are for exploratory visualization and reproducibility documentation.
- They are **not** a clinical decision aid and should not be interpreted as medical guidance.

## How to Read the Gallery (Practical Guide)
1. **Split panels** (`train` vs `test`) show whether image appearance is visibly consistent across splits.
2. **Outcome panels** (`LB=1` vs `LB=0`) are for qualitative comparison only; they are not proof of causal morphology differences.
3. **EXP/ICM/TE panels** show class diversity and class scarcity at a glance (important for model reliability and calibration).

## Descriptive Insights from Current Analysis

### 1) Outcome imbalance is substantial
- Clinical subset size: **754**
- Live birth positive rate: **31.0%** (234/754)
- Implication: AUROC alone is insufficient; report **AUPRC**, calibration, and class-aware metrics.

### 2) Clinical data are mostly in train split
- Clinical rows by split: **653 train / 100 test / 1 unassigned**
- Implication: keep strict protocol and report uncertainty/CI because evaluation set for outcome is relatively small.

### 3) Morphology class distribution is skewed
(Clinical subset, silver labels)

| Label family | Most frequent classes | Rare classes |
|---|---|---|
| EXP | EXP=3 (n=380) | EXP=0 (n=43), EXP=4 (n=63) |
| ICM | ICM=0 (n=474) | ICM=2 (n=1) |
| TE | TE=0 (n=414) | TE=2 (n=12) |

- Implication: rare classes can destabilize ranking and calibration; use stratified reporting + confidence intervals.

### 4) LB rate differs by morphology class, but small-n classes are fragile

| Group | n | LB rate |
|---|---:|---:|
| EXP=4 | 63 | 39.7% |
| EXP=3 | 380 | 32.9% |
| EXP=2 | 111 | 26.1% |
| EXP=1 | 56 | 25.0% |
| EXP=0 | 43 | 34.9% |

| Group | n | LB rate |
|---|---:|---:|
| ICM=0 | 474 | 32.5% |
| ICM=1 | 79 | 31.6% |
| ICM=3 | 99 | 29.3% |
| ICM=2 | 1 | 0.0% *(not interpretable)* |

| Group | n | LB rate |
|---|---:|---:|
| TE=0 | 414 | 33.6% |
| TE=1 | 128 | 31.3% |
| TE=3 | 99 | 29.3% |
| TE=2 | 12 | 0.0% *(very small n)* |

- Implication: observed trends should be treated as **descriptive**; avoid strong biological claims from low-support bins.

### 5) Missingness in key clinical variables is non-trivial
- Endometrium (`Endo`) missing: **20.7%**
- AMH missing after normalization: **21.9%**
- Implication: compare complete-case vs imputed/missing-indicator strategies and report sensitivity.

### 6) Data quality flags remain important for reproducibility
- One duplicate in train split source (`838_02.png`)
- One unassigned image in master (`846_01.png`)
- Implication: keep these checks in preprocessing and document inclusion/exclusion in thesis Methods.

## Recommended Next Analysis Steps
1. Add **patient-grouped bootstrap CI** for AUROC/AUPRC/ECE.
2. Report **risk-coverage** and **selective prediction** under class imbalance.
3. Add **per-class reliability tables** (especially for rare EXP/ICM/TE bins).
4. Run sensitivity analysis for missing clinical variables (Endo/AMH).

