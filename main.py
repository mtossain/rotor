################################################################################
# Control home made rotor on 2 axis
# 2018 M. Tossaint
################################################################################
import logging
import time
import sys,os
import curses
import datetime
import math
import threading
threads =[]

logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('debug.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.WARNING)

#from motor_control import * # PWM was tested but failed completely
from motor_control_nopwm import *
from astronomical import *
from read_heading import *

az_active = True # Azimuth motors activated?
az_sense_active = True # Azimuth sensors activated?
el_active = True # Elevation motors activated?
el_sense_active = True # Elevation sensors activated?
tracking_band = 3 # Tracking band in [deg]

class Config:

   rotor_lat = 52.04058 # deg N
   rotor_lon = 5.03625 # deg E
   rotor_alt = 4 # m

   bias_az = -20 # deg
   bias_el = 57.9 # deg

   mask = [0,90,90,90,90,0] # sectorials from 0 to 360 in deg

   goto_az = 350 # deg from 0 to 360
   goto_el = 80 # deg

   goto_ra = 5.5 # hours decimal
   goto_dec = 22.0 # deg decimal

   track_planet = 'Moon' # planet in capital or small
   track_sat_tle = 'tle.txt' # file with TLE elements, first one taken

class State:

    az_req = 10 # deg
    el_req = 90 # deg

    az_rep = 185 # deg
    el_rep = 85 # deg

    az_stat = 'r'
    el_stat = 'f'

    above_mask = True # Whether pointing target is above or below the set mask
    manual_mode = True # Whether a manual mode or tracking mode command is given

k=0
conf = Config() # Get the configuration of the tool
state = State() # Get the initial state of the rotor

def check_start_middle(width,str):
    return int((width // 2) - (len(str) // 2) - len(str) % 2)

def check_above_mask():

    global k,conf,state

    above_mask = False
    az_mask = []
    el_mask = conf.mask
    num_masks = len(el_mask)
    step_mask = 360/num_masks

    az_idx = int(state.az_req)/int(step_mask)

    if state.el_req>el_mask[az_idx]:
    	above_mask = True

    return above_mask

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
    stdscr.addstr(0, check_start_middle(width,string), string[:width-1],curses.color_pair(6))
    string = "   <<    <     +     >    >>"
    start_x = check_start_middle(width,string)
    stdscr.addstr(1, start_x, string[:width-1])
    stdscr.addstr(2, start_x, "AZ "[:width-1])
    stdscr.addstr(2, start_x+3, "'w'  'e'   'r'   't'  'y'"[:width-1],curses.color_pair(4))
    stdscr.addstr(3, start_x, "EL "[:width-1])
    stdscr.addstr(3, start_x+3, "'s'  'd'   'f'   'g'  'h'"[:width-1],curses.color_pair(4))
    stdscr.addstr(5, 2, "'x' goto Azimuth:       {:6.1f} [deg]".format(conf.goto_az)[:width-1])
    stdscr.addstr(5, 2, "'x'"[:width-1],curses.color_pair(4))
    stdscr.addstr(6, 2, "         Elevation:     {:6.1f} [deg]".format(conf.goto_el)[:width-1])
    stdscr.addstr(5, 42, "'c' track RightAsc:     {:6.1f} [hrs]".format(conf.goto_ra)[:width-1])
    stdscr.addstr(5, 42, "'c'"[:width-1],curses.color_pair(4))
    stdscr.addstr(6, 42, "          Declination:  {:6.1f} [deg]".format(conf.goto_dec)[:width-1])
    stdscr.addstr(8, 2,"'b' track plan body:     {}".format(conf.track_planet)[:width-1])
    stdscr.addstr(8, 2,"'b'"[:width-1],curses.color_pair(4))
    stdscr.addstr(8, 42,"'v' track satellite file: {}".format(conf.track_sat_tle)[:width-1])
    stdscr.addstr(8, 42,"'v'"[:width-1],curses.color_pair(4))

    stdscr.addstr(10, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length
    string = "--- Configuration ---"
    stdscr.addstr(10, check_start_middle(width,string), string[:width-1],curses.color_pair(6))

    string = "Lat rotor: {:.2f} [deg N]".format(conf.rotor_lat)[:width-1]
    stdscr.addstr(11, check_start_middle(width,string),string)
    string = "Lon rotor: {:.2f} [deg N]".format(conf.rotor_lon)[:width-1]
    stdscr.addstr(12, check_start_middle(width,string),string)
    string = "Alt rotor: {:.2f} [deg N]".format(conf.rotor_alt)[:width-1]
    stdscr.addstr(13, check_start_middle(width,string),string)
    string = "Bias AZ sensor: {:.2f} [deg]".format(conf.bias_az)[:width-1]
    stdscr.addstr(14, check_start_middle(width,string),string)
    string = "Bias EL sensor:  {:.2f} [deg]".format(conf.bias_el)[:width-1]
    stdscr.addstr(15, check_start_middle(width,string),string)
    string = "Masking: {} [deg el]".format(str(conf.mask))[:width-1]
    stdscr.addstr(16, check_start_middle(width,string),string)

    stdscr.addstr(18, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length
    string = "--- Rotor State Variables ---"
    stdscr.addstr(18, check_start_middle(width,string), string[:width-1],curses.color_pair(6))

    stdscr.addstr(19, 2, "                          Requested       Reported     Mode    Masked"[:width-1])
    stdscr.addstr(20, 2, "Azimuth rotor:          {:6.1f} [deg]    {:6.1f} [deg]    {}       {}".format(state.az_req,state.az_rep,state.az_stat,not state.above_mask)[:width-1])
    stdscr.addstr(21, 2, "Elevation rotor:        {:6.1f} [deg]    {:6.1f} [deg]    {}       {}".format(state.el_req,state.el_rep,state.el_stat,not state.above_mask)[:width-1])

    stdscr.refresh()

def update_screen(stdscr):

    global k,conf,state

    height, width = stdscr.getmaxyx() # Get the dimensions of the terminal

    statusbarstr = " UTC {} | 2018 - M. Tossaint | ' ' to Stop or 'q' to exit  ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:width-1]
    stdscr.addstr(height-1, check_start_middle(width,statusbarstr), statusbarstr,curses.color_pair(3)) # Render status bar

    if az_active:
        stdscr.addstr(20, 26, "{:6.1f}".format(state.az_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(20, 42, "{:6.1f}".format(state.az_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(20, 58, "{}".format(state.az_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(20, 66, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(5)+curses.A_BOLD)

    if el_active:
        stdscr.addstr(21, 26, "{:6.1f}".format(state.el_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(21, 42, "{:6.1f}".format(state.el_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(21, 58, "{}".format(state.el_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(21, 66, "{} ".format(str(not state.above_mask))[:width-1],curses.color_pair(5)+curses.A_BOLD)

    stdscr.refresh()
    
    time.sleep(0.1)

def check_command():

    global k,conf,state

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

    time.sleep(0.1)

def check_state(): # Check the state and whether target is achieved

    global conf
    global state

    logger.error('Inside check_state: '+str(state.manual_mode))
    if state.manual_mode == False: # Checking only needed for non manual modes

        # Update the pointing target
        if (state.az_stat=='x') or (state.el_stat=='x'):
            state.az_req = conf.goto_az
            state.el_req = conf.goto_el
            logger.error('Inside update pointing: '+str(state.el_req))
        if (state.az_stat=='c') or (state.el_stat=='c'):
            state.az_req,state.el_req = compute_azel_from_radec(conf) # Update the target
        if (state.az_stat=='b') or (state.el_stat=='b'):
            state.az_req,state.el_req = compute_azel_from_planet(conf)  # Update the target
        if (state.az_stat=='v') or (state.el_stat=='v'):
            state.az_req,state.el_req = compute_azel_from_tle(conf) # Update the target

        state.above_mask = check_above_mask(conf,state) # Check whether pointing target is above the mask

        # Update movement of motors
        if az_active:
            if (state.az_req-state.az_rep > tracking_band and state.above_mask):
                for_az()
            if (state.az_req-state.az_rep < tracking_band and state.above_mask):
                rev_az()
            if (abs(state.az_req-state.az_rep) < tracking_band) :
                stop_az()
                if (state.az_stat == 'x'): # Only for the goto command finish automatically (no tracking)
                    state.az_stat = 'r'
                    state.manual_mode = True

        if el_active:
            if (state.el_req-state.el_rep > tracking_band and state.above_mask):
                for_el()
            if (state.el_req-state.el_rep < tracking_band and state.above_mask):
                rev_el()
            if (abs(state.el_req-state.el_rep) < tracking_band) :
                stop_el()
                if (state.el_stat == 'x'): # Only for the goto command finish automatically (no tracking)
                    state.el_stat = 'f'
                    state.manual_mode = True

    time.sleep(0.1)

def read_sensor():

    global state

    if az_sense_active:
        state.az_rep = read_az_ang() - conf.bias_az # Read azimuth sensor output
    if el_sense_active:
        state.el_rep = read_el_ang() - conf.bias_el # Read azimuth sensor output

    time.sleep(0.1)

def mainloop(stdscr):

    global k,conf,state
    logger.error('Started main loop')
    init_screen(stdscr) # Initialise the screen

    t_read_sensor = threading.Thread(target=read_sensor)
    threads.append(t_read_sensor)
    t_read_sensor.start() # Read position sensor data

    t_check_state = threading.Thread(target=check_state)
    threads.append(t_check_state)
    t_check_state.start() # Check the state and whether target is achieved

    while (k != ord('q')): # Loop where k is the last character pressed

        check_command() # Check the typed command

        update_screen(stdscr) # Update the screen with new State

        k = stdscr.getch() # Get next user input
        
        time.sleep(0.1)

def main():
    curses.wrapper(mainloop)

if __name__ == "__main__":
    main()
