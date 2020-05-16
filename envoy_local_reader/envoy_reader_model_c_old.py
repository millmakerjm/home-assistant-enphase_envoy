from .envoy_reader import EnvoyReader
from .property_names_const import SERIAL_NUMBER, LAST_REPORT_DATE, DEVICE_TYPE, LAST_REPORT_WATTS, MAX_REPORT_WATTS


class EnvoyReaderOldC(EnvoyReader):

    async def update(self):
        print("updating Envoy Type Old C {}".format(self.host))

