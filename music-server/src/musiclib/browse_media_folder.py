from pathlib import Path

from musiclib.media_lib import MediaLibParsers

"""
A test program for verifying the music_lib package operation.
"""


def main():
    rootdirs = [Path("/Volumes/Samsung USB/"), Path("/Volumes/DYLAN/")]

    media_lib = MediaLibParsers.parse_lib(rootdirs)
    print(f"{str(rootdirs)} contains {media_lib.size()} playlists")
    for playlist in media_lib.playlists:
        print("Kind:", playlist.get_kind())
        print("Title:", playlist.get_title())
        print(f"There {playlist.size()} items in playlist")
        for item in playlist.items:
            print("Album:", item.album_name, "Item:", item.src, "Exists?", item.src.exists())


if __name__ == "__main__":
    main()
