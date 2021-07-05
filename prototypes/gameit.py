import time

"""
Experiment, play a wav file via Python
"""
import pygame

musicfile = '08 Brain Damage 1.wav'
pygame.mixer.init()
pygame.mixer.music.load(musicfile)
pygame.mixer.music.set_volume(1.0)

print("Loaded and playing, hear anything?")
pygame.mixer.music.play()
time.sleep(10.0)
print("Change volume")
pygame.mixer.music.set_volume(0.5)
time.sleep(10.0)
print("Change volume")
pygame.mixer.music.set_volume(1.0)
time.sleep(10.0)
pygame.mixer.music.stop()
#while pygame.mixer.music.get_busy() == True:
#    pass
