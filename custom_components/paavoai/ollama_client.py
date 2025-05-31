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

    def raise_error(self, message: str, cause_exception=None):
        """Helper method to log error and raise OllamaClientError."""

        if cause_exception:
            message = f"{message} Error: {str(cause_exception)}"
            _LOGGER.error(message)
            raise OllamaClientError(message) from cause_exception
        else:
            _LOGGER.error(message)
            raise OllamaClientError(message)

    def send_request(self, prompt: str) -> str:
        """Send a request to the Ollama API and return the response."""

        # TODO: Use Ollama's API to disable thinking mode
        prompt = prompt.strip() + "\n/nothink"

        api_url = f"{self.base_url}/api/generate"
        payload = {"prompt": prompt, "model": self.model, "stream": False}

        _LOGGER.debug("Sending request to Ollama: URL=%s, Payload=%s", api_url, json.dumps(payload))

        try:
            response = requests.post(api_url, json=payload, timeout=30)
        except Exception as e: # pylint: disable=broad-except
            self.raise_error(f"Failed to connect to Ollama at {self.base_url}.", e)

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
            except Exception as exc: # pylint: disable=broad-except
                self.raise_error("An error occurred while processing the json response.\n"
                                 f"Response: {response.text}.\n", exc)
        else:
            self.raise_error(
                f"Failed to get a valid response from Ollama.\n"
                f"Status code: {response.status_code}.\n"
                f"Response: {response.text}"
            )
