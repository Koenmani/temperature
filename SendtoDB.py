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

def savetodb(val_sensor, val_temp, val_hum, val_bat):
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
			cur.execute( "SELECT tid FROM verwarmschema.thermostaat WHERE tid='"+val_sensor+"'" )
			if cur.rowcount != 0:
				cur.execute( "INSERT INTO verwarmschema.thermostaat_details (fk_tid,datumtijd,temp,vocht,batterij) VALUES ('"+val_sensor+"','"+datumtijd+"','"+val_temp+"','"+val_hum+"','"+val_bat+"')" )
				cur.execute( "UPDATE verwarmschema.thermostaat SET huidige_temp='%s',datumtijd='%s',luchtvocht='%s',batterij_level='%s'  WHERE tid='%s'" % (val_temp,datumtijd,val_hum,val_bat,val_sensor,) )
				conn.commit()
				print("[%s] Updated in database" % (cur_time(),))
			else:
				print("[%s] Sensor does not exist in database. You need to add it manually" % (cur_time(),))
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

val_sensor = sys.argv[2]
val_temp = sys.argv[3]  # change to sys.argv[5] for calibrated
val_hum = sys.argv[4]
val_bat = sys.argv[6]

print("[%s] received temp: %s, hum: %s, bat: %s for %s" % (cur_time(),val_temp,val_hum,val_bat,val_sensor))
if not savetodb(val_sensor, val_temp, val_hum,val_bat):
	print("[%s] some error occured" % (cur_time(),))
