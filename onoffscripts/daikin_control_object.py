## used from https://github.com/ael-code/daikin-aricon-pylib/blob/master/daikin_aircon.py
## And adjusted for my use

import socket
import socketserver
import threading
import time
import requests
#import logging
#import http.client as http_client
#http_client.HTTPConnection.debuglevel = 1
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True


class Airco():

    MODE_AUTO = 0 #or 1 or 7
    MODE_DRY = 2
    MODE_COOL = 3
    MODE_HEAT = 4
    MODE_FAN = 6

    FAN_POWER_AUTO = 'A'
    FAN_POWER_SILENCE = 'B'
    FAN_POWER_1 = '3'
    FAN_POWER_2 = '4'
    FAN_POWER_3 = '5'
    FAN_POWER_4 = '6'
    FAN_POWER_5 = '7'

    FAN_DIR_STOP = 0
    FAN_DIR_VERT = 1
    FAN_DIR_HOR = 2
    FAN_DIR_ALL = 3

    def __init__(self, host):
        self.host = host
        self._http_conn = None
        #f_rate (A auto,B silence,3 lvl_1,4	lvl_2,5	lvl_3,6	lvl_4,7	lvl_5)
        #f_dir (0	all wings stopped, 1	vertical wings motion, 2	horizontal wings motion, 3	vertical and horizontal wings motion)
        self.power = False
        self.mode = MODE_AUTO
        self.temp = 0.0
        self.hum = 0
        self.frate = FAN_POWER_AUTO
        self.fdir = FAN_DIR_STOP
        self.last_change = None

    def update(self):
        #ret=OK,pow=0,mode=3,adv=,stemp=23.0,shum=0,dt1=25.0,dt2=M,dt3=23.0,dt4=25.0,dt5=25.0,dt7=25.0,dh1=AUTO,dh2=50,dh3=0,dh4=0,dh5=0,dh7=AUTO,dhh=50,b_mode=3,b_stemp=23.0,b_shum=0,alert=255,f_rate=A,f_dir=0,b_f_rate=A,b_f_dir=0,dfr1=5,dfr2=5,dfr3=A,dfr4=5,dfr5=5,dfr6=5,dfr7=5,dfrh=5,dfd1=0,dfd2=0,dfd3=0,dfd4=0,dfd5=0,dfd6=0,dfd7=0,dfdh=0,dmnd_run=0,en_demand=0
        try:
            r = requests.get('http://'+self.host+'/aircon/get_control_info', timeout=5)
            returnobject = r.text.split(",")
            if returnobject[0].split("=")[1] == "OK":
                for o in returnobject:
                    if o.split("=")[0] == 'pow':
                        if int(o.split("=")[1]) == 0:
                            self.power = False
                        else:
                            self.power = True
                    if o.split("=")[0] == 'mode':
                        self.mode = int(o.split("=")[1])
                    if o.split("=")[0] == 'shum':
                        self.hum = int(o.split("=")[1])
                    if o.split("=")[0] == 'stemp':
                        self.temp = float(o.split("=")[1])
                    if o.split("=")[0] == 'frate':
                        self.frate = o.split("=")[1]
                    if o.split("=")[0] == 'fdir':
                        self.fdir = int(o.split("=")[1])
                return True
            else:
                return False
        except:
            return False

    def set_power(self):
        if self.power:
            self.power = False
        else:
            self.power = True
    
    def set_fan_speed(self, rate):
        self.frate = rate

    def set_fan_dir(self, dir):
        self.frate = dir

    def set_fan_dir(self, t):
        self.temp = t

    def activate_settings(self):
        try:
            #pow=1&mode=1&stemp=26&shum=0&f_rate=B&f_dir=3
            data = '?pow=%s&mode=%s&stemp=%s&shum=%s&f_rate=%s&f_dir=%s' % (self.power,self.mode,self.temp,self.hum,self.frate,self.fdir)
            r = requests.get('http://'+self.host+'/aircon/set_control_info'+data, timeout=5)
            returnobject = r.text.split(",")
            if returnobject[0].split("=")[1] == "OK":
                return True
            else:
                return False
        except:
            return False


def discover(waitfor=1,
             timeout=10,
             listen_address="0.0.0.0",
             listen_port=0,
             probe_port=30050,
             probe_address='255.255.255.255',
             probe_attempts=10,
             probe_interval=0.3):

    discovered = {}

    class UDPRequestHandler(socketserver.BaseRequestHandler):

        def handle(self):
            log.debug("Discovery: received response from {} - '{}'".format(self.client_address[0], self.request[0]))
            resp = process_response(self.request[0])
            host = self.client_address[0]
            discovered[host] = resp

    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sckt.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    server = socketserver.ThreadingUDPServer((listen_address, listen_port), UDPRequestHandler)
    server.socket = sckt
    srv_addr, srv_port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    log.debug("Discovery: starting UDP server on {}:{}".format(srv_addr, srv_port))
    server_thread.start()

    for i in range(0, probe_attempts):
        log.debug("Discovery: probe attempt {} on {}:{}".format(i, probe_address, probe_port))
        sckt.sendto(DSCV_TXT.encode(), (probe_address, probe_port))
        log.debug("Discovery: sleeping for {}s".format(probe_interval))
        time.sleep(probe_interval)
        if len(discovered) >= waitfor:
            break

    remaining_time = timeout - (probe_interval * probe_attempts)
    if (remaining_time > 0) and (len(discovered) < waitfor):
        log.debug("Discovery: waiting responses for {}s more".format(remaining_time))
        time.sleep(remaining_time)

    server.shutdown()
    server.server_close()

    return discovered