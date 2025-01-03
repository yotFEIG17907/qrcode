import time
from pathlib import Path
from typing import Any

from comms import run_tasks_in_parallel_no_block
from comms.mqtt_comms import SensorListener, MqttComms
from discovery import get_service_host_port_block
from led_messages.led_commands import SetPixels
from led_utls.nm_to_rgb import wavelength_range, wavelength_to_rgb
from messages.serdeser import cmd_to_json

"""
This uses librosa library to generate and display a MEL Spectrogram.
The spectrogram publishes messages to MQTT for ultimate display to 
an LED strand
Takes audio input from the microphone.
"""

import librosa
import numpy as np
import pyaudio

rate = 22050
chunk_size = rate // 4

lavalier_mike_index = 2

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=lavalier_mike_index,
                frames_per_buffer=chunk_size)

frames = []

do_melspec = librosa.feature.melspectrogram
pwr_to_db = librosa.core.power_to_db

red_nm, blue_nm = wavelength_range()
max_db = 60
scalar_db_to_nm = (blue_nm - red_nm) / max_db


class DummyListener(SensorListener):
    def __init__(self):
        pass

    def on_disconnect(self, reason: str):
        pass

    def on_protocol_event(self, reason: str) -> None:
        pass

    def on_message(self, topic: str, payload: bytes):
        pass

class TestCommsRunner:
    # The gateway to the MQTT server
    comms: MqttComms

    def __init__(self,
                 client_id: str,
                 cert_path: Path,
                 username: str,
                 password: str,
                 hostname: str,
                 port: int,
                 cmd_topic: str,
                 msg_listener: SensorListener):
        self.comms = MqttComms(client_id=client_id,
                               cert_path=cert_path,
                               username=username,
                               password=password,
                               hostname=hostname,
                               port=port,
                               cmd_topic=cmd_topic,
                               msg_listener=msg_listener)

    def run(self, keep_alive_seconds: int) -> None:
        """
        This method will block until error
        :param keep_alive_seconds: Ping will be set after this many seconds to keep
        the connection open
        :return: Nothing
        """
        self.comms.connect_and_run(keep_alive_seconds=keep_alive_seconds)

    def publish(self, pub_topic: str, cmd: Any):
        msg = cmd_to_json(cmd)
        self.comms.publish(topic=pub_topic, payload=msg, qos=2)

    def shutdown(self):
        self.comms.connection_stop()



test_listener = DummyListener()
client_id = f"jimmy-{int(time.time())}"
cert_path = None
username = None
password = None
driver_control_topic = "test-driver/led"
# look MQTT broker up using Bonjour / Zeroconf
type = "_mqtt._tcp.local."
name = "DYLAN MQTT Server"
hostname, port = get_service_host_port_block(type=type, name=name, logger=None)
keep_alive_seconds = 20
cmd_topic = "kontrol/led"
comms = TestCommsRunner(client_id=client_id,
                          cert_path=cert_path,
                          username=username,
                          password=password,
                          hostname=hostname,
                          port=port,
                          cmd_topic=driver_control_topic,
                          msg_listener=test_listener)

# Run these tasks in parallel, the communication task.
# Add the shutdown task if you want the whole program to exit after some delay
# Note: in this version the shutdown is not provided so the program will keep going
# for ever or until stopped by some other means
run_tasks_in_parallel_no_block([
    lambda: comms.run(keep_alive_seconds=keep_alive_seconds)])

while True:
    start = time.time()

    data = stream.read(chunk_size, exception_on_overflow=False)
    data = np.frombuffer(data, dtype=np.float32)

    # Map into 100 bins so it can eventually be displayed on the 100 LED strand.
    # melspec = do_melspec(y=data, sr=rate, n_mels=128, fmax=8000)
    melspec = do_melspec(y=data, sr=rate, n_mels=100, fmax=8000)
    db_melspec = pwr_to_db(melspec, ref=np.max)
    norm_melspec = (db_melspec * scalar_db_to_nm) + blue_nm

    for slice in norm_melspec:
        values = []
        for mel in slice:
            values.append(wavelength_to_rgb(mel))
        cmd = SetPixels(payload=values)
        comms.publish(cmd_topic, cmd)

    t = time.time() - start

    print(1 / t)
