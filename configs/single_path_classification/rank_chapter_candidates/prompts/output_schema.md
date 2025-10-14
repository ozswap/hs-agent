## RankingOutput Schema

This structure contains the ranked list of HS code candidates with their confidence scores and reasoning.

### Output Format
Return a JSON object with ranked candidates sorted by relevance score (highest first).

### Key Requirements:
1. **ranked_candidates**: Array of candidate objects, sorted by confidence (descending)
2. **confidence**: Must be between 0.0 and 1.0
3. **reasoning**: Provide clear, concise reasoning for each candidate's position

Ensure all candidates are ranked, even with low confidence scores for completeness.