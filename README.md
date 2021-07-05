# Overview

ActiveMQ broker runs somewhere, possibly on the RaspberryPI. A script subscribes to a topic
providing messages that tell it what to do. There will be a different topic for each kind
of control message. Messages are published to this topic from a variety of sources:
* A web server application that publishes messages based on invocation of its REST API methods.
  An IPhone scans a QR Code that contains a URL with one of the REST API calls and publishes a
  corresponding message to the AMQ Broker.
* A stand-alone script on a Pi-Zero with a RFID reader publishes a message containing selected parts
  of the data in the RFID token. Like a "wand".
  
The AMQ messages do things like:
* Start playing a playlist item, the item index provided in the message. Does the message contain
  an index or does it name a item, e.g. a mp3 file? In the first instance, the message just has
  an index; what this does is determined by the receiver.
* Stop playing the current playlist item
* Pause/Resume the current playlist item
* Reset

All the messages are JSON and follow the same format, which is TBD

# Packages
## amq_client_player

This subscribes to the AMQ topic executes actions specified in the messages, e.g. to play an MP3.
It needs to:
* Connect to an AMQ broker
* Read in a playlist that maps an index to the path to an Audio file
* Execute the actions specified in the messages
* Connect and re-connect to the broker

Configuration
* The host and port of the AMQ broker
* The topic to subscribe to
* The playlist that maps index to Audio file

## HTTP to AMQ Bridge
This is a web server application. The main endpoint for this application does this:
* Connects and re-connects to an AMQ broker
* Receives a request that has a topic + data, e.g. an integer which is the playlist index
* It packs the data into a JSON message and publishes to the specified topic

Configuration:
* The IP and port to listen on
* The host and port of the AMQ broker
* The topic to publish to

## Useful links:
* (https://betterprogramming.pub/how-to-generate-and-decode-qr-codes-in-python-a933bce56fd0)[How to generate and decode QR Codes]
* Play music on MAC or Raspberry PI https://www.pygame.org/ and https://pypi.org/project/pygame/



