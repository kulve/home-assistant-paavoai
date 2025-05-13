from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
    SpeechResponse,
)
from homeassistant.core import HomeAssistant
import logging

_LOGGER = logging.getLogger(__name__)

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
        _LOGGER.debug(f"PaavoAI processing: '{user_input.text}' for conversation_id: {user_input.conversation_id}")
        # TODO: Move to config flow
        response_text = "Sorry, I was unable to process your request."
        try:
            response_text = await self.hass.async_add_executor_job(
                self.client.get_response, user_input.text
            )
            if not response_text:
                _LOGGER.warning(f"Ollama client returned empty response for: '{user_input.text}'")
                response_text = "I received an empty response, so I'm not sure how to reply."

        except Exception as e:
            _LOGGER.error(f"Error during PaavoAI async_process: {e}", exc_info=e)
            response_text = f"An error occurred: {e}"


        # Create a SpeechResponse object
        speech_response = SpeechResponse(
            speech={"plain": {"speech": response_text}},
            language=user_input.language,
        )

        return ConversationResult(
            response=speech_response,
            conversation_id=user_input.conversation_id,
        )
