from python_a2a import A2AClient, Message, TextContent, MessageRole
import logging

print("client1.py loaded")


def main():
    print("Starting client1.py main loop")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    AGENT_URL = "http://localhost:8003/a2a"

    client = A2AClient(AGENT_URL)
    logger.info(f"A2AClient initialized for agent at {AGENT_URL}")

    user_input = input(
        "\nWhat knowledge graph do you want to build? (satellite / radar / insitu): "
    ).strip().lower()

    if user_input not in {"satellite", "radar", "insitu"}:
        print(f" Invalid input: {user_input}. Defaulting to 'radar'.")
        user_input = "radar"

    message_text = f"build {user_input}"

    logger.info(f"Sending message: {message_text}")

    message = Message(
        content=TextContent(text=message_text),
        role=MessageRole.USER
    )

    try:
        print("Sending message to agent...")
        response = client.send_message(message)
        print("Received response from agent.")
        logger.info(" Received response from agent:")

        if hasattr(response.content, "text"):
            print(f"\nAgent:\n{response.content.text}")
        else:
            print(f"\nAgent returned an unexpected response: {response.content}")

    except Exception as e:
        logger.error(f" Error communicating with agent: {e}")


if __name__ == "__main__":
    main()
