from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation as ha_conversation
from homeassistant.exceptions import ConfigEntryNotReady
import logging

from .conversation import PaavoAIConversationAgent
from .ollama_client import OllamaClient

DOMAIN = "paavoai"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Paavo AI integration (legacy)."""
    # We are using config flow, so this usually just returns True
    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Paavo AI from a config entry."""
    _LOGGER.debug(f"Setting up Paavo AI entry: {entry.entry_id}, data: {entry.data}")
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    port = entry.data["port"]
    model = entry.data["model"]

    client = OllamaClient(host, port, model)

    try:
        # Perform a test call to ensure the client can connect.
        # Your OllamaClient.send_request is synchronous, so wrap it.
        # A better client might have an async "check_connection" or "list_models" method.
        # Using a simple prompt like "hello" for testing.
        _LOGGER.debug(f"Testing connection to Ollama for Paavo AI entry {entry.entry_id}...")
        await hass.async_add_executor_job(client.send_request, "hello")
        _LOGGER.info(f"Successfully connected to Ollama for Paavo AI entry {entry.entry_id}")

    except Exception as e: # Catch specific exceptions from your client if possible
        _LOGGER.error(f"Failed to connect to Ollama for Paavo AI entry {entry.entry_id}: {e}")
        # This is CRUCIAL. It tells HA that setup failed and to retry later.
        raise ConfigEntryNotReady(f"Ollama connection error for {host}:{port}: {e}") from e

    # Store the initialized client and other data if needed
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "config": entry.data # Storing original config data
    }

    # Pass the initialized client to the agent
    agent = PaavoAIConversationAgent(hass, entry.data, client)
    hass.data[DOMAIN][entry.entry_id]["agent"] = agent

    ha_conversation.async_set_agent(hass, entry, agent)
    _LOGGER.info(f"Paavo AI conversation agent set for entry {entry.entry_id}")

    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading Paavo AI entry: {entry.entry_id}")
    ha_conversation.async_unset_agent(hass, entry)

    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]: # If no more entries for this domain, pop the domain itself
            hass.data.pop(DOMAIN)
    _LOGGER.info(f"Paavo AI entry {entry.entry_id} unloaded.")
    return True
