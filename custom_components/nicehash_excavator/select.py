from __future__ import annotations

import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONFIG_NAME
from .mining_rig import MiningRig
from .sensor import DeviceSensorBase
from .data_containers import Algorithm
# from .common import *
# from .services import *
# from .entity import create_entity, SolarmanWritableEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    mining_rig: MiningRig = hass.data[DOMAIN][config.entry_id]
    new_devices = []
    for device_id in mining_rig.devices:
        new_devices.append(AlgorithSelector(mining_rig, config, device_id))

    async_add_entities(new_devices)

    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    return True


class AlgorithSelector(SelectEntity, DeviceSensorBase):
    """Algorithm selector"""

    def __init__(
        self,
        mining_rig: MiningRig,
        config_entry: ConfigEntry,
        device_id: int,
    ):
        super(AlgorithSelector, self).__init__(mining_rig, config_entry, device_id)
        self._rig_name = config_entry.data.get(CONFIG_NAME)
        self.algorithms: dict[int, Algorithm] = mining_rig.algorithms

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Algorithm"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_algorithm"

    @property
    def options(self) -> [str]:
        options = ["None"]
        if self.algorithms:
            for a in self.algorithms.values():
                options.append(a.name)
        return options

    @property
    def current_option(self) -> str:
        for w in self._mining_rig.workers.values():
            if w.device_uuid == self._device_uuid:
                for a in w.algorithms.values():
                    return a.name
        return "None"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        match option:
            case "None":
                worker_id = -1
                for w in self._mining_rig.workers.values():
                    if w.device_uuid == self._device_uuid:
                        worker_id = w.id
                        break
                if worker_id != -1:
                    await self._mining_rig.worker_free(worker_id)
                    await self._mining_rig.update()

            case _:
                await self._mining_rig.device_add_algorithm(self._device_uuid, option)
                await self._mining_rig.update()
                found = False
                for alg in self._mining_rig.algorithms.values():
                    if alg.name == option:
                        found = True
                        break
                if not found:
                    await self._mining_rig.add_algorith(option)
