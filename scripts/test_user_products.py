"""Test specific user-provided product descriptions.

These are real product names that may contain marketing language,
variations in naming, or ambiguous descriptions.

Expected Classifications (based on web research):
- Guitar effect/pedal products: Ch 85 (electrical apparatus), NOT Ch 92
  - Ch 92 Note 1(b) excludes electronic accessories of Ch 85
  - Typically 8543 (electrical machines with individual functions)

- Snowboard products: Ch 95 (sports equipment)
  - Specifically 950611 for skis/snowboards

- LED acrylic sign: Ch 94 (illuminated signs)
  - Typically 9405.61 for LED illuminated signs

- Welcome box: AMBIGUOUS - depends on contents
  - If empty packaging: Ch 48 (paper boxes)
  - If filled: GRI 3(b) essential character of contents
  - "Pug Box Premium" gives no indication of contents
"""

import asyncio
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


USER_PRODUCTS = [
    {
        "description": "Guitar Effect",
        "expected": "Ch 85 (electrical apparatus), NOT Ch 92 - Chapter 92 Note 1(b) exclusion",
        "notes": "Electronic effect device for guitars"
    },
    {
        "description": "Guitar Effect Accessory",
        "expected": "Ch 85 (electrical accessories) or ambiguous depending on what 'accessory' is",
        "notes": "Vague - accessory to an effect pedal? Could be cable, power supply, etc."
    },
    {
        "description": "The Multi-managed Snowboard",
        "expected": "Ch 95 (sports equipment) - 950611",
        "notes": "Marketing language but product type is clear: snowboard"
    },
    {
        "description": "Snowboard",
        "expected": "Ch 95 (sports equipment) - 950611",
        "notes": "Clear product type"
    },
    {
        "description": "Snowboard for snowboarding",
        "expected": "Ch 95 (sports equipment) - 950611",
        "notes": "Redundant description but clear product type"
    },
    {
        "description": "Guitar Effect Pedal",
        "expected": "Ch 85 (electrical apparatus) - 8543, NOT Ch 92",
        "notes": "Electronic effect pedal - Ch 92 Note 1(b) exclusion applies"
    },
    {
        "description": "Pug Box Premium - Welcome Box",
        "expected": "000000 - Cannot determine product category from marketing name",
        "notes": "Pure marketing language - no indication of what's in the box or if it's just packaging"
    },
    {
        "description": "Personalized LED Color Changing Acrylic Golf Clubs Sign - 20 Inches",
        "expected": "Ch 94 (illuminated signs) - 9405.61 or similar",
        "notes": "LED illuminated decorative sign"
    },
    {
        "description": "guitar effect",
        "expected": "Ch 85 (electrical apparatus), NOT Ch 92",
        "notes": "Lowercase version of 'Guitar Effect'"
    },
]


async def test_single_product(agent: HSAgent, test: dict, index: int):
    """Test a single product classification."""
    print(f"\n{'=' * 80}")
    print(f"TEST {index}/{len(USER_PRODUCTS)}: {test['description']}")
    print(f"{'=' * 80}")
    print(f"📝 Description: \"{test['description']}\"")
    print(f"🎯 Expected: {test['expected']}")
    print(f"💭 Notes: {test['notes']}")
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

        print(f"\n   💭 Final Reasoning (first 400 chars):")
        reasoning_preview = result.final_reasoning[:400] + "..." if len(result.final_reasoning) > 400 else result.final_reasoning
        for line in reasoning_preview.split('\n'):
            if line.strip():
                print(f"      {line}")

        if result.comparison_summary:
            print(f"\n   📝 Comparison Summary (first 300 chars):")
            comp_preview = result.comparison_summary[:300] + "..." if len(result.comparison_summary) > 300 else result.comparison_summary
            for line in comp_preview.split('\n'):
                if line.strip():
                    print(f"      {line}")

        # Evaluate result
        print(f"\n   🔍 EVALUATION:")
        if result.final_selected_code == "000000":
            print(f"      ✓ Returned 000000 (unclassifiable)")
        elif result.final_selected_code.startswith("85"):
            print(f"      ✓ Classified to Ch 85 (Electrical)")
        elif result.final_selected_code.startswith("92"):
            print(f"      ⚠️  Classified to Ch 92 (Musical) - check Ch 92 Note 1(b)")
        elif result.final_selected_code.startswith("95"):
            print(f"      ✓ Classified to Ch 95 (Sports)")
        elif result.final_selected_code.startswith("94"):
            print(f"      ✓ Classified to Ch 94 (Lighting/Signs)")
        else:
            print(f"      ℹ️  Classified to other chapter: Ch{result.final_selected_code[:2]}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 80)
    print("USER PRODUCT TESTING")
    print("Testing 9 real product descriptions from user")
    print("=" * 80)
    print()

    # Initialize
    print("Loading data...")
    data_loader = HSDataLoader()
    data_loader.load_all_data()

    print("Initializing WIDE NET agent...")
    agent = HSAgent(data_loader, workflow_name="wide_net_classification")
    print("✅ Ready\n")

    # Run tests
    results = []
    for i, test in enumerate(USER_PRODUCTS, 1):
        success = await test_single_product(agent, test, i)
        results.append((test['description'], success, test['expected']))

        # Pause between tests
        if i < len(USER_PRODUCTS):
            print(f"\n{'=' * 80}")
            input("Press Enter to continue to next test...")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    passed = sum(1 for _, success, _ in results if success)
    print(f"Completed: {passed}/{len(USER_PRODUCTS)} tests")
    print()
    for desc, success, expected in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {desc}")
        print(f"         Expected: {expected}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
