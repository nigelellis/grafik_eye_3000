#! /usr/local/bin/python3
# -*- coding: utf-8 -*-
# Communicates with Lutron GRX interface
# Currently returns the state of the system as a
# dictionary with "unit_X" as key and 0-16 and/or M as values
"""
Grafik Eye integration via GRX-CI-NWK

"""

from threading import Thread
import time
import socket
import select
import logging
import telnetlib
import re

_LOGGER = logging.getLogger(__name__)

POLLING_FREQ = 1.

SCENES = {'0': 0, '1': 1,  '2': 2,  '3': 3,  '4': 4,
          '5': 5,  '6': 6,  '7': 7,  '8': 8,
                   '9': 9,  'A': 10, 'B': 11, 'C': 12,
                   'D': 13, 'E': 14, 'F': 15, 'G': 16, 'M': 'M'}

SCENES_REV = dict([(SCENES[x], x) for x in SCENES])


# create a list of units to later zip into a dictionary with status values
x_list = list(range(1, 9))
unit_list = []
for item in x_list:
    unit_list.append("unit_"+str(item))


class GrafikEye(Thread):
    # class GrafikEye:
    """Interface with Lutron GRX-CI-NWK"""

    def __init__(self, host, port, user, callback):
        """Connect to controller using host, port, and username."""
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._user = user
        self._callback = callback
        self._tc = None

        self._running = False
        self._connect()
        if self._tc == None:
            raise ConnectionError(f"Couldn't connect to {host} {port}")
        self.start()

    def _connect(self):
        try:
            self._tc = telnetlib.Telnet(self._host, self._port)
            msg = b"login: "
            resp = self._tc.read_until(msg, 5)
            if (msg != resp.strip(b"\r\n")):
                raise ProcessorError(
                    "Unexpected data from GRX processor: " + resp.decode('ascii'))
            self._send(self._user)
            msg = b"connection established"
            resp = self._tc.read_until(msg, 5)
            if (msg != resp.strip(b"\r\n")):
                raise ProcessorError("Login to processor failed!")
            # Get the system status on startup
            self.request_system_status()
        except (BlockingIOError, ConnectionError, TimeoutError) as error:
            pass

    def _send(self, command):
        _LOGGER.debug(f"send: {command}")
        try:
            self._tc.write(command.encode('ascii') + b'\r\n')
        except (ConnectionError, AttributeError):
            self._tc = None
            return False

    def request_system_status(self):
        """ Request the state of all the control units"""
        return self._send(":G")

    def setScene(self, scene, unit):
        key = int(scene)
        cmdstr = f":A{SCENES_REV[key]}{unit}"
        self._send(cmdstr)

    def run(self):
        """Read and dispatch messages from the controller."""
        self._running = True
        while self._running:
            if self._tc == None:
                time.sleep(POLLING_FREQ)
                self._connect()
            else:
                try:
                    # Receive and process data
                    all_return = re.compile(b"[^/r]+")
                    port_listen = self._tc.expect([all_return])
                    # print(port_listen)
                    self._handle_response(port_listen[2].decode("ascii"))
                except (ConnectionError, AttributeError):
                    _LOGGER.warning("Lost connection.")
                    self._tc = None
                except UnicodeDecodeError:
                    port_listen = ""

    def _handle_response(self, status):
        _LOGGER.debug(f"Raw: {status}")
        try:
            status_regex = re.compile(r":ss\s(.*)\n")
            error_regex = re.compile(r"~ERROR(.*)\n")

            # check for button press (upper case A-X for unit, 0-9A-G for scene) and ignore lower case echo
            button_press_regex = re.compile(r"([A-X])([0-9A-F])\r\n")

            button_press = button_press_regex.findall(status)
            status_string = status_regex.findall(status)
            command_error = error_regex.findall(status)

            # Handle button press events first (time-sensitive)
            if button_press:
                for press in button_press:
                    unit_letter = press[0].upper()
                    scene_char = press[1].upper()

                    # Convert unit letter (A-X) to unit number (1-24)
                    unit_number = str(ord(unit_letter) - ord('A') + 1)

                    # Convert scene character to scene number using SCENES dict
                    scene_number = SCENES.get(scene_char, None)

                    if scene_number is not None:
                        button_data = {
                            'type': 'button_press',
                            'unit': unit_number,
                            'scene': scene_number
                        }
                        _LOGGER.debug(
                            f"Button press detected: Unit {unit_number}, Scene {scene_number}")
                        self._callback(button_data)

            # Handle status updates (existing functionality)
            if status_string:
                rawStatus = status_string[0]
                # convert scenes A to G to number
                pared_status = [SCENES[char] for char in (rawStatus[:8])]
                current_status = dict(zip(unit_list, pared_status))
                self._callback(current_status)
                status_string = None
            else:
                _LOGGER.warning(
                    f"Not handling: {status} Command Error: {command_error}")
                pass
        except ValueError:
            _LOGGER.warning(f"Weird data: {status}")

    def close(self):
        """Close the connection to the gateway."""
        self._running = False
        if self._tc:
            time.sleep(POLLING_FREQ)
            self._tc.close()
            self._tc = None
