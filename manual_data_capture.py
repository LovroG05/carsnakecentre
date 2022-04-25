import evdev
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

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for i in range(len(devices)):
    print(i, devices[i].name)
    
DEVICE = devices[int(input("device number>>> "))]
print("Selected device: ", DEVICE.name)


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
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION
        print("Starting " + self.name)

        device = evdev.InputDevice(DEVICE)

        STEERING_EVENT_MARGIN = int(parser.get('DEVICE', 'steering_margin'))
        GAS_EVENT_MARGIN = int(parser.get('DEVICE', 'gas_margin'))
        BRAKE_EVENT_MARGIN = int(parser.get('DEVICE', 'brake_margin'))

        STEERING_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'steering_axle')]
        GAS_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'gas_axle')]
        BRAKE_AXLE = evdev.ecodes.ecodes[parser.get('DEVICE', 'brake_axle')]

        FORWARD = evdev.ecodes.ecodes[parser.get('DEVICE', 'forward_button')]
        REVERSE = evdev.ecodes.ecodes[parser.get('DEVICE', 'reverse_button')]

        old_steering = 0
        old_gas = 0
        old_brake = 0
        
        gas_changed = False
        brake_changed = False


        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                if event.code == FORWARD:
                    DIRECTION = 1
                    print("changing direction to forward")
                elif event.code == REVERSE:
                    DIRECTION = 0
                    print("changing direction to backward")

            elif event.type == evdev.ecodes.EV_ABS:
                if event.code == STEERING_AXLE:
                    if event.value - old_steering > STEERING_EVENT_MARGIN or event.value - old_steering < -STEERING_EVENT_MARGIN:
                        old_steering = angle(event.value)
                        STEERING_VALUE = angle(event.value)
                        print(f"STEERING: %i" % STEERING_VALUE)
                        if STEERING_VALUE <= 100:
                            self.servo.angle = STEERING_VALUE
                        elif STEERING_VALUE >= 40:
                            self.servo.angle = STEERING_VALUE

                if event.code == GAS_AXLE:
                    if event.value - old_gas > GAS_EVENT_MARGIN or event.value - old_gas < -GAS_EVENT_MARGIN:
                        old_gas = event.value
                        GAS_VALUE = event.value
                        print(f"GAS: %i" % event.value)
                        gas_changed = True
                    else:
                        gas_changed = False

                if event.code == BRAKE_AXLE:
                    if event.value - old_brake > BRAKE_EVENT_MARGIN or event.value - old_brake < -BRAKE_EVENT_MARGIN:
                        old_brake = event.value
                        BRAKE_VALUE = event.value
                        print(f"BRAKE: %i" % event.value)
                        brake_changed = True
                    else:
                        brake_changed = False
                        
                
                if (brake_changed or gas_changed):
                    doThrottle(self.throttle, self.in1, self.in2)
                    

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
        h,  w = self.frame.shape[:2]
        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(MAT, DIST, (w, h), 1, (w, h))
        dst = cv2.undistort(self.frame, MAT, DIST, None, newcameramtx)
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION, FRAMEPATH
        t = time.time()
        cv2.imwrite(FRAMEPATH + str(t) + ".jpg", dst)
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

def doThrottle(en, in1, in2):
    global GAS_VALUE, BRAKE_VALUE
    g = int(20 + ((650-20)/(20-650))*(GAS_VALUE-650))
    b = int(20 + ((540-20)/(20-540))*(BRAKE_VALUE-540))
    
    value = (g - b) / 1000
    print(g, b, value)
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
    
width = 1280
height = 960
dim = (width, height)

camera = cv2.VideoCapture(cam)

cv2.namedWindow("preview", cv2.WINDOW_NORMAL)
cv2.resizeWindow("preview", width, height)



while camera.isOpened():
    ret, frame = camera.read()
    
    print("saving frame")
    SaveThread(randint(0, 9999), frame).start()
    
    newframe = copy(frame)
    newframe = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
    
    
    box = cv2.boxPoints(((320, 360), (30, 60), float(drawingAngle(STEERING_VALUE))))
    box = np.int0(box)
    cv2.drawContours(newframe, [box], 0, (0, 255, 0), 2)
    
    cv2.imshow('preview', newframe)
    cv2.waitKey(1)
    

camera.release()
cv2.destroyAllWindows()