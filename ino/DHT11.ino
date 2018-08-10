#include <DHT.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include "conf.h"

#define DHTTYPE DHT11
#define DHT11_PIN 2

/* ssid, password, id come from uncommitted config */

DHT dht(DHT11_PIN, DHTTYPE);

int temp;
int humidity;
String token = "";

String registerURL = "http://192.168.0.88:5000/register";
String readingsURL = "http://192.168.0.88:5000/iot";

void setup(){
  Serial.begin(9600);
  delay(100);

  dht.begin();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print("Connecting...");
  }
}

void loop()
{
  temp = dht.readTemperature();
  humidity = dht.readHumidity();

  HTTPClient http;
  if (token.equals("")){
    http.begin(registerURL);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    if (http.POST("id=" + String(id)) == 200){
      token = http.getString();
      http.end();
    }
  }
  if (!token.equals("")){
    String postParams = "token=" + token + "&temp=" + String(temp) + "&humidity=" + String(humidity);
    http.begin(readingsURL); 
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    int httpCode = http.POST(postParams);
    http.writeToStream(&Serial);  
    http.end();
  }
  delay(5000);
}

