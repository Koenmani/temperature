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
import os

app = Flask(__name__)
cors = CORS(app)

def load_ot():
	try:
		r = requests.get(airco_ip+'/aircon/get_sensor_info', timeout=5)
		returnobject = r.text.split(",")
		if returnobject[0].split("=")[1] == "OK":
			for o in returnobject:
				if o.split("=")[0] == 'otemp':
					return float(o.split("=")[1])
		else:
			print("%s Could not get sensor info from airco: %s" % (cur_time(),airco_ip), file=sys.stderr)
			return 0
		
	except:
		return 0

def load_airo_power():
	try:
		r = requests.get(airco_ip+'/aircon/get_control_info', timeout=5)
		returnobject = r.text.split(",")
		if returnobject[0].split("=")[1] == "OK":
			for o in returnobject:
				if o.split("=")[0] == 'pow':
					if int(o.split("=")[1]) == 0:
						return False
					else:
						return True
	except:
		print("%s Could not get control info from airco: %s" % (cur_time(),airco_ip), file=sys.stderr)
		return False

@app.route("/setschedule", methods=['POST'])
def setschedule():
	global conn,cur
	if request.method == 'POST':
		try:
			content = request.json
			#print(content)
			kmrnr=content['kmrnr']
			sid=content['sid']
			obj=content['obj']
			#delete current schedule and replace insert all new values
			
			if connectdb():
				try:
					if obj:
						print("Found object: "+str(len(obj))+" for kamer nr: "+str(kmrnr)+ " for sid: "+str(sid))
						print("Found object dag: "+str(obj['dag']))
						print("Found object temp: "+str(obj['temp']))
						print("Found object tijd: "+str(obj['tijd']))
						if str(sid) == 'new':
							cur.execute( "INSERT INTO verwarmschema.thermostaat_schedule (dag,tijd,temp, fk_tid) VALUES ('%s','%s','%s','%s') RETURNING sid" % (obj['dag'],obj['tijd'],obj['temp'],kmrnr))
							conn.commit()
							sid = cur.fetchone()[0]
						else:
							cur.execute( "UPDATE verwarmschema.thermostaat_schedule SET dag='%s',temp='%s',tijd='%s' WHERE sid='%s'" % (obj['dag'],obj['temp'],obj['tijd'],sid))
							conn.commit()
					else:
						print("We need to delete it for sid: "+str(sid))
						cur.execute( "DELETE FROM verwarmschema.thermostaat_schedule WHERE fk_tid='%s' AND sid='%s'" % (kmrnr,sid) )
						conn.commit()
				except Exception as err:
						# pass exception to function
						#print_psycopg2_exception(err)
						# rollback the previous transaction before starting another
						conn.close()
						print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
						return jsonify({'result':'fail'})
				#
				#for object in obj:
				#	print("Found object dag: "+str(object['dag']))
				#	print("Found object temp: "+str(object['temp']))
				#	print("Found object tijd: "+str(object['tijd']))
				#	try:
						#cur.execute( "INSERT INTO verwarmschema.thermostaat_schedule (dag,tijd,temp, fk_tid) VALUES ('%s','%s','%s','%s')" % (object['dag'],object['tijd'],object['temp'],kmrnr))
						#conn.commit()
				#	except Exception as err:
						# pass exception to function
						#print_psycopg2_exception(err)
						# rollback the previous transaction before starting another
				#		conn.close()
				#		print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
			else:
				print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
		except:
			traceback.print_exc()
		
		return jsonify({'result':'done','sid':sid})

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
def setmanual2():
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
			
