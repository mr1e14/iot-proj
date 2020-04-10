db = db.getSiblingDB("devices");

db.createUser(
        {
            user: "admin",
            pwd: "pw",
            roles: [
                {
                    role: "readWrite",
                    db: "devices"
                }
            ]
        }
);

db.createCollection("temp_sensor");
db.createCollection("humidity_sensor");
db.createCollection("lights");


