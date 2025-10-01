"""Simple test without AI calls."""

from hs_agent.core.data_loader import HSDataLoader

def test_data_loading():
    """Test just the data loading functionality."""
    print("Testing HS data loading...")

    loader = HSDataLoader("data")
    loader.load_all_data()

    print(f"✅ Loaded {len(loader.codes_2digit)} 2-digit codes")
    print(f"✅ Loaded {len(loader.codes_4digit)} 4-digit codes")
    print(f"✅ Loaded {len(loader.codes_6digit)} 6-digit codes")
    print(f"✅ Loaded {len(loader.examples)} product examples")

    # Test search functionality
    print("\n🔍 Testing search for 'horse'...")
    candidates = loader.search_codes_by_description("horse", 2, limit=5)
    for code, hs_code, score in candidates:
        print(f"  {code}: {hs_code.description} (score: {score:.1f})")

    print("\n🔍 Testing search for 'computer'...")
    candidates = loader.search_codes_by_description("computer", 6, limit=3)
    for code, hs_code, score in candidates:
        print(f"  {code}: {hs_code.description} (score: {score:.1f})")

if __name__ == "__main__":
    test_data_loading()