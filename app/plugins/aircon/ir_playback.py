#!/usr/bin/env python
import os
import time
import json
import pigpio

class IR_PLAYBACK(object):
    """
    Class for playback IR remote control codes.
    """
    def __init__(self, pi, gpio, freq=38.0):
        """
        pi (pigpio): an instance of pigpio
        gpio (int): playback gpio pin number
        freq (float): Hz
        """
        self.pi = pi
        self.gpio = gpio
        self.freq = freq
        self.setup()

    def setup(self):
        """
        IR RX connected to gpio.
        Ignores glitches.
        """
        pi = self.pi
        gpio = self.gpio

        pi.set_mode(gpio, pigpio.OUTPUT)
        pi.wave_add_new()

    def playback(self, *, file_name, command):
        """
        Playback.
        """
        pi = self.pi
        gpio = self.gpio

        try:
            with open(file_name, "r") as f:
                records = json.load(f)
        except:
            print("Can't open: {}".format(file_name))
            return

        emit_time = time.time()
        if not command in records.keys():
            print("Id {} not found".format(command))
            return

        code = records[command]
        N = len(code)

        # Create wave
        marks_wid = {}
        spaces_wid = {}
        wave = [0 for i in range(N)]

        for i in range(N):
            ci = code[i]
            if self._is_mark(i): # Mark
                if ci not in marks_wid.keys():
                    wf = self.carrier(gpio, freq, ci)
                    pi.wave_add_generic(wf)
                    marks_wid[ci] = pi.wave_create()
                wave[i] = marks_wid[ci]
            else: # Space
                if ci not in spaces_wid.keys():
                    pi.wave_add_generic([pigpio.pulse(0, 0, ci)])
                    spaces_wid[ci] = pi.wave_create()
                wave[i] = spaces_wid[ci]

        delay = emit_time - time.time()

        if delay > 0.0:
            time.sleep(delay)

        pi.wave_chain(wave)
        while pi.wave_tx_busy():
            time.sleep(0.002)

        self._wave_clear(marks_wid)
        self._wave_clear(spaces_wid)

    def _carrier(self, micros) -> list:
        """
        Returns carrier square wave.
        """
        gpio = self.gpio
        freq = self.freq

        wf = []
        cycle = 1000.0 / freq
        cycles = int(round(micros/cycle))
        on = int(round(cycle / 2.0))
        sofar = 0
        for c in range(cycles):
            target = int(round((c+1)*cycle))
            sofar += on
            off = target - sofar
            sofar += off
            wf.append(pigpio.pulse(1<<gpio, 0, on))
            wf.append(pigpio.pulse(0, 1<<gpio, off))

        return wf

    def _is_mark(self, i: int):
        return i % 2 == 0

    def _wave_clear(self, wid_dict: dict):
        pi = self.pi
        for i in wid_dict.keys():
            pi.wave_delete(wid_dict[i])

if __name__ == '__main__':
    pi = pigpio.pi()
    irp = IR_PLAYBACK(pi, 17)
    irp.playback("codes", "command") # playback recodes[command]
