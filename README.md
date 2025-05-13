# Custom Home Assistant Conversation Agent

This repository contains a custom Home Assistant integration that acts as a conversation agent, allowing users to interact with their Home Assistant instance using natural language through a voice assistant. The integration connects to a local Ollama instance for private LLM access.

I've leveraged this integration while learning how to create my own:
https://github.com/ej52/hass-ollama-conversation

## Project Structure

```
ha-Paavo
├── custom_components
│   └── my_conversation_agent
│       ├── __init__.py
│       ├── manifest.json
│       ├── conversation.py
│       └── ollama_client.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone this repository to your local machine.
2. Copy the `custom_components` directory into your Home Assistant configuration directory (usually located at `/config`).
3. Install the required Python dependencies listed in `requirements.txt`.

## Configuration

To configure the integration, add the following to your `configuration.yaml` file:

```yaml
conversation_agent:
  # Add any necessary configuration options here
```

## Usage

Once the integration is installed and configured, you can start using the conversation agent through your voice assistant. Simply speak your command, and the agent will process your input and respond accordingly.

## Development

If you wish to contribute to this project or modify the integration, you can do so by editing the files in the `custom_components/my_conversation_agent` directory.

### Key Files

- `__init__.py`: Initializes the custom integration package and registers the integration with Home Assistant.
- `manifest.json`: Contains metadata about the integration, including its name, version, and dependencies.
- `conversation.py`: Implements the conversation agent functionality, handling user input and managing conversation state.
- `ollama_client.py`: Connects to the local Ollama instance, sending requests to the LLM and processing responses.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.