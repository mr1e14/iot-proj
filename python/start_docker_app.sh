# use env variables to update config values if changed
confd -onetime -backend env
# start server
python -m iot_app