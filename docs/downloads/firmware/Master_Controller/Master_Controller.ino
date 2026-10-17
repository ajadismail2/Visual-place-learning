// Master_Controller.ino
// Controls 4 Peltier plates and synchronises the LED slave via ESP-NOW.
// Controlled over the Serial Monitor (115200 baud).
//
// ── No wires needed between the two boards ───────────────────────────────
//   The master sends one-way ESP-NOW packets to the slave over the air.
//   Range: ~100 m line-of-sight. No router required.
//
// ── Setup steps ──────────────────────────────────────────────────────────
//   1. Flash LED_Slave to the LED matrix ESP32.
//   2. Open the slave's Serial Monitor to read its MAC address printout.
//   3. Paste that MAC into SLAVE_MAC[] below, then flash this sketch.
//
// ── Serial commands ────────────────────────────────────────────────────────
//   EXP A-D-C-D   → pre-heat, then run pattern (A/B/C/D letters, dashes optional)
//   STOP          → emergency stop, all plates off, LED off
//   1 h200 / 2 c150 / 3 s → manual per-plate control (plate 1-4, heat/cool PWM 0-255, stop)
//
// ── Node map ─────────────────────────────────────────────────────────────
//   A = ch3 (idx 0)   B = ch2 (idx 1)   C = ch4 (idx 2)   D = ch1 (idx 3)
//   (verified by hand: 1 r/f=D, 2 r/f=B, 3 r/f=A, 4 r/f=C)
//
// ── Timing ───────────────────────────────────────────────────────────────
//   Pre-heat  : all 4 plates at PRE_HOT_PWM for PRE_HOT_DURATION_MS
//   Each step : cool plate  → boost (COOL_BOOST_PWM, 23 s)
//                           → hold  (COOL_HOLD_PWM on 1st cool,
//                                    COOL_HOLD_PWM_REPEAT on 2nd+ cool —
//                                    a plate drifts hotter each time it
//                                    has cooled before, so it needs more
//                                    cooling PWM to hold at temp)
//               other plates not yet cooled          : EXP_HOT_PWM
//               other plates already cooled          : HOT_PWM
//               plate that JUST finished cooling     : POST_COOL_BOOST_PWM
//                                                       for POST_COOL_BOOST_DURATION_MS,
//                                                       then HOT_PWM
//   A plate holds at PRE_HOT_PWM only during the initial pre-heat. Once the
//   EXPERIMENT phase starts, a plate that has never been cooled holds at
//   EXP_HOT_PWM instead — the two need different PWM because the plate's
//   own thermal state has already shifted by the time steps begin. The
//   moment a plate finishes cooling it gets a short POST_COOL_BOOST_PWM
//   pulse to bring it back up to temperature quickly, then settles at
//   HOT_PWM permanently.

#include <WiFi.h>
#include <esp_now.h>

// ── Slave MAC address ─────────────────────────────────────────────────────
// Flash LED_Slave first, read its MAC from Serial Monitor, paste here.
// Example: {0xAA, 0xB  B, 0xCC, 0xDD, 0xEE, 0xFF}
// Updated slave MAC address
// Personal radio address and access-point credentials stay in a local file.
#include "local_config.h"
// The default FF:FF:FF:FF:FF:FF is broadcast — works without knowing the
// slave MAC but has no delivery confirmation. Replace with the real MAC
// for reliable unicast once you have it.

// ── Wi-Fi credentials ─────────────────────────────────────────────────────
#define AP_CHANNEL  1                              // must match slave channel

// ── Peltier pin assignments ───────────────────────────────────────────────
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
#define REN3  23
#define LEN3  22

#define RPWM4 19
#define LPWM4 18
#define REN4  21
#define LEN4  17  // was 22 (duplicate of LEN3) — GPIO17 is UART2 TX2, unused here

#define PWM_FREQ 20000
#define PWM_RES  8

// Arrays indexed by chamber (A=0,B=1,C=2,D=3); values are the channel
// verified by hand (1 r/f=D, 2 r/f=B, 3 r/f=A, 4 r/f=C) to actually drive
// that chamber, so EXP letters stay in sync with the real hardware.
static const uint8_t RPWM_PIN[4] = {RPWM3, RPWM2, RPWM4, RPWM1};
static const uint8_t LPWM_PIN[4] = {LPWM3, LPWM2, LPWM4, LPWM1};
static const uint8_t REN_PIN[4]  = {REN3,  REN2,  REN4,  REN1};
static const uint8_t LEN_PIN[4]  = {LEN3,  LEN2,  LEN4,  LEN1};

