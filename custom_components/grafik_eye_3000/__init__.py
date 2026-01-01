"""A representation of a Lutron Grafik Eye Scene
Each Grafik Eye Unit can have 16 scenes and "off"

"""

from .pygrafikeye import GrafikEye

#import asyncio
import logging
import voluptuous as vol

from homeassistant.const import (
    CONF_SWITCHES, 
    CONF_NAME, 
    CONF_HOST, 
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform, load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send, dispatcher_send
from homeassistant.core import callback

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType


_LOGGER = logging.getLogger(__name__)

DOMAIN = "grafik_eye"
GRX_INTERFACE = "grafik_eye"

CONF_SWITCHES = "switches"
CONF_USER = "user_name"
CONF_ADDR = "unit"
CONF_SCENE = "scene"
CONF_NAME = "name"

SCENE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_ADDR): cv.string,
        vol.Required(CONF_SCENE): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.string,
                vol.Required(CONF_USER): cv.string,
                vol.Required(CONF_SWITCHES): vol.All(cv.ensure_list, [SCENE_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass: HomeAssistant, base_config: ConfigType) -> bool:
    """ Start Grafik Eye communication. """
    _LOGGER.info("GRX integration started!")
    
    def handle_grx_callback(status):
        """Dispatch state changes and fire button press events."""
        _LOGGER.debug("callback: %s", status)

        # Check if this is a button press event
        if isinstance(status, dict) and status.get('type') == 'button_press':
            unit = status['unit']
            scene = status['scene']

            # Build event data
            event_data = {
                'unit': unit,
                'scene': scene,
                'device_id': f"grafik_eye_unit_{unit}",
            }

            # Look up switch name from configuration if it exists
            switch_name = switch_lookup.get((str(unit), str(scene)))
            if switch_name:
                event_data['name'] = switch_name

            _LOGGER.info("Button press event: unit=%s, scene=%s, name=%s",
                         unit, scene, switch_name or 'unconfigured')

            hass.bus.fire(
                event_type='grafik_eye_button_press',
                event_data=event_data
            )

        # Otherwise, it's a status update (existing functionality)
        else:
            for key in status:
                if status[key] == "M": #"M" means missing, so no unit at that address
                    continue
                signal = f"grafik_eye_entity_{key}"
                unit_status = status[key]
                _LOGGER.debug("Broadcasting to signal %s value %s", signal, unit_status)
                dispatcher_send(hass, signal, unit_status)
    
    config = base_config.get(DOMAIN)
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    user = config[CONF_USER]
    switches = config[CONF_SWITCHES]

    # Create lookup dictionary: (unit, scene) -> switch name
    switch_lookup = {}
    for switch in switches:
        key = (switch[CONF_ADDR], switch[CONF_SCENE])
        switch_lookup[key] = switch[CONF_NAME]

    _LOGGER.info(f"GRX telnet info: {host} {port} {user}")
    controller = GrafikEye(host, port, user, handle_grx_callback)
    hass.data[GRX_INTERFACE] = controller

    def cleanup():
        controller.close()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)

    if switches:
        hass.create_task(
            async_load_platform(hass, "switch", DOMAIN, {CONF_SWITCHES: switches}, base_config)
        )
        
    return True

class GrafikEyeDevice:
    """Base class of a Grafik Eye Device."""
    
    def __init__(self, controller, unit, scene, name):
        """Initialize Grafik Eye device."""
        self._unit = unit
        self._name = name
        self._scene = scene
        self._controller = controller
        
    @property
    def unique_id(self):
        return f"grafik_eye.{self._unit}{self._scene}"
        
    @property
    def name(self):
        return self._name
        
    @property
    def should_poll(self):
        """The GRX interface will push status if DIP switches 6 and 7
        are set to 'on'.  If not, polling will be required with
        request_system_status method."""
        return False
    