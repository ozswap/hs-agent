"""Test the search fix specifically."""

from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.models import ClassificationLevel

def test_search_fix():
    loader = HSDataLoader("data")
    loader.load_all_data()

    # Create agent instance to test the _search_within_codes method
    agent = HSClassificationAgent(loader, "gemini-2.5-flash")

    product = "Laptop computer Intel processor"

    # Test 4-digit codes under Chapter 84
    all_4digit = loader.get_codes_by_level(4)
    chapter_84_codes = {
        code: hs_code for code, hs_code in all_4digit.items()
        if code.startswith("84")
    }

    print(f"Testing search for '{product}' in Chapter 84 (4-digit level)")
    print(f"Total 4-digit codes in Chapter 84: {len(chapter_84_codes)}")

    # Use the agent's search method
    candidates = agent._search_within_codes(product, chapter_84_codes, 4, limit=10)

    print(f"Found {len(candidates)} candidates:")
    for code, hs_code, score in candidates:
        print(f"  {code}: {hs_code.description[:60]}... (score: {score})")

if __name__ == "__main__":
    test_search_fix()