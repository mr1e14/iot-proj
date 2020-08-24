## iot-proj
Includes:
- Flask server for processing sensor readings, smart lights discovery and management, REST API, and handling
custom Alexa skill requests
- Mongo database, used by the Flask server
- INO scripts for reading sensor values and sending data to the Flask server
- Scripts for environment setup

## Docker
Create a docker network for components to communicate with  
`docker network create iot_net`  
Build the Flask application image using  
`docker build -t iotproj:<TAG> .`  
Run container with:  
`docker run -d --name iot-app --net iot-net -p <HOST_PORT>:<CONTAINER_PORT> iotproj:<TAG>
`  
Override environment variables with `-e` e.g. `-e APP_PORT=5001`
