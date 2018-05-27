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

def compute_azel_from_radec(config):

    home = ephem.Observer()
    home.lat = str(config.rotor_lat) # +N
    home.lon = str(config.rotor_lon)  # +E
    home.elevation = config.rotor_alt # meters
    home.date = dt.datetime.utcnow()

    star = ephem.FixedBody()
    star._ra = str(config.goto_ra) # 16.7
    star._dec = str(config.goto_dec) # 90.0

    star.compute(home)

    return r2d(float(star.az)), r2d(float(star.alt))

def compute_azel_from_planet(config):

    home = ephem.Observer()
    home.lon = str(config.rotor_lon)  # +E
    home.lat = str(config.rotor_lat) # +N
    home.elevation = config.rotor_alt # meters
    home.date = dt.datetime.utcnow() # +dt.timedelta(hours=21)

    if config.track_planet.lower() == 'sun':
        planet = ephem.Sun(home)
    if config.track_planet.lower() == 'moon':
        planet = ephem.Moon(home)
    if config.track_planet.lower() == 'mercury':
        planet = ephem.Mercury(home)
    if config.track_planet.lower() == 'venus':
        planet = ephem.Venus(home)
    if config.track_planet.lower() == 'mars':
        planet = ephem.Mars(home)
    if config.track_planet.lower() == 'jupiter':
        planet = ephem.Jupiter(home)
    if config.track_planet.lower() == 'saturn':
        planet = ephem.Saturn(home)
    if config.track_planet.lower() == 'uranus':
        planet = ephem.Uranus(home)
    if config.track_planet.lower() == 'neptune':
        planet = ephem.Neptune(home)
    planet.compute(home)

    return r2d(float(planet.az)), r2d(float(planet.alt))

def compute_azel_from_tle(config):

    home = ephem.Observer()
    home.lon = str(config.rotor_lon)  # +E
    home.lat = str(config.rotor_lat) # +N
    home.elevation = config.rotor_alt # meters
    home.date = dt.datetime.utcnow()

    f = open(config.track_sat_tle, 'r')
    tle_lines = f.read().decode(encoding='utf-8',errors='ignore').split("\n")[0:3]
    tle = ephem.readtle(str(tle_lines[0]),str(tle_lines[1]),str(tle_lines[2]))

    tle.compute(home)

    return r2d(float(tle.az)), r2d(float(tle.alt))
