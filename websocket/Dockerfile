FROM python

ENV LANG C.UTF-8
ENV TZ Europe/Amsterdam

WORKDIR /usr/verwarming
COPY ./requirements.txt /usr/verwarming/
COPY ./ws_handler.py /usr/verwarming/ws_handler.py

RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d

RUN pip3 install -r /usr/verwarming/requirements.txt
ENTRYPOINT python3 -u ws_handler.py
EXPOSE 8081
