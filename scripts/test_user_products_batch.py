"""Test user products in batch mode (no pauses between tests)."""

import asyncio
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


USER_PRODUCTS = [
    {"description": "Guitar Effect", "expected": "Ch 85 NOT Ch 92"},
    {"description": "Guitar Effect Accessory", "expected": "Ch 85 or ambiguous"},
    {"description": "The Multi-managed Snowboard", "expected": "Ch 95"},
    {"description": "Snowboard", "expected": "Ch 95"},
    {"description": "Snowboard for snowboarding", "expected": "Ch 95"},
    {"description": "Guitar Effect Pedal", "expected": "Ch 85 NOT Ch 92"},
    {"description": "Pug Box Premium - Welcome Box", "expected": "000000"},
    {"description": "Personalized LED Color Changing Acrylic Golf Clubs Sign - 20 Inches", "expected": "Ch 94"},
    {"description": "guitar effect", "expected": "Ch 85 NOT Ch 92"},
]


async def main():
    print("=" * 80)
    print("USER PRODUCT BATCH TESTING")
    print("=" * 80)
    print()

    data_loader = HSDataLoader()
    data_loader.load_all_data()
    agent = HSAgent(data_loader, workflow_name="wide_net_classification")

    results = []

    for i, test in enumerate(USER_PRODUCTS, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(USER_PRODUCTS)}: {test['description']}")
        print(f"{'=' * 80}")
        print(f"🎯 Expected: {test['expected']}")

        try:
            result = await agent.classify_multi(test['description'], max_selections=3)

            print(f"✅ Result: {result.final_selected_code} ({result.final_confidence:.0%} conf)")
            print(f"   Paths: {len(result.paths)}")
            for j, path in enumerate(result.paths[:3], 1):
                print(f"   {j}. Ch{path.chapter_code} → {path.heading_code} → {path.subheading_code}")

            # Quick evaluation
            code = result.final_selected_code
            if code == "000000":
                eval_result = "✓ 000000"
            elif code.startswith("85"):
                eval_result = "✓ Ch 85 (Electrical)"
            elif code.startswith("92"):
                eval_result = "⚠️ Ch 92 (Musical)"
            elif code.startswith("95"):
                eval_result = "✓ Ch 95 (Sports)"
            elif code.startswith("94"):
                eval_result = "✓ Ch 94 (Lighting)"
            else:
                eval_result = f"Ch {code[:2]}"

            results.append((test['description'], eval_result, True))
            print(f"   → {eval_result}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((test['description'], "ERROR", False))

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    for desc, result, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc[:50]:50s} → {result}")


if __name__ == "__main__":
    asyncio.run(main())
