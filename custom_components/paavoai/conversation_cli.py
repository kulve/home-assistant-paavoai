import sys
import asyncio
import logging
from datetime import datetime
from collections import deque
from ollama_client import OllamaClient
from conversation import PaavoAIConversationAgent, ConversationInput

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout
)

# Minimal mocks
class MockHomeAssistant:
    async def async_add_executor_job(self, func, *args):
        # This correctly simulates running the synchronous function 'func'
        # in the default thread pool executor.
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)

class MockConversationInput:
    def __init__(self, text, language="fi", conversation_id="test"):
        self.text = text
        self.language = language
        self.conversation_id = conversation_id

async def main():
    if len(sys.argv) < 2:
        print("Usage: python conversation_cli.py 'your prompt here'")
        sys.exit(1)

    user_input_text = sys.argv[1]
    hass = MockHomeAssistant()
    config_data = {}
    client = OllamaClient("192.168.3.1", 11434, "qwen3:30b")
    agent = PaavoAIConversationAgent(hass, config_data, client)

    # Use either the real ConversationInput or a fully compatible mock
    user_input = ConversationInput(text=user_input_text)
    # Or if using a mock:
    # user_input = MockConversationInput(user_input_text)

    try:
        result = await agent.async_process(user_input)
        print(f"{result.response.speech['plain']['speech']}")

    except Exception as e:
        print(f"Error during processing: {e}")
        # Optionally, re-raise or log traceback for more details
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
