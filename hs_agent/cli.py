"""Simple CLI for HS Agent."""

import asyncio
import sys
from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader
from hs_agent.config.settings import settings


def print_result(result):
    """Print classification result."""
    print("\n" + "="*60)
    print(f"Product: {result.product_description}")
    print("="*60)
    print(f"\n📊 CHAPTER: {result.chapter.selected_code}")
    print(f"   Confidence: {result.chapter.confidence:.2f}")
    print(f"   Reasoning: {result.chapter.reasoning[:100]}...")

    print(f"\n📋 HEADING: {result.heading.selected_code}")
    print(f"   Confidence: {result.heading.confidence:.2f}")
    print(f"   Reasoning: {result.heading.reasoning[:100]}...")

    print(f"\n🎯 SUBHEADING: {result.subheading.selected_code}")
    print(f"   Confidence: {result.subheading.confidence:.2f}")
    print(f"   Reasoning: {result.subheading.reasoning[:100]}...")

    print(f"\n✅ FINAL HS CODE: {result.final_code}")
    print(f"🎯 OVERALL CONFIDENCE: {result.overall_confidence:.2f}")
    print(f"⏱️  Processing time: {result.processing_time_ms:.0f}ms")
    print("="*60 + "\n")


async def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python -m hs_agent.cli_simple \"product description\"")
        print("Example: python -m hs_agent.cli_simple \"laptop computer\"")
        sys.exit(1)

    product_description = " ".join(sys.argv[1:])

    print("Initializing HS Agent...")
    loader = HSDataLoader()
    loader.load_all_data()

    agent = HSAgent(loader)

    print(f"\nClassifying: {product_description}\n")
    result = await agent.classify(product_description)

    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())