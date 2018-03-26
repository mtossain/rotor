import smbus
import time
from math import sin,cos,atan2,pi
import numpy as np

bus = smbus.SMBus(1)
address_az = 0x40
address_el = 0x41
resolution = 16384.0
len_avg    = 100

def mean_angle(angles,weights=0,setting='degrees'):
    '''computes the mean angle'''
    if weights==0:
         weights=np.ones(len(angles))
    sumsin=0
    sumcos=0
    if setting=='degrees':
        angles=np.array(angles)*pi/180
    for i in range(len(angles)):
        sumsin+=weights[i]/sum(weights)*sin(angles[i])
        sumcos+=weights[i]/sum(weights)*cos(angles[i])
    average=atan2(sumsin,sumcos)
    if setting=='degrees':
        average=average*180/pi
    return average


buffer = [0,1,2,3,4,5]
angles_az = np.zeros(len_avg)
angles_el = np.zeros(len_avg)
 
while True:

  for i in range(len_avg):

    for j in range(6):
      buffer[j] = bus.read_byte_data(address_az, 0xFA+j);

    AGC_az       = buffer[0];
    MAG_az       = (buffer[2]<<6)+(buffer[3]&0x3F);
    ANG_az       = (buffer[4]<<6)+(buffer[5]&0x3F);
    angle_az     = ANG_az/resolution*360
    angles_az[i] = angle_az

    for j in range(6):
      buffer[j] = bus.read_byte_data(address_el, 0xFA+j);

    AGC_el       = buffer[0];
    MAG_el       = (buffer[2]<<6)+(buffer[3]&0x3F);
    ANG_el       = (buffer[4]<<6)+(buffer[5]&0x3F);
    angle_el     = ANG_el/resolution*360
    angles_el[i] = angle_el

  avg_angle_az = mean_angle(angles_az,0,'degrees')
  avg_angle_el = mean_angle(angles_el,0,'degrees')

  #print('Angle az: '+str(round(avg_angle_az,2))+' [deg]')
  print('Angle el: '+str(round(avg_angle_el,2))+' [deg]')

  #print('Magnitude  az: '+str(round(MAG_az,2))+' [-]')
  print('Magnitude  el: '+str(round(MAG_el,2))+' [-]')

  #print('AGC az: '+str(round(AGC_az,2))+' [-]')
  #print('AGC el: '+str(round(AGC_el,2))+' [-]')
  
  time.sleep(3)


