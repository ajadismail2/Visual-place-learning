#include <PID_v1.h>
#include <Wire.h>

// ========== PIN CONFIGURATION ==========
#define PWM_PIN 9
#define LED_PIN 13

// ========== TMP117 DIRECT I2C ==========
// ADD0 pin sets address: GND=0x48, Vcc=0x49, SDA=0x4A, SCL=0x4B
static uint8_t       tmp117Addr     = 0x48;
static const uint8_t TMP117_REG_TEMP = 0x00;

static const float   TMP117_RES     = 0.0078125f;

// ========== xEMPERATURE SETTINGS ==========
double targetTemp = 34.8;
double tempOffset = 0;

// Allow the temperature to rise slightly above the target without
// immediately increasing cooling. For example, with a 34.80 C target,
// 34.80 to 35.00 C is treated as the acceptable upper deadband.
const double UPPER_DEADBAND = 0;

// ========== PID TUNING ==========
double Kp = 60;
double Ki = 4.0;
double Kd = 5.0;

// ========== PID VARIABLES ==========
double currentTemp = 0.0;
double controlTemp  = 0.0;
double setpoint    = 0.0;
double pwmOutput   = 0.0;

// ========== SAFETY ==========
const double MAX_SAFE_TEMP = 80.0;
const double MIN_SAFE_TEMP = -5.0;

// ========== PID ==========
PID myPID(&controlTemp, &pwmOutput, &setpoint, Kp, Ki, Kd, DIRECT);

// ========== TIMING ==========
unsigned long lastDisplay   = 0;
const unsigned long displayInterval = 500;
unsigned long startTime     = 0;

// ========== SENSOR FILTERING ==========
unsigned long lastSensorRead  = 0;
const unsigned long sensorInterval = 100;
float filteredTemp = 0.0;
const float ALPHA  = 0.3;
bool firstRead     = true;

// ========== STATUS ==========
bool systemActive = true;

// ========================================
// TMP117 — scan all four possible addresses
// ========================================
bool detectTMP117() {
  const uint8_t candidates[] = { 0x48, 0x49, 0x4A, 0x4B };
  for (uint8_t i = 0; i < 4; i++) {
    uint8_t addr = candidates[i];
    Wire.beginTransmission(addr);
    Wire.write(TMP117_REG_TEMP);
    if (Wire.endTransmission() != 0) continue;
    Wire.requestFrom(addr, (uint8_t)2);
    if (Wire.available() < 2) continue;
    int16_t raw = ((int16_t)Wire.read() << 8) | Wire.read();
    float t = raw * TMP117_RES;
    if (t > -10.0f && t < 100.0f) {
      tmp117Addr = addr;
      return true;
    }
  }
  return false;
}

// ========================================
// TMP117 — read temperature register
// ========================================
float readTMP117() {
  Wire.beginTransmission(tmp117Addr);
  Wire.write(TMP117_REG_TEMP);
  if (Wire.endTransmission() != 0) return NAN;
  Wire.requestFrom(tmp117Addr, (uint8_t)2);
  if (Wire.available() < 2) return NAN;
  int16_t raw = ((int16_t)Wire.read() << 8) | Wire.read();
  return raw * TMP117_RES;
}

// ========================================
// SETUP
// ========================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PWM_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);

  Wire.begin();
  delay(500);

  Serial.println(F(""));
  Serial.println(F("========================================"));
  Serial.println(F("  PELTIER PID TEMPERATURE CONTROLLER"));
  Serial.println(F("========================================"));
  Serial.println(F(""));
  Serial.println(F("Scanning for TMP117..."));

  if (!detectTMP117()) {
    Serial.println(F("ERROR: TMP117 not found (0x48/49/4A/4B)"));
    Serial.println(F("Check: SDA, SCL, 3.3V, GND"));
    while (1) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(200);
    }
  }

  Serial.print(F("TMP117 found at 0x"));
  Serial.println(tmp117Addr, HEX);

  setpoint = targetTemp + tempOffset;
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 150);
  myPID.SetSampleTime(sensorInterval);

  Serial.println(F(""));
  Serial.println(F("Configuration:"));
  Serial.print(F("Target:   ")); Serial.print(targetTemp, 2); Serial.println(F(" C"));
  Serial.print(F("Setpoint: ")); Serial.print(setpoint, 2);   Serial.println(F(" C"));
  Serial.print(F("Upper deadband: +")); Serial.print(UPPER_DEADBAND, 2); Serial.println(F(" C"));
  Serial.print(F("Kp/Ki/Kd: "));
  Serial.print(Kp, 1); Serial.print(F(" / "));
  Serial.print(Ki, 1); Serial.print(F(" / "));
  Serial.println(Kd, 1);

  startTime = millis();
}

// ========================================
// MAIN LOOP
// ========================================
void loop() {

  if (millis() - lastSensorRead >= sensorInterval) {
    lastSensorRead = millis();
    float raw = readTMP117();
    if (!isnan(raw)) {
      if (firstRead) {
        filteredTemp = raw;
        firstRead = false;
      } else {
        filteredTemp = ALPHA * raw + (1.0f - ALPHA) * filteredTemp;
      }
      currentTemp = filteredTemp;
    } else {
      Serial.println(F("ERROR: TMP117 read failed!"));
    }
  }

  if (!firstRead) {
    if (currentTemp > MAX_SAFE_TEMP) { emergencyShutdown(F("OVERHEAT"));  return; }
    if (currentTemp < MIN_SAFE_TEMP) { emergencyShutdown(F("UNDERHEAT")); return; }
  }

  if (systemActive && !firstRead) {
    // Upper deadband: when temperature is at/above the target but
    // no more than UPPER_DEADBAND higher, make the PID see the exact
    // setpoint so this small warm-up does not cause a correction.
    // Below target, normal PID control remains active.
    // Above target + deadband, normal PID cooling correction resumes.
    if (currentTemp >= setpoint && currentTemp <= (setpoint + UPPER_DEADBAND)) {
      controlTemp = setpoint;
    } else {
      controlTemp = currentTemp;
    }

    myPID.Compute();
    analogWrite(PWM_PIN, (int)pwmOutput);
    digitalWrite(LED_PIN, HIGH);
  } else if (!systemActive) {
    analogWrite(PWM_PIN, 0);
    digitalWrite(LED_PIN, LOW);
  }

  if (millis() - lastDisplay >= displayInterval) {
    lastDisplay = millis();
    displayStatus();
  }

  if (Serial.available() > 0) {
    handleSerialCommand();
  }
}

