Product: "{product_description}"

Here are all the available HS chapters:
{candidates_list}

Task: Evaluate ALL chapters for relevance, rank them, and select the best 1-{max_selections} chapter codes.

This is the foundation of the classification hierarchy, so choose carefully. Focus on quality over quantity - only select multiple chapters if there's genuine ambiguity or if they represent truly distinct classification possibilities.

For each chapter, consider:
- The product's material composition, function, and intended use
- Multiple possible classification interpretations
- Components or related products
- Both primary and secondary classification possibilities
- Trade classification practices and how customs typically handles similar products

Your output must include:
1. **selected_codes**: The best 1-{max_selections} chapter codes to explore further
2. **individual_confidences**: Confidence score (0.0-1.0) for each selected code
3. **ranked_candidates**: ALL evaluated chapters ranked by relevance (0.0-1.0) with brief reasoning
4. **overall_confidence**: Overall confidence in your selection set
5. **reasoning**: Detailed explanation for your selections

Choose the most accurate, defensible, and trade-compliant classifications.