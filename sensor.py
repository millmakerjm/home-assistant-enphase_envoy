"""Support for Enphase Envoy solar energy monitor."""
import logging
import json
import async_timeout

from datetime import timedelta, datetime, timezone
#from envoy_reader.envoy_reader import EnvoyReader
from .envoy_local_reader.envoy_reader_factory import EnvoyReaderFactory
from .envoy_local_reader import property_names_const as envoy_prop_names

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    ENERGY_WATT_HOUR,
    POWER_WATT,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:flash"
ICON_SOLAR = "mdi:solar-power"

SENSORS = {
    "production": (
        "Envoy Current Energy Production",
        POWER_WATT,
        'watts_now',
        ICON_SOLAR),

    "daily_production": (
        "Envoy Today's Energy Production",
        ENERGY_WATT_HOUR,
        'watt_hours_today',
        ICON_SOLAR),

    "seven_days_production": (
        "Envoy Last Seven Days Energy Production",
        ENERGY_WATT_HOUR,
        'watt_hours_seven_days',
        ICON_SOLAR
    ),

    "lifetime_production": (
        "Envoy Lifetime Energy Production",
        ENERGY_WATT_HOUR,
        'watt_hours_lifetime',
        ICON_SOLAR),

    "inverters": (
        "Envoy Inverter",
        POWER_WATT,
        'last_report_watts',
        ICON_SOLAR),
}

CONST_DEFAULT_HOST = "envoy"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_IP_ADDRESS, default=CONST_DEFAULT_HOST): cv.string,
        vol.Optional(CONF_USERNAME, default="envoy"): cv.string,
        vol.Optional(CONF_PASSWORD, default=""): cv.string,
        vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSORS)): vol.All(
            cv.ensure_list, [vol.In(list(SENSORS))]
        ),
        vol.Optional(CONF_NAME, default=""): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Enphase Envoy sensor."""
    ip_address = config[CONF_IP_ADDRESS]
    monitored_conditions = config[CONF_MONITORED_CONDITIONS]
    name = config[CONF_NAME]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    _LOGGER.info("Envoy async_setup_platform called")

    f = EnvoyReaderFactory(host=ip_address, username=username, password=password)
    # The factory will return a reader based on the SW/FW version found in info.xml
    envoy_reader = await f.get_reader()

    entities = []

    async def async_update_data():
        try:
            async with async_timeout.timeout(10):
                return await envoy_reader.get_data()
        except requests.exceptions.HTTPError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="EnphaseEnvoy",
        update_method=async_update_data,
        update_interval= timedelta(seconds=30),
    )

    # Do an initial data collection so the list with inverters is filled
    await coordinator.async_refresh()

    # Iterate through the list of sensors configured
    for condition in monitored_conditions:
        if condition == "inverters":
            # The initial data collection made sure we know all inverters that are available at this point
            for inverter in coordinator.data['inverters']:
                entities.append(
                    EnvoyInverter(
                        coordinator,
                        inverter['serial_number'],
                        envoy_reader,
                        condition,
                        f"{name}{SENSORS[condition][0]} {inverter['serial_number']}",
                        SENSORS[condition][1],
                        SENSORS[condition][2],
                        SENSORS[condition][3]
                    )
                )
        else:
            entities.append(
                Envoy(
                    coordinator,
                    coordinator.data['serial_number'],
                    envoy_reader,
                    condition,
                    f"{name}{SENSORS[condition][0]}",
                    SENSORS[condition][1],
                    SENSORS[condition][2],
                    SENSORS[condition][3]
                )
            )
    async_add_entities(entities)


class Envoy(Entity):
    """Implementation of the Enphase Envoy sensors."""

    def __init__(self, coordinator, serial_number, envoy_reader, sensor_type, name, unit, data_key, icon):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._envoy_reader = envoy_reader
        self._type = sensor_type
        self._name = name
        self._unit_of_measurement = unit
        self._state = None
        self._last_reported = None
        self._data_key = data_key
        self._icon = icon
        self._serial_number = serial_number

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        state = self._coordinator.data['production'][self._data_key]
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        return None

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self):
        await self.coordinator.async_request_refresh()


class EnvoyInverter(Envoy):
    """Implementation of the Enphase Envoy Inverter sensors."""
    @property
    def state(self):
        # Inverters report the last known value. If the total production is 0 correct the value for the
        # inverters also to 0
        if self._coordinator.data['production']['watts_now'] == 0:
            state = 0
        else:
            state = self.__get_inverter()[self._data_key]
        return state

    @property
    def device_state_attributes(self):
        inverter = self.__get_inverter()
        ts = datetime.fromtimestamp(inverter['last_report_date'], timezone.utc)
        return {
            "last_reported": ts.isoformat(),
            "communicating": inverter[envoy_prop_names.PCU_COMMUNICATING],
            "producing": inverter[envoy_prop_names.PCU_PRODUCING],
            "device_state": ','.join(inverter[envoy_prop_names.PCU_DEVICE_STATUS])
        }

    def __get_inverter(self):
        return list(filter(lambda x: x['serial_number'] == self._serial_number, self._coordinator.data['inverters']))[0]

