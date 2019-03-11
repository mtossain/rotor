################################################################################
# Control home made rotor on 2 axis
# 2018 M. Tossaint
################################################################################
import time
import sys,os
import curses
import datetime
import math
import urllib2
import json
from dateutil.parser import *

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

   max_wind_gust = 8 # When wind gust exceed point to zenith

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

k=0 # Keypress numeric value
conf = Config() # Get the configuration of the tool
state = State() # Get the initial state of the rotor

def convert_az_reading(angle): # Takes an angle from -180 to 180 and converts to proper 0-360 CW
    return 360 - (angle)

def check_start_middle(width,str): # Get the middle of the screen
    return int((width // 2) - (len(str) // 2) - len(str) % 2)

def check_wind():

    try:
        f = urllib2.urlopen('http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/pws:IIJSSELS41.json')
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
        WindGust=0
    return WindGust

def check_night():

    now = dt.datetime.now()
    seconds = (now-station_time).total_seconds()

def check_motor_pins(): # Check the status of the motor pins external to the program

    global state

    pin1 = int(os.popen("gpio -g read 19").read()) # This will run the command and return any output
    pin2 = int(os.popen("gpio -g read 26").read()) # This will run the command and return any output
    pin3 = int(os.popen("gpio -g read 6").read()) # This will run the command and return any output
    pin4 = int(os.popen("gpio -g read 13").read()) # This will run the command and return any output

    state.motor_az_pins = [pin1,pin2]
    state.motor_el_pins = [pin3,pin4]

def check_above_mask(): # Check whether requested target is abovet the mask

    global conf,state

    step_mask = 360/len(conf.mask)

    az_idx = int(state.az_req)/int(step_mask) # integer division

    if state.el_req>conf.mask[az_idx]:
    	state.above_mask = True
    else:
        state.above_mask = False


def init_screen(stdscr):

    global k,conf,state

    stdscr.clear() # Clear the screen
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(True) # Dont wait for input

    curses.start_color() # Define colors in curses
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx() # Get the dimensions of the terminal

    stdscr.addstr(0, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length

    # Print rest of text
    string = "--- Keyboard Commands ---"
    stdscr.addstr(0, check_start_middle(width,string), string[:width-1],curses.color_pair(6)+curses.A_BOLD)
    string = "   <<    <     +     >    >>"
    start_x = check_start_middle(width,string)
    stdscr.addstr(1, start_x, string[:width-1])
    stdscr.addstr(2, start_x, "AZ "[:width-1])
    stdscr.addstr(2, start_x+3, "'w'  'e'   'r'   't'  'y'"[:width-1],curses.color_pair(4)+curses.A_BOLD)
    stdscr.addstr(3, start_x, "EL "[:width-1])
    stdscr.addstr(3, start_x+3, "'s'  'd'   'f'   'g'  'h'"[:width-1],curses.color_pair(4)+curses.A_BOLD)
    stdscr.addstr(5, 2, "'x' goto Azimuth:       {:6.1f} [deg]".format(conf.goto_az)[:width-1])
    stdscr.addstr(5, 2, "'x'"[:width-1],curses.color_pair(4)+curses.A_BOLD)
    stdscr.addstr(6, 2, "         Elevation:     {:6.1f} [deg]".format(conf.goto_el)[:width-1])
    stdscr.addstr(5, 42, "'c' track RightAsc:     {:6.1f} [hrs]".format(conf.goto_ra)[:width-1])
    stdscr.addstr(5, 42, "'c'"[:width-1],curses.color_pair(4)+curses.A_BOLD)
    stdscr.addstr(6, 42, "          Declination:  {:6.1f} [deg]".format(conf.goto_dec)[:width-1])
    stdscr.addstr(8, 2,"'b' track plan body:     {}".format(conf.track_planet)[:width-1])
    stdscr.addstr(8, 2,"'b'"[:width-1],curses.color_pair(4)+curses.A_BOLD)
    stdscr.addstr(8, 42,"'v' track satellite file: {}".format(conf.track_sat_tle)[:width-1])
    stdscr.addstr(8, 42,"'v'"[:width-1],curses.color_pair(4)+curses.A_BOLD)

    stdscr.addstr(10, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length
    string = "--- Configuration ---"
    stdscr.addstr(10, check_start_middle(width,string), string[:width-1],curses.color_pair(6)+curses.A_BOLD)

    string = "Lat rotor: {:.2f} [deg N]".format(conf.rotor_lat)[:width-1]
    stdscr.addstr(11, check_start_middle(width,string),string)
    string = "Lon rotor: {:.2f} [deg E]".format(conf.rotor_lon)[:width-1]
    stdscr.addstr(12, check_start_middle(width,string),string)
    string = "Alt rotor: {:.2f} [m]".format(conf.rotor_alt)[:width-1]
    stdscr.addstr(13, check_start_middle(width,string),string)
    string = "Bias AZ sensor: {:.2f} [deg]".format(conf.bias_az)[:width-1]
    stdscr.addstr(14, check_start_middle(width,string),string)
    string = "Bias EL sensor:  {:.2f} [deg]".format(conf.bias_el)[:width-1]
    stdscr.addstr(15, check_start_middle(width,string),string)
    string = "Masking: {} [deg el]".format(str(conf.mask))[:width-1]
    stdscr.addstr(16, check_start_middle(width,string),string)

    stdscr.addstr(18, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length
    string = "--- Rotor State Variables ---"
    stdscr.addstr(18, check_start_middle(width,string), string[:width-1],curses.color_pair(6)+curses.A_BOLD)

    stdscr.addstr(19, 2, "                          Requested      Reported     Mode   Masked    Pins"[:width-1])
    stdscr.addstr(20, 2, "Azimuth rotor:          {:6.1f} [deg]   {:6.1f} [deg]    {}      {}".format(state.az_req,state.az_rep,state.az_stat,not state.above_mask)[:width-1])
    stdscr.addstr(21, 2, "Elevation rotor:        {:6.1f} [deg]   {:6.1f} [deg]    {}      {}".format(state.el_req,state.el_rep,state.el_stat,not state.above_mask)[:width-1])

    stdscr.refresh()

def update_screen(stdscr):

    global state

    height, width = stdscr.getmaxyx() # Get the dimensions of the terminal

    statusbarstr = " UTC {} | 2018 - M. Tossaint | ' ' to Stop or 'q' to exit  ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:width-1]
    stdscr.addstr(height-1, check_start_middle(width,statusbarstr), statusbarstr,curses.color_pair(3)) # Render status bar

    check_motor_pins()

    if state.wind_gust_flag:
        stdscr.addstr(17, 29, "Wind Speed Gust {} ".format(state.wind_gust)[:width-1],curses.color_pair(2)+curses.A_BOLD)
    else:
        stdscr.addstr(17, 29, "Wind Speed Gust {} ".format(state.wind_gust)[:width-1])

    if az_active:
        stdscr.addstr(20, 26, "{:6.1f}".format(state.az_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        if state.az_false_reading:
            stdscr.addstr(20, 41, "{:6.1f}".format(state.az_rep)[:width-1],curses.color_pair(2)+curses.A_BOLD)
        else:
            stdscr.addstr(20, 41, "{:6.1f}".format(state.az_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(20, 57, "{}".format(state.az_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        if state.above_mask:
            stdscr.addstr(20, 64, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(5)+curses.A_BOLD)
        else:
            stdscr.addstr(20, 64, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(2)+curses.A_BOLD)
        stdscr.addstr(20, 72, "{} ".format(str(state.motor_az_pins))[:width-1],curses.color_pair(5)+curses.A_BOLD)

    if el_active:
        stdscr.addstr(21, 26, "{:6.1f}".format(state.el_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        if state.el_false_reading:
            stdscr.addstr(21, 41, "{:6.1f}".format(state.el_rep)[:width-1],curses.color_pair(2)+curses.A_BOLD)
        else:
            stdscr.addstr(21, 41, "{:6.1f}".format(state.el_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(21, 57, "{}".format(state.el_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        if state.above_mask:
            stdscr.addstr(21, 64, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(5)+curses.A_BOLD)
        else:
            stdscr.addstr(21, 64, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(2)+curses.A_BOLD)
        stdscr.addstr(21, 72, "{} ".format(str(state.motor_el_pins))[:width-1],curses.color_pair(5)+curses.A_BOLD)

    stdscr.refresh()

def check_command():

    global k,state

    if az_active: # Manual activation azimuth
        if (k == ord('w')):
            rev_az()
            state.az_stat = 'w'
            state.manual_mode = True
        if (k == ord('e')):
            rev_az()
            state.az_stat = 'e'
            state.manual_mode = True
        if (k == ord('r') or k == ord(' ')):
            stop_az()
            state.az_stat = 'r'
            state.manual_mode = True
            state.above_mask = True
            state.az_req = 0
        if (k == ord('t')):
            for_az()
            state.az_stat = 't'
            state.manual_mode = True
        if (k == ord('y')):
            for_az()
            state.az_stat = 'y'
            state.manual_mode = True

        if (k == ord('x')):
            state.az_stat = 'x'
            state.manual_mode = False
        if (k == ord('c')):
            state.az_stat = 'c'
            state.manual_mode = False
        if (k == ord('b')):
            state.az_stat = 'b'
            state.manual_mode = False
        if (k == ord('v')):
            state.az_stat = 'v'
            state.manual_mode = False

    if el_active: # Manual activation elevation
        if (k == ord('s')):
            rev_el()
            state.el_stat = 's'
            state.manual_mode = True
        if (k == ord('d')):
            rev_el()
            state.el_stat = 'd'
            state.manual_mode = True
        if (k == ord('f') or k == ord(' ')):
            stop_el()
            state.el_stat = 'f'
            state.manual_mode = True
            state.above_mask = True
            state.el_req = 90
        if (k == ord('g')):
            for_el()
            state.el_stat = 'g'
            state.manual_mode = True
        if (k == ord('h')):
            for_el()
            state.el_stat = 'h'
            state.manual_mode = True

        if (k == ord('x')):
            state.el_stat = 'x'
            state.manual_mode = False
        if (k == ord('c')):
            state.el_stat = 'c'
            state.manual_mode = False
        if (k == ord('b')):
            state.el_stat = 'b'
            state.manual_mode = False
        if (k == ord('v')):
            state.el_stat = 'v'
            state.manual_mode = False

def check_state(): # Check the state and whether target is achieved

    global conf, state

    check_above_mask() # Check whether pointing target is above the mask


    if state.manual_mode == False: # Checking only needed for non manual modes

        # Update the pointing target
        if (state.az_stat=='x') or (state.el_stat=='x'):
            state.az_req = conf.goto_az
            state.el_req = conf.goto_el
        if (state.az_stat=='c') or (state.el_stat=='c'):
            state.az_req,state.el_req = compute_azel_from_radec(conf) # Update the target
        if (state.az_stat=='b') or (state.el_stat=='b'):
            state.az_req,state.el_req = compute_azel_from_planet(conf)  # Update the target
        if (state.az_stat=='v') or (state.el_stat=='v'):
            state.az_req,state.el_req = compute_azel_from_tle(conf) # Update the target

        check_above_mask() # Check whether pointing target is above the mask

        state.wind_gust = check_wind()
        if(wind_check and state.wind_gust>conf.max_wind_gust): # If wind is too strong then go into safe mode at 90 elevation
            state.el_req=90
            state.wind_gust_flag = True
        else:
            state.wind_gust_flag = False

        # Update movement of motors
        if az_active:
            if (not state.above_mask):
                stop_az()
            if (abs(state.az_req-state.az_rep) < az_tracking_band):
                stop_az()
                if (state.az_stat == 'x'): # Only for the goto/wind command finish automatically (no tracking)
                    state.az_stat = 'r'
            else: # order is very important otherwise start/stop
                if (state.az_req-state.az_rep > az_tracking_band and state.above_mask):
                    for_az()
                if (state.az_req-state.az_rep < az_tracking_band and state.above_mask):
                    rev_az()

        if el_active:
            if (not state.above_mask):
                state.el_req=90 # If under mask, then point to zenith
            if (abs(state.el_req-state.el_rep) < el_tracking_band) :
                stop_el()
                if (state.el_stat == 'x'): # Only for the goto/wind command finish automatically (no tracking)
                    state.el_stat = 'f'
            else: # order is very important otherwise start/stop
                if (state.el_req-state.el_rep > el_tracking_band and state.above_mask):
                    for_el()
                if (state.el_req-state.el_rep < el_tracking_band and state.above_mask):
                    rev_el()

def read_sensor():

    global conf,stat

    if az_sense_active:
        state.az_false_reading,angle = read_az_ang() # Read azimuth sensor output
        if not state.az_false_reading:
            state.az_rep = (convert_az_reading(angle) - conf.bias_az)%360 # Convert for AMS5048 readings

    if el_sense_active:
        state.el_false_reading,angle = read_el_ang()
        if not state.el_false_reading:
            state.el_rep = angle - conf.bias_el # Read elevation sensor output

def mainloop(stdscr):

    global k,conf,state

    init_screen(stdscr) # Initialise the screen

    while (k != ord('q')): # Loop where k is the last character pressed

        check_command() # Check the pressed key

        check_state() # Check the state and whether target is achieved

        update_screen(stdscr) # Update the screen with new State

        k = stdscr.getch() # Get next user input

        read_sensor() # Read the input of the AMS5048B sensor

def main():
    curses.wrapper(mainloop)

if __name__ == "__main__":
    main()
