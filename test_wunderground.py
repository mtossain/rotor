import time
import sys,os
import curses
import datetime
import math
import urllib2
import json
from dateutil.parser import *

def check_wind():

    try:
        f = urllib2.urlopen('http://http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/Ijsselstein.json')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        station_time = parse(parsed_json['current_observation']['observation_time_rfc822']).replace(tzinfo=None)
        now = dt.datetime.now()
        seconds = (now-station_time).total_seconds()
        if seconds > 10*60:
            print('ERROR: Wunderground is not updated since: '+str(int(seconds/60))+'min [NOK]')
        Wind = int(float(parsed_json['current_observation']['wind_kph']))
        WindGust = int(float(parsed_json['current_observation']['wind_gust_kph']))
        WindDir = parsed_json['current_observation']['wind_dir']
        WindDirAngle = int(float(parsed_json['current_observation']['wind_degrees']))
    except:
        print('[NOK] Wunderground not found...')
        WindGust=0
    return WindGust

print('Read wind speed: '+str(check_wind()))
