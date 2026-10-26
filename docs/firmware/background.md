---
title: 60-module background
description: "A separate TMP117 feedback loop adjusts one PWM output for the background circuit."
section: Software
---
[← Controller programs](index.md)

<div class="download-links" markdown="1">

[Download Closedloop_60peltier.ino](../downloads/firmware/Closedloop_60peltier/Closedloop_60peltier.ino){: download="Closedloop_60peltier.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

## Temperature feedback

PID control uses filtered TMP117 readings to regulate the 60-module background through one PWM output.

| Setting | Value |
| --- | --- |
| Sensor setpoint | 34.8 °C |
| Reading interval | 100 ms |
| PWM limit | 150/255 |
| PID: P / I / D | 60 / 4 / 5 |
| Output in this sketch | Arduino pin 9 |

The sensor measures its local temperature; floor uniformity requires separate measurements.

## Commands

Serial: **115200 baud**. Commands: `SET` (temperature), `KP`, `KI`, `KD` (gains), `STATUS`, `START`, `STOP`.

Failed reads retain the previous value. There is no stale-data shutdown.

[Arduino wiring and proposed ESP32 conversion](../hardware/wiring.md#background-ring-and-camera)

## Full source

<details class="source-code">
<summary>Read Closedloop_60peltier.ino · 316 lines</summary>
<pre tabindex="0" aria-label="Closedloop_60peltier.ino source code"><code>#include &lt;PID_v1.h&gt;
#include &lt;Wire.h&gt;

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
PID myPID(&amp;controlTemp, &amp;pwmOutput, &amp;setpoint, Kp, Ki, Kd, DIRECT);

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
  for (uint8_t i = 0; i &lt; 4; i++) {
    uint8_t addr = candidates[i];
    Wire.beginTransmission(addr);
    Wire.write(TMP117_REG_TEMP);
    if (Wire.endTransmission() != 0) continue;
    Wire.requestFrom(addr, (uint8_t)2);
    if (Wire.available() &lt; 2) continue;
    int16_t raw = ((int16_t)Wire.read() &lt;&lt; 8) | Wire.read();
    float t = raw * TMP117_RES;
    if (t &gt; -10.0f &amp;&amp; t &lt; 100.0f) {
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
  if (Wire.available() &lt; 2) return NAN;
  int16_t raw = ((int16_t)Wire.read() &lt;&lt; 8) | Wire.read();
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

  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;========================================&quot;));
  Serial.println(F(&quot;  PELTIER PID TEMPERATURE CONTROLLER&quot;));
  Serial.println(F(&quot;========================================&quot;));
  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;Scanning for TMP117...&quot;));

  if (!detectTMP117()) {
    Serial.println(F(&quot;ERROR: TMP117 not found (0x48/49/4A/4B)&quot;));
    Serial.println(F(&quot;Check: SDA, SCL, 3.3V, GND&quot;));
    while (1) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(200);
    }
  }

  Serial.print(F(&quot;TMP117 found at 0x&quot;));
  Serial.println(tmp117Addr, HEX);

  setpoint = targetTemp + tempOffset;
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 150);
  myPID.SetSampleTime(sensorInterval);

  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;Configuration:&quot;));
  Serial.print(F(&quot;Target:   &quot;)); Serial.print(targetTemp, 2); Serial.println(F(&quot; C&quot;));
  Serial.print(F(&quot;Setpoint: &quot;)); Serial.print(setpoint, 2);   Serial.println(F(&quot; C&quot;));
  Serial.print(F(&quot;Upper deadband: +&quot;)); Serial.print(UPPER_DEADBAND, 2); Serial.println(F(&quot; C&quot;));
  Serial.print(F(&quot;Kp/Ki/Kd: &quot;));
  Serial.print(Kp, 1); Serial.print(F(&quot; / &quot;));
  Serial.print(Ki, 1); Serial.print(F(&quot; / &quot;));
  Serial.println(Kd, 1);

  startTime = millis();
}

