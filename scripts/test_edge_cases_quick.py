"""Quick test of critical edge cases with wide net workflow."""

import asyncio
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


# Just the most critical test cases
CRITICAL_CASES = [
    {
        "name": "Marketing Fluff",
        "description": "A Scoop of Cuteness",
        "expected": "Should return low conf or 000000 - ambiguous",
    },
    {
        "name": "Service",
        "description": "Shipping Protection by Route",
        "expected": "Should return 000000 - service not goods",
    },
    {
        "name": "Guitar (Control)",
        "description": "Guitar",
        "expected": "High conf → Ch 92",
    },
    {
        "name": "Guitar Pedal (Ch Notes Needed)",
        "description": "Guitar Electric Pedal",
        "expected": "Ch 85 (electrical) not Ch 92 (musical) - needs chapter notes",
    },
    {
        "name": "Guitar Amplifier (Ch Notes Needed)",
        "description": "Electric Guitar Amplifier",
        "expected": "Ch 85 (amplifiers are electrical) not Ch 92",
    },
]


async def main():
    print("=" * 80)
    print("QUICK EDGE CASE TEST: Wide Net with Chapter Notes")
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
    for i, test in enumerate(CRITICAL_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(CRITICAL_CASES)}: {test['name']}")
        print(f"{'=' * 80}")
        print(f"📝 Description: \"{test['description']}\"")
        print(f"🎯 Expected: {test['expected']}")
        print()

        try:
            result = await agent.classify_multi(test['description'], max_selections=2)

            print(f"✅ RESULT:")
            print(f"   Final Code: {result.final_selected_code}")
            print(f"   Confidence: {result.final_confidence:.1%}")
            print(f"   Paths Explored: {len(result.paths)}")
            print(f"   Sample Paths:")
            for j, path in enumerate(result.paths[:3], 1):
                print(f"     {j}. Ch{path.chapter_code} → {path.heading_code} → {path.subheading_code} (conf: {path.path_confidence:.1%})")

            print(f"\n   💭 Final Reasoning:")
            reasoning_lines = result.final_reasoning.split('\n')
            for line in reasoning_lines[:5]:  # First 5 lines
                print(f"      {line}")
            if len(reasoning_lines) > 5:
                print(f"      ... ({len(reasoning_lines) - 5} more lines)")

            if result.comparison_summary:
                print(f"\n   📝 Chapter Notes Comparison:")
                comp_lines = result.comparison_summary.split('\n')
                for line in comp_lines[:3]:
                    print(f"      {line}")
                if len(comp_lines) > 3:
                    print(f"      ... ({len(comp_lines) - 3} more lines)")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'=' * 80}")
    print("TESTS COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(main())
