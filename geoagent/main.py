from python_a2a import run_server
from agent_executor import InsituGeoAgent

if __name__ == "__main__":
    agent = InsituGeoAgent()
    run_server(agent, host="0.0.0.0", port=8004)
