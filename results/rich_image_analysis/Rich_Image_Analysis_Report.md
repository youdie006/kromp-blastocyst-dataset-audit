# Rich Image Analysis Report (Kromp Dataset)

## Summary
- master rows: 2344
- image files found: 2344
- missing files: 0
- split counts: {'train_silver': 2043, 'test_gold': 300, 'unassigned': 1}
- clinical rows: 754
- LB counts: {'0': 520, '1': 234}

## Patient-level distribution
- images_per_patient_min: 1
- images_per_patient_p50: 2
- images_per_patient_p90: 5
- images_per_patient_max: 11
- images_per_patient_mean: 2.754

## Resolution (top)
- 512x384: 2344

## File size (bytes)
- min: 206896
- p50: 264988
- p90: 291677
- p95: 299705
- max: 323565
- mean: 266242.62

## Generated figure list files
- all: `/mnt/d/MyProject/code/repos/kromp-blastocyst-dataset-audit/results/rich_image_analysis/figures/lists/sample_all_64.txt`
- LB=1: `/mnt/d/MyProject/code/repos/kromp-blastocyst-dataset-audit/results/rich_image_analysis/figures/lists/sample_lb1_64.txt`
- LB=0: `/mnt/d/MyProject/code/repos/kromp-blastocyst-dataset-audit/results/rich_image_analysis/figures/lists/sample_lb0_64.txt`

## Notes
- Contact-sheet figure PNGs are generated separately via ffmpeg from the list files.
