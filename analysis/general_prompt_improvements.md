# General Prompt Improvements (Non-Case-Specific)

## Philosophy: Strengthen General Principles, Not Add Special Cases

---

## 🎯 **IMPROVEMENT #1: Emphasize Mandatory Nature of Chapter Notes**

### Current Problem
Agent treated Chapter Notes as guidance rather than binding rules. Made "reasonable inferences" when notes provided explicit mandatory instructions.

### General Solution: Clarify Legal Language in Notes

---

### Add to `compare_final_codes/prompts/system.md`

**Replace/Enhance the section "Chapter Notes and Legal Texts: Binding Rules" (lines 54-76):**

```markdown
## Chapter Notes and Legal Texts: Binding Rules

Chapter notes and legal texts are MANDATORY RULES, not suggestions or guidance.

### Understanding Legal Language in Chapter Notes

**Mandatory Instructions - NO DISCRETION:**
- "**shall**" = must do, no exceptions
- "**are to be**" = mandatory directive
- "**must**" = required, not optional
- "**do not cover**" = absolute exclusion

**When you see this language:**
1. It is a BINDING RULE, not a guideline
2. You CANNOT make "reasonable inferences" that contradict it
3. You MUST follow the instruction exactly as written
4. Violations invalidate the classification path

**Example of Mandatory Language:**
- "Articles which cannot be identified as X **are to be** classified as Y" → You MUST classify as Y, not make assumptions about X
- "This chapter **does not cover** products of type Z" → Products of type Z CANNOT go in this chapter, period
- "Products **must** meet condition A" → If condition A not met, classification is invalid

**Example of Incorrect Application:**
- ❌ Note says "are to be classified as women's" → Agent: "but I think it's more commonly men's, so I'll classify as men's"
- ❌ Note says "must be in bulk" → Agent: "it's not in bulk, but I'll use this code anyway"
- ❌ Note says "do not cover worn articles" → Agent: "it's worn, but I'll still put it in this chapter"

**Correct Application:**
- ✅ Note says "are to be classified as women's" → Must classify as women's, even if description seems masculine
- ✅ Note says "must be in bulk" → If not in bulk, cannot use this code (find alternative or return 000000)
- ✅ Note says "do not cover worn articles" → Worn articles are EXCLUDED, explore other chapters

### Hierarchy of Rules

1. **Legal texts (section/chapter notes)** override general principles
2. **Chapter notes** create binding exclusions and inclusions
3. **Exclusions** take precedence: if a note says "excluding X", those products CANNOT be classified in that chapter
4. **Inclusion notes** define scope: products outside the defined scope are excluded
5. **Mandatory language** ("shall", "are to be", "must", "do not cover") leaves NO ROOM for interpretation or inference

### How to Apply

**Step 1:** Read all relevant chapter notes for each path
**Step 2:** Identify mandatory language ("shall", "are to be", "must", "do not cover")
**Step 3:** Check if path complies with ALL mandatory instructions
**Step 4:** If path violates ANY mandatory instruction → path is INVALID
**Step 5:** If all paths are invalid → return "000000" (Condition 3)
**Step 6:** If multiple valid paths remain → compare based on precision, specificity, and best customs practice

### Red Flags

- ❌ Path reasoning that doesn't mention relevant chapter notes when notes would affect classification
- ❌ Path that acknowledges mandatory instruction but proceeds anyway with "reasonable inference"
- ❌ Path that interprets mandatory language as flexible or optional
- ❌ Making assumptions that contradict explicit note instructions
- ❌ Using phrases like "while the note says X, I think Y is more reasonable"

### Key Principle

**If a Chapter Note provides an explicit rule using mandatory language, you MUST follow it.**
**No inferences, assumptions, or "reasonable interpretations" are allowed.**
**Chapter notes determine validity; only compare valid paths for best fit.**
```

---

## 🎯 **IMPROVEMENT #2: Encourage More Path Exploration**

### Current Problem
Inconsistent path generation - sometimes only 1 path explored when multiple plausible options exist.

### General Solution: Favor Exploration Over Premature Narrowing

---

### Add to `select_chapter_candidates/prompts/system.md`

