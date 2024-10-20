#!/usr/bin/env python3
from math import ceil

# import RPi.GPIO as GPIO
import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
import re
from urllib.parse import urlparse, parse_qs
import logging
import threading
from robot import *

from jinja2 import Template

loglevel = logging.DEBUG
logfile  = 'log_python.txt'


class MyServer(BaseHTTPRequestHandler):
    base = "templates/"
    logging.basicConfig(filename=base+logfile, format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=loglevel)

    robot = [Hand('/dev/ttyAMA5', 115200, 15, 27, 22),
             #Hand('/dev/ttyAMA4', 115200, 17, 20, 16),
             Hand('/dev/ttyAMA3', 115200, 17, 23, 19),
             Hand('/dev/ttyAMA4', 115200, 19, 20, 16)]
             #Hand('/dev/ttyAMA4', 115200, 19, 20, 16)]
    
    # COM occupied flags
    hand1_com = [1]
    hand2_com = [1]
    hand3_com = [1]
    
    # result variables
    start1_results = [[], [], []]
    start_results = [[], [], []]
    set_results = [0, 0, 0]
    stop_results = [0, 0, 0]
    flash_results = [0, 0, 0]
    reset_results = [0, 0, 0]
    setZero_results = [0, 0, 0]
    get_results = [[], [], []]
    getVersion_results = [0, 0, 0]
    allow_unhold = [0]
    holders = [0, 0, 0]
    on_start_params = [0]
    
    # threads
    #t_start1 = threading.Thread(target=robot[0].start, args = (hand1_com, start_results, 0))
    #t_get1 = threading.Thread(target=robot[0].get, args = (hand1_com, get_results, 0))

    def __init__(self, request, client_address, server):
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)
        self.request_id = ''
        self.hand1_com = [1]
        self.hand2_com = [1]
        self.hand3_com = [1]
        self.allow_unhold = [0]
        self.on_start_params = [0]

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        query = urlparse(self.path).query
        range = self.headers.get('Range')
        from_byte = 0
        to_byte = 0

        if path != '/'+logfile:
            print(urlparse(self.path))
            if query:
                logging.info("Path: "+str(urlparse(self.path)))


        if re.search(r'^\/\S+\.(css|html|jpg|txt|py|ico|js)$', path):
            if not os.path.exists(self.base + path):
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("No such file", "utf8"))
                return

            # serving local file
            file_size = os.path.getsize(self.base + path)

            if (range is None):
                self.send_response(200)

            else:
