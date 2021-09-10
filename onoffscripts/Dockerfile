FROM python

ENV LANG C.UTF-8
ENV TZ Europe/Amsterdam

WORKDIR /usr/verwarming
COPY ./requirements.txt /usr/verwarming/
COPY ./verwarmcontroller.py /usr/verwarming/verwarmcontroller.py
COPY dbconfig.py /usr/verwarming/dbconfig.py


RUN pip3 install -r /usr/verwarming/requirements.txt
CMD python3 verwarmcontroller.py
EXPOSE 5000