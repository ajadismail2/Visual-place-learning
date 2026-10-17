  #include <OneWire.h>
  #include <DallasTemperature.h>

  #define ONE_WIRE_BUS 2
  #define MOSFET_PWM_PIN 9

  OneWire oneWire(ONE_WIRE_BUS);
  DallasTemperature sensors(&oneWire);

  const float SAFE_CUTOFF = 57.0;

  float SETPOINT = 45.0;
  float offset   = 0.0;

  float Kp = 18;
  float Ki = 0.3;
  float Kd = 150;3

  float integral  = 0;
  float lastError = 0;

  unsigned long lastTime = 0;

  String inputBuffer = "";

  void printHelp() {
    Serial.println("--- Commands ---");
    Serial.println("T<value>   Set target  e.g. T45.5");
    Serial.println("O<value>   Set offset  e.g. O-2.0");
    Serial.println("P<value>   Set Kp      e.g. P40");
    Serial.println("I<value>   Set Ki      e.g. I0.8");
    Serial.println("D<value>   Set Kd      e.g. D120");
    Serial.println("S          Print settings");
    Serial.println("----------------");
  }

  void printSettings() {
    Serial.print("Setpoint: "); Serial.print(SETPOINT);
    Serial.print(" | Offset: "); Serial.print(offset);
    Serial.print(" | Effective target: "); Serial.println(SETPOINT + offset);

    Serial.print("Kp: "); Serial.print(Kp);
    Serial.print(" Ki: "); Serial.print(Ki);
    Serial.print(" Kd: "); Serial.println(Kd);
  }

  void handleSerial() {

    while (Serial.available()) {

      char c = (char)Serial.read();

      if (c == '\n' || c == '\r') {

        if (inputBuffer.length() == 0) return;

        char cmd = toupper(inputBuffer.charAt(0));
        float val = inputBuffer.substring(1).toFloat();

        switch (cmd) {

          case 'T':
            if (val > 0 && val < SAFE_CUTOFF) {
              SETPOINT = val;
              integral = 0;
              Serial.print("Setpoint updated: ");
              Serial.println(SETPOINT);
            }
            else {
              Serial.println("Invalid target temperature");
            }
            break;

          case 'O':
            offset = val;
            Serial.print("Offset updated: ");
            Serial.println(offset);
            break;

          case 'P':
            Kp = val;
            Serial.print("Kp updated: ");
            Serial.println(Kp);
            break;

          case 'I':
            Ki = val;
            integral = 0;
            Serial.print("Ki updated: ");
            Serial.println(Ki);
            break;

          case 'D':
            Kd = val;
            Serial.print("Kd updated: ");
            Serial.println(Kd);
            break;

          case 'S':
            printSettings();
            break;

          case 'H':
            printHelp();
            break;

          default:
            Serial.println("Unknown command. Send H for help.");
        }

        inputBuffer = "";
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

    Serial.println("Thermal ring controller starting...");
    printHelp();

    delay(1000);
  }

  void loop() {

    handleSerial();

    sensors.requestTemperatures();
    delay(750);

    float temp = sensors.getTempCByIndex(0);

    if (isnan(temp) || temp == DEVICE_DISCONNECTED_C) {
      Serial.println("ERROR: Temperature sensor failure!");
      analogWrite(MOSFET_PWM_PIN, 0);
      delay(1000);
      return;
    }

    if (temp >= SAFE_CUTOFF) {
      Serial.println("THERMAL CUTOFF TRIGGERED");
      analogWrite(MOSFET_PWM_PIN, 0);
      delay(2000);
      return;
    }

    unsigned long now = millis();
    float dt = (now - lastTime) / 1000.0;
    lastTime = now;

    if (dt <= 0 || dt > 5.0) {
      return;
    }

    float target = SETPOINT + offset;
    float error = target - temp;

    integral += error * dt;

    if (Ki > 0) {
      integral = constrain(integral, -200.0 / Ki, 200.0 / Ki);
    }

    float derivative = (error - lastError) / dt;
    lastError = error;

    float output = (Kp * error) + (Ki * integral) + (Kd * derivative);

    int pwmOut = constrain((int)output, 0, 255);

    analogWrite(MOSFET_PWM_PIN, pwmOut);

    Serial.print("Temp: ");
    Serial.print(temp, 2);
    Serial.print(" °C | Target: ");
    Serial.print(target, 1);
    Serial.print(" °C | Error: ");
    Serial.print(error, 2);
    Serial.print(" | PWM: ");
    Serial.println(pwmOut);
  }