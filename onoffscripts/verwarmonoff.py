import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import tz
import requests
from eq3_control_object import EQ3Thermostat
from daikin_control_object import Airco
from custom_control_object import Custom
import traceback
import os
import json

def mysort(e)										:
	return e['priority']

def cur_time():
	utc = datetime.now()
	# Tell the datetime object that it's in UTC time zone since 
	# datetime objects are 'naive' by default
	utc = utc.replace(tzinfo=tz.gettz('UTC'))
	# Convert time zone
	utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
	utcstr = utc.strftime('%Y-%m-%d %H:%M:%S')
	#now = datetime.strptime(utcstr, "%Y-%m-%d %H:%M:%S")
	return ("[%s]" % (utc.strftime('%Y-%m-%d %H:%M:%S'),))

def CV_openclose(t, test):
	global rpi
	if test:
		return True
	r = requests.post(rpi+'bridge/heatingCircuits/hc1/temperatureRoomManual', json = {"value":t}, timeout=5)
	response = r.json()
	if response['status'] == "ok":
		#next one
		r = requests.post(rpi+'bridge/heatingCircuits/hc1/manualTempOverride/status', json = {"value":"on"}, timeout=5)
		response = r.json()
		if response['status'] == "ok":
			#next one
			r = requests.post(rpi+'bridge/heatingCircuits/hc1/manualTempOverride/temperature', json = {"value":t}, timeout=5)
			response = r.json()
			if response['status'] == "ok":
				return True
			else:
				raise Exception('Could not succesfully connect to heating system')
		else:
			raise Exception('Could not succesfully connect to heating system')
	else:
		raise Exception('Could not succesfully connect to heating system')

def load_forecast():
	global forecast
	forecast = None
	try:
		r = requests.get('https://api.weather.com/v3/wx/forecast/daily/5day?geocode='+latitude+','+longitude+'&units=m&language=en-US&format=json&apiKey='+apikey, timeout=5)
		response = r.json()
		forecast = response
	except:
		forecast = None

def highest_airco_temp(ip,ro):
	t = 0.0
	for room in ro:
		for device in room['devices']:
			if device['ip'] == ip:
				if room['ingesteld'] > t:
					t = room['ingesteld']
	return t

