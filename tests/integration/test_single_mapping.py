"""Quick test of single tax code mapping."""

import asyncio
from hs_agent.workflows.tax_code_mapper import TaxCodeMapper

async def test_single_mapping():
    """Test mapping a single tax code."""

    # Initialize mapper
    mapper = TaxCodeMapper("data/avalara_tax_codes.xlsx", confidence_threshold=0.7)

    # Get first tax code
    first_tax_code = mapper.tax_codes[0]
    print(f"Testing with tax code: {first_tax_code.avalara_code}")
    print(f"Description: {first_tax_code.full_description}")

    # Map it
    result = await mapper.map_single_tax_code(first_tax_code)

    # Display results
    print(f"\n🎯 MAPPING RESULT:")
    print(f"   Avalara Code: {result.avalara_code}")
    print(f"   HS Code: {result.hs_code}")
    print(f"   Confidence: {result.confidence:.3f}")
    print(f"   HS Description: {result.hs_description}")
    print(f"   Processing Time: {result.processing_time_ms:.0f}ms")

    if result.error:
        print(f"   Error: {result.error}")
    else:
        print(f"   Reasoning: {result.reasoning[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_single_mapping())