# Wide Net Classification Workflow

## Overview

The **Wide Net Classification** workflow is a novel approach to HS code classification that casts a wide net by exploring multiple classification paths, then selects the single best HS code through intelligent comparison.

**Key Insight:** Instead of committing to a single path early, this workflow explores multiple possibilities at each level, compares all complete paths holistically, and then selects THE SINGLE BEST code with detailed justification.

## How It Works

### Phase 1: Exploration (Cast a Wide Net)

The workflow explores multiple paths hierarchically:

```
Chapter Level (2-digit)
├─ Select 1-N best chapters
│
├─ Heading Level (4-digit)
│  ├─ For each chapter, select 1-N best headings
│  │
│  └─ Subheading Level (6-digit)
│     └─ For each heading, select 1-N best subheadings
│
└─ Build all possible complete paths
   (chapter → heading → subheading combinations)
```

**Result:** Multiple complete classification paths, each with:
- Full reasoning chain (chapter → heading → subheading)
- Confidence scores at each level
- Overall path confidence

### Phase 2: Selection (Compare & Choose)

After exploring all paths, the comparison agent:

1. **Analyzes** all paths holistically
2. **Evaluates** reasoning quality, specificity, and trade compliance
3. **Compares** paths against each other
4. **Selects** THE SINGLE BEST HS code
5. **Explains** why this code is superior to alternatives

## Why This Approach?

### Traditional Single-Path Classification
- Commits to one path early
- May miss better alternatives
- Less defensible if challenged

### Wide Net Classification
- ✅ Explores multiple possibilities
- ✅ Considers alternatives before deciding
- ✅ Selects best code with justification
- ✅ More defensible (alternatives were considered)
- ✅ Higher confidence in final selection

## Workflow Steps

| Step | Name | Type | Description |
|------|------|------|-------------|
| 1 | `rank_chapter_candidates` | Ranking | Rank all 2-digit chapters by relevance |
| 2 | `select_chapter_candidates` | Multi-selection | Select 1-N best chapters (cast wide net) |
| 3 | `rank_heading_candidates` | Ranking | For each chapter, rank 4-digit headings |
| 4 | `select_heading_candidates` | Multi-selection | Select 1-N best headings per chapter |
| 5 | `rank_subheading_candidates` | Ranking | For each heading, rank 6-digit subheadings |
| 6 | `select_subheading_candidates` | Multi-selection | Select 1-N best subheadings (specialize) |
| 7 | `build_paths` | Path construction | Build all complete paths from selections |
| 8 | `compare_final_codes` | Final comparison | **Compare all paths and select THE BEST** |

## Configuration

### Default Parameters

```yaml
top_k: 10                    # Candidates to rank at each level
max_selections: 3            # Maximum selections per level (1-3)
max_output_paths: 10         # Maximum paths before comparison
enable_comparison: true      # Always perform final comparison
```

### Selection Strategy

The workflow uses a **funnel approach**:

- **Early Levels (Chapter/Heading):** Maximize exploration (more selections)
- **Final Level (Subheading):** Maximize precision (fewer, better selections)
- **Comparison:** Holistic evaluation (consider complete reasoning chains)

## Usage

### Python API

```python
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent

# Initialize
loader = HSDataLoader()
loader.load_all_data()

# Create agent with wide net workflow
agent = HSAgent(loader, workflow_name="wide_net_classification")

# Classify
result = await agent.classify_multi(
    product_description="Cotton t-shirt, men's size L, white",
    top_k=10,
    max_selections=3
)

# Access results
print(f"Explored {len(result.paths)} paths")
print(f"Selected: {result.final_selected_code}")
print(f"Confidence: {result.final_confidence}")
print(f"Reasoning: {result.final_reasoning}")
```

### CLI Usage

```bash
# Run test
python test_wide_net_classification.py

# Or use the HS Agent CLI
hs-agent classify "product description" --workflow wide_net_classification
```

## Response Structure

```python
MultiChoiceClassificationResponse(
    product_description="...",
    paths=[...],                    # All explored paths
    overall_strategy="...",         # Exploration strategy used
    processing_time_ms=...,

    # Final comparison results
    final_selected_code="123456",   # THE BEST code
    final_confidence=0.95,          # Confidence in selection
    final_reasoning="...",          # Why this code is best
    comparison_summary="..."        # How paths were compared
)
```

## Use Cases

This workflow is ideal for:

- ✅ **Ambiguous products** that could fit multiple categories
- ✅ **High-stakes classifications** requiring detailed justification
- ✅ **Products with multiple valid interpretations**
- ✅ **Trade compliance** requiring defensible decisions
- ✅ **Expert-level classification** with alternatives considered

## Advantages

1. **Thorough Exploration:** Doesn't commit to single path prematurely
2. **Intelligent Selection:** Compares alternatives before deciding
3. **Detailed Justification:** Explains why selected code is superior
4. **Trade Compliance:** More defensible in customs disputes
5. **Higher Confidence:** Based on broad exploration, not narrow path

## Comparison with Other Workflows

| Workflow | Exploration | Final Output | Best For |
|----------|-------------|--------------|----------|
| Traditional (single-path) | Single path | One code | Simple, clear-cut products |
| Multi-choice | Multiple paths | Multiple codes | Products with multiple valid classifications |
| **Wide Net** | **Multiple paths** | **One best code** | **Thorough exploration + single decision** |

## Configuration Files

- `workflow.yaml` - Workflow metadata and strategy
- `rank_chapter_candidates/` - Chapter ranking config
- `select_chapter_candidates/` - Chapter selection config
- `rank_heading_candidates/` - Heading ranking config
- `select_heading_candidates/` - Heading selection config
- `rank_subheading_candidates/` - Subheading ranking config
- `select_subheading_candidates/` - Subheading selection config
- `compare_final_codes/` - **Final comparison config** ⭐

## Example Output

```
📊 Wide Net Exploration:
   Strategy: Selected 5 classification path(s) from 5 possible combinations
   Number of paths explored: 5

🔀 All Explored Paths:
   PATH 1 (Confidence: 1.00):
      Final HS Code: 610910
      Path: 61 -> 6109 -> 610910

   PATH 2 (Confidence: 0.93):
      Final HS Code: 620520
      Path: 62 -> 6205 -> 620520

   [... more paths ...]

🏆 FINAL SELECTED HS CODE (after comparison):
   Selected HS Code: 610910
   Confidence: 1.00

   Reasoning: Path 1 provides the most accurate classification because...
   [detailed reasoning explaining why 610910 is superior to alternatives]

   Comparison Summary: I compared all 5 paths by evaluating accuracy,
   specificity, and reasoning quality. Path 1 was selected because it
   correctly identifies the product as a knitted t-shirt, which is more
   specific than general shirts...
```

## Technical Details

- **Model:** Gemini 2.5 Flash (configurable per step)
- **Thinking Mode:** Enabled for final comparison (4096 token budget)
- **Structured Output:** Pydantic models for type safety
- **Observability:** Langfuse integration for tracking
- **Fallback Logic:** Robust error handling with sensible defaults

## Further Reading

- See `workflow.yaml` for full configuration details
- See `compare_final_codes/prompts/` for comparison prompts
- See `test_wide_net_classification.py` for usage examples
