import http.server
import platform

import pygame

HOST = "0.0.0.0"
PORT = 8000

musicfile = '/Users/kenm/Music/iTunes/iTunes Music/Unknown Artist/Unknown Album/Chris and James Nifong What a Wonderful World.mp3'
pygame.mixer.init()
pygame.mixer.music.load(musicfile)
pygame.mixer.music.set_volume(1.0)


def playit():

    print("Loaded and playing, hear anything?")
    pygame.mixer.music.play()
    return b"Started"

def stopit():
    pygame.mixer.music.stop()
    return b"Stopped"

class MusicServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print("Got", self.path)
        if self.path == '/play':
            result = playit()
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(result)
            self.wfile.flush()
        elif self.path == '/stop':
            result = stopit()
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(result)
            self.wfile.flush()
        else:
            self.send_error(404, "Not Found")

web_server = http.server.HTTPServer((HOST, PORT), MusicServer)

hostname = platform.node()
print(f"Server has started: {hostname} {PORT}")

try:
    web_server.serve_forever()
except KeyboardInterrupt:
    web_server.server_close()
finally:
    print("All done...")