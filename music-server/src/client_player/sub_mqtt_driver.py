import argparse
import logging
import logging.config
import os
import time
from pathlib import Path

from client_player.music_player import MusicPlayer
from comms import run_tasks_in_parallel_no_block
from comms.mqtt_comms import SensorListener, MqttComms
from messages.music_control import MusicPlayCommand, MusicStopCommand, MusicVolumeCommand, \
    MusicPauseCommand, MusicUnpauseCommand, MusicNextCommand, MusicPrevCommand
from messages.serdeser import cmd_from_json

"""
This is the music player, it receives commands from the mqtt broker and controls
the sound hardware to play, stop or change the volume.
It needs to be loaded with a playlist, a list of songs, the commands include an
index that is used as a reference to this playlist.
"""


class MusicCommandGatewayListener(SensorListener):
    """
    This handles messages and other events received from the MQTT broker.
    The messages are expected to be JSON and are parsed into commands
    which are used to command the music player.
    """

    def __init__(self, playlist_path: Path):
        self.logger = logging.getLogger("comms.mqtt")
        self.player = MusicPlayer(playlist_path=playlist_path)

    def on_disconnect(self, reason: str):
        self.logger.debug("Disconnection event %s", reason)

    def on_protocol_event(self, reason: str) -> None:
        self.logger.debug("Protocol Event %s", reason)

    def on_message(self, topic: str, payload: bytes):
        try:
            cmd_str = payload.decode("utf-8")
            cmd = cmd_from_json(cmd_str)
            self.logger.info("Message received Topic (%s) Type(%s) Payload (%s)", topic, type(cmd), str(cmd))
            if isinstance(cmd, MusicPlayCommand):
                self.player.start(cmd.payload)
            elif isinstance(cmd, MusicNextCommand):
                self.player.next()
            elif isinstance(cmd, MusicPrevCommand):
                self.player.prev()
            elif isinstance(cmd, MusicStopCommand):
                self.player.stop()
            elif isinstance(cmd, MusicPauseCommand):
                self.player.pause()
            elif isinstance(cmd, MusicUnpauseCommand):
                self.player.unpause()
            elif isinstance(cmd, MusicVolumeCommand):
                self.player.set_volume(cmd.payload)
            else:
                self.logger.warning("Unsupported cmd type %s", type(cmd))
        except Exception as e:
            self.logger.error("Problem de-serialized message %s", str(e))


def parse_arguments() -> argparse.Namespace:
    default_mqtt_broker = "localhost:1883"
    default_cmd_topic = "kontrol/music"
    parser = argparse.ArgumentParser(description="Music Player")
    parser.add_argument("-l", "--log-config", type=Path, required=True, help="Path to logging configuration file")
    parser.add_argument("-id", "--client-id", type=str, required=False, default="music-player",
                        help="Client ID to use, must be unique, default is \"music-player\"")
    parser.add_argument("-broker", "--mqtt-broker", type=str, required=False, default=default_mqtt_broker,
                        help=f"Host and port of the MQTT broker, default is \"{default_mqtt_broker}\"")
    parser.add_argument("-t", "--cmd-topic", type=str, required=False, default=default_cmd_topic,
                        help=f"The topic to receive music commands, default is \"{default_cmd_topic}\"")
    parser.add_argument("-p", "--playlist", type=Path, required=True,
                        help="Path to the file that lists the music files to be played")
    args = parser.parse_args()
    return args


def main():
    global playlist

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
    playlist_path: Path = args.playlist
    if not playlist_path.exists():
        logger.warning("Specified playlist file not found %s", str(playlist_path))
        return
    cert_path = None
    username = None
    password = None
    hostport = args.mqtt_broker.split(':')
    hostname = hostport[0]
    port = int(hostport[1])
    # This topic is for music controlling messages
    cmd_topic = args.cmd_topic
    keep_alive_seconds = 20

    test_listener = MusicCommandGatewayListener(playlist_path=playlist_path)
    comms = MqttComms(client_id=client_id,
                      cert_path=cert_path,
                      username=username,
                      password=password,
                      hostname=hostname,
                      port=port,
                      cmd_topic=cmd_topic,
                      msg_listener=test_listener)
    logger.info("Starting to listen to broker %s, cmd topic: %s", args.mqtt_broker, cmd_topic)

    def shutdown(run_period_seconds: int):
        """
        This sleeps for some period and then stops the connection and returns. Stopping
        the connection will cause an event that stops the main communications loop and
        the program ends.
        :param run_period_seconds: The number of seconds to run before shutting down
        :return: Nothing
        """
        logger.info("Sleep for a %d seconds then stop communications", run_period_seconds)
        time.sleep(run_period_seconds)
        logger.info("Programmed shutdown after %d seconds", run_period_seconds)
        comms.connection_stop()
        logger.info("Shutdown exiting")

    # Run these tasks in parallel, the communication task.
    # Add the shutdown task if you want the whole program to exit after some delay
    # Note: in this version the shutdown is not provided so the program will keep going
    # for ever or until stopped by some other means
    run_tasks_in_parallel_no_block([
        lambda: comms.connect_and_run(keep_alive_seconds=keep_alive_seconds)])

    logger.info("All done..")


if __name__ == "__main__":
    main()
