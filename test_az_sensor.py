################################################################################
# Read heading and magnitude angles from AMS5048B Sensor
# 2018 M. Tossaint
################################################################################

import smbus
import time
from math import sin,cos,atan2,pi
import numpy as np
from read_heading import *

print('Azimuth angle: '+str(read_az_ang()))
print('Azimuth  magnitude: '+str(read_az_mag()))
