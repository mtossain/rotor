###############################################################################
# Program to control rotor for dish, antenna or other pointing purpose
# v1 2018, M. Tossaint, For SETI application and 3m dish
# v2 2019, M. Tossaint, For Solar Panel steering to Sun
# v3 2019, M. Tossaint, added logging feature
###############################################################################
from multiprocessing import Process, Manager
import os
import curses
import datetime
import json
import urllib2
import logging
import logging.handlers as handlers

# from motor_control import * # PWM was tested but failed completely
import smooth
from motor_control_nopwm import *
from astronomical import *
from read_heading import *

logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)
logHandler = handlers.RotatingFileHandler('main.log', maxBytes=5*1024*1024, backupCount=2)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(logHandler)

class Config:

    rotor_lat, rotor_lon, rotor_alt = 52.04058, 5.03625, 4  # deg N,E,m

    bias_az, bias_el = -32.0, 58.9  # deg

    mask = [15, 15, 15, 15]  # sectorials from 0 to 360 in deg

    goto_az, goto_el  = 0, 90 # deg from 0 to 360, el from 0 (hor) to 90 (zenith)

    goto_ra, goto_dec = 5.5, 22.0  # hours decimal

    track_planet = 'Sun'  # planet in capital or small
    track_sat_tle = 'tle.txt'  # file with TLE elements, first one taken

    az_active = False  # Azimuth motors activated?
    az_sense_active = False  # Azimuth sensors activated?
    az_tracking_band = 2  # Tracking band in [deg]

    el_active = True  # Elevation motors activated?
    el_sense_active = True  # Elevation sensors activated?
    el_tracking_band = 1  # Tracking band in [deg]
    el_min = 30  # minimum angle that elevation can go to

    max_wind_gust = 6  # When wind gust exceed point to zenith
    wind_check = False  # Checking wind gust


class State:

    az_req, el_req = 10, 50  # deg

    az_rep, el_rep = 185, 85  # deg

    az_stat, el_stat = 'r', 'f'  # status

    az_false_reading, el_false_reading = False, False

    motor_az_pins, motor_el_pins = [0, 0], [0, 0]

    above_mask = True  # Whether pointing target is above or below the set mask
    manual_mode = True  # Whether a manual mode or tracking mode command is given

    wind_gust = 0  # kph
    wind_gust_flag = False  # Whether there is too much wind


def convert_az_reading(angle):  # Takes an angle from -180 to 180 and converts to proper 0-360 CW
    return 360 - angle


