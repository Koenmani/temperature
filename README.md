This project concerns a personal project to automate the heating system for my own home.

The goal of this automation is to replace my existing radiator heads with bluetooth controlled heads and be able to detect and set temperatures for each room individually.
My CV is a nefit, where other people already invested in home automation APIs, making it suited for this purpose.
Next to that, it is absolutely brilliant to have the data in your database with which you can build great grafana interfaces, visualizing the situation at home.
I also hooked it up to my other project where i read, via the p1 port, my smart meter data. Combining that i calculate (and visualize) how much gas i burn for each room.

I have developed this project in no way to be very generic. Lots of optimizations could be done to make this better suited for generic use, but at least
this is a good attempt to have a working product.

For this project i have used the following hardware:
1. A bluetooth (BLE) radiator head EQ3 https://www.conrad.nl/p/eqiva-cc-rt-ble-eq-draadloze-radiatorthermostaat-elektronisch-1543545
1. A Xiaomi Mijia temperature sensor https://nl.aliexpress.com/item/1005002311446721.html?spm=a2g0o.search0302.0.0.78fd2a932zVGRx&algo_pvid=null&algo_expid=null&btsid=0b0a0ae216206355792451238ebdc1&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_
1. Raspberry pi 4b
1. ESP32 with wifi and bluetooth https://www.tinytronics.nl/shop/nl/communicatie/bluetooth/esp32-wifi-en-bluetooth-board-cp2102

# Technologies
used technologies:
1. Python 3 with libraries:
	1. flask
	1. requests
	1. bluepy
	1. pybluez
1. Postgress
1. Grafana
1. Vue.js
1. Docker
1. Arduino with library
	1. NimBLE-Arduino
	1. webserver

# Thanks to
Further i would love to give thanks to some projects i used and adjusted to work for my project
https://github.com/JsBergbau/MiTemperature2
This project gave me a good headstart for reading thermostats and inject it in my postgress database.
Only little modification was done to the main module. Instead i adjusted only the sendtodb.py example to match my postgres database, which initially was prepared to inject into influx.

https://github.com/robertklep/nefit-easy-http-server
For communication with my CV/heating system. A brilliant piece of technology exposing loads of apis for communication

https://github.com/atc1441/ATC_MiThermometer
I used this library to flash the xiaomi thermostats to save battery power and increase lifetime on one battery.

https://github.com/mpex/EQ3-Thermostat
I used the eq3 control module and modified it to suit my needs for sending messages to my eq3 heads


# The design
The design started pretty simple; Read the temperatures from the thermostats and if the temperature is lower than the set temperature, heat up the room. If it's higher stop heating.
Pretty simple and in fact it is not much harder than this.
I wanted to host all the modules as docker image, so they are easilly managed.

Easy said. Lets go through the structure abit. i have 6 docker containers running
- A postgres database
regular basic postgress database
- Robert kleps' nefit server on port 8000
git clone the https://github.com/robertklep/nefit-easy-http-server and run it
- A thermostat container
This module reads BLE advertisements of known xiaomi thermostats and updates the database with this
- A controller module
The controller module is used for communication with the database exposing several paths over HTTP
- Finally the main module called 'onoff'
This module checks every minute for changes in the readings and sends signals to the radiator heads and heating system accordingly
- Nginx frontend
I created a front-end to visualise the heating system status of each room. It's simple vuejs front end exposed via my already running NGINX docker image

I will dive into my own modules individually and explain the logics and code. Standard modules such as the nefit easy server and the postgress database i will not cover.

## The first module to explain is the thermostat container
The code used is from https://github.com/JsBergbau/MiTemperature2, thanks!
There is one modification i have done, because of errors i was getting during runtime.
The command that will be run (from the Dockerfile) is 
'''
python3 ./LYWSD03MMC.py -a -r -b -df sensors.ini -odl -wdt 60 -call SendtoDB.py
'''
Do note that this is mentioned as ENTRYPOINT and i have put a CMD /bin/bash afterwards in the dockerfile, preventing docker to think that there are no foreground processes
Going into sendtodb.py
The standard code was providing an interface to send the data to an influx database. Because i needed to provide the data to a postgres database i created the 'SendtoDB.py' file.
When we are running the module, using the supplied output '-call SendtoDB.py' it will send the readings to this script and this script will send it to the configured postgres database (using dbconfig.py)
Very import is the usage of '-wdt 60' in the command line.
After alot of testing i have noticed that sometimes the thread gets stuck and will not recieve bluetooth readings anymore. My analysis is that this happens when two python modules are trying to use bluetooth simultaniously.
In this case the reading module and the valve controlling module. If this is the case, you will not have this problem if you have all your valves controlled by ESP32's
The code will not crash (unfortunatly), but will keep on thinking it is connected, but actually is not. 
configuring the supplied -wdt to 60 seconds means that if it will not recieve any readings for 60 seconds, it will re-start the thread.

