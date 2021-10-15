#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <NimBLEDevice.h>
#include <stdlib.h>

const char *ssid = "VBwifiBerging";
const char *password = "Hoera888";
static BLERemoteCharacteristic* pRemoteCharacteristic;
static BLEAdvertisedDevice* myDevice;
static BLEUUID serviceUUID("3e135142-654f-9090-134a-a6ff5bb77046");
static BLEUUID    xUUID("2A1F");
static BLEUUID    charUUID("3fa4585a-ce4a-3bad-db4b-b8df8179ea09");
static BLEClient*  pClient;
static bool isConnected = false;

IPAddress local_IP(192, 168, 0, 126);
IPAddress gateway(192, 168, 0, 2);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(192, 168, 0, 125); //optional
IPAddress secondaryDNS(8, 8, 8, 8); //optional
IPAddress ipserver(192, 168, 0, 125);
//IPAddress ipserver(192, 168, 0, 153);

WebServer server(80);
WiFiClient client;
BLEScan* pBLEScan;

void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";

  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }

  server.send(404, "text/plain", message);
}

bool Connect(std::string mac){
  bool doConnect = false;
  if (isConnected){//check if we were already connected to this client
    Serial.println(" - Already connected, disconnecting");
    //if (pClient->getPeerAddress().toString().c_str().toupper() != mac.toupper()){
    //  Serial.println(" - But to different client, reconnecting to new client");
      if (pClient->disconnect()){
        doConnect = true;
      }      
    //}
  }
  else{
    pClient  = BLEDevice::createClient();
    Serial.println(" - Created client");
    doConnect = true;
  }
  if (doConnect){
    if (pClient->connect(NimBLEAddress(mac))){
      Serial.print("Connected to: ");
      Serial.println(pClient->getPeerAddress().toString().c_str());
      isConnected = true;
      return true;
    }
    else{
      isConnected = false;
      return false;
    }
  }
  //Serial.print(" - Not connecting, we were already");
}

