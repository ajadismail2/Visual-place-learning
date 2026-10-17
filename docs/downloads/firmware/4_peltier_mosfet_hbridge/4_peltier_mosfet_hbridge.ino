// ============================================================
//  4 Peltier Experiment Controller
//  Nodes: A=ch3(idx0)  B=ch2(idx1)  C=ch4(idx2)  D=ch1(idx3)  (verified by hand)
//
//  Serial commands:
//    HOT ALL              → heat all 4 plates at PWM 40
//    EXP A-D-A-D-A-C-D-C → pre-heat (PWM 40, 3 min) then run pattern
//      Each EXP step: 85 PWM 10 s → 75 PWM 5 s → 65 PWM 5 s → 55 PWM remainder
//      Optional PWM overrides (space-separated after the pattern):
//        COOL:NNN          boost cool PWM (default 85)
//        MID:NNN           second cool PWM (default 75)
//        HOLD:NNN          third cool PWM (default 65)
//        FINAL:NNN         final cool PWM (default 55)
//        HA:NNN HB:NNN HC:NNN HD:NNN  per-plate hot PWM (default 47 each)
//      Example: EXP A-D-C-D COOL:85 MID:75 HOLD:65 FINAL:55 HA:47 HB:47 HC:47 HD:47
//    STOP                 → stop all plates
//    1 COOL FAST          → plate 1: PWM 80 (5s) → 70 (10s) → 60 (4m) → 55 (45s)
//    1 f150 / 2 r200 / 3 s → manual per-Peltier control
// ============================================================

// -------- PIN DEFINITIONS --------
#define RPWM1 32
#define LPWM1 33
#define REN1   4
#define LEN1   5

#define RPWM2 25
#define LPWM2 26
#define REN2  13
#define LEN2  15

#define RPWM3 27
#define LPWM3 14
#define REN3  22
#define LEN3  23

#define RPWM4 19
#define LPWM4 18
#define REN4  2
#define LEN4  16

#define PWM_FREQ 20000
#define PWM_RES  8

// Arrays indexed by chamber (A=0,B=1,C=2,D=3); values are the channel
// verified by hand (1 r/f=D, 2 r/f=B, 3 r/f=A, 4 r/f=C) to actually drive
// that chamber, so EXP letters and manual "N f/r" commands stay in sync.
int RPWM_PIN[4] = {RPWM3, RPWM2, RPWM4, RPWM1};
int LPWM_PIN[4] = {LPWM3, LPWM2, LPWM4, LPWM1};
int REN_PIN[4]  = {REN3,  REN2,  REN4,  REN1};
int LEN_PIN[4]  = {LEN3,  LEN2,  LEN4,  LEN1};

// -------- EXPERIMENT CONSTANTS --------
#define HOT_PWM             39
#define PRE_HOT_PWM         39
#define FAST_COOL_PHASE1_PWM 85
#define FAST_COOL_PHASE2_PWM 75
#define FAST_COOL_PHASE3_PWM 65
#define FAST_COOL_PHASE4_PWM 55

#define EXP_COOL_BOOST_MS   (10UL * 1000UL)
#define EXP_COOL_MID_MS     (5UL * 1000UL)    // phase 2: 75 PWM for 5 s
#define EXP_COOL_HOLD_MS    (5UL * 1000UL)    // phase 3: 65 PWM for 5 s

#define FAST_COOL_PHASE1_MS (10UL * 1000UL)                  // 10 s
#define FAST_COOL_PHASE2_MS (10UL  * 1000UL)                 // 5 s
#define FAST_COOL_PHASE3_MS (10UL * 1000UL)                 // 10 s
#define FAST_COOL_PHASE4_MS (4UL * 60UL * 1000UL + 30UL * 1000UL) // 4 m 35 s
#define FAST_COOL_TOTAL_MS  (FAST_COOL_PHASE1_MS + FAST_COOL_PHASE2_MS + FAST_COOL_PHASE3_MS + FAST_COOL_PHASE4_MS)
#define STEP_DURATION_MS    (5UL  * 60UL * 1000UL)
#define PRE_HOT_DURATION_MS (3UL * 60UL * 1000UL)
#define STATUS_INTERVAL     (60UL * 1000UL)
#define MAX_STEPS           12

