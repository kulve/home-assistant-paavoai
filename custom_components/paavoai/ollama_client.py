"""Ollama Client for Home Assistant integration."""

import logging
import json
import re
import requests

_LOGGER = logging.getLogger(__name__)

class OllamaClientError(Exception):
    """Custom exception for Ollama client errors."""

class OllamaClient:
    """Client for interacting with the Ollama API."""
    def __init__(self, host, port, model):
        self.base_url = f"http://{host}:{port}"
        self.model = model

    def send_request(self, prompt: str) -> str:
        """Send a request to the Ollama API and return the response."""

        # TODO: Use Ollama's API to disable thinking mode
        prompt = prompt.strip() + "\n/nothink"

        api_url = f"{self.base_url}/api/generate"
        payload = {"prompt": prompt, "model": self.model, "stream": False}

        _LOGGER.debug("Sending request to Ollama: URL=%s, Payload=%s", api_url, json.dumps(payload))

        response = requests.post(api_url, json=payload, timeout=30)

        _LOGGER.debug("Ollama response status: %s, response: %s",
                      response.status_code,
                      response.json().get("response"))

        if response.status_code == 200:
            try:
                response_data = response.json().get("response")
                response_text = re.sub(r"<think>.*?</think>\s*",
                                       "",
                                       response_data,
                                       flags=re.DOTALL).strip()

                return response_text
            except requests.exceptions.JSONDecodeError as exc:
                # Handle cases where response is 200 but not valid JSON
                # TODO: Use language specific error messages that can be spoken
                error_message = f"Ollama response was not valid JSON. Response: {response.text}"
                _LOGGER.error(error_message)
                raise OllamaClientError(error_message)from exc
        else:
            # TODO: Use language specific error messages that can be spoken
            error_message = f"Ollama Error: {response.status_code} - {response.text}"
            _LOGGER.error(error_message)
            raise OllamaClientError(error_message)
