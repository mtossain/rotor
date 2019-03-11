import time
import sys,os
import curses
import datetime
import math
import json
from dateutil.parser import *
import urllib.request

def check_wind():

    try:
        try:
            f = urllib.request.urlopen('http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/Ijsselstein.json')
        except:
            print('[NOK] Could not open website')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        Wind = int(float(parsed_json['current_observation']['wind_kph']))
        WindGust = int(float(parsed_json['current_observation']['wind_gust_kph']))
        WindDir = parsed_json['current_observation']['wind_dir']
        WindDirAngle = int(float(parsed_json['current_observation']['wind_degrees']))
    except:
        print('[NOK] Wunderground not found...')
        WindGust=0
    return WindGust

print('Read wind speed: '+str(check_wind()))
