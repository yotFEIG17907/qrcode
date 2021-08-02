"""
A class for parsing and reading Windows Media Playlists
"""
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import List

from lxml import etree


@dataclass
class Item():
    # The absolute path to a music item
    src: Path

    # Holds the name of the parent folder, which in some cases is the album name
    album_name: str

@dataclass
class Playlist():
    # The title of this playlist
    title: str

    # Holds a list of items in the playlist and metadata
    items: List[Item]

    def get_item_by_id(self, id: int) -> Item:
        if 0 <= id < len(self.items):
            return self.items[id]
        else:
            raise ValueError(f"Given id is out of range 0 to {len(self.items)}, got {id}")

    def get_title(self) -> str:
        return self.title

    def size(self) -> int:
        return len(self.items)


@dataclass
class MediaLib():
    # The path
    volume: Path

    # A collection of the playlists found in the given volume
    playlists: List[Playlist]

    def get_playlist_by_id(self, id: int) -> Playlist:
        if 0 <= id < len(self.playlists):
            return self.playlists[id]
        else:
            raise ValueError(f"Playlist ID is out of range 0 to {len(self.playlists)}, got {len(self.playlists)}")

    def size(self) -> int:
        """
        Return the number of playlists the library contains
        :return: Number of playlists
        """
        return len(self.playlists)


class MediaLibParsers:

    @staticmethod
    def parse_lib(volume: Path) -> MediaLib:
        """
        Parse all the playlists found in the given volume, order them alphabetically and save here
        :param volume: Path to a folder containing music files
        """
        if MediaLibParsers.is_windows_media_folder(volume):
            return MediaLibParsers.create_from_windows_media(volume)
        else:
            # Not a Windows Media Folder, make a list of all the MP3 files
            # and make a single playlist
            return MediaLibParsers.create_single_playlist(volume)

    @staticmethod
    def create_single_playlist(volume: Path) -> MediaLib:
        """
        Search for all supported media files, e.g. MP3, WAV and OGG
        and make a single playlist from that
        :param volume: The volume to search
        :return:
        """
        items: List[Item] = []
        for path in volume.rglob('*.mp3'):
            items.append(Item(src=path, album_name=path.parent.stem))
        playlist = Playlist(title="All Items", items=items)
        playlists: List[Playlist] = [playlist]
        return MediaLib(volume=volume, playlists=playlists)

    @staticmethod
    def create_from_windows_media(volume: Path) -> MediaLib:
        """
        Create the library from the given Windows Media Folder
        :param volume: Path to the folder
        :return: A populated media lib
        """
        playlists_root = volume.joinpath("Playlists")
        all_playlists_path = playlists_root.glob('*.wpl')
        playlists: List[Playlist] = []
        for pl_path in all_playlists_path:
            playlist = MediaLibParsers.parse_wpl_playlist(pl_path)
            playlists.append(playlist)
        return MediaLib(volume=volume, playlists=playlists)

    @staticmethod
    def is_windows_media_folder(volume: Path) -> bool:
        """
        If this has a Playlists folder and at least one wpl file then return true
        :param volume: Path to the volume in question
        :return: True if this is a Windows Medid folder
        """
        playlists_root = volume.joinpath("Playlists")
        if playlists_root.exists():
            result = playlists_root.glob('*.wpl')
        else:
            result = False
        return result

    @staticmethod
    def parse_wpl_playlist(pl_path: Path) -> Playlist:
        """
        Open the given Windows playlist file and extract the title and list of items
        :param pl_path: The path to the playlist
        :return: A Playlist object containing a list of the items in it
        """
        playlists_root = pl_path.parent
        tree = etree.parse(str(pl_path))

        title = tree.xpath('/smil/head/title')[0].text
        items_element = tree.xpath('/smil/body/seq/media')
        items: List[Item] = []
        for item in items_element:
            item_rel_path = PureWindowsPath(item.attrib['src'])
            item_path = playlists_root.joinpath(item_rel_path)
            item = Item(src=item_path, album_name=item_path.parent.stem)
            items.append(item)
        return Playlist(title=title, items=items)
