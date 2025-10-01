## RankingOutput Schema for Heading Level

This structure contains ranked 4-digit heading candidates under a specific chapter.

### Output Format
Return a JSON object with ranked headings sorted by relevance within the chapter context.

### Key Requirements:
1. **ranked_candidates**: Array of heading objects under the parent chapter
2. **confidence**: Reflects relevance within the specific chapter context
3. **reasoning**: Focus on heading-level distinctions (material, function, manufacturing)
4. **parent_chapter**: Include parent chapter for validation

### Heading-Level Considerations:
- Material composition differences
- Manufacturing process distinctions
- Functional categorizations within the chapter
- Trade classification patterns for headings

### Example Output:
```json
{
  "ranked_candidates": [
    {
      "code": "8471",
      "description": "Automatic data processing machines and units thereof; magnetic or optical readers...",
      "confidence": 0.88,
      "reasoning": "Product matches automatic data processing functionality and electronic components",
      "parent_chapter": "84"
    },
    {
      "code": "8473",
      "description": "Parts and accessories (other than covers, carrying cases...) suitable for use solely or principally with machines of headings 84.69 to 84.72",
      "confidence": 0.65,
      "reasoning": "Could be a component or accessory for data processing equipment",
      "parent_chapter": "84"
    }
  ],
  "metadata": {
    "parent_chapter_code": "84",
    "total_candidates_ranked": 15,
    "ranking_strategy": "focused",
    "context": "Under chapter 84 - machinery and mechanical appliances"
  }
}
```

Focus on distinctions that matter within the specific chapter context.