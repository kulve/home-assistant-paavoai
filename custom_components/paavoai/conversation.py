from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow
from .ollama_client import OllamaClient

class ConversationAgent:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.ollama_client = OllamaClient()

    async def handle_user_input(self, user_input: str) -> str:
        response = await self.ollama_client.send_request(user_input)
        return response

    async def start_conversation(self, user_input: str) -> str:
        # Initialize conversation state if needed
        return await self.handle_user_input(user_input)

    async def end_conversation(self) -> None:
        # Handle any cleanup or state reset if necessary
        pass

    # Additional methods for managing conversation state can be added here

