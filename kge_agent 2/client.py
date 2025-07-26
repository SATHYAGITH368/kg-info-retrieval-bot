from python_a2a import A2AClient, Message, TextContent, MessageRole
import asyncio
import logging

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    AGENT_URL = "http://localhost:8004/a2a"

    client = A2AClient(AGENT_URL)
    logger.info(f"A2AClient initialized for agent at {AGENT_URL}")

    query_text = "Chandrayaan3 HasLaunchVehicle ?"
    logger.info(f" Sending message: {query_text}")

    message = Message(
        content=TextContent(text=query_text),
        role=MessageRole.USER
    )

    try:
        response = client.send_message(message)

        logger.info(" Received response from agent:")

        if response.content.type == "text":
            print(f"\n Agent Response:\n{response.content.text}")
        elif response.content.type == "error":
            logger.error(f" Agent returned an error: {response.content.message}")
        else:
            logger.error(f"Unexpected content type: {response.content.type}")

    except Exception as e:
        logger.error(f" Error communicating with agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
