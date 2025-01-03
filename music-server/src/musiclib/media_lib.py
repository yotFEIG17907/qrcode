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

    def get_song_name(self) -> str:
        return self.src.stem


@dataclass
class Playlist():
    # The volume this playlist was found on
    volume: Path
    # What kind of playlist is this (Windows or what)
    kind: str
    # The title of this playlist
    title: str

    # Holds a list of items in the playlist and metadata
    items: List[Item]

    def exists(self, id: int) -> bool:
        return 0 <= id < len(self.items)

    def get_item_by_id(self, id: int) -> Item:
        """
        May throw out of bound if the index is out of range, call exists first to void this
        :param id:
        :return: The indexed item or raise an exception if index is out of range.
        """
        return self.items[id]

    def get_title(self) -> str:
        return self.title

    def get_kind(self) -> str:
        return self.kind

    def size(self) -> int:
        return len(self.items)


@dataclass
class MediaLib():
    # A collection of the playlists found one more volumes
    playlists: List[Playlist]

    def get_info(self) -> str:
        return f"Loaded {len(self.playlists)} playlists"

    def exists(self, id: int) -> bool:
        """
        Return if the specified playlist exists otherwise false.
        Call this before called get_playlist_by_id to avoid the ValueError exception if
        id is out of range.
        :param id: An index into the playlists
        :return: True if the index is in range
        """
        return 0 <= id < len(self.playlists)

    def add_playlist(self, playlist: Playlist) -> None:
        """
        Add the given playlist to the collection of playlists
        :param playlist: A playlist to add to the media lib
        :return: Nothing
        """
        self.playlists.append(playlist)

    def add_playlists(self, playlists: List[Playlist]) -> None:
        """
        Add the list of playlists to the media lib collection
        :param playlists: A list of one or more playlists to add to the collection
        :return: Nothing
        """
        self.playlists.extend(playlists)

    def get_playlist_by_id(self, id: int) -> Playlist:
        return self.playlists[id]

    def size(self) -> int:
        """
        Return the number of playlists the library contains
        :return: Number of playlists
        """
        return len(self.playlists)


class MediaLibParsers:

    @staticmethod
    def parse_lib(volumes: List[Path]) -> MediaLib:
        """
        :param volumes: A collection of volumes to search for playlists, everything found
        is added to a single MediaLib which is returned
        :return A populated media lib
        """
        medialib = MediaLib(playlists=[])
        for volume in volumes:
            if MediaLibParsers.is_windows_media_folder(volume):
                MediaLibParsers.create_from_windows_media(volume, medialib)
            elif MediaLibParsers.is_simple_text_playlist(volume):
                MediaLibParsers.create_from_simple_text_playlist(volume, medialib)
            else:
                # Not a Windows Media Folder and doesn't contain a simple playlist,
                # just make a list of all the MP3 files and make a single playlist
                MediaLibParsers.create_single_playlist(volume, medialib)
        return medialib

    @staticmethod
    def is_simple_text_playlist(volume: Path) -> bool:
        txt_files = volume.rglob('*.txt')
        count = 0
        for file in txt_files:
            count += 1
        return count > 0

    @staticmethod
    def create_from_simple_text_playlist(volume: Path, medialib: MediaLib) -> MediaLib:
        """
        Create the media lib from a volume that contains simple playlists, just text file
        with a list of music files.
        :param volume: The root to search from
        :param medialib: The playlists found are added to this collection
        :return: A Media Lib
        """
        # Recursive search for plain text playlists
        simple_playlists = volume.rglob('*.txt')
        playlists: List[Playlist] = []
        for playlist_path in simple_playlists:
            if not playlist_path.exists():
                continue
            playlist_root = playlist_path.parent
            title = playlist_path.stem
            with open(playlist_path, 'r') as f:
                mfs = [line.strip() for line in f if not line.startswith("#")]
                # Turn each string into an absolute path if not already absolute
                items: List[Item] = []
                for mf in mfs:
                    music_file = Path(mf)
                    if not music_file.is_absolute():
                        music_file = playlist_root.joinpath(music_file)
                    if music_file.exists():
                        item: Item = Item(album_name=music_file.parent.stem, src=music_file)
                        items.append(item)
                    else:
                        print(f"**WARN** File mentioned in playlist, but not found {str(music_file)}")
            playlist: Playlist = Playlist(volume=volume, kind="Simple Text Playlist", title=title, items=items)
            playlists.append(playlist)
        if len(playlists) > 0:
            medialib.add_playlists(playlists)
        return medialib

    @staticmethod
    def create_single_playlist(volume: Path, medialib: MediaLib) -> MediaLib:
        """
        Search for all supported media files, e.g. MP3, WAV and OGG
        and make a single playlist from that
        :param volume: The volume to search
        :return:
        """
        items: List[Item] = []
        # Ignore hidden files
        visible_files = [file for file in volume.rglob('*.mp3') if not file.name.startswith('.')]
        for path in visible_files:
            items.append(Item(src=path, album_name=path.parent.stem))
        playlist = Playlist(volume=volume, kind="Single Playlist", title="All Items", items=items)
        medialib.add_playlist(playlist)
        return medialib

    @staticmethod
    def create_from_windows_media(volume: Path, medialib: MediaLib) -> MediaLib:
        """
        Create the library from the given Windows Media Folder
        :param volume: Path to the folder
        :param medialib: The playlists found are added to this collection
        :return: A populated media lib
        """
        playlists_root = volume.joinpath("Playlists")
        all_playlists_path = playlists_root.glob('*.wpl')
        playlists: List[Playlist] = []
        for pl_path in all_playlists_path:
            playlist = MediaLibParsers.parse_wpl_playlist(volume, pl_path)
            playlists.append(playlist)
        if len(playlists) > 0:
            medialib.add_playlists(playlists)
        return medialib

    @staticmethod
    def is_windows_media_folder(volume: Path) -> bool:
        """
        If this has a Playlists folder and at least one wpl file then return true
        :param volume: Path to the volume in question
        :return: True if this is a Windows Medid folder
        """
        playlists_root = volume.joinpath("Playlists")
        if playlists_root.exists():
            count = 0
            for file in playlists_root.glob('*.wpl'):
                count += 1
            result = count > 0
        else:
            result = False
        return result

    @staticmethod
    def parse_wpl_playlist(volume: Path, pl_path: Path) -> Playlist:
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
        return Playlist(volume=volume, kind="Windows Media Playlist", title=title, items=items)