## The second module to explain is the onoff module
The basics for this module is prety simple. A loop which checks every minute for changes in the readings from database and sends signals to the radiator heads and heating system accordingly
pretty simple huh!

The mainline is tagged with comment showing MAINLINE.
After initializing some values, the most import one is an array of radiators called radiator_list
This list is maintained to keep track of all attached radiator valves and contains an array of eq3 objects
After the loop is started with a 'While True' three other lists are initialised which contain to open and to close radiators. The third list contains manually operated valves.
The base is an http call to the controller module, which we connect to the database and present a JSON object back containing all needed paramters
After receiving the object back it is parsed for the values.
Either a valve is manually operated or not. If it is, the loop will stop for this radiator.
If it is managed by the script it will continue parsing.
Obviously if the temperature that the room needs to be, is lower than the current measurement (taking some offset into account), the room needs to be heated up.
--Also i have added logic for smart heating, which will take the weather forcast for your location and override the offset.
--in short: if the temperature is going up anyway, the sun will do the heating, saving your gas costs.
If the room needs to be heated, the ip-adress of the valve will be put in the radiator_open list. Else it is placed in the radiator_close list. 
When the last reading of the thermostat is too long ago, the returned controller object will contain a variable in_sync=False variable.
If this is the case, the adress of the valve is also placed in the manual_list array.

Finally, at the end of the loop, it will iterate of both the open and close list and send the needed commands, through the eq3 object, to the valves accordingly
It will update the database for the open/close status by sending an object back to the controller module
And if there are any radiator valves open, it will heat up the CV (taking again an offset into account). Else it will close it.

After a minute, it will again interate of the same.
thats it!

I have chose for the valve to open to just put it to 30 degrees celsius. Closing it simply puts it to 5 degrees. This way it is either 100% open or 0% open.
Same for the CV.
When the insync value is True, this means readings of the thermostat are not accurate (updated longer than 15 mintes ago). In this case i try to send the needed temperature to the valve, hoping the internal thermostat will do its job, until the bluetooth connection for readings stabilise again.

## The third module to explain is the controller module
The controller module is located in the controller folder and named 'verwarmcontroller.py'
This is a Flask app, which will host several api's:
1. verwarmingstatus
1. kamerschema
1. setschedule
1. setradiator
...and some other which are in development. Let me go over them one by one, starting with the most used "verwarmingstatus"

### verwarmingstatus
verwarming is the dutch word for heating. essentially meaning heatingstatus
verwarmstatus will return an object which is populated with values from the database, using dbocnfig.py
it will return an array for each room that contains the following values:
'''
"kamer":[
{
"tid": Id value for the room,
"naam": Name of the room,
"ingesteld": Set temperature for the room at the current time,
"handmatig": Room under manual control (True/False),
"volgend_temp": Temp after next switch point in celsius,
"volgend_tijd": Next switch point time,
"laatste_tijd": Last switch point time,
"huidig": Current read temperature value,
"insync": If not actual readings gotten for more than 15 minutes this will give False, else it is True,
"offset": Value to calculate earlier closing/opening of the valve,
"smartheat": Smartinheating enabled for the room (True/False),
For each attached radiator it will attach and array of radiator valves
"radiator":[
	{
		"mac": Mac-adress of the valve,
		"open_close": current status 1 (open) or 0 (closed)
	}]
}],
"tijd": Current time of returned object
'''

### kamerschema
Kamerschema will return a an object for a given room.
The object will contain the heating schedule for the given room
'''
[{
	"dag": "null",
	"tijd": "null",
	"temp": "null"
}]
'''
usually this will contain multiple values for each switch point that is programmed for this room

### setschedule
setschedule... excuse my english here, as the other api's are dutch
This api will do what it says. It takes an input object in json, similarly like the kamerschema api. This api will delete the current schedule for the given room and replace insert all new values

### setradiator
Set radiator api is maintained for updating the database with the current open or closed status of a valve. It is being called by the onoff module when it opens or closes a radiator.
This way the database reflects the actual status of the valve (open/close).

