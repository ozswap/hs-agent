"""Test script for 5 new edge cases to validate principle-based prompts.

These cases test:
1. Material vs function classification
2. Multi-function products (essential character)
3. Medical vs consumer products
4. Composite products with multiple components
5. Within-chapter disambiguation
"""

import asyncio
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


NEW_EDGE_CASES = [
    {
        "name": "Yoga Mat",
        "description": "Yoga Mat",
        "expected": "Ch 95 (sporting equipment) vs Ch 39/40 (plastic/rubber) vs Ch 57 (floor coverings)",
        "rationale": "Tests material vs function classification. Function (exercise equipment) should dominate over material.",
        "likely_correct": "Ch 95 - Articles for gymnastics/sports"
    },
    {
        "name": "Massage Gun (Electric)",
        "description": "Electric Massage Gun",
        "expected": "Ch 90 (medical/therapeutic) vs Ch 85 (electrical handheld tools) vs Ch 84 (mechanical appliances)",
        "rationale": "Tests medical vs consumer classification and chapter notes on therapeutic apparatus.",
        "likely_correct": "Ch 90 if therapeutic, Ch 85 if consumer device - depends on marketing/intended use"
    },
    {
        "name": "Smart Doorbell with Camera",
        "description": "Smart Doorbell with Camera",
        "expected": "Ch 85 (bells) vs Ch 85 (cameras) vs Ch 85 (transmission apparatus) vs Ch 83 (door fittings)",
        "rationale": "Tests composite product with multiple electrical functions. Needs essential character determination.",
        "likely_correct": "Ch 85 - likely transmission/reception apparatus or cameras based on essential character"
    },
    {
        "name": "Decorative String Lights",
        "description": "Decorative String Lights",
        "expected": "Ch 94 (lamps/lighting) vs Ch 95 (festive/decorative articles)",
        "rationale": "Tests whether decorative purpose overrides lighting function. Chapter notes may guide.",
        "likely_correct": "Ch 94 if general lighting, Ch 95 if explicitly festive/seasonal"
    },
    {
        "name": "Protein Powder",
        "description": "Whey Protein Powder",
        "expected": "Ch 04 (dairy - whey), Ch 21 (food preparations), Ch 23 (residues from food industries), or Ch 30 (pharmaceutical)",
        "rationale": "Tests food classification with specific source material and whether health claims affect classification.",
        "likely_correct": "Ch 04 (if minimally processed whey) or Ch 21 (if prepared/flavored)"
    },
]


async def main():
    print("=" * 80)
    print("NEW EDGE CASE TEST: Validating Principle-Based Prompts")
    print("=" * 80)
    print()

    # Initialize
    print("Loading data...")
    data_loader = HSDataLoader()
    data_loader.load_all_data()

    print("Initializing WIDE NET agent...")
    agent = HSAgent(data_loader, workflow_name="wide_net_classification")
    print("✅ Ready\n")

    # Test each case
    for i, test in enumerate(NEW_EDGE_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(NEW_EDGE_CASES)}: {test['name']}")
        print(f"{'=' * 80}")
        print(f"📝 Description: \"{test['description']}\"")
        print(f"🤔 Challenge: {test['expected']}")
        print(f"💡 Rationale: {test['rationale']}")
        print(f"🎯 Likely Correct: {test['likely_correct']}")
        print()

        try:
            result = await agent.classify_multi(test['description'], max_selections=3)

            print(f"✅ RESULT:")
            print(f"   Final Code: {result.final_selected_code}")
            print(f"   Confidence: {result.final_confidence:.1%}")
            print(f"   Paths Explored: {len(result.paths)}")
            print(f"   Sample Paths:")
            for j, path in enumerate(result.paths[:4], 1):
                print(f"     {j}. Ch{path.chapter_code} → {path.heading_code} → {path.subheading_code} (conf: {path.path_confidence:.1%})")

            print(f"\n   💭 Final Reasoning (first 300 chars):")
            reasoning_preview = result.final_reasoning[:300] + "..." if len(result.final_reasoning) > 300 else result.final_reasoning
            for line in reasoning_preview.split('\n')[:5]:
                print(f"      {line}")

            if result.comparison_summary:
                print(f"\n   📝 Chapter Notes Comparison (first 200 chars):")
                comp_preview = result.comparison_summary[:200] + "..." if len(result.comparison_summary) > 200 else result.comparison_summary
                for line in comp_preview.split('\n')[:3]:
                    print(f"      {line}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 80}")
    print("NEW EDGE CASE TESTS COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(main())
