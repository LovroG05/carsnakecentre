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



parser = configparser.ConfigParser()

with open('config.ini', "r") as config:
    parser.read_file(config)

STEERING_VALUE = 0
GAS_VALUE = 0
BRAKE_VALUE = 0
DIRECTION = int(parser.get('CAR', 'direction'))

FRAMEPATH = parser.get('MISC', 'framepath')

MAT, DIST, RVECS, TVECS = calibrate()


class ControllerThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "ControllerThread"

    def run(self):
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION
        print("Starting " + self.name)

        device = evdev.InputDevice(parser.get('DEVICE', 'device'))

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
                        old_steering = event.value
                        STEERING_VALUE = event.value
                        print(f"STEERING: %i" % event.value)

                if event.code == GAS_AXLE:
                    if event.value - old_gas > GAS_EVENT_MARGIN or event.value - old_gas < -GAS_EVENT_MARGIN:
                        old_gas = event.value
                        GAS_VALUE = event.value
                        print(f"GAS: %i" % event.value)

                if event.code == BRAKE_AXLE:
                    if event.value - old_brake > BRAKE_EVENT_MARGIN or event.value - old_brake < -BRAKE_EVENT_MARGIN:
                        old_brake = event.value
                        BRAKE_VALUE = event.value
                        print(f"BRAKE: %i" % event.value)

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
            


ctrlThread = ControllerThread(1).start()

cam = parser.get("CAR", "camera_url")

if cam == "0":
    cam = 0

camera = cv2.VideoCapture(cam)

while camera.isOpened():
    ret, frame = camera.read()
    cv2.namedWindow("preview", cv2.WINDOW_NORMAL)
    print("saving frame")
    SaveThread(randint(0, 9999), frame).start()
    
    print("showing frame")
    cv2.imshow('preview', frame)
    cv2.waitKey(1)
    

camera.release()
cv2.destroyAllWindows()