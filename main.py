import configparser
import cv2
from random import randint
import numpy as np
from camera_calibration import calibrate
from copy import copy
import math
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
#from control import *
from saver import SaveThread
from interactions import *




parser = configparser.ConfigParser()

with open('config.ini', "r") as config:
    parser.read_file(config)

STEERING_VALUE = 0
GAS_VALUE = 0
BRAKE_VALUE = 0
DIRECTION = int(parser.get('CAR', 'direction'))
IP = parser.get('CAR', 'ip')
print(IP)

FRAMEPATH = parser.get('MISC', 'framepath')

#MAT, DIST, RVECS, TVECS = calibrate()

IN1 = parser.get("DEVICE", "in1")
IN2 = parser.get("DEVICE", "in2")
EN = parser.get("DEVICE", "en")


# Defining variables to hold meter-to-pixel conversion
ym_per_pix = 0.2 / 80
# Standard lane width is 3.7 meters divided by lane width in pixels which is
# calculated to be approximately 720 pixels not to be confused with frame height
xm_per_pix = 0.18 / 363  

# keyboard = False
# devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
# if len(devices) > 0:
#     for i in range(len(devices)):
#         print(i, devices[i].name)
        
#     DEVICE = devices[int(input("device number>>> "))]
#     print("Selected device: ", DEVICE.name)
#     SteeringWheelThread(randint(0, 9999), IP, EN, IN1, IN2, DEVICE, parser).start()
# else:
#     keyboard = True
#     print("Controls set to keyboard - requires sudo")
#     KeyboardThread(randint(0, 9999), IP, EN, IN1, IN2).start()




cam = parser.get("CAR", "camera_url")

if cam == "0":
    cam = 0
    
print(cam)

factory = PiGPIOFactory(host=IP)
servo = AngularServo(17, min_angle=40, max_angle=100, frame_width=0.02, initial_angle=72, pin_factory=factory)
throttle = PWMOutputDevice(EN, frequency=1000, pin_factory=factory)
in1 = DigitalOutputDevice(IN1, pin_factory=factory, initial_value=True)
in2 = DigitalOutputDevice(IN2, pin_factory=factory, initial_value=False)



weird_left_angle = False
weird_right_angle = False


cam = cv2.VideoCapture(cam)


    
while True:
    ret, frame = cam.read()
    doThrottle(throttle, in1, in2, 0.2)
    if ret:
        
        img = copy(frame)
        
        ROI = img[200:280, 0:480]
        
        greyframe = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
        newframe = cv2.cvtColor(ROI, cv2.COLOR_BGR2HSV)
        low_blue = np.array([110, 50, 50])
        upper_blue = np.array([130, 255, 255])
        
        mask = cv2.inRange(newframe, low_blue, upper_blue)
        
        res = cv2.bitwise_and(newframe, newframe, mask=mask)

        
        newframe = cv2.blur(res, (5, 5), 0)
        canny = cv2.Canny(newframe, 50, 150, apertureSize=3)
        
        canny2 = copy(canny) 
        h, w = canny2.shape[:2]
        
        upper_row = canny2[10]
        lower_row = canny2[79]
        
        left_upper_x = 0
        left_lower_x = 0
        
        right_upper_x = 0
        right_lower_x = 0
        # first check from l to r for white pixel coords
        for x in range(0, len(upper_row)):
            if upper_row[x] == 255:
                left_upper_x = x
                break
            
        for x in range(0, len(lower_row)):
            if lower_row[x] == 255:
                left_lower_x = x
                break
            
        # then check from r to l for white pixel coords
        for x in range(len(upper_row)-1, 0, -1):
            if upper_row[x] == 255:
                right_upper_x = x
                break
            
        for x in range(len(lower_row)-1, 0, -1):
            if lower_row[x] == 255:
                right_lower_x = x
                break
            
        cv2.line(img, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(img, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(canny2, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(canny2, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(res, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(res, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
        
        try:
            left_angle = int(math.atan((10-79)/(left_upper_x-left_lower_x)) * 180 / math.pi)
            weird_left_angle = False
        except ZeroDivisionError:
            print("left line not detected")
            weird_left_angle = True
            left_angle = 0
        
        try:
            right_angle = int(math.atan((10-79)/(right_upper_x-right_lower_x)) * 180 / math.pi)
            weird_right_angle = False
        except ZeroDivisionError:
            print("right line not detected")
            weird_right_angle = True
            right_angle = 0
        
        try: 
            servo.angle = camAngle(left_angle, right_angle, weird_left_angle, weird_right_angle)
            print(servo.angle)
        except ZeroDivisionError:
            break
        
        cv2.imshow('actual image', img) # display image while receiving data
        cv2.imshow('the resemblence is unCANNY', canny2) # display image while receiving data
        cv2.imshow('res', res) # display image while receiving data
        if cv2.waitKey(1) == 27: # if user hit esc            
            break
        
doThrottle(throttle, in1, in2, 0)
cv2.destroyAllWindows()