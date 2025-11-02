# Fix for Split Title Bug: "6." vs "6. Normalización del servicio"

**Date**: 2025-10-23
**Status**: 🔴 CRITICAL BUG - Proposed Fix
**Affects**: Chapter titles extraction in EAF Patch v2.0

---

## 🐛 Problem Summary

The EAF Patch correctly extracts complete merged lines from PDF:
- **PyMuPDF extracts**: "6. Normalización del servicio" (complete title, 3 spans merged)
- **Patch output**: Only "6." (missing "Normalización del servicio")

**Impact**: Chapter titles are incomplete - only the number is extracted, not the descriptive text.

---

## 🔍 Root Cause Analysis

### What We Know

1. **PyMuPDF correctly merges spans** (lines 109-141 in eaf_patch_engine.py):
   - Span 1: "6." (x0=56.6, x1=66.2, width=9.6)
   - Span 2: " " (space, stripped away)
   - Span 3: "Normalización del servicio" (x0=68.8, x1=205.0, width=136.2)
   - **Merged line**: "6. Normalización del servicio" (x0=56.6, x1=205.0, width=148.3) ✅

2. **Native Docling has 0% coverage** for the complete title area (y=60-71)
   - No elements found in the title position
   - Title should be in `missing_lines` ✅

3. **Title detector works correctly**:
   - `is_missing_title("6.")` → True ✅
   - `is_missing_title("6. Normalización del servicio")` → True ✅
   - `is_missing_title("Normalización del servicio")` → False ❌ (no number prefix)

