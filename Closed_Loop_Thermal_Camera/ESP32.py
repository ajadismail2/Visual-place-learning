/*
  ESP32 PyBadge PID Pattern Controller
  -----------------------------------
  Pattern example:
    PATTERN:C-D-A-B-C-D

  Trial: 5 min
  Buffer: 1 min
  Final heat: 60 s
*/

#include <HardwareSerial.h>

HardwareSerial SerialPyBadge(1);

// ================= UART =================
#define RX_PIN 16
#define TX_PIN 17
#define BAUD_RATE 115200

// ================= H-BRIDGE =================
#define IN1 18
#define IN2 4
#define ENA 27

#define IN3 21
#define IN4 23
#define ENB 14

#define IN5 5
#define IN6 19
#define ENC 12

#define IN7 22
#define IN8 25
#define END 13

// ================= PWM =================
#define PWM_FREQ 25000
#define PWM_RES  8
#define PWM_MIN  40
#define PWM_MAX  160

// ================= TEMPERATURE =================
#define TEMP_HEAT 36.0
#define TEMP_COOL 25.0
#define DEADBAND  0.25

// ================= PID =================
#define KP 7.0
#define KI 0.25
#define KD 1.8
#define PID_INTERVAL 500

// ================= TIMING =================
#define TRIAL_TIME   (5UL * 60UL * 1000UL)
#define BUFFER_TIME  (1UL * 60UL * 1000UL)
#define FINAL_TIME   (60UL * 1000UL)

// ================= STATE =================
enum SystemState {
  STATE_IDLE,
  STATE_TRIAL,
  STATE_BUFFER,
  STATE_FINAL,
  STATE_COMPLETE
};

SystemState state = STATE_IDLE;

// ================= STRUCT =================
struct Peltier {
  char label;
  int pinP, pinN, pinE;
  float currentTemp;
  float targetTemp;
  float errorSum;
  float lastError;
  bool heating;
  bool enabled;
  unsigned long lastUpdate;
};

Peltier peltiers[4] = {
  {'A', IN1, IN2, ENA, 0, 0, 0, 0, true, false, 0},
  {'B', IN3, IN4, ENB, 0, 0, 0, 0, true, false, 0},
  {'C', IN5, IN6, ENC, 0, 0, 0, 0, true, false, 0},
  {'D', IN7, IN8, END, 0, 0, 0, 0, true, false, 0}
};

// ================= PATTERN =================
String pattern = "";
int patternIndex = 0;
unsigned long phaseStart = 0;

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  SerialPyBadge.begin(BAUD_RATE, SERIAL_8N1, RX_PIN, TX_PIN);

  int pins[] = {IN1,IN2,IN3,IN4,IN5,IN6,IN7,IN8};
  for (int p : pins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }

  ledcAttach(ENA, PWM_FREQ, PWM_RES);
  ledcAttach(ENB, PWM_FREQ, PWM_RES);
  ledcAttach(ENC, PWM_FREQ, PWM_RES);
  ledcAttach(END, PWM_FREQ, PWM_RES);

  stopAll();

  Serial.println("ESP32 PID Pattern Controller READY");
  Serial.println("Command: PATTERN:C-D-A-B");

  SerialPyBadge.println("REQUEST_CALIB");
}

// ================= LOOP =================
String uartBuf = "";

void loop() {
  // ---- UART TEMP ----
  while (SerialPyBadge.available()) {
    char c = SerialPyBadge.read();
    if (c == '\n') {
      uartBuf.trim();
      if (uartBuf.startsWith("TEMP:"))
        parseTemperatures(uartBuf);
      uartBuf = "";
    } else uartBuf += c;
  }

  // ---- COMMANDS ----
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    processCommand(cmd);
  }

  // ---- PID ----
  for (auto &p : peltiers)
    if (p.enabled)
      updatePID(p);

  // ---- PATTERN FSM ----
  handlePattern();

  delay(20);
}

