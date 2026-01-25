/*
  ESP32 Peltier Test Controller
  -----------------------------
  ESP32 Core 3.x compatible
  FIXED PWM handling (NO analogWrite, NO ledcSetup)

  Serial @115200:
    HEAT A/B/C/D
    COOL A/B/C/D
    HEAT ALL
    COOL ALL
    STOP A/B/C/D
    STOP
    STATUS
*/

// ================= PIN DEFINITIONS =================
// H-Bridge 1 (A & B)
#define IN1 18   // A+
#define IN2 4    // A-
#define ENA 27   // PWM A

#define IN3 21   // B+
#define IN4 23   // B-
#define ENB 14   // PWM B

// H-Bridge 2 (C & D)
#define IN5 5    // C+
#define IN6 19   // C-
#define ENC 12   // PWM C

#define IN7 22   // D+
#define IN8 25   // D-
#define END 13   // PWM D

// ================= PWM SETTINGS =================
#define PWM_FREQ   25000
#define PWM_RES    8
#define FIXED_PWM  100

// ================= PELTIER STRUCT =================
struct Peltier {
  char label;
  int pinPlus;
  int pinMinus;
  int pinEnable;
  int currentPWM;
  bool isHeating;
  bool isActive;
};

// ================= PELTIER OBJECTS =================
Peltier peltiers[4] = {
  {'A', IN1, IN2, ENA, 0, false, false},
  {'B', IN3, IN4, ENB, 0, false, false},
  {'C', IN5, IN6, ENC, 0, false, false},
  {'D', IN7, IN8, END, 0, false, false}
};

// ================= FUNCTION DECLARATIONS =================
void setupPins();
void setPeltierPower(Peltier &p, bool heating);
void stopPeltier(Peltier &p);
void stopAll();
void printStatus();
void processCommand(String cmd);
Peltier* findPeltier(char label);

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(1000);

  setupPins();
  stopAll();

  Serial.println();
  Serial.println("==============================================");
  Serial.println("ESP32 PELTIER TEST CONTROLLER (CORE 3.x)");
  Serial.println("==============================================");
  Serial.println("Commands:");
  Serial.println("  HEAT A/B/C/D");
  Serial.println("  COOL A/B/C/D");
  Serial.println("  HEAT ALL");
  Serial.println("  COOL ALL");
  Serial.println("  STOP [A/B/C/D]");
  Serial.println("  STATUS");
  Serial.println("----------------------------------------------");
  Serial.printf("PWM: %d @ %d Hz\n", FIXED_PWM, PWM_FREQ);
  Serial.println("==============================================");
  Serial.println("Ready.");
}

// ================= LOOP =================
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length()) {
      Serial.printf("[CMD] %s\n", cmd.c_str());
      processCommand(cmd);
    }
  }
  delay(50);
}

// ================= GPIO + PWM SETUP =================
void setupPins() {
  int logicPins[] = {IN1, IN2, IN3, IN4, IN5, IN6, IN7, IN8};
  for (int i = 0; i < 8; i++) {
    pinMode(logicPins[i], OUTPUT);
    digitalWrite(logicPins[i], LOW);
  }

  // ESP32 Core 3.x PWM attach
  ledcAttach(ENA, PWM_FREQ, PWM_RES);
  ledcAttach(ENB, PWM_FREQ, PWM_RES);
  ledcAttach(ENC, PWM_FREQ, PWM_RES);
  ledcAttach(END, PWM_FREQ, PWM_RES);

  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
  ledcWrite(ENC, 0);
  ledcWrite(END, 0);
}

// ================= FIND PELTIER =================
Peltier* findPeltier(char label) {
  label = toupper(label);
  for (int i = 0; i < 4; i++) {
    if (peltiers[i].label == label) return &peltiers[i];
  }
  return nullptr;
}

// ================= COMMAND PROCESSOR =================
void processCommand(String cmd) {
  cmd.toUpperCase();
  cmd.trim();

  int space = cmd.indexOf(' ');
  String action = (space > 0) ? cmd.substring(0, space) : cmd;
  String target = (space > 0) ? cmd.substring(space + 1) : "";
  target.trim();

  if (action == "HEAT" || action == "COOL") {
    bool heating = (action == "HEAT");

    if (target == "ALL") {
      for (int i = 0; i < 4; i++) {
        setPeltierPower(peltiers[i], heating);
        peltiers[i].isActive = true;
      }
    } else if (target.length() == 1) {
      Peltier* p = findPeltier(target[0]);
      if (p) {
        setPeltierPower(*p, heating);
        p->isActive = true;
      }
    }
  }

  else if (action == "STOP") {
    if (target == "" || target == "ALL") {
      stopAll();
    } else if (target.length() == 1) {
      Peltier* p = findPeltier(target[0]);
      if (p) stopPeltier(*p);
    }
  }

  else if (action == "STATUS") {
    printStatus();
  }
}

// ================= SET POWER =================
void setPeltierPower(Peltier &p, bool heating) {
  // Stop first (dead-time)
  digitalWrite(p.pinPlus, LOW);
  digitalWrite(p.pinMinus, LOW);
  ledcWrite(p.pinEnable, 0);
  delay(100);

  p.isHeating = heating;
  p.currentPWM = FIXED_PWM;

  digitalWrite(p.pinPlus, heating ? HIGH : LOW);
  digitalWrite(p.pinMinus, heating ? LOW : HIGH);
  ledcWrite(p.pinEnable, FIXED_PWM);

  Serial.printf("Peltier %c -> %s @ PWM %d\n",
                p.label,
                heating ? "HEAT" : "COOL",
                FIXED_PWM);
}

// ================= STOP =================
void stopPeltier(Peltier &p) {
  digitalWrite(p.pinPlus, LOW);
  digitalWrite(p.pinMinus, LOW);
  ledcWrite(p.pinEnable, 0);

  p.currentPWM = 0;
  p.isActive = false;

  Serial.printf("Peltier %c STOPPED\n", p.label);
}

void stopAll() {
  for (int i = 0; i < 4; i++) stopPeltier(peltiers[i]);
}

// ================= STATUS =================
void printStatus() {
  Serial.println("\n----------- STATUS -----------");
  for (int i = 0; i < 4; i++) {
    Serial.printf("Peltier %c: %s\n",
      peltiers[i].label,
      peltiers[i].isActive
        ? (peltiers[i].isHeating ? "HEATING" : "COOLING")
        : "STOPPED");
  }
  Serial.println("------------------------------\n");
}
