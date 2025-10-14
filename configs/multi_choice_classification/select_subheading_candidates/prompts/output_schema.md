## MultiSelectionOutput Schema

This structure contains the final 1-3 selected HS code candidates with detailed reasoning and selection strategy.

### Output Format
Return a JSON object with selected candidates and selection methodology.

### Key Requirements:
1. **selected_codes**: 1-3 best candidates (adaptive based on confidence)
2. **individual_confidences**: Confidence for each selected code
3. **overall_confidence**: Overall confidence in the selection set
4. **reasoning**: Detailed justification for each selection

### Selection Guidelines:
- **High confidence (>0.8)**: Select 1-2 candidates
- **Medium confidence (0.6-0.8)**: Select 2-3 candidates
- **Low confidence (<0.6)**: Select 2-3 candidates with diverse coverage

Ensure each selection adds unique value and provides comprehensive coverage of likely classification scenarios.