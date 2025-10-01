"""Test script to verify Langfuse integration works."""

import os
from dotenv import load_dotenv
from langfuse import get_client

# Load environment variables
load_dotenv()

def test_langfuse_connection():
    """Test Langfuse connection and authentication."""

    print("Testing Langfuse connection...")

    # Check if environment variables are set
    required_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False

    print(f"✅ Environment variables found")
    print(f"   Host: {os.getenv('LANGFUSE_HOST')}")
    print(f"   Public Key: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10]}...")

    # Test connection
    try:
        langfuse = get_client()

        if langfuse.auth_check():
            print("✅ Langfuse authentication successful!")

            # Create a test trace
            with langfuse.start_as_current_span(
                name="test-trace",
                input="Test input for HS agent",
                metadata={"test": True}
            ) as span:
                span.update_trace(
                    output="Test output",
                    tags=["test", "hs-agent"]
                )
                span.score_trace(name="test_score", value=1.0, data_type="NUMERIC")

            langfuse.flush()
            print("✅ Test trace created successfully!")
            return True

        else:
            print("❌ Langfuse authentication failed!")
            return False

    except Exception as e:
        print(f"❌ Error connecting to Langfuse: {e}")
        return False

if __name__ == "__main__":
    test_langfuse_connection()