FROM python

ENV LANG C.UTF-8
ENV TZ Europe/Amsterdam

WORKDIR /usr/verwarming
COPY ./requirements.txt /usr/verwarming/
COPY ./verwarmonoff.py /usr/verwarming/verwarmonoff.py
COPY ./eq3_control_object.py /usr/verwarming/eq3_control_object.py
COPY ./daikin_control_object.py /usr/verwarming/daikin_control_object.py
COPY ./custom_control_object.py /usr/verwarming/custom_control_object.py

RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d
RUN apt-get update
RUN apt-get -y install bluetooth bluez

RUN pip3 install -r /usr/verwarming/requirements.txt
ENTRYPOINT python3 -u verwarmonoff.py
CMD /bin/bash
