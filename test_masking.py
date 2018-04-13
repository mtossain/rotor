################################################################################
# Control home made rotor on 2 axis
# 2018 M. Tossaint
################################################################################
import time
import sys,os
import curses
import datetime
import math

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
    el_req = 45 # deg

    az_rep = 185 # deg
    el_rep = 85 # deg

    az_stat = 'r'
    el_stat = 'f'

    above_mask = False # Whether pointing target is above or below the set mask
    manual_mode = True # Whether a manual mode or tracking mode command is given

k=0
conf = Config() # Get the configuration of the tool
state = State() # Get the initial state of the rotor

def check_above_mask():

    global conf,state

    el_mask = conf.mask
    num_masks = len(el_mask)
    step_mask = 360/num_masks

    az_idx = int(state.az_req)/int(step_mask)
    print('az_idx: '+str(az_idx))

    if state.el_req>el_mask[az_idx]:
        print('Found above mask')
    	state.above_mask = True
    else:
        state.above_mask = False

print('Masking string: '+str(conf.mask))
for i in range(0,360,45):
    print('***')
    state.az_req = i
    state.el_req = 45
    print('AZ req: ' + str ( state.az_req))
    print('EL req: ' + str ( state.el_req))
    check_above_mask()
    print('Masked: ' + str (not state.above_mask))

