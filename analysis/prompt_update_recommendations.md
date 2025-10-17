# Prompt Update Recommendations

## Based on Testing Results from Questionable Classifications Analysis

---

## 🎯 **PRIORITY 1: Fix Gender Default Rule Enforcement**

### Issue
Case #3 (Blue Shirt) classified as men's (620520) when gender was unspecified.
- Chapter 62 Note 9 is **MANDATORY**: unspecified gender → women's/girls'
- Agent made "reasonable inference" instead of applying rule

### Current Behavior
Agent reasoning:
> "While the gender is not explicitly stated, the term 'shirt' with 'urban stripe' and 'square pocket' is commonly associated with men's or boys' wear..."

**This violates Chapter 62 Note 9** which says garments that "cannot be identified" must go to women's/girls' headings.

---

### Proposed Fix: Update `compare_final_codes/prompts/system.md`

**Add new section after line 76 (after "Chapter notes determine validity"):**

```markdown
## Critical: Gender Default Rules (Chapter 61 Note 9 & Chapter 62 Note 9)

**MANDATORY RULE - NOT OPTIONAL:**

For Chapters 61 (knitted) and 62 (not knitted), when comparing apparel paths:

**Chapter 61 Note 9 & Chapter 62 Note 9 state:**
> "Garments which cannot be identified as either men's or boys' garments or as women's or girls' garments are to be classified in the headings covering women's or girls' garments."

**This is MANDATORY, not a suggestion. Apply as follows:**

1. **Check product description for explicit gender indicators:**
   - Closure direction (men's: left over right, women's: right over left)
   - Explicit marketing ("men's shirt", "women's blouse", "boys' jacket")
   - Clear gender-specific cut or styling EXPLICITLY stated

2. **If gender CANNOT BE IDENTIFIED from description:**
   - You MUST select paths with women's/girls' headings
   - Do NOT make "reasonable inferences" about typical gender associations
   - Do NOT assume based on style names like "urban" or "classic"
   - Do NOT infer from product names or colors

3. **Invalid reasoning to avoid:**
   - ❌ "This style is commonly associated with men's wear"
   - ❌ "The term 'shirt' typically refers to men's garments"
   - ❌ "Urban stripe suggests masculine styling"

4. **Correct application:**
   - ✅ "Gender not explicitly stated → must apply Note 9 default to women's/girls'"
   - ✅ "No closure direction or gender-specific features mentioned → women's/girls' per Note 9"
   - ✅ "Description does not identify gender → mandatory default to women's/girls' headings"

**When comparing paths:**
- If you have both men's and women's paths for a gender-unspecified garment
- **You MUST select the women's/girls' path** per mandatory Note 9
- Mark men's/boys' paths as INVALID for gender-unspecified products

**This rule applies to:**
- Headings 6103/6104 (knitted suits, jackets, trousers, etc.)
- Headings 6105/6106 (knitted shirts)
- Headings 6107/6108 (knitted underwear)
- Headings 6109/6110/6111/6114 (various knitted garments)
- Headings 6203/6204 (woven suits, jackets, trousers, etc.)
- Headings 6205/6206 (woven shirts)
- Headings 6207/6208 (woven underwear)
- Headings 6209/6210/6211 (various woven garments)

**Enforcement**: Gender default is as binding as any other chapter note exclusion.
```

---

## 🎯 **PRIORITY 2: Add Preloved/Used Goods Guidance**

### Issue
Case #2 (Preloved Fleece) classified as 630900 (worn clothing) even though it's a single retail item, not bulk shipment.

- Agent correctly applies Chapter 61/62 Notes (exclude worn clothing)
- But 6309 requires bulk shipment per Chapter 63 Note 3(b)(ii)
- Creates classification limbo for single "preloved" items

---

### Proposed Fix: Add to `compare_final_codes/prompts/system.md`

**Add new section after the gender default rules:**

