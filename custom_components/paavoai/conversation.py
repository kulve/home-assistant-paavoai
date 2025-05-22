try:
    from homeassistant.components.conversation import (
        AbstractConversationAgent,
        ConversationInput,
        ConversationResult,
    )
    from homeassistant.helpers.intent import IntentResponse
    from homeassistant.core import HomeAssistant
except ImportError:
    from ha_mocks import (
        AbstractConversationAgent,
        ConversationInput,
        ConversationResult,
        IntentResponse,
        HomeAssistant,
    )

import logging
import sys
from datetime import datetime
from collections import deque

logging.basicConfig(
    level=logging.DEBUG,  # or INFO
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout
)

_LOGGER = logging.getLogger(__name__)

_MAX_HISTORY_LENGTH = 10  # Static max history length


class PaavoAIConversationAgentError(Exception):
    """Custom exception for PaavoAI conversation agent errors."""


class PaavoAIConversationAgent(AbstractConversationAgent):
    def __init__(self, hass: HomeAssistant, config_data: dict, client):
        self.hass = hass
        self.config_data = config_data
        self.ollama = client
        # Single history for the discussion
        self._history = deque(maxlen=_MAX_HISTORY_LENGTH)

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

    async def conversation_store(self, role: str, message: str) -> None:
        """Store the conversation in the history."""
        if len(self._history) >= _MAX_HISTORY_LENGTH:
            self._history.popleft()
        self._history.append({"role": role,
                              "content": message,
                              "timestamp": datetime.utcnow().isoformat()})

    async def conversation_get_str(self, length: int) -> str:
        """Get the conversation history as a string."""
        history = ""

        if len(self._history) == 0:
            # This can't happen as we always first add the user input
            return "Error: No conversation history available."

        for entry in list(self._history)[-length:]:
            role = entry["role"]
            content = entry["content"]
            timestamp = entry["timestamp"]
            history += f"[{timestamp}] {role}: {content}\n"
        return history

    async def topic_get(self) -> str:
        """Get the topic of the conversation."""
        conversation_history = await self.conversation_get_str(4)
        # TODO: Get this from the config
        prompt = "You act as a AI agent part of a larger Home AI.\n"
        prompt += "Your task is to select the  topic from the conversation at the end.\n"
        prompt += "The topics are:\n"
        prompt += "- lights: Control lights\n"
        prompt += "- music: Control music\n"
        prompt += "- sensor: Query sensor value (e.g. temperature in a given location)\n"
        prompt += "\n"
        prompt += "Use only the listed topics, do not invent new ones. Select the 'sensor' topic if the others don't match\n"
        prompt += "Answer with two lines: First contains the reasoning for it (starts with 'reasoning:') and the second contains the topic (starts with 'topic:').\n"
        prompt += "\n"
        prompt += "Example answer in the exact correct format:\n"
        prompt += "reasoning: The user asked about the temperature of the living room\n"
        prompt += "topic: sensor\n"
        prompt += "\n"
        prompt += f"\n\n{conversation_history}\n"

        try:
            response = await self.ollama_prompt(prompt)
        except PaavoAIConversationAgentError as e:
            raise e from e

        response = response.strip().lower()
        if ("reasoning:" not in response) or ("topic:" not in response):
            error_message = "Ollama response was not in specified format. Response: %s" % response
            _LOGGER.error(error_message)
            # TODO : Use language specific error messages that can be spoken
            raise PaavoAIConversationAgentError(error_message)

        # Extract the topic from the response
        topic = response.split("topic:")[-1].strip()
        topic = topic.split("\n")[0].strip()
        # Check if the topic is valid
        if topic not in ["lights", "music", "sensor"]:
            error_message = f"Invalid topic '{topic}' returned by Ollama. Response: {response}"
            _LOGGER.error(error_message)
            # TODO : Use language specific error messages that can be spoken
            raise PaavoAIConversationAgentError(error_message)

        # Extract the reasoning
        reasoning = response.split("reasoning:")[-1].strip()
        reasoning = reasoning.split("\n")[0].strip()
        # Log the reasoning
        _LOGGER.debug("Ollama topic '%s' with reasoning: %s", topic, reasoning)

        return topic


    async def ollama_prompt(self, prompt: str) -> str:
        """Send a prompt to the Ollama server and return the response."""
        # Get the response from the Ollama server
        try:
            response = await self.hass.async_add_executor_job(self.ollama.send_request,
                                                              prompt)
        except Exception as e:  # pylint: disable=broad-except
            error_message = f"Error while sending request to Ollama: {e}"
            _LOGGER.error(error_message)
            # TODO: Use language specific error messages that can be spoken
            raise PaavoAIConversationAgentError(error_message)

        return response

    async def create_response(self, user_input: ConversationInput, response: str) -> ConversationResult:
        """Return the response from the Ollama server."""
               # Create an IntentResponse object
        intent_response = IntentResponse(language=user_input.language)

        intent_response.async_set_speech(response)

        result = ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )

        return result

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        _LOGGER.debug("PaavoAI processing: '%s' for conversation_id: %s", user_input.text, user_input.conversation_id)

        # TODO: Need to have the conversation ID
        # Add user input to history
        await self.conversation_store("user", user_input.text)

        try:
            topic = await self.topic_get()
        except PaavoAIConversationAgentError as e:
            return await self.create_response(user_input, str(e))

        # TMP: just turn the topic for now
        return await self.create_response(user_input, topic)

        # TODO: Add proper prompt
        # TODO: configure the history length
        conversation_history = await self.conversation_get_str(4)
        engineered_prompt = f"{conversation_history}\n"

        response = await self.ollama_prompt(engineered_prompt)

        # Add assistant response to history
        await self.conversation_store("assistant", response)

        return await self.return_response(response)
