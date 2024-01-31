from http.server import HTTPServer
import robot
from server import *

#lkjlpojlkjlkj

host_name = '192.168.0.184'  # IP Address of Raspberry Pi
local_host_name = '127.0.0.1'
host_port = 8001
# base = "templates/"

# my_robot = robot.Robot('/dev/ttyS3', 115200)
robot.setupGPIO()
# my_server = MyServer()
# my_server.set_Robot(r=my_robot)
http_server = HTTPServer(('', host_port), MyServer)
#http_server = HTTPServer((host_name, host_port), MyServer)
# http_server = HTTPServer((local_host_name, host_port), MyServer)
print("Server Starts - %s:%s" % (host_name, host_port))
# print("Server Starts - %s:%s" % (local_host_name, host_port))
try:
    http_server.serve_forever()
except KeyboardInterrupt:
    http_server.server_close()