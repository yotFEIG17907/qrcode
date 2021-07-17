import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pygame


@dataclass
class MusicPlayer():
    # A list of paths to music files (mp3, wav, possibly others)
    playlist: List[Path]
    # The parent folder where the playlist file was located
    playlist_root: Path

    def __init__(self, playlist_path: Path):
        self.logger = logging.getLogger("comms.mqtt")
        # Increase the buffer from the default of 512 to eliminate the underrun warning message that occurs
        # when running on the Raspberry PI
        pygame.mixer.pre_init(buffer=2048)
        pygame.mixer.init()
        if not playlist_path.exists():
            raise ValueError(f"Specified playlist file does not exist {str(playlist_path)}")
        self.playlist_root = playlist_path.parent
        with open(playlist_path, 'r') as f:
            mfs = [line.strip() for line in f if not line.startswith("#")]
        # Turn each string into an absolute path if not already absolute
        playlist = []
        for mf in mfs:
            music_file = Path(mf)
            if not music_file.is_absolute():
                music_file = self.playlist_root.joinpath(music_file)
            if music_file.exists():
                playlist.append(music_file)
            else:
                self.logger.warning("File mentioned in playlist, but not found %s", str(music_file))
        self.playlist = playlist
        self.logger.info("Loaded playlist from %s", str(playlist_path))
        self.logger.info("Playlist %s", playlist)

    def start(self, index: int) -> None:
        """
        Stop playing and load and play something else
        :param index: Identifies the item in the playlist to play
        :return: Nothing
        """
        music_file = self.playlist[index]
        if music_file.exists():
            self.logger.info("Stop playing current item, play %s",
                             str(self.playlist[index]))
            pygame.mixer.music.load(self.playlist[index])
            pygame.mixer.music.play()
            self.logger.info("Music loaded")
        else:
            self.logger.warning("Specified item %s not found, skip it", str(self.playlist[index]))

    def stop(self) -> None:
        """
        Stop the music
        :return: None
        """
        pygame.mixer.music.stop()

    def pause(self) -> None:
        """
        Pause the music
        :return: None
        """
        pygame.mixer.music.pause()

    def unpause(self) -> None:
        """
        Unpause the music
        :return: None
        """
        pygame.mixer.music.unpause()

    def set_volume(self, setting: int) -> None:
        """
        Sets the volume, 0 mutes completely. 100 is the full volume set by
        the host's volume control. The setting value is clamped to between 0
        and 100.
        :param setting: The new volume setting.
        :return: The old volume setting as a value between 0 and 100
        """
        old_volume = pygame.mixer.music.get_volume()
        new_value = max(0, min(100, setting))
        pygame.mixer.music.set_volume(new_value / 100.0)
        self.logger.info("Input value %d, adjusted to %d", setting, new_value)
        return int(old_volume * 100.0)
