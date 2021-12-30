import os
import re
import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import tz
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors
import dbconfig
import requests
import math

def cur_time():
	utc = datetime.now()
	# Tell the datetime object that it's in UTC time zone since 
	# datetime objects are 'naive' by default
	utc = utc.replace(tzinfo=tz.gettz('UTC'))
	#utc = utc.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
	# Convert time zone
	utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
	utcstr = utc.strftime('%Y-%m-%d %H:%M:%S')
	#now = datetime.strptime(utcstr, "%Y-%m-%d %H:%M:%S")
	return ("[%s]" % (utc.strftime('%Y-%m-%d %H:%M:%S'),))

def savetodb(day, hw, ch, temp, page):
	utc = datetime.now()
	utc = utc.replace(tzinfo=tz.gettz('UTC'))
	#utc = utc.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
	utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
	datumtijd = datetime.strftime(utc, "%m/%d/%Y, %H:%M:%S")
	try:
		conn = psycopg2.connect(host=dbconfig.dbip,database=dbconfig.dbname,user=dbconfig.dbuser,password=dbconfig.dbpass)
		cur = conn.cursor()
		#print("%s Connected to database" % (cur_time(),), file=sys.stderr)
		print("[%s] Connected to database" % (cur_time(),))
			
		try:
			#see if reading already exists
			cur.execute( "SELECT datumtijd FROM verwarmschema.thermostaat WHERE datumtijd='%s'" % (day,))
			if cur.rowcount == 0:
				#cur.execute( "INSERT INTO verwarmschema.nefit_gas_history (datumtijd,hw,ch,t) VALUES ('"+day+"','"+hw+"','"+ch+"','"+temp+"')" )
				cur.execute( "INSERT INTO verwarmschema.nefit_gas_history (page,datumtijd,hw,ch,t) VALUES ('%s','%s','%s','%s','%s')" % (page,day,hw,ch,temp) )
				conn.commit()
				print("[%s] Updated in database" % (cur_time(),))
			else:
				print("[%s] Reading already in database" % (cur_time(),))
			#print("%s Loaded object into %s " % (cur_time(),self.sid), file=sys.stderr)
		except Exception as err: #tables do not seem to be there... running in no connection mode.
			print_psycopg2_exception(err)
			#print("%s Database and/or tables are not available" % (cur_time(),), file=sys.stderr)
			if conn:
				conn.close()
			conn = None
			return False
		return True
	except OperationalError as err:
		# pass exception to function
		print_psycopg2_exception(err)
		conn.close()
		conn = None
		return False
		#try again in one minute
		#retry_timer = retry_connect() #init the connect retry timer
	except Exception as err: #tables do not seem to be there... running in no connection mode.
		# pass exception to function
		print_psycopg2_exception(err)
		conn.close()
		conn = None
		cur = None
		#print("%s Database and/or tables are not available" % (cur_time(),), file=sys.stderr)
		return False
		
def initfromdb():
	global page,last_date
	utc = datetime.now()
	utc = utc.replace(tzinfo=tz.gettz('UTC'))
	#utc = utc.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
	utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
	datumtijd = datetime.strftime(utc, "%m/%d/%Y, %H:%M:%S")
	try:
		conn = psycopg2.connect(host=dbconfig.dbip,database=dbconfig.dbname,user=dbconfig.dbuser,password=dbconfig.dbpass)
		cur = conn.cursor()
		#print("%s Connected to database" % (cur_time(),), file=sys.stderr)
		print("[%s] Connected to database" % (cur_time(),))
			
		try:
			#see if sensor already exists
			cur.execute( "SELECT page,datumtijd FROM verwarmschema.nefit_gas_history order by datumtijd desc limit 1" )
			if cur.rowcount != 0:
				result = cur.fetchone()
				last_date = result[1]
				page = result[0]				
				print("[%s] Load page(%s) and last_date(%s) from database" % (cur_time(),page,last_date))
			#print("%s Loaded object into %s " % (cur_time(),self.sid), file=sys.stderr)
		except Exception as err: #tables do not seem to be there... running in no connection mode.
			print_psycopg2_exception(err)
			#print("%s Database and/or tables are not available" % (cur_time(),), file=sys.stderr)
			if conn:
				conn.close()
			conn = None
			return False
		return True
	except OperationalError as err:
		# pass exception to function
		print_psycopg2_exception(err)
		conn.close()
		conn = None
		return False
		#try again in one minute
		#retry_timer = retry_connect() #init the connect retry timer
	except Exception as err: #tables do not seem to be there... running in no connection mode.
		# pass exception to function
		print_psycopg2_exception(err)
		conn.close()
		conn = None
		cur = None
		#print("%s Database and/or tables are not available" % (cur_time(),), file=sys.stderr)
		return False

def get_pointer():
	global current_page_pointer 
	try:
		r = requests.get(rpi+'bridge/ecus/rrc/recordings/gasusagePointer')
		response = r.json()
		current_page_pointer = math.ceil(response['value'] / 32)
	except:
		print("[%s] Error getting the readings" % (cur_time(),))

def get_reading(page):
	try:
		r = requests.get(rpi+'bridge/ecus/rrc/recordings/gasusage?page=%s' % (page,))
		return r.json()
	except:
		print("[%s] Error getting the readings" % (cur_time(),))
		return None
	

#initialize the readings from the db.
#store last stored page pointer in a variable
#store last stored date in a variable
#then update from that point onwards
page = 1
last_date = datetime(2100, 1, 1)
current_page_pointer = 1

###configurable variables
if os.getenv("VERWARMING_ONOFF_RPI") is not None:
	rpi = os.getenv("VERWARMING_ONOFF_RPI")
else:
	rpi = 'http://192.168.0.125:8000/' #ip:port to the api serving the interface to the CV/heater

def updater():
	global current_page_pointer, page, last_date
	initfromdb()
	get_pointer()

	while(page <= current_page_pointer):
		print("[%s] Getting the readings for page %s" % (cur_time(),page))
		response = get_reading(page)
		if response != None:
			for r in response['value']:
				#loop over all received values
				#if they are lower than last stored date, store them
				try:
					datum = datetime.strptime(r['d'], '%d-%m-%Y')
				except:
					if r['d'] == '255-256-65535':
						datum = datetime(2000, 1, 1)
					else:
						print("[%s] Error converting datum?" % (cur_time(),))	
				if datum > last_date:
					if not savetodb(datum, r['hw'], r['ch'], r['T'], page):
						print("[%s] Error saving the readings" % (cur_time(),))
					else:
						last_date = datum	
		else:
			#error?
			print("[%s] Error getting the readings" % (cur_time(),))
		page = page + 1

###MAINLINE

print("[%s] Starting script, scheduled every 12 hours to read CV data and push to DB" % (cur_time(),))
try:
	while True:
		updater()
		utc = datetime.now()
		utc = utc.replace(tzinfo=tz.gettz('UTC'))
		utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
		utc = utc + timedelta(hours=+12)
		print("[%s] Sleeping for 12 hours, next run is %s" % (cur_time(),utc.strftime('%Y-%m-%d %H:%M:%S')))
		time.sleep(43200)#wait 12 hours

except KeyboardInterrupt:
	print("%s Netjes afsluiten" % (cur_time(),), file=sys.stderr)
	


	
