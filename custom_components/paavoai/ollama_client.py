class OllamaClient:
    def __init__(self, host, port, model):
        self.base_url = f"http://{host}:{port}"
        self.model = model

    def send_request(self, prompt):
        import requests

        response = requests.post(
            f"{self.base_url}/generate",
            json={"prompt": prompt, "model": self.model}
        )

        if response.status_code == 200:
            return response.json().get("response")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def get_response(self, user_input):
        return self.send_request(user_input)
