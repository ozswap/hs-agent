Product: "{product_description}"

Here are all the available HS chapters:
{candidates_list}

Task: Evaluate ALL chapters and select the best 1-{max_selections} chapter codes.

For each chapter, consider:
- The product's material composition, function, and intended use
- Multiple possible classification interpretations
- Components or related products
- Both primary and secondary classification possibilities

Your output must include:
**selections**: Array of 1-{max_selections} best chapter codes, each with:
- **code**: The chapter code
- **confidence**: Confidence score (0.0-1.0) for this specific code
- **reasoning**: Explanation for why this specific code was selected