#           range may be: bytes=-30000   last 30k to end
#	                  bytes=100-     from 100 to end
                m = re.search(r'^(bytes=)?-(\d+)$', range)
                if m:  from_byte = file_size - int(m.group(2))
                m = re.search(r'^(bytes=)?(\d+)-$', range)
                if m:  from_byte = int(m.group(2))
                    
                if from_byte < 0: from_byte = 0
                if from_byte > file_size: # requested incorrect range, exiting
                    self.send_response(416)
                    self.end_headers()
                    return
                self.send_response(206)

            if re.search(r'\.(css)$', path):
                self.send_header("Content-Type", "text/css")
            elif re.search(r'\.(html)$', path):
                self.send_header("Content-Type", "text/html")
            elif re.search(r'\.(js)$', path):
                self.send_header("Content-Type", "application/javascript")
            elif re.search(r'\.(txt)', path):
                self.send_header("Content-Type", "text/html")

            self.send_header("Content-Length", str(file_size-from_byte)) # actual transmit length

            if range is not None:
                self.send_header("Content-Range", "bytes " + str(from_byte) + "-" + str(file_size-1) + "/" + str(file_size))

            self.end_headers()

            with open(self.base + path) as file:
                if from_byte>0:
                    file.seek(from_byte) # or (-lastbytes, os.SEEK_END)
                data = file.read()  # .replace('\n','<br>')
                self.wfile.write(bytes(data, "utf8"))

            return





        # Sending an '200 OK' response
        self.send_response(200)

        # Setting the header
        self.send_header("Content-type", "text/html")

        # Whenever using 'send_header', you also have to call 'end_headers'
        self.end_headers()

        # Extract query param
        name = 'World'
        query_components = parse_qs(urlparse(self.path).query)
        print(query_components)
        if 'name' in query_components:
            name = query_components["name"][0]

        # Some custom HTML code, possibly generated by another function
        # with open('templates/index.html', 'r') as file:
        #     html = file.read()

        with open('templates/index.html', 'r') as f:
            template = Template(f.read())
        with open('rendered_index.html', 'w') as f:
            f.write(template.render(allow=self.allow_unhold[0]))
            # html = f.read()
        with open('rendered_index.html', 'r') as f:
            # f.write(template.render(var='hello world'))
            html = f.read()
        # html = f"<html><head></head><body><h1>Hello {name}!</h1></body></html>"

        # Writing the HTML contents with UTF-8
        self.wfile.write(bytes(html, "utf8"))

        if self.on_start_params[0] != 1:
            # logging.error(f'Get params on start: {self.on_start_params[0]}')
            self.get_params_holders()

        return

    def do_POST(self):

        # if not self.on_start_params:
        #     self.get_params_holders()
        # logging.error(self.get_results)
        # logging.error(self.holders)

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        args = parse_qs(post_data)
        # logging.error(args)
        print(args)

        if "set1" in args:
            lin = 0
            ang = 0.0
            hold = 0
            if "lin1" in args:
                lin = float(args["lin1"][0])
            if "ang1" in args:
                ang = float(args["ang1"][0])
            if "hold1" in args:
                hold = int(args["hold1"][0])
            self.robot[0].params = Params(0.0, 0.0, 0, 0, lin, ang, hold)
            #print(str(self.robot[0].params.lin_mm) + " " + str(self.robot[0].params.ang_deg) + " " + str(self.robot[0].params.hold))

        if "set2" in args:
            lin = 0
            ang = 0.0
            hold = 0
            if "lin2" in args:
                lin = float(args["lin2"][0])
            if "ang2" in args:
                ang = float(args["ang2"][0])
            if "hold2" in args:
                hold = int(args["hold2"][0])
            self.robot[1].params = Params(0.0, 0.0, 0, 0, lin, ang, hold)
            #print(str(self.robot[1].params.lin) + " " + str(self.robot[1].params.ang) + " " + str(self.robot[1].params.hold))

        if "set3" in args:
            lin = 0
            ang = 0.0
            hold = 0
            if "lin3" in args:
                lin = float(args["lin3"][0])
            if "ang3" in args:
                ang = float(args["ang3"][0])
            if "hold3" in args:
                hold = int(args["hold3"][0])
            self.robot[2].params = Params(0.0, 0.0, 0, 0, lin, ang, hold)
            #print(str(self.robot[2].params.lin) + " " + str(self.robot[2].params.ang) + " " + str(self.robot[2].params.hold))

        if "get1" in args:
            #self.robot[0].get()
            t_get1 = threading.Thread(target=self.robot[0].get, args = (self.hand1_com[0], self.get_results, 0))
            t_get1.start()
        if "get2" in args:
            #print("get request 2")
            #self.robot[1].get(self.hand2_com, self.get_results, 1)
            t_get2 = threading.Thread(target=self.robot[1].get, args = (self.hand2_com[0], self.get_results, 1))
            t_get2.start()
        if "get3" in args:
            #self.robot[2].get(self.hand3_com, self.get_results, 2)
            t_get3 = threading.Thread(target=self.robot[2].get, args = (self.hand3_com[0], self.get_results, 2))
            t_get3.start()
        if "send1" in args:
            self.get_params_holders()

            if (self.holders[1] != 1 or self.holders[2] != 1) and not self.allow_unhold[0] and self.robot[0].params[6] == 0:
                logging.error(f'Another hand is unholded already!')
            else:
                t_start1 = threading.Thread(target=self.robot[0].start, args = (self.hand1_com[0], self.start1_results, self.start_results, 0))
                t_start1.start()
            #self.robot[0].start(hand1_com, start_results, 0)
        if "send2" in args:
            self.get_params_holders()

            #self.robot[1].start(self.hand2_com, self.start_results, 1)
            if (self.holders[0] != 1 or self.holders[2] != 1) and not self.allow_unhold[0] and self.robot[1].params[6] == 0:
                logging.error(f'Another hand is unholded already!')
            else:
                t_start2 = threading.Thread(target=self.robot[1].start, args = (self.hand2_com[0], self.start1_results, self.start_results, 1))
                t_start2.start()
        if "send3" in args:
            self.get_params_holders()

            #self.robot[2].start(self.hand3_com, self.start_results, 2)
            if (self.holders[0] != 1 or self.holders[1] != 1) and not self.allow_unhold[0] and self.robot[2].params[6] == 0:
                logging.error(f'Another hand is unholded already!')
            else:
                t_start3 = threading.Thread(target=self.robot[2].start, args = (self.hand3_com[0], self.start1_results, self.start_results, 2))
                t_start3.start()
        if "send_cmd" in args:
            if "cmd" in args:
                if args["cmd"][0] == "1R":
                    print("1R")
                    f = open("arr.txt", "r")
                    file_arr = f.read()

                    a0_start = file_arr.find("angle0")+10
                    a0_end = file_arr.find("}", a0_start)
                    angle0_str = file_arr[a0_start:a0_end].split(",")

                    s0_start = file_arr.find("shift0") + 10
                    s0_end = file_arr.find("}", s0_start)
                    shift0_str = file_arr[s0_start:s0_end].split(",")

                    a1_start = file_arr.find("angle1") + 10
                    a1_end = file_arr.find("}", a1_start)
                    angle1_str = file_arr[a1_start:a1_end].split(",")

                    s1_start = file_arr.find("shift1") + 10
                    s1_end = file_arr.find("}", s1_start)
                    shift1_str = file_arr[s1_start:s1_end].split(",")

                    a2_start = file_arr.find("angle2") + 10
                    a2_end = file_arr.find("}", a2_start)
                    angle2_str = file_arr[a2_start:a2_end].split(",")

                    s2_start = file_arr.find("shift2") + 10
                    s2_end = file_arr.find("}", s2_start)
                    shift2_str = file_arr[s2_start:s2_end].split(",")

                    h0_start = file_arr.find("hoock0") + 10
                    h0_end = file_arr.find("}", h0_start)
                    hoock0_str = file_arr[h0_start:h0_end].split(",")

                    h1_start = file_arr.find("hoock1") + 10
                    h1_end = file_arr.find("}", h1_start)
                    hoock1_str = file_arr[h1_start:h1_end].split(",")

                    h2_start = file_arr.find("hoock2") + 10
                    h2_end = file_arr.find("}", h2_start)
                    hoock2_str = file_arr[h2_start:h2_end].split(",")

                    arr_len = len(angle0_str)
                    #logging.error(f"{angle0_str}")

                    angle0 = [float(angle0_str[0])]
                    shift0 = [float(shift0_str[0])]
                    angle1 = [float(angle1_str[0])]
                    shift1 = [float(shift1_str[0])]
                    angle2 = [float(angle2_str[0])]
                    shift2 = [float(shift2_str[0])]
                    hoock0 = [int(hoock0_str[0])]
                    hoock1 = [int(hoock1_str[0])]
                    hoock2 = [int(hoock2_str[0])]
                    
                    counter = -1
                    last_hoock0 = int(hoock0_str[0])
                    last_hoock1 = int(hoock1_str[0])
                    last_hoock2 = int(hoock2_str[0])

                    for i in range(len(angle0_str)):
                        counter += 1
                        h0 = int(hoock0_str[i])
                        h1 = int(hoock1_str[i])
                        h2 = int(hoock2_str[i])
                        if (counter == 99) or (h0 != last_hoock0) or (h1 != last_hoock1) or (h2 != last_hoock2):
                            angle0.append(float(angle0_str[i]))
                            shift0.append(float(shift0_str[i]))
                            angle1.append(float(angle1_str[i]))
                            shift1.append(float(shift1_str[i]))
                            angle2.append(float(angle2_str[i]))
                            shift2.append(float(shift2_str[i]))
                            hoock0.append(int(hoock0_str[i]))
                            hoock1.append(int(hoock1_str[i]))
                            hoock2.append(int(hoock2_str[i]))
                            counter = -1
                        last_hoock0 = h0
                        last_hoock1 = h1
                        last_hoock2 = h2
                    f.close()
                    logging.error(f'START 1R')

                    for i in range(0, arr_len):
                        #logging.error(f"{i}")
                        steps_periods = self.calc_steps_and_ARR(angle0[i], shift0[i], angle1[i], shift1[i], angle2[i], shift2[i])

                        #logging.error(f"Send params: ({shift0[i]}, {angle0[i]}), ({shift1[i]}, {angle1[i]}), ({shift2[i]}, {angle2[i]})")
                        self.robot[0].params = Params(steps_periods[0][0], steps_periods[0][1], steps_periods[1][0], steps_periods[1][1], shift0[i], angle0[i], hoock0[i])
                        self.robot[1].params = Params(steps_periods[0][2], steps_periods[0][3], steps_periods[1][2], steps_periods[1][3], shift1[i], angle1[i], hoock1[i])
                        self.robot[2].params = Params(steps_periods[0][4], steps_periods[0][5], steps_periods[1][4], steps_periods[1][5], shift2[i], angle2[i], hoock2[i])

                        '''self.robot[0].params = Params(shift0[i], angle0[i], 0, 0, hoock0[i])
                        self.robot[1].params = Params(shift1[i], angle1[i], 0, 0, hoock1[i])
                        self.robot[2].params = Params(shift2[i], angle2[i], 0, 0, hoock2[i])'''
                        
                        '''self.robot[0].setSteps(self.hand1_com, self.set_results, 0)
                        self.robot[1].setSteps(self.hand2_com, self.set_results, 1)
                        self.robot[2].setSteps(self.hand3_com, self.set_results, 2)'''
                        
                        t_set1 = threading.Thread(target=self.robot[0].setSteps,
                                                  args = (self.hand1_com[0], self.set_results, 0))
                        t_set2 = threading.Thread(target=self.robot[1].setSteps,
                                                  args = (self.hand2_com[0], self.set_results, 1))
                        t_set3 = threading.Thread(target=self.robot[2].setSteps,
                                                  args = (self.hand3_com[0], self.set_results, 2))
                        t_set1.start()
                        t_set2.start()
                        t_set3.start()
                        
                        t_set1.join()
                        t_set2.join()
                        t_set3.join()
                        
                        logging.error(f'SEND  : ({shift0[i]:.3f}, {angle0[i]:.3f}), ({shift1[i]:.3f}, {angle1[i]:.3f}), ({shift2[i]:.3f}, {angle2[i]:.3f})')
                        
                        if (self.set_results[0] < 0) or (self.set_results[1] < 0) or (self.set_results[2] < 0):
                            logging.error(f'Error occurred on setting coordinates: ({shift0[i]}, {angle0[i]}), ({shift1[i]}, {angle1[i]}), ({shift2[i]}, {angle2[i]})\nAbort the move')
                            break

                        '''status0 = self.robot[0].start(self.hand1_com, self.start_results, 0)
                        status1 = self.robot[1].start(self.hand2_com, self.start_results, 1)
                        status2 = self.robot[2].start(self.hand3_com, self.start_results, 2)'''
                        #sleep(1)

                        # wait for threads to end AND for robot to finish move
                        
                        '''t_set1.join()
                        t_set2.join()
                        t_set3.join()'''
                        #logging.error("GET obtained")

                        t_start1 = threading.Thread(target=self.robot[0].startSteps,
                                                    args=(self.hand1_com[0], self.start1_results, self.start_results, 0))
                        t_start2 = threading.Thread(target=self.robot[1].startSteps,
                                                    args=(self.hand2_com[0], self.start1_results, self.start_results, 1))
                        t_start3 = threading.Thread(target=self.robot[2].startSteps,
                                                    args=(self.hand3_com[0], self.start1_results, self.start_results, 2))
                        #logging.error("BEFORE start")
                        t_start1.start()
                        t_start2.start()
                        t_start3.start()
                        #logging.error("AFTER start")

                        #sleep(1)

                        # wait for threads to end AND for robot to finish move

                        t_start1.join()
                        t_start2.join()
                        t_start3.join()
                        
                        '''self.robot[0].startSteps(self.hand1_com, self.start_results, 0)
                        self.robot[1].startSteps(self.hand2_com, self.start_results, 1)
                        self.robot[2].startSteps(self.hand3_com, self.start_results, 2)'''
                        
                        if (self.start_results[0][0] < 0) or (self.start_results[1][0] < 0) or (self.start_results[2][0] < 0):
                            logging.error(f'Error occurred on coordinates: ({shift0[i]}, {angle0[i]}), ({shift1[i]}, {angle1[i]}), ({shift2[i]}, {angle2[i]})\nAbort the move')
                            break
                        
                        '''t_get1 = threading.Thread(target=self.robot[0].get,
                                                  args=(self.hand1_com, self.get_results, 0, False))
                        t_get2 = threading.Thread(target=self.robot[1].get,
                                                  args=(self.hand2_com, self.get_results, 1, False))
                        t_get3 = threading.Thread(target=self.robot[2].get,
                                                  args=(self.hand3_com, self.get_results, 2, False))
                        t_get1.start()
                        t_get2.start()
                        t_get3.start()
                        
                        t_get1.join()
                        t_get2.join()
                        t_get3.join()'''
                        
                        
                        #logging.error(f"{self.start_results}")
                        logging.error(f"FIRST : ({self.start_results[0][0]:.3f}, {self.start_results[0][1]:.3f}), ({self.start_results[1][0]:.3f}, {self.start_results[1][1]:.3f}), ({self.start_results[2][0]:.3f}, {self.start_results[2][1]:.3f})")
                        logging.error(f"AFTER : ({self.start_results[0][4]:.3f}, {self.start_results[0][5]:.3f}), ({self.start_results[1][4]:.3f}, {self.start_results[1][5]:.3f}), ({self.start_results[2][4]:.3f}, {self.start_results[2][5]:.3f})")
                        logging.error("---")
                        #logging.error(f"DELTA : ({abs(self.get_results[0][4]-shift0[i]):.3f}, {abs(self.get_results[0][5]-angle0[i]):.3f}), ({abs(self.get_results[1][4]-shift1[i]):.3f}, {abs(self.get_results[1][5]-angle1[i]):.3f}), ({abs(self.get_results[2][4]-shift2[i]):.3f}, {abs(self.get_results[2][5]-angle2[i]):.3f})")
                        delta_l1 = self.start_results[0][4]-shift0[i]
                        delta_a1 = self.start_results[0][5]-angle0[i]
                        delta_l2 = self.start_results[1][4]-shift1[i]
                        delta_a2 = self.start_results[1][5]-angle1[i]
                        delta_l3 = self.start_results[2][4]-shift2[i]
                        delta_a3 = self.start_results[2][5]-angle2[i]
                        if (360.0 - delta_a1 < delta_a1):
                            delta_a1 = 360.0 - delta_a1
                        if (360.0 - delta_a2 < delta_a2):
                            delta_a2 = 360.0 - delta_a2
                        if (360.0 - delta_a3 < delta_a3):
                            delta_a3 = 360.0 - delta_a3
                        logging.error(f"DELTA : ({delta_l1:.3f}, {delta_a1:.3f}), ({delta_l2:.3f}, {delta_a2:.3f}), ({delta_l3:.3f}, {delta_a3:.3f})")
                        logging.error("---------------------")
                    logging.error(f'END 1R')
                
                '''if args["cmd"][0] == "test":
                    for i in range(1000):
                        if i%2 == 0:
                            self.robot[0].params = Params(20,100,1)
                            self.robot[2].params = Params(20,100,1)
                        else:
                            self.robot[0].params = Params(130,200,0)
                            self.robot[2].params = Params(130,200,0)
                        
                        status0 = self.robot[0].start()
                        status2 = self.robot[2].start()
                        
                        if (status0 < 0) or (status2 < 0):
                            logging.error(f'TEST Error occures on iteration {i}')
                            break
                        logging.error('Test finished')''' 

                if args["cmd"][0] == "hold":
                    self.get_params_holders()

                    print("hold")
                    t_get1 = threading.Thread(target=self.robot[0].get,
                                              args=(self.hand1_com[0], self.get_results, 0))
                    t_get2 = threading.Thread(target=self.robot[1].get,
                                              args=(self.hand2_com[0], self.get_results, 1))
                    t_get3 = threading.Thread(target=self.robot[2].get,
                                              args=(self.hand3_com[0], self.get_results, 2))
                    t_get1.start()
                    t_get2.start()
                    t_get3.start()
                    
                    t_get1.join()
                    t_get2.join()
                    t_get3.join()
                    #logging.error(f"Get results: ({self.get_results[0][4]:.3f}, {self.get_results[0][5]:.3f}), ({self.get_results[1][4]:.3f}, {self.get_results[1][5]:.3f}), ({self.get_results[2][4]:.3f}, {self.get_results[2][5]:.3f})")
                    error_flag = False
                    
                    if (self.get_results[0][0] < 0) or (self.get_results[1][0] < 0) or (self.get_results[2][0] < 0):
                        logging.error(f'Error occurred while getting the coordinates\nAbort the move')
                        error_flag = True

                    if not error_flag:
                        
                        lin_1 = self.get_results[0][4]
                        ang_1 = self.get_results[0][5]
                        
                        lin_2 = self.get_results[1][4]
                        ang_2 = self.get_results[1][5]
                        
                        lin_3 = self.get_results[2][4]
                        ang_3 = self.get_results[2][5]
                        
                        self.robot[0].params = Params(0, 0, 0, 0, lin_1, ang_1, 1)
                        self.robot[1].params = Params(0, 0, 0, 0, lin_2, ang_2, 1)
                        self.robot[2].params = Params(0, 0, 0, 0, lin_3, ang_3, 1)
                    
                        t_start1 = threading.Thread(target=self.robot[0].start, args = (self.hand1_com[0], self.start1_results, self.start_results, 0))
                        t_start2 = threading.Thread(target=self.robot[1].start, args = (self.hand2_com[0], self.start1_results, self.start_results, 1))
                        t_start3 = threading.Thread(target=self.robot[2].start, args = (self.hand3_com[0], self.start1_results, self.start_results, 2))
                        
                        t_start1.start()
                        t_start2.start()
                        t_start3.start()
                        
                        t_start1.join()
                        t_start2.join()
                        t_start3.join()
                        
                        #logging.error(f"Res1: {self.start1_results}\nRes2: {self.start_results}")
                        #self.robot[0].start(self.hand1_com, self.start_results, 0)
                        #self.robot[1].start(self.hand2_com, self.start_results, 1)
                        #self.robot[2].start(self.hand3_com, self.start_results, 2)

                if args["cmd"][0] == "unhold":
                    self.get_params_holders()

                    print("unhold")
                    if not self.allow_unhold[0]:
                        logging.error(f'Unhold is not allowed!')
                    else:
                        error_flag = False

                        t_get1 = threading.Thread(target=self.robot[0].get,
                                                  args=(self.hand1_com[0], self.get_results, 0))
                        t_get2 = threading.Thread(target=self.robot[1].get,
                                                  args=(self.hand2_com[0], self.get_results, 1))
                        t_get3 = threading.Thread(target=self.robot[2].get,
                                                  args=(self.hand3_com[0], self.get_results, 2))
                        t_get1.start()
                        t_get2.start()
                        t_get3.start()

                        t_get1.join()
                        t_get2.join()
                        t_get3.join()
                        #logging.error(f"Get results: ({self.get_results[0][4]:.3f}, {self.get_results[0][5]:.3f}), ({self.get_results[1][4]:.3f}, {self.get_results[1][5]:.3f}), ({self.get_results[2][4]:.3f}, {self.get_results[2][5]:.3f})")
                        error_flag = False

                        if (self.get_results[0][0] < 0) or (self.get_results[1][0] < 0) or (self.get_results[2][0] < 0):
                            logging.error(f'Error occurred while getting the coordinates coordinates\nAbort the move')
                            error_flag = True

                        if not error_flag:
                            lin_1 = self.get_results[0][4]
                            ang_1 = self.get_results[0][5]

                            lin_2 = self.get_results[1][4]
                            ang_2 = self.get_results[1][5]

                            lin_3 = self.get_results[2][4]
                            ang_3 = self.get_results[2][5]

                            self.robot[0].params = Params(0, 0, 0, 0, lin_1, ang_1, 0)
                            self.robot[1].params = Params(0, 0, 0, 0, lin_2, ang_2, 0)
                            self.robot[2].params = Params(0, 0, 0, 0, lin_3, ang_3, 0)

                            t_start1 = threading.Thread(target=self.robot[0].start, args = (self.hand1_com[0], self.start1_results, self.start_results, 0))
                            t_start2 = threading.Thread(target=self.robot[1].start, args = (self.hand2_com[0], self.start1_results, self.start_results, 1))
                            t_start3 = threading.Thread(target=self.robot[2].start, args = (self.hand3_com[0], self.start1_results, self.start_results, 2))

                            t_start1.start()
                            t_start2.start()
                            t_start3.start()

                            t_start1.join()
                            t_start2.join()
                            t_start3.join()

                            #logging.error(f"Res1: {self.start1_results}\nRes2: {self.start_results}")

                            #self.robot[0].start(self.hand1_com, self.start_results, 0)
                            #self.robot[1].start(self.hand2_com, self.start_results, 1)
                            #self.robot[2].start(self.hand3_com, self.start_results, 2)
                if args["cmd"][0] == "getVersion1":
                    t_get1 = threading.Thread(target=self.robot[0].getVersion, args = (self.hand1_com[0], self.getVersion_results, 0))
                    t_get1.start()
                if args["cmd"][0] == "getVersion2":
                    t_get2 = threading.Thread(target=self.robot[1].getVersion, args = (self.hand2_com[0], self.getVersion_results, 1))
                    t_get2.start()
                if args["cmd"][0] == "getVersion3":
                    t_get3 = threading.Thread(target=self.robot[2].getVersion, args = (self.hand3_com[0], self.getVersion_results, 2))
                    t_get3.start()

        if "stop_cmd" in args:
            t_stop1 = threading.Thread(target=self.robot[0].stop, args = (self.hand1_com[0], self.stop_results, 0))
            t_stop2 = threading.Thread(target=self.robot[1].stop, args = (self.hand2_com[0], self.stop_results, 1))
            t_stop3 = threading.Thread(target=self.robot[2].stop, args = (self.hand3_com[0], self.stop_results, 2))
                                   
            t_stop1.start()
            t_stop2.start()
            t_stop3.start()
            
            #self.robot[0].stop()
            #self.robot[1].stop()
            #self.robot[2].stop()

        if "allow_cmd" in args:
            if not self.allow_unhold[0]:
                logging.error(f'Unhold is allowed')
                self.allow_unhold[0] = 1
            else:
                logging.error(f'Unhold is forbidden')
                self.allow_unhold[0] = 0
            # logging.error(f'Redirecting')
            self._redirect('/')

        if "zero_pos" in args:
            t_zero1 = threading.Thread(target=self.robot[0].setZeroPos, args = (self.hand1_com[0], self.setZero_results, 0))
            t_zero2 = threading.Thread(target=self.robot[1].setZeroPos, args = (self.hand2_com[0], self.setZero_results, 1))
            t_zero3 = threading.Thread(target=self.robot[2].setZeroPos, args = (self.hand3_com[0], self.setZero_results, 2))
                                   
            t_zero1.start()
            t_zero2.start()
            t_zero3.start()
            
            #self.robot[0].setZeroPos()
            #self.robot[1].setZeroPos()
            #self.robot[2].setZeroPos()

        if "flash" in args:
            #status0 = self.robot[0].stop()
            #status1 = self.robot[1].stop()
            #status2 = self.robot[2].stop()
            
            #if (status0<0) or (status1 < 0) or (status2 < 0):
            #    logging.error("Error occured while stopping hands, abort the rebooting")

            #self.robot[0].flash("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_0.bin?raw=true") #тестова прошивка блимання світлодіодом
            
            t_flash1 = threading.Thread(target=self.robot[0].flash, args = ("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_0.bin?raw=true", self.hand1_com[0], self.flash_results, 0))
            t_flash2 = threading.Thread(target=self.robot[1].flash, args = ("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_1.bin?raw=true", self.hand2_com[0], self.flash_results, 1))
            t_flash3 = threading.Thread(target=self.robot[2].flash, args = ("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_2.bin?raw=true", self.hand3_com[0], self.flash_results, 2))
                                   
            t_flash1.start()
            t_flash2.start()
            t_flash3.start()
            #sleep(1)
            #self.robot[1].flash("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_1.bin?raw=true")
            #sleep(1)
            #self.robot[2].flash("https://github.com/AnastasiyaYatsenko/robot_bin/blob/main/hand_2.bin?raw=true")
        
        if "reset" in args:
            t_reset1 = threading.Thread(target=self.robot[0].reset, args = (self.reset_results, 0))
            t_reset2 = threading.Thread(target=self.robot[1].reset, args = (self.reset_results, 1))
            t_reset3 = threading.Thread(target=self.robot[2].reset, args = (self.reset_results, 2))
                                   
            t_reset1.start()
            t_reset2.start()
            t_reset3.start()

        self._redirect('/')  # Redirect back to the root url

    def get_params_holders(self):
        # logging.error(f'Get params on start (inside): {self.on_start_params[0]}')
        # if self.on_start_params:
        #     return
        self.on_start_params[0] = 1
        # logging.error(f'params on start: {self.on_start_params}')
        t_get1 = threading.Thread(target=self.robot[0].get, args=(self.hand1_com[0], self.get_results, 0, False))
        t_get2 = threading.Thread(target=self.robot[1].get, args=(self.hand2_com[0], self.get_results, 1, False))
        t_get3 = threading.Thread(target=self.robot[2].get, args=(self.hand3_com[0], self.get_results, 2, False))

        t_get1.start()
        t_get2.start()
        t_get3.start()

        t_get1.join()
        t_get2.join()
        t_get3.join()

        self.holders[0] = self.get_results[0][6]
        self.holders[1] = self.get_results[1][6]
        self.holders[2] = self.get_results[2][6]
        # logging.error(self.holders)



    def calc_steps_and_ARR(self, a1, l1, a2, l2, a3, l3):
        t_get1 = threading.Thread(target=self.robot[0].get,
                                  args=(self.hand1_com[0], self.get_results, 0, False))
        t_get2 = threading.Thread(target=self.robot[1].get,
                                  args=(self.hand2_com[0], self.get_results, 1, False))
        t_get3 = threading.Thread(target=self.robot[2].get,
                                  args=(self.hand3_com[0], self.get_results, 2, False))
        t_get1.start()
        t_get2.start()
        t_get3.start()

        t_get1.join()
        t_get2.join()
        t_get3.join()
        
        #TODO check if get results are ok
        
        #print(self.get_results)
        logging.error(f"BEFORE: ({self.get_results[0][4]:.3f}, {self.get_results[0][5]:.3f}), ({self.get_results[1][4]:.3f}, {self.get_results[1][5]:.3f}), ({self.get_results[2][4]:.3f}, {self.get_results[2][5]:.3f})")

        lin_1 = self.get_results[0][4]
        ang_1 = self.get_results[0][5]

        lin_2 = self.get_results[1][4]
        ang_2 = self.get_results[1][5]

        lin_3 = self.get_results[2][4]
        ang_3 = self.get_results[2][5]

        #pos_ang1 = abs(ang_1 - a1)
        #inverse_pos_ang1 = abs(360.0 - pos_ang1)
        #actualPosAngle1 = 0
        #
        #pos_ang2 = abs(ang_2 - a2)
        #inverse_pos_ang2 = abs(360.0 - pos_ang2)
        #actualPosAngle2 = 0
        #
        #pos_ang3 = abs(ang_3 - a3)
        #inverse_pos_ang3 = abs(360.0 - pos_ang3)
        #actualPosAngle3 = 0

        actualPosAngle1, actualPosDistance1, angDir1, linDir1 = self.get_pos_send_dir(0, lin_1, l1, ang_1, a1)
        actualPosAngle2, actualPosDistance2, angDir2, linDir2 = self.get_pos_send_dir(1, lin_2, l2, ang_2, a2)
        actualPosAngle3, actualPosDistance3, angDir3, linDir3 = self.get_pos_send_dir(2, lin_3, l3, ang_3, a3)

        motorStep = 200
        drvMicroSteps = 16
        steps4OneMM = 200 * drvMicroSteps / (2 * 20)

        anglePsteps1 = (actualPosAngle1 * (8 * motorStep * drvMicroSteps)) / 360
        distPsteps1 = actualPosDistance1 * steps4OneMM

        anglePsteps2 = (actualPosAngle2 * (8 * motorStep * drvMicroSteps)) / 360
        distPsteps2 = actualPosDistance2 * steps4OneMM

        anglePsteps3 = (actualPosAngle3 * (8 * motorStep * drvMicroSteps)) / 360
        distPsteps3 = actualPosDistance3 * steps4OneMM

        #period = 30
        period = 300

        steps_periods = [[distPsteps1, anglePsteps1, distPsteps2, anglePsteps2, distPsteps3, anglePsteps3],
                         [period, period, period, period, period, period]]

        max_steps = steps_periods[0][0]
        for i in range(6):
            if steps_periods[0][i] > max_steps:
                max_steps = steps_periods[0][i]

        for i in range(6):
            if steps_periods[0][i] != max_steps:
                delimiter = float(max_steps) / max(float(steps_periods[0][i]), 1)
                mnoj = ceil(period * delimiter)
                steps_periods[1][i] = mnoj

        steps_periods[0][0] *= linDir1
        steps_periods[0][1] *= angDir1
        steps_periods[0][2] *= linDir2
        steps_periods[0][3] *= angDir2
        steps_periods[0][4] *= linDir3
        steps_periods[0][5] *= angDir3

        '''logging.error(f"l1 from {lin_1} to {l1} in {distPsteps1} with {linDir1}, period={steps_periods[1][0]}") 
        logging.error(f"a1 from {ang_1} to {a1} in {anglePsteps1} with {angDir1}, period={steps_periods[1][1]}") 
        logging.error(f"l2 from {lin_2} to {l2} in {distPsteps2} with {linDir2}, period={steps_periods[1][2]}") 
        logging.error(f"a2 from {ang_2} to {a2} in {anglePsteps2} with {angDir2}, period={steps_periods[1][3]}") 
        logging.error(f"l3 from {lin_3} to {l3} in {distPsteps3} with {linDir3}, period={steps_periods[1][4]}") 
        logging.error(f"a3 from {ang_3} to {a3} in {anglePsteps3} with {angDir3}, period={steps_periods[1][5]}")'''

        return steps_periods

    def get_pos_send_dir(self, i, curr_lin, dest_lin, curr_ang, dest_ang):
        pos_ang = abs(curr_ang - dest_ang)
        inverse_pos_ang = abs(360.0 - pos_ang)
        actualPosAngle = 0
        actualPosDistance = abs(curr_lin - dest_lin)
        angDir = 0
        linDir = 0

        if inverse_pos_ang < pos_ang:
            actualPosAngle = inverse_pos_ang
            if curr_ang < dest_ang:
                # enable inverse
                angDir = -1
                # self.robot[i].setAngDir(1)
            elif curr_ang > dest_ang:
                # disable inverse
                angDir = 1
                # self.robot[i].setAngDir(0)
        else:
            actualPosAngle = pos_ang
            if curr_ang < dest_ang:
                # disable inverse
                angDir = 1
                # self.robot[i].setAngDir(0)
            elif curr_ang > dest_ang:
                # enable inverse
                angDir = -1
                # self.robot[i].setAngDir(1)

        if curr_lin < dest_lin:
            # enable inverse
            linDir = -1
            # self.robot[i].setLinDir(1)
        elif curr_lin > dest_lin:
            # disable inverse
            linDir = 1
            # self.robot[i].setLinDir(0)

        return actualPosAngle, actualPosDistance, angDir, linDir

