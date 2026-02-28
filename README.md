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
