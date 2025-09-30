#!/usr/bin/env python3
"""
Test script to verify AgentOrchestrator integration in MCP Bridge
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_orchestrator_in_mcp():
    """Test that MCP Bridge uses AgentOrchestrator"""
    print("Testing MCP Bridge with AgentOrchestrator...")

    try:
        from mcp_bridge import agent_orchestrator
        print("✓ AgentOrchestrator imported successfully")

        # Test orchestrator initialization
        if hasattr(agent_orchestrator, 'agents'):
            print(f"✓ AgentOrchestrator has {len(agent_orchestrator.agents)} agents")
        else:
            print("✗ AgentOrchestrator not properly initialized")
            return False

        # Test a simple query
        result = agent_orchestrator.process_query("Summarize AI concepts")
        print("✓ AgentOrchestrator processed query successfully")

        # Check for orchestrator metadata
        if result.get("orchestrator_routed"):
            print("✓ Query was routed through orchestrator")
        else:
            print("✗ Query was not routed through orchestrator")
            return False

        if result.get("detected_intent"):
            print(f"✓ Intent detected: {result.get('detected_intent')}")
        else:
            print("✗ No intent detected")
            return False

        if result.get("agent_logs"):
            print(f"✓ Agent logs present: {len(result.get('agent_logs'))} entries")
        else:
            print("✗ No agent logs found")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("AGENT ORCHESTRATOR INTEGRATION TEST")
    print("=" * 50)

    success = test_orchestrator_in_mcp()

    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: AgentOrchestrator is properly integrated!")
        print("\nNow all queries through MCP Bridge will:")
        print("• Go through intent classification")
        print("• Use intelligent agent routing")
        print("• Include detailed agent logs")
        print("• Provide processing metadata")
    else:
        print("FAILED: AgentOrchestrator integration issues found")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)