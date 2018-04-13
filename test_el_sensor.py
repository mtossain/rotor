################################################################################
# Read heading and magnitude angles from AMS5048B Sensor
# 2018 M. Tossaint
################################################################################

import smbus
import time
from math import sin,cos,atan2,pi
import numpy as np
from read_heading import *

print('Elevation angle: '+str(read_el_ang()))
print('Elevation magnitude: '+str(read_el_mag()))
