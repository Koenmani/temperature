FROM python

ENV LANG C.UTF-8
ENV TZ Europe/Amsterdam

WORKDIR /usr/verwarming
COPY ./requirements.txt /usr/verwarming/
COPY ./sensors.ini /usr/verwarming/
COPY ./SendtoDB.py /usr/verwarming/SendtoDB.py
COPY ./LYWSD03MMC.py /usr/verwarming/LYWSD03MMC.py
COPY ./bluetooth_utils.py /usr/verwarming/bluetooth_utils.py
COPY ./dbconfig.py /usr/verwarming/dbconfig.py


RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d
RUN apt-get update
RUN apt-get -y install bluetooth libbluetooth-dev libglib2.0-dev
RUN pip3 install -r /usr/verwarming/requirements.txt
ENTRYPOINT service dbus start

ENTRYPOINT while true; do timeout 30 python3 ./LYWSD03MMC.py -a -r -b -df sensors.ini -odl -wdt 60 -call SendtoDB.py; sleep 60; done
CMD /bin/bash
 