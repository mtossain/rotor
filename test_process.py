from multiprocessing import Process, Manager
import time
import sys,os
import curses
import datetime
import math
import json
from dateutil.parser import *
import urllib2

#from motor_control import * # PWM was tested but failed completely
from motor_control_nopwm import *
from astronomical import *
from read_heading import *

az_active = False # Azimuth motors activated?
az_sense_active = False # Azimuth sensors activated?
az_tracking_band = 2 # Tracking band in [deg]
el_active = True # Elevation motors activated?
el_sense_active = True # Elevation sensors activated?
el_tracking_band = 0.3 # Tracking band in [deg]
wind_check = True # Checking wind gust


class Config:

   rotor_lat = 52.04058 # deg N
   rotor_lon = 5.03625 # deg E
   rotor_alt = 4 # m

   bias_az = -32.0 # deg
   bias_el = 58.9 # deg

   mask = [15,15,15,15] # sectorials from 0 to 360 in deg

   goto_az = 0 # deg from 0 to 360
   goto_el = 90 # deg from 0 (hor) to 90 (zenith)

   goto_ra = 5.5 # hours decimal
   goto_dec = 22.0 # deg decimal

   track_planet = 'Sun' # planet in capital or small
   track_sat_tle = 'tle.txt' # file with TLE elements, first one taken

   max_wind_gust = 6 # When wind gust exceed point to zenith

class State:

   az_req = 10 # deg
   el_req = 50 # deg

   az_rep = 185 # deg
   el_rep = 85 # deg

   az_stat = 'r'
   el_stat = 'f'

   az_false_reading = False
   el_false_reading = False

   motor_az_pins = [0,0]
   motor_el_pins = [0,0]

   above_mask = True # Whether pointing target is above or below the set mask
   manual_mode = True # Whether a manual mode or tracking mode command is given

   wind_gust = 0 #kph
   wind_gust_flag = False # Whether there is too much wind

def read_az(d):
    while (1):
        false_reading,angle = read_az_ang()
        d['az_false_reading'] = True
        if not false_reading:
            d['az_false_reading'] = False
            d['az_rep'] = round((convert_az_reading(angle) - d['bias_az'])%360,2)
        time.sleep(.5)

def read_el(d):
    while (1):
        false_reading,angle = read_el_ang()
        d['el_false_reading']=True
        if not false_reading:
            d['el_false_reading'] = False
            d['el_rep'] = round(angle - d['bias_el'],2)
        time.sleep(.5)

def check_wind(d):
    while(1):
        try:
            f = urllib2.urlopen('http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/Ijsselstein.json')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            Wind = int(float(parsed_json['current_observation']['wind_kph']))
            WindGust = int(float(parsed_json['current_observation']['wind_gust_kph']))
            WindDir = parsed_json['current_observation']['wind_dir']
            WindDirAngle = int(float(parsed_json['current_observation']['wind_degrees']))
        except:
            print('Could not use WU, tried OWM')
            f = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=Ijsselstein&APPID=37c36ad4b5df0e23f93e8cff206e5a2c')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            Wind = int(float(parsed_json['wind']['speed']))
            WindGust = 99
            WindDir = 99
            WindDirAngle = int(float(parsed_json['wind']['deg']))

        d['Wind']=Wind
        d['WindGust']=WindGust
        d['WindDirAngle']=WindDirAngle

        time.sleep(1)

if __name__ == '__main__':
    manager = Manager() # share the dictionaries by a manager

    k=0 # Keypress numeric value
    conf = Config() # Get the configuration of the tool
    state = State() # Get the initial state of the rotor

    d = manager.dict() # all the shared dictnaries between processes

    d['bias_az'] = conf.bias_az # Need to initialize here to use it in main
    d['bias_el'] = conf.bias_el
    d['az_rep'] = state.az_rep
    d['el_rep'] = state.el_rep
    d['az_false_reading'] = False
    d['el_false_reading'] = False
    d['WindGust'] = state.wind_gust

    print(d)

    #p1 = Process(target=read_az, args=(d,))
    p2 = Process(target=read_el, args=(d,))
    p3 = Process(target=check_wind, args=(d,))

    #p1.start()
    p2.start()
    p3.start()

    while(1):
        print(d)
        time.sleep(3)
