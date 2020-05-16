import httpx

from .envoy_reader_exception import EnvoyReaderError


class EnvoyReader:
    """
    Base class for the EnvoyReader and interface to outside world, this class hides the implementation
    of the different EnvoyReaders for different Envoy firmware versions.

    for older Envoy model C, s/w < R3.9 no json pages
    production data only (ie. Envoy model C, s/w >= R3.9)
    for production and consumption data (ie. Envoy model S, s/w >= R3.9 < R4.10)
    for production and consumption data (ie. Envoy model S, s/w >= R4.10)
    """

    INFO_URL = "info.xml"
    PRODUCTION_JSON_URL = "production.json"
    PRODUCTION_URL = "production"
    PRODUCTION_API_URL = "api/v1/production"
    INVERTERS_API_URL = "api/v1/production/inverters"
    INVENTORY_JSON_URL = "inventory.json"

    def __init__(self, host, port=80, username="envoy", password="", serial_number=""):
        self.host = host.lower()
        self.port = port
        self.username = username
        self.password = password
        self.serial_number = serial_number

    async def call_http_api(self, url_path):
        digest_auth = httpx.DigestAuth(self.username, self.password)
        timeout = httpx.Timeout(20)
        try:
            async with httpx.AsyncClient(timeout=timeout) as session:
                resp = await session.get("http://{}:{}/{}".format(self.host, self.port, url_path), auth=digest_auth)
                if resp.status_code == 200:
                    return resp
                raise EnvoyReaderError("Cannot complete http request, error: {}".format(resp.status_code))

        except httpx.HTTPError as ex:
            raise EnvoyReaderError("Cannot connect: {}".format(ex.__str__()))

    async def get_data(self):
        data = await self.update()
        data['serial_number'] = self.serial_number
        return data;

