import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pygame

from speech import do_text_to_speech


@dataclass
class MusicPlayer():
    # The music player inside pygame might well be thread-safe
    # but this class is not. In particular, next and prev depend
    # on single-threadedness because they and the start method
    # read and write mru_index

    # A list of paths to music files (mp3, wav, possibly others)
    playlist: List[Path]
    # The parent folder where the playlist file was located
    playlist_root: Path

    # Holds index of the current or most recent item played
    mru_index: int

    def __init__(self, playlist_path: Path):
        self.logger = logging.getLogger("comms.mqtt")
        # Just start at the first item always
        self.mru_index = 0
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
        do_text_to_speech("Music Player is ready to go")

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
            pygame.mixer.music.stop()
            item: Path = self.playlist[index]
            item_name = item.stem
            do_text_to_speech(f"Start playing song {item_name}")
            pygame.mixer.music.load(item)
            pygame.mixer.music.play()
            self.logger.info("Music loaded")
            self.mru_index = index
        else:
            self.logger.warning("Specified item %s not found, skip it", str(self.playlist[index]))

    def set_playlist(self, index: int) -> None:
        """
        Keep playing the current song if any, but switch the playlist to the new
        value if it is in range. The next item to be played will be from
        the new list.
        :param index: Identifies which playlist to make the active one.
        :return: Nothing
        """
        # Not fully implemented at this time
        self.logger.info("Select the playlist %d", index)
        do_text_to_speech(f"Play list has been set to number {index}")

    def do_status_report(self) -> None:
        """
        Report the playlist parameters
        :param index: Identifies which playlist to make the active one.
        :return: Nothing
        """
        # Not fully implemented at this time
        self.logger.info("Reporting music player parameters")
        # Another thread issue here, if the user changes the volume
        # while the status is reported, this will be overwritten
        # when the volume is reset to the value saved here. Really need
        # a lock here so the volume cannot be changed until the speech is finished
        curr_vol = self.get_volume()
        self.set_volume(20)
        msg = f"There is one playlist with {len(self.playlist)} items"
        self.logger.info(msg)
        do_text_to_speech(msg)
        msg = f"Current song is {self.playlist[self.mru_index].stem.split(' ')[1]}"
        self.logger.info(msg)
        do_text_to_speech(msg)
        self.set_volume(curr_vol * 100)

    def next(self) -> None:
        """
        Play the next item, wrapping around to 0 if the end it reached
        :return: None
        """
        temp = self.mru_index + 1
        if temp > len(self.playlist):
            temp = 0
        self.start(temp)

    def prev(self) -> None:
        """
        Play the previous item, wrapping around to the end of the playlist if necessary
        :return: None
        """
        temp = self.mru_index - 1
        if temp < 0:
            temp = len(self.playlist) - 1
        self.start(temp)

    def stop(self) -> None:
        """
        Stop the music
        :return: None
        """
        do_text_to_speech("Stop")
        pygame.mixer.music.stop()

    def pause(self) -> None:
        """
        Pause the music
        :return: None
        """
        do_text_to_speech("Pause")
        pygame.mixer.music.pause()

    def unpause(self) -> None:
        """
        Unpause the music
        :return: None
        """
        do_text_to_speech("Resume")
        pygame.mixer.music.unpause()

    def get_volume(self):
        return pygame.mixer.music.get_volume()

    def set_volume(self, setting: int) -> None:
        """
        Sets the volume, 0 mutes completely. 100 is the full volume set by
        the host's volume control. The setting value is clamped to between 0
        and 100.
        :param setting: The new volume setting.
        :return: The old volume setting as a value between 0 and 100
        """
        do_text_to_speech(f"Set volume {setting}")
        old_volume = pygame.mixer.music.get_volume()
        new_value = max(0, min(100, setting))
        pygame.mixer.music.set_volume(new_value / 100.0)
        self.logger.info("Input value %d, adjusted to %d", setting, new_value)
        return int(old_volume * 100.0)
