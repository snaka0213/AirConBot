#!/usr/bin/env python3
import time
import functools
from ir_playback import IR_PLAYBACK

class RemoteForApp(object):
    def __init__(self, *, pi, gpio, code_file):
        """
        pi (pigpio): an instance of pigpio
        gpio (int): gpio pin number
        """
        self.pi = pi
        self.gpio = gpio
        self.code_file = code_file
        self.mode = None
        self.temp = None
        self._playback = None
        self.setup()

    def setup(self):
        self.mode = "PowerOff"
        irp = IR_PLAYBACK(self.pi, self.gpio)
        self._playback = functools.partial(irp.playback, file_name=self.code_file)

    def PowerOn(self, mode: str, temp=None):
        self.mode = mode
        self.temp = temp

        if isinstance(temp, int):
            self._playback(command=mode+str(temp))
        elif temp is None:
            self._playback(command=mode)
        else:
            print("TypeError: var temp must be int or None")

    def PowerOff(self):
        self.mode = "off"
        self._playback(command="off")

    def SetDirection(self):
        self._playback(command="wind")

    def SetTemp(self, temp: int):
        self._playback(command="{}{}".format(self.mode, temp))

    def SetTimer(self, time_m: int):
        self._playback(command="{}m".format(time_m))