# Installation guidelines
1. Clone the GIT repo to your machine
1. Modify the variables in dbconfig.py to match your situation
1. Modify the docker-compose.yml NEFIT variables to match your situation
1. Maybe you also want to look at the timezone details there. For some reason i have been struggling with this alot
1. Modify the sensors.ini to match your sensor adresses and database keys
1. Create the tables in your postgress database using following queries
'''
CREATE TABLE verwarmschema.thermostaat (
tid serial NOT NULL,
mac varchar(100) NOT NULL,
kamer_naam varchar(100) NULL,
datumtijd timestamp NULL,
ingestelde_temp float4 NULL,
huidige_temp float4 NULL,
luchtvocht int NULL,
batterij_level int NULL,
handmatig int4 NOT NULL DEFAULT 0,
smartheat bool NOT NULL DEFAULT false;
CONSTRAINT thermostaat_pk PRIMARY KEY (tid)
);
CREATE TABLE verwarmschema.radiator (
rid serial NOT NULL,
mac varchar(100) NOT NULL,
fk_tid int NOT NULL,
open_close int NULL,
CONSTRAINT radiator_pk PRIMARY KEY (rid),
CONSTRAINT radiator_thermostaat_fk FOREIGN KEY (fk_tid) REFERENCES verwarmschema.thermostaat(tid) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE verwarmschema.thermostaat_details (
tid_d serial NOT NULL,
datumtijd timestamp NOT NULL,
fk_tid int NOT NULL,
"temp" float4 NOT NULL,
vocht int4 NULL,
batterij int4 NULL,
CONSTRAINT thermostaat_details_pk PRIMARY KEY (tid_d),
CONSTRAINT thermostaat_details_thermostaat_fk FOREIGN KEY (fk_tid) REFERENCES verwarmschema.thermostaat(tid) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE verwarmschema.thermostaat_schedule (
sid serial NOT NULL,
dag int4 NULL,
tijd varchar NULL,
"temp" float4 NULL,
fk_tid int4 NOT NULL,
CONSTRAINT thermostaat_schedule_pk PRIMARY KEY (sid,dag,tijd,fk_tid),
CONSTRAINT thermostaat_schedule_thermostaat_fk FOREIGN KEY (fk_tid) REFERENCES verwarmschema.thermostaat(tid) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE verwarmschema.radiator_history (
rhid serial NOT NULL,
fk_rid int4 NOT NULL,
open_close int4 NOT NULL,
datumtijd timestamp NOT NULL,
CONSTRAINT radiator_history_pk PRIMARY KEY (rhid),
CONSTRAINT radiator_history_radiator_fk FOREIGN KEY (fk_rid) REFERENCES verwarmschema.radiator(rid) ON DELETE CASCADE ON UPDATE CASCADE
);
'''
1. Now that you have your database set up, you should manually add room details in the main thermostat table (in sync with sensors.ini). Also add associated radiators in the radiator table. Be sure to put the right adresses for the thermostats and radiator valves. When using an ESP32 the nameconvention is '''esp32_ip@valve_mac''' for example: '''192.168.0.1@ae:01:e6:78:a1'''
1. Also , which should be an improvement, is that there are some variables stored in the 'verwarmonoff.py' module, under the 'onoff' directory. The section is marked with comment 'configurable variables'.
The most important variable here is the rpi adress, which should be pointing towards the nefit http server of robert klep.
Other mentioned variables are settings that you could adjust to fit your usage
smartheat variables are yet untested
For usage of smartheating you should replace your apikey with yours. You can create it on api.weather.com.
Also you should fill in your own logitide and latitude, of course.
1. build your docker images with following command in the root folder of the repo
'''
docker-compose build
'''
this will take a while, as it also runs apt-get upgrade and update
1. All set, run with '''docker-compose up'''

[optionally]
If you experience problems with the range of your bluetooth to your valves, you will need to set up an ESP32 with http and bluetooth closer by.
I've set it up to connect to my wifi and host an http server on port 80 which can receive commands from the eq3 object
Navigate to the 'Http_EQ3_Control.ino' file and modify the wifi and password settings to match your situation (on line 7 and 8)
'''
const char *ssid = "";
const char *password = "";
'''


# Screenshots


# Todo
1. replace sensors.ini with database content instead
1. when starting for first time, create tables itself
1. get rid of the variables in verwarmonoff.py and read them from database
1. Use proper timezone settings...
