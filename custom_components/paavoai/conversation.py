from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.helpers.intent import IntentResponse
from homeassistant.core import HomeAssistant
import logging
import re

_LOGGER = logging.getLogger(__name__)

class PaavoAIConversationAgent(AbstractConversationAgent):
    def __init__(self, hass: HomeAssistant, config_data: dict, client):
        self.hass = hass
        self.config_data = config_data
        self.client = client

    @property
    def supported_languages(self):
        return ["fi"]

    @property
    def attribution(self) -> dict:
        """Return attribution for the agent."""

        return {
            "name": "Powered by Ollama",
            # "url": "URL_TO_OLLAMA_OR_YOUR_PROJECT" # Optional
        }

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        _LOGGER.debug(f"PaavoAI processing: '{user_input.text}' for conversation_id: {user_input.conversation_id}")

        # TODO: Add proper prompt
        engineered_prompt = f"{user_input.text}\n"

        raw_response_text = "Sorry, I was unable to process your request."
        try:
            # Get the raw response from the client
            raw_response_text = await self.hass.async_add_executor_job(
                self.client.get_response, engineered_prompt
            )

            if not raw_response_text:
                _LOGGER.warning(f"Ollama client returned empty response for: '{user_input.text}'")
                response_text = "I received an empty response, so I'm not sure how to reply."
            else:
                # Clean the response text to remove <think>...</think> blocks
                # This regex removes the <think> block and any immediately following whitespace/newlines
                cleaned_response_text = re.sub(r"<think>.*?</think>\s*", "", raw_response_text, flags=re.DOTALL).strip()

                if not cleaned_response_text:  # If cleaning resulted in an empty string
                    _LOGGER.warning(f"Response became empty after cleaning <think> tags for: '{user_input.text}'. Original: '{raw_response_text}'")
                    response_text = "I'm sorry, I couldn't formulate a proper reply."
                else:
                    response_text = cleaned_response_text
                _LOGGER.debug(f"Raw Ollama response: '{raw_response_text}'")
                _LOGGER.debug(f"Cleaned response for speech: '{response_text}'")

        except Exception as e:
            _LOGGER.error(f"Error during PaavoAI async_process: {e}", exc_info=e)
            # TODO: Provide language specific error messages that can be spoken
            response_text = f"An error occurred: {e}"

        # Create an IntentResponse object
        intent_response = IntentResponse(language=user_input.language)

        intent_response.async_set_speech(response_text)

        result = ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )

        return result
