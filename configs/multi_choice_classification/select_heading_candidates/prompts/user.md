Product: "{product_description}"

Parent Chapter: {parent_chapter}

Here are all the available heading codes within this chapter:
{candidates_list}

Task: Evaluate ALL headings for relevance, rank them, and select the best 1-{max_selections} heading codes.

This narrows down the classification within the chapter. Focus on quality over quantity - only select multiple headings if there's genuine ambiguity or if they represent truly distinct classification possibilities.

For each heading, consider:
- The product's material composition, function, and intended use
- How the heading's description aligns with the product's essential character
- Trade classification practices and customs interpretations
- Both primary and alternative classification possibilities

Your output must include:
1. **selected_codes**: The best 1-{max_selections} heading codes to explore further
2. **individual_confidences**: Confidence score (0.0-1.0) for each selected code
3. **ranked_candidates**: ALL evaluated headings ranked by relevance (0.0-1.0) with brief reasoning
4. **overall_confidence**: Overall confidence in your selection set
5. **reasoning**: Detailed explanation for your selections

Consider which headings most precisely describe the product's essential character and function.