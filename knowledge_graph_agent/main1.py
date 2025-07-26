from python_a2a import run_server
from agent_executor1 import KGAgentExecutor
import traceback

if __name__ == "__main__":
    try:
        agent = KGAgentExecutor()
        print("Starting A2A server on http://0.0.0.0:8003/a2a")
        run_server(agent, host="0.0.0.0", port=8003, debug=True)
    except Exception as e:
        print("Exception in main1.py:", e)
        traceback.print_exc()
