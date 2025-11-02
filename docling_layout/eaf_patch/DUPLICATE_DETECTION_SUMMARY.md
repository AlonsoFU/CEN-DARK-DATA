# Duplicate Detection Summary

## Problem Discovered

When adding clusters with the EAF patch, duplicates were being created when Docling correctly extracted the same content.

**Example**: Chapter 7 had duplicate title "7. Análisis de las causas de la falla..."
- Docling correctly extracted it → 1 copy
- Patch also created it → **DUPLICATE!**

## Root Cause

The patch was checking ALL PDF lines for patterns (titles, company names, power lines) and creating clusters for matches, **without checking if Docling already extracted them**.

```python
# BEFORE (created duplicates):
for title_block in missing_titles:
    cluster = Cluster(label=SECTION_HEADER, bbox=..., text=...)
    custom_clusters.append(cluster)  # ← No duplicate check!
```

## Solution: IOU Overlap Detection

Added **Intersection Over Union (IOU)** duplicate detection for ALL patch cluster types:

### 1. Title Clusters (lines 557-572)
```python
# Check if Docling already has this title
for cluster in self.regular_clusters:
    if cluster.label == DocItemLabel.SECTION_HEADER:
        overlap = cluster.bbox.intersection_over_union(title_bbox)
        if overlap > 0.5:  # 50% threshold
            skip_duplicate = True
            break

if skip_duplicate:
    continue  # Don't create the cluster
```

### 2. Company Name Clusters (lines 624-638)
```python
# Check if Docling already has this company name
for cluster in self.regular_clusters:
    if cluster.label == DocItemLabel.SECTION_HEADER:
        overlap = cluster.bbox.intersection_over_union(company_bbox)
        if overlap > 0.5:
            skip_duplicate = True
            break
```

### 3. Power Line Clusters (lines 688-702)
```python
# Check if Docling already has this power line
for cluster in self.regular_clusters:
    if cluster.label == DocItemLabel.LIST_ITEM:
        overlap = cluster.bbox.intersection_over_union(power_bbox)
        if overlap > 0.5:
            skip_duplicate = True
            break
```

## How IOU Works

**IOU (Intersection Over Union)** compares bounding boxes:

```
IOU = Intersection Area / Union Area

Example from Chapter 7:
  Docling bbox: x0=56.64, y0=62.24, x1=534.66, y1=70.54
  Patch bbox:   x0=56.64, y0=60.07, x1=538.14, y1=70.98

  IOU = 75.6% → DUPLICATE DETECTED → Skipped!
```

**Why 50% threshold?**
- Too low (20%): False positives (nearby titles flagged as duplicates)
- Too high (90%): Misses duplicates with minor coordinate differences
- **50%**: Perfect balance - catches same content with slight variations

## Results

After implementing duplicate detection across all 11 chapters:

- ✅ **32 duplicates prevented** (titles only, first run)
- ✅ **Chapter 7**: Reduced from 352 to 349 elements (duplicate removed)
- ✅ **All chapters**: Zero duplicates found in final verification
- ✅ **Total elements**: 2,075 (down from 2,091)

### Verification Results
```
Chapter 01: ✅ No duplicates (17 section headers)
Chapter 02: ✅ No duplicates (4 section headers)
Chapter 03: ✅ No duplicates (1 section header)
Chapter 04: ✅ No duplicates (12 section headers)
Chapter 05: ✅ No duplicates (1 section header)
Chapter 06: ✅ No duplicates (38 section headers)
Chapter 07: ✅ No duplicates (34 section headers) ← Fixed!
Chapter 08: ✅ No duplicates (1 section header)
Chapter 09: ✅ No duplicates (36 section headers)
Chapter 10: ✅ No duplicates (24 section headers)
Chapter 11: ✅ No duplicates (50 section headers)
```

## Code Locations

All duplicate detection code is in:
```
eaf_patch/core/eaf_patch_engine.py
```

- **Lines 557-572**: Title duplicate detection
- **Lines 624-638**: Company name duplicate detection
- **Lines 688-702**: Power line duplicate detection

## Key Principle

**Every cluster the patch creates must check if Docling already extracted it using IOU overlap detection (threshold: 50%).**

This ensures the patch only adds truly missing content, not duplicates of what Docling correctly found.
