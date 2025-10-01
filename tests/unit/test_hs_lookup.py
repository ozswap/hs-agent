"""Quick test of HS code description lookup."""

from hs_agent.core.data_loader import HSDataLoader

def test_hs_lookup():
    """Test HS code description lookup."""

    # Initialize and load data
    loader = HSDataLoader()
    loader.load_all_data()

    print(f"Loaded {len(loader.codes_6digit)} 6-digit HS codes")

    # Test the specific code from our mapping
    test_code = "901890"  # 9018.90 without the dot

    if test_code in loader.codes_6digit:
        hs_code = loader.codes_6digit[test_code]
        print(f"✅ Found {test_code}: {hs_code.description}")
    else:
        print(f"❌ Code {test_code} not found")

        # Try to find similar codes
        print("Looking for codes starting with 9018...")
        for code, hs_code in loader.codes_6digit.items():
            if code.startswith("9018"):
                print(f"  {code}: {hs_code.description}")

if __name__ == "__main__":
    test_hs_lookup()