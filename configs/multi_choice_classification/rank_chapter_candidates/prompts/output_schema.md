## RankingOutput Schema

This structure contains the ranked list of HS code candidates with their confidence scores and reasoning.

### Output Format
Return a JSON object with ranked candidates sorted by relevance score (highest first).

### Key Requirements:
1. **ranked_candidates**: Array of candidate objects, sorted by confidence (descending)
2. **confidence**: Must be between 0.0 and 1.0
3. **reasoning**: Provide clear, concise reasoning for each candidate's position
4. **metadata**: Include ranking strategy and total count

### Example Output:
```json
{
  "ranked_candidates": [
    {
      "code": "84",
      "description": "Nuclear reactors, boilers, machinery and mechanical appliances; parts thereof",
      "confidence": 0.85,
      "reasoning": "Product involves mechanical components and machinery"
    },
    {
      "code": "85",
      "description": "Electrical machinery and equipment and parts thereof; sound recorders and reproducers, television image and sound recorders and reproducers, and parts and accessories of such articles",
      "confidence": 0.72,
      "reasoning": "Contains electrical components that may be primary classification"
    }
  ],
  "metadata": {
    "total_candidates_ranked": 20,
    "ranking_strategy": "comprehensive",
    "timestamp": "2025-09-26T15:30:00Z"
  }
}
```

Ensure all candidates are ranked, even with low confidence scores for completeness.