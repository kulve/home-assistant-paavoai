# This file initializes the custom integration package for Home Assistant.

from homeassistant import config_entries, core

DOMAIN = "my_conversation_agent"


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Paavo AI integration."""
    return True

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Paavo AI from a config entry."""
    hass.data[DOMAIN] = entry.data
    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    return True