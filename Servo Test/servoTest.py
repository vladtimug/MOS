from adafruit_servokit import ServoKit
import time
import argparse

parser  = argparse.ArgumentParser()
parser.add_argument('servo', help = "Servo ID: 0-Tilt, 1-Pan", type = int)
parser.add_argument('angle', help = "Target angle using absolute positioning.", type = int)
args = parser.parse_args()

# value set for channels variable must be the same as the number of aavailable dommunication channels found on the driver
myKit = ServoKit(channels=16)

# value set for motrNumber variable must reflect the number of the communication channel on the driver the servo is connected to
if args.servo == 0:
    motorNumber = 15
    print('Motor number ', motorNumber)
if args.servo == 1:
    motorNumber = 14 
    print('Motor number ', motorNumber)
if args.servo == 2:
    motorNumber = 3
    print('Motor number ', motorNumber)
myKit.servo[motorNumber].angle = args.angle