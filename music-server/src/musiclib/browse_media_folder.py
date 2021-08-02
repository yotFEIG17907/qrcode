from pathlib import Path

from musiclib.media_lib import MediaLibParsers


def main():
    rootdir = Path("/Volumes/Samsung USB/")

    media_lib = MediaLibParsers.parse_lib(rootdir)
    print(f"{str(rootdir)} contains {media_lib.size()} playlists")
    for playlist in media_lib.playlists:
        print("Title:", playlist.get_title())
        print(f"There {playlist.size()} items in playlist")
        for item in playlist.items:
            print("Album:", item.album_name, "Item:", item.src, "Exists?", item.src.exists())


if __name__ == "__main__":
    main()
