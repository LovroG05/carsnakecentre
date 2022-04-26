import keyboard
import threading
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
from interactions import doThrottle, angle
import sys
import evdev


class KeyboardThread(threading.Thread):
    def __init__(self, threadID, IP, EN, IN1, IN2):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "KeyboardThread"
        factory = PiGPIOFactory(host=IP)
        self.servo = AngularServo(17, min_angle=40, max_angle=100, frame_width=0.02, initial_angle=72, pin_factory=factory)
        self.throttle = PWMOutputDevice(EN, frequency=1000, pin_factory=factory)
        self.in1 = DigitalOutputDevice(IN1, pin_factory=factory, initial_value=True)
        self.in2 = DigitalOutputDevice(IN2, pin_factory=factory, initial_value=False)

    def run(self):
        print("Starting " + self.name)

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
        

class SteeringWheelThread(threading.Thread):
    def __init__(self, threadID, IP, EN, IN1, IN2, device, parser):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "SteeringWheelThread"
        factory = PiGPIOFactory(host=IP)
        self.servo = AngularServo(17, min_angle=40, max_angle=100, frame_width=0.02, initial_angle=72, pin_factory=factory)
        self.throttle = PWMOutputDevice(EN, frequency=1000, pin_factory=factory)
        self.in1 = DigitalOutputDevice(IN1, pin_factory=factory, initial_value=True)
        self.in2 = DigitalOutputDevice(IN2, pin_factory=factory, initial_value=False)
        self.device = evdev.InputDevice(device)
        self.parser = parser

    def run(self):
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE
        print("Starting " + self.name)


        STEERING_EVENT_MARGIN = int(self.parser.get('DEVICE', 'steering_margin'))
        GAS_EVENT_MARGIN = int(self.parser.get('DEVICE', 'gas_margin'))
        BRAKE_EVENT_MARGIN = int(self.parser.get('DEVICE', 'brake_margin'))

        STEERING_AXLE = evdev.ecodes.ecodes[self.parser.get('DEVICE', 'steering_axle')]
        GAS_AXLE = evdev.ecodes.ecodes[self.parser.get('DEVICE', 'gas_axle')]
        BRAKE_AXLE = evdev.ecodes.ecodes[self.parser.get('DEVICE', 'brake_axle')]


        old_steering = 0
        old_gas = 0
        old_brake = 0
        
        gas_changed = False
        brake_changed = False


        for event in self.device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
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