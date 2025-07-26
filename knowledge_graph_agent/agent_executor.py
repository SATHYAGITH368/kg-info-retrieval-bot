from python_a2a import A2AServer, Message, TextContent, MessageRole, ErrorContent
from kg_pipeline.job_offer_kg_agent_skills import JobOfferKGSkills


class JobOfferKGAgent(A2AServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.skills = JobOfferKGSkills()

    def handle_message(self, message: Message) -> Message:
        try:
            response_text = self.skills.build_kg_from_job_offer()
            content = TextContent(text=response_text)
        except Exception as e:
            # if anything fails, return as ErrorContent
            content = ErrorContent(message=str(e))

        return Message(
            content=content,
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )
