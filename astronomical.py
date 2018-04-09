################################################################################
# Astronomical routines
# 2018 M. Tossaint
################################################################################
import ephem
import math
import datetime as dt

r2d = math.degrees
d2r = math.radians
pi = math.pi

def compute_azel_from_radec(state):

    home = ephem.Observer()
    home.lon = str(-state.rotor_lon)  # +E
    home.lat = str(state.rotor_lat) # +N
    home.elevation = str(state.rotor_alt) # meters
    home.date = dt.datetime.utcnow()

    star = ephem.FixedBody()
    star._ra = ephem.degrees(str(state.ra)) # 16.7
    star._dec = ephem.degrees(str(state.dec)) # 90.0

    star.compute(observer)

    return r2d(float(star.az)), r2d(float(star.alt))

def compute_azel_from_planet(state):

    home = ephem.Observer()
    home.lon = str(-state.rotor_lon)  # +E
    home.lat = str(state.rotor_lat) # +N
    home.elevation = str(state.rotor_alt) # meters
    home.date = dt.datetime.utcnow()

    if state.track_planet.lower() == 'sun':
        planet = ephem.Sun(home)
    if state.track_planet.lower() == 'moon':
        planet = ephem.Moon(home)
    if state.track_planet.lower() == 'mercury':
        planet = ephem.Mercury(home)
    if state.track_planet.lower() == 'venus':
        planet = ephem.Venus(home)
    if state.track_planet.lower() == 'mars':
        planet = ephem.Mars(home)
    if state.track_planet.lower() == 'jupiter':
        planet = ephem.Jupiter(home)
    if state.track_planet.lower() == 'saturn':
        planet = ephem.Saturn(home)
    if state.track_planet.lower() == 'uranus':
        planet = ephem.Uranus(home)
    if state.track_planet.lower() == 'neptune':
        planet = ephem.Neptune(home)
    planet.compute(home)

    return r2d(float(planet.az)), r2d(float(planet.alt))

def compute_azel_from_tle(state):

    home = ephem.Observer()
    home.lon = str(-state.rotor_lon)  # +E
    home.lat = str(state.rotor_lat) # +N
    home.elevation = str(state.rotor_alt) # meters
    home.date = dt.datetime.utcnow()

    f = open(state.track_sat_tle, 'r')
    tle_lines = f.read().decode(encoding='utf-8',errors='ignore').split("\n")[0:3]
    tle = ephem.readtle(tle_lines[0],tle_lines[1],tle_lines[2])

    tle.compute(home)

    return r2d(float(tle.az)), r2d(float(tle.alt))
