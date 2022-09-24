import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import tz
import requests
from eq3_control_object import EQ3Thermostat
from daikin_control_object import Airco
import traceback
import os

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

def CV_openclose(t):
	global rpi
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

def isknownhead(mac):
	global radiator_list
	t1 = 0
	while t1 < len(radiator_list):
		if radiator_list[t1].address == mac:
			return True		
		t1 = t1 + 1
	return False

def isknownairco(ip):
	global airco_list
	t1 = 0
	while t1 < len(airco_list):
		if airco_list[t1].host == ip:
			return True		
		t1 = t1 + 1
	return False

def load_ot():
	try:
		r = requests.get('http://'+airco_ot_ip+'/aircon/get_sensor_info', timeout=5)
		returnobject = r.text.split(",")
		if returnobject[0].split("=")[1] == "OK":
			for o in returnobject:
				if o.split("=")[0] == 'otemp':
					return float(o.split("=")[1])
		else:
			return 0
		
	except:
		return 0

def highest_airco_temp(ip,ro):
	t = None
	for room in ro:
		if room['airco'][0]['ip'] == ip:
			if room['ingesteld'] > t:
				t = room['ingesteld']
	return t

#########
## Todo:
## - lock radiator heads
## - if ingesteld > huidig -> more smarter opening and closing of radiators (for example when its heating, already close radiator half a degree earlier)
## - offset per room
## - discovery modus voor new radiator heads
## - initialisatie met .ini bestand
#########

