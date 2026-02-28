# Verification Report: Kromp Blastocyst Dataset (Public Benchmark)

**Date:** 2026-02-28  
**Author:** Independent audit (public-source verification)  
**Language:** English

## 1) Objective
To verify the following claim block used in thesis planning:

- 2,344 blastocyst images
- 837 patients
- Gardner labels: Expansion / ICM / TE
- Silver-train / Gold-test structure
- Clinical-outcome subset: 752 fresh transfer cases
- Clinical outcomes include biochemical pregnancy, clinical pregnancy, live birth
- Clinical variables include Age, AMH, Endometrium height (Endo)
- Split/data generation logic code is publicly available on GitHub

## 2) Sources checked
1. **Paper (Scientific Data)**  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC10175281/
2. **Dataset DOI (figshare)**  
   https://doi.org/10.6084/m9.figshare.20123153.v3  
   (API endpoint used for metadata: `https://api.figshare.com/v2/articles/20123153`)
3. **Code repository for split/processing logic**  
   https://github.com/software-competence-center-hagenberg/Blastocyst-Dataset
4. **Downloaded dataset artifact**  
   `Blastocyst_Dataset.zip` from figshare (`files/39348899`, CC BY 4.0)

## 3) Verification summary (claim-by-claim)

| Claim | Status | Evidence |
|---|---|---|
| 2,344 blastocyst images | **Confirmed** | Paper states 2,344 blastocysts in Methods. Zip audit counted **2,344 PNG files** under `Images/`. |
| 837 patients | **Confirmed (paper-level)** | Paper Methods states 837 patients. This is not directly re-countable from public CSVs because explicit patient-ID linkage is not provided in the downloaded split tables. |
| Gardner labels (Expansion/ICM/TE) | **Confirmed** | Paper and CSV headers include `EXP`, `ICM`, `TE` (silver/gold variants). |
| Silver-train / Gold-test structure | **Confirmed** | Paper describes silver-standard train and gold-standard test; zip audit counted `Gardner_train_silver.csv` = **2,044** rows and `Gardner_test_gold_onlyGardnerScores.csv` = **300** rows (sum = 2,344). |
| Clinical subset = 752 fresh transfer cases | **Partially confirmed / discrepancy found** | Paper text states **752** fresh transfer cases. Downloaded `Clincial_annotations.csv` contains **754** non-empty rows. One filename (`187_1.png`) does not match an image filename in `Images/`. This indicates a minor version/data-quality discrepancy that should be documented before modeling. |
| Clinical outcomes include biochemical/clinical pregnancy/live birth | **Confirmed** | Clinical file includes columns `SS` (biochemical pregnancy), `HA` (clinical heart activity), `LB` (live birth). Paper Table/description aligns with this. |
| Clinical variables include Age, AMH, Endo | **Confirmed** | Clinical file header includes `Age`, `AMH`, `Endo`; paper also lists these variables. |
| Data creation and split logic code on GitHub | **Confirmed** | GitHub repository contains split/evaluation scripts including `create_testset.py`, `combine_testset_annotations.py`, and metric scripts. |

## 4) Additional technical notes

1. **License**: figshare metadata reports **CC BY 4.0**.
2. **Clinical CSV filename typo** in archive: `Clincial_annotations.csv` (spelling as published).
3. **Potential data-cleaning requirement** before experiments:
   - Resolve mismatched image name (`187_1.png` vs expected naming style in image folder).
   - Reconcile the 752 (paper) vs 754 (file rows) difference in the data card.

## 5) Reproducibility

Verification script in this repo:

```bash
python scripts/verify_kromp_dataset.py --zip /path/to/Blastocyst_Dataset.zip
```

Script output used for this report:
- `results/verification_output.json`

## 6) Practical conclusion for thesis use

The benchmark structure and labels are suitable for the planned thesis direction (multimodal outcome prediction + reliability analysis).  
However, the clinical-subset count discrepancy should be explicitly handled in the **Data Card** and **Methods** section (inclusion/exclusion logic and final N after cleaning).
