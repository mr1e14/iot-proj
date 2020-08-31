FROM mongo

# root is a database admin user
# app user only has access to the iot db which python server uses for persistance

ENV MONGO_INITDB_ROOT_USERNAME=db_root \
    MONGO_INITDB_ROOT_PASSWORD=password \
    MONGO_INITDB_DATABASE=iot_db \
    APP_USERNAME=app_user \
    APP_PASSWORD=app_password \
    PORT=27017

ADD mongo-init.sh /docker-entrypoint-initdb.d/

VOLUME ["/data/db"]
WORKDIR /data

EXPOSE $PORT

