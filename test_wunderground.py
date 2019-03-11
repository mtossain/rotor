import time
import sys,os
import curses
import datetime
import math
import json
from dateutil.parser import *
import urllib2

def check_wind():

    try:
        try:
            f = urllib2.urlopen('http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/Ijsselstein.json')
        except:
            print('[NOK] Could not open website')
        try:
            json_string = f.read()
            #print(json_string)
            parsed_json = json.loads(json_string)
            print(parsed_json)
        except:
            print('[NOK] Could not parse wunderground json')
        try:
            Wind = int(float(parsed_json['current_observation']['wind_kph']))
            WindGust = int(float(parsed_json['current_observation']['wind_gust_kph']))
            WindDir = parsed_json['current_observation']['wind_dir']
            WindDirAngle = int(float(parsed_json['current_observation']['wind_degrees']))
        except:
            print('[NOK] Could not convert wunderground data')
    except:
        print('[NOK] Wunderground not found...')
        WindGust=0
    return WindGust

print('Read wind speed: '+str(check_wind()))
