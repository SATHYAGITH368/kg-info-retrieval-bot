from python_a2a import A2AClient, Message, TextContent, MessageRole
import asyncio
import logging
import json

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    AGENT_URL = "http://localhost:8004/a2a"

    # Initialize A2A client
    client = A2AClient(AGENT_URL)
    logger.info(f"A2AClient initialized for agent at {AGENT_URL}")

    # Choose method: "bm25" or "embedding"
    method = "embedding"  # or "embedding"
    query_text = {
        "query": "When does the peak of TPW over the Arabian Sea occur in relation to the monsoon onset over Kerala?",
        "method": method
    }
    logger.info(f"Sending query: {query_text}")

    message = Message(
        content=TextContent(text=json.dumps(query_text)),
        role=MessageRole.USER
    )

    try:
        # Send message to agent
        response = client.send_message(message)

        # Print response
        logger.info("Received response from agent:")
        if hasattr(response.content, "text"):
            print(f"\nAgent:\n{response.content.text}")
        else:
            print(f"\nAgent error: {getattr(response.content, 'error', str(response.content))}")

    except Exception as e:
        logger.error(f"Error communicating with agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())