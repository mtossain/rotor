################################################################################
# Control home made rotor on 2 axis
# 2018 M. Tossaint
################################################################################

import time
import sys,os
import curses
import datetime
import math
#from motor_control import *
from motor_control_nopwm import *
from astronomical import *
#import read_heading

az_active = False
el_active = True

class Config:

   rotor_lat = 52 # deg N
   rotor_lon = 5 # deg E
   rotor_alt = 6 # m

   bias_az = 10 # deg
   bias_el = 20 # deg

   mask = [0,0,50,0] # sectorials from 0 to 360 in deg

   goto_az = 360 # deg from 0 to 360
   goto_el = 90 # deg
   goto_ra = 24.6 # hours decimal
   goto_dec = 90.0 # deg decimal
   track_planet = 'Sun' # planet in capital or small
   track_sat_tle = 'satnorad.tle'

class State:

    az_req = 180 # deg
    el_req = 90 # deg

    az_rep = 185 # deg
    el_rep = 85 # deg

    az_stat = 'r'
    el_stat = 'f'

def init_screen(stdscr, conf, state):

    stdscr.clear() # Clear the screen
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(True) # Dont wait for input

    curses.start_color() # Define colors in curses
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx() # Get the dimensions of the terminal

    statusbarstr = " UTC {}  |  Rotor control - M. Tossaint  |  Press 'q' to exit  ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:width-1]
    stdscr.addstr(height-1, 0, statusbarstr,curses.color_pair(3)) # Render status bar

    stdscr.addstr(0, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length

    # Print rest of text
    stdscr.addstr(1, 2, "                         <<    <     +     >    >>"[:width-1])
    stdscr.addstr(2, 2, "Manual Azimuth ctrl:     "[:width-1])
    stdscr.addstr(2, 27, "'w'  'e'   'r'   't'  'y'"[:width-1],curses.color_pair(4))
    stdscr.addstr(3, 2, "Manual Elevation ctrl:   "[:width-1])
    stdscr.addstr(3, 27, "'s'  'd'   'f'   'g'  'h'"[:width-1],curses.color_pair(4))
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

    stdscr.addstr(9, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length

    stdscr.addstr(10, 2, "Latitude rotor:          {:5.1f} [deg N]".format(conf.rotor_lat)[:width-1])
    stdscr.addstr(11, 2, "Longitude rotor:        {:6.1f} [deg E]".format(conf.rotor_lon)[:width-1])
    stdscr.addstr(12, 2, "Altitude rotor:         {:6.1f} [m]".format(conf.rotor_alt)[:width-1])
    stdscr.addstr(13, 2, "Bias azimuth sensor:    {:6.1f} [deg]".format(conf.bias_az)[:width-1])
    stdscr.addstr(14, 2, "Longitude rotor:        {:6.1f} [deg]".format(conf.bias_el)[:width-1])
    stdscr.addstr(15, 2, "Masking:                 {}".format(str(conf.mask))[:width-1])

    stdscr.addstr(16, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length

    stdscr.addstr(17, 2, "                          Requested       Reported     Mode"[:width-1])
    stdscr.addstr(18, 2, "Azimuth rotor:          {:6.1f} [deg]    {:6.1f} [deg]    {}".format(state.az_req,state.az_rep,state.az_stat)[:width-1])
    stdscr.addstr(19, 2, "Elevation rotor:        {:6.1f} [deg]    {:6.1f} [deg]    {}".format(state.el_req,state.el_rep,state.el_stat)[:width-1])

    stdscr.addstr(20, 0, '-' * width,curses.color_pair(2)) # Seperation line over full length

    stdscr.refresh()

def update_screen(stdscr, state):

    height, width = stdscr.getmaxyx() # Get the dimensions of the terminal

    statusbarstr = " UTC {}  |  Rotor control - M. Tossaint  |  Press 'q' to exit  ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:width-1]
    stdscr.addstr(height-1, 0, statusbarstr,curses.color_pair(3)) # Render status bar

    if az_active:
        stdscr.addstr(18, 26, "{:6.1f}".format(state.az_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(18, 42, "{:6.1f}".format(state.az_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(18, 58, "{}".format(state.az_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)

    if el_active:
        stdscr.addstr(19, 26, "{:6.1f}".format(state.el_req)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(19, 42, "{:6.1f}".format(state.el_rep)[:width-1],curses.color_pair(5)+curses.A_BOLD)
        stdscr.addstr(19, 58, "{}".format(state.el_stat)[:width-1],curses.color_pair(5)+curses.A_BOLD)

    stdscr.refresh()

def check_command(k,state):

    if az_active:
        if (k == ord('w')):
            #rev_az(1)
            rev_az()
            state.az_stat = 'w'
        if (k == ord('e')):
            #rev_az(0.5)
            rev_az()
            state.az_stat = 'e'
        if (k == ord('r')):
            stop_az()
            state.az_stat = 'r'
        if (k == ord('t')):
            #for_az(0.5)
            for_az()
            state.az_stat = 't'
        if (k == ord('y')):
            #for_az(1)
            for_az()
            state.az_stat = 'y'

    if el_active:
        if (k == ord('s')):
            #rev_el(1)
            rev_el()
            state.el_stat = 's'
        if (k == ord('d')):
            #rev_el(.5)
            rev_el()
            state.el_stat = 'd'
        if (k == ord('f')):
            stop_el()
            state.el_stat = 'f'
        if (k == ord('g')):
            #for_el(.5)
            for_el()
            state.el_stat = 'g'
        if (k == ord('h')):
            #for_el(1)
            for_el()
            state.el_stat = 'h'

    if az_active and el_active: # Start the goto and other tracking commands
        if (k == ord('x'))
            state.az_stat = 'x'
            state.el_stat = 'x'
        if (k == ord('c')):
            state.az_req,state.el_req = compute_azel_from_radec(state)
            state.az_stat = 'c'
            state.el_stat = 'c'
        if (k == ord('b')):
            state.az_req,state.el_req = compute_azel_from_planet(state)
            state.az_stat = 'b'
            state.el_stat = 'b'
        if (k == ord('v')):
            state.az_req,state.el_req = compute_azel_from_tle(state)
            state.az_stat = 'v'
            state.el_stat = 'v'

        if (k == ord('x')) or (k == ord('c')) or (k == ord('b')) or (k == ord('v')): # check which direction to move if at all
            if (state.az_req-state.az_rep > 1):
                #for_az(1)
                for_az()
            if (state.az_req-state.az_rep < 1):
                #rev_az(1)
                rev_az()
            if (state.el_req-state.el_rep > 1):
                #for_el(1)
                for_el()
            if (state.el_req-state.el_rep < 1):
                #rev_el(1)
                rev_el()

    return state

def check_state(state): # Check the state and whether target is achieved

    if az_active and el_active: # Goto only works when both motors active

        if (state.az_stat == 'x') or (state.az_stat == 'c') or (state.az_stat == 'b') or (state.az_stat == 'v'): # Do we have to stop the goto command?
            if (abs(state.az_req-state.az_rep) < 3) :
                stop_az()
                state.az_stat = 'r'

        if (state.el_stat == 'x') or (state.el_stat == 'c') or (state.el_stat == 'b') or (state.el_stat == 'v'): # Do we have to stop the goto command?
            if (abs(state.el_req-state.el_rep) < 3) :
                stop_el()
                state.el_stat = 'r'

    return state

def mainloop(stdscr):

    k = 0 # Initialise key press
    conf = Config() # Get the configuration of the tool
    state = State() # Get the initial state of the rotor

    init_screen(stdscr,conf,state) # Initialise the screen

    while (k != ord('q')): # Loop where k is the last character pressed

        update_screen(stdscr,state) # Update the screen with new State

        state = check_command(k,state) # Check the typed command

        state = check_state(state) # Check the state and whether target is achieved

        k = stdscr.getch() # Get next user input

        #if az_active:
            #state.az_rep = read_az_ang() # Read azimuth sensor output
        #if el_active:
            #state.el_rep = read_el_ang() # Read azimuth sensor output

        # For simulation purpose
        #time.sleep(.5)
        #state.az_rep = state.az_rep-0.1
        #state.el_rep = state.el_rep-0.1

def main():
    curses.wrapper(mainloop)

if __name__ == "__main__":
    main()
