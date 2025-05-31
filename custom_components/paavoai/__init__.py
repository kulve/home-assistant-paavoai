""" Initialization for the Paavo AI integration."""
import logging
import os
import tomllib

from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation as ha_conversation
from homeassistant.exceptions import ConfigEntryNotReady

from .conversation import PaavoAIConversationAgent
from .ollama_client import OllamaClient

DOMAIN = "paavoai"
_LOGGER = logging.getLogger(__name__)

async def async_setup(_hass: core.HomeAssistant, _config: dict) -> bool:
    """Set up the Paavo AI integration (legacy)."""
    return True

def _load_paavoai_toml_config_sync():
    """Synchronously loads the paavoai.toml file."""
    current_dir = os.path.dirname(__file__)
    toml_path = os.path.join(current_dir, "paavoai.toml")
    _LOGGER.debug("Attempting to load paavoai.toml from: %s", toml_path)
    try:
        with open(toml_path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        _LOGGER.error("paavoai.toml not found at %s", toml_path)
        raise
    except tomllib.TOMLDecodeError as e:
        _LOGGER.error("Error decoding paavoai.toml from %s: %s", toml_path, str(e))
        raise

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Paavo AI from a config entry."""
    _LOGGER.debug("Setting up Paavo AI entry: %s, data: %s", str(entry.entry_id), str(entry.data))
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    port = entry.data["port"]
    model = entry.data["model"]

    ollama_client = OllamaClient(host, port, model)

    try:
        # Perform a test call to ensure the client can connect.
        # TODO: Use a faster test, e.g. to list the models instead of running them"
        _LOGGER.debug("Testing connection to Ollama for Paavo AI entry %s...", str(entry.entry_id))
        await hass.async_add_executor_job(ollama_client.send_request, "hello")
        _LOGGER.info("Successfully connected to Ollama for Paavo AI entry %s", str(entry.entry_id))

    except Exception as e: # Catch specific exceptions from your client if possible
        _LOGGER.error("Failed to connect to Ollama for Paavo AI entry %s: %s",
                      str(entry.entry_id), str(e))
        # This is CRUCIAL. It tells HA that setup failed and to retry later.
        raise ConfigEntryNotReady(f"Ollama connection error for {host}:{port}: {e}") from e

    # Load the paavoai.toml configuration
    try:
        paavoai_config = await hass.async_add_executor_job(_load_paavoai_toml_config_sync)
        conversation_config = paavoai_config.get("conversation", {}) if paavoai_config else {}
        if not conversation_config.get("topic_get_prompt"):
            error_message = "paavoai.toml is empty or 'topic_get_prompt' under "\
                            "[conversation] is missing or empty."
            _LOGGER.error(error_message)
            raise ConfigEntryNotReady(error_message)
        _LOGGER.info("Successfully loaded paavoai.toml for entry %s", str(entry.entry_id))
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        error_message = f"Error loading paavoai.toml: {e}"
        _LOGGER.error(error_message)
        raise ConfigEntryNotReady(error_message) from e
    except Exception as e: # Catch any other unexpected error during loading
        error_message = f"Unexpected error loading paavoai.toml: {e}"
        _LOGGER.error(error_message)
        raise ConfigEntryNotReady(error_message) from e


    hass.data[DOMAIN][entry.entry_id] = {
        "ollama_client": ollama_client,
        "hass_config": entry.data, # Storing original config data
        "paavoai_config": paavoai_config # Loaded paavoai.toml data
   }

    # Pass the initialized client and the loaded paavoai.toml config to the agent
    try:
        agent = PaavoAIConversationAgent(hass, dict(entry.data), ollama_client, paavoai_config)
    except Exception as e:
        error_message = f"Failed to initialize PaavoAIConversationAgent: {e}"
        _LOGGER.error(error_message)
        raise ConfigEntryNotReady(error_message) from e

    hass.data[DOMAIN][entry.entry_id]["agent"] = agent

    ha_conversation.async_set_agent(hass, entry, agent)
    _LOGGER.info("Paavo AI conversation agent set for entry %s", str(entry.entry_id))

    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Paavo AI entry: %s", str(entry.entry_id))
    ha_conversation.async_unset_agent(hass, entry)

    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]: # If no more entries for this domain, pop the domain itself
            hass.data.pop(DOMAIN)
    _LOGGER.info("Paavo AI entry %s unloaded", str(entry.entry_id))
    return True
