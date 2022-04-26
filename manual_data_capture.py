from turtle import dot
import keyboard
import configparser
import cv2
import threading
import time
from csv import writer
from random import randint
import numpy as np
from camera_calibration import calibrate
import sys
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from time import sleep
from copy import copy, deepcopy
import urllib.request
import math


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

# devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
# for i in range(len(devices)):
#     print(i, devices[i].name)
    
# DEVICE = devices[int(input("device number>>> "))]
# print("Selected device: ", DEVICE.name)


class ControllerThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "ControllerThread"
        factory = PiGPIOFactory(host=IP)
        self.servo = AngularServo(17, min_angle=40, max_angle=100, frame_width=0.02, initial_angle=72, pin_factory=factory)
        self.throttle = PWMOutputDevice(EN, frequency=1000, pin_factory=factory)
        self.in1 = DigitalOutputDevice(IN1, pin_factory=factory, initial_value=True)
        self.in2 = DigitalOutputDevice(IN2, pin_factory=factory, initial_value=False)

    def run(self):
        print("Starting " + self.name)

        STEERING_EVENT_MARGIN = int(parser.get('DEVICE', 'steering_margin'))
        GAS_EVENT_MARGIN = int(parser.get('DEVICE', 'gas_margin'))
        BRAKE_EVENT_MARGIN = int(parser.get('DEVICE', 'brake_margin'))

        # STEERING_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'steering_axle')]
        # GAS_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'gas_axle')]
        # BRAKE_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'brake_axle')]

        # FORWARD = evdev.ecodes.ecodes[parser.get('DEVICE', 'forward_button')]
        # REVERSE = evdev.ecodes.ecodes[parser.get('DEVICE', 'reverse_button')]

        old_steering = 0
        old_gas = 0
        old_brake = 0
        
        gas_changed = False
        brake_changed = False


        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == "w":
                    doThrottle(self.throttle, self.in1, self.in2, 0.5)
                if event.name == "s":
                    doThrottle(self.throttle, self.in1, self.in2, -0.5)
                if event.name == "a":
                    self.servo.angle = 50
                if event.name == "d":
                    self.servo.angle = 90
                if event.name == "q":
                    break
            if event.event_type == keyboard.KEY_UP:
                if event.name == "w" or event.name == "s":
                    doThrottle(self.throttle, self.in1, self.in2, 0)
                if event.name == "a" or event.name == "d":
                    self.servo.angle = 72
                    

        print("Exiting " + self.name)
        sys.exit()
        
        
class SaveThread(threading.Thread):
    def __init__(self, threadID, frame):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "SaveThread"
        self.frame = frame
        
    def run(self):
        print("Starting " + self.name + ": " + str(self.threadID))
        #h,  w = self.frame.shape[:2]
        #newcameramtx, roi=cv2.getOptimalNewCameraMatrix(MAT, DIST, (w, h), 1, (w, h))
        #dst = cv2.undistort(self.frame, MAT, DIST, None, newcameramtx)
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION, FRAMEPATH
        t = time.time()
        cv2.imwrite(FRAMEPATH + str(t) + ".jpg", self.frame)
        with open("framedata.csv", "a") as file:
            writer_ = writer(file, delimiter=',', quotechar='"')
            writer_.writerow([FRAMEPATH + str(t) + ".jpg", str(STEERING_VALUE), str(GAS_VALUE), str(BRAKE_VALUE), str(DIRECTION)])
            file.close()
            
        print("Exiting " + self.name + ": " + str(self.threadID))
        sys.exit()
        
    
def angle(input):
    return int(40 + ((100-40) / (1024 - 1)) * (input - 1))

def drawingAngle(input):
    return int(((-40-40) / (100-40)) * (input - 40) + 40)

def doThrottle(en, in1, in2, value=0):    
    if abs(value) < 0.1:
        in1.off()
        in2.off()
        en.value = 0
    elif value < 0:
        in1.on()
        in2.off()
        en.value = abs(value)
    elif value > 0:
        in1.off()
        in2.on()
        en.value = value
            


ctrlThread = ControllerThread(1).start()

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
        total_bytes= total_bytes[b+2:] # other informations
        
        # decode to colored image ( another option is cv2.IMREAD_GRAYSCALE )
        img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR) 
        newframe = copy(img) 
        newframe3 = copy(img)
        
        
        #ROI = 
        
        newframe = cv2.cvtColor(newframe, cv2.COLOR_BGR2GRAY)
        newframe = cv2.blur(newframe, (5, 5), 0)
        canny = cv2.Canny(newframe, 50, 150, apertureSize=3)
        #cv2.imshow("canny", canny)
        
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
        if cv2.waitKey(1) ==27: # if user hit esc            
            break
cv2.destroyWindow('Window name')