# Prompt Changes Summary - Quick Reference

## 🎯 Three Main Changes Needed

---

### ✅ **Change #1: Gender Default Rule Enforcement** (CRITICAL)

**File**: `configs/wide_net_classification/compare_final_codes/prompts/system.md`

**Add after line 76**: New section on mandatory gender default rules

**Key Points**:
- Chapter 61 Note 9 & Chapter 62 Note 9 are **MANDATORY**
- Gender unspecified → MUST use women's/girls' headings
- NO "reasonable inferences" allowed
- Explicit guidance on what counts as "identified gender"

**Fixes**: Case #3 (Blue Shirt) - will now return 620630 instead of 620520

**Impact**: High - Ensures compliance with binding HS rules

---

### ✅ **Change #2: Preloved Goods Policy** (IMPORTANT)

**File**: `configs/wide_net_classification/compare_final_codes/prompts/system.md`

**Add after gender default section**: Guidance on preloved/used goods

**Key Points**:
- Clarify that 6309 requires BULK shipment
- Single "preloved" retail items = classification dilemma
- Recommendation: Use 630900 but acknowledge bulk requirement not met
- Clear reasoning expectations

**Fixes**: Case #2 (Preloved Fleece) - clearer justification for 630900

**Impact**: Medium - Provides consistent policy for edge case

---

### ✅ **Change #3: More Path Diversity** (HELPFUL)

**File**: `configs/wide_net_classification/select_chapter_candidates/prompts/system.md`

**Add to "Multi-Chapter Exploration Strategy"**: More reasons to explore multiple paths

**Key Points**:
- Explore 2-3 chapters when material/construction ambiguous
- Add guidance on edge cases and boundaries
- Favor exploration over premature narrowing

**Fixes**: More consistent path generation across all products

**Impact**: Medium - Better exploration, fewer missed alternatives

---

## 📊 Quick Decision Matrix

| Issue | Priority | Effort | Risk | Recommend? |
|-------|----------|--------|------|------------|
| Gender Default | 🔴 Critical | Low | Low | **YES - Do First** |
| Preloved Policy | 🟡 Important | Low | Low | **YES - Do Second** |
| Path Diversity | 🟢 Helpful | Low | Low | **YES - Do Third** |
| Jewelry Guidance | ⚪ Optional | Low | Very Low | Optional |

---

## 🧪 Testing Checklist

After implementing:

- [ ] Case #3 (Blue Shirt) → Returns 620630 (women's shirt)
- [ ] Case #2 (Preloved Fleece) → Returns 630900 with clear reasoning
- [ ] Case #1 (Snake Rings) → Still returns 711719 (should work)
- [ ] Run full 138-case dataset for regression
- [ ] Verify other gender-ambiguous cases fixed
- [ ] Check confidence scores remain high

---

## 📁 Files to Modify

1. `configs/wide_net_classification/compare_final_codes/prompts/system.md`
   - Add Gender Default section (~50 lines)
   - Add Preloved Goods section (~40 lines)

2. `configs/wide_net_classification/select_chapter_candidates/prompts/system.md`
   - Add to multi-chapter exploration (~20 lines)
   - Update key principles (~15 lines)

3. *(Optional)* `configs/wide_net_classification/select_heading_candidates/prompts/system.md`
   - Add jewelry plating guidance (~30 lines)

**Total**: ~120-150 lines of new prompt content across 2-3 files

---

## ⚡ Quick Implementation Steps

1. **Backup originals**:
   ```bash
   cp system.md system.md.backup
   ```

2. **Apply Priority 1 (Gender Default)**:
   - Add section to compare_final_codes/prompts/system.md
   - Test Case #3

3. **Apply Priority 2 (Preloved)**:
   - Add section to compare_final_codes/prompts/system.md
   - Test Case #2

4. **Apply Priority 3 (Path Diversity)**:
   - Update select_chapter_candidates/prompts/system.md
   - Test all 3 cases + run full dataset

5. **Validate**:
   - Run regression tests
   - Check for unintended side effects

---

## 🎯 Expected Results

**Before**:
- Case #1: 000000 → **711719** ✅ (fixed with max_selections=5)
- Case #2: 000000 → 630900 ✅ (but needs clearer reasoning)
- Case #3: 000000 → 620520 ❌ (wrong - men's instead of women's)

**After Prompt Updates**:
- Case #1: **711719** ✅ (maintain)
- Case #2: **630900** ✅ (with better reasoning)
- Case #3: **620630** ✅ (corrected to women's)

---

## 📞 Need Help?

See detailed explanations in: `prompt_update_recommendations.md`
