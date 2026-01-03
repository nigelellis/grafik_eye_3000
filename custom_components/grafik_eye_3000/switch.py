"""A representation of a Lutron Grafik Eye Scene"""
import logging

# from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.switch import SwitchEntity

from . import CONF_ADDR, CONF_SCENE, CONF_NAME, CONF_SWITCHES, GRX_INTERFACE, GrafikEyeDevice  # DOMAIN

_LOGGER = logging.getLogger(__name__)


# async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
def setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Grafik Eye Scenes. """
    if discovery_info is None:
        return

    controller = hass.data[GRX_INTERFACE]

    devs = []
    # for device_id, device_config in discovery_info.items():
    #     name = device_config[CONF_NAME]
    #     unit = device_id[0]
    #     scene = device_id[1]
    #     switches.append(GrafikEyeScene(name, unit, scene, controller))
    for switch in discovery_info[CONF_SWITCHES]:
        dev = GrafikEyeScene(
            controller, switch[CONF_ADDR], switch[CONF_SCENE], switch[CONF_NAME]
        )
        devs.append(dev)
    # Do I need to return True?
    async_add_entities(devs, update_before_add=True)


class GrafikEyeScene(GrafikEyeDevice, SwitchEntity):
    """ Grafik Eye Scene. """

    def __init__(self, controller, unit, scene, name):
        """Create device with Name, Unit, Scene."""
        super().__init__(controller, unit, scene, name)
        self._state = 0

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        signal = f"grafik_eye_entity_unit_{self._unit}"
        _LOGGER.debug("Connecting to signal %s", signal)
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self.update_callback)
        )
        self._controller.request_system_status()

    @property
    def is_on(self):
        """ True if GRX scene is on. """
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
#        self._state = True
        self._controller.setScene(self._scene, self._unit)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off. """
        self._controller.setScene("0", self._unit)

    @callback
    def update_callback(self, status):
        """Process device specific messages."""
        _LOGGER.debug("Returned scene for unit %s is %s and scene id is %s",
                      self._unit, status, self._scene)
        if str(status) == str(self._scene):
            self._state = True
        else:
            self._state = False
        self.async_write_ha_state()
        self.async_schedule_update_ha_state(True)
