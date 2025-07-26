from python_a2a import (
    A2AServer,
    Message,
    MessageRole,
    TextContent,
    ErrorContent,
)

from kge_pipeline.kge import DistMultKnowledgeGraphEmbedding


class KGEAgent(A2AServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kge = DistMultKnowledgeGraphEmbedding()

    def handle_message(self, message: Message) -> Message:
        try:
            query_text = message.content.text
            results = self.kge.query_knowledge_graph(query_text)

            if not results:
                response_text = "No results found."
            else:
                lines = []
                for h, r, t, score in results:
                    lines.append(f"{h} — {r} — {t} (score: {score:.4f})")
                response_text = "\n".join(lines)

            content = TextContent(text=response_text)

        except Exception as e:
            content = ErrorContent(message=str(e))

        return Message(
            content=content,
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )
