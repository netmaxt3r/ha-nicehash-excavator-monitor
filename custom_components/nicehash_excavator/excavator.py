"""Nicehash Excavator API"""

from __future__ import annotations

import logging

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from .data_containers import Algorithm, GraphicsCard, RigInfo, Worker

_LOGGER = logging.getLogger(__name__)


class ExcavatorAPI:
    """Excavator API Implementation."""

    def __init__(
        self, host_address: str, host_port: int, enable_debug_logging: bool = False
    ) -> None:
        """Init ExcavatorAPI."""
        self.host_address = self.format_host_address(host_address)
        self._host_port = host_port
        self._enable_debug_logging = enable_debug_logging

    async def request(self, query: str) -> ClientResponse | None:
        """Excavator API Request"""

        url = f"{self.host_address}:{self._host_port}/api?command={query}"

        if self._enable_debug_logging:
            _LOGGER.info("GET %s", url)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        if json_data["error"]:
                            raise Exception(json_data["error"])
                        return json_data
                    if response.content:
                        raise Exception(
                            str(response.status)
                            + ": "
                            + response.reason
                            + ": "
                            + str(await response.text())
                        )
                    raise Exception(str(response.status) + ": " + response.reason)
            except Exception as e:
                if self._enable_debug_logging:
                    _LOGGER.warning(
                        "Error while getting data from %s error: %s", url, e
                    )
                return None

    async def test_connection(self) -> bool:
        """Test connectivity"""
        query = '{"id":1,"method":"info","params":[]}'
        response = await self.request(query)
        if response is not None:
            return True
        return False

    async def get_rig_info(self) -> RigInfo:
        """Get Rig Information"""
        query = '{"id":1,"method":"info","params":[]}'
        response = await self.request(query)
        if response is not None:
            return RigInfo(response)
        return None

    async def get_devices(self) -> dict[int, GraphicsCard]:
        """Get the devices"""
        query = '{"id":1,"method":"devices.get","params":[]}'
        response = await self.request(query)
        if response is not None:
            devices = {}
            for device_data in response.get("devices"):
                card = GraphicsCard(device_data)
                devices[card.id] = card
            return devices
        return {}

    async def get_algorithms(self) -> dict[int, Algorithm]:
        """Get the Algorithms"""
        query = '{"id":1,"method":"algorithm.list","params":[]}'
        response = await self.request(query)
        if response is not None:
            algorithms = {}
            for algorithm_data in response.get("algorithms"):
                algorithm = Algorithm(algorithm_data)
                algorithms[algorithm.id] = algorithm
            return algorithms
        return {}

    async def get_workers(self) -> dict[int, Worker]:
        """Get the workers"""
        query = '{"id":1,"method":"worker.list","params":[]}'
        response = await self.request(query)
        if response is not None:
            workers = {}
            for worker_data in response.get("workers"):
                worker = Worker(worker_data)
                workers[worker.id] = worker
            return workers
        return {}

    async def worker_add_algorithm(self, worker_id: int, algorithm: str) -> bool:
        """Add algorithm to a worker"""
        query = (
            '{"id":1,"method":"worker.add","params":["'
            + algorithm
            + '","'
            + str(worker_id)
            + '"]}'
        )
        response = await self.request(query)
        if response is not None:
            return True
        return False

    async def worker_free(self, worker_id: int) -> bool:
        """free up worker"""
        query = '{"id":1,"method":"worker.free","params":["' + str(worker_id) + '"]}'
        response = await self.request(query)
        if response is not None:
            return True
        return False

    @staticmethod
    def format_host_address(host_address: str) -> str:
        """Add http if missing"""
        if not host_address.startswith("http://") and not host_address.startswith(
            "https://"
        ):
            host_address = "http://" + host_address
        return host_address