// -------- STATE --------
enum Mode { IDLE, HOT_ALL, PRE_HOT, EXPERIMENT, FAST_COOL };
Mode mode = IDLE;

char expPattern[MAX_STEPS];
int  patternLen        = 0;
int  currentStep       = 0;
int  expCoolPhase      = 1;   // 1=boost, 2=75 PWM, 3=65 PWM, 4=55 PWM

unsigned long stepStartMs   = 0;
unsigned long lastStatusMs  = 0;
unsigned long preHotStartMs = 0;

int           fastCoolPlate = -1;
unsigned long fastCoolStartMs = 0;
int           fastCoolPhase  = 1;

// Per-experiment PWM values (set when EXP is parsed; default to constants)
int expCoolPWM     = FAST_COOL_PHASE1_PWM;
int expCoolMidPWM  = FAST_COOL_PHASE2_PWM;
int expCoolHoldPWM = FAST_COOL_PHASE3_PWM;
int expCoolFinalPWM = 55;
int expHotPWM[4]   = {HOT_PWM, HOT_PWM, HOT_PWM, HOT_PWM};

// -------- OUTPUT STATE --------
// Keep an explicit desired state for every Peltier. This prevents a
// single manual/EXP command from depending on whatever PWM happened to
// be left on another channel.
enum PlateState { PLATE_STOPPED, PLATE_HEATING, PLATE_COOLING };
PlateState plateState[4] = {
  PLATE_STOPPED, PLATE_STOPPED, PLATE_STOPPED, PLATE_STOPPED
};
int platePWM[4] = {0, 0, 0, 0};

// ============================================================
//  HELPERS
// ============================================================

int nodeToIndex(char c) {
  switch (c) {
    case 'A': return 0;
    case 'B': return 1;
    case 'C': return 2;
    case 'D': return 3;
    default:  return -1;
  }
}

void writePlateOutput(int idx) {
  if (idx < 0 || idx > 3) return;

  switch (plateState[idx]) {
    case PLATE_HEATING:
      ledcWrite(LPWM_PIN[idx], 0);
      ledcWrite(RPWM_PIN[idx], constrain(platePWM[idx], 0, 255));
      break;

    case PLATE_COOLING:
      ledcWrite(RPWM_PIN[idx], 0);
      ledcWrite(LPWM_PIN[idx], constrain(platePWM[idx], 0, 255));
      break;

    default:
      ledcWrite(RPWM_PIN[idx], 0);
      ledcWrite(LPWM_PIN[idx], 0);
      break;
  }
}

void heatPlate(int idx, int pwm) {
  if (idx < 0 || idx > 3) return;
  plateState[idx] = PLATE_HEATING;
  platePWM[idx] = constrain(pwm, 0, 255);
  writePlateOutput(idx);
}

void coolPlate(int idx, int pwm) {
  if (idx < 0 || idx > 3) return;
  plateState[idx] = PLATE_COOLING;
  platePWM[idx] = constrain(pwm, 0, 255);
  writePlateOutput(idx);
}

void stopPlate(int idx) {
  if (idx < 0 || idx > 3) return;
  plateState[idx] = PLATE_STOPPED;
  platePWM[idx] = 0;
  writePlateOutput(idx);
}

void stopAll() {
  for (int i = 0; i < 4; i++) stopPlate(i);
}

void refreshAllPlateOutputs() {
  // Re-assert all four requested outputs. This is intentionally per-plate
  // and never derives one plate's state from another plate.
  for (int i = 0; i < 4; i++) writePlateOutput(i);
}

