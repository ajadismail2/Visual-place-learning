---
title: Four-Peltier controller
description: ESP32 program for four independently driven Peltier plates, timed trials and wireless display synchronisation.
section: Software
---
An ESP32 drives four BTS7960 bridges and sends the selected A–D state to the display over ESP-NOW.

[Download Experiment_Controller.ino](../downloads/firmware/Experiment_Controller/Experiment_Controller.ino) · [Configuration example](../downloads/firmware/Experiment_Controller/local_config.example.h)

## Control

Each BTS7960 drives one Peltier plate. LPWM heats and RPWM cools; the opposite output is zeroed before reversal.

Peltier-plate control is open-loop, using 20 kHz, 8-bit PWM (0–255). Background and ring control are independent.

## Peltier-plate labels and wiring

| Peltier plate | Manual number | Driver channel | RPWM | LPWM | R_EN | L_EN |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1 | 3 | 27 | 14 | 23 | 22 |
| B | 2 | 2 | 25 | 26 | 13 | 15 |
| C | 3 | 4 | 19 | 18 | 2 | 16 |
| D | 4 | 1 | 32 | 33 | 4 | 5 |

Values are ESP32 GPIO numbers. Share controller and driver logic ground. Enables remain HIGH; stopping zeros both PWM inputs. See [power connections](../hardware/esp32-and-arduino-wiring.md#power-and-peltier-plate-connections).


## Prepare and start

1. Place the downloaded sketch in an Arduino sketch folder named `Experiment_Controller`.
2. Copy `local_config.example.h` to `local_config.h` in that folder. Enter the display board's MAC address and local AP settings, then remove the example's `#error` line. Use an AP password of at least eight characters.
3. Use an ESP32 board package supporting the sketch's `ledcAttach` interface and `wifi_tx_info_t` send callback. Older package versions can require API changes. Firmware compilation and hardware operation have not been verified here.
4. Configure both boards for radio channel 1. The sketch sets both the AP channel and peer channel; changing one alone is insufficient. The AP fixes the radio channel and provides no web interface.
5. Open Serial Monitor at 115200 baud with a newline ending. Verify Peltier-plate labels and display states, then enter the sequence.

```text
EXP B-C-D-C-B-A-D-C-B-A
```

Ten trials take 55 minutes including five-minute preheat. Analysis starts at the first cooling trial. The parser accepts lowercase, ignores non-A–D characters and retains the first 16 valid selections; check the echoed order.

## One complete sequence

Startup zeros the Peltier-plate outputs and sends `OFF`. `EXP` resets the sequence and starts preheat.

| Phase | Output | Duration |
| --- | --- | --- |
| Preheat | All four Peltier plates heat at PWM 30; display off | 300 s |
| Cooling boost | Selected Peltier plate cools at PWM 150 | First 23 s of each trial |
| Cooling hold, first selection | Selected Peltier plate cools at PWM 106 | Remaining 277 s |
| Cooling hold, repeat selection | Selected Peltier plate cools at PWM 120 | Remaining 277 s |
| Other Peltier plates, never selected | Heat at PWM 29 | While another Peltier plate cools |
| Other Peltier plates, previously selected | Heat at PWM 24 | After their return boost |
| Return from cooling | Previous Peltier plate heats at PWM 50, then 24 | Boost lasts 17 s |
| Sequence complete | All Peltier-plate PWM outputs zero; display off | Until another command |

Each Peltier plate's repeat flag selects its hold PWM and resets at the next experiment.

At trial boundaries, `applyStep()` zeros outputs, starts cooling boost and sets heating levels. Consecutive selections of the same Peltier plate restart cooling with the repeat hold PWM and no intervening heating boost.

Every letter initiates cooling of a Peltier plate, including an eleventh selection. The sketch has no all-heating probe trial.

## Commands and display synchronisation

| Command | Action |
| --- | --- |
| `EXP A-D-C-D` | Reset the current sequence, preheat and run four trials |
| `STOP` | Zero all four Peltier-plate outputs, clear the sequence and send display OFF |
| `LED A` | Send visual state A; B, C and D work the same way |
| `LED OFF` | Request a blank display |
| `1 h30` | Heat Peltier plate A at PWM 30 |
| `2 c150` | Cool Peltier plate B at PWM 150 |
| `3 s` | Stop Peltier plate C |

Send `STOP` before manual commands; they do not cancel the sequence. `LED OFF` affects only the display.

Each trial sends `STATE:A`–`STATE:D`. Radio delivery does not confirm the visible pattern; the sketch has no retry or stop-on-radio-failure logic.

## Timing and temperature checks

`millis()` controls `IDLE`, `PRE_HOT`, trial transitions and the 17-second heating boost. Progress prints about once a minute. Serial line reads can briefly block timing.

Record Peltier-plate temperatures alongside video. `STOP` zeros the four plate outputs and requests display shutdown; stop background and ring heating separately.

## Full source

The download replaces the earlier controller file. Device address and AP credentials are configured locally; names and explanatory comments use controller/display terminology. The supplied control logic and numeric settings are preserved.

<details class="source-code">
<summary>Read Experiment_Controller.ino</summary>
<pre tabindex="0" aria-label="Experiment_Controller.ino source code"><code>// Experiment_Controller.ino
// Controls 4 Peltier plates and synchronises the LED display controller via ESP-NOW.
// Controlled over the Serial Monitor (115200 baud).
//
// ── No wires needed between the two boards ───────────────────────────────
//   The controller sends one-way ESP-NOW packets to the display controller over the air.
//   No router is required. Verify radio delivery in the installed setup.
//
// ── Setup steps ──────────────────────────────────────────────────────────
//   1. Flash Display_Controller to the LED matrix ESP32.
//   2. Open the display controller&#x27;s Serial Monitor to read its MAC address printout.
//   3. Configure DISPLAY_MAC in local_config.h, then flash this sketch.
//
// ── Serial commands ────────────────────────────────────────────────────────
//   EXP A-D-C-D   -&gt; pre-heat, then run pattern (A/B/C/D letters, dashes optional)
//   STOP          -&gt; emergency stop, all plates off, LED off
//   1 h200 / 2 c150 / 3 s -&gt; manual per-plate control (plate 1-4, heat/cool PWM 0-255, stop)
//
// ── Node map ─────────────────────────────────────────────────────────────
//   A = ch3 (idx 0)   B = ch2 (idx 1)   C = ch4 (idx 2)   D = ch1 (idx 3)
//   (verified by hand: 1 r/f=D, 2 r/f=B, 3 r/f=A, 4 r/f=C)
//
// ── Timing ───────────────────────────────────────────────────────────────
//   Pre-heat  : all 4 plates at PRE_HOT_PWM for PRE_HOT_DURATION_MS
//   Each step : cool plate  -&gt; boost (COOL_BOOST_PWM, 23 s)
//                           -&gt; hold  (COOL_HOLD_PWM on 1st cool,
//                                    COOL_HOLD_PWM_REPEAT on 2nd+ cool ;
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
//   EXP_HOT_PWM instead ; the two need different PWM because the plate&#x27;s
//   own thermal state has already shifted by the time steps begin. The
//   moment a plate finishes cooling it gets a short POST_COOL_BOOST_PWM
//   pulse to bring it back up to temperature quickly, then settles at
//   HOT_PWM permanently.

#include &lt;WiFi.h&gt;
#include &lt;esp_now.h&gt;

// Local radio settings are configured in the private header.
#include &quot;local_config.h&quot;
#define AP_CHANNEL  1                              // must match display controller channel

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
#define REN4  2
#define LEN4  16

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
#define PRE_HOT_PWM         30
#define EXP_HOT_PWM         29  // not-yet-cooled plates once EXPERIMENT has started (PRE_HOT phase still uses PRE_HOT_PWM)
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

// Plate index -&gt; has this plate ever finished a cool step? A plate needs
// PRE_HOT_PWM to hold at 36C before its first cool cycle, and HOT_PWM
// after, since post-cool the plate reaches 36C at a different PWM.
static bool hasCooled[4] = {false, false, false, false};

// Set by applyStep() for the plate currently cooling ; true if this plate
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
    case &#x27;A&#x27;: return 0; case &#x27;B&#x27;: return 1;
    case &#x27;C&#x27;: return 2; case &#x27;D&#x27;: return 3;
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
  for (int i = 0; i &lt; 4; i++) stopPlate(i);
}

