Product: "{product_description}"

Number of paths to compare: {path_count}

Here are the classification paths that were explored:

{classification_paths}

---

Task: Compare all these classification paths and select THE SINGLE BEST HS code for this product.

Evaluate each path holistically - consider the complete reasoning chain from chapter to subheading, not just confidence scores. Which path has the most compelling and defensible justification? Are there any red flags or weak justifications?

Compare the paths based on:
- How precisely each HS code matches the product
- How well-justified each classification path is
- Which path has the strongest reasoning at each level
- Which classification is most defensible for customs
- Which code is most specific and practical for trade

You must provide:
- selected_code: The single best 6-digit HS code (from the explored paths), or "000000" if the description is invalid/meaningless
- confidence: Your confidence in this selection (0.0 to 1.0)
- reasoning: Detailed explanation of why this code is better than the alternatives, including what makes this path superior and what the weaknesses are in the other paths (or why the description is invalid)
- comparison_summary: Brief summary of how you compared the paths and what factors were decisive

Note: If the product description is completely invalid, meaningless, or just a test input (e.g., "test", gibberish), you may select "000000" instead of forcing a classification from the explored paths.

This is the final classification decision. Be thorough, precise, and decisive.
