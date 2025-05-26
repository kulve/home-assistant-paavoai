import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

class MusicPlayerError(Exception):
    """Custom exception for MusicPlayer errors."""
    pass

class MusicPlayer:
    """
    A class to control a Home Assistant media_player entity,
    specifically tailored for Music Assistant commands.
    """
    def __init__(self, hass: HomeAssistant, entity_id: str, default_playlist_id: str = None):
        """
        Initialize the MusicPlayer.

        :param hass: The Home Assistant instance.
        :param entity_id: The entity_id of the Music Assistant media_player.
        :param default_playlist_id: The media_content_id for the default playlist (for 'play' action).
        """
        self.hass = hass
        self.entity_id = entity_id
        self.default_playlist_id = default_playlist_id

    async def parse_action(self, action: str) -> str:
        """
        Parse the action string and call the appropriate method.
        :param action: The action string (e.g., "play", "load [playlist_name]", etc.)
        :return: A message indicating the result of the action.
        """

        action = action.strip().lower()
        _LOGGER.debug("Parsing action: %s", action)
        if action == "play":
            return await self.play_default()
        elif action.startswith("load "):
            playlist_name = action[len("load "):].strip()
            return await self.load_playlist(playlist_name)
        elif action == "stop":
            return await self.stop()
        elif action == "pause":
            return await self.pause()
        elif action == "resume":
            return await self.resume()
        elif action == "next":
            return await self.next_track()
        elif action == "prev":
            return await self.previous_track()
        else:
            raise MusicPlayerError(f"Unknown action: {action}")

    async def _call_service(self, service_name: str, data: dict = None) -> None:
        """
        Helper method to call media_player services.
        Raises MusicPlayerError on failure.
        """
        if data is None:
            data = {}

        _LOGGER.debug(
            "Calling media_player.%s for %s with data: %s",
            service_name, self.entity_id, data
        )
        try:
            await self.hass.services.async_call(
                domain="media_player",
                service=service_name,
                service_data=data,
                blocking=True,  # Wait for the service call to complete
                target={"entity_id": self.entity_id}
            )
            _LOGGER.info(
                "Successfully called media_player.%s for %s",
                service_name, self.entity_id
            )
        except HomeAssistantError as e:
            _LOGGER.error(
                "Error calling media_player.%s for %s: %s",
                service_name, self.entity_id, e
            )
            raise MusicPlayerError(f"Failed to execute {service_name} on {self.entity_id}: {e}") from e
        except Exception as e:
            _LOGGER.error(
                "Unexpected error calling media_player.%s for %s: %s",
                service_name, self.entity_id, e
            )
            raise MusicPlayerError(f"Unexpected error during {service_name} on {self.entity_id}: {e}") from e

    async def play_default(self) -> str:
        """
        Handles the 'play' action: Powers on the player and loads the default playlist.
        If no default playlist is configured, attempts a generic 'media_play'.
        """
        _LOGGER.info("Executing 'play default' action for %s.", self.entity_id)
        #await self._call_service("turn_on") # Ensure player is on

        #if not self.default_playlist_id:
        #    _LOGGER.warning(
        #        "No default_playlist_id configured for %s. Attempting generic media_play.",
        #        self.entity_id
        #    )
        #    await self._call_service("media_play")
        #    return f"Playback started/resumed on {self.entity_id}."

        #service_data = {
        #    "media_content_id": self.default_playlist_id,
        #    "media_content_type": "playlist", # Assuming default is a playlist
        #}
        await self._call_service("play_media", service_data)
        return f"Playing default playlist on {self.entity_id}."

    async def load_playlist(self, playlist_name: str) -> str:
        """
        Handles the 'load [playlist_name]' action: Loads and plays a specific playlist.
        """
        _LOGGER.info("Executing 'load playlist: %s' for %s.", playlist_name, self.entity_id)
        await self._call_service("turn_on") # Ensure player is on

        service_data = {
            "media_content_id": playlist_name,
            "media_content_type": "playlist",
            "enqueue": "replace" # Typically, loading a new playlist replaces the current queue
        }
        await self._call_service("play_media", service_data)
        return f"Playing playlist '{playlist_name}' on {self.entity_id}."

    async def stop(self) -> str:
        """Handles the 'stop' action: Stops playback."""
        _LOGGER.info("Executing 'stop' action for %s.", self.entity_id)
        await self._call_service("media_stop")
        # If "powers down the needed devices" implies turning off the player:
        # await self._call_service("turn_off")
        return f"Playback stopped on {self.entity_id}."

    async def pause(self) -> str:
        """Handles the 'pause' action: Pauses playback."""
        _LOGGER.info("Executing 'pause' action for %s.", self.entity_id)
        await self._call_service("media_pause")
        return f"Playback paused on {self.entity_id}."

    async def resume(self) -> str:
        """Handles the 'resume' action: Resumes playback (uses media_play)."""
        _LOGGER.info("Executing 'resume' action for %s.", self.entity_id)
        await self._call_service("media_play")
        return f"Playback resumed on {self.entity_id}."

    async def next_track(self) -> str:
        """Handles the 'next' action: Skips to the next track."""
        _LOGGER.info("Executing 'next track' action for %s.", self.entity_id)
        await self._call_service("media_next_track")
        return f"Skipped to next track on {self.entity_id}."

    async def previous_track(self) -> str:
        """Handles the 'prev' action: Skips to the previous track."""
        _LOGGER.info("Executing 'previous track' action for %s.", self.entity_id)
        await self._call_service("media_previous_track")
        return f"Skipped to previous track on {self.entity_id}."
