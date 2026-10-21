---
title: UART hot-output slave
description: "An alternative split-controller experiment receives heating commands over a wired serial link."
section: Software
---
[← Controller programs](index.md)

<div class="download-links" markdown="1">

[Download hot_slave.ino](../downloads/firmware/hot_slave/hot_slave.ino){: download="hot_slave.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

This alternative controller receives heating commands through Serial2 on GPIO 16 at 115200 baud.

## Commands

| Command | Action |
| --- | --- |
| H0:47 | Heat output 0 at PWM 47 |
| S2 | Stop output 2 |
| SA | Stop all outputs |

Output indices 0–3 use GPIO **32, 25, 27 and 18**. It holds the last command until another arrives.

The matching cool-master program is not included. The supplied Master_Controller does not send this protocol and uses GPIO 17 as a driver enable. Do not connect the two as a serial pair.

## Full source

<details class="source-code">
<summary>Read hot_slave.ino · 84 lines</summary>
<pre tabindex="0" aria-label="hot_slave.ino source code"><code>// ============================================================
//  4 Peltier Experiment Controller — HOT SLAVE
//  Drives LPWM pins (heat direction) for all 4 plates.
//  Receives commands from Cool Master via Serial2
//  (RX=GPIO16 ← Master TX=GPIO17, shared GND).
//
//  Protocol (newline-terminated ASCII):
//    H&lt;idx&gt;:&lt;pwm&gt;  →  heat plate idx at pwm   (e.g. H0:47)
//    S&lt;idx&gt;        →  stop plate idx           (e.g. S2)
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

  for (int i = 0; i &lt; 4; i++) {
    ledcAttach(LPWM_PIN[i], PWM_FREQ, PWM_RES);
    ledcWrite(LPWM_PIN[i], 0);
  }

  Serial.println(F(&quot;\n=== 4 Peltier Controller — HOT SLAVE ===&quot;));
  Serial.println(F(&quot;Listening on Serial2 RX=GPIO16 &lt;- Master TX=GPIO17&quot;));
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
  if (!Serial2.available()) return;

  String cmd = Serial2.readStringUntil(&#x27;\n&#x27;);
  cmd.trim();
  if (cmd.length() == 0) return;

  // SA → stop all
  if (cmd.equalsIgnoreCase(&quot;SA&quot;)) {
    for (int i = 0; i &lt; 4; i++) ledcWrite(LPWM_PIN[i], 0);
    Serial.println(F(&quot;[SLAVE] Stop all&quot;));
    return;
  }

  // S&lt;idx&gt; → stop one plate
  if (cmd.charAt(0) == &#x27;S&#x27; &amp;&amp; cmd.length() == 2) {
    int idx = cmd.charAt(1) - &#x27;0&#x27;;
    if (idx &gt;= 0 &amp;&amp; idx &lt;= 3) {
      ledcWrite(LPWM_PIN[idx], 0);
      Serial.print(F(&quot;[SLAVE] Stop P&quot;)); Serial.println(idx + 1);
    }
    return;
  }

  // H&lt;idx&gt;:&lt;pwm&gt; → heat one plate
  if (cmd.charAt(0) == &#x27;H&#x27; &amp;&amp; cmd.length() &gt;= 4 &amp;&amp; cmd.charAt(2) == &#x27;:&#x27;) {
    int idx = cmd.charAt(1) - &#x27;0&#x27;;
    int pwm = constrain(cmd.substring(3).toInt(), 0, 255);
    if (idx &gt;= 0 &amp;&amp; idx &lt;= 3) {
      ledcWrite(LPWM_PIN[idx], pwm);
      Serial.print(F(&quot;[SLAVE] Heat P&quot;)); Serial.print(idx + 1);
      Serial.print(F(&quot; PWM=&quot;)); Serial.println(pwm);
    }
    return;
  }

  Serial.print(F(&quot;[SLAVE] Unknown cmd: &quot;)); Serial.println(cmd);
}
</code></pre>
</details>
