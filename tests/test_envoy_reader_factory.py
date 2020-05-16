import asyncio
from unittest import TestCase

from envoy_local_reader.envoy_reader_factory import EnvoyReaderFactory
from envoy_local_reader.envoy_reader_model_c_old import EnvoyReaderOldC
from envoy_local_reader.envoy_reader_model_s import EnvoyReaderS
from tests.mock_envoy import TestMockEnvoy, RequestType

import envoy_local_reader.property_names_const as props

DEFAULT_FILE_MAP = {
    RequestType.INFO:           'data/info_model_s.xml',
    RequestType.API_PROD:       'data/api_v1_production.json',
    RequestType.API_INVERTERS:  'data/api_v1_production_inverters.json',
    RequestType.PROD_JSON:      'data/production.json',
    RequestType.INVENTORY_JSON: 'data/inventory.json'
}



class TestEnvoyReaderFactory(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._server = TestMockEnvoy()
        cls._server.set_file_map(DEFAULT_FILE_MAP)

    def testVersionDetection(self):
        fm = DEFAULT_FILE_MAP.copy()
        self._server.set_file_map(fm)

        loop = asyncio.get_event_loop()
        r = loop.run_until_complete(EnvoyReaderFactory("localhost", port=self._server.server_port).get_reader())
        self.assertIsInstance(r, EnvoyReaderS)

        fm[RequestType.INFO] = 'data/info_model_c.xml'
        r = loop.run_until_complete(EnvoyReaderFactory("localhost", port=self._server.server_port).get_reader())
        self.assertIsInstance(r, EnvoyReaderS)

        fm[RequestType.INFO] = 'data/info_model_c_old.xml'
        r = loop.run_until_complete(EnvoyReaderFactory("localhost", port=self._server.server_port).get_reader())
        self.assertIsInstance(r, EnvoyReaderOldC)

    def testEnvoyReaderS(self):
        fm = DEFAULT_FILE_MAP.copy()
        self._server.set_file_map(fm)

        loop = asyncio.get_event_loop()
        r = loop.run_until_complete(EnvoyReaderFactory("localhost", port=self._server.server_port).get_reader())
        data = loop.run_until_complete(r.get_data())

        self.assertTrue(props.PRODUCTION in data)
        self.assertEqual(data[props.SERIAL_NUMBER], '0000000000')
        self.assertTrue(props.PRODUCTION in data)
        self.assertTrue(props.INVERTERS in data)
        self.assertEqual(data[props.PRODUCTION][props.WATT_HOURS_SEVEN_DAYS], 182847)
        self.assertEqual(data[props.PRODUCTION][props.ACTIVE_INVERTERS], 12)
        self.assertEqual(data[props.INVERTERS][0][props.LAST_REPORT_DATE], 1589224854)