```markdown
## Special Case: Preloved/Used Goods Classification

**Context**: Chapter 63, Heading 6309 covers "Worn clothing and other worn articles"

**Critical Requirement - Chapter 63 Note 3:**
> For heading 6309, articles must:
> (i) show signs of appreciable wear; AND
> (ii) be entered in bulk or in bales, sacks or similar packings

**Classification Guidance:**

### Single "Preloved" Retail Items

**Product indicators:**
- Described as "preloved", "second-hand", "pre-owned", "vintage" in retail context
- Single garment or small quantity
- No indication of bulk commercial shipment
- Retail packaging (not bales, sacks, commercial bulk)

**Classification approach:**

**Option A - Use 6309 (more conservative):**
- If product explicitly states "preloved", "used", "worn"
- Chapters 61 & 62 Notes explicitly exclude worn articles → must use 6309
- Accept that 6309 may be technically incorrect for retail items but is the only available category

**Option B - Classify as new garment (more practical):**
- "Preloved" is marketing language for single retail items
- Chapter 63 Note 3(b)(ii) requires BULK shipment for 6309
- Single retail items don't meet bulk requirement
- Classify by material/construction as if new garment
- Note in reasoning: "Single preloved retail item classified by material/construction; not bulk shipment per Ch 63 Note 3(b)(ii)"

**Recommendation**: **Use Option A** unless explicitly told otherwise
- Agent should apply Chapter Notes as written (61/62 exclude worn → 6309)
- Acknowledge in reasoning that bulk requirement may not be met
- Set confidence at 100% for correct Chapter Note application

**For bulk commercial shipments of used clothing:**
- Clear 6309 classification
- Must meet both wear AND bulk requirements
```

---

## 🎯 **PRIORITY 3: Encourage More Path Diversity**

### Issue
Inconsistent path generation:
- Case 1 (Snake Rings): 1 path
- Case 2 (Preloved Fleece): 8 paths
- Case 3 (Blue Shirt): 1 path

Need more consistent exploration, especially when initial path might be rejected.

---

### Proposed Fix: Update `select_chapter_candidates/prompts/system.md`

**Add after line 65 (after "Specialized vs General Categories"):**

```markdown
**Reason 5: Multiple Interpretations of Material/Construction**
- When material or construction method is ambiguous or not stated
- Example: "shirt" could be knitted (Ch 61) or woven (Ch 62)
- Example: "jewelry" could be precious metal (7113) or plated base metal (7117)
- Explore both interpretations to compare in final step

**Reason 6: Edge Cases and Ambiguous Products**
- Products with limited description that could fit multiple categories
- When product characteristics suggest multiple classification approaches
- Products at the boundary between chapters
- Explore 2-3 plausible chapters even if one seems most likely
```

**Update the "Key Principle" section (starting line 65):**

```markdown
## Key Principle: Explore Alternatives When Uncertain

**Default Strategy:**
- If product CLEARLY fits one chapter → select that chapter
- If ANY uncertainty or alternative interpretation exists → explore 2-3 chapters

**When to explore multiple chapters:**
- ✅ Material or construction ambiguous (knitted vs woven, plastic vs rubber)
- ✅ Chapter notes might exclude the obvious choice
- ✅ Multiple classification principles apply (material vs function)
- ✅ Limited product description could fit multiple categories
- ✅ Product at boundary between specialized and general chapters

**Goal**: Better to over-explore and compare paths than miss the correct classification

**Do NOT:**
- ❌ Guess at product categories from pure marketing language
- ❌ Invent product types from brand names or adjectives
- ❌ Force classification when product category is genuinely indeterminate

**DO:**
- ✅ Select Ch 99 when you cannot identify what TYPE of good this is
- ✅ Explore 2-3 chapters when reasonable alternative interpretations exist
- ✅ Favor exploration over premature narrowing
```

---

## 🎯 **OPTIONAL: Add Jewelry Plating vs. Cladding Guidance**

### Issue
Case #1 (Snake Rings) initially explored only 711320 (clad) not 711719 (plated).
With max_selections=5, it got the right path, but we could add explicit guidance.

---

### Proposed Fix: Add to `select_heading_candidates/prompts/system.md`

**Add new section for jewelry-specific guidance:**

```markdown
## Special Guidance: Jewelry Classification (Chapter 71)

**Critical Distinction: Plating vs. Cladding**

When classifying jewelry described as "dipped", "plated", "gold-plated", "rhodium-plated", etc.:

**Chapter 71 Note 7 - Metal Clad with Precious Metal:**
> "Metal clad with precious metal" means material with a covering of precious metal affixed by soldering, brazing, welding, hot-rolling, or similar mechanical means.

**Chapter 71 Note 6:**
> References to precious metal do NOT include base metal plated with precious metal.

**Chapter 71 Note 11 - Imitation Jewelry (Heading 7117):**
> Includes jewelry with precious metal present "as plating or as minor constituents"

**Classification Approach:**

1. **"Dipped", "Plated", "Electroplated"** → Heading 7117 (Imitation jewelry)
   - Electrochemical process ≠ mechanical bonding
   - Precious metal as plating → falls under 7117 definition
   - Base metal (brass, steel, etc.) + precious metal plating = 711719

2. **"Clad", "Filled", "Rolled gold"** → Heading 7113 (Articles of precious metal)
   - Mechanical bonding process
   - Thicker layer than plating
   - If base metal clad with precious metal → 711320

**When evaluating jewelry paths:**
- If description says "dipped" or "plated" → strongly favor 7117 over 7113
- If description says "clad" or "filled" → favor 7113
- If unclear → explore BOTH 7113 and 7117 for comparison
- Let final comparison apply the strict Chapter Note definitions
```

---

## 📊 **Summary of Changes**

| Priority | Location | Issue Fixed | Impact |
|----------|----------|-------------|--------|
| **1** | `compare_final_codes/prompts/system.md` | Gender default rule | High - Fixes Case #3 |
| **2** | `compare_final_codes/prompts/system.md` | Preloved goods policy | Medium - Clarifies Case #2 |
| **3** | `select_chapter_candidates/prompts/system.md` | Path diversity | Medium - More consistent exploration |
| Optional | `select_heading_candidates/prompts/system.md` | Jewelry guidance | Low - Case #1 already fixed |

---

## 🧪 **Testing Strategy After Updates**

1. **Immediate Validation:**
   - Re-run Case #3 (Blue Shirt) → should now return 620630 (women's)
   - Re-run Case #2 (Preloved Fleece) → should return 630900 with clearer reasoning
   - Verify Case #1 (Snake Rings) still returns 711719

2. **Regression Testing:**
   - Run full 138-case wide net dataset
   - Verify no new failures introduced
   - Check that other gender-ambiguous cases now default correctly

3. **Edge Case Testing:**
   - Test with various gender-ambiguous apparel descriptions
   - Test with "preloved", "vintage", "second-hand" descriptions
   - Test jewelry with various plating terms

---

## ✅ **Expected Outcomes**

**After Priority 1 (Gender Default):**
- All gender-ambiguous apparel → women's/girls' headings
- Case #3: Blue Shirt → 620630 (not 620520)
- No more "reasonable inference" violations of Note 9

**After Priority 2 (Preloved Goods):**
- Consistent handling of preloved items
- Clear reasoning explaining Chapter Note application
- Case #2: Clearer justification for 630900

**After Priority 3 (Path Diversity):**
- More consistent 2-3 path exploration
- Fewer single-path classifications
- Better alternative path generation

---

## 📝 **Implementation Notes**

1. **Test incrementally** - Apply Priority 1 first, test, then Priority 2, etc.
2. **Monitor confidence scores** - Should remain high for correct classifications
3. **Review reasoning quality** - Check that explanations cite the new guidance
4. **Document any unexpected behaviors** - New edge cases may emerge

---

## 🔄 **Rollback Plan**

If updates cause issues:
1. Keep original prompts as `.md.backup`
2. Can revert specific sections independently
3. Priority 1 is most critical - keep this even if others need adjustment
