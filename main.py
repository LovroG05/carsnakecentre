import evdev

device = evdev.InputDevice('/dev/input/event256')

STEERING_EVENT_MARGIN = 5
GAS_EVENT_MARGIN = 20
BRAKE_EVENT_MARGIN = 20

STEERING_AXLE = evdev.ecodes.ABS_RY
GAS_AXLE = evdev.ecodes.ABS_Y
BRAKE_AXLE = evdev.ecodes.ABS_Z

old_steering = 0
old_gas = 0
old_brake = 0

direction = 1 # 0: backwards, 1: forward


for event in device.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        if event.code == evdev.ecodes.BTN_THUMB2:
            direction = 1
            print("changing direction to forward")
        elif event.code == evdev.ecodes.BTN_PINKIE:
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