#MAINLINE
#initialize
time.sleep(5) #wait for other modules to be available
forecast = None #This is used to load the weather forecast, to determine if we should heat up if smartheating = true
verwarming = False
radiator_list = []
airco_list = []
updatecounter = 0 #this is a counter which is used to keep track of when to call the radiator head update, so low battery status is checked
first_load = True
heatingcounter = 0 #Sometimes connection is lost with CV, need to at least send a signal every 15min
smartheatingcounter = 0 #we dont want to load every minute. twice a day is enough = 720 minutes/counters
outside_temp = 0 #Keep track of the outside temperature, initialize with 0, updates after 15min

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
			#r = requests.get('http://192.168.0.158:5000/verwarmingstatus')
			if r:
				#print("%s Got a response" % (cur_time(),), file=sys.stderr)
				response = r.json()
				#print("%s Contains %s rooms" % (cur_time(),len(response['kamer'])), file=sys.stderr)
				#we have a valid response, loop through all rooms and determine which radiators mac needs to be opened
				radiator_open = []
				radiator_close = []
				exclude = []
				outofsync = []
				t1 = 0
				tempdiff = 0 # this value keeps track of the highest difference in temperature. We need this value later on
				try:
					while t1 < len(response['kamer']):
						if response['kamer'][t1]['ingesteld']:
							ingesteld = float(response['kamer'][t1]['ingesteld'])
						else:
							ingesteld = 0
						if response['kamer'][t1]['huidig']:
							huidig = float(response['kamer'][t1]['huidig'])
						else:
							huidig = 0
						if not verwarming: #if there is no hot water in the pipes. Don't count on a closing offset
							closing_offset = 0
						insync = response['kamer'][t1]['insync']
						
						if response['kamer'][t1]['handmatig']: #check if the time has passed for overwrite
							a=0	
						
						if response['kamer'][t1]['exclude'] == True : #temperature is set manually on the radiator head
							#send the temp to the radiator heads
							#put to manual mode
							print("%s Room %s in full manual mode. Excluding further instructions" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
							t2 = 0
							while t2 < len(response['kamer'][t1]['radiator']):
								if response['kamer'][t1]['radiator'][t2]['mac']:
									exclude.append(response['kamer'][t1]['radiator'][t2]['mac'])
									t4 = 0
									while t4 < len(radiator_list): # look up the right object in the list
										if radiator_list[t4].address == response['kamer'][t1]['radiator'][t2]['mac']:
											if radiator_list[t4].exclude == False:
												radiator_list[t4].exclude = True
												radiator_list[t4].set_manual_mode()
												radiator_list[t4].set_temperature(ingesteld) 
											break
										t4 = t4 + 1
								t2 = t2 + 1
							
						else: #automated radiator control or via console at least
							print("%s Room %s in automated mode" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
							if insync:
								#check if there is a closing offset defined, else use the general set one
								print("%s In sync len %s" % (cur_time(),len(response['kamer'][t1]['radiator'])), file=sys.stderr)
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
								
								if len(response['kamer'][t1]['airco']) > 0: #check if this room has an airco
									#check if we already know this airco
									if isknownairco(response['kamer'][t1]['airco'][0]['ip']) != True:
										#add to airco list and initialize
										print("%s New Airco unit found: %s Initializing" % (cur_time(),response['kamer'][t1]['airco'][0]['ip']), file=sys.stderr)
										a = Airco(response['kamer'][t1]['airco'][0]['ip'])
										a.update()
										a.last_change = response['kamer'][t1]['airco'][0]['last_change']
										airco_list.append(a)

								if (ingesteld - co) > huidig: #if there is still hot water in the pipes, we should take closing offset into account
									t2 = 0
									useAC = False									
									if outside_temp < -5: # if outside temp is lower than -5, no use in starting airco
										useAC = False
									else:
										if len(response['kamer'][t1]['airco']) > 0: #check if this room has an airco
											#check if we already know this airco
											if isknownairco(response['kamer'][t1]['airco'][0]['ip']) != True:
												#add to airco list and initialize
												print("%s New Airco unit found: %s Initializing" % (cur_time(),response['kamer'][t1]['airco'][0]['ip']), file=sys.stderr)
												a = Airco(response['kamer'][t1]['airco'][0]['ip'])
												a.update()
												a.last_change = response['kamer'][t1]['airco'][0]['last_change']
												airco_list.append(a)
											
											t4 = 0
											while t4 < len(airco_list): # look up the right object in the list
												if airco_list[t4].host == response['kamer'][t1]['airco'][0]['ip']: #found our airco unit
													if airco_list[t4].power: #if it is already open
														useAC == True
														# if there is a set temp change, we need to send new temp instructions
														# and reset last_change timer

														#find highest temp for the rooms for this airco
														t = highest_airco_temp(response['kamer'][t1]['airco'][0]['ip'],response['kamer'][t1])
														if (airco_list[t4].temp) != t: 
															#apparently temp of one of the rooms has changed. We need to adjust and reset last_change time
															#and re-send new instructions to the unit
															nu = datetime.now()
															nu = nu.replace(tzinfo=tz.gettz('UTC'))
															nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
															airco_list[t4].last_change = nu
															airco_list[t4].temp = t
														else:
															last_change = response['kamer'][t1]['airco'][0]['last_change']
															nu = datetime.now()
															nu = nu.replace(tzinfo=tz.gettz('UTC'))
															nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
															last_change_delta = last_change + timedelta(minutes=60)
															if last_change_delta > nu: # if it is very long (>1 hr) and temp is not met... # useAC = False, but leave it on
																print("%s Room %s is heating with airco. But for more than 1 hr already, start using radiator" % (cur_time(),t1), file=sys.stderr)
																useAC = False #meaning also radiator will start heating up
																#but we don't shut down the airco (yet), until temp is reached
															else:
																print("%s Room %s is heating with airco. Excluding further instructions for now" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
													else: #if it isn't open, start with airco
														useAC = True
														airco_list[t4].temp = float(response['kamer'][t1]['ingesteld'])
														airco_list[t4].mode = 4
														airco_list[t4].fdir = 0
														airco_list[t4].frate= 'A'
														print("%s Room %s starts heating with airco. Excluding further instructions for now" % (cur_time(),response['kamer'][t1]['tid']), file=sys.stderr)
												t4 = t4 + 1

									if useAC == True: #airco is running and therefor all radiators in this room need to be excluded from further instructions
										t4 = 0
										doit = False
										while t4 < len(airco_list): # look up the right object in the list
											if airco_list[t4].host == response['kamer'][t1]['airco'][0]['ip']: #found our airco unit
												airco_list[t4].power = True
												if airco_list[t4].activate_settings():
													print("%s Started Airco: %s" % (cur_time(),airco_list[t4].host), file=sys.stderr)
													doit = True
												break;
											t4 = t4 + 1
										if doit == False:
											print("%s ERROR; Couldnt start airco" % (cur_time(),), file=sys.stderr)
										t2 = 0
										while t2 < len(response['kamer'][t1]['radiator']):
											if response['kamer'][t1]['radiator'][t2]['mac']:
												exclude.append(response['kamer'][t1]['radiator'][t2]['mac'])
												t4 = 0
												while t4 < len(radiator_list): # look up the right object in the list
													if radiator_list[t4].address == response['kamer'][t1]['radiator'][t2]['mac']:
														if radiator_list[t4].exclude == False:
															radiator_list[t4].exclude = True
															radiator_list[t4].set_manual_mode()
															radiator_list[t4].set_temperature(ingesteld) 
														break
													t4 = t4 + 1
											t2 = t2 + 1
									
									else: # AC is not used, lets take a look at the radiators
										diff = ingesteld - huidig
										if tempdiff < diff: #keep track of highest difference in temperature for CV heating
											tempdiff = diff
										if len(response['kamer'][t1]['radiator']) > 0:
											while t2 < len(response['kamer'][t1]['radiator']):
												#print("%s Opening radiotor for room: %s with mac-adres: %s" % (cur_time(),response['kamer'][t1]['naam'],response['kamer'][t1]['radiator'][t2]['mac']), file=sys.stderr)
												if response['kamer'][t1]['radiator'][t2]['mac']:
													if "@" in response['kamer'][t1]['radiator'][t2]['mac']:
														radiator_open.append(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0])
													else:
														radiator_open.append(response['kamer'][t1]['radiator'][t2]['mac'])
													
													if (isknownhead(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0]) != True):
														print("%s Found new radiator head, initializing" % (cur_time(),), file=sys.stderr)
														h = EQ3Thermostat(response['kamer'][t1]['radiator'][t2]['mac'])
														radiator_list.append(h)
														h.set_manual_mode()
														time.sleep(4) # wait for stabilization
														#h.lock_thermostat()
												t2 = t2 + 1
								else: # temp has been met (taking offset into account), shut down all radiators. and airco's?
									# If room has an airco
									# and if airco was running
									if len(response['kamer'][t1]['airco']) > 0: #check if this room has an airco
										t4 = 0
										doit = False
										while t4 < len(airco_list): # look up the right object in the list
											if airco_list[t4].host == response['kamer'][t1]['airco'][0]['ip']: #found our airco unit
												airco_list[t4].power = False
												airco_list[t4].activate_settings()
												doit = True
												break;
											t4 = t4 + 1
										if doit == False:
											print("%s ERROR; Couldnt shut down airco" % (cur_time(),), file=sys.stderr)
									
									t2 = 0
									if len(response['kamer'][t1]['radiator']) > 0:
										while t2 < len(response['kamer'][t1]['radiator']):
											#print("%s Closing radiotor for room: %s with mac-adres: %s" % (cur_time(),response['kamer'][t1]['naam'],response['kamer'][t1]['radiator'][t2]['mac']), file=sys.stderr)
											if response['kamer'][t1]['radiator'][t2]['mac']:
												if "@" in response['kamer'][t1]['radiator'][t2]['mac']:
													radiator_close.append(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0])
												else:
													radiator_close.append(response['kamer'][t1]['radiator'][t2]['mac'])
												
												if (isknownhead(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0]) != True):
													print("%s Found new radiator head, initializing" % (cur_time(),), file=sys.stderr)
													h = EQ3Thermostat(response['kamer'][t1]['radiator'][t2]['mac'])
													radiator_list.append(h)
													h.set_manual_mode()
													time.sleep(4) # wait for stabilization
													#h.lock_thermostat()
												
											t2 = t2 + 1
							else: #problems with receiving measurements from thermostats, we need to switch to an alternative
								#manually set the temperature, so that it doesnt overheat the room
								#also it will not be taken into account in the boiler heating
								#if it's solved, it will return to normal
								print("%s Not in sync len %s" % (cur_time(),len(response['kamer'][t1]['radiator'])), file=sys.stderr)
								t2 = 0
								if len(response['kamer'][t1]['radiator']) > 0:
									while t2 < len(response['kamer'][t1]['radiator']):
										if response['kamer'][t1]['radiator'][t2]['mac']:
											if "@" in response['kamer'][t1]['radiator'][t2]['mac']:
												outofsync.append(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0])
												tempadress = response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0]
											else:
												outofsync.append(response['kamer'][t1]['radiator'][t2]['mac'])
												tempadress = response['kamer'][t1]['radiator'][t2]['mac']
											
											if (isknownhead(response['kamer'][t1]['radiator'][t2]['mac'].split("@")[0]) != True):
												#radiator does not exist yet in the list. Add it and put to error mode
												print("%s Found new radiator head, initializing" % (cur_time(),), file=sys.stderr)
												h = EQ3Thermostat(response['kamer'][t1]['radiator'][t2]['mac'])
												radiator_list.append(h)
												h.set_manual_mode()
												time.sleep(4) # wait for stabilization
												#h.lock_thermostat()
												h.set_temperature(ingesteld) 
											else:
												#try finding it in the list and put to manual mode
												print("%s Radiator head is known, but malfunctioning len %s" % (cur_time(),len(radiator_list)), file=sys.stderr)
												t4 = 0
												while t4 < len(radiator_list): # look up the right object in the list
													if radiator_list[t4].address == tempadress:
														print("%s Put to manual mode" % (cur_time(),), file=sys.stderr)
														radiator_list[t4].set_manual_mode()
														print("%s And set target temp manually" % (cur_time(),), file=sys.stderr)
														radiator_list[t4].set_temperature(ingesteld) 
														break
													t4 = t4 + 1									
													if t4 > len(radiator_list):
														break
										t2 = t2 + 1
							
						t1 = t1 + 1
					print("%s Number of radiators to open %s" % (cur_time(),len(radiator_open)), file=sys.stderr)
					print("%s Number of radiators to close %s" % (cur_time(),len(radiator_close)), file=sys.stderr)
					print("%s Number of radiators to exclude %s" % (cur_time(),len(exclude)), file=sys.stderr)
					print("%s Number of radiators out of sync %s" % (cur_time(),len(outofsync)), file=sys.stderr)
				except:
					print("%s Object integrity error" % (cur_time(),), file=sys.stderr)
					traceback.print_exc()
					break
				try:
					print("%s Total of %s radiator heads" % (cur_time(),len(radiator_list)), file=sys.stderr)
					
					#loop through all radiator heads and see if it needs to be set to open or close
					t4 = 0
					serious_radiator_problem = False
					while t4 < len(radiator_list):
						if radiator_list[t4].address in radiator_open:
							print("%s Opening radiator %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
							if radiator_list[t4].temperature == 100 and radiator_list[t4].status != 'error' and radiator_list[t4].force_command < 5: #force a fresh signal at least every 5 minutes
								radiator_list[t4].status = 'on' #radiator is already open, don't do anything
								print("%s Radiator already open" % (cur_time(),), file=sys.stderr)
								radiator_list[t4].force_command = radiator_list[t4].force_command + 1
							else:
								if radiator_list[t4].set_valve_open():
									print("%s Success for %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
									radiator_list[t4].status = 'on'
									radiator_list[t4].force_command = 0
								else:
									print("%s Failed for %s, retry next time" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
						elif radiator_list[t4].address in radiator_close:
							print("%s Closing radiator %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
							if radiator_list[t4].temperature == 0 and radiator_list[t4].status != 'error' and radiator_list[t4].force_command < 5: #force a fresh signal at least every 5 minutes
								radiator_list[t4].status = 'off' #radiator is already closed, don't do anything
								print("%s Radiator already closed" % (cur_time(),), file=sys.stderr)
								radiator_list[t4].force_command = radiator_list[t4].force_command + 1
							else:
								if radiator_list[t4].set_valve_close():
									print("%s Success for %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
									radiator_list[t4].status = 'off'
									radiator_list[t4].force_command = 0
								else:
									print("%s Failed for %s, retry next time" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
						elif radiator_list[t4].address in exclude:
							a=0 #dont know yet
						elif radiator_list[t4].address in outofsync:
							print("%s Thermostat out of sync, no touching %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)

						else:
							raise Exception('Unknown radiator head('+radiator_list[t4].address+'), something is terribly wrong')
						if radiator_list[t4].failedtimes > 15: #something is wrong... more than 15 minutes of failures
							radiator_list[t4].status = 'error'
							serious_radiator_problem = True 
						
						#send radiator and CV status to database
						try:
							print("%s Sending to db for %s status: %s" % (cur_time(),radiator_list[t4].address,radiator_list[t4].status), file=sys.stderr)
							a = radiator_list[t4].address
							if radiator_list[t4].remoteaddress:
								a = radiator_list[t4].address+"@"+radiator_list[t4].remoteaddress							
							rpi_temp = rpi.split(":")[0]+":"+rpi.split(":")[1]
							r = requests.post(rpi_temp+':6543/setradiatorvalve', data = {'valve' : radiator_list[t4].status, 'mac': a}, timeout=5)
							#r = requests.post('http://192.168.0.158:5000/setradiator', data = {'valve' : status, 'mac': radiator_list[t4].address})
						except:
							traceback.print_exc()
							print("%s Failed to send radiator status to database for %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)

						t4 = t4 + 1					
					
				except:
					print("%s Failed to open/close all radiator(s)" % (cur_time(),), file=sys.stderr)
					traceback.print_exc()
				try:
					#if there are any rooms that need heating, heat up boiler
					if len(radiator_open) > 0:
						if serious_radiator_problem:
							#If a closing radiator is in error for 15min, we should close CV as well... else it will overheat
							#unless there is nothing else open anyway
							print("%s Closing_radiator_problem, closing CV to prevent overheat" % (cur_time(),), file=sys.stderr)
							if CV_openclose(5):
								verwarming = False
								heatingcounter = 0
						
						print("%s Radiators are open, warming up CV" % (cur_time(),), file=sys.stderr)
						print("%s Biggest difference %s and heating offset %s" % (cur_time(),tempdiff,heating_offset), file=sys.stderr)
						if float(tempdiff) > float(heating_offset): 
							#Only heat up the boiler is there is at least one room where the temp exceeds the heating offset 
							#and warm water is still in the pipes
							print("%s There is a huge temperature difference, warming up CV" % (cur_time(),), file=sys.stderr)
							if CV_openclose(30):
								verwarming = True
							#print("%s There is a huge temperature difference" % (cur_time(),), file=sys.stderr)
							#if not verwarming or first_load: #check if it was not already heating
							#	print("%s No active hot water in pipes, warming up CV" % (cur_time(),), file=sys.stderr)
							#	if CV_openclose(30):
							#		verwarming = True
							#else:
							#	print("%s Hot water still active, no need to start CV" % (cur_time(),), file=sys.stderr)
						else:
							print("%s Difference in temp is within offset" % (cur_time(),), file=sys.stderr)
							if verwarming or first_load: #if it was still heating, close it
								print("%s Hot water is still active, we can already close CV assuming it will remain heating to set temperature" % (cur_time(),), file=sys.stderr)
								if CV_openclose(5):
									verwarming = False
							else:
								print("%s CV is already closed" % (cur_time(),), file=sys.stderr)
					else:
						print("%s No radiators open, closing CV" % (cur_time(),), file=sys.stderr)
						heatingcounter = heatingcounter + 1
						if verwarming or first_load or heatingcounter > 15: #if it was still heating, close it
							if CV_openclose(5):
								verwarming = False
								heatingcounter = 0
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
			if updatecounter > 15: #call update every 15min to update outside temp
				outside_temp = load_ot()
			if updatecounter > 60: #call update every hour to check for battery status
				t4 = 0
				while t4 < len(radiator_list):
					try:
						print("%s Checking for battery for %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
						if radiator_list[t4].update:
							print("%s Lowbattery status %s " % (cur_time(),radiator_list[t4].lowbattery), file=sys.stderr)
						a = radiator_list[t4].address
						if radiator_list[t4].remoteaddress:
							a = radiator_list[t4].address+"@"+radiator_list[t4].remoteaddress
						rpi_temp = rpi.split(":")[0]+":"+rpi.split(":")[1]
						r = requests.post(rpi_temp+':6543/setradiatorbattery', data = {'lowbattery' : str(radiator_list[t4].lowbattery), 'mac': a}, timeout=5)
					except:
						traceback.print_exc()
						print("%s Failed to send radiator status to database for %s" % (cur_time(),radiator_list[t4].address), file=sys.stderr)
					t4 = t4 + 1
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
