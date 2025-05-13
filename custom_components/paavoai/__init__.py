from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
# Import the conversation module directly
from homeassistant.components import conversation # MODIFIED
from .conversation import PaavoAIConversationAgent

DOMAIN = "paavoai"

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Paavo AI integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Paavo AI from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Store the config entry data if needed by other parts,
    # but the agent itself will receive the full entry or entry.data as per its constructor
    hass.data[DOMAIN][entry.entry_id] = { # Storing by entry_id is good practice
        "config": entry.data
    }

    # Initialize your agent
    # Your PaavoAIConversationAgent expects `config` which is entry.data, this is fine.
    agent = PaavoAIConversationAgent(hass, entry.data)
    hass.data[DOMAIN][entry.entry_id]["agent"] = agent

    # Register with conversation component using async_set_agent
    # This method associates the agent with the specific config entry
    conversation.async_set_agent(hass, entry, agent) # MODIFIED

    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unregister the agent associated with this config entry
    conversation.async_unset_agent(hass, entry) # ADDED for completeness

    # Clean up hass.data
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]: # If no more entries for this domain, pop the domain itself
            hass.data.pop(DOMAIN)

    return True
