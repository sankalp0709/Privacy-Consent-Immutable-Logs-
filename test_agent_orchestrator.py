#!/usr/bin/env python3
"""
Test script for AgentOrchestrator functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_import():
    """Test basic import of AgentOrchestrator"""
    print("Testing basic import...")
    try:
        from agents.agent_orchestrator import AgentOrchestrator
        print("SUCCESS: AgentOrchestrator imported successfully")
        return True
    except Exception as e:
        print(f"FAILED: Import error - {str(e)}")
        return False

def test_initialization():
    """Test AgentOrchestrator initialization"""
    print("\nTesting initialization...")
    try:
        from agents.agent_orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        print("SUCCESS: AgentOrchestrator initialized successfully")
        return orchestrator
    except Exception as e:
        print(f"FAILED: Initialization error - {str(e)}")
        return None

def test_available_agents(orchestrator):
    """Test getting available agents"""
    print("\nTesting available agents...")
    try:
        agents_info = orchestrator.get_available_agents()
        available_agents = agents_info.get("available_agents", {})
        print(f"SUCCESS: Found {len(available_agents)} available agents:")
        for agent_name, agent_info in available_agents.items():
            print(f"  - {agent_name}: {agent_info.get('description', 'No description')}")
        return True
    except Exception as e:
        print(f"FAILED: Error getting agents - {str(e)}")
        return False

def test_intent_classification(orchestrator):
    """Test intent classification"""
    print("\nTesting intent classification...")
    test_queries = [
        ("Summarize this article about AI", "summarization"),
        ("Create a project plan for mobile app development", "planning"),
        ("Find documents about machine learning", "file_search"),
        ("What is the difference between supervised and unsupervised learning?", "qna")
    ]

    success_count = 0
    for query, expected_intent in test_queries:
        try:
            # Use the private method for testing
            detected_intent, confidence, scores = orchestrator._classify_intent(query)
            if detected_intent == expected_intent:
                print(f"SUCCESS: '{query[:30]}...' -> {detected_intent} (confidence: {confidence:.2f})")
                success_count += 1
            else:
                print(f"PARTIAL: '{query[:30]}...' -> {detected_intent} (expected {expected_intent}, confidence: {confidence:.2f})")
        except Exception as e:
            print(f"FAILED: '{query[:30]}...' -> Error: {str(e)}")

    print(f"Intent classification: {success_count}/{len(test_queries)} correct")
    return success_count > 0

def test_agent_routing(orchestrator):
    """Test agent routing (without full execution)"""
    print("\nTesting agent routing...")
    try:
        # Test routing logic without full execution
        test_query = "Summarize this document"
        intent, confidence, scores = orchestrator._classify_intent(test_query)

        # Check if the intent maps to an available agent
        agent = orchestrator.agents.get(intent)

        if agent:
            print(f"SUCCESS: Query would route to {agent.name} for intent '{intent}' (confidence: {confidence:.2f})")
            return True
        else:
            print(f"FAILED: No agent available for intent '{intent}'")
            return False
    except Exception as e:
        print(f"FAILED: Routing error - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("AGENT ORCHESTRATOR TEST SUITE")
    print("=" * 60)

    # Test 1: Basic import
    if not test_basic_import():
        print("\nCRITICAL: Cannot import AgentOrchestrator. Check installation.")
        return False

    # Test 2: Initialization
    orchestrator = test_initialization()
    if not orchestrator:
        print("\nCRITICAL: Cannot initialize AgentOrchestrator.")
        return False

    # Test 3: Available agents
    if not test_available_agents(orchestrator):
        print("\nWARNING: Cannot get available agents list.")

    # Test 4: Intent classification
    if not test_intent_classification(orchestrator):
        print("\nWARNING: Intent classification may not be working properly.")

    # Test 5: Agent routing
    if not test_agent_routing(orchestrator):
        print("\nWARNING: Agent routing may not be working properly.")

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the uniguru_lm_service.py server: python uniguru_lm_service.py")
    print("2. Test the /ask endpoint with Postman or curl")
    print("3. Check the logs for any errors during API calls")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)