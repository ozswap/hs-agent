## MultiSelectionOutput Schema

This structure contains the final 1-3 selected HS code candidates with detailed reasoning and selection strategy.

### Output Format
Return a JSON object with selected candidates and selection methodology.

### Key Requirements:
1. **selected_candidates**: 1-3 best candidates (adaptive based on confidence)
2. **selection_strategy**: Document approach and rationale
3. **confidence**: Individual confidence for each selection
4. **reasoning**: Detailed justification for each selection



### Example Output:
```json
{
  "selected_candidates": [
    {
      "code": "84",
      "description": "Nuclear reactors, boilers, machinery and mechanical appliances; parts thereof",
      "confidence": 0.85,
      "reasoning": "Primary classification - product is clearly mechanical machinery with specific industrial application",
      "rank_in_original": 1
    },
    {
      "code": "85",
      "description": "Electrical machinery and equipment...",
      "confidence": 0.72,
      "reasoning": "Secondary classification - significant electrical components justify consideration",
      "rank_in_original": 2
    }
  ],
  "selection_strategy": {
    "approach": "adaptive",
    "rationale": "High confidence in primary classification, included secondary for component coverage",
    "confidence_level": "high"
  },
  "metadata": {
    "total_selections": 2,
    "selection_timestamp": "2025-09-26T15:30:00Z"
  }
}
```

Ensure each selection adds unique value and provides comprehensive coverage of likely classification scenarios.
