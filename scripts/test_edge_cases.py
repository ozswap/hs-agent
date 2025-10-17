"""Test script for edge case handling in HS classification using WIDE NET workflow.

Tests the improved prompts with chapter notes comparison with:
1. Marketing fluff / ambiguous names
2. Services vs physical goods
3. Product codes without descriptions
4. Clear products (control group)
5. Products needing material specification
6. Ambiguous products needing chapter notes (e.g., guitar electric pedal)

NOTE: Using wide_net_classification workflow which:
- Explores multiple paths (1-N chapters, headings, subheadings)
- Uses chapter notes for final comparison
- Better at catching misclassifications
"""

import asyncio
from hs_agent.data_loader import HSDataLoader
from hs_agent.agent import HSAgent


# Test cases organized by category
TEST_CASES = {
    "Marketing Fluff / Ambiguous": [
        {
            "description": "A Scoop of Cuteness",
            "expected_behavior": "Should return 000000 - cannot determine product type",
            "notes": "Pure marketing language, could be toy, kitchen item, clothing, etc."
        },
        {
            "description": "Pluto Lilac",
            "expected_behavior": "Should return 000000 - cannot determine product type",
            "notes": "Color name without product type - perfume? clothing? paint?"
        },
        {
            "description": "The Classic Twist",
            "expected_behavior": "Should return 000000 - cannot determine product type",
            "notes": "Marketing name without product indication"
        },
        {
            "description": "Dreamy Delight Collection",
            "expected_behavior": "Should return 000000 - cannot determine product type",
            "notes": "Marketing collection name without product type"
        }
    ],

    "Services (Not Goods)": [
        {
            "description": "Shipping Protection by Route",
            "expected_behavior": "Should return 000000 - service not goods",
            "notes": "This is a service, not a physical product"
        },
        {
            "description": "Extended Warranty Protection",
            "expected_behavior": "Should return 000000 - service not goods",
            "notes": "Warranty is a service"
        }
    ],

    "Product Codes Without Context": [
        {
            "description": "114155 - TAUPE JANUS BUTTS - E",
            "expected_behavior": "Should recognize 'JANUS BUTTS' as leather terminology → 4107",
            "notes": "SKU with recognizable leather industry term"
        },
        {
            "description": "SKU-45732-BLK",
            "expected_behavior": "Should return 000000 - need product description",
            "notes": "Pure alphanumeric code without product info"
        }
    ],

    "Clear Products (Control - Should Work Well)": [
        {
            "description": "Guitar",
            "expected_behavior": "High confidence → 9202",
            "notes": "Clear product type, material not critical"
        },
        {
            "description": "Cotton T-Shirt",
            "expected_behavior": "High confidence → 6109",
            "notes": "Clear product + material specified"
        },
        {
            "description": "Laptop Computer",
            "expected_behavior": "High confidence → 8471",
            "notes": "Clear product type"
        },
        {
            "description": "Diamond Ring",
            "expected_behavior": "High confidence → 7113",
            "notes": "Clear product + material/gem type"
        },
        {
            "description": "Fresh Apples",
            "expected_behavior": "High confidence → 0808",
            "notes": "Clear product type"
        }
    ],

    "Material Missing (Should Handle)": [
        {
            "description": "Jagger Jacket",
            "expected_behavior": "Should ask for material or assume (cotton vs synthetic)",
            "notes": "Material critical for Ch 61 vs 62, should state assumption"
        },
        {
            "description": "Dress",
            "expected_behavior": "Should make material assumption and state it",
            "notes": "Material affects classification, should note alternatives"
        },
        {
            "description": "Boutique Trouser",
            "expected_behavior": "Should make material assumption with moderate confidence",
            "notes": "Need material for accurate classification"
        }
    ],

    "Chapter Notes Disambiguation (Wide Net Advantage)": [
        {
            "description": "Guitar Electric Pedal",
            "expected_behavior": "Should use chapter notes to select Ch 85 (electrical) over Ch 92 (musical)",
            "notes": "Ambiguous: could be Ch 85 (electrical equipment) or Ch 92 (musical instrument accessory). Chapter notes should clarify."
        },
        {
            "description": "Electric Guitar Amplifier",
            "expected_behavior": "Should classify to Ch 85 (electrical amplifiers) not Ch 92",
            "notes": "Chapter notes should clarify that amplifiers are electrical equipment"
        },
        {
            "description": "Piano Key",
            "expected_behavior": "Should classify as Ch 92 (parts of musical instruments)",
            "notes": "Parts of instruments should stay in Ch 92"
        }
    ]
}


async def test_classification(agent: HSAgent, description: str, max_selections: int = 2) -> dict:
    """Test a single classification using WIDE NET (multi-path) and return results."""
    try:
        result = await agent.classify_multi(description, max_selections=max_selections)
        return {
            "description": description,
            "final_code": result.final_selected_code,
            "confidence": result.final_confidence,
            "num_paths": len(result.paths),
            "paths": [f"Ch{p.chapter_code}→{p.heading_code}→{p.subheading_code}" for p in result.paths[:3]],  # Show first 3
            "final_reasoning": result.final_reasoning[:250] + "..." if len(result.final_reasoning) > 250 else result.final_reasoning,
            "comparison_summary": result.comparison_summary[:200] + "..." if result.comparison_summary and len(result.comparison_summary) > 200 else result.comparison_summary,
            "success": True
        }
    except Exception as e:
        return {
            "description": description,
            "error": str(e),
            "success": False
        }


async def run_tests():
    """Run all edge case tests."""
    print("=" * 80)
    print("EDGE CASE TESTING: Wide Net Workflow with Chapter Notes")
    print("=" * 80)
    print()

    # Initialize agent with WIDE NET workflow
    print("Initializing agent with WIDE NET workflow...")
    data_loader = HSDataLoader()
    data_loader.load_all_data()
    agent = HSAgent(data_loader, workflow_name="wide_net_classification")
    print("✅ Agent ready (using multi-path exploration + chapter notes comparison)\n")

    # Run tests by category
    for category, test_cases in TEST_CASES.items():
        print("=" * 80)
        print(f"CATEGORY: {category}")
        print("=" * 80)
        print()

        for test_case in test_cases:
            description = test_case["description"]
            expected = test_case["expected_behavior"]
            notes = test_case["notes"]

            print(f"📝 Test: {description}")
            print(f"   Expected: {expected}")
            print(f"   Notes: {notes}")
            print()

            # Run classification
            result = await test_classification(agent, description, max_selections=2)

            if result["success"]:
                print(f"   ✅ Final Code: {result['final_code']}")
                print(f"   📊 Confidence: {result['confidence']:.2%}")
                print(f"   🔀 Paths Explored: {result['num_paths']}")
                print(f"   📍 Path Examples: {', '.join(result['paths'])}")
                print(f"   💭 Final Reasoning: {result['final_reasoning']}")
                if result['comparison_summary']:
                    print(f"   📝 Comparison: {result['comparison_summary']}")

                # Evaluate against expectations
                if result["final_code"] == "000000":
                    print(f"   ✓ Correctly flagged as unclassifiable")
                elif result["final_code"].startswith("99"):
                    print(f"   ⚠️  Classified to Chapter 99 (unspecified commodities)")
                else:
                    print(f"   ℹ️  Classified normally")
            else:
                print(f"   ❌ Error: {result['error']}")

            print()
            print("-" * 80)
            print()

    print("=" * 80)
    print("Testing Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_tests())
