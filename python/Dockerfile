FROM python:3
RUN mkdir -p /usr/src/iot_app
WORKDIR /usr/src/
COPY ./iot_app /usr/src/iot_app
RUN mkdir /usr/src/iot_app/logs
COPY ./requirements.txt /usr/src
RUN pip3 install -r requirements.txt
EXPOSE 5000
CMD ["python", "-m", "iot_app"]
