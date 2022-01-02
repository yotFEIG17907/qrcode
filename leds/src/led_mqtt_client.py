"""
Receives LED control messages via MQTT and loads them into the LED Strand
to set the LEDs.
"""
import argparse
import logging
import logging.config
import time
import traceback
from pathlib import Path

from comms import run_tasks_in_parallel_no_block
from comms.mqtt_comms import MqttComms, SensorListener
from discovery import get_service_host_port_block
from led_utls.led_strand_class import LEDStrand
from messages.serdeser import cmd_from_json


class LEDCommandGatewayListener(SensorListener):
    """
    This handles messages and other events received from the MQTT broker.
    The messages are expected to be JSON and are parsed into commands
    which are used to command the music player.
    """

    def __init__(self, led_driver = None):
        self.logger = logging.getLogger("comms.mqtt")
        self.led_driver = led_driver

    def on_disconnect(self, reason: str):
        self.logger.debug("Disconnection event %s", reason)

    def on_protocol_event(self, reason: str) -> None:
        self.logger.debug("Protocol Event %s", reason)

    def on_message(self, topic: str, payload: bytes):
        try:
            cmd_str = payload.decode("utf-8")
            cmd = cmd_from_json(cmd_str)
            self.logger.debug("Topic %s, Payload %s", topic, type(cmd))
            if self.led_driver is not None:
                self.led_driver.execute(cmd)

        except Exception as e:
            self.logger.error("Problem with message %s:%s, exception %s", topic, cmd_str, str(e))
            traceback.print_exc()


def parse_arguments() -> argparse.Namespace:
    # default_mqtt_broker = "localhost:1883"
    default_mqtt_service_name = "DYLAN MQTT Server"
    default_cmd_topic = "kontrol/led"
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
                        help=f"The topic to receive music commands, default is \"{default_cmd_topic}\"")
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
    logger.info("Starting LED Controller %s", "v2")

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
    keep_alive_seconds = 20

    led_driver = LEDStrand(n=100)
    test_listener = LEDCommandGatewayListener(led_driver=led_driver)
    comms = MqttComms(client_id=client_id,
                      cert_path=cert_path,
                      username=username,
                      password=password,
                      hostname=hostname,
                      port=port,
                      cmd_topic=cmd_topic,
                      msg_listener=test_listener)
    logger.info("Starting to listen to broker %s:%d, cmd topic: %s", hostname, port, cmd_topic)

    # Run these tasks in parallel, the communication task.
    # Add the shutdown task if you want the whole program to exit after some delay
    # Note: in this version the shutdown is not provided so the program will keep going
    # for ever or until stopped by some other means
    run_tasks_in_parallel_no_block([
        lambda: comms.connect_and_run(keep_alive_seconds=keep_alive_seconds)])

    logger.info("All done..")


if __name__ == "__main__":
    main()
