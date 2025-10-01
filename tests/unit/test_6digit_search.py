"""Test 6-digit search specifically."""

from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.core.data_loader import HSDataLoader

def test_6digit_search():
    loader = HSDataLoader("data")
    loader.load_all_data()

    agent = HSClassificationAgent(loader, "gemini-2.5-flash")

    product = "Laptop computer Intel processor"

    # Get 6-digit codes under 8471
    all_6digit = loader.get_codes_by_level(6)
    heading_8471_codes = {
        code: hs_code for code, hs_code in all_6digit.items()
        if code.startswith("8471")
    }

    print(f"Testing 6-digit search for '{product}' under heading 8471")
    print(f"Total 6-digit codes under 8471: {len(heading_8471_codes)}")

    candidates = agent._search_within_codes(product, heading_8471_codes, 6, limit=10)

    print(f"Found {len(candidates)} candidates:")
    for code, hs_code, score in candidates:
        print(f"  {code}: {hs_code.description[:80]}... (score: {score})")

    if len(candidates) == 0:
        print("\n❌ No candidates found! Let's debug...")
        print("Manual scoring test:")
        for code, hs_code in heading_8471_codes.items():
            desc_lower = hs_code.description.lower()
            print(f"  {code}: {desc_lower}")
            print(f"    Contains 'portable': {'portable' in desc_lower}")
            print(f"    Contains 'processing': {'processing' in desc_lower}")
            print(f"    Contains 'central': {'central' in desc_lower}")
            print()

if __name__ == "__main__":
    test_6digit_search()