FROM mongo

ADD init-devices.js /docker-entrypoint-initdb.d/
VOLUME ["/data/db"]
WORKDIR /data

EXPOSE 27017
