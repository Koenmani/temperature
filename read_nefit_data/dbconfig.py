import os

if os.getenv("VERWARMING_DB_IP") is not None:
	dbip = os.getenv("VERWARMING_DB_IP")
else:
	dbip = "192.168.0.125"
	
if os.getenv("VERWARMING_DBNAME") is not None:
	dbname = os.getenv("VERWARMING_DBNAME")
else:
	dbname = "verwarming"

if os.getenv("VERWARMING_DBUSER") is not None:
	dbuser = os.getenv("VERWARMING_DBUSER")
else:
	dbuser= "postgres"

if os.getenv("VERWARMING_DBPASS") is not None:
	dbpass = os.getenv("VERWARMING_DBPASS")
else:
	dbpass = "docker"




