import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant # Required for type hinting hass
import logging

# It's better to test the connection in async_setup_entry
# as config_flow should ideally not perform long I/O operations directly
# without careful handling (e.g. async_add_executor_job for sync client parts)

DOMAIN = "paavoai"
_LOGGER = logging.getLogger(__name__)

class PaavoaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Create a unique ID, e.g., based on host and port
            # This helps HA identify if this exact configuration already exists.
            unique_id = f"{user_input['host']}/{user_input['port']}/{user_input['model']}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Here, ollama_conversation does an API test.
            # For simplicity and to ensure async_setup_entry handles runtime issues,
            # we'll let async_setup_entry do the primary connection test.
            # If you wanted to test here, you'd need to make your OllamaClient async
            # or use hass.async_add_executor_job.

            _LOGGER.debug(f"Creating Paavo AI entry with data: {user_input}")
            return self.async_create_entry(
                title=f"Paavo AI ({user_input['model']})", data=user_input
            )

        data_schema = vol.Schema({
            vol.Required("host", default="localhost"): str,
            vol.Required("port", default=11434): int,
            vol.Required("model", default="qwen3:30b"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
