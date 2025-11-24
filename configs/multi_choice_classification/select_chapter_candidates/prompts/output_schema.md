## MultiSelectionOutput Schema

Return a JSON object with an array of selected HS codes. Each selection must include:
- **code**: The selected HS code
- **confidence**: Confidence score (0.0-1.0) for this specific code
- **reasoning**: Clear explanation for why this code was selected