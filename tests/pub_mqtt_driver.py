import argparse
import logging
import logging.config
import os
import time
from pathlib import Path

from comms import run_tasks_in_parallel
from comms.mqtt_comms import SensorListener, MqttComms


class TestListener(SensorListener):

    def __init__(self):
        self.logger = logging.getLogger("comms.mqtt")

    def on_disconnect(self, reason: str):
        self.logger.debug("Disconnection event %s", reason)

    def on_protocol_event(self, reason: str) -> None:
        self.logger.debug("Protocol Event %s", reason)

    def on_message(self, topic: bytes, payload: bytes):
        self.logger.info("Message received Topic (%s) Payload (%s)", topic.decode(encoding="UTF-8"),
                         payload.decode(encoding="UTF-8"))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Player")
    parser.add_argument("-l", "--log-config", type=Path, required=True, help="Path to logging configuration file")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    logging_configuration = args.log_config
    if not logging_configuration.exists():
        print("Path to logging configuration not found: ", str(logging_configuration))
        return

    log_folder = "target/logs"
    os.makedirs(log_folder, exist_ok=True)

    logging.config.fileConfig(logging_configuration, disable_existing_loggers=False)
    logger = logging.getLogger("comms.mqtt")
    logger.info("Starting music player")

    # Client id for this must be different from client id for the music player
    # or indeed for all the clients
    client_id = "music-controller"
    cert_path = None
    username = None
    password = None
    hostname = "localhost"
    port = 1883
    # This topic is for music controlling messages
    sub_topic = None
    pub_topic = "kontrol/music"
    keep_alive_seconds = 10

    test_listener = TestListener()
    comms = MqttComms(client_id=client_id,
                      cert_path=cert_path,
                      username=username,
                      password=password,
                      hostname=hostname,
                      port=port,
                      sub_topic=sub_topic,
                      msg_listener=test_listener)

    def publisher():
        for i in range(5):
            # Do things here for a while, then shut down
            logger.info("Try to publish payload")
            payload = f"Message #{i}"
            comms.publish(pub_topic, payload, qos=2)
            time.sleep(1)
        comms.connection_stop()

    # Need a list of function objects hence the use of the lambda keyword
    # without this, the function would simply be invoked and its return value
    # is what would be added to the list
    run_tasks_in_parallel([
        lambda: comms.connect_and_run(keep_alive_seconds=keep_alive_seconds),
        lambda: publisher()])
    logger.info("Shutting down")


if __name__ == "__main__":
    main()
