Product: "{product_description}"

Parent Chapter: {parent_chapter}

Here are all the available heading codes within this chapter:
{candidates_list}

Task: Evaluate ALL headings and select the best 1-{max_selections} heading codes.

For each heading, consider:
- The product's material composition, function, and intended use
- How the heading's description aligns with the product's essential character
- Both primary and alternative classification possibilities

Your output must include:
**selections**: Array of 1-{max_selections} best heading codes, each with:
- **code**: The heading code
- **confidence**: Confidence score (0.0-1.0) for this specific code
- **reasoning**: Explanation for why this specific code was selected