// ── Experiment constants ──────────────────────────────────────────────────
#define HOT_PWM             24
#define PRE_HOT_PWM         29
#define EXP_HOT_PWM         24  // not-yet-cooled plates once EXPERIMENT has started (PRE_HOT phase still uses PRE_HOT_PWM)
#define COOL_BOOST_PWM     150
#define COOL_HOLD_PWM       106
#define COOL_HOLD_PWM_REPEAT 120  // 2nd+ cool cycle: plate drifts hotter, needs more    to hold
#define COOL_BOOST_MS      (23UL  * 1000UL)
#define STEP_DURATION_MS   (5UL   * 60UL * 1000UL)
#define PRE_HOT_DURATION_MS (5UL  * 60UL * 1000UL)
#define LOG_INTERVAL_MS    (60UL  * 1000UL)
#define MAX_STEPS           16

#define POST_COOL_BOOST_PWM          50
#define POST_COOL_BOOST_DURATION_MS  (17UL * 1000UL)

// ── State machine ─────────────────────────────────────────────────────────
enum ExpMode { IDLE, PRE_HOT, EXPERIMENT };
static ExpMode mode = IDLE;

static char  pat[MAX_STEPS];
static int   patLen   = 0;
static int   stepIdx  = 0;
static bool  inBoost  = true;

static unsigned long modeStartMs = 0;
static unsigned long stepStartMs = 0;
static unsigned long lastLogMs   = 0;

// Plate index -> has this plate ever finished a cool step? A plate needs
// PRE_HOT_PWM to hold at 36C before its first cool cycle, and HOT_PWM
// after, since post-cool the plate reaches 36C at a different PWM.
static bool hasCooled[4] = {false, false, false, false};

// Set by applyStep() for the plate currently cooling — true if this plate
// has cooled before (its 2nd+ cool cycle), which needs COOL_HOLD_PWM_REPEAT
// instead of COOL_HOLD_PWM because the plate drifts to the hotter side.
static bool currentCoolIsRepeat = false;

// Post-cool boost: right after a plate finishes cooling, it is driven at
// POST_COOL_BOOST_PWM for POST_COOL_BOOST_DURATION_MS before dropping to
// HOT_PWM, to bring it back up to temperature quickly after the cold swing.
static bool          inPostCoolBoost[4]      = {false, false, false, false};
static unsigned long postCoolBoostUntilMs[4] = {0, 0, 0, 0};

// ── Peltier helpers ───────────────────────────────────────────────────────
// Inactive side is always zeroed BEFORE the active side is driven,
// preventing any shoot-through condition in the BTS7960 H-bridges.

static int nodeToIdx(char c) {
  switch (toupper((unsigned char)c)) {
    case 'A': return 0; case 'B': return 1;
    case 'C': return 2; case 'D': return 3;
    default:  return -1;
  }
}

static void heatPlate(int idx, uint8_t pwm) {
  ledcWrite(RPWM_PIN[idx], 0);
  ledcWrite(LPWM_PIN[idx], pwm);
}

static void coolPlate(int idx, uint8_t pwm) {
  ledcWrite(LPWM_PIN[idx], 0);
  ledcWrite(RPWM_PIN[idx], pwm);
}

static void stopPlate(int idx) {
  ledcWrite(RPWM_PIN[idx], 0);
  ledcWrite(LPWM_PIN[idx], 0);
}

static void stopAllPlates() {
  for (int i = 0; i < 4; i++) stopPlate(i);
}

// justCooledIdx is the plate that just finished cooling (or -1 if none,
// e.g. the very first cool step after pre-heat) — it gets the post-cool
// boost instead of jumping straight to its steady-state PWM.
static void applyStep(int coolIdx, int justCooledIdx, unsigned long now) {
  stopAllPlates();
  delayMicroseconds(200);
  coolPlate(coolIdx, COOL_BOOST_PWM);
  currentCoolIsRepeat    = hasCooled[coolIdx]; // was this plate already cooled before now?
  hasCooled[coolIdx]      = true;   // this plate has now been through a cool cycle
  inPostCoolBoost[coolIdx] = false;
  for (int i = 0; i < 4; i++) {
    if (i == coolIdx) continue;
    if (i == justCooledIdx) {
      heatPlate(i, POST_COOL_BOOST_PWM);
      inPostCoolBoost[i]      = true;
      postCoolBoostUntilMs[i] = now + POST_COOL_BOOST_DURATION_MS;
    } else {
      inPostCoolBoost[i] = false;
      heatPlate(i, hasCooled[i] ? HOT_PWM : EXP_HOT_PWM);
    }
  }
}

// Called every loop() tick — ends a plate's post-cool boost once its
// POST_COOL_BOOST_DURATION_MS has elapsed, independent of the step clock.
static void servicePostCoolBoost(unsigned long now) {
  for (int i = 0; i < 4; i++) {
    if (inPostCoolBoost[i] && now >= postCoolBoostUntilMs[i]) {
      inPostCoolBoost[i] = false;
      heatPlate(i, HOT_PWM);
    }
  }
}

