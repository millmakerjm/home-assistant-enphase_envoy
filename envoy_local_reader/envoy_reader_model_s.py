from .envoy_reader import EnvoyReader
from .property_names_const import (
    INVERTERS,
    PRODUCTION,
    WATT_HOURS_LIFETIME,
    WATT_HOURS_SEVEN_DAYS,
    WATT_HOURS_TODAY,
    WATTS_NOW,
    ACTIVE_INVERTERS,
    MAX_REPORT_WATTS,
    DEVICE_TYPE,
    LAST_REPORT_DATE,
    SERIAL_NUMBER,
    LAST_REPORT_WATTS, PCU_PRODUCING, PCU_COMMUNICATING, PCU_DEVICE_STATUS)


class EnvoyReaderS(EnvoyReader):

    def __init__(self, host, port, username="envoy", password="", use_production_json=True, serial_number=""):
        super().__init__(host, port, username, password, serial_number)
        self.use_production_json = use_production_json

    async def update(self):
        resp_prod_json = await self.call_http_api(self.PRODUCTION_JSON_URL)
        if not self.use_production_json:
            resp_extra_prod = await self.call_http_api(self.PRODUCTION_API_URL)

        resp_inverter = await self.call_http_api(self.INVERTERS_API_URL)
        resp_inventory = await self.call_http_api(self.INVENTORY_JSON_URL)

        data = dict()
        data[PRODUCTION] = self.__process_production_json(resp_prod_json.json(), resp_extra_prod.json())
        data[INVERTERS] = self.__process_inverter_json(resp_inverter.json(), resp_inventory.json())
        return data

    def __process_production_json(self, raw_prod_json, raw_extra_prod_json):
        data = dict()
        if self.use_production_json:
            raw_json = list(filter(lambda x: x['type'] == 'eim', raw_prod_json['production']))[0]
            data[ACTIVE_INVERTERS] = raw_json['activeCount']
            data[WATTS_NOW] = raw_json['wNow']
            data[WATT_HOURS_TODAY] = raw_json['whToday']
            data[WATT_HOURS_SEVEN_DAYS] = raw_json['whLastSevenDays']
            data[WATT_HOURS_LIFETIME] = raw_json['whLifetime']
        else:
            raw_json = list(filter(lambda x: x['type'] == 'inverters', raw_prod_json['production']))[0]
            data[ACTIVE_INVERTERS] = raw_json['activeCount']
            data[WATTS_NOW] = raw_json['wNow']
            data[WATT_HOURS_TODAY] = raw_extra_prod_json['wattHoursToday']
            data[WATT_HOURS_SEVEN_DAYS] = raw_extra_prod_json['wattHoursSevenDays']
            data[WATT_HOURS_LIFETIME] = raw_extra_prod_json['wattHoursLifetime']
        return data

    @staticmethod
    def __process_inverter_json(raw_inverter_json, raw_inventory_json):
        inverter_data = []
        for raw_json in raw_inverter_json:
            data = dict()
            data[SERIAL_NUMBER] = raw_json['serialNumber']
            data[LAST_REPORT_DATE] = raw_json['lastReportDate']
            data[DEVICE_TYPE] = raw_json['devType']
            data[LAST_REPORT_WATTS] = raw_json['lastReportWatts']
            data[MAX_REPORT_WATTS] = raw_json['maxReportWatts']

            # Lookup the inverter in the inventory
            pcus = list(filter(lambda x: x['type'] == 'PCU', raw_inventory_json))[0]
            inverter_in_inventory = list(filter(lambda x: x['serial_num'] == data[SERIAL_NUMBER], pcus['devices']))[0]

            data[PCU_PRODUCING] = inverter_in_inventory['producing']
            data[PCU_COMMUNICATING] = inverter_in_inventory['communicating']
            data[PCU_DEVICE_STATUS] = inverter_in_inventory['device_status']

            inverter_data.append(data)
        return inverter_data

