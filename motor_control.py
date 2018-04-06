################################################################################
# Drive motors for rotor control
# 2018 M. Tossaint
################################################################################

from gpiozero import PWMOutputDevice
from time import sleep

# Motor A, az Side GPIO CONSTANTS
PWM_FORWARD_az_PIN = 26	# IN1 - Forward Drive
PWM_REVERSE_az_PIN = 19	# IN2 - Reverse Drive

# Motor B, el Side GPIO CONSTANTS
PWM_FORWARD_el_PIN = 13	# IN1 - Forward Drive
PWM_REVERSE_el_PIN = 6	# IN2 - Reverse Drive

# Initialise objects for H-Bridge PWM pins
# Set initial duty cycle to 0 and frequency to 1000
forward_az = PWMOutputDevice(PWM_FORWARD_az_PIN, True, 0, 1000)
reverse_az = PWMOutputDevice(PWM_REVERSE_az_PIN, True, 0, 1000)

forward_el = PWMOutputDevice(PWM_FORWARD_el_PIN, True, 0, 1000)
reverse_el = PWMOutputDevice(PWM_REVERSE_el_PIN, True, 0, 1000)

def stop_az():
	forward_az.value = 0
	reverse_az.value = 0

def stop_el():
	forward_el.value = 0
	reverse_el.value = 0

def forward_az(duty_cycle):
	forward_az.value = duty_cycle
	reverse_az.value = 0

def forward_el(duty_cycle):
	forward_el.value = duty_cycle
	reverse_el.value = 0

def reverse_az(duty_cycle):
	forward_az.value = 0
	reverse_az.value = duty_cycle

def reverse_el(duty_cycle):
	forward_el.value = 0
	reverse_el.value = duty_cycle
