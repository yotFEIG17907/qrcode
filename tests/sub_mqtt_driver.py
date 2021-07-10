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
        self.logger.info("Message received Topic (%s) Payload (%s)", topic, payload.decode("utf-8"))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Player")
    parser.add_argument("-l", "--log-config", type=Path, required=True, help="Path to logging configuration file")
    parser.add_argument("-id", "--client-id", type=str, required=False, default="music-player",
                        help="Client ID to use, must be unique, default is \"music-player\"")
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

    client_id = args.client_id
    cert_path = None
    username = None
    password = None
    hostname = "localhost"
    port = 1883
    # This topic is for music controlling messages
    sub_topic = "kontrol/music"
    keep_alive_seconds = 20

    test_listener = TestListener()
    comms = MqttComms(client_id=client_id,
                      cert_path=cert_path,
                      username=username,
                      password=password,
                      hostname=hostname,
                      port=port,
                      sub_topic=sub_topic,
                      msg_listener=test_listener)
    logger.info("Starting to listen")

    # This call will block so start a thread before this to shut it down after
    # some period of time

    def shutdown(run_period_seconds: int):
        logger.info("Sleep for a %d seconds then stop communications", run_period_seconds)
        time.sleep(run_period_seconds)
        logger.info("Tell communications to stop")
        comms.connection_stop()
        logger.info("Shutdown exiting")

    # Run these tasks in parallel, the communication task and a shutdown task
    run_tasks_in_parallel([
        lambda: comms.connect_and_run(keep_alive_seconds=keep_alive_seconds),
        lambda: shutdown(run_period_seconds=20)])

    logger.info("All done..")


if __name__ == "__main__":
    main()
