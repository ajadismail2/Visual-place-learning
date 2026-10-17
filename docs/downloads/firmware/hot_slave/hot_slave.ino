// ============================================================
//  4 Peltier Experiment Controller — HOT SLAVE
//  Drives LPWM pins (heat direction) for all 4 plates.
//  Receives commands from Cool Master via Serial2
//  (RX=GPIO16 ← Master TX=GPIO17, shared GND).
//
//  Protocol (newline-terminated ASCII):
//    H<idx>:<pwm>  →  heat plate idx at pwm   (e.g. H0:47)
//    S<idx>        →  stop plate idx           (e.g. S2)
//    SA            →  stop all plates
// ============================================================

// -------- HOT (LPWM) PINS --------
#define LPWM1 32
#define LPWM2 25
#define LPWM3 27
#define LPWM4 18

#define MASTER_RX  16   // Serial2 RX ← Master TX (GPIO17)

#define PWM_FREQ 20000
#define PWM_RES  8

int LPWM_PIN[4] = {LPWM1, LPWM2, LPWM3, LPWM4};

// ============================================================
//  SETUP
// ============================================================

void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, MASTER_RX, -1);  // RX only

  for (int i = 0; i < 4; i++) {
    ledcAttach(LPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcWrite(LPWM_PIN[i], 0);
  }

  Serial.println(F("\n=== 4 Peltier Controller — HOT SLAVE ==="));
  Serial.println(F("Listening on Serial2 RX=GPIO16 <- Master TX=GPIO17"));
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
  if (!Serial2.available()) return;

  String cmd = Serial2.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  // SA → stop all
  if (cmd.equalsIgnoreCase("SA")) {
    for (int i = 0; i < 4; i++) ledcWrite(LPWM_PIN[i], 0);
    Serial.println(F("[SLAVE] Stop all"));
    return;
  }

  // S<idx> → stop one plate
  if (cmd.charAt(0) == 'S' && cmd.length() == 2) {
    int idx = cmd.charAt(1) - '0';
    if (idx >= 0 && idx <= 3) {
      ledcWrite(LPWM_PIN[idx], 0);
      Serial.print(F("[SLAVE] Stop P")); Serial.println(idx + 1);
    }
    return;
  }

  // H<idx>:<pwm> → heat one plate
  if (cmd.charAt(0) == 'H' && cmd.length() >= 4 && cmd.charAt(2) == ':') {
    int idx = cmd.charAt(1) - '0';
    int pwm = constrain(cmd.substring(3).toInt(), 0, 255);
    if (idx >= 0 && idx <= 3) {
      ledcWrite(LPWM_PIN[idx], pwm);
      Serial.print(F("[SLAVE] Heat P")); Serial.print(idx + 1);
      Serial.print(F(" PWM=")); Serial.println(pwm);
    }
    return;
  }

  Serial.print(F("[SLAVE] Unknown cmd: ")); Serial.println(cmd);
}
