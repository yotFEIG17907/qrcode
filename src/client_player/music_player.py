import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pygame


@dataclass
class MusicPlayer():
    # A list of paths to music files (mp3, wav, possibly others)
    playlist: List[Path]

    def __init__(self, playlist: List[Path]):
        pygame.mixer.init()
        self.playlist = playlist
        self.logger = logging.getLogger("comms.mqtt")

    def start(self, index: int) -> None:
        """
        Stop playing and load and play something else
        :param index: Identifies the item in the playlist to play
        :return: Nothing
        """
        if self.playlist[index].exists():
            self.logger.info("Stop playing current item, play %s",
                             str(self.playlist[index]))
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.playlist[index])
            pygame.mixer.music.play()
            self.logger.info("Music loaded")
        else:
            self.logger.warning("Specified item %s not found", str(self.playlist[index]))

    def stop(self) -> None:
        """
        Stop the music
        :return: None
        """
        pygame.mixer.music.stop()

    def set_volume(self, setting: float) -> None:
        self.logger.info("Set volume to %f", setting)
        pygame.mixer.music.set_volume(setting)
