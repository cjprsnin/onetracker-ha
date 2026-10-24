"""Polling coordinator + delivered-event detection."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OneTrackerAuthError, OneTrackerClient, OneTrackerError
from .const import DOMAIN, EVENT_DELIVERED, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

type OneTrackerConfigEntry = ConfigEntry[OneTrackerCoordinator]


def eta(parcel: dict[str, Any]) -> str | None:
    """OneTracker uses year 1001 as 'no estimate'."""
    value = parcel.get("tracking_time_estimated")
    if not value or str(value).startswith("1001"):
        return None
    return value


def summarise(parcel: dict[str, Any]) -> dict[str, Any]:
    """Small, attribute-friendly view of one parcel."""
    return {
        "id": parcel.get("id"),
        "description": parcel.get("description")
        or parcel.get("retailer_name")
        or parcel.get("tracking_id"),
        "retailer": parcel.get("retailer_name"),
        "carrier": parcel.get("carrier_name") or parcel.get("carrier"),
        "tracking_id": parcel.get("tracking_id"),
        "status": parcel.get("tracking_status"),
        "status_text": parcel.get("tracking_status_text")
        or parcel.get("tracking_status_description"),
        "location": parcel.get("tracking_location"),
        "eta": eta(parcel),
        "updated": parcel.get("time_updated"),
    }


class OneTrackerCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Fetches parcels and fires an event when one becomes delivered."""

    config_entry: OneTrackerConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: OneTrackerConfigEntry, client: OneTrackerClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self._last_status: dict[Any, str | None] | None = None

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            parcels = await self.client.async_get_parcels()
        except OneTrackerAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OneTrackerError as err:
            raise UpdateFailed(str(err)) from err

        parcels = [p for p in parcels if not p.get("is_archived")]
        self._fire_delivered_events(parcels)
        return parcels

    def _fire_delivered_events(self, parcels: list[dict[str, Any]]) -> None:
        current = {p.get("id"): p.get("tracking_status") for p in parcels}
        # First refresh only sets the baseline, so already-delivered
        # packages never trigger announcements after a restart.
        if self._last_status is not None:
            for parcel in parcels:
                previous = self._last_status.get(parcel.get("id"))
                if (
                    previous is not None
                    and previous != "delivered"
                    and parcel.get("tracking_status") == "delivered"
                ):
                    self.hass.bus.async_fire(EVENT_DELIVERED, summarise(parcel))
        self._last_status = current