// ========================================
// MAIN LOOP
// ========================================
void loop() {

  if (millis() - lastSensorRead &gt;= sensorInterval) {
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
      Serial.println(F(&quot;ERROR: TMP117 read failed!&quot;));
    }
  }

  if (!firstRead) {
    if (currentTemp &gt; MAX_SAFE_TEMP) { emergencyShutdown(F(&quot;OVERHEAT&quot;));  return; }
    if (currentTemp &lt; MIN_SAFE_TEMP) { emergencyShutdown(F(&quot;UNDERHEAT&quot;)); return; }
  }

  if (systemActive &amp;&amp; !firstRead) {
    // Upper deadband: when temperature is at/above the target but
    // no more than UPPER_DEADBAND higher, make the PID see the exact
    // setpoint so this small warm-up does not cause a correction.
    // Below target, normal PID control remains active.
    // Above target + deadband, normal PID cooling correction resumes.
    if (currentTemp &gt;= setpoint &amp;&amp; currentTemp &lt;= (setpoint + UPPER_DEADBAND)) {
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

  if (millis() - lastDisplay &gt;= displayInterval) {
    lastDisplay = millis();
    displayStatus();
  }

  if (Serial.available() &gt; 0) {
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

  if (hours   &lt; 10) Serial.print(&#x27;0&#x27;); Serial.print(hours);   Serial.print(&#x27;:&#x27;);
  if (minutes &lt; 10) Serial.print(&#x27;0&#x27;); Serial.print(minutes); Serial.print(&#x27;:&#x27;);
  if (seconds &lt; 10) Serial.print(&#x27;0&#x27;); Serial.print(seconds);

  Serial.print(F(&quot; | Temp: &quot;));    Serial.print(currentTemp, 2);
  Serial.print(F(&quot; C | Tgt: &quot;));   Serial.print(setpoint, 2);
  Serial.print(F(&quot; C | Err: &quot;));   Serial.print(setpoint - currentTemp, 2);
  Serial.print(F(&quot; C | PWM: &quot;));   Serial.print((int)pwmOutput);
  Serial.print(F(&quot; (&quot;));           Serial.print((pwmOutput / 255.0) * 100.0, 1);
  Serial.println(F(&quot;%)&quot;));
}

// ========================================
// EMERGENCY SHUTDOWN
// ========================================
// Takes a flash string (__FlashStringHelper) so callers can pass F(&quot;...&quot;)
void emergencyShutdown(const __FlashStringHelper* reason) {
  systemActive = false;
  analogWrite(PWM_PIN, 0);
  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;!!! EMERGENCY SHUTDOWN !!!&quot;));
  Serial.print(F(&quot;Reason: &quot;));      Serial.println(reason);
  Serial.print(F(&quot;Temperature: &quot;)); Serial.print(currentTemp, 2); Serial.println(F(&quot; C&quot;));
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

  while (Serial.available() &amp;&amp; len &lt; sizeof(buf) - 1) {
    char c = Serial.read();
    if (c == &#x27;\n&#x27;) break;
    if (c == &#x27;\r&#x27;) continue;
    buf[len++] = toupper((unsigned char)c);
  }
  buf[len] = &#x27;\0&#x27;;

  if (strncmp(buf, &quot;SET &quot;, 4) == 0) {
    double v = atof(buf + 4);
    if (v &gt; 0 &amp;&amp; v &lt; MAX_SAFE_TEMP) {
      targetTemp = v;
      setpoint   = targetTemp + tempOffset;
      Serial.print(F(&quot;Target: &quot;)); Serial.print(targetTemp, 2); Serial.println(F(&quot; C&quot;));
    }
  }
  else if (strncmp(buf, &quot;OFFSET &quot;, 7) == 0) {
    tempOffset = atof(buf + 7);
    setpoint   = targetTemp + tempOffset;
    Serial.print(F(&quot;Offset: &quot;)); Serial.println(tempOffset, 2);
  }
  else if (strncmp(buf, &quot;KP &quot;, 3) == 0) {
    Kp = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F(&quot;Kp: &quot;)); Serial.println(Kp);
  }
  else if (strncmp(buf, &quot;KI &quot;, 3) == 0) {
    Ki = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F(&quot;Ki: &quot;)); Serial.println(Ki);
  }
  else if (strncmp(buf, &quot;KD &quot;, 3) == 0) {
    Kd = atof(buf + 3); myPID.SetTunings(Kp, Ki, Kd);
    Serial.print(F(&quot;Kd: &quot;)); Serial.println(Kd);
  }
  else if (strcmp(buf, &quot;STATUS&quot;) == 0) { displayDetailedStatus(); }
  else if (strcmp(buf, &quot;STOP&quot;)   == 0) {
    systemActive = false; analogWrite(PWM_PIN, 0);
    Serial.println(F(&quot;STOPPED&quot;));
  }
  else if (strcmp(buf, &quot;START&quot;)  == 0) {
    systemActive = true;
    Serial.println(F(&quot;STARTED&quot;));
  }
  else if (strcmp(buf, &quot;HELP&quot;)   == 0) { printHelp(); }
}

// ========================================
// DETAILED STATUS
// ========================================
void displayDetailedStatus() {
  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;===== STATUS =====&quot;));
  Serial.print(F(&quot;Sensor:  TMP117 @ 0x&quot;)); Serial.println(tmp117Addr, HEX);
  Serial.print(F(&quot;Temp:    &quot;)); Serial.print(currentTemp, 3); Serial.println(F(&quot; C&quot;));
  Serial.print(F(&quot;Target:  &quot;)); Serial.print(targetTemp, 2);  Serial.println(F(&quot; C&quot;));
  Serial.print(F(&quot;PWM:     &quot;)); Serial.println((int)pwmOutput);
  Serial.print(F(&quot;Kp/Ki/Kd: &quot;));
  Serial.print(Kp); Serial.print(F(&quot;/&quot;)); Serial.print(Ki); Serial.print(F(&quot;/&quot;)); Serial.println(Kd);
  Serial.println(F(&quot;==================&quot;));
}

// ========================================
// HELP
// ========================================
void printHelp() {
  Serial.println(F(&quot;&quot;));
  Serial.println(F(&quot;=== COMMANDS ===&quot;));
  Serial.println(F(&quot;SET &lt;temp&gt;&quot;));
  Serial.println(F(&quot;OFFSET &lt;val&gt;&quot;));
  Serial.println(F(&quot;KP/KI/KD &lt;val&gt;&quot;));
  Serial.println(F(&quot;STATUS / START / STOP&quot;));
  Serial.println(F(&quot;================&quot;));
}
</code></pre>
</details>
