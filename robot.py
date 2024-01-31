# import RPi.GPIO as GPIO
import RPi.GPIO as GPIO
import os
import serial
from time import sleep          # this lets us have a time delay
from typing import NamedTuple
from struct import *
import sys
import logging


class Params(NamedTuple):
    lin: float
    ang: float
    hold: int


BOOT0 = 19  # gpio19
RESET = 26  # gpio26


def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BOOT0, GPIO.OUT)
    GPIO.setup(RESET, GPIO.OUT)

    GPIO.output(BOOT0, 0) # Normal flash boot
    GPIO.output(RESET, 1) # Normal running state


class Hand:

    def __init__(self, tty, br, num):
        self.tty = tty
        self.ser = serial.Serial(tty, br)
        self.ser.timeout = 0.5
        self.params = Params(0.0, 0, 0)
        self.num = num

    def stop(self):
        print("stop")
        logging.error("Stop")
        p = pack('@ffi', 0.0, 0.0, 25)
        print(p)
        logging.error("send: " + str(p) + "\n")
        self.ser.write(p)

        tdata = self.ser.read(12)
        if (tdata):
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("Some error occured while stopping the hand")
                return -1
            return 1
        else:
            logging.error("No response from the hand")
            return -1

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
        logging.error("send: " + str(p) + "\n")
        print(p)

        self.ser.write(p)

        self.ser.timeout = 12
        tdata = self.ser.read(12)
        self.ser.timeout = 0.5
        if tdata:
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("Some error occured while moving the hand")
                return -1
            print('okie!')
            return 1
        else:
            logging.error("No response from the hand")
            return -1

        # print(p)

    def get(self):
        # flag = False
        self.clear_inWaiting()
        p = pack('@ffi', 0.0, 0.0, 50)
        logging.error("send: " + str(p))
        print(p)

        self.ser.write(p)
        tdata = self.ser.read(12)  # Wait forever for anything
        print("------")
        print(tdata)
        print("---")
        if tdata:
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            logging.error("lin: "+str(LS2[0])+"; ang: "+str(LS2[1])+"; hold: "+str(LS2[2])+ "\n")
            print("lin: "+str(LS2[0])+"; ang: "+str(LS2[1])+"; hold: "+str(LS2[2]))
            return LS2
        else:
            logging.error("Timeout reading Serial")
            print("Timeout reading Serial")
            return [-1]

    def setPos(self, l, a, h):
        # not used
        print("set zero position")
        # send cmd to stm to set proper zero
        self.params = Params(l, a, h)

    def setZeroPos(self):
        logging.error("Set zero position")
        print("! set zero position")
        self.clear_inWaiting()
        p = pack('@ffi', 0.0, 0.0, 75)
        logging.error("send: " + str(p) + "\n")
        print(p)
        self.ser.write(p)

        tdata = self.ser.read(12)
        if tdata:
            print(tdata)
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("an error occurred when setting zero position")
                print("an error occurred when setting zero position")
                return -1
        else:
            print("No answer recieved")
            return -1

    def reboot(self, url):
        print("reboot")
        logging.error("Reboot")
        self.clear_inWaiting()
        '''p = pack('@ffi', 0.0, 0.0, 25)
        logging.error("send: " + str(p))
        logging.error("")
        print(p)
        self.ser.write(p)

        tdata = self.ser.read(12)
        unpacked_struct = unpack('@ffi', tdata)
        LS2 = list(unpacked_struct)
        if LS2[2]!=10:
            logging.error("an error occurred when stopping the hand")
            print("an error occurred when stopping the hand")
            return -1'''
        #url = "https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/led_toggle.bin?raw=true" #TEST .BIN
        os.system("wget -q -O stmfirmware"+str(self.num)+".bin "+url)

        bin_file = "stmfirmware"+str(self.num)+".bin"
        print(bin_file)
        GPIO.output(BOOT0, 1) # Boot from serial
        GPIO.output(RESET, 0) # reset
        sleep(0.1)
        GPIO.output(RESET, 1)
        sleep(0.5)

        os.system(str("stm32flash "+self.tty))
        sleep(1)
        os.system(str("stm32flash -w stmfirmware"+str(self.num)+".bin "+self.tty))

        sleep(0.1)
        GPIO.output(BOOT0, 0)  # boot from flash
        GPIO.output(RESET, 0)  # reset
        sleep(0.1)
        GPIO.output(RESET, 1)

    def clear_inWaiting(self):
        if self.ser.inWaiting():
            self.ser.read(self.ser.inWaiting())