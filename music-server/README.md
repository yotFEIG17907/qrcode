# Overview

ActiveMQ broker runs somewhere, possibly on the RaspberryPI. A script subscribes to a topic providing messages that tell
it what to do. There will be a different topic for each kind of control message. Messages are published to this topic
from a variety of sources:

* A web server application that publishes messages based on invocation of its REST API methods. An IPhone scans a QR
  Code that contains a URL with one of the REST API calls and publishes a corresponding message to the AMQ Broker.
* A stand-alone script on a Pi-Zero with a RFID reader publishes a message containing selected parts of the data in the
  RFID token. Like a "wand".

The MQTT messages do things like:

* Start playing a playlist item, the item index provided in the message. The message has an index into the current play
  list. The file paths in the playlist are absolute or relative. Relative paths will be relative to the folder that the
  playlist itself was found in. Some questions:
    1. Is the new index played after the current one finishes or does it cause the current one to terminate immediately?
       I like the idea of adding the index to a list of items to play that is managed by the music player.
* Stop playing the current playlist item
* Pause/Resume the current playlist item
* Reset

All the messages are JSON and follow the same format, which is TBD

# Packages

## client_player

This subscribes to the topic and executes actions specified in the messages, e.g. to play an MP3. It needs to:

* Connect to an MQTT broker (mqtt protocol)
* Read in a playlist that maps an index to the path to an Audio file.
* Execute the actions specified in the messages
  ** PLAY
  ** STOP
* Connect and re-connect to the broker

Configuration

* The host and port of the AMQ broker
* The topic to subscribe to
* The playlist that maps index to Audio file

## HTTP to MQTT Bridge

This is a web server application. The main endpoint for this application does this:

* Connects and re-connects to an MQTT broker
* Receives a request that has a topic + data, e.g. an integer which is the playlist index
* It packs the data into a JSON message and publishes to the specified topic

Configuration:

* The IP and port to listen on
* The host and port of the MQTT broker
* The topic to publish to

There are two test drivers used to explore how to pub/sub and deal with the broker connection
failing. `pub_mqtt_driver.py` and `sub_mqt_driver.py`

# Docker Stuff

This assumes Docker community edition is installed which it is.

## Run Portainer in Docker

