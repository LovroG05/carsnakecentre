import evdev
import configparser

parser = configparser.ConfigParser()

with open('config.ini', "r") as config:
    parser.read_file(config)

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
            print("changing direction to forward")
        elif event.code == REVERSE:
            direction = 0
            print("changing direction to backward")

    elif event.type == evdev.ecodes.EV_ABS:
        if event.code == STEERING_AXLE:
            if event.value - old_steering > STEERING_EVENT_MARGIN or event.value - old_steering < -STEERING_EVENT_MARGIN:
                old_steering = event.value
                print(f"STEERING: %i" % event.value)

        if event.code == GAS_AXLE:
            if event.value - old_gas > GAS_EVENT_MARGIN or event.value - old_gas < -GAS_EVENT_MARGIN:
                old_gas = event.value
                print(f"GAS: %i" % event.value)

        if event.code == BRAKE_AXLE:
            if event.value - old_brake > BRAKE_EVENT_MARGIN or event.value - old_brake < -BRAKE_EVENT_MARGIN:
                old_brake = event.value
                print(f"BRAKE: %i" % event.value)