void applyStep(int coolIdx) {
  if (coolIdx < 0 || coolIdx > 3) return;

  // Explicitly set the requested state of every Peltier.
  // There is NO global stop here.
  for (int i = 0; i < 4; i++) {
    if (i == coolIdx) {
      coolPlate(i, expCoolPWM);
    } else {
      heatPlate(i, expHotPWM[i]);
    }
  }

  Serial.print(F("[EXP] COOL="));
  Serial.print("ABCD"[coolIdx]);
  Serial.print(F(" boost="));
  Serial.print(expCoolPWM);
  Serial.print(F(" mid="));
  Serial.print(expCoolMidPWM);
  Serial.print(F(" hold="));
  Serial.print(expCoolHoldPWM);
  Serial.print(F("  HOT: "));

  for (int i = 0; i < 4; i++) {
    if (i != coolIdx) {
      Serial.print("ABCD"[i]);
      Serial.print(F("="));
      Serial.print(expHotPWM[i]);
      Serial.print(F(" "));
    }
  }
  Serial.println();
}

void printStepStatus(int coolIdx, unsigned long elapsedMs) {
  unsigned long remainSec = (STEP_DURATION_MS - min(elapsedMs, STEP_DURATION_MS)) / 1000UL;
  Serial.print(F("[EXP] Step "));
  Serial.print(currentStep + 1);
  Serial.print(F("/"));
  Serial.print(patternLen);
  Serial.print(F("  Cooling="));
  Serial.print("ABCD"[coolIdx]);
  Serial.print(F("  Remaining: "));
  Serial.print(remainSec / 60); Serial.print(F("m "));
  Serial.print(remainSec % 60); Serial.println(F("s"));
}

