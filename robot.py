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


#BOOT0 = 19  # gpio19
#RESET = 26  # gpio26


def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.OUT) #BOOT0 for stm n.1
    GPIO.setup(22, GPIO.OUT) #RESET for stm n.1

    GPIO.output(27, 0) # Normal flash boot
    GPIO.output(22, 0) # Normal running state
    
    GPIO.setup(23, GPIO.OUT) #BOOT0 for stm n.2
    GPIO.setup(19, GPIO.OUT) #RESET for stm n.2

    GPIO.output(23, 0) # Normal flash boot
    GPIO.output(19, 0) # Normal running state
    
    GPIO.setup(20, GPIO.OUT) #BOOT0 for stm n.3
    GPIO.setup(16, GPIO.OUT) #RESET for stm n.3

    GPIO.output(20, 0) # Normal flash boot
    GPIO.output(16, 0) # Normal running state


class Hand:

    def __init__(self, tty, br, num, boot_pin, reset_pin):
        self.tty = tty
        self.br = br
        self.ser = serial.Serial(tty, br)
        self.ser.timeout = 0.5
        self.params = Params(0.0, 0, 0)
        self.num = num
        self.BOOT0 = boot_pin
        self.RESET = reset_pin

    def read_serial(self, bytes):
        try:
            tdata = self.ser.read(bytes)
            #print("in read")
        except serial.SerialException as e:
            #There is no new data from serial port
            logging.error("SerialException")
            return None
        except TypeError as e:
            #Disconnect of USB->UART occured
            logging.error("TypeError")
            self.ser.close()
            return None
        else:
            #Some data was received
            #print("data received")
            return tdata
    
    def stop(self):
        print("stop")
        logging.error("Stop")
        p = pack('@ffi', 0.0, 0.0, 25)
        print(p)
        #logging.error("send: " + str(p) + "\n")
        self.ser.write(p)

        #tdata = self.ser.read(12)
        tdata = self.read_serial(12)
        if (tdata):
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("Some error occured while stopping the hand "+str(self.num))
                return -1
            return 1
        else:
            logging.error("No response from the hand "+str(self.num))
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
        #logging.error("send: " + str(p) + "\n")
        print(p)

        self.ser.write(p)

        #return 1
        self.ser.timeout = 12
        #tdata = self.ser.read(12)
        tdata = self.read_serial(12)
        self.ser.timeout = 0.5
        if tdata:
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("Some error occured while moving the hand "+str(self.num))
                return -1
            #print('okie!')
            return 1
        else:
            logging.error("No response from the hand "+str(self.num))
            return -1

        # print(p)

    def get(self):
        # flag = False
        self.clear_inWaiting()
        p = pack('@ffi', 0.0, 0.0, 50)
        #logging.error("send: " + str(p))
        print(p)

        self.ser.write(p)
        #tdata = self.ser.read(12)  # Wait forever for anything
        tdata = self.read_serial(12)
        print("------")
        print(tdata)
        print("---")
        if tdata:
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            logging.error(f'Hand {self.num} | lin: {LS2[0]:.3f}; ang: {LS2[1]:.3f}; hold: {LS2[2]}\n')
            #logging.error("Hand "+str(self.num)+" | lin: "+str(LS2[0])+"; ang: "+str(LS2[1])+"; hold: "+str(LS2[2])+ "\n")
            print(f'Hand {self.num} | lin: {LS2[0]:.3f}; ang: {LS2[1]:.3f}; hold: {LS2[2]}')
            #print("Hand "+str(self.num)+" | lin: "+str(LS2[0])+"; ang: "+str(LS2[1])+"; hold: "+str(LS2[2]))
            return LS2
        else:
            logging.error("Timeout reading Serial (Hand "+str(self.num)+")")
            print("Timeout reading Serial (Hand "+str(self.num)+")")
            return [-1]

    #def setPos(self, l, a, h):
        # not used
        #print("set zero position")
        # send cmd to stm to set proper zero
        #self.params = Params(l, a, h)

    def setZeroPos(self):
        logging.error("Set zero position")
        #print("! set zero position")
        self.clear_inWaiting()
        p = pack('@ffi', 0.0, 0.0, 75)
        #logging.error("send: " + str(p) + "\n")
        print(p)
        self.ser.write(p)

        #tdata = self.ser.read(12)
        tdata = self.read_serial(12)
        if tdata:
            print(tdata)
            unpacked_struct = unpack('@ffi', tdata)
            LS2 = list(unpacked_struct)
            if LS2[2] != 10:
                logging.error("an error occurred when setting zero position to the hand "+str(self.num))
                print("an error occurred when setting zero position to the hand "+str(self.num))
                return -1
        else:
            print("No answer recieved from hand "+str(self.num))
            return -1

    def flash(self, url):
        print("flash")
        logging.error("Flash")
        self.clear_inWaiting()
        ser.close()
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
        GPIO.output(self.BOOT0, 1) # Boot from serial
        GPIO.output(self.RESET, 1) # reset
        sleep(0.1)
        GPIO.output(self.RESET, 0)
        sleep(0.5)

        os.system(str("stm32flash "+self.tty))
        sleep(1)
        os.system(str("stm32flash -b 115200 -w stmfirmware"+str(self.num)+".bin "+self.tty))

        sleep(0.1)
        GPIO.output(self.BOOT0, 0)  # boot from flash
        sleep(0.1)
        GPIO.output(self.RESET, 1)  # reset
        sleep(0.1)
        GPIO.output(self.RESET, 0)
        self.ser = serial.Serial(self.tty, self.br)

    def clear_inWaiting(self):
        if self.ser.inWaiting():
            self.read_serial(self.ser.inWaiting())
            