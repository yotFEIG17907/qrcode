import argparse
import logging
import logging.config
import time
import traceback
from pathlib import Path
from typing import List

from client_player.music_player import MusicPlayer
from comms import run_tasks_in_parallel_no_block
from comms.mqtt_comms import SensorListener, MqttComms
from discovery import get_service_host_port_block
from messages.music_control import MusicPlayCommand, MusicStopCommand, MusicVolumeCommand, \
    MusicPauseCommand, MusicUnpauseCommand, MusicNextCommand, MusicPrevCommand, MusicListCommand, MusicStatusReport
from messages.serdeser import cmd_from_json
from musiclib.media_lib import MediaLib, MediaLibParsers

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

    def __init__(self, volumes: List[Path]):
        self.logger = logging.getLogger("comms.mqtt")
        media_lib: MediaLib = MediaLibParsers.parse_lib(volumes)
        self.player = MusicPlayer(media_lib=media_lib)

    def on_disconnect(self, reason: str):
        self.logger.debug("Disconnection event %s", reason)

    def on_protocol_event(self, reason: str) -> None:
        self.logger.debug("Protocol Event %s", reason)

    def on_message(self, topic: str, payload: bytes):
        try:
            cmd_str = payload.decode("utf-8")
            self.logger.info("Payload %s", cmd_str)
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
            elif isinstance(cmd, MusicListCommand):
                self.player.set_playlist(cmd.payload)
            elif isinstance(cmd, MusicStatusReport):
                self.player.do_status_report()
            else:
                self.logger.warning("Unsupported cmd type %s", type(cmd))
        except Exception as e:
            self.logger.error("Problem executing message %s, exception %s", cmd_str, str(e))
            traceback.print_exc()


def parse_arguments() -> argparse.Namespace:
    # default_mqtt_broker = "localhost:1883"
    default_mqtt_service_name = "DYLAN MQTT Server"
    default_cmd_topic = "kontrol/music"
    parser = argparse.ArgumentParser(description="Music Player")
    parser.add_argument("-l", "--log-config", type=Path, required=True, help="Path to logging configuration file")
    parser.add_argument("-id", "--client-id", type=str, required=False, default="music-player",
                        help="Client ID to use, must be unique, default is \"music-player\"")
    parser.add_argument("-broker", "--mqtt-broker", type=str, required=False, default=None,
                        help="Host and port of the MQTT broker, takes precedence if both this and service-name are provided")
    parser.add_argument("-s", "--service-name", type=str, required=False, default=default_mqtt_service_name,
                        help=f"Service name for the MQTT Broker, will be looked up using Bonjour, use only if mqtt-broker not provided")
    parser.add_argument("-t", "--cmd-topic", type=str, required=False, default=default_cmd_topic,
                        help=f"The topic to receive music commands, default is \"{default_cmd_topic}\"")
    parser.add_argument("-v", "--volumes", nargs="+", type=Path, required=True,
                        help="One or more Paths to volumes that hold the music and the playlists, They must all exist."
                             "Use space as the separator")
    args = parser.parse_args()
    return args


def main():
    global playlist

    args = parse_arguments()
    logging_configuration = args.log_config
    if not logging_configuration.exists():
        print("Path to logging configuration not found: ", str(logging_configuration))
        return

    logging.config.fileConfig(logging_configuration, disable_existing_loggers=False)
    logger = logging.getLogger("comms.mqtt")
    logger.info("Starting music player %s", "v2")

    client_id = f"{args.client_id}-{int(time.time())}"
    volumes: List[Path] = args.volumes
    vc = 0
    for volume in volumes:
        if volume.exists():
            vc += 1
            logger.info("Music volume found %s", str(volume))
        else:
            logger.warning("Specified music volume not found %s", str(volume))
    if vc < len(volumes):
        logger.warning("Not all specified volumes found, will exit")
        return
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

    test_listener = MusicCommandGatewayListener(volumes=volumes)
    comms = MqttComms(client_id=client_id,
                      cert_path=cert_path,
                      username=username,
                      password=password,
                      hostname=hostname,
                      port=port,
                      cmd_topic=cmd_topic,
                      msg_listener=test_listener)
    logger.info("Starting to listen to broker %s:%d, cmd topic: %s", hostname, port, cmd_topic)

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
