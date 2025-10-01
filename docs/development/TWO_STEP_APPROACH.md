# Two-Step Multi-Choice HS Classification

## 🔄 Overview

The HS Agent now uses a **two-step ranking approach** that combines broad initial discovery with refined intelligent selection:

**Step 1: Broad Initial Ranking** → **Step 2: Refined Selection (1 to max_n)**

## 🎯 How It Works

### Step 1: Broad Initial Ranking
- Uses **high K value** (e.g., 15-50) for comprehensive coverage
- LLM ranks ALL available codes to find potential matches
- Ensures no relevant codes are missed in the initial phase
- Creates a rich candidate pool for refined selection

### Step 2: Refined Selection
- LLM intelligently selects from the broad candidate pool
- **Flexible range**: Can choose 1, 2, 3, up to max_n codes
- Quality over quantity - focuses on most relevant matches
- Adapts selection count based on product characteristics

## 📊 Configuration Parameters

```python
result = await agent.classify_multi_choice(
    product_description="cotton textile fabric",
    initial_ranking_k=20,        # STEP 1: Broad ranking (high K)
    max_selections_per_level=3,  # STEP 2: Max selections (1 to 3 range)
    min_confidence_threshold=0.6 # Quality threshold
)
```

## 🚀 Benefits

### 1. **Comprehensive Coverage**
- High initial_ranking_k ensures no relevant codes are overlooked
- Better than single-step with low K that might miss good candidates

### 2. **Intelligent Selection**
- LLM decides how many codes based on product characteristics:
  - **Clear products**: Selects fewer codes (1-2)
  - **Ambiguous products**: Selects more codes (2-4)

### 3. **Quality Focus**
- Refined selection step filters out noise from broad ranking
- Only high-confidence, relevant codes make it to final results

### 4. **Concurrent Processing**
- Both steps run concurrently across chapters/headings
- Much faster than sequential processing

## 📈 Performance Characteristics

### For Clear Products (e.g., "cotton t-shirt")
```
Step 1: Ranks 20 chapters → finds 3-4 highly relevant
Step 2: Selects 1-2 chapters → focused, precise results
```

### For Ambiguous Products (e.g., "electronic textile sensor")
```
Step 1: Ranks 25 chapters → finds 6-8 potentially relevant
Step 2: Selects 3-4 chapters → comprehensive coverage
```

## 🔄 Workflow Flow

```
START
  ↓
rank_chapter_candidates (STEP 1: Broad ranking, K=20)
  ↓
select_multiple_chapters (STEP 2: Refined selection, 1 to max_n)
  ↓
process_all_chapters (CONCURRENT: Each chapter uses two-step)
  ├── STEP 1: Broad heading ranking (K=20 per chapter)
  └── STEP 2: Refined heading selection (1 to max_n per chapter)
  ↓
process_all_headings (CONCURRENT: Each heading uses two-step)
  ├── STEP 1: Broad subheading ranking (K=20 per heading)
  └── STEP 2: Refined subheading selection (1 to max_n per heading)
  ↓
aggregate_all_results
  ↓
END
```

## 🎯 Example Results

### Input
```python
await agent.classify_multi_choice(
    product_description="organic cotton fabric",
    initial_ranking_k=15,       # Broad coverage
    max_selections_per_level=2, # Up to 2 selections per level
    min_confidence_threshold=0.6
)
```

### Two-Step Process
```
STEP 1: Broad ranking finds 15 chapters
STEP 2: Refined selection chooses 2 best chapters: ['52', '58']

STEP 1: Broad ranking finds 15 headings per chapter
STEP 2: Refined selection chooses 1-2 headings per chapter

STEP 1: Broad ranking finds 15 subheadings per heading
STEP 2: Refined selection chooses 1-2 subheadings per heading
```

### Final Output
```python
{
    "total_paths": 4,
    "processing_stats": {
        "unique_chapters": 2,
        "unique_headings": 3,
        "unique_subheadings": 4
    },
    "overall_confidence": 0.78,
    "all_classification_paths": [
        # Complete chapter→heading→subheading paths
    ]
}
```

## 🔧 Tuning Guidelines

### initial_ranking_k (Step 1)
- **Conservative**: 10-15 (faster, might miss edge cases)
- **Balanced**: 15-25 (recommended for most cases)
- **Comprehensive**: 25-50 (slower, maximum coverage)

### max_selections_per_level (Step 2)
- **Focused**: 1-2 (clear products, precise results)
- **Balanced**: 2-3 (most products)
- **Comprehensive**: 3-5 (complex/ambiguous products)

### min_confidence_threshold
- **Strict**: 0.7-0.8 (high quality, fewer results)
- **Balanced**: 0.5-0.7 (recommended)
- **Permissive**: 0.3-0.5 (more results, lower quality)

The two-step approach provides the best of both worlds: comprehensive discovery with intelligent refinement! 🎉