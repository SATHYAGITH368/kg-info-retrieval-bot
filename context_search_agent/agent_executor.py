from python_a2a import A2AServer, Message, TextContent, MessageRole
from agent_skills import AgentSkills
import ollama

class ContextSearchAgent(A2AServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_skills = AgentSkills()

    def handle_message(self, message: Message) -> Message:
        try:
            query_text = message.content.text.strip()
            method = "embedding"  # or "bm25"
            top_k = 5
            rerank = True

            results = self.agent_skills.search_context(
                query=query_text,
                top_k=top_k,
                method=method,
                rerank=rerank
            )

            if not results:
                response_text = "No relevant documents found for your query."
            else:
                # Prepare text snippets for the prompt
                snippets = []
                for i, res in enumerate(results, 1):
                    chunk = res.get("chunk", "").strip()
                    snippets.append(f"Result {i}:\n{chunk}")

                combined_text = "\n\n---\n\n".join(snippets)

                prompt = (
                    f"You are a helpful assistant. Summarize the following search results in a clear, concise, and natural way.\n"
                    f"Explain the main points relevant to this query:\n\n"
                    f"Query: {query_text}\n\n"
                    f"Search Results:\n{combined_text}\n\n"
                    f"Please provide a friendly summary for a user."
                )

                # Call Ollama chat model (change model name if needed)
                response = ollama.chat(
                    model="llama3",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                explanation = response["message"]["content"].strip()
                response_text = explanation

            return self._build_response(message, response_text)

        except Exception as e:
            return self._build_response(message, f"ContextSearchAgent error: {str(e)}")

    def _build_response(self, message, text):
        return Message(
            content=TextContent(text=text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )
