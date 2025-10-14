Product: "{product_description}"

Parent Heading: {parent_heading}

Here are all the available subheading codes within this heading:
{candidates_list}

Task: Evaluate ALL subheadings for relevance, rank them, and select the best 1-{max_selections} subheading codes.

This is the FINAL HS code classification - the definitive codes that will be used for international trade and customs. Focus on maximum accuracy and precision.

For each subheading, consider:
- The product's exact specifications, material composition, and essential character
- How the subheading's description precisely matches the product
- Trade classification practices and customs interpretations
- Intended use and functional characteristics

Your output must include:
1. **selected_codes**: The best 1-{max_selections} subheading codes as final classifications
2. **individual_confidences**: Confidence score (0.0-1.0) for each selected code
3. **ranked_candidates**: ALL evaluated subheadings ranked by relevance (0.0-1.0) with brief reasoning
4. **overall_confidence**: Overall confidence in your selection set
5. **reasoning**: Detailed explanation for your selections

Consider the product's exact specifications, essential character, intended use, and which codes customs officials would most likely accept.