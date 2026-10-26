---
title: Thermal ring
description: "A separate temperature loop adjusts the ring heater through a MOSFET."
section: Software
---
[← Controller programs](index.md)

<div class="download-links" markdown="1">

[Download Thermal_ring.ino](../downloads/firmware/Thermal_ring/Thermal_ring.ino){: download="Thermal_ring.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

## Closed-loop ring heating

OneWire temperature feedback regulates heater PWM through a MOSFET.

| Setting | Value |
| --- | --- |
| Sensor target | 45 °C |
| High-temperature cutoff | 57 °C |
| PID: P / I / D | 18 / 0.3 / 150 |
| Sensor / heater output | Arduino pins 2 / 9 |

The setpoint applies at the sensor. Heating resumes after cooling below the cutoff.

## Commands

Serial: **115200 baud**. Commands: `T` (target), `O` (offset), `P`, `I`, `D` (gains). Example: `T45`.

Compile the [corrected sketch](../downloads/firmware/Thermal_ring_syntax_fixed/Thermal_ring_syntax_fixed.ino), which removes a stray `3` after `float Kd = 150;`.

[Arduino wiring and proposed ESP32 conversion](../hardware/wiring.md#background-ring-and-camera)

## Full source

<details class="source-code">
<summary>Read Thermal_ring.ino · 193 lines</summary>
<pre tabindex="0" aria-label="Thermal_ring.ino source code"><code>  #include &lt;OneWire.h&gt;
  #include &lt;DallasTemperature.h&gt;

  #define ONE_WIRE_BUS 2
  #define MOSFET_PWM_PIN 9

  OneWire oneWire(ONE_WIRE_BUS);
  DallasTemperature sensors(&amp;oneWire);

  const float SAFE_CUTOFF = 57.0;

  float SETPOINT = 45.0;
  float offset   = 0.0;

  float Kp = 18;
  float Ki = 0.3;
  float Kd = 150;3

  float integral  = 0;
  float lastError = 0;

  unsigned long lastTime = 0;

  String inputBuffer = &quot;&quot;;

  void printHelp() {
    Serial.println(&quot;--- Commands ---&quot;);
    Serial.println(&quot;T&lt;value&gt;   Set target  e.g. T45.5&quot;);
    Serial.println(&quot;O&lt;value&gt;   Set offset  e.g. O-2.0&quot;);
    Serial.println(&quot;P&lt;value&gt;   Set Kp      e.g. P40&quot;);
    Serial.println(&quot;I&lt;value&gt;   Set Ki      e.g. I0.8&quot;);
    Serial.println(&quot;D&lt;value&gt;   Set Kd      e.g. D120&quot;);
    Serial.println(&quot;S          Print settings&quot;);
    Serial.println(&quot;----------------&quot;);
  }

  void printSettings() {
    Serial.print(&quot;Setpoint: &quot;); Serial.print(SETPOINT);
    Serial.print(&quot; | Offset: &quot;); Serial.print(offset);
    Serial.print(&quot; | Effective target: &quot;); Serial.println(SETPOINT + offset);

    Serial.print(&quot;Kp: &quot;); Serial.print(Kp);
    Serial.print(&quot; Ki: &quot;); Serial.print(Ki);
    Serial.print(&quot; Kd: &quot;); Serial.println(Kd);
  }

  void handleSerial() {

    while (Serial.available()) {

      char c = (char)Serial.read();

      if (c == &#x27;\n&#x27; || c == &#x27;\r&#x27;) {

        if (inputBuffer.length() == 0) return;

        char cmd = toupper(inputBuffer.charAt(0));
        float val = inputBuffer.substring(1).toFloat();

        switch (cmd) {

          case &#x27;T&#x27;:
            if (val &gt; 0 &amp;&amp; val &lt; SAFE_CUTOFF) {
              SETPOINT = val;
              integral = 0;
              Serial.print(&quot;Setpoint updated: &quot;);
              Serial.println(SETPOINT);
            }
            else {
              Serial.println(&quot;Invalid target temperature&quot;);
            }
            break;

          case &#x27;O&#x27;:
            offset = val;
            Serial.print(&quot;Offset updated: &quot;);
            Serial.println(offset);
            break;

          case &#x27;P&#x27;:
            Kp = val;
            Serial.print(&quot;Kp updated: &quot;);
            Serial.println(Kp);
            break;

          case &#x27;I&#x27;:
            Ki = val;
            integral = 0;
            Serial.print(&quot;Ki updated: &quot;);
            Serial.println(Ki);
            break;

          case &#x27;D&#x27;:
            Kd = val;
            Serial.print(&quot;Kd updated: &quot;);
            Serial.println(Kd);
            break;

          case &#x27;S&#x27;:
            printSettings();
            break;

          case &#x27;H&#x27;:
            printHelp();
            break;

          default:
            Serial.println(&quot;Unknown command. Send H for help.&quot;);
        }

        inputBuffer = &quot;&quot;;
      }
      else {
        inputBuffer += c;
      }
    }
  }

  void setup() {

    Serial.begin(115200);

    pinMode(MOSFET_PWM_PIN, OUTPUT);
    analogWrite(MOSFET_PWM_PIN, 0);

    sensors.begin();

    lastTime = millis();

    Serial.println(&quot;Thermal ring controller starting...&quot;);
    printHelp();

    delay(1000);
  }

  void loop() {

    handleSerial();

    sensors.requestTemperatures();
    delay(750);

    float temp = sensors.getTempCByIndex(0);

    if (isnan(temp) || temp == DEVICE_DISCONNECTED_C) {
      Serial.println(&quot;ERROR: Temperature sensor failure!&quot;);
      analogWrite(MOSFET_PWM_PIN, 0);
      delay(1000);
      return;
    }

    if (temp &gt;= SAFE_CUTOFF) {
      Serial.println(&quot;THERMAL CUTOFF TRIGGERED&quot;);
      analogWrite(MOSFET_PWM_PIN, 0);
      delay(2000);
      return;
    }

    unsigned long now = millis();
    float dt = (now - lastTime) / 1000.0;
    lastTime = now;

    if (dt &lt;= 0 || dt &gt; 5.0) {
      return;
    }

    float target = SETPOINT + offset;
    float error = target - temp;

    integral += error * dt;

    if (Ki &gt; 0) {
      integral = constrain(integral, -200.0 / Ki, 200.0 / Ki);
    }

    float derivative = (error - lastError) / dt;
    lastError = error;

    float output = (Kp * error) + (Ki * integral) + (Kd * derivative);

    int pwmOut = constrain((int)output, 0, 255);

    analogWrite(MOSFET_PWM_PIN, pwmOut);

    Serial.print(&quot;Temp: &quot;);
    Serial.print(temp, 2);
    Serial.print(&quot; °C | Target: &quot;);
    Serial.print(target, 1);
    Serial.print(&quot; °C | Error: &quot;);
    Serial.print(error, 2);
    Serial.print(&quot; | PWM: &quot;);
    Serial.println(pwmOut);
  }</code></pre>
</details>
