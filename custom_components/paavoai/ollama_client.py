import logging
_LOGGER = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, host, port, model):
        self.base_url = f"http://{host}:{port}"
        self.model = model

    def send_request(self, prompt):
        import requests
        import json # Import json for logging the payload if needed

        # Standard Ollama API endpoint is /api/generate
        api_url = f"{self.base_url}/api/generate"
        payload = {"prompt": prompt, "model": self.model, "stream": False} # Added stream: False

        # It's good practice to log what you're sending, especially during debugging
        _LOGGER.debug(f"Sending request to Ollama: URL={api_url}, Payload={json.dumps(payload)}")

        response = requests.post(api_url, json=payload)

        _LOGGER.debug(f"Ollama response status: {response.status_code}, Text: {response.text[:500]}") # Log response

        if response.status_code == 200:
            try:
                # For non-streaming, the response is a JSON object
                response_data = response.json()
                return response_data.get("response")
            except requests.exceptions.JSONDecodeError:
                # Handle cases where response is 200 but not valid JSON
                raise Exception(f"Error: Ollama returned 200 but response was not valid JSON. Response: {response.text}")
        else:
            _LOGGER.error(f"Ollama error: {response.status_code} - {response.text}")
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def get_response(self, user_input):
        return self.send_request(user_input)
