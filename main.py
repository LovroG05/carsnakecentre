import configparser
import cv2
from random import randint
import numpy as np
from camera_calibration import calibrate
from copy import copy
import math
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
from saver import SaveThread
from interactions import *
import picamera
import picamera.array
from errors import NoBlueLineException






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


factory = PiGPIOFactory()
servo = AngularServo(17, min_angle=40, max_angle=100, frame_width=0.02, initial_angle=72, pin_factory=factory)
throttle = PWMOutputDevice(EN, frequency=1000, pin_factory=factory)
in1 = DigitalOutputDevice(IN1, initial_value=True, pin_factory=factory)
in2 = DigitalOutputDevice(IN2, initial_value=False, pin_factory=factory)



weird_left_angle = False
weird_right_angle = False


cam = picamera.PiCamera()
cam.resolution = (640, 480)
cam.framerate = 30
rawCapture = picamera.array.PiRGBArray(cam, size=(640, 480))

    
for frame in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = frame.array
    doThrottle(throttle, in1, in2, 0.35)

        
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
    # first check from l to r for colored pixel coords
    for x in range(0, len(upper_row)):
        if upper_row[x] == 255:
            left_upper_x = x
            break
        
    for x in range(0, len(lower_row)):
        if lower_row[x] == 255:
            left_lower_x = x
            break
        
    # then check from r to l for colored pixel coords
    for x in range(len(upper_row)-1, 0, -1):
        if upper_row[x] == 255:
            right_upper_x = x
            break
        
    for x in range(len(lower_row)-1, 0, -1):
        if lower_row[x] == 255:
            right_lower_x = x
            break

    rawCapture.truncate()
    rawCapture.seek(0)
        
    # cv2.line(img, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    # cv2.line(img, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    # cv2.line(canny2, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    # cv2.line(canny2, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    # cv2.line(res, (left_upper_x, 10), (left_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    # cv2.line(res, (right_upper_x, 10), (right_lower_x, 79), (255,255,0), 3, cv2.LINE_AA)
    
    try:
        left_angle = int(math.atan((10-79)/(left_upper_x-left_lower_x)) * 180 / math.pi)
        weird_left_angle = False
    except ZeroDivisionError as e:
        print(e)
        weird_left_angle = True
        left_angle = 0
    
    try:
        right_angle = int(math.atan((10-79)/(right_upper_x-right_lower_x)) * 180 / math.pi)
        weird_right_angle = False
    except ZeroDivisionError as e:
        print(e)
        weird_right_angle = True
        right_angle = 0
    
    try: 
        servo.angle = camAngle(left_angle, right_angle, weird_left_angle, weird_right_angle)
        print(servo.angle)
    except NoBlueLineException as e:
        print(e)
        break
    
    # cv2.imshow('actual image', img) # display image while receiving data
    # cv2.imshow('the resemblence is unCANNY', canny2) # display image while receiving data
    # cv2.imshow('res', res) # display image while receiving data

    
    if cv2.waitKey(1) == 27: # if user hit esc            
        break
        

cam.close()
doThrottle(throttle, in1, in2, 0)
cv2.destroyAllWindows()