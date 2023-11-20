# import RPi.GPIO as GPIO
import OPi.GPIO as GPIO
import os
import serial
from time import sleep          # this lets us have a time delay
from typing import NamedTuple
from struct import *
import sys


class Params(NamedTuple):
    lin: float
    ang: float
    hold: int

BOOT0 = GPIO.PA + 10  # pa.10
RESET = GPIO.PA + 20  # pa.20

def setupGPIO():
    GPIO.setboard(GPIO.PCPCPLUS)
    GPIO.setmode(GPIO.SOC)
    GPIO.setup(BOOT0, GPIO.OUT)
    GPIO.setup(RESET, GPIO.OUT)

    GPIO.output(BOOT0, 0) # Normal flash boot
    #    GPIO.output(RESET, 1) # Normal running state

class Hand:

    def __init__(self, tty, br):
        self.ser = serial.Serial(tty, br)
        self.params = Params(0.0, 0, 0)

    # ser = serial.Serial('/dev/ttyS3', 115200)
    # hand = [Params(0.0, 0, 0) for i in range(3)]

    # lin1 = 0.0
    # ang1 = 0.0
    # hold1 = 0.0
    #
    # lin2 = 0.0
    # ang2 = 0.0
    # hold2 = 0.0
    #
    # lin3 = 0.0
    # ang3 = 0.0
    # hold3 = 0.0


    # def stopHands(self):
    #     self.stopHand(0)
    #     self.stopHand(1)
    #     self.stopHand(2)
        # wait for synchr?

    def stop(self):
        print("stop")

    def start(self):
        print("start")
        l = self.params.lin
        a = self.params.ang
        h = self.params.hold
        print(l)
        # https://docs.python.org/3/library/struct.html#examples
        # Format Characters
        # @  === native
        # f  === float
        # i  === int
        p = pack('@ffi', l, a, h)
        print(p)
        print(calcsize('@ffi'))

        s = str(int(l * 100)) + str(int(a * 100)) + str(h)
        print(sys.getsizeof(s))

        self.ser.write(p)
        print(p)

    def get(self):
        flag = False
        p = pack('@ffi', 0.0, 0.0, 50)
        print(p)
        self.ser.write(p)
        tdata = self.ser.read()  # Wait forever for anything
        sleep(1)  # Sleep (or inWaiting() doesn't give the correct value)
        data_left = self.ser.inWaiting()  # Get the number of characters ready to be read
        tdata += self.ser.read(data_left)
        print("------")
        print(tdata)
        print("---")
        data_l, data_a, data_h= unpack('@ffi', tdata)
        print(str(data_l)+" "+str(data_a)+" "+str(data_h))

    def setPos(self, l, a, h):
        print("set zero position")
        # send cmd to stm to set proper zero
        self.params = Params(l, a, h)

    def setZeroPos(self):
        print("set zero position")
        # send cmd to stm to set proper zero
        self.params = Params(0.0, 0.0, 0)

    def reboot(self):
        print("reboot")
        url = "https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/led_toggle.bin?raw=true" #TEST .BIN
        os.system("wget -q -O stmfirmware.bin "+url)

        bin_file = "stmfirmware.bin"
        print(bin_file)
        #setupGPIO()
        GPIO.output(self.BOOT0, 1) # Boot from serial
        GPIO.output(self.RESET, 0) # reset
        sleep(0.1)
        GPIO.output(self.RESET, 1)
        sleep(0.5)

        os.system("stm32flash /dev/ttyS3")
        sleep(1)
        os.system("stm32flash -w stmfirmware.bin /dev/ttyS3")

        sleep(0.1)
        GPIO.output(self.BOOT0, 0) # boot from flash
        GPIO.output(self.RESET, 0) # reset
        sleep(0.1)
        GPIO.output(self.RESET, 1)