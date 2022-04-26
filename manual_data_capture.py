import configparser
import cv2
from random import randint
import numpy as np
from camera_calibration import calibrate
from copy import copy
import urllib.request
import math
from control import *
from saver import SaveThread
from interactions import *
import evdev


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

MAT, DIST, RVECS, TVECS = calibrate()

IN1 = parser.get("DEVICE", "in1")
IN2 = parser.get("DEVICE", "in2")
EN = parser.get("DEVICE", "en")

keyboard = False
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
if len(devices) > 0:
    for i in range(len(devices)):
        print(i, devices[i].name)
        
    DEVICE = devices[int(input("device number>>> "))]
    print("Selected device: ", DEVICE.name)
else:
    keyboard = True
    print("Controls set to keyboard")
    


# TODO: if no device pick keyboard

cam = parser.get("CAR", "camera_url")

if cam == "0":
    cam = 0
    
print(cam)



stream = urllib.request.urlopen(cam)
total_bytes = b""
while True:
    total_bytes += stream.read(1024)
    b = total_bytes.find(b'\xff\xd9') # JPEG end
    if not b == -1:
        a = total_bytes.find(b'\xff\xd8') # JPEG start
        jpg = total_bytes[a:b+2] # actual image
        total_bytes = total_bytes[b+2:] # other informations
        
        img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR) 
        newframe = copy(img) 
        newframe3 = copy(img)
        
        newframe = cv2.cvtColor(newframe, cv2.COLOR_BGR2GRAY)
        newframe = cv2.blur(newframe, (5, 5), 0)
        canny = cv2.Canny(newframe, 50, 150, apertureSize=3)
        
        canny2 = copy(canny) 
        h, w = canny2.shape[:2]
        
        ROI = np.array([[0, 200], [w, 200], [0, 360], [w, 360]])
        
        blank = np.zeros_like(canny2)
        roi = cv2.fillPoly(blank, [ROI], 255)
        roiimg = cv2.bitwise_and(canny2, roi)
        
        upper_row = canny2[220]
        lower_row = canny2[350]
        
        left_upper_x = 0
        left_lower_x = 0
        
        right_upper_x = 0
        left_upper_x = 0
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
            
        cv2.line(img, (left_upper_x, 220), (left_lower_x, 350), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(img, (right_upper_x, 220), (right_lower_x, 350), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(canny2, (left_upper_x, 220), (left_lower_x, 350), (255,255,0), 3, cv2.LINE_AA)
        cv2.line(canny2, (right_upper_x, 220), (right_lower_x, 350), (255,255,0), 3, cv2.LINE_AA)
        
        left_angle = int(math.atan((220-350)/(left_upper_x-left_lower_x)) * 180 / math.pi)
        right_angle = int(math.atan((220-350)/(right_upper_x-right_lower_x)) * 180 / math.pi)
        
        print(left_angle, right_angle)
        
        cv2.imshow('Window name3', img) # display image while receiving data
        cv2.imshow('Window name4', canny2) # display image while receiving data
        if cv2.waitKey(1) == 27: # if user hit esc            
            break
        
        
cv2.destroyWindow('Window name')