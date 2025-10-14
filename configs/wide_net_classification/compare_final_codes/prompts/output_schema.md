## FinalComparisonOutput Schema

This structure contains the final selected HS code after comparing candidates from multiple classification paths.

### Output Format
Return a JSON object with the single best HS code selection and detailed comparison analysis.

### Key Requirements:
1. **selected_code**: The single best HS code selected from all paths
2. **confidence**: Confidence level in the final selection (0.0 to 1.0)
3. **reasoning**: Detailed reasoning for selecting this code over alternatives
4. **comparison_summary**: Summary of how the different paths were compared and evaluated

### Comparison Guidelines:
- Analyze consistency across different classification approaches
- Weight higher confidence scores more heavily
- Consider the breadth of analysis from each path
- Provide transparent reasoning for the final decision