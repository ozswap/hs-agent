"""Test edge cases one at a time based on real-world difficult classifications.

Based on web research of actual challenging HS code classification scenarios:
- Sets for retail sale (GRI 3)
- Composite goods requiring essential character determination
- Material mixtures
- Products spanning multiple chapters
"""

import asyncio
import sys
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


# Real-world difficult classification cases from research
RESEARCH_BASED_EDGE_CASES = [
    {
        "name": "Chocolate Covered Biscuits",
        "description": "Chocolate Covered Graham Crackers",
        "challenge": "Composite good: Ch 19 (biscuits) vs Ch 18 (chocolate)",
        "expected": "Essential character should determine - likely Ch 18 if chocolate dominates",
        "source": "Real example from GRI 3(b) guidance"
    },
    {
        "name": "Barbecue Utensil Set",
        "description": "Barbecue Set with Fork, Spatula, Tongs, and Brush",
        "challenge": "Set for retail sale: GRI 3 - multiple items in different headings",
        "expected": "Ch 82 (cutlery/kitchen tools) as a set",
        "source": "Real example from GRI 3 sets classification"
    },
    {
        "name": "Fishing Rod and Reel Set",
        "description": "Fishing Rod and Reel Set",
        "challenge": "Set with no clear essential character - both equally important",
        "expected": "Ch 95 - Should use GRI 3(c) last in numerical order when essential character unclear",
        "source": "Real example from GRI 3(c) guidance"
    },
    {
        "name": "Mixed Grain for Brewing",
        "description": "Brewing Mix 70% Wheat 30% Barley",
        "challenge": "Mixture: Ch 10 (wheat) vs Ch 10 (barley) - different headings within chapter",
        "expected": "Heading for wheat (10.01) based on predominant material",
        "source": "Real example from GRI 3(a) mixtures"
    },
    {
        "name": "Bed Linen Set",
        "description": "Bed Linen Set with Bedspread, Pillowcases, and Bolsters",
        "challenge": "Textile set for retail sale",
        "expected": "Ch 63 (home textiles) - set classification",
        "source": "Real example from GRI 3 sets classification"
    },
    {
        "name": "Liquor-Filled Chocolates",
        "description": "Liquor Filled Chocolates",
        "challenge": "Composite good: Ch 18 (chocolate) vs Ch 22 (alcoholic beverages)",
        "expected": "Ch 18 - chocolate gives essential character",
        "source": "Real example from GRI 3(b) guidance"
    },
    {
        "name": "Phone Charging Cable",
        "description": "USB-C Phone Charging Cable",
        "challenge": "Ch 85 (electrical cables) vs Ch 84 (parts of machines) vs Ch 85 (phone accessories)",
        "expected": "Ch 85 - electrical cables or phone accessories",
        "source": "Common misclassification scenario"
    },
    {
        "name": "Almond Butter",
        "description": "Almond Butter",
        "challenge": "Ch 08 (nuts/fruit) vs Ch 20 (fruit preparations) vs Ch 21 (food preparations)",
        "expected": "Ch 20 (preparations of nuts) - processed/prepared product",
        "source": "Common food preparation classification challenge"
    },
]


async def test_single_case(agent: HSAgent, test: dict):
    """Test a single classification case."""
    print(f"\n{'=' * 80}")
    print(f"TEST: {test['name']}")
    print(f"{'=' * 80}")
    print(f"📝 Description: \"{test['description']}\"")
    print(f"🤔 Challenge: {test['challenge']}")
    print(f"🎯 Expected: {test['expected']}")
    print(f"📚 Source: {test['source']}")
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

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    # Check for test number argument
    if len(sys.argv) > 1:
        try:
            test_num = int(sys.argv[1])
            if test_num < 1 or test_num > len(RESEARCH_BASED_EDGE_CASES):
                print(f"❌ Test number must be between 1 and {len(RESEARCH_BASED_EDGE_CASES)}")
                sys.exit(1)
            tests_to_run = [RESEARCH_BASED_EDGE_CASES[test_num - 1]]
            print(f"\n🎯 Running single test: #{test_num}")
        except ValueError:
            print("❌ Test number must be an integer")
            sys.exit(1)
    else:
        tests_to_run = RESEARCH_BASED_EDGE_CASES
        print(f"\n🎯 Running all {len(RESEARCH_BASED_EDGE_CASES)} tests")

    print("=" * 80)
    print("RESEARCH-BASED EDGE CASE TESTING")
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
    for i, test in enumerate(tests_to_run, 1):
        success = await test_single_case(agent, test)
        results.append((test['name'], success))

        # If running all tests, ask to continue
        if len(tests_to_run) > 1 and i < len(tests_to_run):
            print(f"\n{'=' * 80}")
            response = input(f"Continue to next test? [Y/n]: ").strip().lower()
            if response in ['n', 'no']:
                print("Stopping tests.")
                break

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
