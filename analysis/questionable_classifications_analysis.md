# Analysis of Questionable Wide Net Classifications

## Executive Summary

Analyzed 3 cases where the wide_net_classification agent returned `000000` but should have returned specific HS codes. Root cause identified: **insufficient path exploration** - agent only generates 1 candidate path per classification, limiting its ability to find valid alternatives when rejecting incorrect paths.

## Cases Analyzed

### ✅ Case #1: Snake Ring Duo → Should be 711719

**Product**: "Set of two snake rings, one 12-karat gold-dipped brass, the other is rhodium-dipped brass"

**Current Result**: 000000
**Expected Result**: 711719 (Imitation jewelry of base metal, plated with precious metal)

**Agent's Reasoning**:
- ✓ Correctly identified "dipped" = plating (electrochemical), NOT cladding (mechanical)
- ✓ Correctly rejected 711320 (base metal clad with precious metal)
- ✓ Correctly cited Chapter 71 Note 7 (cladding requires mechanical bonding)
- ✗ **Failed to explore 711719** (imitation jewelry, plated)

**Root Cause**: Only 1 path explored (711320). When rejected, no alternative paths available.

**Correct Classification**:
```
Chapter: 71 (Jewelry, precious metals)
Heading: 7117 (Imitation jewelry)
Subheading: 711719 (Imitation jewelry of base metal, whether or not plated with precious metal)
```

**Justification**:
- Brass = base metal ✓
- Gold/rhodium plating = precious metal as plating ✓
- Chapter 71 Note 11 explicitly includes jewelry with precious metal "as plating" in 7117 ✓

---

### ⚠️ Case #2: Blake Fleece Preloved → Should be 611090 (probable)

**Product**: "Blake Fleece - Recycled Bottles - Cara Print - PRELOVED"

**Current Result**: 000000
**Expected Result**: 611090 (Jerseys/pullovers of other textile materials, knitted)

**Agent's Reasoning**:
- ✓ Correctly identified 6309 (worn clothing) requires bulk shipment
- ✓ Correctly rejected 6309 for single retail item
- ✗ **Failed to explore knitted garment alternatives** (6110)

**Root Cause**: Only 1 path explored (630900). No exploration of classifying as new garment by material.

**Issue with 6309**:
- Chapter 63 Note 3 requires: (i) signs of wear + (ii) **bulk/bales**
- Single "PRELOVED" retail item ≠ bulk worn clothing shipments
- 6309 is for commercial quantities of used clothing (thrift store shipments, etc.)

**Correct Classification** (assuming knitted fleece):
```
Chapter: 61 (Knitted or crocheted apparel)
Heading: 6110 (Jerseys, pullovers, cardigans, waistcoats)
Subheading: 611090 (Of textile materials other than wool, cotton, or man-made fibers)
```

