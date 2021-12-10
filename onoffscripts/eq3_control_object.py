#!/usr/bin/python3
# -*-coding: utf-8 -*-

import datetime
import subprocess
import time
import requests
import traceback
import sys

class EQ3Thermostat(object):

    def __init__(self, address):
        if ("@" in address ):
            self.remoteaddress = address.split("@")[1]
            self.address = address.split("@")[0]
        else:
            self.address = address
            self.remoteaddress = None
		
        self.locked = False
        self.temperature = -1
        self.failedtimes = 0
        self.status = 'initializing'
        self.lowbattery = False
        self.force_command = 0
        #self.update()

    def update(self):
        """Reads the current temperature from the thermostat. We need to kill
        the gatttool process as the --listen option puts it into an infinite
        loop."""
        p = subprocess.Popen(["timeout", "-s", "INT", "4", "gatttool", "-b",
                              self.address, "--char-write-req", "-a", "0x0411",
                              "-n", "03", "--listen"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        value_string = out.decode("utf-8")

        if "Notification handle" in value_string:
            value_string_splt = value_string.split()
            #temperature = value_string_splt[-1]
            locked = value_string_splt[-4]
            batt = value_string_splt[-13]
            BITMASK_BATTERY = 0x80
            
            if batt & BITMASK_BATTERY:
            	self.lowbattery = True
            else:
            	self.lowbattery = False
            
            try:
                subprocess.Popen.kill(p)
            except ProcessLookupError:
                pass

            if locked == "20":
                self.locked = True
            elif locked == "00":
                self.locked = False
            else:
                print("Could not read lockstate of {}".format(self.address))
            return True
			
            #try:
            #    self.temperature = int(temperature, 16) / 2
            #except Exception as e:
            #    print("Getting temperature of {} failed {}".format(self.address, e))
        else:
        	return False

    def activate_boostmode(self):
        """Boostmode fully opens the thermostat for 300sec."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "4501"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def deactivate_boostmode(self):
        """Use only to stop boostmode before 300sec."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "4500"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_automatic_mode(self):
        """Put thermostat in automatic mode."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "4000"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_manual_mode(self):
        """Put thermostat in manual mode."""
        try:
            if (self.remoteaddress):
                r = requests.get('http://'+self.remoteaddress+'/manualmode?mac='+self.address, timeout=30)            
            else:
                p = subprocess.Popen(["timeout" ,"20", "gatttool", "-b", self.address, "--char-write-req",
                                "-a", "0x0411", "-n", "4040"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            traceback.print_exc(file=sys.stderr)
            self.failedtimes = self.failedtimes + 1
            return False

    def set_eco_mode(self):
        """Put thermostat in eco mode."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "4080"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def lock_thermostat(self):
        """Locks the thermostat for manual use."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "8001"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def unlock_thermostat(self):
        """Unlocks the thermostat for manual use."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "8000"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_temperature(self, temperature):
        """Transform the temperature in celcius to make it readable to the thermostat."""
        try:
            if (self.remoteaddress):
                r = requests.get('http://'+self.remoteaddress+'/settemp?mac='+self.address+"&temp="+str(temperature), timeout=30)
                self.failedtimes = 0
            else:
                temperature = hex(int(2 * float(temperature)))[2:]
                p = subprocess.Popen(["timeout" ,"20", "gatttool", "-b", self.address, "--char-write-req",
                                        "-a", "0x0411", "-n", "41{}".format(temperature)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    	        # Block for 3 secs to let the thermostat adjust the temperature
                stdout, stderr = p.communicate()
    	        #print(stdout)
                time.sleep(3)
        except:
            traceback.print_exc(file=sys.stderr)
            self.failedtimes = self.failedtimes + 1
            return False
    
    def set_valve_open(self):
        try:
            if (self.remoteaddress):
                r = requests.get('http://'+self.remoteaddress+'/valve?mac='+self.address+"&status=open", timeout=30)
                response = r.json()
                if (response[0]['result']=='done'):
                    self.temperature = 100
                    self.failedtimes = 0
                    return True
                else:
                    self.failedtimes = self.failedtimes + 1
                    return False
            else:
                p = subprocess.Popen(["timeout" ,"20", "gatttool", "-b", self.address, "--char-write-req",
    	                              "-a", "0x0411", "-n", "413c"],
    	                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    	        # Block for 2 secs to let the thermostat adjust the temperature
                stdout, stderr = p.communicate()
                value_string = stdout.decode("utf-8")
    	#        print(value_string)
    	#        print(stderr)
                time.sleep(2)
                if "success" in value_string:
                    self.temperature = 100
                    self.failedtimes = 0
                    return True
                else:
                    self.failedtimes = self.failedtimes + 1
                    return False
        except:
            traceback.print_exc(file=sys.stderr)
            self.failedtimes = self.failedtimes + 1
            return False
    
    def set_valve_close(self):
        try:
            if (self.remoteaddress):
                r = requests.get('http://'+self.remoteaddress+'/valve?mac='+self.address+"&status=closed", timeout=30)
                response = r.json()
                if (response[0]['result']=='done'):
                    self.temperature = 0
                    self.failedtimes = 0
                    return True
                else:
                    self.failedtimes = self.failedtimes + 1
                    return False
            else:
                p = subprocess.Popen(["timeout" ,"20", "gatttool", "-b", self.address, "--char-write-req",
    	                              "-a", "0x0411", "-n", "4109"],
    	                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    	        # Block for 2 secs to let the thermostat adjust the temperature
                stdout, stderr = p.communicate()
                value_string = stdout.decode("utf-8")
    	#        print(value_string)
    	#        print(stderr)
                time.sleep(2)
                if "success" in value_string:
                    self.temperature = 0
                    self.failedtimes = 0
                    return True
                else:
                    self.failedtimes = self.failedtimes + 1
                    return False
        except:
            traceback.print_exc(file=sys.stderr)
            self.failedtimes = self.failedtimes + 1
            return False

    def set_temperature_offset(self, offset):
        """Untested."""
        temperature = hex(int(2 * float(offset) + 7))[2:]
        p = subprocess.Popen(["timeout" ,"20", "gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "13{}".format(temperature)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_day(self):
        """Puts thermostat into day mode (sun icon)."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "43"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_night(self):
        """Puts thermostat into night mode (moon icon)."""
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "44"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_day_night(self, night, day):
        """Sets comfort temperature for day and night."""
        day = hex(int(2 * float(day)))[2:]
        night = hex(int(2 * float(night)))[2:]
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "11{}{}".format(day, night)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_windows_open(self, temperature, duration_min):
        """Untested."""
        temperature = hex(int(2 * float(temperature)))[2:]
        duration_min = hex(int(duration_min / 5.0))[2:]
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", "11{}{}".format(temperature, duration_min)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_time(self, datetimeobj):
        """Takes a datetimeobj (like datetime.datetime.now()) and sets the time
        in the thermostat."""
        command_prefix = "03"
        year = "{:02X}".format(datetimeobj.year % 100)
        month = "{:02X}".format(datetimeobj.month)
        day = "{:02X}".format(datetimeobj.day)
        hour = "{:02X}".format(datetimeobj.hour)
        minute = "{:02X}".format(datetimeobj.minute)
        second = "{:02X}".format(datetimeobj.second)
        control_string = "{}{}{}{}{}{}{}".format(
                          command_prefix, year, month, day, hour, minute, second)
        p = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                              "-a", "0x0411", "-n", control_string],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Block for 3 secs to let the thermostat adjust the settings
        time.sleep(3)

#if __name__ == '__main__':
#    h = EQ3Thermostat("00:1A:22:16:8B:E9")
#    # Take some time
#    time.sleep(5)
    # Deactivate autonomous behavior on the thermostat
#    h.set_manual_mode()
    # Set current date
#    h.set_time(datetime.datetime.now())
    # Set the current temperature
#    h.set_temperature(20)
#    print(h.temperature)
