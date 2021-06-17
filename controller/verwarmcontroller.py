from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from datetime import time
from dateutil import tz
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors
import requests
import traceback
import dbconfig

app = Flask(__name__)
cors = CORS(app)

@app.route("/setschedule", methods=['POST'])
def setschedule():
	global conn,cur
	if request.method == 'POST':
		try:
			content = request.json
			#print(content)
			kmrnr=content['kmrnr']
			obj=content['obj']
			#delete current schedule and replace insert all new values
			print("Found object: "+str(len(obj))+" for kamer nr: "+str(kmrnr))
			if connectdb():
				cur.execute( "DELETE FROM verwarmschema.thermostaat_schedule WHERE fk_tid='%s'" % (kmrnr,) )
				conn.commit()
				for object in obj:
					print("Found object dag: "+str(object['dag']))
					print("Found object temp: "+str(object['temp']))
					print("Found object tijd: "+str(object['tijd']))
					try:
						cur.execute( "INSERT INTO verwarmschema.thermostaat_schedule (dag,tijd,temp, fk_tid) VALUES ('%s','%s','%s','%s')" % (object['dag'],object['tijd'],object['temp'],kmrnr))
						conn.commit()
					except Exception as err:
						# pass exception to function
						#print_psycopg2_exception(err)
						# rollback the previous transaction before starting another
						conn.close()
						print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
			else:
				print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
		except:
			traceback.print_exc()
		
		return jsonify({'result':'done'})

@app.route("/settemp", methods=['POST'])
def settemp():
	global conn,cur
	#stel een temperatuur in voor een bepaalde kamer
	#post request bevat kamer nr en gewenste temp
	if request.method == 'POST':
		#print("%s recieved form object: %s" % (cur_time(),request.form), file=sys.stderr)
		#if iobj.recieve(request.form):
		tid=request.form['nr']
		temp=request.form['temp']
		if connectdb():
			try:
				cur.execute( "UPDATE verwarmschema.thermostaat SET ingestelde_temp=%s WHERE tid=%s" % (tid,temp) )
				conn.commit()
			except Exception as err:
				# pass exception to function
				#print_psycopg2_exception(err)
				# rollback the previous transaction before starting another
				conn.close()
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)

@app.route("/overwriteschedule", methods=['POST'])
def setmanual():
	global conn,cur
	#stel een temperatuur in voor een bepaalde kamer
	#post request bevat kamer nr en gewenste temp
	if request.method == 'POST':
		#print("%s recieved form object: %s" % (cur_time(),request.form), file=sys.stderr)
		#if iobj.recieve(request.form):
		tid=request.form['nr']
		temp=request.form['temp']
		if connectdb():
			try:
				cur.execute( "UPDATE verwarmschema.thermostaat SET ingestelde_temp=%s,handmatig='1', WHERE tid=%s" % (tid,temp) )
				conn.commit()
			except Exception as err:
				# pass exception to function
				#print_psycopg2_exception(err)
				# rollback the previous transaction before starting another
				conn.close()
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)

