#!/usr/bin/env python3
import time
from dht11 import DHT11

class RemoteForMeter(object):
    def __init__(self, *, pi, gpio):
        """
        pi (pigpio): an instance of pigpio
        gpio (int): gpio pin number
        """
        self.pi = pi
        self.gpio = gpio
        self.sensor = None
        self.setup()

    def setup(self):
        self.sensor = DHT11(self.pi, self.gpio)

    def read(self) -> dict:
        sensor = self.sensor

        sensor.read()
        response =  {
            'humidity': sensor.humidity,
            'temperature': sensor.temperature
        }
        sensor.close()
        return response
