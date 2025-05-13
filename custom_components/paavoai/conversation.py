from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.core import HomeAssistant


class PaavoAIConversationAgent(AbstractConversationAgent):
    def __init__(self, hass: HomeAssistant, config_data: dict, client):
        self.hass = hass
        self.config_data = config_data
        self.client = client

    @property
    def supported_languages(self):
        return ["en", "fi"]

    @property
    def attribution(self) -> dict:
        """Return attribution for the agent."""

        return {
            "name": "Powered by Ollama",
            # "url": "URL_TO_OLLAMA_OR_YOUR_PROJECT" # Optional
        }

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        # TODO: Call OllamaClient synchronously for simplicity; you may want to use async
        response = await self.hass.async_add_executor_job(
            self.client.get_response, user_input.text
        )
        return ConversationResult(
            response=response,
            conversation_id=user_input.conversation_id,
        )