// ========================================
// DISPLAY STATUS
// ========================================
void displayStatus() {
  unsigned long elapsed = (millis() - startTime) / 1000;
  int hours   = elapsed / 3600;
  int minutes = (elapsed % 3600) / 60;
  int seconds = elapsed % 60;

  if (hours   < 10) Serial.print('0'); Serial.print(hours);   Serial.print(':');
  if (minutes < 10) Serial.print('0'); Serial.print(minutes); Serial.print(':');
  if (seconds < 10) Serial.print('0'); Serial.print(seconds);

  Serial.print(F(" | Temp: "));    Serial.print(currentTemp, 2);
  Serial.print(F(" C | Tgt: "));   Serial.print(setpoint, 2);
  Serial.print(F(" C | Err: "));   Serial.print(setpoint - currentTemp, 2);
  Serial.print(F(" C | PWM: "));   Serial.print((int)pwmOutput);
  Serial.print(F(" ("));           Serial.print((pwmOutput / 255.0) * 100.0, 1);
  Serial.println(F("%)"));
}

// ========================================
// EMERGENCY SHUTDOWN
// ========================================
// Takes a flash string (__FlashStringHelper) so callers can pass F("...")
void emergencyShutdown(const __FlashStringHelper* reason) {
  systemActive = false;
  analogWrite(PWM_PIN, 0);
  Serial.println(F(""));
  Serial.println(F("!!! EMERGENCY SHUTDOWN !!!"));
  Serial.print(F("Reason: "));      Serial.println(reason);
  Serial.print(F("Temperature: ")); Serial.print(currentTemp, 2); Serial.println(F(" C"));
  while (1) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
}

// ========================================
// SERIAL COMMAND HANDLER
// Fixed char buffer — no heap-allocating String object
// ========================================
void handleSerialCommand() {
  char    buf[32];
  uint8_t len = 0;

  while (Serial.available() && len < sizeof(buf) - 1) {
    char c = Serial.read();
    if (c == '\n') break;
    if (c == '\r') continue;
    buf[len++] = toupper((unsigned char)c);
  }
  buf[len] = '\0';

  if (strncmp(buf, "SET ", 4) == 0) {
    double v = atof(buf + 4);
    if (v > 0 && v < MAX_SAFE_TEMP) {
      targetTemp = v;
      setpoint   = targetTemp + tempOffset;
      Serial.print(F("Target: ")); Serial.print(targetTemp, 2); Serial.println(F(" C"));
    }
  }
  else if (strncmp(buf, "OFFSET ", 7) == 0) {
    tempOffset = atof(buf + 7);
    setpoint   = targetTemp + tempOffset;
    Serial.print(F("Offset: ")); Serial.println(tempOffset, 2);
  }
  else if (strncmp(buf, "KP ", 3) == 0) {
    Kp = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F("Kp: ")); Serial.println(Kp);
  }
  else if (strncmp(buf, "KI ", 3) == 0) {
    Ki = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F("Ki: ")); Serial.println(Ki);
  }
  else if (strncmp(buf, "KD ", 3) == 0) {
    Kd = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F("Kd: ")); Serial.println(Kd);
  }
  else if (strcmp(buf, "STATUS") == 0) { displayDetailedStatus(); }
  else if (strcmp(buf, "STOP")   == 0) {
    systemActive = false; analogWrite(PWM_PIN, 0);
    Serial.println(F("STOPPED"));
  }
  else if (strcmp(buf, "START")  == 0) {
    systemActive = true;
    Serial.println(F("STARTED"));
  }
  else if (strcmp(buf, "HELP")   == 0) { printHelp(); }
}

// ========================================
// DETAILED STATUS
// ========================================
void displayDetailedStatus() {
  Serial.println(F(""));
  Serial.println(F("===== STATUS ====="));
  Serial.print(F("Sensor:  TMP117 @ 0x")); Serial.println(tmp117Addr, HEX);
  Serial.print(F("Temp:    ")); Serial.print(currentTemp, 3); Serial.println(F(" C"));
  Serial.print(F("Target:  ")); Serial.print(targetTemp, 2);  Serial.println(F(" C"));
  Serial.print(F("PWM:     ")); Serial.println((int)pwmOutput);
  Serial.print(F("Kp/Ki/Kd: "));
  Serial.print(Kp); Serial.print(F("/")); Serial.print(Ki); Serial.print(F("/")); Serial.println(Kd);
  Serial.println(F("=================="));
}

// ========================================
// HELP
// ========================================
void printHelp() {
  Serial.println(F(""));
  Serial.println(F("=== COMMANDS ==="));
  Serial.println(F("SET <temp>"));
  Serial.println(F("OFFSET <val>"));
  Serial.println(F("KP/KI/KD <val>"));
  Serial.println(F("STATUS / START / STOP"));
  Serial.println(F("================"));
}
