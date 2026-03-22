"""Test script to verify surfa-ingest instrumentation."""

import asyncio
import os
from dotenv import load_dotenv
from src.surfa_mcp.analytics import get_analytics_client, track_tool

# Load .env file
load_dotenv()


async def test_analytics_client():
    """Test that analytics client is created correctly."""
    print("Testing analytics client...")
    
    # Check if SURFA_INGEST_KEY is set
    ingest_key = os.getenv("SURFA_INGEST_KEY")
    if not ingest_key:
        print("❌ SURFA_INGEST_KEY not set - analytics will be disabled")
        print("   Set it in .env to enable dogfooding")
        return
    
    print(f"✅ SURFA_INGEST_KEY found: {ingest_key[:20]}...")
    
    # Get analytics client
    client = get_analytics_client()
    if client is None:
        print("❌ Analytics client is None")
        return
    
    print(f"✅ Analytics client created")
    print(f"   Session ID: {client.session_id}")
    print(f"   API URL: {client.api_url}")


@track_tool("test_tool")
async def test_tracked_function(param1: str, param2: int):
    """Test function with tracking decorator."""
    print(f"   Executing test_tool with param1={param1}, param2={param2}")
    await asyncio.sleep(0.1)  # Simulate work
    return {"result": "success"}


async def test_tool_tracking():
    """Test that tool tracking works."""
    print("\nTesting tool tracking...")
    
    try:
        result = await test_tracked_function("test_value", 42)
        print(f"✅ Tool executed successfully: {result}")
        print("   Check your Surfa dashboard for the 'test_tool' event!")
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")


async def main():
    """Run all tests."""
    print("=== Surfa MCP Dogfooding Test ===\n")
    
    await test_analytics_client()
    await test_tool_tracking()
    
    # Flush events
    from src.surfa_mcp.analytics import flush_analytics
    print("\nFlushing analytics...")
    flush_analytics()
    print("✅ Done! Check your Surfa dashboard.")


if __name__ == "__main__":
    asyncio.run(main())
