#!/usr/bin/env python3
import re
import pigpio
import slackbot_settings
from slackbot.bot import respond_to, listen_to
from aircon.aircon_remote import RemoteForApp as RFA

pi = pigpio.pi()
rfa = RFA(pi, slackbot_settings.GPIO_IR, slackbot_settings.CODE_FILE)
app_name = "エアコン"

@listen_to(r'{}.*(つけて|点けて|入れて)'.format(app_name))
def PowerOnApp(message, *args):
    rfa.PowerOn()
    message.reply("{}をつけました".format(app_name))

@listen_to(r'{}.*(きって|切って|消して)'.format(app_name))
def PowerOffApp(message, *args):
    rfa.PowerOff()
    message.reply("{}の電源を切りました".format(app_name))

@listen_to(r'(自動|オート)にして'.format(app_name))
def PowerOnAuto(message, *args):
    mode = args[0]
    rfa.PowerOn("auto")
    message.reply("{}[{}]をつけました".format(app_name, mode))

@listen_to(r'(除湿|ドライ).*?(\d+)')
def PowerOnDry(message, *args):
    mode = args[0]
    temp = int(args[1])
    rfa.PowerOn("dry", temp)
    message.reply("{}[{}: {}度]をつけました".format(app_name, mode, temp))

@listen_to(r'(冷房|クーラー).*?(\d+)')
def PowerOnCooler(message, *args):
    mode = args[0]
    temp = int(args[1])
    rfa.PowerOn("cool", temp)
    message.reply("{}[{}: {}度]をつけました".format(app_name, mode, temp))

@listen_to(r'(暖房|ヒーター).*?(\d+)')
def PowerOnHeater(message, *args):
    mode = args[0]
    temp = int(args[1])
    rfa.PowerOn("heat", temp)
    message.reply("{}[{}: {}度]をつけました".format(app_name, mode, temp))

@listen_to(r'(むき|向き).*?(かえて|変えて|変更)')
def SetDirection(message, *args):
    rfa.SetDirection()
    message.reply("{}の風向きを変えました".format(app_name))

@listen_to(r'(\d+).*?(かえて|変えて|変更)')
def SetTemp(message, *args):
    temp = int(args[0])
    rfa.SetTemp(temp)
    message.reply("{}の設定温度を{}度に変更しました".format(app_name, temp))

@listen_to(r'タイマー.*?(\d+)分')
def SetTimer(message, *args):
    time_m = int(args[0])
    rfa.SetTimer(time_m)
    message.reply("{}のタイマー[{}分]をセットしました".format(app_name, timer))