// ============================================================
//  SETUP
// ============================================================

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 4; i++) {
    pinMode(REN_PIN[i], OUTPUT);
    pinMode(LEN_PIN[i], OUTPUT);
    digitalWrite(REN_PIN[i], HIGH);
    digitalWrite(LEN_PIN[i], HIGH);

    ledcAttach(RPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcAttach(LPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcWrite(RPWM_PIN[i], 0);
    ledcWrite(LPWM_PIN[i], 0);
  }

  Serial.println(F("\n=== 4 Peltier Experiment Controller ==="));
  Serial.println(F("Node map: A=ch3  B=ch2  C=ch4  D=ch1  (verified by hand)"));
  Serial.println(F("EN pins driven by ESP32 (not 3V3 rail)"));
  Serial.println();
  Serial.println(F("Commands:"));
  Serial.println(F("  HOT ALL                           -> heat all 4 plates"));
  Serial.println(F("  EXP A-D-C-D                                      -> pre-heat 3min, then run"));
  Serial.println(F("    defaults: COOL=85 MID=75 HOLD=65 FINAL=55 HA/B/C/D=47; 10s -> 5s -> 5s -> rest"));
  Serial.println(F("  EXP A-D-C-D COOL:85 MID:75 HOLD:65 FINAL:55 HA:47 HB:47 HC:47 HD:47  -> with overrides"));
  Serial.println(F("  STOP                              -> stop all plates"));
  Serial.println(F("  1 COOL FAST                       -> PWM 80 (10s), 70 (5s), 60 (10s), 55 (4m 35s)"));
  Serial.println(F("  1 f150 / 2 r200 / 3 s             -> manual per-Peltier"));
}

// ============================================================
//  LOOP
// ============================================================

void loop() {

  // Keep all four requested outputs explicitly asserted. A command that
  // changes one Peltier therefore cannot cancel the other three.
  refreshAllPlateOutputs();

  // ── PRE_HOT ──────────────────────────────────────────────
  if (mode == PRE_HOT) {
    unsigned long now     = millis();
    unsigned long elapsed = now - preHotStartMs;

    if (elapsed >= PRE_HOT_DURATION_MS) {
      currentStep       = 0;
      stepStartMs       = now;
      lastStatusMs      = now;
      expCoolPhase      = 1;
      mode              = EXPERIMENT;

      applyStep(nodeToIndex(expPattern[0]));
      Serial.print(F("[PRE_HOT] Done. Starting EXP Step 1/"));
      Serial.println(patternLen);
    } else if (now - lastStatusMs >= STATUS_INTERVAL) {
      lastStatusMs = now;
      unsigned long remainSec = (PRE_HOT_DURATION_MS - elapsed) / 1000UL;
      Serial.print(F("[PRE_HOT] Remaining: "));
      Serial.print(remainSec / 60); Serial.print(F("m "));
      Serial.print(remainSec % 60); Serial.println(F("s"));
    }
  }

  // ── EXPERIMENT ───────────────────────────────────────────
  if (mode == EXPERIMENT) {
    unsigned long now     = millis();
    unsigned long elapsed = now - stepStartMs;
    int coolIdx = nodeToIndex(expPattern[currentStep]);

    if (expCoolPhase == 1 && elapsed >= EXP_COOL_BOOST_MS) {
      expCoolPhase = 2;
      // Change only the cooling plate's PWM. Leave the other three
      // heating outputs untouched and active.
      coolPlate(coolIdx, expCoolMidPWM);
      Serial.print(F("[EXP] Node "));
      Serial.print("ABCD"[coolIdx]);
      Serial.print(F(" boost->mid  PWM "));
      Serial.print(expCoolPWM);
      Serial.print(F(" -> "));
      Serial.println(expCoolMidPWM);
    }

    if (expCoolPhase == 2 && elapsed >= (EXP_COOL_BOOST_MS + EXP_COOL_MID_MS)) {
      expCoolPhase = 3;
      // Change only the cooling plate's PWM. Leave the other three
      // heating outputs untouched and active.
      coolPlate(coolIdx, expCoolHoldPWM);
      Serial.print(F("[EXP] Node "));
      Serial.print("ABCD"[coolIdx]);
      Serial.print(F(" mid->hold  PWM "));
      Serial.print(expCoolMidPWM);
      Serial.print(F(" -> "));
      Serial.println(expCoolHoldPWM);
    }

    if (expCoolPhase == 3 && elapsed >= (EXP_COOL_BOOST_MS + EXP_COOL_MID_MS + EXP_COOL_HOLD_MS)) {
      expCoolPhase = 4;
      // Change only the cooling plate's PWM. Leave the other three
      // heating outputs untouched and active.
      coolPlate(coolIdx, expCoolFinalPWM);
      Serial.print(F("[EXP] Node "));
      Serial.print("ABCD"[coolIdx]);
      Serial.print(F(" 65->final  PWM "));
      Serial.print(expCoolHoldPWM);
      Serial.print(F(" -> "));
      Serial.println(expCoolFinalPWM);
    }

    if (elapsed >= STEP_DURATION_MS) {
      currentStep++;
      if (currentStep >= patternLen) {
        stopAll();
        mode = IDLE;
        Serial.println(F("[EXP] All steps complete. Plates stopped."));
      } else {
        stepStartMs       = now;
        lastStatusMs      = now;
        expCoolPhase      = 1;
        applyStep(nodeToIndex(expPattern[currentStep]));
        Serial.print(F("[EXP] Step "));
        Serial.print(currentStep + 1);
        Serial.print(F("/")); Serial.println(patternLen);
      }
    } else if (now - lastStatusMs >= STATUS_INTERVAL) {
      lastStatusMs = now;
      printStepStatus(coolIdx, elapsed);
    }
  }

  // ── FAST_COOL ────────────────────────────────────────────
  if (mode == FAST_COOL) {
    unsigned long now     = millis();
    unsigned long elapsed = now - fastCoolStartMs;

    // Phase 1: PWM 80 for 10 seconds
    if (fastCoolPhase == 1 && elapsed >= FAST_COOL_PHASE1_MS) {
      fastCoolPhase = 2;
      coolPlate(fastCoolPlate, FAST_COOL_PHASE2_PWM);
      Serial.print(F("[FAST_COOL] P"));
      Serial.print(fastCoolPlate + 1);
      Serial.println(F(" Phase 2 -> PWM 70 for 5 s"));
    }

    // Phase 2: PWM 70 for the next 5 seconds
    if (fastCoolPhase == 2 && elapsed >= (FAST_COOL_PHASE1_MS + FAST_COOL_PHASE2_MS)) {
      fastCoolPhase = 3;
      coolPlate(fastCoolPlate, FAST_COOL_PHASE3_PWM);
      Serial.print(F("[FAST_COOL] P"));
      Serial.print(fastCoolPlate + 1);
      Serial.println(F(" Phase 3 -> PWM 60 for 10 s"));
    }

    // Phase 3: PWM 60 until 25 s elapsed
    if (fastCoolPhase == 3 &&
        elapsed >= (FAST_COOL_PHASE1_MS + FAST_COOL_PHASE2_MS + FAST_COOL_PHASE3_MS)) {
      fastCoolPhase = 4;
      coolPlate(fastCoolPlate, FAST_COOL_PHASE4_PWM);
      Serial.print(F("[FAST_COOL] P"));
      Serial.print(fastCoolPlate + 1);
      Serial.println(F(" Phase 4 -> PWM 55 for 4 min 35 s (to 5 min total)"));
    }

    // Phase 4: PWM 55 until the full 5 minutes are complete
    if (elapsed >= FAST_COOL_TOTAL_MS) {
      stopPlate(fastCoolPlate);
      mode = IDLE;
      Serial.print(F("[FAST_COOL] P"));
      Serial.print(fastCoolPlate + 1);
      Serial.println(F(" done. Stopped after 5 min."));
    }
  }

  // ── Serial command handler ────────────────────────────────
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();
  if (input.length() == 0) return;

  // ── HOT ALL ──────────────────────────────────────────────
  if (input.equalsIgnoreCase("HOT ALL")) {
    // Set all four outputs directly. Do not globally stop first:
    // some H-bridge/MOSFET setups can latch or disable outputs when
    // all PWM inputs are simultaneously driven to zero.
    for (int i = 0; i < 4; i++) heatPlate(i, HOT_PWM);
    mode = HOT_ALL;
    Serial.println(F("[OK] All 4 plates heating"));
  }

  // ── STOP ─────────────────────────────────────────────────
  else if (input.equalsIgnoreCase("STOP")) {
    stopAll();
    mode = IDLE;
    Serial.println(F("[OK] All plates stopped"));
  }

  // ── EXP <pattern> [COOL:NNN] [HA:NNN] [HB:NNN] [HC:NNN] [HD:NNN] ──
  else if (input.length() > 4 && input.substring(0, 4).equalsIgnoreCase("EXP ")) {
    String rest = input.substring(4);
    rest.trim();

    // Split pattern (before first space) from optional PWM params (after first space)
    int spaceIdx = rest.indexOf(' ');
    String nodeStr  = (spaceIdx == -1) ? rest : rest.substring(0, spaceIdx);
    String paramStr = (spaceIdx == -1) ? String("") : rest.substring(spaceIdx + 1);
    paramStr.trim();
    paramStr.toUpperCase();

    // Parse node pattern (only A/B/C/D, dashes are skipped)
    patternLen = 0;
    for (int i = 0; i < (int)nodeStr.length() && patternLen < MAX_STEPS; i++) {
      char c = toupper(nodeStr.charAt(i));
      if (c == 'A' || c == 'B' || c == 'C' || c == 'D') {
        expPattern[patternLen++] = c;
      }
    }

    if (patternLen == 0) {
      Serial.println(F("[ERR] No valid nodes (A/B/C/D) found in pattern"));
      return;
    }

    // Reset PWMs to defaults, then apply any overrides
    expCoolPWM     = FAST_COOL_PHASE1_PWM;
    expCoolMidPWM  = FAST_COOL_PHASE2_PWM;
    expCoolHoldPWM = 65;
    expCoolFinalPWM = 55;
    expHotPWM[0] = expHotPWM[1] = expHotPWM[2] = expHotPWM[3] = HOT_PWM;

    int idx;
    idx = paramStr.indexOf("COOL:");
    if (idx != -1) expCoolPWM = constrain(paramStr.substring(idx + 5).toInt(), 0, 255);
    idx = paramStr.indexOf("MID:");
    if (idx != -1) expCoolMidPWM = constrain(paramStr.substring(idx + 4).toInt(), 0, 255);
    idx = paramStr.indexOf("HOLD:");
    if (idx != -1) expCoolHoldPWM = constrain(paramStr.substring(idx + 5).toInt(), 0, 255);
    idx = paramStr.indexOf("FINAL:");
    if (idx != -1) expCoolFinalPWM = constrain(paramStr.substring(idx + 6).toInt(), 0, 255);

    const char nodeChars[4] = {'A', 'B', 'C', 'D'};
    for (int i = 0; i < 4; i++) {
      String key = "H"; key += nodeChars[i]; key += ":";
      idx = paramStr.indexOf(key);
      if (idx != -1) expHotPWM[i] = constrain(paramStr.substring(idx + 3).toInt(), 0, 255);
    }

    Serial.print(F("[EXP] Pattern ("));
    Serial.print(patternLen);
    Serial.print(F(" steps): "));
    for (int i = 0; i < patternLen; i++) {
      if (i > 0) Serial.print('-');
      Serial.print(expPattern[i]);
    }
    Serial.println();
    Serial.print(F("[EXP] COOL boost="));  Serial.print(expCoolPWM);
    Serial.print(F(" mid="));              Serial.print(expCoolMidPWM);
    Serial.print(F(" hold="));             Serial.print(expCoolHoldPWM);
    Serial.print(F(" final="));            Serial.print(expCoolFinalPWM);
    Serial.print(F("  HOT: A="));          Serial.print(expHotPWM[0]);
    Serial.print(F(" B="));               Serial.print(expHotPWM[1]);
    Serial.print(F(" C="));               Serial.print(expHotPWM[2]);
    Serial.print(F(" D="));               Serial.println(expHotPWM[3]);

    // Start preheat directly; do not globally stop all channels first.
    // This keeps the four H-bridges independent and matches the proven
    // manual behavior of heating each Peltier separately.
    for (int i = 0; i < 4; i++) heatPlate(i, PRE_HOT_PWM);
    preHotStartMs = millis();
    lastStatusMs  = preHotStartMs;
    mode          = PRE_HOT;

    Serial.println(F("[PRE_HOT] All 4 plates heating for 3 min."));
  }

  // ── X COOL FAST ──────────────────────────────────────────
  else if (
      input.equalsIgnoreCase("1 COOL FAST") ||
      input.equalsIgnoreCase("2 COOL FAST") ||
      input.equalsIgnoreCase("3 COOL FAST") ||
      input.equalsIgnoreCase("4 COOL FAST")) {

    int id = input.charAt(0) - '1';
    stopAll();
    coolPlate(id, FAST_COOL_PHASE1_PWM);
    fastCoolPlate = id;
    fastCoolStartMs = millis();
    fastCoolPhase = 1;
    mode = FAST_COOL;

    Serial.print(F("[FAST_COOL] P"));
    Serial.print(id + 1);
    Serial.println(F(" Phase 1 -> PWM 80 for 5 s"));
  }

  // ── Manual per-Peltier: "1 f150" ─────────────────────────
  else {
    int id = input.charAt(0) - '1';
    if (id >= 0 && id <= 3 && input.length() >= 3) {
      char cmd = input.charAt(2);
      int  pwm = constrain(input.substring(3).toInt(), 0, 255);

      if (cmd == 'f') {
        coolPlate(id, pwm);
        Serial.print(F("P")); Serial.print(id + 1);
        Serial.print(F(" Cooling  PWM=")); Serial.println(platePWM[id]);
      } else if (cmd == 'r') {
        heatPlate(id, pwm);
        Serial.print(F("P")); Serial.print(id + 1);
        Serial.print(F(" Heating  PWM=")); Serial.println(platePWM[id]);
      } else if (cmd == 's') {
        stopPlate(id);
        Serial.print(F("P")); Serial.print(id + 1); Serial.println(F(" Stopped"));
      } else {
        Serial.println(F("[ERR] Unknown command (f/r/s expected)"));
      }
    } else {
      Serial.println(F("[ERR] Unknown command"));
    }
  }
}