import asyncio
import httpx

import xml.etree.ElementTree as ET

from .envoy_reader_exception import EnvoyReaderError
from .envoy_reader_model_c_old import EnvoyReaderOldC
from .envoy_reader_model_s import EnvoyReaderS


class EnvoyReaderFactory:
    """
    The factory returns based on the firmware version the correct EnvoyReader implementation
    """

    def __init__(self, host, port=80, username="envoy", password="", firmware_version=""):
        self.host = host.lower()
        self.username = username
        self.password = password
        self.endpoint_type = ""
        self.serial_number = None
        self.firmware_version = None
        self.port = port

    async def get_reader(self, fw_version=""):
        """
        older Envoy model C, s/w < R3.9 no json pages
        production data only (ie. Envoy model C, s/w >= R3.9)
        for production and consumption data (ie. Envoy model S, s/w >= R3.9 < R4.10)
        for consumption data and production from separate api call (ie. Envoy model S, s/w >= R4.10)
        """
        if self.firmware_version is None or len(self.firmware_version) == 0:
            await self.__get_info()

        # If no password is set use the serial number as password
        if len(self.password) == 0 and not self.serial_number is None:
            self.password = self.serial_number[6:]

        _v = self.to_version_tuple(self.firmware_version)

        if _v[0] < 3:
            return EnvoyReaderOldC(self.host, self.port, self.username, self.password)
        elif _v[0] == 3 and _v[1] < 9:
            return EnvoyReaderOldC(self.host, self.port, self.username, self.password)
        elif _v[0] == 3 and _v[1] >= 9:
            return EnvoyReaderS(host=self.host, port=self.port, username=self.username, password=self.password,
                                use_production_json=True, serial_number=self.serial_number)
        elif _v[0] == 4 and _v[1] < 10:
            return EnvoyReaderS(host=self.host, port=self.port, username=self.username, password=self.password,
                                use_production_json=True, serial_number=self.serial_number)
        else:
            return EnvoyReaderS(host=self.host, port=self.port, username=self.username, password=self.password,
                                use_production_json=False, serial_number=self.serial_number)

    @staticmethod
    def to_version_tuple(v):
        """
        Parse the firmware version string and convert it into a tuple
        :param v:
        :return: version tuple (int, int, int)
        """
        if v is None:
            return 0, 0, 0
        try:
            _v = v
            if not v[0].isdigit():
                _v = v[1:]
            return tuple(map(int, (_v.split("."))))
        except ValueError:
            return 0, 0, 0

    async def __get_info(self):
        timeout = httpx.Timeout(20)
        try:
            async with httpx.AsyncClient(timeout=timeout) as session:
                resp = await session.get("http://{}:{}/info.xml".format(self.host, self.port), allow_redirects=False)
                if resp.status_code == 200:
                    xml = ET.fromstring(resp.text)
                    self.serial_number = xml.find("device/sn").text
                    self.firmware_version = xml.find("device/software").text
                else:
                    raise EnvoyReaderError("Cannot complete http request, error: {}".format(resp.status_code))
        except httpx.HTTPError as ex:
            raise EnvoyReaderError("Cannot connect: {}".format(ex.__str__()))
