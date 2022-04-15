import evdev
import configparser
import cv2
import threading
import time
from csv import writer
from random import randint



parser = configparser.ConfigParser()

with open('config.ini', "r") as config:
    parser.read_file(config)

STEERING_VALUE = 0
GAS_VALUE = 0
BRAKE_VALUE = 0
DIRECTION = int(parser.get('CAR', 'direction'))

FRAMEPATH = parser.get('MISC', 'framepath')



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


class CameraThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "CameraThread"

    def run(self):
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION, FRAMEPATH
        print("Starting " + self.name)

        camera = cv2.VideoCapture(0)

        while True:
            ret, frame = camera.read()
            SaveThread(randint(0, 9999), frame).start()
            
            # image = cv2.putText(frame, "STEERING: " + str(STEERING_VALUE), (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # image = cv2.putText(frame, "GAS: " + str(GAS_VALUE), (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # image = cv2.putText(frame, "BRAKE: " + str(BRAKE_VALUE), (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # image = cv2.putText(frame, "DIRECTION: " + str(DIRECTION), (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        camera.release()
        cv2.destroyAllWindows()

        print("Exiting " + self.name)
        
        
class SaveThread(threading.Thread):
    def __init__(self, threadID, frame):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "SaveThread"
        self.frame = frame
        
    def run(self):
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION, FRAMEPATH
        t = time.time()
        cv2.imwrite(FRAMEPATH + str(t) + ".jpg", self.frame)
        with open("framedata.csv", "a") as file:
            writer_ = writer(file, delimiter=',', quotechar='"')
            writer_.writerow([FRAMEPATH + str(t) + ".jpg", str(STEERING_VALUE), str(GAS_VALUE), str(BRAKE_VALUE), str(DIRECTION)])
            file.close()
            


ctrlThread = ControllerThread(1).start()
camThread = CameraThread(2).start()