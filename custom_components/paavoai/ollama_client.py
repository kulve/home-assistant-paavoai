import logging
import requests
_LOGGER = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, host, port, model):
        self.base_url = f"http://{host}:{port}"
        self.model = model

    def send_request(self, prompt):

        # TODO: Use Ollama's API to disable thinking mode
        prompt = prompt.strip() + "\n/nothink"

        api_url = f"{self.base_url}/api/generate"
        payload = {"prompt": prompt, "model": self.model, "stream": False}

        _LOGGER.debug(f"Sending request to Ollama: URL={api_url}, Payload={json.dumps(payload)}")

        response = requests.post(api_url, json=payload)

        _LOGGER.debug(f"Ollama response status: {response.status_code}, response: {response}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data.get("response")
            except requests.exceptions.JSONDecodeError:
                # Handle cases where response is 200 but not valid JSON
                # TODO: Use language specific error messages that can be spoken
                error_message = f"Ollama response was not valid JSON. Response: {response.text}"
                _LOGGER.error(error_message)
                return error_message

        else:
            # TODO: Use language specific error messages that can be spoken
            error_message = f"Ollama Error: {response.status_code} - {response.text}"
            _LOGGER.error(error_message)
            return error_message

    def get_response(self, user_input):
        return self.send_request(user_input)
