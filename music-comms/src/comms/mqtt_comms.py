"""
A class to wrap dealing with the MQTT broker
Background reading: http://www.steves-internet-guide.com/into-mqtt-python-client/
Note: if connection is successful but then fails almost immediately on the first subscribe
action with errors that end with "Out of Memory", then check that the client id is unique,
you could easily be running more than instance of the same program using the same client ID.
"""
import logging
import time
from abc import ABC, abstractmethod

import paho.mqtt.client as mqtt


class SensorListener(ABC):
    """
    An interface supported by an object that receives the payload from the messages
    """

    @abstractmethod
    def on_message(self, topic: bytes, payload: bytes):
        pass

    @abstractmethod
    def on_disconnect(self, reason: str):
        pass

    @abstractmethod
    def on_protocol_event(self, reason: str) -> None:
        """
        Notifies the Sensor Listener of connection related events
        :param reason: Human readable and parseable text describing the event
        :return: None
        """
        pass


class MqttComms:
    """
    A class that wraps the MQTT client and is an interface between
    it and a listener that handles the messages
    """
    client: mqtt.Client
    # The name of the host to use to connect to MQTT server
    hostname: str
    # The port number to use to connect to MQTT server
    port: int
    # The topic to subscribe to, messages are received on this topic
    # For topic naming see this: https://www.hivemq.com/blog/mqtt-essentials-part-5-mqtt-topics-best-practices/
    cmd_topic: str
    # All received messages are sent to this listener for handling
    msg_listener: SensorListener
    # This is the quality of service
    #   At most once (0)
    #   At least once (1)
    #   Exactly once (2).
    qos: int  # The desired quality of service
    # Stop running if this flag becomes false
    running: bool

    def __init__(self,
                 client_id: str,
                 cert_path: str,
                 username: str,
                 password: str,
                 hostname: str,
                 port: int,
                 cmd_topic: str,
                 msg_listener: SensorListener = None):
        if msg_listener is None:
            raise ValueError("Need to supply a SensorListener")
        self.running = True
        self.cmd_topic = cmd_topic
        # Clean session = don't want persistence
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311, clean_session=True)
        # Connect the client's callback functions to the methods in this class
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log
        self.client.on_subscribe = self.on_subscribe
        # See if leaving this as is will improve the re-connection
        self.client.on_disconnect = self.on_disconnect
        if username is not None:
            self.client.username_pw_set(username=username, password=password)
        if cert_path is not None:
            self.client.tls_set(ca_certs=cert_path)
        self.hostname = hostname
        self.port = port
        self.msg_listener = msg_listener
        self.logger = logging.getLogger("comms.mqtt")
        self.qos = 1  # At least once

    def connect_and_run(self, keep_alive_seconds: int) -> None:
        """
        Connect once and then call the client loop_forever() function which will
        handle everything, even re-connecting automatically. The downside of the
        automatic connection is that it won't use zeroconf to look up the
        mqtt broker host and port if this has changed. Need to stop and destroy this
        instance of mqtt_comms and start a new one if there is an update to the mqtt host and
        port.
        :param keep_alive_seconds: Number of seconds of silence before a keep-alive message
        is setn
        :return: None
        """
        self.logger.info("Start the connection attempt to %s:%d", self.hostname, self.port)
        # Loop until initial connection is made and while the running flag is still true
        retry_period_seconds = 5
        while self.running:
            try:
                self.client.connect(host=self.hostname, port=self.port, keepalive=keep_alive_seconds)
                self.logger.info("Successful Connection to %s:%d", self.hostname, self.port)
                break
            except ConnectionRefusedError:
                self.logger.warning("Connection refused, try again in %d seconds", retry_period_seconds)
                time.sleep(retry_period_seconds)
            except OSError as e:
                self.logger.warning("OSError connecting to %s:%d %s, try again in %d seconds",
                                    self.hostname,
                                    self.port,
                                    str(e),
                                    retry_period_seconds)
                time.sleep(retry_period_seconds)
            except Exception as e:
                self.logger.error("Unexpected exception connecting, just exit %s, %s", type(e), str(e))
                return
        if not self.running:
            self.logger.warning("Running flag is not set, abort")
            return

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting. Which is great, if it disconnects the re-connection is automatic.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        try:
            self.logger.info("Start the communications loop, will run until stopped")
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.client.loop_stop(force=True)
            self.client.disconnect()
        except Exception as e:
            self.logger.warning(f"Some problem {str(e)})")
            self.client.loop_stop(force=True)
            self.client.disconnect()

    def connection_stop(self):
        self.running = False
        self.client.disconnect()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Connected with result code " + str(rc) + " " + mqtt.connack_string(rc))
        if rc == 0:
            # If a cmd_topic was supplied in the constructor then subscribe
            if self.cmd_topic is not None:
                res = client.subscribe(self.cmd_topic, qos=self.qos)
                if res[0] != mqtt.MQTT_ERR_SUCCESS:
                    raise RuntimeError(f"Subscribe failed, the client is not really connected {res[0]}")
                msg = f"Subscribed to messages for all devices {self.cmd_topic} returned mid {res[1]}"
                self.logger.info(msg)
                self.msg_listener.on_protocol_event(msg)
        else:
            msg = f"Connection failed {str(rc)} {mqtt.connack_string(rc)}"
            self.msg_listener.on_protocol_event(msg)
            raise RuntimeError(msg)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        '''
        Callback for the subscribe call
        :param client:
        :param userdata:
        :param mid: Message id that was returned in the subscribe call
        :param granted_qos: The QOS that was granted to the subscriber
        :return: None
        '''
        self.logger.info(f"Subscribed mid {mid} Granted QOS {granted_qos}")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        if self.msg_listener is not None:
            self.msg_listener.on_message(msg.topic, msg.payload)

    # The callback for when a disconnect message is received regarding the mqtt connection.
    def on_disconnect(self, client, userdata, rc):
        msg = f"Disconnected status err code {rc} - {mqtt.error_string(rc)}"
        self.logger.warning(msg)
        if self.msg_listener is not None:
            msg = mqtt.error_string(rc)
            self.msg_listener.on_disconnect(mqtt.error_string(rc))
            self.msg_listener.on_protocol_event(msg)

    def on_log(self, client, userdata, level, buf):
        """
        Log all MQTT protocol events, and the exceptions in callbacks
        that have been caught by Paho.
        """
        logging_level = mqtt.LOGGING_LEVEL[level]
        logging.log(logging_level, buf)
        # Don't report these protocol events to the msg_listener
        # they are only confusing
        # self.msg_listener.on_protocol_event(buf)

    def publish(self, topic: str, payload=None, qos=0, retain=False):
        rc: mqtt.MQTTMessageInfo = self.client.publish(topic, payload, qos, retain)
        self.logger.info("Message published to topic %s payload %s", topic, payload)
        error_code = rc.rc
        if error_code == mqtt.MQTT_ERR_SUCCESS:
            self.logger.info("Message published or queued for publishing")
        elif error_code == mqtt.MQTT_ERR_NO_CONN:
            self.logger.error("Not connected, message discarded")
        elif error_code == mqtt.MQTT_ERR_CONN_REFUSED:
            self.logger.error("Connection refused, message discarded")
        elif error_code == mqtt.MQTT_ERR_CONN_LOST:
            self.logger.error("Connection refused, message discarded")
        else:
            self.logger.error("Publish unexpected %d %s", error_code, mqtt.error_string(error_code))
