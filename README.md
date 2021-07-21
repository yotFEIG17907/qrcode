# Overview

ActiveMQ broker runs somewhere, possibly on the RaspberryPI. A script subscribes to a topic
providing messages that tell it what to do. There will be a different topic for each kind
of control message. Messages are published to this topic from a variety of sources:
* A web server application that publishes messages based on invocation of its REST API methods.
  An IPhone scans a QR Code that contains a URL with one of the REST API calls and publishes a
  corresponding message to the AMQ Broker.
* A stand-alone script on a Pi-Zero with a RFID reader publishes a message containing selected parts
  of the data in the RFID token. Like a "wand".
  
The MQTT messages do things like:
* Start playing a playlist item, the item index provided in the message. The message has an index
  into the current play list. The file paths in the playlist are absolute or relative. Relative
  paths will be relative to the folder that the playlist itself was found in. Some questions:
  1. Is the new index played after the current one finishes or does it cause the current one
  to terminate immediately? I like the idea of adding the index to a list of items to play that
     is managed by the music player.
* Stop playing the current playlist item
* Pause/Resume the current playlist item
* Reset

All the messages are JSON and follow the same format, which is TBD

# Packages

## client_player

This subscribes to the topic and executes actions specified in the messages, e.g. to play an MP3.
It needs to:
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
remote folders and check the box for automatic upload. After that everytime a file changes it is automatically
uploaded and the entire project can be uploaded manually on demand.

After uploading the first time I used `pip3 install -e .` inside the music_player folder where `setup.py` is to
install my code and all the dependencies listed in requirements.txt

I did not set up remote execution, for that I just open terminal window (MAC) and ssh to the PI. I develop and test
the code on the desktop and then upload and run on the PI.

## Making the music_player component run on Raspberry PI. 

* Problem with qrcode module needing Python >=3.8 when the PI has only 3.7.x installed. Solution
was basically that qrcode is not needed in the music_player, it is for making QRCodes and doesn't need
to run on the PI, this is something that will be run only on the desktop.
  
* Next problem was that pygame couldn't find libsdl2-mixer-2.0.so.0. Solution to this was simply to
install it.
  ```bash
  sudo apt install libsdl2-mixer-2.0
  ```
* The music player had same problem running tasks in paralell that the qr-gateway had, the tasks seemed to be running series -- because
there was a block on getting results from each function. The comms function failed because the host name was missing a hyphen but
the log message was not visible. Changing to the no_block version of the function worked and the error message was printed out,
easy fix to the hostname.
* The music could not play because the file does not exist, none of the ones in the playlist are available. So... it didn't
play but then after some tens of seconds there this this error
```
ALSA lib pcm.c:8424:(snd_pcm_recover) underrun occurred
```
This error can be solved by increasing the mixer buffer, which in version 2.0.0 has a default of 512
```python
        # Increase the buffer from the default of 512 to eliminate the underrun warning message
        pygame.mixer.pre_init(buffer=2048)
```
* File names that have accents on the letters are valid file names on the PI (and on the MAC) but
the Path exists() function says they don't exist. So, how does Python Pathlib deal with file names that have accents
  even when in theory it is using UTF-8 strings?
  

* Started with one WAV file that was included the upload and it worked, amazing. Quickly after that switched
to putting music and the playlist on an external USB drive. The PI mounts these to `/media/pi/<VOLUME_NAME>` provided
one of the standard file formats is used.
  
# Use text to speech for logging
Follow the set up instructions here: [https://www.dexterindustries.com/howto/make-your-raspberry-pi-speak/](https://www.dexterindustries.com/howto/make-your-raspberry-pi-speak/)
This includes a check that sound is set up, which it already is otherwise the music playback would not have worked.

`sudo apt-get install espeak`

The voice sounds robotic, but it is free and doesn't require an internet connection unlike the other Text-to-Speech tools.
But... to run this with Python it is run as an external process.

Try festival

`sudo apt-get install festival`

And a lighter version of Festival

`sudo apt-get install flite`

`flite` with the female voice `slt` sounds best. But it needs to be installed and run via subprocess call on the PI

```python
import subprocess
text = '"Hello world"'
subprocess.call('flite -voice slt '+text, shell=True)

text = '"You are listening to text to speech synthesis using Festival package from the University of Edinburgh in the UK."'
subprocess.call('flite -voice slt '+text, shell=True)
filename = 'hello'
file=open(filename,'w')
file.write(text)
file.close()
subprocess.call('flite -voice slt < '+filename, shell=True)
```

This will be installed the music-player to voice informational, instructional and warning messages. There will
be a standalone program that takes messages from a topic on MQTT and plays them as text.

# Console Scripts

Add console scripts to `setup.py` to simplify launching Python scripts
```python
    entry_points = {
        'console_scripts': ['music_player=client_player.sub_mqtt_driver:main']
    }
```

# Make the MQTT broker run on the Raspberry PI

I just followed the instructions here [Install Mosquitto Server](https://pimylifeup.com/raspberry-pi-mosquitto-mqtt-server/)

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

* Music Player Node
 ** This has the music player and the mqtt broker.
  ```bash
  cd src
  python3 client_player/sub_mqtt_driver.py -l ../conf/logging.config -p /media/pi/9016-4EF8/dylan_playlist.txt
  ```

* Qr Gateway
  ** Provides the web server interface
  ```bash
  # This uses the defaults for everything. Need to add command-line arguments to this one
  python3 src/main.py 
  ```
# Useful links:
* [How to generate and decode QR Codes](https://betterprogramming.pub/how-to-generate-and-decode-qr-codes-in-python-a933bce56fd0)
* [Play music on MAC or Raspberry PI](https://www.pygame.org/ and https://pypi.org/project/pygame/)



