""" Conversation agent for PaavoAI using Ollama."""


import logging
import sys
from datetime import datetime
from collections import deque

from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.helpers.intent import IntentResponse
from homeassistant.core import HomeAssistant

from .music_player import MusicPlayer

logging.basicConfig(
    level=logging.DEBUG,  # or INFO
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout
)

_DOMAIN = "paavoai"
_LOGGER = logging.getLogger(__name__)
_MAX_HISTORY_LENGTH = 10  # Static max history length


class PaavoAIError(Exception):
    """Custom exception for PaavoAI conversation agent errors."""
    def __init__(self, message: str, ollama_broken: bool = False):
        super().__init__(message)
        self.ollama_broken= ollama_broken


class PaavoAIConversationAgent(AbstractConversationAgent):
    """ PaavoAI conversation agent using Ollama for processing user input."""

    def __init__(self, hass: HomeAssistant, hass_data: dict, ollama_client, paavoai_config: dict):
        """ Initialize the PaavoAI conversation agent."""
        self._hass = hass
        self._hass_data = hass_data
        self._ollama = ollama_client
        self._cfg = paavoai_config

        # Single history for the discussion
        self._history = deque(maxlen=_MAX_HISTORY_LENGTH)
        # TODO: Don't hardcode the media player entity ID
        media_player_entity_id = self._hass_data.get("media_player_entity_id",
                                                      "media_player.shieldi")
        default_playlist = self._hass_data.get("default_playlist_id", "")
        self.music_player = MusicPlayer(self._hass, media_player_entity_id, default_playlist)


    def raise_error(self, message: str, broken: bool=False, cause_exception=None):
        """Helper method to log error and raise PaavoAIError."""
        if cause_exception:
            message = f"{message} Error: {str(cause_exception)}"
            _LOGGER.error(message)
            raise PaavoAIError(message, ollama_broken=broken) from cause_exception
        else:
            _LOGGER.error(message)
            raise PaavoAIError(message, ollama_broken=broken)

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

    async def music_get_actions(self) -> str:
        """Get the music actions."""

        prompt = self._cfg['conversation']['music_get_action_prompt']
        conversation_history = await self.conversation_get_str(4)
        prompt = prompt.replace("{conversation_history}",conversation_history)

        try:
            response = await self.ollama_prompt(prompt)
        except PaavoAIError as e:
            self.raise_error("Error while getting music actions from Ollama",
                             broken=True,
                             cause_exception=e)

        response = response.strip().lower()
        if ("reasoning:" not in response) or ("action:" not in response):
            self.raise_error("Ollama response was not in specified format. " \
                             f"Response: {response}")

        # Extract the topic from the response
        action = response.split("action:")[-1].strip()
        action = action.split("\n")[0].strip()
        # Check if the topic is valid
        if action not in ["play", "stop", "pause", "resume", "next", "prev", "info"]:
            # These takes extra parameters, so need to check separately
            if not action.startswith("load ") and not action.startswith("message "):
                self.raise_error(f"Invalid action '{action}' "
                                 f"returned by Ollama. Response: {response}")

        # Extract the reasoning
        reasoning = response.split("reasoning:")[-1].strip()
        reasoning = reasoning.split("\n")[0].strip()
        # Log the reasoning
        _LOGGER.debug("Ollama action '%s' with reasoning: %s", action, reasoning)

        return action

    async def topic_get(self) -> str:
        """Get the topic of the conversation."""
        prompt = self._cfg['conversation']['topic_get_prompt']
        conversation_history = await self.conversation_get_str(4)
        prompt = prompt.replace("{conversation_history}", conversation_history)

        try:
            response = await self.ollama_prompt(prompt)
        except PaavoAIError as e:
            self.raise_error("Error while getting topic from Ollama",
                             broken=True,
                             cause_exception=e)

        response = response.strip().lower()
        if ("reasoning:" not in response) or ("topic:" not in response):
            self.raise_error(f"Ollama response was not in specified format. Response: {response}")

        # Extract the topic from the response
        topic = response.split("topic:")[-1].strip()
        topic = topic.split("\n")[0].strip()
        if topic not in ["lights", "music", "sensor"]:
            self.raise_error(f"Invalid topic '{topic}' returned by Ollama. Response: {response}")

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
            response = await self._hass.async_add_executor_job(self._ollama.send_request,
                                                              prompt)
        except Exception as e:  # pylint: disable=broad-except
            self.raise_error("Error while sending request to Ollama",
                broken=True,
                cause_exception=e
            )

        return response

    async def generate_user_error(self,
                                  user_input: ConversationInput,
                                  message: str,
                                  ollama_broken: bool = False) -> ConversationResult:
        """Generate a user error response."""
        _LOGGER.error(message)
        if ollama_broken:
            message = "AI server is broken, please try again later."
            _LOGGER.error("Ollama broken, overriding the message: %s", message)
            return await self.create_response(user_input, message)

        prompt = self._cfg['conversation']['user_error_prompt']
        conversation_history = await self.conversation_get_str(4)
        prompt = prompt.replace("{conversation_history}", conversation_history)
        prompt = prompt.replace("{message}", message)

        try:
            response = await self.ollama_prompt(prompt)
            _LOGGER.error("User error response from Ollama: %s", response)
        except PaavoAIError as e:
            # We are already in an error state, so just return a generic error message
            _LOGGER.error("Error while generating user error response: %s", e)
            response = "AI server is broken, please try again later."

        return await self.create_response(user_input, response)

    async def generate_user_reply(self, message: str) -> str:

        """Generate a user reply based on the action result string."""
        _LOGGER.debug(message)

        prompt = self._cfg['conversation']['user_reply_prompt']
        conversation_history = await self.conversation_get_str(8)
        prompt = prompt.replace("{conversation_history}", conversation_history)
        prompt = prompt.replace("{message}", message)

        try:
            response = await self.ollama_prompt(prompt)
            _LOGGER.debug("The rephased message from Ollama: %s", response)
        except PaavoAIError as e:
            # We are responding to the user, so too late to do any fallbacks
            _LOGGER.error("Error while generating rephrased response: %s", e)
            response = "The request might have been completed but AI server is now broken"

        return response.strip()


    async def create_response(self,
                              user_input: ConversationInput,
                              response: str) -> ConversationResult:
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
        """ The main method to process the user input and return a response."""

        _LOGGER.debug("PaavoAI processing: '%s' for conversation_id: %s",
                      user_input.text, user_input.conversation_id)

        # TODO: Need to have the conversation ID
        # Add user input to history
        await self.conversation_store("user", user_input.text)

        try:
            topic = await self.topic_get()
        except PaavoAIError as e:
            return await self.generate_user_error(user_input,
                                                  "Error while getting topic for the user comment",
                                                  e.ollama_broken)

        action = "NONE"
        if topic == "sensor":
            # Use HA's APIs to get the sensor value
            pass
        elif topic == "lights":
            # Use HA's APIs to control the lights
            pass
        elif topic == "music":
            try:
                action_string = await self.music_get_actions()
                if action_string.startswith("message "):
                    # If the action is a message, just return it
                    response_message = action_string.split("message ")[-1].strip()
                    await self.conversation_store("assistant", response_message)
                    return await self.create_response(user_input, response_message)

                result = await self.music_player.parse_action(action_string)
            except Exception: # pylint: disable=broad-except
                return await self.generate_user_error(user_input,
                                                     "Error while processing music action")

            response_message = await self.generate_user_reply(result)
            await self.conversation_store("assistant", response_message)
            return await self.create_response(user_input, response_message)

        # TMP: just turn the action for now
        return await self.create_response(user_input, f"{topic} {action}")

        # TODO: Add proper prompt
        # TODO: configure the history length
        #conversation_history = await self.conversation_get_str(4)
        #engineered_prompt = f"{conversation_history}\n"

        #response = await self.ollama_prompt(engineered_prompt)

        # Add assistant response to history
        #await self.conversation_store("assistant", response)

        #return await self.return_response(response)
