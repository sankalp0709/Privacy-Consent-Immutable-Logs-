#!/usr/bin/env python3
"""
Test script for RAG API integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.rag_client import rag_client
from agents.KnowledgeAgent import KnowledgeAgent

def test_rag_client():
    """Test the RAG client directly"""
    print("[TEST] Testing RAG Client...")

    try:
        result = rag_client.query("what is vedas", top_k=3)
        print(f"[SUCCESS] RAG Client Response Status: {result['status']}")
        print(f"[INFO] Results Count: {len(result.get('response', []))}")
        if result.get('groq_answer'):
            print(f"[INFO] Groq Answer: {result['groq_answer'][:100]}...")
        return True
    except Exception as e:
        print(f"[ERROR] RAG Client Test Failed: {str(e)}")
        return False

def test_knowledge_agent():
    """Test the KnowledgeAgent with RAG integration"""
    print("\n[TEST] Testing KnowledgeAgent...")

    try:
        agent = KnowledgeAgent()
        result = agent.query("what is artificial intelligence", top_k=3)

        print(f"[SUCCESS] KnowledgeAgent Response Status: {result['status']}")
        print(f"[INFO] Results Count: {len(result.get('response', []))}")
        if result.get('groq_answer'):
            print(f"[INFO] Groq Answer: {result['groq_answer'][:100]}...")
        return True
    except Exception as e:
        print(f"[ERROR] KnowledgeAgent Test Failed: {str(e)}")
        return False

def test_agent_run():
    """Test the full agent run method"""
    print("\n[TEST] Testing KnowledgeAgent Run Method...")

    try:
        agent = KnowledgeAgent()
        result = agent.run("explain machine learning", model="knowledge_agent")

        print(f"[SUCCESS] Agent Run Status: {result['status']}")
        print(f"[INFO] Response Length: {len(result.get('response', ''))}")
        if result.get('groq_answer'):
            print(f"[INFO] Groq Answer Available: {len(result['groq_answer'])} chars")
        return True
    except Exception as e:
        print(f"[ERROR] Agent Run Test Failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(">>> Starting RAG Integration Tests")
    print("=" * 50)

    tests = [
        ("RAG Client", test_rag_client),
        ("KnowledgeAgent Query", test_knowledge_agent),
        ("KnowledgeAgent Run", test_agent_run)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n[RUNNING] {test_name}")
        if test_func():
            passed += 1
            print(f"[PASS] {test_name}: PASSED")
        else:
            print(f"[FAIL] {test_name}: FAILED")

    print("\n" + "=" * 50)
    print(f"[RESULTS] Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! RAG integration is working correctly.")
        return 0
    else:
        print("[WARNING] Some tests failed. Please check the integration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())