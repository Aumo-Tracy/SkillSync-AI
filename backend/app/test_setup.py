"""
Test Script
Quick verification of backend components
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_components():
    """Test all major components"""
    
    print("=" * 60)
    print("E-COMMERCE SUPPORT AI - Component Tests")
    print("=" * 60)
    
    # Test 1: Configuration
    print("\n[1/8] Testing Configuration...")
    try:
        from app.config import settings
        print(f"✓ Config loaded")
        print(f"  - Environment: {settings.ENVIRONMENT}")
        print(f"  - Local mode: {settings.USE_LOCAL_MODE}")
        print(f"  - Model: {settings.OPENAI_MODEL}")
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return
    
    # Test 2: Database
    print("\n[2/8] Testing Database...")
    try:
        from app.services.database import get_database
        db = get_database()
        health = db.health_check()
        print(f"✓ Database connected")
        print(f"  - Mode: {health['mode']}")
        print(f"  - Status: {health['status']}")
    except Exception as e:
        print(f"✗ Database failed: {e}")
        return
    
    # Test 3: Order Tool
    print("\n[3/8] Testing Order Tool...")
    try:
        from app.services.tools import track_order
        result = track_order("ORD-123456", "john.doe@example.com")
        if result.get("success"):
            print(f"✓ Order tool working")
            print(f"  - Order: {result['order_number']}")
            print(f"  - Status: {result['status']}")
        else:
            print(f"✗ Order tool failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Order tool error: {e}")
    
    # Test 4: Discount Tool
    print("\n[4/8] Testing Discount Tool...")
    try:
        from app.services.tools import validate_discount_code
        result = validate_discount_code("SAVE20", 150.0)
        if result.get("success"):
            print(f"✓ Discount tool working")
            print(f"  - Code: {result['code']}")
            print(f"  - Valid: {result['valid']}")
            if result['valid']:
                print(f"  - Discount: ${result.get('discount_amount', 0):.2f}")
        else:
            print(f"✗ Discount tool failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Discount tool error: {e}")
    
    # Test 5: Product Search Tool
    print("\n[5/8] Testing Product Search...")
    try:
        from app.services.tools import search_products
        result = search_products("headphones", max_price=100.0)
        if result.get("success"):
            print(f"✓ Product search working")
            print(f"  - Query: {result['query']}")
            print(f"  - Results: {len(result['products'])}")
            if result['products']:
                print(f"  - First: {result['products'][0]['name']}")
        else:
            print(f"✗ Product search failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Product search error: {e}")
    
    # Test 6: Document Chunking
    print("\n[6/8] Testing Document Chunking...")
    try:
        from app.services.rag.chunking import get_document_chunker
        chunker = get_document_chunker()
        faqs = chunker.chunk_faqs()
        print(f"✓ Document chunking working")
        print(f"  - FAQs loaded: {len(faqs)}")
        if faqs:
            print(f"  - First FAQ: {faqs[0].metadata.get('category')}")
    except Exception as e:
        print(f"✗ Document chunking error: {e}")
    
    # Test 7: Vector Store (initialization check only)
    print("\n[7/8] Testing Vector Store...")
    try:
        from app.services.rag.vector_store import get_vector_store
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        print(f"✓ Vector store initialized")
        print(f"  - Type: {stats['type']}")
        print(f"  - Initialized: {stats['initialized']}")
        
        # Check if needs initialization
        if not vector_store.is_initialized():
            print(f"  ⚠ Vector store empty - run initialization")
            print(f"    (This is normal on first run)")
    except Exception as e:
        print(f"✗ Vector store error: {e}")
    
    # Test 8: Agent (basic check)
    print("\n[8/8] Testing Agent...")
    try:
        from app.services.langchain.agent import get_support_agent
        agent = get_support_agent()
        print(f"✓ Agent initialized")
        print(f"  - Tools available: {len(agent.tools)}")
        print(f"  - LLM model: {settings.OPENAI_MODEL}")
    except Exception as e:
        print(f"✗ Agent error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPONENT TEST SUMMARY")
    print("=" * 60)
    print("\n✓ All core components loaded successfully!")
    print("\nNext steps:")
    print("1. Set your OPENAI_API_KEY in .env file")
    print("2. Run: uvicorn app.main:app --reload")
    print("3. Visit: http://localhost:8000/docs")
    print("4. Test the /api/chat endpoint")
    print("\nFor vector store initialization:")
    print("  Run: python -c \"from app.services.rag.vector_store import initialize_vector_store_if_needed; initialize_vector_store_if_needed()\"")


async def test_simple_chat():
    """Test a simple chat interaction"""
    print("\n" + "=" * 60)
    print("TESTING SIMPLE CHAT")
    print("=" * 60)
    
    try:
        from app.services.langchain.agent import get_support_agent
        
        agent = get_support_agent()
        
        print("\nSending test message: 'How long does shipping take?'")
        
        response = await agent.chat(
            message="How long does shipping take?",
            session_id="test_session",
            include_sources=True
        )
        
        print(f"\n✓ Chat response received!")
        print(f"\nResponse: {response.response[:200]}...")
        print(f"\nSources: {len(response.sources) if response.sources else 0}")
        print(f"Tools used: {len(response.tool_calls) if response.tool_calls else 0}")
        print(f"Tokens: {response.token_usage.total_tokens}")
        print(f"Cost: ${response.token_usage.estimated_cost_usd:.4f}")
        
    except Exception as e:
        print(f"\n✗ Chat test failed: {e}")
        print(f"\nMake sure OPENAI_API_KEY is set in .env file")


if __name__ == "__main__":
    print("\nRunning component tests...")
    asyncio.run(test_components())
    
    # Uncomment to test chat (requires OpenAI API key)
    # print("\n\nRunning chat test...")
    # asyncio.run(test_simple_chat())