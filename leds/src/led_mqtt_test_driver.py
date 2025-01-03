"""
Generates commands to control the LEDs, publishes there to MQTT server
This is to be used for testing the led_mqtt_client

"""
import argparse
import logging
import logging.config
import time
from pathlib import Path
from typing import Any

from comms import run_tasks_in_parallel_no_block
from comms.mqtt_comms import MqttComms, SensorListener
from discovery import get_service_host_port_block
from led_messages.led_commands import FillAll, SetPixels
from led_mqtt_client import LEDCommandGatewayListener
from led_utls.nm_to_rgb import wavelength_range, wavelength_to_rgb
from messages.serdeser import cmd_to_json


class DriverCommsRunner:
    # The gateway to the MQTT server
    comms: MqttComms

    def __init__(self,
                 client_id: str,
                 cert_path: Path,
                 username: str,
                 password: str,
                 hostname: str,
                 port: int,
                 cmd_topic: str,
                 msg_listener: SensorListener):
        self.comms = MqttComms(client_id=client_id,
                               cert_path=cert_path,
                               username=username,
                               password=password,
                               hostname=hostname,
                               port=port,
                               cmd_topic=cmd_topic,
                               msg_listener=msg_listener)

    def run(self, keep_alive_seconds: int) -> None:
        """
        This method will block until error
        :param keep_alive_seconds: Ping will be set after this many seconds to keep
        the connection open
        :return: Nothing
        """
        self.comms.connect_and_run(keep_alive_seconds=keep_alive_seconds)

    def publish(self, pub_topic: str, cmd: Any):
        msg = cmd_to_json(cmd)
        self.comms.publish(topic=pub_topic, payload=msg, qos=2)

    def shutdown(self):
        self.comms.connection_stop()


def parse_arguments() -> argparse.Namespace:
    default_mqtt_service_name = "DYLAN MQTT Server"
    default_cmd_topic = "kontrol/led"
    default_control_topic = "test-driver/led"
    parser = argparse.ArgumentParser(description="LED Controller")
    parser.add_argument("-l", "--log-config", type=Path, required=True, help="Path to logging configuration file")
    parser.add_argument("-id", "--client-id", type=str, required=False, default="music-player",
                        help="Client ID to use, must be unique, default is \"music-player\"")
    parser.add_argument("-broker", "--mqtt-broker", type=str, required=False, default=None,
                        help="Host and port of the MQTT broker, takes precedence if both this and "
                             "service-name are provided")
    parser.add_argument("-s", "--service-name", type=str, required=False, default=default_mqtt_service_name,
                        help=f"Service name for the MQTT Broker, will be looked up using Bonjour, "
                             f"use only if mqtt-broker not provided")
    parser.add_argument("-t", "--cmd-topic", type=str, required=False, default=default_cmd_topic,
                        help=f"The topic to publish LED commands, default is \"{default_cmd_topic}\"")
    parser.add_argument("-c", "--control-topic", type=str, required=False, default=default_control_topic,
                        help=f"The driver will receive control commands on this topic, "
                             f"\default is \"{default_control_topic}\"")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    logging_configuration = args.log_config
    if not logging_configuration.exists():
        print("Path to logging configuration not found: ", str(logging_configuration))
        return

    logging.config.fileConfig(logging_configuration, disable_existing_loggers=False)
    logger = logging.getLogger("comms.mqtt")
    logger.info("Starting LED MQTT Test Driver %s", "v2")

    client_id = f"{args.client_id}-{int(time.time())}"
    cert_path = None
    username = None
    password = None
    # Try finding the broker using Zeroconf first
    if args.service_name is not None:
        # look MQTT broker up using Bonjour / Zeroconf
        type = "_mqtt._tcp.local."
        name = args.service_name
        hostname, port = get_service_host_port_block(type=type, name=name, logger=logger)
    elif args.mqtt_broker is not None:
        hostport = args.mqtt_broker.split(':')
        hostname = hostport[0]
        port = int(hostport[1])
    else:
        print("Must provide either MQTT Broker host/port or the Bonjour name of the service")
    # This topic is for music controlling messages
    cmd_topic = args.cmd_topic
    driver_control_topic = args.control_topic
    keep_alive_seconds = 20

    test_listener = LEDCommandGatewayListener()
    comms = DriverCommsRunner(client_id=client_id,
                              cert_path=cert_path,
                              username=username,
                              password=password,
                              hostname=hostname,
                              port=port,
                              cmd_topic=driver_control_topic,
                              msg_listener=test_listener)
    logger.info("Starting to listen to broker %s:%d, cmd topic: %s", hostname, port, cmd_topic)

    # Run these tasks in parallel, the communication task.
    # Add the shutdown task if you want the whole program to exit after some delay
    # Note: in this version the shutdown is not provided so the program will keep going
    # for ever or until stopped by some other means
    run_tasks_in_parallel_no_block([
        lambda: comms.run(keep_alive_seconds=keep_alive_seconds)])

    time.sleep(1.0)

    cmd = FillAll(payload=(155, 155, 155))
    comms.publish(cmd_topic, cmd)
    time.sleep(3.0)
    cmd = FillAll(payload=(0, 0, 0))
    comms.publish(cmd_topic, cmd)

    num_pixels = 100
    # Cycle the LEDs from RED to VIOLET
    wavelengths = wavelength_range()
    for i in range(int(wavelengths[1]), int(wavelengths[0]), -5):
        values = []
        for pixel in range(num_pixels):
            values.append(wavelength_to_rgb(i))
        cmd = SetPixels(payload=values)
        comms.publish(cmd_topic, cmd)
        time.sleep(1.0)
    cmd = FillAll(payload=(0, 0, 0))
    comms.publish(cmd_topic, cmd)

    # Generate and publish the commands
    time.sleep(5.0)

    comms.shutdown()
    logger.info("Main Thread Done..")


if __name__ == "__main__":
    main()