**Alternative if woven**: 621050 (Women's garments of special fabrics)

**Classification Principle**: Single preloved retail items should be classified as NEW garments by their material/construction, NOT as worn clothing.

---

### ⚠️ Case #3: Sky Blue Urban Stripe Shirt → Should be 620630 or 620690

**Product**: "Sky Blue Urban Stripe Square Pocket Shirt. Ocean blue cotton shirt with a narrow collar and buttons down the front and long sleeves"

**Current Result**: 000000
**Expected Result**: 620630 (Women's shirt of cotton) or 620690 (Women's shirt of other materials)

**Agent's Reasoning**:
- ✓ Correctly identified Chapter 62 (not knitted/crocheted)
- ✓ Correctly identified shirt characteristics (collar, buttons)
- ✗ Explored only 620520 (men's cotton shirt)
- ✗ **Failed to apply Chapter 62 Note 9** (gender default rule)

**Root Cause**: Only 1 path explored (620520 - men's). Should have explored women's category per mandatory rule.

**Chapter 62 Note 9** (MANDATORY):
> "Garments which cannot be identified as either men's or boys' garments or as women's or girls' garments are **to be classified in the headings covering women's or girls' garments**."

**Reasonable Inferences**:
1. "Shirt" with buttons = woven fabric ✓
2. "Square pocket" on shirt = chest pocket (above waist) = NOT excluded ✓
3. Material mentioned as "cotton" ✓
4. Gender unspecified = **default to women's** per Note 9 ✓

**Correct Classification**:
```
Chapter: 62 (Apparel not knitted/crocheted)
Heading: 6206 (Women's shirts/blouses)
Subheading: 620630 (Of cotton)
```

---

## Root Cause Analysis

### Primary Issue: Insufficient Path Exploration

All three cases show the same pattern:
- Agent called with `max_selections=2`
- **Only 1 path generated per classification**
- When that single path is rejected, no alternatives available
- Result: 000000 even when valid classifications exist

### Why This Matters

The wide_net agent is designed to:
1. Generate multiple candidate paths
2. Evaluate each path against HS rules
3. Compare valid paths and select the best

**Current behavior**: Generating only 1 path defeats the "wide net" strategy.

---

## Recommendations

### 1. Immediate Fix: Increase Path Generation

**Action**: Investigate why `max_selections=2` only generates 1 path

**Possible causes**:
- Bug in candidate selection logic
- Too-narrow filtering at chapter/heading/subheading selection
- LLM not generating diverse enough candidates

**Test**: Run with `max_selections=5` to see if more paths are explored

### 2. Add Fallback Logic for Jewelry Plating

**Issue**: Snake rings case shows gap in jewelry classification

**Fix**: When heading 7113 is rejected due to plating vs. cladding, **automatically explore 7117** (imitation jewelry)

**Logic**:
```python
if product_type == "jewelry" and material == "plated base metal":
    explore_both(7113, 7117)  # Compare clad vs. plated paths
```

### 3. Clarify Preloved/Used Goods Policy

**Policy needed**:
- Single "preloved" retail items → classify as NEW by material/type
- Only use 6309 for **bulk commercial shipments** of used clothing
- 6309 ≠ single secondhand item sold at retail

**Implementation**: Add to system prompt or validation rules

### 4. Strengthen Gender Default Application

**Issue**: Agent didn't apply Chapter 62 Note 9 automatically

**Fix**: In comparison stage, when gender is ambiguous:
1. Check if Note 9 applies
2. If yes, **prioritize women's/girls' paths**
3. Or **only explore women's/girls' headings** when gender unspecified

---

## Testing Plan

### Phase 1: Verify Path Exploration (CURRENT)
- [x] Run test_questionable_cases.py with max_selections=2
- [ ] Run test_questionable_detailed.py with max_selections=5
- [ ] Check if more paths generated with higher max_selections

### Phase 2: Targeted Fixes
- [ ] If max_selections=5 doesn't help, investigate candidate generation
- [ ] Add explicit jewelry plating/cladding comparison logic
- [ ] Add preloved goods classification guidance

### Phase 3: Validation
- [ ] Re-run all 138 wide net examples
- [ ] Verify Snake Rings → 711719
- [ ] Verify Blue Shirt → 620630/620690
- [ ] Verify Preloved items classified reasonably

---

## Success Criteria

✅ **Case #1 (Snake Rings)**: Returns 711719, confidence >90%
✅ **Case #2 (Preloved Fleece)**: Returns valid knitted garment code (611090 or similar), NOT 000000
✅ **Case #3 (Blue Shirt)**: Returns women's shirt code (620630/620690) applying Note 9

**Overall goal**: Reduce incorrect 000000 classifications from ~3 cases to 0-1 cases in test set.

---

## Notes

- Agent's **reasoning is generally excellent** when it explores the right paths
- Problem is **path generation**, not path evaluation
- The comparison logic correctly applies Chapter Notes when paths are available
- Once path exploration is fixed, accuracy should improve significantly
