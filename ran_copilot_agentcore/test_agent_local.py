"""
Local test script for the agent before deploying to AgentCore.
This simulates the AgentCore Runtime environment locally.
"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test 1: Check if strands imports work
print("Test 1: Testing Strands imports...")
try:
    from strands import Agent, tool
    print("[OK] Strands imports successful")
except ImportError as e:
    print(f"[FAIL] Strands import failed: {e}")
    sys.exit(1)

# Test 2: Create a simple agent
print("\nTest 2: Creating a basic agent...")
try:
    # According to Strands docs, the simplest initialization
    agent = Agent()
    print("[OK] Agent created successfully with default settings")
except Exception as e:
    print(f"[FAIL] Agent creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test agent with a simple query
print("\nTest 3: Testing agent with a simple query...")
try:
    response = agent("Hello, who are you?")
    print(f"[OK] Agent responded: {response[:100]}...")
except Exception as e:
    print(f"[FAIL] Agent query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create agent with a tool
print("\nTest 4: Creating agent with a mock tool...")
try:
    @tool()
    def test_tool(input_text: str) -> str:
        """A simple test tool."""
        return f"Tool received: {input_text}"
    
    agent_with_tool = Agent(tools=[test_tool])
    print("[OK] Agent with tool created successfully")
except Exception as e:
    print(f"[FAIL] Agent with tool creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test the FastAPI app endpoints locally
print("\nTest 5: Testing FastAPI app import...")
try:
    from agent.app import app, ping
    print("[OK] FastAPI app imported successfully")
except Exception as e:
    print(f"[FAIL] FastAPI app import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("All local tests passed!")
print("="*50)
print("\nYou can now start the local server with:")
print("  cd ran_copilot_agentcore")
print("  python src/agent/app.py")
print("\nThen test the endpoints:")
print("  curl http://localhost:8080/ping")
print("  curl -X POST http://localhost:8080/invocations -H 'Content-Type: application/json' -d '{\"inputText\": \"Hello\"}'")

