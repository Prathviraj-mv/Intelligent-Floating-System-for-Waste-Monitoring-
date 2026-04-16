#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP085.h>

// ===== AS5600 =====
#define AS5600_ADDR 0x36
#define ANGLE_REG 0x0E

// ===== FLOW CONSTANTS =====
#define RADIUS 0.05
#define PIPE_RADIUS 0.01
#define K_FACTOR 0.75

// ===== LED =====
#define LED_PIN 8

// ===== TDS =====
#define TDS_PIN A0
#define VREF 5.0
#define SCOUNT 30

// ===== OBJECT =====
Adafruit_BMP085 bmp;

// ===== VARIABLES =====
int lastAngle = 0;
long totalCounts = 0;

unsigned long lastTime = 0;
unsigned long ledTime = 0;
unsigned long angleTime = 0;

bool ledState = false;

// ===== TDS BUFFERS =====
int analogBuffer[SCOUNT];
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;

float tdsValue = 0;
float temperature = 25;

// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  Wire.begin();
  Wire.setClock(100000);

  pinMode(LED_PIN, OUTPUT);

  delay(100);

  if (!bmp.begin()) {
    Serial.println("BMP180 ERROR");
    while (1)
      ;
  }

  Serial.println("SYSTEM READY");
}

// ================= LOOP =================
void loop() {

  // ===== AS5600 CONTROLLED READ =====
  if (millis() - angleTime >= 5) {
    int angle = readAngle();

    int delta = angle - lastAngle;

    if (delta > 2048) delta -= 4096;
    if (delta < -2048) delta += 4096;

    totalCounts += delta;
    lastAngle = angle;

    angleTime = millis();
  }

  // ===== TDS CONTINUOUS SAMPLING =====
  sampleTDS();

  // ===== LED =====
  if (millis() - ledTime >= 1000) {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
    ledTime = millis();
  }

  // ===== MAIN OUTPUT EVERY 1 SEC =====
  if (millis() - lastTime >= 1000) {

    float rotations = totalCounts / 4096.0;
    float rpm = abs(rotations * 60.0);

    float velocity = K_FACTOR * (2 * 3.1416 * RADIUS * rpm) / 60.0;
    float area = 3.1416 * PIPE_RADIUS * PIPE_RADIUS;
    float flowRate = area * velocity;
    float flow_L_min = flowRate * 1000.0 * 60.0;

    // ===== BMP180 =====
    float temp = bmp.readTemperature();
    float pressure = bmp.readPressure();
    float altitude = bmp.readAltitude();

    temperature = temp;  // for TDS compensation
    float tds = computeTDS();

    Serial.print("temp:");
    Serial.print(temp);
    Serial.print(",pressure:");
    Serial.print(pressure);
    Serial.print(",alt:");
    Serial.print(altitude);
    Serial.print(",rpm:");
    Serial.print(rpm);
    Serial.print(",flow:");
    Serial.print(flow_L_min);
    Serial.print(",tds:");
    Serial.print(tds);
    Serial.print(",ph:");
    Serial.print(random(65, 85) / 10.0);  // fake pH
    Serial.println();

    totalCounts = 0;
    lastTime = millis();
  }
}

// ================= AS5600 READ =================
int readAngle() {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(ANGLE_REG);

  if (Wire.endTransmission(false) != 0) {
    return lastAngle;
  }

  Wire.requestFrom(AS5600_ADDR, 2);
  delayMicroseconds(200);

  if (Wire.available() == 2) {
    int highByte = Wire.read();
    int lowByte = Wire.read();
    return ((highByte << 8) | lowByte) & 0x0FFF;
  }

  return lastAngle;
}

// ================= TDS SAMPLING =================
void sampleTDS() {
  static unsigned long sampleTime = millis();

  if (millis() - sampleTime > 40) {
    sampleTime = millis();
    analogBuffer[analogBufferIndex] = analogRead(TDS_PIN);
    analogBufferIndex++;

    if (analogBufferIndex == SCOUNT) {
      analogBufferIndex = 0;
    }
  }
}

// ================= TDS COMPUTE =================
float computeTDS() {

  for (int i = 0; i < SCOUNT; i++) {
    analogBufferTemp[i] = analogBuffer[i];
  }

  // Sort (median filter)
  for (int i = 0; i < SCOUNT - 1; i++) {
    for (int j = i + 1; j < SCOUNT; j++) {
      if (analogBufferTemp[i] > analogBufferTemp[j]) {
        int temp = analogBufferTemp[i];
        analogBufferTemp[i] = analogBufferTemp[j];
        analogBufferTemp[j] = temp;
      }
    }
  }

  float avgVoltage = analogBufferTemp[SCOUNT / 2] * VREF / 1024.0;

  float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
  float compensationVoltage = avgVoltage / compensationCoefficient;

  float tds = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage
               - 255.86 * compensationVoltage * compensationVoltage
               + 857.39 * compensationVoltage)
              * 0.5;

  return tds;
}