// ================= PATTERN ENGINE =================
void handlePattern() {
  unsigned long now = millis();

  if (state == STATE_TRIAL && now - phaseStart >= TRIAL_TIME) {
    patternIndex++;
    if (patternIndex >= pattern.length()) {
      startFinal();
    } else {
      startBuffer();
    }
  }

  else if (state == STATE_BUFFER && now - phaseStart >= BUFFER_TIME) {
    startTrial(pattern[patternIndex]);
  }

  else if (state == STATE_FINAL && now - phaseStart >= FINAL_TIME) {
    stopAll();
    state = STATE_COMPLETE;
    Serial.println("EXPERIMENT COMPLETE");
  }
}

// ================= START PHASES =================
void startTrial(char coolLabel) {
  Serial.printf("TRIAL START — Cool %c\n", coolLabel);
  phaseStart = millis();
  state = STATE_TRIAL;

  for (auto &p : peltiers) {
    p.enabled = true;
    p.errorSum = 0;
    p.lastError = 0;
    if (p.label == coolLabel) {
      p.heating = false;
      p.targetTemp = TEMP_COOL;
    } else {
      p.heating = true;
      p.targetTemp = TEMP_HEAT;
    }
  }
}

void startBuffer() {
  Serial.println("BUFFER — All heat");
  phaseStart = millis();
  state = STATE_BUFFER;

  for (auto &p : peltiers) {
    p.enabled = true;
    p.heating = true;
    p.targetTemp = TEMP_HEAT;
    p.errorSum = 0;
    p.lastError = 0;
  }
}

void startFinal() {
  Serial.println("FINAL HEAT — All heat 60s");
  phaseStart = millis();
  state = STATE_FINAL;

  for (auto &p : peltiers) {
    p.enabled = true;
    p.heating = true;
    p.targetTemp = TEMP_HEAT;
    p.errorSum = 0;
    p.lastError = 0;
  }
}

// ================= COMMANDS =================
void processCommand(String cmd) {
  cmd.toUpperCase();

  if (cmd.startsWith("PATTERN:")) {
    pattern = cmd.substring(8);
    pattern.replace("-", "");
    if (pattern.length() == 0 || pattern.length() > 10) {
      Serial.println("INVALID PATTERN");
      return;
    }
    patternIndex = 0;
    startTrial(pattern[0]);
  }

  else if (cmd == "STOP") {
    stopAll();
    state = STATE_IDLE;
    Serial.println("STOPPED");
  }
}

// ================= PID =================
void updatePID(Peltier &p) {
  unsigned long now = millis();
  if (now - p.lastUpdate < PID_INTERVAL) return;
  p.lastUpdate = now;

  float error = p.targetTemp - p.currentTemp;
  if (abs(error) < DEADBAND) {
    stopDrive(p);
    p.errorSum = 0;
    return;
  }

  float dt = PID_INTERVAL / 1000.0;
  p.errorSum += error * dt;
  p.errorSum = constrain(p.errorSum, -20, 20);

  float dErr = (error - p.lastError) / dt;
  p.lastError = error;

  float out = KP * error + KI * p.errorSum + KD * dErr;
  int pwm = constrain(abs((int)out), PWM_MIN, PWM_MAX);

  drive(p, pwm);
}

// ================= DRIVE =================
void drive(Peltier &p, int pwm) {
  digitalWrite(p.pinP, p.heating ? HIGH : LOW);
  digitalWrite(p.pinN, p.heating ? LOW : HIGH);
  ledcWrite(p.pinE, pwm);
}

void stopDrive(Peltier &p) {
  digitalWrite(p.pinP, LOW);
  digitalWrite(p.pinN, LOW);
  ledcWrite(p.pinE, 0);
}

void stopAll() {
  for (auto &p : peltiers) {
    p.enabled = false;
    stopDrive(p);
  }
}

// ================= TEMP PARSER =================
void parseTemperatures(String data) {
  int i = data.indexOf(':') + 1;
  while (i < data.length()) {
    char lbl = data.charAt(i);
    int c1 = data.indexOf(':', i);
    int c2 = data.indexOf(',', c1);
    float t = data.substring(c1 + 1,
               c2 > 0 ? c2 : data.length()).toFloat();

    for (auto &p : peltiers)
      if (p.label == lbl) p.currentTemp = t;

    if (c2 < 0) break;
    i = c2 + 1;
  }
}
