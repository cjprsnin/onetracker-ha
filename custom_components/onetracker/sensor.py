"""Sensors: active and delivered package counts."""
from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OneTrackerConfigEntry, OneTrackerCoordinator, summarise


async def async_setup_entry(
    hass: HomeAssistant, entry: OneTrackerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            OneTrackerSensor(coordinator, entry, "active", "Active packages", delivered=False),
            OneTrackerSensor(coordinator, entry, "delivered", "Delivered packages", delivered=True),
        ]
    )


class OneTrackerSensor(CoordinatorEntity[OneTrackerCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "packages"
    _attr_icon = "mdi:package-variant-closed"

    def __init__(
        self,
        coordinator: OneTrackerCoordinator,
        entry: OneTrackerConfigEntry,
        key: str,
        name: str,
        delivered: bool,
    ) -> None:
        super().__init__(coordinator)
        self._delivered = delivered
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="OneTracker",
            manufacturer="OneTracker",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _matching(self) -> list[dict[str, Any]]:
        return [
            p
            for p in self.coordinator.data or []
            if (p.get("tracking_status") == "delivered") == self._delivered
        ]

    @property
    def native_value(self) -> int:
        return len(self._matching())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        parcels = self._matching()
        return {
            "by_status": dict(Counter(p.get("tracking_status") or "unknown" for p in parcels)),
            "packages": [summarise(p) for p in parcels],
        }