4. **Patch output has only "6."** with bbox width=9.6 (exactly span 1's bbox)

### The Bug: Internal Docling Cell Splitting

**Hypothesis**: Docling internally extracts the title as **TWO separate cells** during processing:

1. **Cell 1**: "6." (x=56.6-66.2)
2. **Cell 2**: "Normalización del servicio" (x=68.8-205.0)

Both cells are added to `docling_blocks` (line 171-190), even though they don't appear in the final JSON output.

**What happens next**:

```python
# Line 265-276: Title detector runs on ALL blocks
for block in all_blocks:  # all_blocks = docling_blocks + missing_lines
    if title_detector.should_create_cluster(text, bbox, page):
        missing_titles.append(block)
```

- **"6."** → Passes title detection ✅ → Cluster created
- **"Normalización del servicio"** → Fails title detection ❌ (no number prefix) → Ignored
- **Merged line** "6. Normalización del servicio" → Either not in `missing_lines` (if Docling cells have >50% coverage) OR detected but overridden by separate "6." cell

---

## 💡 Proposed Solution: Adjacent Title Merging

### Strategy

After detecting individual title blocks, **merge adjacent blocks that form a complete title**:

1. Detect all title blocks (current behavior)
2. Find title blocks that are:
   - On the same page
   - At similar Y coordinates (same line, ±5 pts)
   - Adjacent horizontally (x1 of first ≈ x0 of second, ±20 pts gap)
   - Where first block is a short title pattern ("6.", "a.") and second is regular text
3. Merge them into a single title block with:
   - Combined text: "6. " + "Normalización del servicio"
   - Expanded bbox: covering both blocks
4. Create cluster for the merged title

### Implementation

Add new function after line 276 in `eaf_patch_engine.py`:

```python
def _merge_adjacent_titles(missing_titles):
    """
    Merge adjacent blocks that form complete titles

    Example:
        Block 1: "6." at x0=56.6, x1=66.2
        Block 2: "Normalización del servicio" at x0=68.8, x1=205.0
        Result: "6. Normalización del servicio" at x0=56.6, x1=205.0
    """
    if len(missing_titles) <= 1:
        return missing_titles

    merged = []
    skip_indices = set()

    for i, title in enumerate(missing_titles):
        if i in skip_indices:
            continue

        # Check if this is a short title (just number/letter)
        text = title['text'].strip()
        if not (len(text) <= 5 and ('.' in text or text.isdigit())):
            merged.append(title)
            continue

        # Look for adjacent block on the same line
        found_continuation = False
        for j in range(i + 1, len(missing_titles)):
            if j in skip_indices:
                continue

            next_title = missing_titles[j]

            # Check if on same page
            if title['page'] != next_title['page']:
                continue

            # Check if on same line (Y coordinates similar)
            y_diff = abs(title['bbox']['y0'] - next_title['bbox']['y0'])
            if y_diff > 5:
                continue

            # Check if horizontally adjacent (with small gap)
            x_gap = next_title['bbox']['x0'] - title['bbox']['x1']
            if x_gap < 0 or x_gap > 20:
                continue

            # Merge!
            merged_text = text + ' ' + next_title['text'].strip()
            merged_bbox = {
                'x0': title['bbox']['x0'],
                'y0': min(title['bbox']['y0'], next_title['bbox']['y0']),
                'x1': next_title['bbox']['x1'],
                'y1': max(title['bbox']['y1'], next_title['bbox']['y1'])
            }

            merged.append({
                **title,
                'text': merged_text,
                'bbox': merged_bbox,
                'font': title.get('font'),
                'size': title.get('size')
            })

            skip_indices.add(j)
            found_continuation = True

            print(f"   🔗 [PATCH] Merged adjacent titles: '{text}' + '{next_title['text'].strip()}' → '{merged_text}'")
            break

        if not found_continuation:
            merged.append(title)

    return merged
```

### Integration Point

Insert after line 277 in `eaf_patch_engine.py`:

```python
print(f"📝 [PATCH] Found {len(missing_titles)} missing titles")
for title in missing_titles:
    print(f"   ✅ '{title['text']}' (nivel {title['level']})")

# NEW: Merge adjacent title blocks
missing_titles = _merge_adjacent_titles(missing_titles)
print(f"📝 [PATCH] After merging: {len(missing_titles)} complete titles")
```

---

## 🧪 Expected Behavior After Fix

### Before Fix
```
Input PDF: "6. Normalización del servicio"
Patch detects:
  - "6." (x0=56.6, x1=66.2)
  - "Normalización del servicio" (ignored, doesn't match title pattern)
Output: Only "6."
```

### After Fix
```
Input PDF: "6. Normalización del servicio"
Patch detects:
  - "6." (x0=56.6, x1=66.2)
  - "Normalización del servicio" (x0=68.8, x1=205.0)
Merge adjacent blocks:
  - "6." + "Normalización del servicio" → "6. Normalización del servicio"
  - Merged bbox: x0=56.6, x1=205.0
Output: "6. Normalización del servicio" ✅
```

---

## 📋 Testing Plan

### Test Cases

1. **Single-word title**: "6." (should work as before)
2. **Multi-word title**: "6. Normalización del servicio" (should merge)
3. **Long title**: "6.1 Plan de Recuperación de Servicio del Sistema Eléctrico Nacional" (should merge)
4. **Letter titles**: "a. Introducción" (should merge)
5. **Non-adjacent**: "6." and "Normalización" with >20pts gap (should NOT merge)
6. **Different lines**: "6." at y=60 and "Normalización" at y=100 (should NOT merge)

### Validation

Run on Chapter 6 page 1 and verify output contains:
```json
{
  "type": "section_header",
  "text": "6. Normalización del servicio",
  "bbox": {"x0": 56.6, "y0": 60.1, "x1": 205.0, "y1": 71.0},
  "page": 1
}
```

---

## 🚀 Implementation Steps

1. ✅ Add `_merge_adjacent_titles()` function to `eaf_patch_engine.py`
2. ✅ Call function after title detection (line 277)
3. ⏳ Test on Chapter 6
4. ⏳ Verify other chapters (01-11) still work correctly
5. ⏳ Update documentation

---

## 🔄 Alternative Solutions Considered

### Option 1: Improve Coverage Detection (Rejected)
- **Idea**: Check coverage per span instead of per merged line
- **Problem**: Would create separate clusters for each span, defeating the purpose of merging
- **Verdict**: ❌ Not the right approach

### Option 2: Extend Title Detector Patterns (Rejected)
- **Idea**: Add pattern to detect "Normalización del servicio" as title
- **Problem**: Too generic - would match regular text paragraphs
- **Verdict**: ❌ Would cause false positives

### Option 3: Adjacent Block Merging (Selected) ✅
- **Idea**: Merge adjacent blocks that form complete titles
- **Advantages**:
  - Preserves current detection logic
  - Works for all title patterns
  - Handles edge cases (gaps, alignment)
  - No false positives
- **Verdict**: ✅ Best solution

---

## 📊 Impact Analysis

### Affected Documents
- All EAF chapters with numbered/lettered titles
- Estimated: 11 chapters × 1-3 titles per chapter = 20-30 title elements

### Compatibility
- ✅ Backward compatible with existing extractions
- ✅ No changes to title detector patterns
- ✅ No changes to power line classification
- ✅ Only affects title merging logic

### Performance
- Negligible: O(n²) merge check where n = number of detected titles (typically <10 per page)
- Expected overhead: <1ms per page

---

**Status**: Ready for implementation
**Next Step**: Apply fix to `eaf_patch_engine.py` and test on Chapter 6