def check_start_middle(width, str):  # Get the middle of the screen
    return int((width // 2) - (len(str) // 2) - len(str) % 2)


def check_motor_pins():  # Check the status of the motor pins external to the program

    global state

    pin1 = int(os.popen("gpio -g read 19").read())  # This will run the command and return any output
    pin2 = int(os.popen("gpio -g read 26").read())  # This will run the command and return any output
    pin3 = int(os.popen("gpio -g read 6").read())  # This will run the command and return any output
    pin4 = int(os.popen("gpio -g read 13").read())  # This will run the command and return any output

    state.motor_az_pins = [pin1, pin2]
    state.motor_el_pins = [pin3, pin4]


def check_above_mask():  # Check whether requested target is abovet the mask

    global conf, state

    step_mask = 360 / len(conf.mask)

    az_idx = int(int(state.az_req) / int(step_mask))  # integer division

    if state.el_req > conf.mask[az_idx]:
        state.above_mask = True
    else:
        state.above_mask = False


def update_screen(stdscr):
    global conf, state

    height, width = stdscr.getmaxyx()  # Get the dimensions of the terminal

    statusbarstr = " UTC {} | 2018 - M. Tossaint | ' ' to Stop or 'q' to exit  ".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))[:width - 1]
    stdscr.addstr(height - 1, check_start_middle(width, statusbarstr), statusbarstr,
                  curses.color_pair(3))  # Render status bar

    check_motor_pins()

    if state.wind_gust_flag:
        stdscr.addstr(17, 29, "Wind Speed Gust {} ".format(state.wind_gust)[:width - 1],
                      curses.color_pair(2) + curses.A_BOLD)
    else:
        stdscr.addstr(17, 29, "Wind Speed Gust {} ".format(state.wind_gust)[:width - 1])

    if conf.az_active:
        stdscr.addstr(20, 26, "{:6.1f}".format(state.az_req)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        if state.az_false_reading:
            stdscr.addstr(20, 41, "{:6.1f}".format(state.az_rep)[:width - 1], curses.color_pair(2) + curses.A_BOLD)
        else:
            stdscr.addstr(20, 41, "{:6.1f}".format(state.az_rep)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        stdscr.addstr(20, 57, "{}".format(state.az_stat)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        if state.above_mask:
            stdscr.addstr(20, 64, "{} ".format(str(not state.above_mask))[:width - 1],
                          curses.color_pair(5) + curses.A_BOLD)
        else:
            stdscr.addstr(20, 64, "{} ".format(str(not state.above_mask))[:width - 1],
                          curses.color_pair(2) + curses.A_BOLD)
        stdscr.addstr(20, 72, "{} ".format(str(state.motor_az_pins))[:width - 1], curses.color_pair(5) + curses.A_BOLD)

    if conf.el_active:
        stdscr.addstr(21, 26, "{:6.1f}".format(state.el_req)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        if state.el_false_reading:
            stdscr.addstr(21, 41, "{:6.1f}".format(state.el_rep)[:width - 1], curses.color_pair(2) + curses.A_BOLD)
        else:
            stdscr.addstr(21, 41, "{:6.1f}".format(state.el_rep)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        stdscr.addstr(21, 57, "{}".format(state.el_stat)[:width - 1], curses.color_pair(5) + curses.A_BOLD)
        if state.above_mask:
            stdscr.addstr(21, 64, "{} ".format(str(not state.above_mask))[:width - 1],
                          curses.color_pair(5) + curses.A_BOLD)
        else:
            stdscr.addstr(21, 64, "{} ".format(str(not state.above_mask))[:width - 1],
                          curses.color_pair(2) + curses.A_BOLD)
        stdscr.addstr(21, 72, "{} ".format(str(state.motor_el_pins))[:width - 1], curses.color_pair(5) + curses.A_BOLD)

    stdscr.refresh()


def check_command():
    global k, conf, state

    if conf.az_active:  # Manual activation azimuth
        if k == ord('w'):
            rev_az()
            state.az_stat = 'w'
            state.manual_mode = True
        if k == ord('e'):
            rev_az()
            state.az_stat = 'e'
            state.manual_mode = True
        if k == ord('r') or k == ord(' '):
            stop_az()
            state.az_stat = 'r'
            state.manual_mode = True
            state.above_mask = True
            state.az_req = 0
        if k == ord('t'):
            for_az()
            state.az_stat = 't'
            state.manual_mode = True
        if k == ord('y'):
            for_az()
            state.az_stat = 'y'
            state.manual_mode = True

        if k == ord('x'):
            state.az_stat = 'x'
            state.manual_mode = False
        if k == ord('c'):
            state.az_stat = 'c'
            state.manual_mode = False
        if k == ord('b'):
            state.az_stat = 'b'
            state.manual_mode = False
        if k == ord('v'):
            state.az_stat = 'v'
            state.manual_mode = False

    if conf.el_active:  # Manual activation elevation
        if k == ord('s'):
            rev_el()
            state.el_stat = 's'
            state.manual_mode = True
        if k == ord('d'):
            rev_el()
            state.el_stat = 'd'
            state.manual_mode = True
        if k == ord('f') or k == ord(' '):
            stop_el()
            state.el_stat = 'f'
            state.manual_mode = True
            state.above_mask = True
            state.el_req = 90
        if k == ord('g'):
            for_el()
            state.el_stat = 'g'
            state.manual_mode = True
        if k == ord('h'):
            for_el()
            state.el_stat = 'h'
            state.manual_mode = True

        if k == ord('x'):
            state.el_stat = 'x'
            state.manual_mode = False
        if k == ord('c'):
            state.el_stat = 'c'
            state.manual_mode = False
        if k == ord('b'):
            state.el_stat = 'b'
            state.manual_mode = False
        if k == ord('v'):
            state.el_stat = 'v'
            state.manual_mode = False


def init_screen(stdscr):
    global k, conf, state

    stdscr.clear()  # Clear the screen
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Don't wait for input

    curses.start_color()  # Define colors in curses
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx()  # Get the dimensions of the terminal

    stdscr.addstr(0, 0, '-' * width, curses.color_pair(2))  # Separation line over full length

    # Print rest of text
    string = "--- Keyboard Commands ---"
    stdscr.addstr(0, check_start_middle(width, string), string[:width - 1], curses.color_pair(6) + curses.A_BOLD)
    string = "   <<    <     +     >    >>"
    start_x = check_start_middle(width, string)
    stdscr.addstr(1, start_x, string[:width - 1])
    stdscr.addstr(2, start_x, "AZ "[:width - 1])
    stdscr.addstr(2, start_x + 3, "'w'  'e'   'r'   't'  'y'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)
    stdscr.addstr(3, start_x, "EL "[:width - 1])
    stdscr.addstr(3, start_x + 3, "'s'  'd'   'f'   'g'  'h'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)
    stdscr.addstr(5, 2, "'x' goto Azimuth:       {:6.1f} [deg]".format(conf.goto_az)[:width - 1])
    stdscr.addstr(5, 2, "'x'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)
    stdscr.addstr(6, 2, "         Elevation:     {:6.1f} [deg]".format(conf.goto_el)[:width - 1])
    stdscr.addstr(5, 42, "'c' track RightAsc:     {:6.1f} [hrs]".format(conf.goto_ra)[:width - 1])
    stdscr.addstr(5, 42, "'c'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)
    stdscr.addstr(6, 42, "          Declination:  {:6.1f} [deg]".format(conf.goto_dec)[:width - 1])
    stdscr.addstr(8, 2, "'b' track plan body:     {}".format(conf.track_planet)[:width - 1])
    stdscr.addstr(8, 2, "'b'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)
    stdscr.addstr(8, 42, "'v' track satellite file: {}".format(conf.track_sat_tle)[:width - 1])
    stdscr.addstr(8, 42, "'v'"[:width - 1], curses.color_pair(4) + curses.A_BOLD)

    stdscr.addstr(10, 0, '-' * width, curses.color_pair(2))  # Separation line over full length
    string = "--- Configuration ---"
    stdscr.addstr(10, check_start_middle(width, string), string[:width - 1], curses.color_pair(6) + curses.A_BOLD)

    string = "Lat rotor: {:.2f} [deg N]".format(conf.rotor_lat)[:width - 1]
    stdscr.addstr(11, check_start_middle(width, string), string)
    string = "Lon rotor: {:.2f} [deg E]".format(conf.rotor_lon)[:width - 1]
    stdscr.addstr(12, check_start_middle(width, string), string)
    string = "Min elev: {:.1f} [deg]".format(conf.el_min)[:width - 1]
    stdscr.addstr(13, check_start_middle(width, string), string)
    string = "Bias AZ sensor: {:.2f} [deg]".format(conf.bias_az)[:width - 1]
    stdscr.addstr(14, check_start_middle(width, string), string)
    string = "Bias EL sensor:  {:.2f} [deg]".format(conf.bias_el)[:width - 1]
    stdscr.addstr(15, check_start_middle(width, string), string)
    string = "Masking: {} [deg el]".format(str(conf.mask))[:width - 1]
    stdscr.addstr(16, check_start_middle(width, string), string)

    stdscr.addstr(18, 0, '-' * width, curses.color_pair(2))  # Separation line over full length
    string = "--- Rotor State Variables ---"
    stdscr.addstr(18, check_start_middle(width, string), string[:width - 1], curses.color_pair(6) + curses.A_BOLD)

    stdscr.addstr(19, 2, "                          Requested      Reported     Mode   Masked    Pins"[:width - 1])
    stdscr.addstr(20, 2, "Azimuth rotor:          {:6.1f} [deg]   {:6.1f} [deg]    {}      {}".format(state.az_req,
                                                                                                      state.az_rep,
                                                                                                      state.az_stat,
                                                                                                      not state.above_mask)[
                         :width - 1])
    stdscr.addstr(21, 2, "Elevation rotor:        {:6.1f} [deg]   {:6.1f} [deg]    {}      {}".format(state.el_req,
                                                                                                      state.el_rep,
                                                                                                      state.el_stat,
                                                                                                      not state.above_mask)[
                         :width - 1])

    stdscr.refresh()


def read_az(d):
    while 1:
        false_reading, angle = read_az_ang()
        d['az_false_reading'] = True
        if not false_reading:
            d['az_false_reading'] = False
            d['az_rep'] = round((convert_az_reading(angle) - d['bias_az']) % 360, 2)
        time.sleep(.5)


def read_el(d):
    while 1:
        false_reading, angle = read_el_ang()
        d['el_false_reading'] = True
        if not false_reading:
            d['el_false_reading'] = False
            d['el_rep'] = round(angle - d['bias_el'], 2)
        time.sleep(.5)


def check_wind(d):
    wind_s = smooth.Smooth(10, 10)
    wind_gust_s = smooth.Smooth(10, 10)

    while 1:
        try:
            f = urllib2.urlopen('http://api.wunderground.com/api/c76852885ada6b8a/conditions/q/Ijsselstein.json')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            wind = round(wind_s.add_step(int(float(parsed_json['current_observation']['wind_kph']))))
            wind_gust = round(wind_gust_s.add_step(int(float(parsed_json['current_observation']['wind_gust_kph']))))
        except:
            f = urllib2.urlopen(
                'http://api.openweathermap.org/data/2.5/weather?q=Ijsselstein&APPID=37c36ad4b5df0e23f93e8cff206e5a2c')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            wind = round(wind_s.add_step(int(float(parsed_json['wind']['speed']))))
            wind_gust = Wind

        d['Wind'] = wind
        d['WindGust'] = wind_gust

        time.sleep(1)


def check_state():  # Check the state and whether target is achieved

    global conf, state

    check_above_mask()  # Check whether pointing target is above the mask

    if not state.manual_mode:  # Checking only needed for non manual modes

        # Update the pointing target
        if (state.az_stat == 'x') or (state.el_stat == 'x'):
            state.az_req = conf.goto_az
            state.el_req = conf.goto_el
            logger.info(['Going to AZ/EL [req/req]:', str(state.az_req), str(state.el_req)])
        if (state.az_stat == 'c') or (state.el_stat == 'c'):
            state.az_req, state.el_req = compute_azel_from_radec(conf)  # Update the target
            logger.info(['Going to AZ/EL [req/req]:', str(state.az_req), str(state.el_req)])
        if (state.az_stat == 'b') or (state.el_stat == 'b'):
            state.az_req, state.el_req = compute_azel_from_planet(conf)  # Update the target
            logger.info(['Going to AZ/EL [req/req]:', str(state.az_req), str(state.el_req)])
        if (state.az_stat == 'v') or (state.el_stat == 'v'):
            state.az_req, state.el_req = compute_azel_from_tle(conf)  # Update the target
            logger.info(['Going to AZ/EL [req/req]:', str(state.az_req), str(state.el_req)])

        check_above_mask()  # Check whether pointing target is above the mask

        # If wind is too strong then go into safe mode at 90 elevation
        if conf.wind_check and state.wind_gust > conf.max_wind_gust:
            state.el_req = 90

        # Update movement of motors
        if conf.az_active:
            if not state.above_mask:
                stop_az()
            if abs(state.az_req - state.az_rep) < conf.az_tracking_band:
                stop_az()
                logger.info(['Stopping az tracking [req/rep]:', str(state.az_req), str(state.az_rep)])
                if state.az_stat == 'x':  # Only for the goto/wind command finish automatically (no tracking)
                    state.az_stat = 'r'
            else:  # order is very important otherwise start/stop
                if state.az_req - state.az_rep > conf.az_tracking_band and state.above_mask:
                    for_az()
                    logger.info(['Forward az tracking [req/rep]:', str(state.az_req), str(state.az_rep)])
                if state.az_req - state.az_rep < conf.az_tracking_band and state.above_mask:
                    rev_az()
                    logger.info(['Reverse az tracking [req/rep]:', str(state.az_req), str(state.az_rep)])

        if conf.el_active:
            if not state.above_mask:
                state.el_req = 90  # If under mask, then point to zenith
            if state.el_req < conf.el_min:
                state.el_req = conf.el_min
            if abs(state.el_req - state.el_rep) < conf.el_tracking_band:
                stop_el()
                logger.info(['Stopping el tracking [req/rep]:', str(state.el_req), str(state.el_rep)])
                if state.el_stat == 'x':  # Only for the goto/wind command finish automatically (no tracking)
                    state.el_stat = 'f'
            else:  # order is very important otherwise start/stop
                if state.el_req - state.el_rep > conf.el_tracking_band:
                    for_el()
                    logger.info(['Forward el tracking [req/rep]:', str(state.el_req), str(state.el_rep)])
                if state.el_req - state.el_rep < conf.el_tracking_band:
                    rev_el()
                    logger.info(['Reverse el tracking [req/rep]:', str(state.el_req), str(state.el_rep)])


def read_sensor(d):
    global conf, stat

    state.el_false_reading = d['el_false_reading']

    if conf.az_sense_active:
        state.az_false_reading = d['az_false_reading']
        state.az_rep = d['az_rep']

    if conf.el_sense_active:
        state.el_false_reading = d['el_false_reading']
        state.el_rep = d['el_rep']

    if conf.wind_check:
        state.wind_gust = d['WindGust']
        if state.wind_gust > conf.max_wind_gust:  # If wind is too strong then go into safe mode at 90 elevation
            state.wind_gust_flag = True
        else:
            state.wind_gust_flag = False


def mainloop(stdscr):
    global k, conf, state

    manager = Manager()  # share the dictionaries by a manager

    k = 0  # Keypress numeric value
    conf = Config()  # Get the configuration of the tool
    state = State()  # Get the initial state of the rotor

    d = manager.dict()  # all the shared dictionaries between processes

    d['bias_az'] = conf.bias_az
    d['bias_el'] = conf.bias_el

    if conf.az_sense_active:
        p1 = Process(target=read_az, args=(d,))
        p1.start()
    if conf.el_sense_active:
        p2 = Process(target=read_el, args=(d,))
        p2.start()
    if conf.wind_check:
        p3 = Process(target=check_wind, args=(d,))
        p3.start()

    time.sleep(1)  # Wait for the processes to 'fill' the dictionaries otherwise key errors appear

    init_screen(stdscr)  # Initialise the screen

    while k != ord('q'):  # Loop where k is the last character pressed

        read_sensor(d)  # Read the input of the AMS5048B sensor

        check_command()  # Check the pressed key

        check_state()  # Check the state and whether target is achieved

        update_screen(stdscr)  # Update the screen with new State

        k = stdscr.getch()  # Get next user input

    if conf.az_sense_active:
        p1.terminate()
    if conf.el_sense_active:
        p2.terminate()
    if conf.wind_check:
        p3.terminate()


def main():
    curses.wrapper(mainloop)


if __name__ == "__main__":
    main()