**Add new section after "Multi-Chapter Exploration Strategy":**

```markdown
## General Exploration Strategy: When in Doubt, Explore More

### Default Mindset: Explore Alternatives

**Philosophy**: It's better to generate 2-3 plausible paths and compare them than to narrow too early and miss the correct classification.

**When to explore MULTIPLE chapters (2-3 candidates):**

1. **Any ambiguity in product description**
   - Material not specified or ambiguous
   - Construction method not stated (knitted vs woven, molded vs fabricated, etc.)
   - Function could support multiple chapters

2. **Product at classification boundaries**
   - Could fit either a specialized chapter or general chapter
   - Characteristics span multiple material categories
   - Both material-based and function-based chapters seem applicable

3. **Potential chapter note exclusions**
   - The "obvious" chapter might exclude this product type
   - Chapter notes mention products "classified elsewhere"
   - Uncertain whether note exclusions apply

4. **Limited product information**
   - Description is brief or missing details
   - Could plausibly fit 2-3 different product categories
   - Reasonable interpretations lead to different chapters

5. **You're uncertain about the best fit**
   - If you have even slight uncertainty, explore alternatives
   - Trust that final comparison will select the best path
   - Over-exploration is better than under-exploration

### Single Chapter Only When:

- Product description is highly specific and unambiguous
- Only one chapter logically applies
- Material, function, and form all clearly point to same chapter
- No reasonable alternative interpretations exist
- You are highly confident (>95%) in the classification

### Examples of Good Exploration Strategy

**Example 1: "Cotton shirt" - no construction mentioned**
- Could be: Chapter 61 (if knitted) OR Chapter 62 (if woven)
- **Explore both** → let comparison determine based on typical construction

**Example 2: "Plastic jewelry box"**
- Could be: Chapter 39 (plastic articles) OR Chapter 42 (cases/containers) OR Chapter 71 (jewelry boxes specifically)
- **Explore 2-3** → chapter notes will determine correct classification

**Example 3: "Gold-plated ring"**
- Could be: Chapter 71 heading 7113 (precious metal) OR heading 7117 (imitation jewelry)
- **Explore both** → notes on plating vs cladding will determine

**Example 4: "Preloved fleece jacket"**
- Could be: Chapter 61 (knitted garments) OR Chapter 62 (woven garments) OR Chapter 63 (worn clothing)
- **Explore all 3** → notes on exclusions and bulk requirements will determine

### Key Principle

**Favor exploration over premature narrowing.**
**Generate 2-3 plausible paths when any uncertainty exists.**
**Trust the comparison stage to select the best path using chapter notes.**
**Better to explore too much than miss the correct classification.**
```

---

### Update in `select_chapter_candidates/prompts/system.md`

**Replace the "Key Principle: Honest Uncertainty" section (lines 65-73) with:**

```markdown
## Key Principles

### 1. Honest Assessment of Product Category

- Do NOT guess at product categories from pure marketing language
- Do NOT invent product types from brand names or adjectives
- Do NOT force classification when product category is genuinely indeterminate
- DO select Ch 99 when you cannot identify what TYPE of good this is

### 2. Favor Exploration Over Certainty

- When confident (>95%) → Single chapter is fine
- When uncertain (<95%) → Explore 2-3 plausible chapters
- When ambiguous → Always explore multiple interpretations
- Default: If you're asking "should I explore another chapter?" → YES

### 3. Trust the Comparison Process

- Don't worry about generating "too many" paths (2-3 is good)
- Chapter notes in comparison stage will eliminate invalid paths
- Final comparison is designed to handle multiple valid alternatives
- Your job: generate plausible candidates, not make the final decision

Your selections will cascade through heading and subheading levels, so explore thoroughly at the chapter stage.
```

---

## 🎯 **IMPROVEMENT #3: Strengthen Note Application in Comparison**

### Add to `compare_final_codes/prompts/user.md`

**Enhance the "Important considerations" section (after line 19):**

