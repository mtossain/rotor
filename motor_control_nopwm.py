################################################################################
# Drive motors for rotor control
# 2018 M. Tossaint
################################################################################

from gpiozero import Motor
from time import sleep

# Motor A, az Side GPIO CONSTANTS
PWM_FORWARD_az_PIN = 26	# IN1 - Forward Drive
PWM_REVERSE_az_PIN = 19	# IN2 - Reverse Drive

# Motor B, el Side GPIO CONSTANTS
PWM_FORWARD_el_PIN = 13	# IN1 - Forward Drive
PWM_REVERSE_el_PIN = 6	# IN2 - Reverse Drive

# Initialise objects for H-Bridge PWM pins
# Set initial duty cycle to 0 and frequency to 1000
motor_az = Motor(forward=PWM_FORWARD_az_PIN, backward=PWM_REVERSE_az_PIN, pwm=False)
motor_el = Motor(forward=PWM_FORWARD_el_PIN, backward=PWM_REVERSE_el_PIN, pwm=False)

def stop_az():
	motor_az.stop()

def stop_el():
	motor_el.stop()

def for_az():
	motor_az.forward()

def for_el():
	motor_el.forward()

def rev_az():
	motor_az.backward()

def rev_el():
	motor_el.backward()
