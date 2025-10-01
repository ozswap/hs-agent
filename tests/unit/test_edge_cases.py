"""Test edge cases and error handling."""

from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.core.models import ClassificationLevel
import asyncio

def test_edge_cases():
    """Test various edge cases."""
    loader = HSDataLoader("data")
    loader.load_all_data()

    print("=== TESTING EDGE CASES ===")

    # Test 1: Empty query
    print("\n1. Testing empty query:")
    try:
        results = loader.search_codes_by_description("", 2, limit=5)
        print(f"   Empty query returned {len(results)} results")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Query with no matches
    print("\n2. Testing query with no matches:")
    try:
        results = loader.search_codes_by_description("xyzabc123nonexistent", 2, limit=5)
        print(f"   No-match query returned {len(results)} results")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Query with special characters
    print("\n3. Testing query with special characters:")
    try:
        results = loader.search_codes_by_description("horses!!!@#$%", 2, limit=5)
        print(f"   Special chars query returned {len(results)} results")
        for code, hs_code, score in results[:2]:
            print(f"     {code}: {score}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: Very long query
    print("\n4. Testing very long query:")
    long_query = "horse " * 100
    try:
        results = loader.search_codes_by_description(long_query, 2, limit=5)
        print(f"   Long query returned {len(results)} results")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 5: Invalid level
    print("\n5. Testing invalid level:")
    try:
        results = loader.search_codes_by_description("horse", 3, limit=5)  # Level 3 doesn't exist
        print(f"   Invalid level returned {len(results)} results")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 6: Test candidate filtering with non-existent parent
    print("\n6. Testing filtering with non-existent parent:")
    try:
        agent = HSClassificationAgent(loader, "gemini-2.5-flash")
        all_codes = loader.get_codes_by_level(4)
        filtered = {code: hs_code for code, hs_code in all_codes.items() if code.startswith("99")}
        print(f"   Filtered codes with parent '99': {len(filtered)}")

        if len(filtered) == 0:
            candidates = agent._search_within_codes("test", filtered, 4, 10)
            print(f"   Search within empty set returned: {len(candidates)} candidates")
    except Exception as e:
        print(f"   Error: {e}")

async def test_async_edge_cases():
    """Test async edge cases."""
    print("\n=== TESTING ASYNC EDGE CASES ===")

    loader = HSDataLoader("data")
    loader.load_all_data()

    # Test with malformed input
    print("\n7. Testing classification with empty product description:")
    try:
        agent = HSClassificationAgent(loader, "gemini-2.5-flash")
        result = await agent.classify_at_level("", ClassificationLevel.CHAPTER, top_k=5)
        print(f"   Empty description classification succeeded: {result.selected_code}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_edge_cases()
    # asyncio.run(test_async_edge_cases())  # Uncomment to test async cases