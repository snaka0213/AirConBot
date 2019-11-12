#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from os.path import join, dirname

# for make path to .env file
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

### SlackBot ###
API_TOKEN = os.environ.get('API_TOKEN')
DEFAULT_REPLY = "Hello"
PLUGINS = ['plugins']

### AirCon ###
GPIO_IR = 17
GPIO_TH = 18
CODE_FILE = "aircon/codes"