@app.route("/verwarmingstatus")
def verwarmingstatus():
	#geeft aan welke thermostaten/kamers wel of niet op de juiste temp zijn
	#een json met {kamer: {nr,naam,huidig,ingesteld, radiator:{mac} } }
	global conn,cur
	if connectdb():
		try:
			cur.execute( "SELECT t.tid,t.kamer_naam,t.huidige_temp,t.ingestelde_temp,r.mac,handmatig,r.open_close,t.datumtijd,t.ofset,t.smartheat FROM verwarmschema.thermostaat t left outer join verwarmschema.radiator r on tid=fk_tid ORDER BY tid")
			conn.commit()
			if cur.rowcount != 0:
				x = {"kamer" : [], "tijd" :[]}
				y = None
				nu = datetime.today()
				nu = nu.replace(tzinfo=tz.gettz('UTC'))
				nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
				
				weekdag = nu.weekday() + 1
				vorigedag = weekdag - 1
				volgendedag = weekdag + 1
				tijd = nu.time()
				if vorigedag <= 0: #0 does not exist, range is from mo-sun; 1-7
					vorigedag = 7
				if volgendedag >= 8: #8 does not exist, range is from mo-sun; 1-7
					volgendedag = 1
				results = cur.fetchall()
				tid = 999
				for result in results:
					if tid != int(result[0]):
						
						offset = result[8]
						#check if last update is less then 15 min ago
						last_time = result[7]
						last_time = last_time + timedelta(minutes=15)
						last_time = last_time.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
						if last_time < nu:
							insync = False
						else:
							insync = True
							
						smartheat = result[9]
						
						#process rest of values for object to return
						cur.execute("(select * from verwarmschema.thermostaat_schedule where fk_tid='%s' and dag='%s' order by dag asc, TO_TIMESTAMP(tijd,'HH24:MI') asc)union all(select * from verwarmschema.thermostaat_schedule where fk_tid='%s' and dag='%s' order by dag asc, TO_TIMESTAMP(tijd,'HH24:MI') asc)union all(select * from verwarmschema.thermostaat_schedule where fk_tid='%s' and dag='%s' order by dag asc, TO_TIMESTAMP(tijd,'HH24:MI') asc)" % (result[0],vorigedag,result[0],weekdag,result[0],volgendedag)) 
						conn.commit()
						rs = cur.fetchall()
						handmatig = False
						found = False
						last_r = None
						first_r = None
						temp = 0
						temp2 = 0
						dag2 = 0
						dag3 = 0
						if cur.rowcount != 0:
							for r in rs: #loop through schedule to find the right place in time
								if first_r == None:
									first_r = r
								#compare_time = datetime(nu.year,nu.month,nu.day,int(r[2].split(':')[0]),int(r[2].split(':')[1]))
								compare_time = time(int(r[2].split(':')[0]),int(r[2].split(':')[1]),0)
								if weekdag == r[1] and tijd < compare_time and found==False:
									#next switch point gevonden
									found = True
									dag2 = r[2]
									temp2 = r[3]
									if last_r:
										#this means we haven't found the current temp yet, lets set it to last record
										#if this was the first record, don't worry it will be captured by the if in the end
										temp = last_r[3]
										dag3 = last_r[2]
										break #stop the loop, we found our values
								if volgendedag == r[1] and found==False: #this means we didnt find our value yet, however we have passed the current day in the list already
									#this must be next switch point
									found = True
									dag2 = r[2]
									temp2 = r[3]
									if last_r:
										#this means we haven't found the current temp yet, lets set it to last record
										temp = last_r[3]
										dag3 = last_r[2]
										break #stop the loop, we found our values									
								last_r = r
							if temp2 == 0:
								#this means we haven't found it, because day = 7 and the loop tries to find the next temp, which is actually the first record
								#example: day = 7 and after the last switch point
								dag2 = first_r[2]
								temp2 = first_r[3]
								temp = last_r[3]
								dag3 = last_r[2]
							if temp == 0:
								#this means we haven't last switch point, because day = 1 and the last switch point is actually the last record
								#example: day = 1 and before the first switch point
								temp = last_r[3]
								dag3 = last_r[2]
								
						else:
							dag2 = 0
							temp2 = 0
							temp = 0
							dag3 = 0
							#something really wrong. why would you set to automatic mode without schedule?
						
						if result[5] == "1": #temp is manually set and should overwrite existing schedule
							#temp = result[3]
							#handmatig = True
							#unless time has passed, so it should switch back to the schedule
							a=0
						
						if y:
							x['kamer'].append(y)
						y = {
							"tid": result[0],
							"naam": result[1],
							"ingesteld": temp,
							"handmatig": handmatig,
							"volgend_temp": temp2,
							"volgend_tijd": dag2,
							"laatste_tijd": dag3,
							"huidig": result[2],
							"insync": insync,
							"offset": offset,
							"smartheat": smartheat,
							"radiator":[
							{
								"mac": result[4],
								"open_close": result[6]
							}]
						}
						tid = int(result[0])
					else:
						y['radiator'].append({"mac": result[4],"open_close": result[6]})
					
				#add last one
				if y:
					x['kamer'].append(y)
					x['tijd'].append({"tijd" : nu.astimezone(tz.gettz('Europe/Amsterdam'))})
				return jsonify(x)
				#print("got row: %s" % (row,))
		except Exception as err:
			# pass exception to function
			#print_psycopg2_exception(err)
			# rollback the previous transaction before starting another
			traceback.print_exc() 
			conn.close()
			print("%s Failed to select database" % (cur_time(),), file=sys.stderr)

