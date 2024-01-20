import json
import subprocess
import requests
import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import tz

class Custom():
	# {
	# 	"on" : str, #String Value containing a bash or http command to execute
	# 	"off" : str, #String Value containing a bash or http command to execute
	# 	"set_temp" : str, #String Value containing a bash or http command to execute
	# 	"get_status" str, #String Value containing a bash or http command to execute
	# 	"update": str #String Value containing a bash or http command to execute
	# 	"success": str #String Value containing an evaluation for it to measure successfull execution in json if None, with HTTP it will consider http200.
	# }
	
	def __init__(self, custom, protocol):
		self.power = False
		self.temp = 0.0
		self.last_change = None
		self.exclude = False
		self.status = 'initializing'
		self.custom = custom
		self.ingesteld = 0
		self.name = 'custom'
		self.failedtimes = 0
		self.oncmd = None
		self.offcmd = None
		self.set_tempcmd = None
		self.get_statuscmd = None
		self.updatecmd = None
		self.cmd_success = None
		self.protocol = protocol
		self._load_commands()
		self.force_command = 0

	def cur_time(self):
		utc = datetime.now()
		# Tell the datetime object that it's in UTC time zone since 
		# datetime objects are 'naive' by default
		utc = utc.replace(tzinfo=tz.gettz('UTC'))
		# Convert time zone
		utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
		utcstr = utc.strftime('%Y-%m-%d %H:%M:%S')
		#now = datetime.strptime(utcstr, "%Y-%m-%d %H:%M:%S")
		return ("[%s]" % (utc.strftime('%Y-%m-%d %H:%M:%S'),))

	def _load_commands(self):
		try:
			print("%s Parsing custom object commands: %s" % (self.cur_time(),self.custom), file=sys.stderr)
			c = json.loads(self.custom)
			self.custom = c
		except:
			c = None
			print("%s Error parsing custom object: %s" % (self.cur_time(),json.dumps(c)), file=sys.stderr)
		try:
			self.oncmd = c['on']
		except:
			self.oncmd = None
		print("%s Custom object on command: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
		try:
			self.offcmd = c['off']
		except:
			self.offcmd = None
		print("%s Custom object off command: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)
		try:
			self.set_tempcmd = c['set_temp']
		except:
			self.set_tempcmd = None
		try:
			self.get_statuscmd = c['get_status']
		except:
			self.get_statuscmd = None
		try:
			self.updatecmd = c['update']
		except:
			self.updatecmd = None
		try:
			self.cmd_success = c['success']
		except:
			self.cmd_success = None
		print("%s Custom object success evaluation: %s" % (self.cur_time(),self.cmd_success), file=sys.stderr)

	def set_on(self, test):
		if self.oncmd:
			if test:
				return True
			if str.upper(self.protocol) == 'HTTP':
				print("%s Requesting from custom object: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
				try:
					r = requests.get(self.oncmd, timeout=5)
				except:
					return False
				if self.cmd_success:
					response = r.text
					if response == self.cmd_success:
						return True
					else:
						print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
						return False						
				else:
					if r.status_code == 200:
						return True
					else:
						print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
						return False						
			else: #lets execute a bash command
				try:
					p = subprocess.Popen([self.oncmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					out, err = p.communicate()
				except FileNotFoundError:
					print("%s Invalid command in custom object: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)

				if p:
					if self.cmd_success:
						response = out.decode("utf-8")
						if response == self.cmd_success:
							return True
						else:
							print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
							return False							
					else:
						if p.returncode == 0:
							return True
						else:
							print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.oncmd), file=sys.stderr)
							return False
				else:
					return False
		else:
			print("%s Did not set on_command in custom object " % (self.cur_time(),), file=sys.stderr)
			return False
    
	def set_off(self, test):
		if self.offcmd:
			if test:
				return True
			if str.upper(self.protocol) == 'HTTP':
				try:
					r = requests.get(self.offcmd, timeout=5)
				except:
					return False
				if self.cmd_success:
					response = r.text
					if response == self.cmd_success:
						return True
					else:
						print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)
						return False						
				else:
					if r.status_code == 200:
						return True
					else:
						print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)
						return False						
			else: #lets execute a bash command
				try:
					p = subprocess.Popen([self.offcmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					out, err = p.communicate()
				except FileNotFoundError:
					print("%s Invalid command in custom object: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)

				if p:
					if self.cmd_success:
						response = out.decode("utf-8")
						if response == self.cmd_success:
							return True
						else:
							return False
							print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)
					else:
						if p.returncode == 0:
							return True
						else:
							print("%s Invalid response in custom object command: %s" % (self.cur_time(),self.offcmd), file=sys.stderr)
							return False
				else:
					return False
		else:
			print("%s Did not set off_command in custom object " % (self.cur_time(),), file=sys.stderr)
			return False

	def update(self):
		pass
    
	def set_temp(self):
		pass