@app.route("/setreading", methods=['GET'])
def setreading():
	global conn,cur
	utc = datetime.now()
	utc = utc.replace(tzinfo=tz.gettz('UTC'))
	#utc = utc.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
	utc = utc.astimezone(tz.gettz('Europe/Amsterdam'))
	datumtijd = datetime.strftime(utc, "%m/%d/%Y, %H:%M:%S")
	if request.method == 'GET':
		hum=request.args['hum']
		bat=request.args['bat']
		temp=request.args['temp']
		mac=request.args['mac']
		#print("%s Received data %s" % (cur_time(),data), file=sys.stderr)
		if connectdb():
			try:
				#see if sensor already exists
				cur.execute( "SELECT * FROM verwarmschema.thermostaat WHERE mac=upper('%s')" % (mac,) )
				if cur.rowcount != 0:
					#check date and values of last update
					#if values are same and update is less than 10min ago, dont do anything
					#if values are different or update is longer than 10min, update db
					result = cur.fetchone()
					tid = result[0]
					#last_reading = datetime.strptime(result[3], "%m/%d/%Y, %H:%M:%S")
					last_reading = result[3]
					last_reading = last_reading.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
					#print("[%s] Comparing times current-10: %s with database %s" % (cur_time(),(utc + timedelta(minutes=-10)),last_reading))
					if ((utc + timedelta(minutes=-10)) > last_reading): #if its longer than 10min ago since last reading... add it anyway
						cur.execute( "INSERT INTO verwarmschema.thermostaat_details (fk_tid,datumtijd,temp,vocht,batterij) VALUES ('%s','%s','%s','%s','%s')" % (tid,datumtijd,temp,hum,bat) )
						cur.execute( "UPDATE verwarmschema.thermostaat SET huidige_temp='%s',datumtijd='%s',luchtvocht='%s',batterij_level='%s'  WHERE tid='%s'" % (temp,datumtijd,hum,bat,tid,) )
						conn.commit()
						#print("[%s] Updated in database based on time" % (cur_time(),))
						return jsonify('done')
					else:
						#check if data is different
						db_temp = result[4]
						db_hum = result[5]
						db_bat = result[6]
						if ((float(db_temp) != float(temp)) or (int(db_hum) != int(hum)) or (int(db_bat) != int(bat))):
							cur.execute( "INSERT INTO verwarmschema.thermostaat_details (fk_tid,datumtijd,temp,vocht,batterij) VALUES ('%s','%s','%s','%s','%s')" % (tid,datumtijd,temp,hum,bat) )
							cur.execute( "UPDATE verwarmschema.thermostaat SET huidige_temp='%s',datumtijd='%s',luchtvocht='%s',batterij_level='%s'  WHERE tid='%s'" % (temp,datumtijd,hum,bat,tid,) )
							conn.commit()
							#print("[%s] Updated in database based on value diff" % (cur_time(),))
							return jsonify('done')
						else:
							#print("[%s] Same readings within 10 min, no need to update" % (cur_time(),))
							cur.execute( "UPDATE verwarmschema.thermostaat SET datumtijd='%s' WHERE tid='%s'" % (datumtijd,tid,) )
							conn.commit()
							return jsonify('done')
				else:
					print("[%s] Sensor does not exist in database. You need to add it manually" % (cur_time(),))
			except Exception as err:
				# pass exception to function
				#print_psycopg2_exception(err)
				# rollback the previous transaction before starting another
				print(traceback.format_exc())
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
			cur.execute( "SELECT t.tid,t.kamer_naam,t.huidige_temp,t.ingestelde_temp,r.mac,handmatig,r.open_close,t.datumtijd,t.ofset,t.smartheat,t.handmatig_tijd,t.exclude,r.lowbattery,t.fk_aid FROM verwarmschema.thermostaat t left outer join verwarmschema.radiator r on tid=fk_tid ORDER BY tid")
			conn.commit()
			if cur.rowcount != 0:
				x = {"kamer" : [], "tijd" :[], "otemp" :[]}
				y = None
				nu = datetime.today()
				nu = nu.replace(tzinfo=tz.gettz('UTC'))
				nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
				lowbat = False

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
						
						if result[12] == True:
							lowbat = True
							
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
								#this means we haven't found last switch point, because day = 1 and the last switch point is actually the last record
								#example: day = 1 and before the first switch point
								temp = last_r[3]
								dag3 = last_r[2]
								
						else:
							dag2 = 0
							temp2 = 0
							temp = 0
							dag3 = 0
							#something really wrong. why would you set to automatic mode without schedule?
						
						if result[5] == 1: #temp is manually set and should overwrite existing schedule
							#unless time has passed, so it should switch back to the schedule
							switch_time = result[10]
							switch_time = switch_time.replace(tzinfo=tz.gettz('Europe/Amsterdam'))
							if nu > switch_time:
								cur.execute( "UPDATE verwarmschema.thermostaat SET handmatig='0', ingestelde_temp=null, handmatig_tijd=null WHERE tid='%s'" % (result[0],) )
								conn.commit()
								handmatig = False
							else:
								temp = result[3]
								handmatig = True
						
						if y:
							x['kamer'].append(y)
						y = {
							"tid": result[0],
							"naam": result[1],
							"ingesteld": temp,
							"handmatig": handmatig,
							"exclude": result[11],
							"volgend_temp": temp2,
							"volgend_tijd": dag2,
							"laatste_tijd": dag3,
							"huidig": result[2],
							"insync": insync,
							"offset": offset,
							"smartheat": smartheat,
							"lowbattery": lowbat,
							"radiator":[],
							"airco":[]
						}
						cur.execute( "select r.mac, r.open_close, r.lowbattery from verwarmschema.radiator r where fk_tid=%s" % (result[0],))
						conn.commit()
						res = cur.fetchall()
						for r in res:
							y['radiator'].append({"mac": r[0],"open_close": r[1], "lowbattery": r[2]})
							if r[2] == True:
								lowbat = True
						if result[13]:
							cur.execute( "select a.ip, a.open_close, a.last_change from verwarmschema.airco a where aid=%s" % (result[13],))
							conn.commit()
							res = cur.fetchall()
							for r in res:
								if load_airo_power():
									open_close = 1
								else:
									open_close = 0
								y['airco'].append({"ip": r[0],"open_close": open_close, "last_change": r[2]})
							
						tid = int(result[0])
					else:
						pass
					
				#add last one
				if y:
					x['kamer'].append(y)
					x['tijd'].append({"tijd" : nu.astimezone(tz.gettz('Europe/Amsterdam'))})
					x['otemp'].append({'otemp' : load_ot()})

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
			cur.execute( "SELECT dag,tijd,temp,sid FROM verwarmschema.thermostaat_schedule where fk_tid=%s order by dag,TO_TIMESTAMP(tijd,'HH24:MI')" % (kamernr,))
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
						"temp": result[2],
						"sid" : result[3]
					}
					x.append(y)
			else:
				x = [{
						"sid": "null",
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

@app.route("/togglevac", methods=['GET']) 
def togglevac():
	#toggle vacation modus for a room
	#/togglevac?room=x
	if request.method == 'GET':
		print("%s Parsing requested values from POST" % (cur_time(),), file=sys.stderr)
		#content = request.json
		kmr=request.args['room']		
		vac=False
		if connectdb():
			try:
				print("%s Updating db " % (cur_time(),), file=sys.stderr)
				cur.execute( "SELECT exclude from verwarmschema.thermostaat WHERE tid='%s'" % (kmr,) )
				conn.commit()
				if cur.rowcount != 0:
					r = cur.fetchone()
					if r[0] == False:
						vac=True
					else:
						vac=False
					cur.execute( "UPDATE verwarmschema.thermostaat SET exclude='%s' WHERE tid='%s'" % (vac,kmr) )
					conn.commit()
					return jsonify('done')
				else:
					return jsonify('fail')
			except Exception as err:
				conn.close()
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
				traceback.print_exc()
				return jsonify('fail')				
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
			return jsonify('fail')

@app.route("/setmanual", methods=['GET', 'POST'])
def setmanual():
	global conn,cur
	#zet de status van een radiator naar handmatig (on) of automatisch (off) met de juiste temp en switch to automatic (time)
	# POST /setmanual?tid=xx&manual=on&temp=20.5&time=
	# POST /setmanual?tid=xx&manual=off
	if request.method == 'POST':
		print("%s Parsing requested values from POST" % (cur_time(),), file=sys.stderr)
		content = request.json
		manual=content['manual']
		tid = content['tid']
		temp=content.get('temp') #this is fine if empty, probably the manual mode has been release by user
		print("%s Got the manual(%s), tid(%s) and the temp(%s)" % (cur_time(),manual,tid,temp), file=sys.stderr)	
		tijd=content.get('tijd')
		parsed = True
	elif request.method == 'GET':
		print("%s Parsing requested values from GET" % (cur_time(),), file=sys.stderr)
		manual=request.args['manual']
		tid = request.args['tid']
		try:
			temp=request.args['temp']
		except:
			temp=None
			#this is fine, probably the manual mode has been release by user
		print("%s Got the manual(%s), tid(%s) and the temp(%s)" % (cur_time(),manual,tid,temp), file=sys.stderr)	
		try:
			tijd=request.args['tijd']
		except:
			tijd=None
		parsed = True
	else:
		return jsonify('fail')
		
	if parsed:		
		if tijd != None:	
			try:
				nu = datetime.today()
				nu = nu.replace(tzinfo=tz.gettz('UTC'))
				nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
				#temp_time = time(int(tijd.split(':')[0]),int(tijd.split(':')[1]),0)
				switch_time = nu.replace(hour=int(tijd.split(':')[0]),minute=int(tijd.split(':')[1]))
			
				if switch_time < nu:
					switch_time = switch_time + timedelta(days=1)
			except:
				#something is wrong,  don't do anything
				print("%s Failed to calculate next switch point for manual -> automatic" % (cur_time(),), file=sys.stderr)
				return jsonify('fail')			
		else:
			switch_time=None
			#this is fine, probably the manual mode has been release by user
		
		print("%s Also got the requested time(%s) translated into next switch point(%s)" % (cur_time(),tijd,switch_time), file=sys.stderr)	
		if manual == "on":
			v = 1
		else:
			v = 0
		
		
		if connectdb():
			try:
				print("%s Updating db " % (cur_time(),), file=sys.stderr)
				if v == 0: #need to shut it down
					cur.execute( "UPDATE verwarmschema.thermostaat SET handmatig=0, ingestelde_temp=null, handmatig_tijd=null WHERE tid='%s'" % (tid,) )
				else:
					cur.execute( "UPDATE verwarmschema.thermostaat SET handmatig='%s', ingestelde_temp='%s', handmatig_tijd='%s' WHERE tid='%s'" % (v,temp,switch_time,tid) )
				conn.commit()
				return jsonify('done')
			except Exception as err:
				conn.close()
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
				traceback.print_exc()
				return jsonify('fail')				
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
			return jsonify('fail')
	
@app.route("/setradiatorbattery", methods=['POST'])
def setradiatorbattery():
	global conn,cur
	#zet de status van een radiator naar open of dicht
	# POST /setradiator?valve=on
	# POST /setradiator?valve=off
	if request.method == 'POST':
		battery_status=request.form['lowbattery']
		mac=request.form['mac']
		
		if connectdb():
			try:
				cur.execute( "UPDATE verwarmschema.radiator SET lowbattery='%s' WHERE mac='%s'" % (battery_status,mac) )
				conn.commit()
				return jsonify('done')
			except Exception as err:
				conn.close()
				traceback.print_exc() 
				print("%s Failed to update database" % (cur_time(),), file=sys.stderr)
				return jsonify('fail')				
		else:
			print("%s Could not connect to database" % (cur_time(),), file=sys.stderr)
			return jsonify('fail')

@app.route("/setradiatorvalve", methods=['POST'])
def setradiator():
	global conn,cur
	#zet de status van een radiator naar open of dicht
	# POST /setradiator?valve=on
	# POST /setradiator?valve=off
	if request.method == 'POST':
		valve_status=request.form['valve']
		
		if valve_status == "on":
			v = 1
		elif valve_status == "error":
			v = 99
		else:
			v = 0
		
		mac=request.form['mac']
		
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

if os.getenv("AIRCO_IP") is not None:
	airco_ip = os.getenv("AIRCO_IP")
else:
	airco_ip = 'http://192.168.0.135' #ip:port to the api serving the interface to the CV/heater
app.run(host='0.0.0.0')