@app.route("/kamerschema")
def kamerschema():
	#geeft aan welke thermostaten/kamers wel of niet op de juiste temp zijn
	#een json met {kamer: {nr,naam,huidig,ingesteld, radiator:{mac} } }
	global conn,cur
	kamernr=request.args['nr']
	if kamernr == None:
		return jsonify([{"error":"true"}])
	print("%s Request is ontvangen voor nr: %s" % (cur_time(),kamernr), file=sys.stderr)
	if connectdb():
		try:
			#cur.execute( "SELECT dag,tijd,temp FROM verwarmschema.thermostaat_schedule where fk_tid=%s" % (kamernr,))
			cur.execute( "SELECT dag,tijd,temp FROM verwarmschema.thermostaat_schedule where fk_tid=%s order by dag,TO_TIMESTAMP(tijd,'HH24:MI')" % (kamernr,))
			conn.commit()
			print("%s We got %s rows from db" % (cur_time(),cur.rowcount), file=sys.stderr)
			if cur.rowcount != 0:
				x = []
				y = None
				results = cur.fetchall()
				for result in results:
					y = {
						"dag": result[0],
						"tijd": result[1],
						"temp": result[2]
					}
					x.append(y)
			else:
				x = [{
						"dag": "null",
						"tijd": "null",
						"temp": "null"
					}]
			return jsonify(x)
				#print("got row: %s" % (row,))
		except Exception as err:
			# pass exception to function
			#print_psycopg2_exception(err)
			# rollback the previous transaction before starting another
			traceback.print_exc() 
			conn.close()
			print("%s Failed to select database" % (cur_time(),), file=sys.stderr)
			return jsonify([{"error":"true"}])

@app.route("/getsensors")
def getsensors():
	#resulteerd een array met sensor mac adressen en nrs
	#mogelijk voor input voor LYWSD03MMC.py
	a=0
	
@app.route("/setradiator", methods=['POST'])
def setradiator():
	global conn,cur
	#zet de status van een radiator naar open of dicht
	# POST /setradiator?valve=on
	# POST /setradiator?valve=off
	if request.method == 'POST':
		valve_status=request.form['valve']
		mac=request.form['mac']
		if valve_status == "on":
			v = 1
		elif valve_status == "error":
			v = 99
		else:
			v = 0
		if connectdb():
			try:
				cur.execute( "UPDATE verwarmschema.radiator SET open_close='%s' WHERE mac='%s'" % (v,mac) )
				conn.commit()
				cur.execute( "SELECT rid FROM verwarmschema.radiator WHERE mac='%s'" % (mac,) )
				conn.commit()
				if cur.rowcount != 0:
					fk_rid = cur.fetchone()[0]
					utc = datetime.now()
					utc = utc.replace(tzinfo=tz.gettz('UTC'))
					utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
					datumtijd = datetime.strftime(utc, "%m/%d/%Y, %H:%M:%S")
					cur.execute( "INSERT INTO verwarmschema.radiator_history (fk_rid,open_close,datumtijd) VALUES ('%s','%s','%s')" % (fk_rid,v,datumtijd) )
					conn.commit()
				return jsonify('done')
			except Exception as err:
				conn.close()
				return jsonify('fail')
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
			return jsonify('fail')
	
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

def connectdb():
	global conn,cur
	try:
		conn = psycopg2.connect(host=dbconfig.dbip,database=dbconfig.dbname,user=dbconfig.dbuser,password=dbconfig.dbpass)
		cur = conn.cursor()
		print("%s Connected to database" % (cur_time(),), file=sys.stderr)
		return True
			
	except OperationalError as err:
		# pass exception to function
		#print_psycopg2_exception(err)
		conn.close()
		conn = None
		return False
		#try again in one minute
		#retry_timer = retry_connect() #init the connect retry timer
	except Exception as err: #tables do not seem to be there... running in no connection mode.
		# pass exception to function
		#print_psycopg2_exception(err)
		conn.close()
		conn = None
		cur = None
		print("%s Database is not available" % (cur_time(),), file=sys.stderr)
		return False

app.run(host='0.0.0.0')