[https://documentation.portainer.io/v2.0/deploy/ceinstalldocker/](https://documentation.portainer.io/v2.0/deploy/ceinstalldocker/)

## Run MQTT Broker in docker

* [Run MQTT in docker](https://philhawthorne.com/setting-up-a-local-mosquitto-server-using-docker-for-mqtt-communication/)
* [Eclipse MQTT](https://hub.docker.com/_/eclipse-mosquitto)

# Deployment to Raspberry PI

## PyCharm Remote

Basic idea is to configure PyCharm to use SFTP to upload files from the desktop to the PI; and a project can even be
configured to use ssh to invoke a program on the PI. I set up passwordless ssh.

Go to `Preferences -> Build, Execution, Deployment -> Deployment`; set up a ssh configuration, specify the local and
remote folders and check the box for automatic upload. After that everytime a file changes it is automatically uploaded
and the entire project can be uploaded manually on demand.

After uploading the first time I used `pip3 install -e .` inside the music_player folder where `setup.py` is to install
my code and all the dependencies listed in requirements.txt

I did not set up remote execution, for that I just open terminal window (MAC) and ssh to the PI. I develop and test the
code on the desktop and then upload and run on the PI.

## Making the music_player component run on Raspberry PI.

* Problem with qrcode module needing Python >=3.8 when the PI has only 3.7.x installed. Solution was basically that
  qrcode is not needed in the music_player, it is for making QRCodes and doesn't need to run on the PI, this is
  something that will be run only on the desktop.

* Next problem was that pygame couldn't find libsdl2-mixer-2.0.so.0. Solution to this was simply to install it.
  ```bash
  sudo apt install libsdl2-mixer-2.0
  ```
* The music player had same problem running tasks in paralell that the qr-gateway had, the tasks seemed to be running
  series -- because there was a block on getting results from each function. The comms function failed because the host
  name was missing a hyphen but the log message was not visible. Changing to the no_block version of the function worked
  and the error message was printed out, easy fix to the hostname.
* The music could not play because the file does not exist, none of the ones in the playlist are available. So... it
  didn't play but then after some tens of seconds there this this error

```
ALSA lib pcm.c:8424:(snd_pcm_recover) underrun occurred
```

This error can be solved by increasing the mixer buffer, which in version 2.0.0 has a default of 512

```python
        # Increase the buffer from the default of 512 to eliminate the underrun warning message
pygame.mixer.pre_init(buffer=2048)
```

* File names that have accents on the letters are valid file names on the PI (and on the MAC) but the Path exists()
  function says they don't exist. So, how does Python Pathlib deal with file names that have accents even when in theory
  it is using UTF-8 strings?


* Started with one WAV file that was included the upload and it worked, amazing. Quickly after that switched to putting
  music and the playlist on an external USB drive. The PI mounts these to `/media/pi/<VOLUME_NAME>` provided one of the
  standard file formats is used.

# Use text to speech for logging

Follow the set up instructions
here: [https://www.dexterindustries.com/howto/make-your-raspberry-pi-speak/](https://www.dexterindustries.com/howto/make-your-raspberry-pi-speak/)
This includes a check that sound is set up, which it already is otherwise the music playback would not have worked.

`sudo apt-get install espeak`

The voice sounds robotic, but it is free and doesn't require an internet connection unlike the other Text-to-Speech
tools. But... to run this with Python it is run as an external process.

Try festival

`sudo apt-get install festival`

And a lighter version of Festival

`sudo apt-get install flite`

`flite` with the female voice `slt` sounds best. But it needs to be installed and run via subprocess call on the PI

```python
import subprocess

text = '"Hello world"'
subprocess.call('flite -voice slt ' + text, shell=True)

text = '"You are listening to text to speech synthesis using Festival package from the University of Edinburgh in the UK."'
subprocess.call('flite -voice slt ' + text, shell=True)
filename = 'hello'
file = open(filename, 'w')
file.write(text)
file.close()
subprocess.call('flite -voice slt < ' + filename, shell=True)
```

This will be installed the music-player to voice informational, instructional and warning messages. There will be a
standalone program that takes messages from a topic on MQTT and plays them as text.

# Console Scripts

Add console scripts to `setup.py` to simplify launching Python scripts

```python
    entry_points = {
    'console_scripts': ['music_player=client_player.sub_mqtt_driver:main']
}
```

# Make the MQTT broker run on the Raspberry PI

I just followed the instructions
here [Install Mosquitto Server](https://pimylifeup.com/raspberry-pi-mosquitto-mqtt-server/)

* First step was to update the PI, which was quite involved because my image is from at least a year ago, this took
  minutes and minutes. Mosquitto is easy because it is part of the raspbian repository
  ```bash
  sudo apt update
  sudo apt full-upgrade
  # Install mosquitto and clients
  sudo apt install mosquitto mosquitto-clients
  # Testing
  # Could use the client scripts but I just used the Python application and it worked
  ```
*

# Running the system

Reminder, in my setup I have a Raspberry PI 4 running the Music player and MQTT broker; this connects via a cable to small Bose music player. I also have a Raspberry PI 3 that runs either or both of a web server (the HTTP to MQTT bridge) or the Barcode reader. The two PIs are connected to a network switch which is connected to the nearest satellite of the house WiFi network; the main house router provides IP addresses via DHCP.

I also have the Bose, the two PIs and a network switch connected to power strip, turn them all at once. 

* Music Player Node This has the music player and the mqtt broker. On my system the host is: `music-player.local`. Music is loaded onto USB flash drives plugged into this PI. It looks for play lists when it starts up; the player says where to find the music.
  ** Using Python explicitly
  ```bash
  cd src
  python3 client_player/sub_mqtt_driver.py -l ../conf/logging.config -p /media/pi/9016-4EF8/dylan_playlist.txt
  ```
  ** Or using the console script
  ```bash
  music_player -l ../conf/logging.config -p /media/pi/9016-4EF8/dylan_playlist.txt  
  ```
* QR Gateway Provides the web server interface. On my system the host is: `qrgateway.local`. The URL for the Swagger docs is http://qrgateway.local:8004
  ** Using Python explicitly
  ```bash
  # This uses the defaults for everything. Need to add command-line arguments to this one
  python3 src/main.py 
  ```
  ** Or using console script
  ```bash
  cd proj/qrgateway
  qr_gateway
  ```
  
* Barcode Reader Reads a barcode and publishes a command to the MQTT broker On my system the host is `qrgateway.local`. Yes, the barcode reader is running on the same host as the QR Gateway (the HTTP to MQTT broker).
  ** Using console script 
  ```bash
  cd qrgateway
  barcode
  ```

# Music Player State

I want to keep the music player very simple, tell it to play, pause, unpause, stop, volume. Next and Prev need it to
keep the index of the item that is playing but that is not too big a deal. I want to implement more complex functions,
such as to play a queue of items, in the middleware (between the sensors and the music player, put the state there).
But, the player needs to report events:

* Event when the current item stops (either because it ended or was told to stop)
* And report item that is playing and the current volume setting, maybe a copy of the playlist.


# Windows Media to rip CDs to MP3s
Windows Media is much more flexible than iTunes in its ability to specify the destination for MP3s and the playlists (WPL)
are essentially XML files and are relatively easy to parse with `lmxl`. Windows Media Player offers easier control 
over where the files are ripped to; this they can be ripped directly to a
USB drive, the encoder scheme can be selected. A playlist can be created and uses WPL format although there does seem to
be an option for M3U. Once the RIP settings are chosen. Click Organize menu item to add more library locations such as
the external USB drive then once this exists the RIP settings can be configured to send to the USB drive.)

A ton of tracks can be ripped to the USB drive then playlists can be created and added. The file paths in the playlist
are relative to the playlist location which is really useful. They are Windows paths with backslashes but Pathlib can
handle these easily. A ton of music can be put onto the USB stick and multiple playlists.

See the `musiclib` package for the source.

# Service Discovery

How to find the mqtt broker, all messages flow through this, but how to find it??

Use Bonjour, mDNS (https://www.win.tue.nl/~johanl/educ/IoT-Course/mDNS-SD%20Tutorial.pdf)[https://www.win.tue.nl/~johanl/educ/IoT-Course/mDNS-SD%20Tutorial.pdf]
using the avahi package. This was already installed for me on the RaspberryPI; if it is not there then use the above
tutorial to learn how to install it.

And this shows an example of how to advertise it:
(http://dagrende.blogspot.com/2017/02/find-mqtt-broker-without-hard-coded-ip.html)[http://dagrende.blogspot.com/2017/02/find-mqtt-broker-without-hard-coded-ip.html]

Create `sudo vi /etc/avahi/services/mosquitto.service` and put this in it:

```xml
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
 <name replace-wildcards="yes">Mosquitto MQTT server on %h</name>
  <service>
   <type>_mqtt._tcp</type>
   <port>1883</port>
   <txt-record>info=Use this for pub/sub music related commands</txt-record>
  </service>
</service-group>
```

Almost immediately it shows up in the Bonjour Browser as described in the above link, and also using the avahi utilities:

```bash
pi@qrgateway:~/proj/qrgateway $ avahi-browse -rt _mqtt._tcp
+   eth0 IPv6 Mosquitto MQTT server on music-player         _mqtt._tcp           local
+   eth0 IPv4 Mosquitto MQTT server on music-player         _mqtt._tcp           local
=   eth0 IPv6 Mosquitto MQTT server on music-player         _mqtt._tcp           local
   hostname = [music-player.local]
   address = [fd44:43db:78a1:1:d3cc:19ab:1bf1:1134]
   port = [1883]
   txt = ["info=Use this for pub/sub music related commands"]
=   eth0 IPv4 Mosquitto MQTT server on music-player         _mqtt._tcp           local
   hostname = [music-player.local]
   address = [192.168.1.21]
   port = [1883]
   txt = ["info=Use this for pub/sub music related commands"]
```
And then use python-zeroconf to find it using Python. Zeroconf supports either a synchronous query on demand
or an asynchronous ServiceBrowser that runs a background thread and informs a listener when services matching
a standing query are added, updated or removed (e.g. because they stop)

Look in this package: `src/discovery` and in this module to see examples of both `tests/find_service.py`

# Running the programs on re-boot
* Use crontab to run the python scripts from boot-up
[https://www.tomshardware.com/how-to/run-script-at-boot-raspberry-pi](https://www.tomshardware.com/how-to/run-script-at-boot-raspberry-pi)

For `crontab` need a single command to run the programs, this is the one for the music-server. One of the volume names contains
a space which caused some problems, had to specify quoting style to escape the space and then xargs to pass the list of paths
as separate items to the script; using the usual back tick scheme resulted in python or the shell splitting the problematic
volume name at the space.

The music player was modified to take a list of volumes; for the RaspberryPI the USB sticks all appear under `/media/pi`
and this allows them all to be searched for playlists.

```python
ls -d --quoting-style=escape /media/pi/* | xargs music_player -l /home/pi/proj/music_player/music-server/conf/no-logging.config -v
```



# Road map

* Another problem. For some classical music (Beethoven's 6th Symphony for example) the movements and hence the tracks 
follow onto each other without a gap. But the player is designed to play individual tracks and then stop. Not all
tracks should run into each other, need a scheme to tell the player that a certain list of tracks must run into other
with no break. Or provide a mode command that tells player to stop after a given track or keep going with a configurable
delay.

* A listing of the tracks would be useful, maybe Windows Media can do this.

* The mqtt_comms class uses a function in Paho MQTT called loop_forever() after the initial connection has been made, this automatically
handles re-connection which is great. But what if the host running the broker changes, this will not be picked up until the next
time the program re-starts. Making it automatically change the mqtt broker and port and re-connect will require a major change,
the mqtt connection will need to be triggered by add or updates to the service, a totally different flow.

# Useful links:

* [How to generate and decode QR Codes](https://betterprogramming.pub/how-to-generate-and-decode-qr-codes-in-python-a933bce56fd0)
* [Play music on MAC or Raspberry PI](https://www.pygame.org/ and https://pypi.org/project/pygame/)

# Troubleshooting

* The external storage suddenly disappeared. It was an 8GB I had lying around of unknown vintage, I guess it just
  failed. It showed up when I plugged it into the MAC but it had none of the new stuff on it; was all the old stuff. I
  switched to a brand new 64 GB flash drive and copied MP3s and playlist onto it and it is working fine again; and it
  shows up with the volume label I wrote to it on the MAC which the old one didn't another indication there was
  something wrong with it.
  
