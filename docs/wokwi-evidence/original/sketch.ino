#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <atomic>
#include <esp_system.h>
#include "controller.h"

// Use only synthetic demonstration telemetry with this public, unencrypted broker.
const char* BROKER="broker.hivemq.com";
const uint16_t BROKER_PORT=1883;
// Change this suffix for your own session, and give Python the identical topic.
const char* TOPIC="smartagri/23bct0157/demo-v1/data";
const uint32_t SAMPLE_MS=5000, DOSE_WINDOW_MS=60000;
// Simulation acceleration: 1 commanded irrigation minute = 1 simulator second.
// All timing is ESP32/simulation time, not necessarily wall-clock time.
const uint32_t MS_PER_IRRIGATION_MINUTE=1000;
const uint8_t DHT_PIN=4,SOIL_PIN=34,PUMP_PIN=2,FAULT_PIN=25,NET_PIN=26;

DHT dht(DHT_PIN,DHT22);
Adafruit_SSD1306 display(128,64,&Wire,-1);
bool oledReady=false,overrideInputs=false,forcedFault=false,serialOffline=false;
bool baseline=false,resetFilters=true,haveSample=false,pendingDose=true;
float overrideM=50,overrideT=27,overrideH=60;
float rawM=0,rawT=0,rawH=0,moisture=0,temperature=0,humidity=0;
bool sensorOK=false;const char* state="STARTUP";
agri::Average avgM,avgT,avgH;agri::Result decision={false,0,0,false};agri::Pump pump;
uint32_t sequence=0,lastSample=0,lastWindow=0,lastStatus=0;
uint32_t inferenceUs=0,sampleWorkUs=0;
std::atomic<bool> networkAllowed(true),mqttOnline(false);
QueueHandle_t telemetryQueue;
struct Telemetry { char data[1000]; };
char command[100];size_t commandLength=0;

