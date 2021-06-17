FROM node:10

RUN npm install nefit-easy-http-server -g

ENV NEFIT_PORT=8000

CMD easy-server --host=$NEFIT_IP --port=$NEFIT_PORT
EXPOSE 8000