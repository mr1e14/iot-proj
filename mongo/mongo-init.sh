#!/bin/bash
set -eu

mongo -- <<EOF
    db = db.getSiblingDB("$MONGO_INITDB_DATABASE");
    db.createUser({user: "$APP_USERNAME", pwd: "$APP_PASSWORD", roles: ["readWrite"]});

    db.createCollection("temp_sensor")
    db.createCollection("humidity_sensor")
    db.createCollection("lights")
EOF
