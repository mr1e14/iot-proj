FROM python:3

# Overridable secret variables
ENV DB_HOST=iot-db \
    DB_PORT=27017 \
    DB_NAME=iot_db \
    DB_USERNAME=app_user \
    DB_PASSWORD=app_password \
    APP_HOST=0.0.0.0 \
    APP_PORT=5000 \
    SENSORS_API_KEY=secretDevSensorsKey \
    LIGHTS_API_KEY=secretDevLightsKey

# Copy Python source code and set up working directory
ENV IOT_APP_HOME=/usr/src/iot_app
RUN mkdir -p $IOT_APP_HOME
COPY ./iot_app $IOT_APP_HOME
RUN mkdir $IOT_APP_HOME/logs
ARG WORK_DIR=/usr/src
WORKDIR $WORK_DIR
# Install dependencies
COPY ./requirements.txt /usr/src
RUN pip3 install -r requirements.txt

# Set up confd for generating YAML secrets config using environment variables
ARG CONFD_BIN=/usr/local/bin/confd
RUN curl -s -L https://github.com/kelseyhightower/confd/releases/download/v0.16.0/confd-0.16.0-linux-amd64 -o $CONFD_BIN
RUN chmod +x $CONFD_BIN
ENV CONFD_HOME=/etc/confd
RUN mkdir $CONFD_HOME
COPY ./confd/conf.d $CONFD_HOME/conf.d
COPY ./confd/templates $CONFD_HOME/templates

# Set up start script for updating config and running server
COPY ./start_docker_app.sh $WORK_DIR
RUN chmod +x ./start_docker_app.sh

CMD ./start_docker_app.sh
