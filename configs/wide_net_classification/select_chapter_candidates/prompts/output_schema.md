## MultiSelectionOutput Schema

This structure contains both the comprehensive ranking of all candidates AND the final 1-N selected HS codes.

### Output Format
Return a JSON object with ranked candidates, selected codes, and detailed reasoning.

### Key Requirements:
1. **selected_codes**: 1-N best candidates to explore further (adaptive based on confidence)
2. **individual_confidences**: Confidence score (0.0-1.0) for each selected code
3. **ranked_candidates**: ALL evaluated candidates with relevance scores and brief reasoning
4. **overall_confidence**: Overall confidence in the selection set
5. **reasoning**: Detailed justification for the selections

### Ranking Guidelines:
For each candidate in ranked_candidates:
- **code**: The HS code
- **relevance_score**: Score from 0.0 to 1.0 indicating relevance
- **reasoning**: Brief explanation (max 25 words) for the relevance score

### Selection Guidelines:
- **High confidence (>0.8)**: Select 1-2 candidates
- **Medium confidence (0.6-0.8)**: Select 2-3 candidates
- **Low confidence (<0.6)**: Select 2-3 candidates with diverse coverage

Ensure each selection adds unique value and provides comprehensive coverage of likely classification scenarios.