def clean_device_list(response, test=False):
	global device_list
	tmp_device_list_add = []
	tmp_device_list_rm = device_list.copy()
	for kmr in response['kamer']:
		for device in kmr['devices']:
			if hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name'])) in device_list:
				del tmp_device_list_rm[hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name']))]
			else:
				#found a new device, initialise it
				#store it in a temp list, because we might have redundant devices as well
				#we'll add it later
				tmp_device_list_add.append(device)
	#check if there are redundant devices (the other way around) and close the objects
	print("%s Redundant devices %s" % (cur_time(),len(tmp_device_list_rm)), file=sys.stderr)
	for d in tmp_device_list_rm.keys():
		del device_list[d]
	
	#add the new found ones (if any) and initialize them
	if len(tmp_device_list_add)>0:
		for d in tmp_device_list_add:
			print("%s Found new %s, initializing, hash %s" % (cur_time(),d['name'],hash(hash(d['mac'])+hash(d['ip'])+hash(json.dumps(d['custom']))+hash(d['protocol'])+hash(d['name']))), file=sys.stderr)
			if d['name'] == 'radiator':
				h = EQ3Thermostat(d['mac'])
				device_list[hash(hash(d['mac'])+hash(d['ip'])+hash(json.dumps(d['custom']))+hash(d['protocol'])+hash(d['name']))] = h
				#h.set_manual_mode()
				if not test:
					time.sleep(4) # wait for stabilization
				#h.lock_thermostat()
			elif d['name'] == 'airco':
				a = Airco(d['ip'])
				a.update(test)
				a.last_change = d['last_change']
				device_list[hash(hash(d['mac'])+hash(d['ip'])+hash(json.dumps(d['custom']))+hash(d['protocol'])+hash(d['name']))] = a
			else: #custom
				c = Custom(d['custom'],d['protocol'])
				device_list[hash(hash(d['mac'])+hash(d['ip'])+hash(json.dumps(d['custom']))+hash(d['protocol'])+hash(d['name']))] = c

def check_opening_offset(device, huidig, ingesteld, offset=None):
	global airco_heating_offset, heating_offset
	print("%s Checking heating offset for %s. Ingesteld: %s, Huidig: %s and custom Offset: %s" % (cur_time(),device['name'],ingesteld,huidig,offset), file=sys.stderr)
	if device['name'] == 'airco':
		if float(ingesteld - huidig) > float(airco_heating_offset):
			return True
		else:
			return False
	else: #same for radiator and custom
		# if offset == 0:
		# 	offset = None
		if offset != None:
			if float(ingesteld - huidig) > float(offset):
				return True
			else:
				return False	
		else:
			if float(ingesteld - huidig) > float(heating_offset):
				return True
			else:
				return False

def process_rooms(response, test=False):
	global closing_offset, device_list, smartheating, smartheating, outside_temp, device_open, device_close, exclude, outofsync, tempdiff, airco_ht_inc, verwarming
	t1 = 0
	try:
		outside_temp = float(response['otemp'][0]['otemp'])
	except:
		outside_temp = load_ot()

	while t1 < len(response['kamer']):
		if response['kamer'][t1]['ingesteld']:
			ingesteld = float(response['kamer'][t1]['ingesteld'])
		else:
			ingesteld = 0
		if response['kamer'][t1]['huidig']:
			huidig = float(response['kamer'][t1]['huidig'])
		else:
			huidig = 0
		# if not verwarming: #if there is no hot water in the pipes. Don't count on a closing offset
		# 	closing_offset = 0
		insync = response['kamer'][t1]['insync']
		
		if response['kamer'][t1]['exclude'] == True : #temperature is set manually on the radiator head or on airco
			#send the temp to the radiator heads or airco
			#put to manual mode
			print("%s Room %s in full manual mode. Excluding further instructions" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
			for device in response['kamer'][t1]['devices']:
				hashy = hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name']))
				exclude.append(hashy)
				if device_list[hashy].exclude == False:
					device_list[hashy].exclude = True
					device_list[hashy].status = 'exclude'

		else: #automated radiator control or via console at least
			if response['kamer'][t1]['handmatig']: #temp is set via the console manually for a period of time, managed by controller
				print("%s Room %s in manual mode, via console" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
			else:
				print("%s Room %s in automated mode" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
			if insync:
				#check if there is a closing offset defined, else use the general set one
				print("%s In sync len %s devices" % (cur_time(),len(response['kamer'][t1]['devices'])), file=sys.stderr)
				co = None
				try:
					co = response['kamer'][t1]['offset']
				except NameError:
					co = closing_offset
				if co == None:
					co = closing_offset
				
				try:
					smartheating = response['kamer'][t1]['smartheat']
				except NameError:
					smartheating = False
				
				if smartheating: #if smartheating is on. Try read the weather forecast
					print("%s Smart heating on" % (cur_time(),), file=sys.stderr)
					try:
						smartheatingcounter = smartheatingcounter + 1
						utc = datetime.now()
						utc = utc.replace(tzinfo=tz.gettz('UTC'))
						utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
						if utc.time() < time(0,2): #Reset timer right after 12 at night, so we get fresh forecast
							smartheatingcounter = 721									
						
						if smartheatingcounter >= 720:
							load_forecast()
							smartheatingcounter = 0
						if forecast != None:
							#if we know that it will become 20 degrees, why heatup? lets heat up to like 20-4=16 if needed
							#likewise if we know it will become 15, lets heat up to like at least 15-4=11 degrees, if needed
							#for this sake, overwrite the set temp, so it will not heat up, while the sun will do the rest
							if response['temperatureMax'][0] != None:
								smartheat = (response['temperatureMax'][0] + co) - 4
								if smartheat < ingesteld:
									ingesteld = smartheat
					except:
						ingesteld = float(response['kamer'][t1]['ingesteld']) #rolback, don't do anything
				if ingesteld > huidig:
					#create list in order of given priority
					response['kamer'][t1]['devices'].sort(key=mysort)
					
					#cycle over devices in order of priority
					#heat up using the highest priority device
					#unless last_change is > 1 hr
					#then use all other devices
					lastprio = 1
					use_next_device = True
					for device in response['kamer'][t1]['devices']:
						hashy = hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name']))
						if use_next_device or lastprio == device['priority']: #keep track of prio devices #if there are multiple devices with the same prio, it should treat as one
							use_next_device = False
							#if device.power or device.status == 'on': #this device was already powered up													
							if device_list[hashy].status == 'on': #this device was already powered up													
								nu = datetime.now()
								nu = nu.replace(tzinfo=tz.gettz('UTC'))
								nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
								if device['name'] == 'airco': #for airco it is set to the associated room with the highest set temperature
									tmp_ingesteld = highest_airco_temp(device['ip'],response['kamer'])
								else:
									tmp_ingesteld = ingesteld								
								if tmp_ingesteld != device_list[hashy].ingesteld: #if new temperature is set, reset last_change timer
									device_list[hashy].last_change = nu
									print("%s Room %s old temperature(%s) changed to (%s), resending new instructions" % (cur_time(),response['kamer'][t1]['tid'],device_list[hashy].ingesteld,ingesteld), file=sys.stderr)
								else:
									if device_list[hashy].last_change:
										last_change_delta = device_list[hashy].last_change + timedelta(minutes=60)
									else:
										last_change_delta = nu
									if last_change_delta < nu: # if it is very long (>1 hr) and temp is not met... # useAC = False, but leave it on
										print("%s Room %s is heating with initial device. But for more than 1 hr already (since: %s), start using next" % (cur_time(),response['kamer'][t1]['tid'], device_list[hashy].last_change), file=sys.stderr)
										use_next_device = True

							if device['name'] == 'airco' and outside_temp < -5: # if outside temp is lower than -5, no use in starting airco
								print("%s Outside temp (%s) is too low for efficient airco" % (cur_time(),outside_temp), file=sys.stderr)
								use_next_device = True	#What if there is no other device? then we should use airco
								if len(response['kamer'][t1]['devices']) > 1:
									device_close.append(hashy)
								else:
									if check_opening_offset(device, huidig, ingesteld): #We need to see if the opening offset is met
										print("%s But only an airco is available for this room" % (cur_time()), file=sys.stderr)
										device_open.append(hashy)
										device_list[hashy].ingesteld = ingesteld
										use_next_device = False
									else:
										device_close.append(hashy)
							else: #custom device & radiator
								#first check offset
								if check_opening_offset(device, huidig, ingesteld, co) or device_list[hashy].status == 'on': #We need to see if the opening offset is met, unless it was already open
									if device['name'] == 'airco':
										device_list[hashy].ingesteld = highest_airco_temp(device['ip'],response['kamer']) #find highest temperature set for the airco unit
									else:
										device_list[hashy].ingesteld = ingesteld
									device_open.append(hashy)
									print("%s Room %s starts heating with %s. Excluding further instructions for now" % (cur_time(),response['kamer'][t1]['tid'],device['name']), file=sys.stderr)									
								else: 
									device_close.append(hashy)
									print("%s Room %s wants to start heating with %s, but is not within heating offset" % (cur_time(),response['kamer'][t1]['tid'],device['name']), file=sys.stderr)

							if device['name'] == 'radiator': #keep track of highest difference in temperature for CV heating
								diff = ingesteld - huidig
								if tempdiff < diff: 
									tempdiff = diff
							lastprio = device['priority']#if there are multiple devices with the same prio, it should treat as one
						else:
							device_close.append(hashy)

				#else: # temp has been met (taking offset into account), shut down all radiators. and airco's?
				else: # temp has been met, shut down all devices
					for device in response['kamer'][t1]['devices']:
						device_close.append(hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name'])))

			else: #problems with receiving measurements from thermostats, we need to switch to an alternative
				#manually set the temperature, so that it doesnt overheat the room
				#also it will not be taken into account in the boiler heating
				#if it's solved, it will return to normal
				print("%s Not in sync len %s devices" % (cur_time(),len(response['kamer'][t1]['devices'])), file=sys.stderr)
				for device in response['kamer'][t1]['devices']:
					hashy = hash(hash(device['mac'])+hash(device['ip'])+hash(json.dumps(device['custom']))+hash(device['protocol'])+hash(device['name']))
					outofsync.append(hashy)
			
		t1 = t1 + 1
	print("%s Number of devices to open %s" % (cur_time(),len(device_open)), file=sys.stderr)
	print("%s Number of devices to close %s" % (cur_time(),len(device_close)), file=sys.stderr)
	print("%s Number of devices to exclude %s" % (cur_time(),len(exclude)), file=sys.stderr)
	print("%s Number of devices out of sync %s" % (cur_time(),len(outofsync)), file=sys.stderr)

def device_on_off(test=False):
	global device_list, device_open, device_close, exclude, outofsync, airco_ht_inc, serious_radiator_problem
	serious_radiator_problem = False
	for device_hash in device_list.keys():
		if device_hash in device_open:
			if device_list[device_hash].name == 'radiator':
				print("%s Opening radiator %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
				if device_list[device_hash].temperature == 100 and device_list[device_hash].status != 'error' and device_list[device_hash].force_command < 5: #force a fresh signal at least every 5 minutes
					device_list[device_hash].status = 'on' #radiator is already open, don't do anything
					print("%s Radiator already open" % (cur_time(),), file=sys.stderr)
					device_list[device_hash].force_command = device_list[device_hash].force_command + 1
				else:
					if device_list[device_hash].set_valve_open(test):
						print("%s Success for %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
						device_list[device_hash].status = 'on'
						device_list[device_hash].force_command = 0
					else:
						print("%s Failed for %s, retry next time" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
						device_list[device_hash].force_command = device_list[device_hash].force_command + 1
			elif device_list[device_hash].name == 'airco':
				print("%s Starting airco %s" % (cur_time(),device_list[device_hash].host), file=sys.stderr)
				device_list[device_hash].temp = device_list[device_hash].ingesteld + airco_ht_inc
				device_list[device_hash].mode = 4
				device_list[device_hash].fdir = 0
				device_list[device_hash].frate= 'A'
				doit = False
				if device_list[device_hash].power == False:
					device_list[device_hash].power = True
					if device_list[device_hash].activate_settings(test):
						nu = datetime.now()
						nu = nu.replace(tzinfo=tz.gettz('UTC'))
						nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
						device_list[device_hash].status = 'on'
						device_list[device_hash].last_change = nu
						print("%s Started Airco: %s" % (cur_time(),device_list[device_hash].host), file=sys.stderr)
						doit = True
					else:
						doit = False
				else:
					print("%s Airco already running, keep going" % (cur_time(),), file=sys.stderr)
					doit = True
				if doit == False:
					print("%s ERROR; Couldnt start airco" % (cur_time(),), file=sys.stderr)
			else: #custom
				print("%s Opening custom object %s" % (cur_time(),device_hash), file=sys.stderr)
				if device_list[device_hash].status == 'on' and device_list[device_hash].status != 'error' and device_list[device_hash].force_command < 5: #force a fresh signal at least every 5 minutes
					print("%s Custom object already open" % (cur_time(),), file=sys.stderr)
					device_list[device_hash].force_command = device_list[device_hash].force_command + 1
				else:
					if device_list[device_hash].set_on(test):
						print("%s Success for %s" % (cur_time(),device_hash), file=sys.stderr)
						device_list[device_hash].status = 'on'
						device_list[device_hash].force_command = 0
					else:
						print("%s Failed for %s, retry next time" % (cur_time(),device_hash), file=sys.stderr)
						device_list[device_hash].force_command = device_list[device_hash].force_command + 1
		elif device_hash in device_close or device_hash in outofsync:
			if device_hash in outofsync:
				print("%s Thermostat out of sync, closing device by default" % (cur_time(),), file=sys.stderr)
			if device_list[device_hash].name == 'radiator':			
				print("%s Closing radiator %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
				if device_list[device_hash].temperature == 0 and device_list[device_hash].status != 'error' and device_list[device_hash].force_command < 5: #force a fresh signal at least every 5 minutes
					device_list[device_hash].status = 'off' #radiator is already closed, don't do anything
					print("%s Radiator already closed" % (cur_time(),), file=sys.stderr)
					device_list[device_hash].force_command = device_list[device_hash].force_command + 1
				else:
					if device_list[device_hash].set_valve_close(test):
						print("%s Success for %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
						device_list[device_hash].status = 'off'
						device_list[device_hash].force_command = 0
					else:
						print("%s Failed for %s, retry next time" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
						device_list[device_hash].force_command = device_list[device_hash].force_command + 1
			elif device_list[device_hash].name == 'airco':
				print("%s Temp has been met, shut down airco" % (cur_time(),), file=sys.stderr)
				doit = False
				if device_list[device_hash].power == True:
					device_list[device_hash].power = False
					if device_list[device_hash].activate_settings(test):
						device_list[device_hash].status = 'off'						
						print("%s Airco: %s is shut down" % (cur_time(),device_list[device_hash].host), file=sys.stderr)
						doit = True
					else:
						doit = False
				else:
					print("%s Airco was already down" % (cur_time(),), file=sys.stderr)
					device_list[device_hash].status = 'off'
					doit = True
				if doit == False:
					print("%s ERROR; Couldnt start airco" % (cur_time(),), file=sys.stderr)
			else:
				print("%s Closing custom object %s" % (cur_time(),device_hash), file=sys.stderr)
				if device_list[device_hash].status == 'off' and device_list[device_hash].status != 'error' and device_list[device_hash].force_command < 5: #force a fresh signal at least every 5 minutes
					print("%s Custom object already closed" % (cur_time(),), file=sys.stderr)
					device_list[device_hash].force_command = device_list[device_hash].force_command + 1
				else:
					if device_list[device_hash].set_off(test):
						print("%s Success for %s" % (cur_time(),device_hash), file=sys.stderr)
						device_list[device_hash].status = 'off'
						device_list[device_hash].force_command = 0
					else:
						print("%s Failed for %s, retry next time" % (cur_time(),device_hash), file=sys.stderr)
						device_list[device_hash].force_command = device_list[device_hash].force_command + 1
		elif device_hash in exclude:
			pass #dont do anything
		#elif device_hash in outofsync:
		else:
			print("%s Debug Device_list%s" % (cur_time(),device_list), file=sys.stderr)
			print("%s Debug Device_open%s" % (cur_time(),device_open), file=sys.stderr)
			print("%s Debug Device_close%s" % (cur_time(),device_close), file=sys.stderr)
			print("%s Debug Device_exclude%s" % (cur_time(),exclude), file=sys.stderr)
			print("%s Debug Device_outofsync%s" % (cur_time(),outofsync), file=sys.stderr)
			raise Exception('Unknown radiator head(%s), something is terribly wrong' % (+device_hash,))
		if device_list[device_hash].failedtimes > 15: #something is wrong... more than 15 minutes of failures
			device_list[device_hash].status = 'error'
			serious_radiator_problem = True

		#send radiator and CV status to database
		
		if not test and device_list[device_hash].name == 'radiator':
			try:
				print("%s Sending to db for %s status: %s" % (cur_time(),device_list[device_hash].address,device_list[device_hash].status), file=sys.stderr)
				a = device_list[device_hash].address
				if device_list[device_hash].remoteaddress:
					a = device_list[device_hash].address+"@"+device_list[device_hash].remoteaddress							
				rpi_temp = rpi.split(":")[0]+":"+rpi.split(":")[1]
				r = requests.post(rpi_temp+':6543/setradiatorvalve', data = {'valve' : device_list[device_hash].status, 'mac': a}, timeout=5)
				#r = requests.post('http://192.168.0.158:5000/setradiator', data = {'valve' : status, 'mac': radiator_list[t4].address})
			except:
				traceback.print_exc()
				print("%s Failed to send radiator status to database for %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)

def boiler_on_off(test=False):
	global device_list, device_open, device_close, verwarming, serious_radiator_problem, heatingcounter, tempdiff, heating_offset, first_load
	#if there are any rooms that need heating by radiator, heat up boiler
	radiator_open = False
	for device_hash in device_list.keys():
		if device_hash in device_open:
			if device_list[device_hash].name == 'radiator':
				radiator_open = True #at least one radiator device is open
				break

	if radiator_open:
		if serious_radiator_problem:
			#If a closing radiator is in error for 15min, we should close CV as well... else it will overheat
			#unless there is nothing else open anyway
			print("%s Opening_radiator_problem, closing CV to prevent overheat" % (cur_time(),), file=sys.stderr)
			if CV_openclose(5, test):
				verwarming = False
				heatingcounter = 0
		else:
			print("%s Radiators are open, warming up CV" % (cur_time(),), file=sys.stderr)
			print("%s Biggest difference %s and heating offset %s" % (cur_time(),tempdiff,heating_offset), file=sys.stderr)
			if float(tempdiff) > float(heating_offset): 
				#Only heat up the boiler is there is at least one room where the temp exceeds the heating offset 
				#and warm water is still in the pipes
				print("%s There is a huge temperature difference, warming up CV" % (cur_time(),), file=sys.stderr)
				if CV_openclose(30, test):
					verwarming = True
			else:
				print("%s Difference in temp is within offset" % (cur_time(),), file=sys.stderr)
				if verwarming or first_load: #if it was still heating, close it
					print("%s Hot water is still active, we can already close CV assuming it will remain heating to set temperature" % (cur_time(),), file=sys.stderr)
					if CV_openclose(5, test):
						verwarming = False
				else:
					print("%s CV is already closed" % (cur_time(),), file=sys.stderr)
	else:
		print("%s No radiators open, closing CV" % (cur_time(),), file=sys.stderr)
		heatingcounter = heatingcounter + 1
		if verwarming or first_load or heatingcounter > 15: #if it was still heating, close it
			if CV_openclose(5, test):
				verwarming = False
				heatingcounter = 0

#########
## Todo:
## - lock radiator heads
## - initialize met .ini bestand
#########

#MAINLINE
#initialize
time.sleep(5) #wait for other modules to be available
forecast = None #This is used to load the weather forecast, to determine if we should heat up if smartheating = true
verwarming = False
radiator_list = []
airco_list = []
device_list = {}
updatecounter = 0 #this is a counter which is used to keep track of when to call the radiator head update, so low battery status is checked
first_load = True
heatingcounter = 0 #Sometimes connection is lost with CV, need to at least send a signal every 15min
smartheatingcounter = 0 #we dont want to load every minute. twice a day is enough = 720 minutes/counters
outside_temp = 0 #Keep track of the outside temperature, initialize with 0, updates after 15min
serious_radiator_problem = False #If a closing radiator is in error for 15min, we should close CV as well... else it will overheat

###configurable variables
if os.getenv("VERWARMING_ONOFF_RPI") is not None:
	rpi = os.getenv("VERWARMING_ONOFF_RPI")
else:
	rpi = 'http://192.168.0.125:8000/' #ip:port to the api serving the interface to the CV/heater

if os.getenv("VERWARMING_CLOSING_OFFSET") is not None:
	closing_offset = os.getenv("VERWARMING_CLOSING_OFFSET")
else:
	closing_offset = 0.2 #close radiator head 0.2 a degree earlier as the existing warm water will heat the room up for the last 0.5 degree
if os.getenv("VERWARMING_HEATING_OFFSET") is not None:
	heating_offset = os.getenv("VERWARMING_HEATING_OFFSET")
else:
	heating_offset = 0.7 #stop heating boiler 1 degree before the actual temperature has reached, but keep radiators open. Existing warm water will be enough to heat the room up last degree
if os.getenv("AIRCO_VERWARMING_HEATING_OFFSET") is not None:
	airco_heating_offset = os.getenv("AIRCO_VERWARMING_HEATING_OFFSET")
else:
	airco_heating_offset = 0.4 #start heating up airco from this offset te prevent alot of on/offs
if os.getenv("VERWARMING_SMART_HEAT") is not None:
	smartheating = os.getenv("VERWARMING_SMART_HEAT")
else:
	smartheating = False

if os.getenv("VERWARMING_ONOFF_LON") is not None:
	longitude = os.getenv("VERWARMING_ONOFF_LON")
else:
	longitude = '4.60' 
if os.getenv("VERWARMING_ONOFF_LAT") is not None:
	latitude = os.getenv("VERWARMING_ONOFF_LAT")
else:
	latitude = '51.87' 
if os.getenv("VERWARMING_ONOFF_API") is not None:
	apikey = os.getenv("VERWARMING_ONOFF_API")
else:
	apikey = "b3e2781468f747d3a2781468f7d7d30b"
if os.getenv("AIRCO_OUTSIDE_TEMP_IP") is not None:
	airco_ot_ip = os.getenv("AIRCO_OUTSIDE_TEMP_IP")
else:
	airco_ot_ip = "192.168.0.137"
if os.getenv("AIRCO_HEATING_TEMP_INCREASE") is not None:
	airco_ht_inc = float(os.getenv("AIRCO_HEATING_TEMP_INCREASE"))
else:
	airco_ht_inc = 2.0

if __name__ == '__main__':
	try:
		print("%s Starting up for the first time" % (cur_time(),), file=sys.stderr)
		print("%s Loading status of heating system" % (cur_time(),), file=sys.stderr)
		r = requests.get(rpi+'api/status', timeout=5)
		response = r.json()
		if response['boiler indicator'] == "central heating":
			if response['hot water active'] == "true":
				verwarming = True
		if verwarming:
			print("%s Heating system is already warming" % (cur_time(),), file=sys.stderr)
		else:
			print("%s Heating system not warming" % (cur_time(),), file=sys.stderr)
			verwarming = False

	except:
		print("%s Could not load status of heating system" % (cur_time(),), file=sys.stderr)

	#request status every minute and determine which radiator needs to be opened and closed
	#then send a signal, if any radiator is openen, to heat the CV
	try:
		while True:
			try:
				#r = requests.get('http://verwarmcontroller:5000/verwarmingstatus')
				print("%s Requesting new status" % (cur_time(),), file=sys.stderr)
				rpi_temp = rpi.split(":")[0]+":"+rpi.split(":")[1]
				r = requests.get(rpi_temp+':6543/verwarmingstatus', timeout=5)
				#r = requests.get('http://localhost:5000/verwarmingstatus')
				if r:
					#print("%s Got a response" % (cur_time(),), file=sys.stderr)
					response = r.json()
					#print("%s Contains %s rooms" % (cur_time(),len(response['kamer'])), file=sys.stderr)
					#we have a valid response, loop through all rooms and determine which radiators mac needs to be opened
					device_open = []
					device_close = []
					exclude = []
					outofsync = []
					tempdiff = 0 # this value keeps track of the highest difference in temperature. We need this value later on
					
					#check for new devices and initialise them
					clean_device_list(response)

					try:
						process_rooms(response)
					except:
						print("%s Object integrity error" % (cur_time(),), file=sys.stderr)
						traceback.print_exc()
						break
					
					try:
						print("%s Total of %s devices" % (cur_time(),len(device_list)), file=sys.stderr)
						#loop through all radiator heads and see if it needs to be set to open or close
						device_on_off()						
					except:
						print("%s Failed to open/close all devices(s)" % (cur_time(),), file=sys.stderr)
						traceback.print_exc()

					try:
						boiler_on_off()
					except:
						verwarming = False
						print("%s Failed to start CV" % (cur_time(),), file=sys.stderr)
						traceback.print_exc()
					if first_load:
						first_load = False					

					#once every hour, sync CV status with script?
						
				print("%s Waiting for one minute for next batch" % (cur_time(),), file=sys.stderr)
				time.sleep(60)
				updatecounter = updatecounter + 1
				#if updatecounter == 15 or updatecounter == 30 or updatecounter == 45 or updatecounter == 60: #call update every 15min to update outside temp
					#outside_temp = load_ot()
				if updatecounter > 60: #call update every hour to check for battery status
					for device_hash in device_list:
						if device_list[device_hash].name == 'radiator':
							try:
								print("%s Checking for battery for %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
								if radiator_list[t4].update:
									print("%s Lowbattery status %s " % (cur_time(),device_list[device_hash].lowbattery), file=sys.stderr)
								a = device_list[device_hash].address
								if device_list[device_hash].remoteaddress:
									a = device_list[device_hash].address+"@"+device_list[device_hash].remoteaddress
								rpi_temp = rpi.split(":")[0]+":"+rpi.split(":")[1]
								r = requests.post(rpi_temp+':6543/setradiatorbattery', data = {'lowbattery' : str(device_list[device_hash].lowbattery), 'mac': a}, timeout=5)
							except:
								traceback.print_exc()
								print("%s Failed to send radiator status to database for %s" % (cur_time(),device_list[device_hash].address), file=sys.stderr)
					updatecounter = 0
					
			except KeyboardInterrupt:
				print("%s netjes afsluiten" % (cur_time(),), file=sys.stderr)
				sys.exit(0)
				
			except:
				traceback.print_exc()
				print("%s Failed to get status" % (cur_time(),), file=sys.stderr)
				print("%s Waiting for one minute for next batch" % (cur_time(),), file=sys.stderr)
				time.sleep(60)

	except KeyboardInterrupt:
		print("%s netjes afsluiten" % (cur_time(),), file=sys.stderr)