// ── ESP-NOW helpers ───────────────────────────────────────────────────────

static void espNowSend(const char* msg) {
  esp_err_t r = esp_now_send(SLAVE_MAC,
                              (const uint8_t*)msg,
                              (size_t)(strlen(msg) + 1));
  if (r != ESP_OK) {
    Serial.print(F("[ESP-NOW] Send error: "));
    Serial.println(esp_err_to_name(r));
  }
}

static void onDataSent(const wifi_tx_info_t* tx_info, esp_now_send_status_t status) {
  (void)tx_info;
  Serial.println(status == ESP_NOW_SEND_SUCCESS
                    ? F("[ESP-NOW] Delivery OK")
                    : F("[ESP-NOW] Delivery FAILED — check SLAVE_MAC / channel"));
}

static void slaveOff()              { espNowSend("OFF"); }
static void slaveShowState(char s)  {
  char buf[10];
  snprintf(buf, sizeof(buf), "STATE:%c", s);
  espNowSend(buf);
}

// ── Experiment control ────────────────────────────────────────────────────

static void hardStop() {
  stopAllPlates();
  slaveOff();
  mode    = IDLE;
  patLen  = 0;
  stepIdx = 0;
  for (int i = 0; i < 4; i++) { hasCooled[i] = false; inPostCoolBoost[i] = false; }
  Serial.println(F("[MASTER] Hard stop — all plates off, LED off."));
}

static bool startExperiment(const String& raw) {
  char newPat[MAX_STEPS];
  int  newLen = 0;
  for (int i = 0; i < (int)raw.length() && newLen < MAX_STEPS; i++) {
    char c = toupper((unsigned char)raw.charAt(i));
    if (c == 'A' || c == 'B' || c == 'C' || c == 'D')
      newPat[newLen++] = c;
  }
  if (newLen == 0) return false;

  hardStop();   // safe stop before any hardware change

  memcpy(pat, newPat, newLen);
  patLen = newLen;

  stopAllPlates();
  delayMicroseconds(200);
  for (int i = 0; i < 4; i++) heatPlate(i, PRE_HOT_PWM);
  slaveOff();

  unsigned long now = millis();
  modeStartMs = now;
  lastLogMs   = now;
  mode        = PRE_HOT;

  Serial.print(F("[MASTER] Pre-heat started. Pattern ("));
  Serial.print(patLen); Serial.print(F(" steps × 5 min): "));
  for (int i = 0; i < patLen; i++) { if (i) Serial.print('-'); Serial.print(pat[i]); }
  Serial.println();
  return true;
}

// ── setup ─────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(100);

  // All Peltier channels off immediately on boot
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

  // WiFi: AP_STA mode — soft AP only used to pin the radio to AP_CHANNEL
  // so ESP-NOW has a fixed channel to talk to the slave on; no HTTP served.
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS, AP_CHANNEL);
  delay(200);
  Serial.print(F("[WiFi] AP SSID : ")); Serial.println(AP_SSID);
  Serial.print(F("[WiFi] IP      : ")); Serial.println(WiFi.softAPIP());
  Serial.print(F("[WiFi] Channel : ")); Serial.println(AP_CHANNEL);
  Serial.print(F("[Master MAC STA]: ")); Serial.println(WiFi.macAddress());

  // ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println(F("[ESP-NOW] Init FAILED — halting"));
    while (true) delay(1000);
  }

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, SLAVE_MAC, 6);
  peer.channel = 0;       // 0 = use current channel
  peer.encrypt = false;
  if (esp_now_add_peer(&peer) != ESP_OK) {
    Serial.println(F("[ESP-NOW] Add peer FAILED — halting"));
    while (true) delay(1000);
  }
  esp_now_register_send_cb(onDataSent);
  // NOTE: if this fails to compile on arduino-esp32 2.x, the send callback
  // signature there is the same (mac_addr, status) — only recv changed.
  Serial.println(F("[ESP-NOW] Ready."));

  slaveOff();   // ensure slave starts dark

  Serial.println(F("[MASTER] Ready. Commands: EXP A-D-C-D | STOP | 1 h200 / 2 c150 / 3 s"));
}

// ── Serial command handler ───────────────────────────────────────────────

