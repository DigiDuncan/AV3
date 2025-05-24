import logging
import time

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder

from digiosc.lib.types import IP, Atomic, Port, Seconds

logger = logging.getLogger("digiosc")

class OSCClient:
    def __init__(self, ip: IP = '127.0.0.1', port: Port = 9000):
        self.ip: IP = ip
        self.port: Port = port

        self.min_sleep: Seconds = 1/10

        self.client = udp_client.UDPClient(ip, port)

    def _send(self, address: str, data: tuple[Atomic, ...]):
        msg = OscMessageBuilder(address = address)
        try:
            for d in data:
                msg.add_arg(d)
            m = msg.build()
        except Exception as e:
            logger.error(e)
            return
        self.client.send(m)

    def send_button(self, address: str):
        """Quickly send an ON then OFF message to `address`."""
        msg = OscMessageBuilder(address = address)
        msg.add_arg(1)
        m = msg.build()

        msg_off = OscMessageBuilder(address = address)
        msg_off.add_arg(0)
        mo = msg_off.build()

        self.client.send(m)
        time.sleep(self.min_sleep)
        self.client.send(mo)
        logger.debug(f"{self.ip}:{self.port} | {address}: BUTTON")


    def send_int(self, address: str, data: Atomic):
        """Set data at address `address` to integer `data`."""
        senddata = int(data)
        self._send(address, (senddata,))
        logger.debug(f"{self.ip}:{self.port} | {address}: {data}")


    def send_float(self, address: str, data: Atomic):
        """Set data at address `address` to float `data`."""
        senddata = float(data)
        self._send(address, (senddata,))
        logger.debug(f"{self.ip}:{self.port} | {address}: {data}")


    def send_bool(self, address: str, data: Atomic):
        """Set data at address `address` to bool `data`."""
        senddata = bool(data)
        self._send(address, (senddata,))
        logger.debug(f"{self.ip}:{self.port} | {address}: {data}")


    def send_string(self, address: str, data: Atomic):
        """Set data at address `address` to string `data`."""
        senddata = str(data)
        self._send(address, (senddata,))
        logger.debug(f"{self.ip}:{self.port} | {address}: {data}")