void ManualMode() {
  String out = "";

  if (Connect(server.arg("mac").c_str())){
  
    BLERemoteService* pRemoteService = pClient->getService(serviceUUID);
    if (pRemoteService == nullptr) {
        Serial.print("Failed to find our service UUID: ");
        Serial.println(serviceUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
    }
    else{
      Serial.println(" - Found our service");
      pRemoteCharacteristic = pRemoteService->getCharacteristic(charUUID);
      if (pRemoteCharacteristic == nullptr) {
        Serial.print("Failed to find our characteristic UUID: ");
        Serial.println(charUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
      }
      else{
        if(pRemoteCharacteristic->canWrite()) {
          Serial.println(" - Found our characteristic");
          uint8_t modeByte = 0x40;
          uint8_t command[] = {0x40,modeByte};
          
          if(pRemoteCharacteristic->writeValue(command, 2, true)) {
            Serial.println(" - Set mode to manual");
            out = "[{\"result\": \"done\"}]";
          }
        }
        else{
          Serial.println("Write failed");
          out = "[{\"result\": \"failed\"}]";
        }
        
      }
    }
  }
  else{
    out = "[{\"result\": \"failed\"}]";
  }
  pClient->disconnect();
  isConnected = false;
  server.send(200, "application/json", out);  
}

void OpenCloseVale() {
  String out = "";

  if (Connect(server.arg("mac").c_str())){
  
    BLERemoteService* pRemoteService = pClient->getService(serviceUUID);
    if (pRemoteService == nullptr) {
        Serial.print("Failed to find our service UUID: ");
        Serial.println(serviceUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
    }
    else{
      Serial.println(" - Found our service");
      pRemoteCharacteristic = pRemoteService->getCharacteristic(charUUID);
      if (pRemoteCharacteristic == nullptr) {
        Serial.print("Failed to find our characteristic UUID: ");
        Serial.println(charUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
      }
      else{
        if(pRemoteCharacteristic->canWrite()) {
          Serial.println(" - Found our characteristic");
          uint8_t modeByte = 0x09;
          //uint8_t command[] = {0x41, 0x09}; //close be default
          bool closed = true;
          if (server.arg("status") == "open"){
            modeByte = 0x3c;
            closed = false;
          }          
          uint8_t command[] = {0x41,modeByte};
          if(pRemoteCharacteristic->writeValue(command, 2, true)) {
            if (closed){
              Serial.println(" - Set valve closed");
            }
            else{
              Serial.println(" - Set valve open");
            }
            out = "[{\"result\": \"done\"}]";
          }
        }
        else{
          Serial.println("Write failed");
          out = "[{\"result\": \"failed\"}]";
        }
        
      }
    }
  }
  else{
    out = "[{\"result\": \"failed\"}]";
  }
  pClient->disconnect();
  isConnected = false;
  server.send(200, "application/json", out);
}

void SetTemp() {
  String out = "";

  if (Connect(server.arg("mac").c_str())){
  
    BLERemoteService* pRemoteService = pClient->getService(serviceUUID);
    if (pRemoteService == nullptr) {
        Serial.print("Failed to find our service UUID: ");
        Serial.println(serviceUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
    }
    else{
      Serial.println(" - Found our service");
      pRemoteCharacteristic = pRemoteService->getCharacteristic(charUUID);
      if (pRemoteCharacteristic == nullptr) {
        Serial.print("Failed to find our characteristic UUID: ");
        Serial.println(charUUID.toString().c_str());
        pClient->disconnect();
        out = "[{\"result\": \"failed\"}]";
      }
      else{
        if(pRemoteCharacteristic->canWrite()) {
          Serial.println(" - Found our characteristic");
          
          float temperature = server.arg("temp").toFloat();
          
          uint8_t command[] = { 0x41, (uint8_t)(temperature * 2) };
          
          if(pRemoteCharacteristic->writeValue(command, 2, true)) {
            Serial.print(" - Set to temp ");
            Serial.println(temperature);
            out = "[{\"result\": \"done\"}]";
          }
        }
        else{
          Serial.println("Write failed");
          out = "[{\"result\": \"failed\"}]";
        }
        
      }
    }
  }
  else{
    out = "[{\"result\": \"failed\"}]";
  }
  pClient->disconnect();
  isConnected = false;
  server.send(200, "application/json", out);
}

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {

float BitShiftCombine( unsigned char x_high, unsigned char x_low)
      {
        int combined;
        combined = x_high;              //send x_high to rightmost 8 bits
        combined = combined<<8;         //shift x_high over to leftmost 8 bits
        combined |= x_low;                 //logical OR keeps x_high intact in combined and fills in                                                             //rightmost 8 bits
        return combined;
      }
  void onResult(BLEAdvertisedDevice* advertisedDevice) {
    String naam = advertisedDevice->getName().c_str();
    String firstFour = naam.substring(0,4);
    
    if (firstFour == "ATC_") {
      //Serial.print("Found ServiceUUID: ");
      //Serial.println(devUUID.toString().c_str());
      //Serial.println("");
      std::string serviceData = advertisedDevice->getServiceData();
      std::string mac = advertisedDevice->getAddress();
      
      const char *val = serviceData.c_str();
      Serial.print("Hex: ");
      for (int i = 0; i < 19; i++) {
        Serial.print((int)val[i], HEX);
        Serial.print(" ");
      }
      Serial.println(" ");
      Serial.print("Hum: ");
      Serial.println((int)val[8]);
      Serial.print("Bat: ");
      Serial.println((int)val[9]);
      
      float temp_raw = BitShiftCombine(val[6],val[7]) / 10;
      Serial.print("temp: ");
      Serial.println(temp_raw);
         
      Serial.println(naam);
      if (client.connect(ipserver, 6543)) {
      //if (client.connect(ipserver, 5000)) {
          Serial.println("connected");
          // Make a HTTP request:
          client.print("GET /setreading?");
          client.print("hum=");
          client.print((int)val[8]);
          client.print("&");
          client.print("bat=");
          client.print((int)val[9]);
          client.print("&");
          client.print("temp=");
          client.print(temp_raw);
          client.print("&");
          client.print("mac=");
          client.print(mac.c_str());
          client.print(" HTTP/1.0");
          client.println();
      }
    }
  } 
}; 

void setup(void) {

  Serial.begin(115200);
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("STA Failed to configure");
  }
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin("esp32")) {
    Serial.println("MDNS responder started");
  }

  server.on("/manualmode", HTTP_GET, ManualMode);
  server.on("/valve", HTTP_GET, OpenCloseVale);
  server.on("/settemp", HTTP_GET, SetTemp);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("HTTP server started");
  
  Serial.println("Starting Arduino BLE Client application...");
  BLEDevice::init("");

  // Retrieve a Scanner and set the callback we want to use to be informed when we
  // have detected a new device.  Specify that we want active scanning and start the
  // scan to run for 5 seconds.
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setInterval(1349);
  pBLEScan->setWindow(449);
  pBLEScan->setActiveScan(true);
  
}

void loop(void) {
  server.handleClient();
  pBLEScan->start(5, false);
  pBLEScan->clearResults();
}
