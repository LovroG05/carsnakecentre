import evdev
import configparser
import cv2
import threading


STEERING_VALUE = 0
GAS_VALUE = 0
BRAKE_VALUE = 0
DIRECTION = 1

parser = configparser.ConfigParser()

with open('config.ini', "r") as config:
    parser.read_file(config)


class ControllerThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "ControllerThread"

    def run(self):
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

        direction = int(parser.get('CAR', 'direction')) # 0: backwards, 1: forward


        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                if event.code == FORWARD:
                    direction = 1
                    DIRECTION = 1
                    print("changing direction to forward")
                elif event.code == REVERSE:
                    direction = 0
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
        print("Starting " + self.name)

        camera = cv2.VideoCapture()

        while True:
            ret, frame = camera.read()
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        camera.release()
        cv2.destroyAllWindows()

        print("Exiting " + self.name)


threads = []

ctrlThread = ControllerThread(1)
threads.append(ctrlThread)
camThread = CameraThread(2)
threads.append(camThread)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
