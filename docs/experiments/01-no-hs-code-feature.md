# No HS Code Classification Feature (000000)

## Overview

This feature adds support for returning HS code **"000000"** when a product description is invalid, meaningless, or not classifiable (e.g., "test", gibberish, nonsensical input).

## Implementation

### Branch

- **Branch name**: `feature/no-hs-code-classification`

### Changes Summary

#### 1. Prompt Updates (All Workflows)

Updated prompts to instruct the LLM when to use "000000":

**Single Path Classification** (`select_subheading_candidates`):
- `configs/single_path_classification/select_subheading_candidates/prompts/system.md`
- `configs/single_path_classification/select_subheading_candidates/prompts/user.md`

**Wide Net Classification** (`compare_final_codes`):
- `configs/wide_net_classification/compare_final_codes/prompts/system.md`
- `configs/wide_net_classification/compare_final_codes/prompts/user.md`

**Multi Choice Classification** (`compare_final_codes`):
- `configs/multi_choice_classification/compare_final_codes/prompts/system.md`
- `configs/multi_choice_classification/compare_final_codes/prompts/user.md`

**Prompt Guidelines Added:**
- Use "000000" ONLY when description is completely meaningless or invalid
- Examples: "test", gibberish, empty strings, nonsensical input
- Do NOT use for ambiguous or complex products (classify them normally)

#### 2. Agent Validation Logic

**File**: `hs_agent/agent.py`

Updated two key methods to allow "000000" as a special case:

1. **`_select_code()` method** (lines 277-285):
   - Added check for "000000" before validation
   - Returns `ClassificationResult` with description "No HS Code - Invalid or unclassifiable description"

2. **`_compare_final_codes()` method** (lines 589-597):
   - Added check for "000000" before path validation
   - Allows "000000" even if not in explored paths

#### 3. API Response Handling

**File**: `app.py`

Updated high_performance mode handling (lines 127-157):
- Added special case for "000000" in `/api/classify` endpoint
- Creates proper response structure with:
  - Chapter: "00" - "No HS Code - Invalid or unclassifiable description"
  - Heading: "0000" - "No HS Code - Invalid or unclassifiable description"
  - Subheading: "000000" - "No HS Code - Invalid or unclassifiable description"

## Usage

### When Will 000000 Be Returned?

The LLM will return "000000" when it determines the product description is:

1. **Meaningless**: e.g., "test", "asdfghjkl", random characters
2. **Test input**: Placeholder text or dummy data
3. **Empty/nonsensical**: No actual product information
4. **Invalid**: Not a real product description

### When Will Normal Codes Be Returned?

The LLM will return normal HS codes for:

1. **Ambiguous products**: Will classify to best available code
2. **Uncertain cases**: Will use best judgment with lower confidence
3. **Incomplete descriptions**: Will make reasonable inferences
4. **All valid products**: Normal classification process

## Testing

### Test Cases

To verify the feature works correctly, test with:

1. **Invalid descriptions (should return 000000)**:
   - "test"
   - "asdfghjkl"
   - "123456"
   - "" (empty string)

2. **Valid descriptions (should return normal codes)**:
   - "wireless bluetooth headphones"
   - "cotton t-shirt"
   - "steel screws"

### Example API Call

```bash
curl -X POST "http://localhost:8000/api/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "test",
    "high_performance": true
  }'
```

Expected response for "test":
```json
{
  "product_description": "test",
  "final_code": "000000",
  "overall_confidence": 0.95,
  "chapter": {
    "level": "2",
    "selected_code": "00",
    "description": "No HS Code - Invalid or unclassifiable description",
    "confidence": 0.95,
    "reasoning": "The input 'test' is not a valid product description..."
  },
  ...
}
```

## Architecture Notes

### Affected Workflows

1. **single_path_classification**: Can return 000000 at final subheading selection
2. **wide_net_classification**: Can return 000000 at final comparison step
3. **multi_choice_classification**: Can return 000000 at final comparison step

### Why Only Final Stage?

The "000000" option is only available at the **final classification stage** (subheading selection or final comparison), not in earlier stages (chapter/heading). This is because:

1. **Validates the description early**: LLM must attempt classification through hierarchy
2. **Provides better reasoning**: LLM can explain why it's invalid after evaluation
3. **Prevents premature rejection**: Ensures legitimate edge cases still get classified

## Files Changed

```
modified:   app.py
modified:   configs/multi_choice_classification/compare_final_codes/prompts/system.md
modified:   configs/multi_choice_classification/compare_final_codes/prompts/user.md
modified:   configs/single_path_classification/select_subheading_candidates/prompts/system.md
modified:   configs/single_path_classification/select_subheading_candidates/prompts/user.md
modified:   configs/wide_net_classification/compare_final_codes/prompts/system.md
modified:   configs/wide_net_classification/compare_final_codes/prompts/user.md
modified:   hs_agent/agent.py
```

## Next Steps

1. **Test with real LLM**: Run full integration tests with various invalid inputs
2. **Monitor behavior**: Check if LLM correctly identifies invalid vs. ambiguous descriptions
3. **Adjust prompts**: Fine-tune if LLM is too aggressive or too conservative with 000000
4. **Add edge cases**: Document additional scenarios where 000000 should be returned

## Rollback

To rollback this feature:

```bash
git checkout refactor/merge-ranking-selection-stages
git branch -D feature/no-hs-code-classification
```

