Product: "{product_description}"

Parent Heading: {parent_heading}

Here are all the available subheading codes within this heading:
{candidates_list}

Task: Evaluate ALL subheadings and select the best 1-{max_selections} subheading codes as final classifications.

This is the FINAL HS code classification - the definitive codes that will be used for international trade and customs.

For each subheading, consider:
- The product's exact specifications, material composition, and essential character
- How the subheading's description precisely matches the product
- Intended use and functional characteristics

Your output must include:
**selections**: Array of 1-{max_selections} best subheading codes, each with:
- **code**: The subheading code
- **confidence**: Confidence score (0.0-1.0) for this specific code
- **reasoning**: Explanation for why this specific code was selected
