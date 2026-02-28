# Kromp Final Cleaning Summary

## Row-level summary
- master_total: 2344
- clinical_total: 754
- split_valid_total: 2343
- split_unassigned_total: 1
- clinical_split: {'train_silver': 653, 'test_gold': 100, 'unassigned': 1}

## Split quality
- train_unique: 2043
- test_unique: 300
- train_duplicates: {'838_02.png': 2}
- test_duplicates: {}

## Clinical cleaning
- AMH_status: {'numeric': 88, 'month_suffix': 124, 'month_prefix': 377, 'missing': 165}
- AMH_clean_non_missing: 589
- AMH_clean_missing: 165
- AMH_out_of_range_count: 0
- AMH_min: 0.08
- AMH_max: 19.04
- LB_distribution: {'0': 520, '1': 234}
- has_multimodal_core: 598
- has_multimodal_full: 471
