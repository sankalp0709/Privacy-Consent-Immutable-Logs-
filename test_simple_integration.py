#!/usr/bin/env python3
"""
Simple test for Vaani integration and Agent Orchestrator logging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_vaani_fallback():
    """Test Vaani fallback functionality"""
    print("Testing Vaani fallback...")

    try:
        from utils.vaani_client import VaaniClient

        vaani = VaaniClient()
        print(f"Vaani initialized (authenticated: {vaani.authenticated})")

        # Test content generation (should work with fallback if API fails)
        result = vaani.generate_content("Test content", ["twitter"], "neutral", "en")

        if "generated_content" in result:
            print("SUCCESS: Content generation working")
            print(f"Generated for platforms: {list(result['generated_content'].keys())}")
            return True
        else:
            print("FAILED: Content generation not working")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def test_agent_logging():
    """Test Agent Orchestrator logging"""
    print("\nTesting Agent Orchestrator logging...")

    try:
        from agents.agent_orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_query("Summarize AI concepts")

        agent_logs = result.get('agent_logs', [])
        if agent_logs and len(agent_logs) > 0:
            print(f"SUCCESS: Found {len(agent_logs)} agent logs")
            print(f"Sample log: {agent_logs[0][:50]}...")
            return True
        else:
            print("FAILED: No agent logs found")
            return False

    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def main():
    print("INTEGRATION TEST SUITE")
    print("=" * 40)

    vaani_ok = test_vaani_fallback()
    agent_ok = test_agent_logging()

    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"Vaani Fallback: {'PASS' if vaani_ok else 'FAIL'}")
    print(f"Agent Logging: {'PASS' if agent_ok else 'FAIL'}")

    if vaani_ok and agent_ok:
        print("\nSUCCESS: All integrations working!")
        print("\nYou can now:")
        print("1. Start uniguru_lm_service.py")
        print("2. Test /ask endpoint with queries")
        print("3. Check detailed agent logs in responses")
    else:
        print("\nSome tests failed - check errors above")

    return vaani_ok and agent_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)