void draw(){
  if(!oledReady)return;
  display.clearDisplay();display.setTextColor(SSD1306_WHITE);display.setTextSize(1);
  display.setCursor(0,0);display.printf("%s %s\n",baseline?"BASE":"FUZZY",overrideInputs?"TEST":"LIVE");
  if(sensorOK)display.printf("T %.1fC H %.1f%%\nM %.1f%%\n",temperature,humidity,moisture);
  else display.println("SENSOR INVALID\nOutputs OFF");
  display.printf("Cmd %.2f min\nLED %s MQTT %s\n",decision.minutes,pump.on?"ON":"OFF",mqttOnline.load()?"ON":"OFF");
  display.println(state);display.display();
}
void emit(){
  Telemetry msg;const char* fmt=
    "{\"schema\":1,\"device_id\":\"esp32-wokwi-01\",\"seq\":%lu,\"uptime_ms\":%lu,"
    "\"controller\":\"%s\",\"input_source\":\"%s\",\"sensor_ok\":%s,"
    "\"temperature_c\":%s,\"humidity_pct\":%s,\"moisture_pct\":%s,"
    "\"raw_temperature_c\":%s,\"raw_humidity_pct\":%s,\"raw_moisture_pct\":%s,"
    "\"irrigation_minutes\":%.4f,\"pump_on\":%s,\"status\":\"%s\","
    "\"low_moisture_alert\":%s,\"mqtt_connected\":%s,\"inference_us\":%lu,"
    "\"sample_work_us\":%lu,\"ms_per_irrigation_minute\":%lu}";
  char t[16],h[16],m[16],rt[16],rh[16],rm[16];
  if(sensorOK){snprintf(t,16,"%.4f",temperature);snprintf(h,16,"%.4f",humidity);snprintf(m,16,"%.4f",moisture);
    snprintf(rt,16,"%.4f",rawT);snprintf(rh,16,"%.4f",rawH);snprintf(rm,16,"%.4f",rawM);}
  else {strcpy(t,"null");strcpy(h,"null");strcpy(m,"null");strcpy(rt,"null");strcpy(rh,"null");strcpy(rm,"null");}
  int n=snprintf(msg.data,sizeof(msg.data),fmt,(unsigned long)++sequence,(unsigned long)millis(),
    baseline?"baseline":"fuzzy",overrideInputs?"serial_override":"simulated_sensors",sensorOK?"true":"false",
    t,h,m,rt,rh,rm,decision.minutes,pump.on?"true":"false",state,
    sensorOK&&rawM<=30.0f?"true":"false",mqttOnline.load()?"true":"false",
    (unsigned long)inferenceUs,(unsigned long)sampleWorkUs,(unsigned long)MS_PER_IRRIGATION_MINUTE);
  if(n<0||n>=(int)sizeof(msg.data)){Serial.println("ERROR payload too large");return;}
  Serial.println(msg.data);
  // Latest-snapshot queue, NOT a durable offline history. Older unsent snapshots are overwritten.
  xQueueOverwrite(telemetryQueue,&msg);
}
void invalidate(){
  sensorOK=false;state="SENSOR_FAULT";decision={false,0,0,false};pump.stop();
  inferenceUs=0;sampleWorkUs=0;
  digitalWrite(PUMP_PIN,LOW);resetFilters=true;pendingDose=false;
}
void sample(){
  uint32_t workStart=micros();
  if(overrideInputs){rawM=overrideM;rawT=overrideT;rawH=overrideH;}
  else {rawM=100.0f*analogRead(SOIL_PIN)/4095.0f;rawT=dht.readTemperature();rawH=dht.readHumidity();}
  if(forcedFault||digitalRead(FAULT_PIN)==LOW||!agri::valid(rawM,rawT,rawH)){
    invalidate();sampleWorkUs=micros()-workStart;inferenceUs=0;draw();emit();return;
  }
  if(resetFilters){avgM.reset();avgT.reset();avgH.reset();resetFilters=false;}
  moisture=avgM.add(rawM);temperature=avgT.add(rawT);humidity=avgH.add(rawH);
  uint32_t inferenceStart=micros();decision=agri::evaluate(moisture,temperature,humidity,baseline);
  inferenceUs=micros()-inferenceStart;sensorOK=decision.valid;
  if(!sensorOK){invalidate();state="RULE_FAULT";}
  else {
    state=rawM<=30?"LOW_MOISTURE":"OK";
    // Raw wet readings stop an existing dose without waiting for the filter to settle.
    if(rawM>=80||decision.minutes<=0)pump.stop();
    if(pendingDose){
      if(rawM<80)pump.start(millis(),decision.minutes,MS_PER_IRRIGATION_MINUTE);
      pendingDose=false;lastWindow=millis();
    }
  }
  digitalWrite(PUMP_PIN,pump.on?HIGH:LOW);sampleWorkUs=micros()-workStart;
  draw();emit();
}
void scheduleTest(){
  pump.stop();digitalWrite(PUMP_PIN,LOW);pendingDose=true;resetFilters=true;
  lastSample=millis()-SAMPLE_MS;haveSample=false;
}
void help(){Serial.println("COMMANDS: SET moisture temperature humidity | LIVE | MODE FUZZY | MODE BASELINE | FAULT ON | FAULT OFF | NET OFF | NET ON | RUN | HELP");}
void parseCommand(char* s){
  float m,t,h;char extra;
  if(sscanf(s,"SET %f %f %f %c",&m,&t,&h,&extra)==3){
    if(!agri::valid(m,t,h)){Serial.println("REJECTED use moisture 0..100, temp 0..50, humidity 0..100");return;}
    overrideInputs=true;overrideM=m;overrideT=t;overrideH=h;scheduleTest();
  }else if(!strcmp(s,"LIVE")){overrideInputs=false;scheduleTest();}
  else if(!strcmp(s,"MODE FUZZY")){baseline=false;scheduleTest();}
  else if(!strcmp(s,"MODE BASELINE")){baseline=true;scheduleTest();}
  else if(!strcmp(s,"FAULT ON")){forcedFault=true;invalidate();draw();emit();}
  else if(!strcmp(s,"FAULT OFF")){forcedFault=false;scheduleTest();}
  else if(!strcmp(s,"NET OFF")){serialOffline=true;networkAllowed.store(false);}
  else if(!strcmp(s,"NET ON")){serialOffline=false;}
  else if(!strcmp(s,"RUN")){scheduleTest();}
  else {help();return;}
  Serial.print("ACK ");Serial.println(s);
}
void readCommands(){
  while(Serial.available()){
    char c=Serial.read();if(c=='\r')continue;
    if(c=='\n'){command[commandLength]=0;if(commandLength)parseCommand(command);commandLength=0;}
    else if(commandLength<sizeof(command)-1)command[commandLength++]=c;
    else {commandLength=0;Serial.println("ERROR command too long");}
  }
}
// All DNS/socket/broker calls occur on a separate ESP32 task. No remote pump-control topic exists.
void networkTask(void*){
  WiFiClient transport;PubSubClient mqtt(transport);
  mqtt.setServer(BROKER,BROKER_PORT);mqtt.setBufferSize(1100);mqtt.setSocketTimeout(1);
  // Generous broker keepalive: simulator clocks can run much slower than wall time.
  mqtt.setKeepAlive(300);WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(false);
  uint32_t lastTry=millis()-3000;bool wifiStarted=false;
  for(;;){
    if(!networkAllowed.load()){
      mqttOnline.store(false);if(mqtt.connected())mqtt.disconnect();
      if(wifiStarted){WiFi.disconnect(false,false);wifiStarted=false;}
    }else if(!wifiStarted){WiFi.begin("Wokwi-GUEST","",6);wifiStarted=true;lastTry=millis()-3000;}
    else if(WiFi.status()!=WL_CONNECTED){
      mqttOnline.store(false);
      if((uint32_t)(millis()-lastTry)>=10000){lastTry=millis();WiFi.begin("Wokwi-GUEST","",6);}
    }else if(!mqtt.connected()){
      mqttOnline.store(false);
      if((uint32_t)(millis()-lastTry)>=3000){
        lastTry=millis();String clientId="agri-"+String((uint32_t)ESP.getEfuseMac(),HEX)+"-"+String(esp_random(),HEX);
        mqtt.connect(clientId.c_str());
      }
    }else{
      mqttOnline.store(true);mqtt.loop();Telemetry msg;
      if(xQueueReceive(telemetryQueue,&msg,0)==pdTRUE)mqtt.publish(TOPIC,msg.data,false);
    }
    vTaskDelay(pdMS_TO_TICKS(25));
  }
}
void setup(){
  Serial.begin(115200);pinMode(PUMP_PIN,OUTPUT);digitalWrite(PUMP_PIN,LOW);
  pinMode(FAULT_PIN,INPUT_PULLUP);pinMode(NET_PIN,INPUT_PULLUP);pinMode(SOIL_PIN,INPUT);
  analogReadResolution(12);analogSetPinAttenuation(SOIL_PIN,ADC_11db);
  dht.begin();Wire.begin(21,22);Wire.setTimeOut(50);
  oledReady=display.begin(SSD1306_SWITCHCAPVCC,0x3c);draw();
  telemetryQueue=xQueueCreate(1,sizeof(Telemetry));
  if(!telemetryQueue){Serial.println("FATAL no telemetry queue; stopped");while(true)delay(1000);}
  if(xTaskCreatePinnedToCore(networkTask,"mqtt",6144,nullptr,1,nullptr,0)!=pdPASS)
    Serial.println("WARNING network task unavailable; serial/local control still usable");
  Serial.println("SMARTAGRI SIMULATION v1 | DHT22 | I2C 21/22 | QoS0 | demo 1 minute = 1 second");
  help();lastSample=millis()-SAMPLE_MS;
}
void loop(){
  readCommands();uint32_t now=millis();
  networkAllowed.store(!serialOffline&&digitalRead(NET_PIN)!=LOW);
  if((forcedFault||digitalRead(FAULT_PIN)==LOW)&&sensorOK){invalidate();draw();emit();}
  if((uint32_t)(now-lastWindow)>=DOSE_WINDOW_MS){pendingDose=true;lastWindow=now;}
  bool wasOn=pump.on;pump.tick(now);digitalWrite(PUMP_PIN,pump.on?HIGH:LOW);
  if(wasOn&&!pump.on){draw();emit();}
  if((uint32_t)(now-lastSample)>=SAMPLE_MS){lastSample=now;sample();haveSample=true;}
  if((uint32_t)(now-lastStatus)>=1000){lastStatus=now;draw();}
  delay(10);
}
