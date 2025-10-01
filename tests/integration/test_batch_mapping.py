"""Test batch mapping with a few tax codes."""

import asyncio
from hs_agent.workflows.tax_code_mapper import TaxCodeMapper

async def test_batch_mapping():
    """Test mapping a small batch of tax codes."""

    # Initialize mapper
    mapper = TaxCodeMapper("data/avalara_tax_codes.xlsx", confidence_threshold=0.6)

    print("First few tax codes to be processed:")
    for i, tax_code in enumerate(mapper.tax_codes[:3]):
        print(f"{i+1}. {tax_code.avalara_code}: {tax_code.full_description[:100]}...")

    # Map first 3 tax codes
    results = await mapper.map_batch(batch_size=2, max_items=3)

    # Save results
    output_path = mapper.save_results(results, "sample_batch_mapping")

    print(f"\n✅ Batch mapping completed! Results saved to {output_path}")

    # Print individual results
    print(f"\n📋 INDIVIDUAL RESULTS:")
    for result in results:
        print(f"\n🏷️  {result.avalara_code}")
        print(f"   HS Code: {result.hs_code}")
        print(f"   Confidence: {result.confidence:.3f}")
        if result.error:
            print(f"   Error: {result.error}")
        else:
            print(f"   Description: {result.avalara_description[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_batch_mapping())