// justCooledIdx is the plate that just finished cooling (or -1 if none,
// e.g. the very first cool step after pre-heat) ; it gets the post-cool
// boost instead of jumping straight to its steady-state PWM.
static void applyStep(int coolIdx, int justCooledIdx, unsigned long now) {
  stopAllPlates();
  delayMicroseconds(200);
  coolPlate(coolIdx, COOL_BOOST_PWM);
  currentCoolIsRepeat    = hasCooled[coolIdx]; // was this plate already cooled before now?
  hasCooled[coolIdx]      = true;   // this plate has now been through a cool cycle
  inPostCoolBoost[coolIdx] = false;
  for (int i = 0; i &lt; 4; i++) {
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

// Called every loop() tick ; ends a plate&#x27;s post-cool boost once its
// POST_COOL_BOOST_DURATION_MS has elapsed, independent of the step clock.
static void servicePostCoolBoost(unsigned long now) {
  for (int i = 0; i &lt; 4; i++) {
    if (inPostCoolBoost[i] &amp;&amp; now &gt;= postCoolBoostUntilMs[i]) {
      inPostCoolBoost[i] = false;
      heatPlate(i, HOT_PWM);
    }
  }
}

// ── ESP-NOW helpers ───────────────────────────────────────────────────────

static void espNowSend(const char* msg) {
  esp_err_t r = esp_now_send(DISPLAY_MAC,
                              (const uint8_t*)msg,
                              (size_t)(strlen(msg) + 1));
  if (r != ESP_OK) {
    Serial.print(F(&quot;[ESP-NOW] Send error: &quot;));
    Serial.println(esp_err_to_name(r));
  }
}

static void onDataSent(const wifi_tx_info_t* tx_info, esp_now_send_status_t status) {
  (void)tx_info;
  Serial.println(status == ESP_NOW_SEND_SUCCESS
                    ? F(&quot;[ESP-NOW] Delivery OK&quot;)
                    : F(&quot;[ESP-NOW] Delivery FAILED ; check DISPLAY_MAC / channel&quot;));
}

static void displayOff()              { espNowSend(&quot;OFF&quot;); }
static void displayShowState(char s)  {
  char buf[10];
  snprintf(buf, sizeof(buf), &quot;STATE:%c&quot;, s);
  espNowSend(buf);
}

// ── Experiment control ────────────────────────────────────────────────────

static void hardStop() {
  stopAllPlates();
  displayOff();
  mode    = IDLE;
  patLen  = 0;
  stepIdx = 0;
  for (int i = 0; i &lt; 4; i++) { hasCooled[i] = false; inPostCoolBoost[i] = false; }
  Serial.println(F(&quot;[CONTROLLER] Hard stop ; all plates off, LED off.&quot;));
}

static bool startExperiment(const String&amp; raw) {
  char newPat[MAX_STEPS];
  int  newLen = 0;
  for (int i = 0; i &lt; (int)raw.length() &amp;&amp; newLen &lt; MAX_STEPS; i++) {
    char c = toupper((unsigned char)raw.charAt(i));
    if (c == &#x27;A&#x27; || c == &#x27;B&#x27; || c == &#x27;C&#x27; || c == &#x27;D&#x27;)
      newPat[newLen++] = c;
  }
  if (newLen == 0) return false;

  hardStop();   // safe stop before any hardware change

  memcpy(pat, newPat, newLen);
  patLen = newLen;

  stopAllPlates();
  delayMicroseconds(200);
  for (int i = 0; i &lt; 4; i++) heatPlate(i, PRE_HOT_PWM);
  displayOff();

  unsigned long now = millis();
  modeStartMs = now;
  lastLogMs   = now;
  mode        = PRE_HOT;

  Serial.print(F(&quot;[CONTROLLER] Pre-heat started. Pattern (&quot;));
  Serial.print(patLen); Serial.print(F(&quot; steps × 5 min): &quot;));
  for (int i = 0; i &lt; patLen; i++) { if (i) Serial.print(&#x27;-&#x27;); Serial.print(pat[i]); }
  Serial.println();
  return true;
}

// ── setup ─────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(100);

  // All Peltier channels off immediately on boot
  for (int i = 0; i &lt; 4; i++) {
    pinMode(REN_PIN[i], OUTPUT);
    pinMode(LEN_PIN[i], OUTPUT);
    digitalWrite(REN_PIN[i], HIGH);
    digitalWrite(LEN_PIN[i], HIGH);

    ledcAttach(RPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcAttach(LPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcWrite(RPWM_PIN[i], 0);
    ledcWrite(LPWM_PIN[i], 0);
  }

  // WiFi: AP_STA mode ; soft AP only used to pin the radio to AP_CHANNEL
  // so ESP-NOW has a fixed channel to talk to the display controller on; no HTTP served.
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS, AP_CHANNEL);
  delay(200);
  Serial.print(F(&quot;[WiFi] AP SSID : &quot;)); Serial.println(AP_SSID);
  Serial.print(F(&quot;[WiFi] IP      : &quot;)); Serial.println(WiFi.softAPIP());
  Serial.print(F(&quot;[WiFi] Channel : &quot;)); Serial.println(AP_CHANNEL);
  Serial.print(F(&quot;[Controller MAC STA]: &quot;)); Serial.println(WiFi.macAddress());

  // ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println(F(&quot;[ESP-NOW] Init FAILED ; halting&quot;));
    while (true) delay(1000);
  }

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, DISPLAY_MAC, 6);
  peer.channel = 1;       // 0 = use current channel
  peer.encrypt = false;
  if (esp_now_add_peer(&amp;peer) != ESP_OK) {
    Serial.println(F(&quot;[ESP-NOW] Add peer FAILED ; halting&quot;));
    while (true) delay(1000);
  }
  esp_now_register_send_cb(onDataSent);
  // Use an ESP32 board package compatible with wifi_tx_info_t.
  Serial.println(F(&quot;[ESP-NOW] Ready.&quot;));

  displayOff();   // ensure display controller starts dark

  Serial.println(F(&quot;[CONTROLLER] Ready. Commands: EXP A-D-C-D | STOP | LED A/B/C/D/OFF | 1 h200 / 2 c150 / 3 s&quot;));
}

// ── Serial command handler ───────────────────────────────────────────────

static void handleSerial() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil(&#x27;\n&#x27;);
  input.trim();
  if (input.length() == 0) return;

  if (input.equalsIgnoreCase(&quot;STOP&quot;)) {
    hardStop();
  } else if (input.length() &gt; 4 &amp;&amp; input.substring(0, 4).equalsIgnoreCase(&quot;EXP &quot;)) {
    if (startExperiment(input.substring(4)))
      Serial.println(F(&quot;[OK] Experiment starting.&quot;));
    else
      Serial.println(F(&quot;[ERR] Invalid pattern ; use letters A/B/C/D only&quot;));
  } else if (input.equalsIgnoreCase(&quot;LED OFF&quot;)) {
    displayOff();
    Serial.println(F(&quot;[OK] LED OFF sent&quot;));
  } else if (input.length() == 5 &amp;&amp; input.substring(0,4).equalsIgnoreCase(&quot;LED &quot;)) {
    char s = toupper(input.charAt(4));
    if (s&gt;=&#x27;A&#x27; &amp;&amp; s&lt;=&#x27;D&#x27;) {
      displayShowState(s);
      Serial.print(F(&quot;[OK] LED &quot;));
      Serial.println(s);
    } else {
      Serial.println(F(&quot;[ERR] Use LED A, LED B, LED C, LED D or LED OFF&quot;));
    }
  } else if (input.charAt(0) &gt;= &#x27;1&#x27; &amp;&amp; input.charAt(0) &lt;= &#x27;4&#x27; &amp;&amp; input.length() &gt;= 3) {
    // Manual per-plate control: &quot;1 h200&quot; (heat), &quot;2 c150&quot; (cool), &quot;3 s&quot; (stop)
    int  id  = input.charAt(0) - &#x27;1&#x27;;
    char cmd = tolower(input.charAt(2));
    if (cmd == &#x27;s&#x27;) {
      stopPlate(id);
      Serial.print(F(&quot;[OK] P&quot;)); Serial.print(id + 1); Serial.println(F(&quot; stopped&quot;));
    } else if (cmd == &#x27;h&#x27; || cmd == &#x27;c&#x27;) {
      int pwm = constrain(input.substring(3).toInt(), 0, 255);
      if (cmd == &#x27;h&#x27;) heatPlate(id, pwm); else coolPlate(id, pwm);
      Serial.print(F(&quot;[OK] P&quot;)); Serial.print(id + 1);
      Serial.print(cmd == &#x27;h&#x27; ? F(&quot; Heating  PWM=&quot;) : F(&quot; Cooling  PWM=&quot;));
      Serial.println(pwm);
    } else {
      Serial.println(F(&quot;[ERR] Unknown command (h/c/s expected)&quot;));
    }
  } else {
    Serial.println(F(&quot;[ERR] Unknown command. Use: EXP A-D-C-D | STOP | LED A/B/C/D/OFF | 1 h200 / 2 c150 / 3 s&quot;));
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
    if (now - lastLogMs &gt;= LOG_INTERVAL_MS) {
      lastLogMs = now;
      unsigned long rem = (elapsed &lt; PRE_HOT_DURATION_MS) ? (PRE_HOT_DURATION_MS - elapsed) / 1000UL : 0;
      Serial.print(F(&quot;[PRE_HOT] &quot;)); Serial.print(rem/60); Serial.print(F(&quot;m &quot;)); Serial.print(rem%60); Serial.println(F(&quot;s remaining&quot;));
    }
    if (elapsed &gt;= PRE_HOT_DURATION_MS) {
      stepIdx     = 0;
      inBoost     = true;
      stepStartMs = now;
      lastLogMs   = now;
      mode        = EXPERIMENT;
      applyStep(nodeToIdx(pat[0]), -1, now);
      displayShowState(pat[0]);
      Serial.print(F(&quot;[EXP] Pre-heat done. Step 1/&quot;)); Serial.print(patLen);
      Serial.print(F(&quot; ; cooling &quot;)); Serial.println(pat[0]);
    }
  }

  // ── EXPERIMENT ───────────────────────────────────────────────────────
  if (mode == EXPERIMENT) {
    unsigned long elapsed = now - stepStartMs;
    int ci = nodeToIdx(pat[stepIdx]);

    if (inBoost &amp;&amp; elapsed &gt;= COOL_BOOST_MS) {
      inBoost = false;
      uint8_t holdPwm = currentCoolIsRepeat ? COOL_HOLD_PWM_REPEAT : COOL_HOLD_PWM;
      coolPlate(ci, holdPwm);
      Serial.print(F(&quot;[EXP] Node &quot;)); Serial.print(pat[stepIdx]);
      Serial.print(F(&quot; -&gt; hold (PWM &quot;)); Serial.print(holdPwm); Serial.println(&#x27;)&#x27;);
    }

    if (now - lastLogMs &gt;= LOG_INTERVAL_MS) {
      lastLogMs = now;
      unsigned long rem = (elapsed &lt; STEP_DURATION_MS) ? (STEP_DURATION_MS - elapsed) / 1000UL : 0;
      Serial.print(F(&quot;[EXP] Step &quot;)); Serial.print(stepIdx+1); Serial.print(&#x27;/&#x27;); Serial.print(patLen);
      Serial.print(F(&quot; node=&quot;)); Serial.print(pat[stepIdx]);
      Serial.print(F(&quot; remain=&quot;)); Serial.print(rem/60); Serial.print(&#x27;m&#x27;); Serial.print(rem%60); Serial.println(&#x27;s&#x27;);
    }

    if (elapsed &gt;= STEP_DURATION_MS) {
      stepIdx++;
      if (stepIdx &gt;= patLen) {
        stopAllPlates();
        displayOff();
        mode   = IDLE;
        patLen = 0;
        Serial.println(F(&quot;[EXP] All steps complete. Plates stopped. LED off.&quot;));
      } else {
        inBoost     = true;
        stepStartMs = now;
        lastLogMs   = now;
        applyStep(nodeToIdx(pat[stepIdx]), ci, now);
        displayShowState(pat[stepIdx]);
        Serial.print(F(&quot;[EXP] Step &quot;)); Serial.print(stepIdx+1); Serial.print(&#x27;/&#x27;); Serial.print(patLen);
        Serial.print(F(&quot; ; cooling &quot;)); Serial.println(pat[stepIdx]);
      }
    }
  }
}
</code></pre>
</details>
