#!/usr/bin/env python3
import re
import pigpio
import slackbot_settings
from slackbot.bot import respond_to, listen_to
from meter.meter_remote import RemoteForMeter as RFM

pi = pigpio.pi()
rfm = RFM(pi, slackbot_settings.GPIO_TH)

@listen_to(r'(温度|湿度).*?(おしえて|教えて|何度)')
def TempAndHumid(message, *args):
    response = RFM().read()
    humid = response.get("humidity")
    temp  = response.get("temperature")
    message.reply("現在の温度は{}度，湿度は{}%です".format(temp, humid))