static void handleSerial() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();
  if (input.length() == 0) return;

  if (input.equalsIgnoreCase("STOP")) {
    hardStop();
  } else if (input.length() > 4 && input.substring(0, 4).equalsIgnoreCase("EXP ")) {
    if (startExperiment(input.substring(4)))
      Serial.println(F("[OK] Experiment starting."));
    else
      Serial.println(F("[ERR] Invalid pattern — use letters A/B/C/D only"));
  } else if (input.charAt(0) >= '1' && input.charAt(0) <= '4' && input.length() >= 3) {
    // Manual per-plate control: "1 h200" (heat), "2 c150" (cool), "3 s" (stop)
    int  id  = input.charAt(0) - '1';
    char cmd = tolower(input.charAt(2));
    if (cmd == 's') {
      stopPlate(id);
      Serial.print(F("[OK] P")); Serial.print(id + 1); Serial.println(F(" stopped"));
    } else if (cmd == 'h' || cmd == 'c') {
      int pwm = constrain(input.substring(3).toInt(), 0, 255);
      if (cmd == 'h') heatPlate(id, pwm); else coolPlate(id, pwm);
      Serial.print(F("[OK] P")); Serial.print(id + 1);
      Serial.print(cmd == 'h' ? F(" Heating  PWM=") : F(" Cooling  PWM="));
      Serial.println(pwm);
    } else {
      Serial.println(F("[ERR] Unknown command (h/c/s expected)"));
    }
  } else {
    Serial.println(F("[ERR] Unknown command. Use: EXP A-D-C-D | STOP | 1 h200 / 2 c150 / 3 s"));
  }
}

// ── loop ──────────────────────────────────────────────────────────────────

void loop() {
  handleSerial();

  unsigned long now = millis();
  servicePostCoolBoost(now);

  // ── PRE_HOT ──────────────────────────────────────────────────────────
  if (mode == PRE_HOT) {
    unsigned long elapsed = now - modeStartMs;
    if (now - lastLogMs >= LOG_INTERVAL_MS) {
      lastLogMs = now;
      unsigned long rem = (elapsed < PRE_HOT_DURATION_MS) ? (PRE_HOT_DURATION_MS - elapsed) / 1000UL : 0;
      Serial.print(F("[PRE_HOT] ")); Serial.print(rem/60); Serial.print(F("m ")); Serial.print(rem%60); Serial.println(F("s remaining"));
    }
    if (elapsed >= PRE_HOT_DURATION_MS) {
      stepIdx     = 0;
      inBoost     = true;
      stepStartMs = now;
      lastLogMs   = now;
      mode        = EXPERIMENT;
      applyStep(nodeToIdx(pat[0]), -1, now);
      slaveShowState(pat[0]);
      Serial.print(F("[EXP] Pre-heat done. Step 1/")); Serial.print(patLen);
      Serial.print(F(" — cooling ")); Serial.println(pat[0]);
    }
  }

  // ── EXPERIMENT ───────────────────────────────────────────────────────
  if (mode == EXPERIMENT) {
    unsigned long elapsed = now - stepStartMs;
    int ci = nodeToIdx(pat[stepIdx]);

    if (inBoost && elapsed >= COOL_BOOST_MS) {
      inBoost = false;
      uint8_t holdPwm = currentCoolIsRepeat ? COOL_HOLD_PWM_REPEAT : COOL_HOLD_PWM;
      coolPlate(ci, holdPwm);
      Serial.print(F("[EXP] Node ")); Serial.print(pat[stepIdx]);
      Serial.print(F(" → hold (PWM ")); Serial.print(holdPwm); Serial.println(')');
    }

    if (now - lastLogMs >= LOG_INTERVAL_MS) {
      lastLogMs = now;
      unsigned long rem = (elapsed < STEP_DURATION_MS) ? (STEP_DURATION_MS - elapsed) / 1000UL : 0;
      Serial.print(F("[EXP] Step ")); Serial.print(stepIdx+1); Serial.print('/'); Serial.print(patLen);
      Serial.print(F(" node=")); Serial.print(pat[stepIdx]);
      Serial.print(F(" remain=")); Serial.print(rem/60); Serial.print('m'); Serial.print(rem%60); Serial.println('s');
    }

    if (elapsed >= STEP_DURATION_MS) {
      stepIdx++;
      if (stepIdx >= patLen) {
        stopAllPlates();
        slaveOff();
        mode   = IDLE;
        patLen = 0;
        Serial.println(F("[EXP] All steps complete. Plates stopped. LED off."));
      } else {
        inBoost     = true;
        stepStartMs = now;
        lastLogMs   = now;
        applyStep(nodeToIdx(pat[stepIdx]), ci, now);
        slaveShowState(pat[stepIdx]);
        Serial.print(F("[EXP] Step ")); Serial.print(stepIdx+1); Serial.print('/'); Serial.print(patLen);
        Serial.print(F(" — cooling ")); Serial.println(pat[stepIdx]);
      }
    }
  }
}
