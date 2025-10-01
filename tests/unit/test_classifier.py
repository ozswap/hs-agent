"""Test script for the HS classifier."""

import asyncio
import os
from hs_agent.agents.traditional.classifier import HSClassifier


async def test_classification():
    """Test the HS classifier with some example products."""

    # You need to set your Google API key
    if "GOOGLE_API_KEY" not in os.environ:
        print("Please set GOOGLE_API_KEY environment variable")
        return

    # Initialize classifier
    print("Initializing HS classifier...")
    classifier = HSClassifier(data_dir="data", model_name="gemini-2.5-flash")

    # Test cases
    test_products = [
        "Pure-bred Arabian mare for breeding",
        "Fresh apples from Washington state",
        "Cotton t-shirt for men",
        "Laptop computer with Intel processor",
        "Raw steel sheets for manufacturing"
    ]

    for product in test_products:
        print(f"\n{'='*60}")
        print(f"Testing: {product}")
        print('='*60)

        try:
            results = await classifier.classify(
                product_description=product,
                top_k=5,
                verbose=True
            )

            print(f"\n✅ Successfully classified '{product}'")
            print(f"Final HS Code: {results['final_code']}")
            print(f"Overall Confidence: {results['overall_confidence']:.2f}")

        except Exception as e:
            print(f"❌ Error classifying '{product}': {e}")


if __name__ == "__main__":
    asyncio.run(test_classification())