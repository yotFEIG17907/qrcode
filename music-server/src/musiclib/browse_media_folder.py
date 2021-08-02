from pathlib import Path

from musiclib.media_lib import MediaLibParsers

"""
A test program for verifying the music_lib package operation.
"""


def main():
    rootdir = Path("/Volumes/Samsung USB/")
    # rootdir = Path("/Volumes/DYLAN/")

    media_lib = MediaLibParsers.parse_lib(rootdir)
    print(f"{str(rootdir)} contains {media_lib.size()} playlists")
    print("Media lib kind:", media_lib.kind)
    for playlist in media_lib.playlists:
        print("Title:", playlist.get_title())
        print(f"There {playlist.size()} items in playlist")
        for item in playlist.items:
            print("Album:", item.album_name, "Item:", item.src, "Exists?", item.src.exists())


if __name__ == "__main__":
    main()
