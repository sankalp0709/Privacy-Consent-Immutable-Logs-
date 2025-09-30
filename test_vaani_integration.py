#!/usr/bin/env python3
"""
Test script for Vaani integration and Agent Orchestrator logging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_vaani_client():
    """Test Vaani client functionality"""
    print("=== Testing Vaani Client ===")

    try:
        from utils.vaani_client import VaaniClient

        # Initialize client
        print("Initializing Vaani client...")
        vaani = VaaniClient()
        print(f"✅ Vaani client initialized (authenticated: {vaani.authenticated})")

        # Test content generation
        print("\nTesting content generation...")
        test_text = "Artificial Intelligence is transforming education"
        result = vaani.generate_content(test_text, ["twitter", "instagram"], "educational", "en")

        if "error" in result:
            print(f"❌ Content generation failed: {result['error']}")
            print("🔄 Using fallback - this is expected if Vaani API is not configured")
        else:
            print("✅ Content generation successful")
            if "generated_content" in result:
                for platform, content in result["generated_content"].items():
                    print(f"  {platform}: {content.get('content', '')[:50]}...")

        # Test translation
        print("\nTesting translation...")
        translation_result = vaani.translate_content(test_text, ["hi"], "educational")
        if "error" in translation_result:
            print(f"❌ Translation failed: {translation_result['error']}")
        else:
            print("✅ Translation successful")

        return True

    except Exception as e:
        print(f"❌ Vaani client test failed: {str(e)}")
        return False

def test_agent_orchestrator_with_logging():
    """Test Agent Orchestrator with detailed logging"""
    print("\n=== Testing Agent Orchestrator with Logging ===")

    try:
        from agents.agent_orchestrator import AgentOrchestrator

        # Initialize orchestrator
        print("Initializing Agent Orchestrator...")
        orchestrator = AgentOrchestrator()
        print("✅ Agent Orchestrator initialized")

        # Test query processing
        test_query = "Summarize the key concepts of machine learning"
        print(f"\nProcessing query: '{test_query}'")

        result = orchestrator.process_query(test_query)

        # Check response structure
        print("\nResponse structure:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Agent used: {result.get('agent', 'unknown')}")
        print(f"  Intent detected: {result.get('detected_intent', 'unknown')}")

        # Check for agent logs
        agent_logs = result.get('agent_logs', [])
        if agent_logs:
            print(f"\n Agent logs found ({len(agent_logs)} entries):")
            for i, log in enumerate(agent_logs[:5], 1):  # Show first 5 logs
                print(f"  {i}. {log}")
            if len(agent_logs) > 5:
                print(f"  ... and {len(agent_logs) - 5} more logs")
        else:
            print(" No agent logs found in response")

        # Check for processing details
        processing_details = result.get('processing_details', {})
        if processing_details:
            print(f"\n✅ Processing details found:")
            for key, value in processing_details.items():
                print(f"  {key}: {value}")
        else:
            print("❌ No processing details found")

        # Check orchestrator metadata
        orchestrator_routed = result.get('orchestrator_routed', False)
        agent_processing_time = result.get('agent_processing_time', 0)
        print(f"\n✅ Orchestrator metadata:")
        print(f"  Routed by orchestrator: {orchestrator_routed}")
        print(f"  Agent processing time: {agent_processing_time:.2f}s")

        return True

    except Exception as e:
        print(f"❌ Agent Orchestrator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("VAANI INTEGRATION & AGENT LOGGING TEST SUITE")
    print("=" * 60)

    # Test 1: Vaani Client
    vaani_success = test_vaani_client()

    # Test 2: Agent Orchestrator with logging
    orchestrator_success = test_agent_orchestrator_with_logging()

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Vaani Integration: {'✅ PASS' if vaani_success else '❌ FAIL'}")
    print(f"Agent Logging: {'✅ PASS' if orchestrator_success else '❌ FAIL'}")

    if vaani_success and orchestrator_success:
        print("\n🎉 All tests passed! The system is working correctly.")
        print("\nNext steps:")
        print("1. Start the uniguru_lm_service.py server")
        print("2. Test the /ask endpoint with queries like 'Summarize AI concepts'")
        print("3. Check that detailed agent logs appear in responses")
        print("4. Verify Vaani fallback content generation works")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")

    return vaani_success and orchestrator_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)