from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.core import HomeAssistant
from .ollama_client import OllamaClient

class PaavoAIConversationAgent(AbstractConversationAgent):
    def __init__(self, hass: HomeAssistant, config):
        self.hass = hass
        self.config = config
        self.client = OllamaClient(
            config["host"], config["port"], config["model"]
        )

    @property
    def supported_languages(self):
        return ["en", "fi"]

    @property
    def attribution(self):
        return "Powered by Ollama"

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        # Call OllamaClient synchronously for simplicity; you may want to use async
        response = await self.hass.async_add_executor_job(
            self.client.get_response, user_input.text
        )
        return ConversationResult(
            response=response,
            conversation_id=user_input.conversation_id,
        )