```markdown
Important considerations:

**FIRST - CHECK MANDATORY INSTRUCTIONS IN CHAPTER NOTES:**

Chapter notes may contain mandatory instructions that ELIMINATE certain paths.

Look for this language:
- "**shall**" / "**must**" / "**are to be**" = mandatory instruction, must follow exactly
- "**do not cover**" / "**excluding**" = absolute exclusion, path is invalid if violated
- "**only when**" / "**provided that**" = conditional requirement, must be met

If ANY path violates mandatory instructions in chapter notes, that path is INVALID.
Mark it as invalid and explain why, citing the specific note.

**THEN - EVALUATE REMAINING VALID PATHS:**

After eliminating paths that violate chapter notes:

- Consider the complete reasoning chain from chapter to subheading
- Don't just pick the highest confidence score - look at the quality of reasoning
- Identify which path has the most compelling and defensible justification
- Look for red flags or weak justifications
- Consider which classification customs would most likely accept

Compare the paths based on:
- How precisely each HS code matches the product
- How well-justified each classification path is
- Which path has the strongest reasoning at each level
- Which classification is most defensible for customs
- Which code is most specific and practical for trade

**Remember**: If chapter notes say something "must" or "shall" be done, or products "are to be" classified a certain way, this is NOT optional. Follow the mandatory instruction, even if your inference suggests otherwise.
```

---

## 📊 **Summary of General Improvements**

| Improvement | Location | General Principle | Effect on Cases |
|-------------|----------|-------------------|-----------------|
| **1. Mandatory Note Language** | compare_final_codes/system.md | Chapter notes are binding rules, not guidelines | Fixes gender default (Case #3) |
| **2. Exploration Strategy** | select_chapter_candidates/system.md | Favor exploration, generate 2-3 paths | More consistent path generation |
| **3. Note Application** | compare_final_codes/user.md | Check mandatory instructions FIRST | Stronger enforcement |

---

## 🎯 **Key Differences from Previous Approach**

### Before (Case-Specific):
- ❌ "For gender-ambiguous apparel, use women's/girls' heading"
- ❌ "For preloved items, classify as worn clothing in 6309"
- ❌ "For plated jewelry, use heading 7117 not 7113"

### Now (General Principles):
- ✅ "When notes use mandatory language ('are to be', 'must', 'shall'), follow exactly - no inferences"
- ✅ "When uncertain, explore 2-3 plausible paths instead of narrowing to one"
- ✅ "Check mandatory note instructions FIRST, before comparing path quality"

---

## ✅ **Why This Is Better**

1. **Scales to all products** - not just the 3 test cases
2. **Teaches agent HOW to think** - not just WHAT to think
3. **Applies to any Chapter Note** - not just gender, preloved, jewelry
4. **Fewer special cases** - simpler, more maintainable prompts
5. **Handles future edge cases** - without needing new prompt updates

---

## 🧪 **Expected Results**

**Case #3 (Blue Shirt)**:
- Chapter 62 Note 9 says "are to be classified" (mandatory)
- Agent will recognize mandatory language
- Will apply women's default as required → **620630** ✅

**Case #2 (Preloved Fleece)**:
- Will explore Ch 61, 62, AND 63
- Comparison will note Ch 61/62 "do not cover" (mandatory exclusion)
- Will select 630900 with clear reasoning about mandatory exclusions

**Case #1 (Snake Rings)**:
- "Plated" → will explore both 7113 and 7117 (exploration principle)
- Comparison will apply Note 7 on cladding vs plating
- Will select 711719 correctly

---

## 📝 **Implementation Strategy**

1. **Add ~80 lines total** (less than case-specific version)
2. **Three files** to modify:
   - compare_final_codes/system.md (~40 lines)
   - select_chapter_candidates/system.md (~30 lines)
   - compare_final_codes/user.md (~10 lines)

3. **Test incrementally**:
   - Add mandatory language section → test Case #3
   - Add exploration strategy → test all cases
   - Verify regression tests pass

---

## 🎯 **Key Message to Agent**

**For Note Application:**
> "When Chapter Notes use mandatory language like 'shall', 'must', 'are to be', or 'do not cover', this is a BINDING RULE with no room for inference. Follow the instruction exactly as written."

**For Path Exploration:**
> "When uncertain, explore 2-3 plausible paths. Better to generate alternatives and compare them than to narrow prematurely and miss the correct classification."

These two general principles would have caught all three questionable cases.
