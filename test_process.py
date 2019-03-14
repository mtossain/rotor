import Process, Manager
from read_heading import *
import time

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

def read_az(azimuth,bias):
    while (1):
        false_reading,angle = read_az_ang(d)
        d['az_false_reading'] = True
        if not false_reading:
            d['az_false_reading'] = False
            d['az_rep'] = round((convert_az_reading(angle) - bias)%360,2)
            #print(d['az_rep'])
        time.sleep(.5)


def read_el():
    while (1):
        false_reading,angle = read_el_ang(d)
        d['el_false_reading'] = True
        if not false_reading:
            d['el_false_reading'] = False
            d['el_rep']  = round(angle - bias,2)
            #print(d['el_rep'])
        time.sleep(.5)

def check_wind():
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
            #print('[NOK] Wunderground not found...')
            Wind=99
            WindGust=99
        d['Wind']=Wind
        d['WindGust']=WindGust
        d['WindDirAngle']=WindDirAngle

        time.sleep(1)

if __name__ == '__main__':

    k=0 # Keypress numeric value
    conf = Config() # Get the configuration of the tool
    state = State() # Get the initial state of the rotor

    d = manager.dict() # all the shared dictnaries between processes

    d['bias_az'] = conf.bias_az # deg
    d['bias_el'] = conf.bias_el # deg

    #p1 = Process(target=read_az, args=(d))
    p2 = Process(target=read_el, args=(d))
    p3 = Process(target=check_wind, args=(d))

    #p1.start()
    p2.start()
    p3.start()

    while(1):
        print('In main azimuth: ',d['az_rep'])
        print('In main elevation: ',d['el_rep'])
        print('In main wind: ',d['Wind'])
        time.sleep(3)
