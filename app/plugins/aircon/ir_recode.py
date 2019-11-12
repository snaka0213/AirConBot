#!/usr/bin/env python
import os
import json
import pigpio

GLITCH     = 100
PRE_MS     = 200
POST_MS    = 130
SHORT      = 10
TOLERANCE  = 15

POST_US    = POST_MS * 1000
PRE_US     = PRE_MS  * 1000
TOLER_MIN =  (100 - TOLERANCE) / 100.0
TOLER_MAX =  (100 + TOLERANCE) / 100.0

class IR_RECORD(object):
    """
    Class for record IR remote control codes.
    """
    def __init__(self, pi, gpio, freq=38.0):
        """
        pi (pigpio): an instance of pigpio
        gpio (int): record gpio pin number
        freq (float): Hz
        """
        self.pi = pi
        self.gpio = gpio
        self.freq = freq
        self.last_tick = 0
        self.in_code = False
        self.either_edge_cb = None
        self.code = []
        self.setup()

    def backup(self, file_name):
        """
        file_name -> file_name.bak -> file_name.bak1 -> file_name.bak2
        """
        f = os.path.realpath(file_name)
        try:
            os.rename(f+".bak1", f+".bak2")
        except:
            pass
        try:
            os.rename(f+".bak", f+".bak1")
        except:
            pass
        try:
            os.rename(f, f+".bak")
        except:
            pass

    def setup(self):
        """
        IR RX connected to gpio.
        Ignores glitches.
        """
        gpio = self.gpio

        self.pi.set_mode(gpio, pigpio.INPUT)
        self.pi.set_glitch_filter(gpio, GLITCH)

    def record(self, file_name, *commands):
        """
        Records.
        """
        pi = self.pi
        gpio = self.gpio

        try: # Overwrite
            with open(file_name, "r") as f:
                records = json.load(f)
        except: # New file
            records = {}

        # Process
        print("Recording")
        for command in commands:
            print("Press key for '{}'".format(command))
            self.register_callback()
            print("Okay")
            records[command] = self.code
            self.code = []

        self.close()
        self.tidy(records)
        self.backup(file_name)

        with open(file_name, "w") as f:
            f.write(json.dumps(records, sort_keys=True).replace("],", "],\n")+"\n")

    def register_callback(self):
        """
        Monitors RISING_EDGE changes using callback.
        """
        self.either_edge_cb = self.pi.callback(
            self.gpio,
            pigpio.EITHER_EDGE,
            self._callback
        )

    def _callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        """
        level_handlers = {
            pigpio.FALLING_EDGE: self._edge_INCODE,
            pigpio.RISING_EDGE : self._edge_INCODE,
            pigpio.EITHER_EDGE : self._edge_EITHER
        }
        handler = level_handlers[level]
        diff = pigpio.tickDiff(self.last_tick, tick)
        handler(tick, diff)

    def _edge_INCODE(self, tick, diff):
        self.last_tick = tick
        in_code = self.in_code

        if (diff > PRE_US) and (not in_code): # Start of a code.
            self.in_code = True
            self.pi.set_watchdog(gpio, POST_MS) # Start watchdog.

        elif (diff > POST_US) and in_code: # End of a code.
            self.in_code = False
            self.pi.set_watchdog(gpio, 0) # Cancel watchdog.
            self._end_of_code()

        elif in_code:
            self.code.append(diff)

    def _edge_EITHER(self, tick, diff):
        self.pi.set_watchdog(gpio, 0) # Cancel watchdog.
        if self.in_code:
            self.in_code = False
            self._end_of_code()

    def _end_of_code():
        if len(self.code) > SHORT:
            self._normalize()
            self.close()
        else:
            self.code = []
            print("Short code, probably a repeat, try again")

    def _normalize(self):
        """
        Typically a code will be made up of two or three distinct
        marks (carrier) and spaces (no carrier) of different lengths.

        Because of transmission and reception errors those pulses
        which should all be x micros long will have a variance around x.

        This function identifies the distinct pulses and takes the
        average of the lengths making up each distinct pulse.  Marks
        and spaces are processed separately.

        This makes the eventual generation of waves much more efficient.

        Input

        M    S   M   S   M   S   M    S   M    S   M
        9000 4500 600 540 620 560 590 1660 620 1690 615

        Distinct marks

        9000                average 9000
        600 620 590 620 615 average  609

        Distinct spaces

        4500                average 4500
        540 560             average  550
        1660 1690           average 1675

        Output

        M    S   M   S   M   S   M    S   M    S   M
        9000 4500 609 550 609 550 609 1675 609 1675 609
        """
        entries = len(self.code)
        p = [0 for i in range(entries)] # Set all entries not processed.
        for i in range(entries):
            if not p[i]: # Not processed?
                v_i = self.code[i]
                tot = v_i
                similar = 1.0

                # Find all pulses with similar lengths to the start pulse.
                for j in range(i+2, entries, 2):
                    v_j = self.code[j]
                    if not p[j]: # Unprocessed.
                        if (v_j*TOLER_MIN) < v_i < (v_j*TOLER_MAX): # Similar.
                            tot = tot + v_j
                            similar += 1.0

                # Calculate the average pulse length.
                newv = round(tot / similar, 2)
                self.code[i] = newv

                # Set all similar pulses to the average value.
                for j in range(i+2, entries, 2):
                    v_j = self.code[j]
                    if not p[j]: # Unprocessed.
                        if (v_j*TOLER_MIN) < v_i < (v_j*TOLER_MAX): # Similar.
                            self.code[j] = newv
                            p[j] = 1

    def close(self):
        """
        Stop recording, remove callbacks.
        """
        pi = self.pi
        gpio = self.gpio

        pi.set_glitch_filter(gpio, 0) # Cancel glitch filter.
        pi.set_watchdog(gpio, 0) # Cancel watchdog.

        if self.either_edge_cb is not None:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None

    def tidy(self, records):
        self._tidy_ms(records, 0) # Marks.
        self._tidy_ms(records, 1) # Spaces.

    def _tidy_ms(self, records, base):
        ms = {}
        # Find all the unique marks (base=0) or spaces (base=1)
        # and count the number of times they appear.
        for rec in records.keys():
            rl = len(records[rec])
            for i in range(base, rl, 2):
                if records[rec][i] in ms:
                    ms[records[rec][i]] += 1
                else:
                    ms[records[rec][i]] = 1

        v = None
        for plen in sorted(ms):
            # Now go through in order, shortest first, and collapse
            # pulses which are the same within a tolerance to the
            # same value.  The value is the weighted average of the
            # occurences.
            #
            # E.g. 500x20 550x30 600x30  1000x10 1100x10  1700x5 1750x5
            #
            # becomes 556(x80) 1050(x20) 1725(x10)
            if v == None:
                e = [plen]
                v = plen
                tot = plen * ms[plen]
                similar = ms[plen]
            elif plen < (v*TOLER_MAX):
                e.append(plen)
                tot += (plen * ms[plen])
                similar += ms[plen]

            else:
                v = int(round(tot/float(similar)))
                # set all previous to v
                for i in e:
                    ms[i] = v
                e = [plen]
                v = plen
                tot = plen * ms[plen]
                similar = ms[plen]

        v = int(round(tot/float(similar)))
        # set all previous to v
        for i in e:
            ms[i] = v

        for rec in records.keys():
            rl = len(records[rec])
            for i in range(base, rl, 2):
                records[rec][i] = ms[records[rec][i]]

if __name__ == '__main__':
    pi = pigpio.pi()
    irr = IR_RECORD(pi, 18)
    irr.record("codes", "command") # record {command: int_list}
