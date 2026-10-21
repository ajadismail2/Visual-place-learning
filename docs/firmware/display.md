---
title: LED display controller
description: "An ESP32 translates a target letter into a panorama rotation across eight HUB75 panels."
section: Software
---
[← Controller programs](index.md)

<div class="download-links" markdown="1">

[Download Display_Controller.ino](../downloads/firmware/Display_Controller/Display_Controller.ino){: download="Display_Controller.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

The display ESP32 receives <code>STATE:A</code> to <code>STATE:D</code> over ESP-NOW. Each state shifts the pattern across the eight HUB75 panels. The display remains in that state until another command arrives.

## Pattern positions

| State | Offset |
| --- | --- |
| A | 192 px |
| B | 0 px |
| C | 64 px |
| D | 128 px |

The logical canvas is 256 × 64 pixels. The program maps it to the physical panel chain.

The diagonals in this program are about 19.5° from vertical. The horizontal bars are 11 and 10 rows thick.

## Direct control

Send <code>A</code>, <code>B</code>, <code>C</code>, <code>D</code> or <code>OFF</code> to the display board at **115200 baud**. The program uses the ESP32-HUB75-MatrixPanel-I2S-DMA library.

The uploaded program requests a minimum refresh rate of **1000 Hz**, with double buffering disabled. This is a configuration request, not a measured refresh rate or a guarantee that every panel and library configuration achieves it.

[Display wiring](../build/wiring.md#display-board-pin-map) · [Angle calculation](../build/visual-angle.md)

## Full source

<details class="source-code">
<summary>Read Display_Controller.ino · 248 lines</summary>
<pre tabindex="0" aria-label="Display_Controller.ino source code"><code>// Display_Controller.ino
// Receives state commands from Experiment_Controller via ESP-NOW (wireless)
// and displays the corresponding panorama rotation on the 8-panel
// HUB75 octagon column. No wires between boards needed.
//
// ── First-time setup ─────────────────────────────────────────────────────
//   1. Flash this sketch.
//   2. Open Serial Monitor at 115200 baud.
//   3. The display controller prints its MAC address on boot — copy it into
//      DISPLAY_MAC[] in Experiment_Controller.ino, then flash the experiment controller.
//
// ── Commands received from experiment controller ────────────────────────────────────────
//   OFF      → blank all panels
//   STATE:A  → rotation offset 192 px
//   STATE:B  → rotation offset   0 px
//   STATE:C  → rotation offset  64 px
//   STATE:D  → rotation offset 128 px
//
// All timing is controlled by the experiment controller. This board is purely reactive.
//
// ── Standalone testing over Serial Monitor (115200 baud) ─────────────────
//   Type A, B, C, D or OFF and press enter to preview a rotation without
//   the experiment controller board connected.

#include &lt;WiFi.h&gt;
#include &lt;esp_now.h&gt;
#include &lt;esp_wifi.h&gt;                 // for esp_wifi_set_channel
#include &lt;ESP32-HUB75-MatrixPanel-I2S-DMA.h&gt;

// ── Channel must match experiment controller AP_CHANNEL ─────────────────────────────────
#define ESPNOW_CHANNEL  1

// ── Display geometry ──────────────────────────────────────────────────────
#define PANELS_IN_CHAIN  8
#define VIRTUAL_W       256
#define VIRTUAL_H        64
#define ROTATE_CW        0
#define REVERSE_CHAIN    1

// ── HUB75 pin map ─────────────────────────────────────────────────────────
static HUB75_I2S_CFG::i2s_pins pins = {
    /*R1=*/  2, /*G1=*/ 15, /*B1=*/  4,
    /*R2=*/ 16, /*G2=*/ 27, /*B2=*/ 17,
    /*A =*/  5, /*B =*/ 18, /*C =*/ 19, /*D =*/ 21, /*E =*/ 12,
    /*LAT=*/ 25, /*OE =*/ 26, /*CLK=*/ 22
};

static MatrixPanel_I2S_DMA* dma = nullptr;
static uint16_t GREEN, BLACK;
static int      rotationOffset = 0;

// ── ESP-NOW receive buffer ────────────────────────────────────────────────
// The callback runs in the WiFi task context — keep it short.
// Copy data and set a flag; process in loop().
static volatile bool cmdPending = false;
static char          cmdBuf[32] = {0};

// ── Drawing (identical to panorama renderer) ─────────────────────────────────

static inline void putV(int vx, int vy, uint16_t c) {
  if (vy &lt; 0 || vy &gt;= VIRTUAL_H) return;
  vx = ((vx + rotationOffset) % VIRTUAL_W + VIRTUAL_W) % VIRTUAL_W;
  int panel = vx &gt;&gt; 5;
  int lx    = vx &amp; 31;
  int ly    = vy;
#if REVERSE_CHAIN
  panel = (PANELS_IN_CHAIN - panel) % PANELS_IN_CHAIN;
#endif
  int nx, ny;
#if ROTATE_CW
  nx = ly;       ny = 31 - lx;
#else
  nx = 63 - ly;  ny = lx;
#endif
  dma-&gt;drawPixel(panel * 64 + nx, ny, c);
}

static inline void fillRect(int x0, int y0, int x1, int y1, uint16_t c, int offX = 0) {
  for (int x = x0; x &lt;= x1; x++)
    for (int y = y0; y &lt;= y1; y++)
      putV(offX + x, y, c);
}

static inline void fillPgram(int xTop0, int xTop1, int y0, int y1, int slant,
                              uint16_t c, int offX = 0) {
  int dy = y1 - y0;
  if (dy &lt;= 0) return;
  for (int y = y0; y &lt;= y1; y++) {
    int shift = ((y - y0) * slant) / dy;
    for (int x = xTop0 + shift; x &lt;= xTop1 + shift; x++)
      putV(offX + x, y, c);
  }
}

static inline void fillStripes(int x0, int x1, int offX = 0) {
  fillRect(x0,  0, x1, 10, GREEN, offX);
  fillRect(x0, 22, x1, 31, GREEN, offX);
}

static void drawPanel1(int offX)      { fillRect(11, 0, 21, 30, GREEN, offX); }
static void drawPanel2(int offX)      { fillRect(0, 0, 10, 30, GREEN, offX); fillRect(21, 0, 31, 30, GREEN, offX); }
static void drawPanels3and4(int offX) {
  fillPgram(11, 21, 0, 31, -11, GREEN, offX);
  fillPgram(32, 42, 0, 31, -11, GREEN, offX);
  fillPgram(53, 63, 0, 31, -11, GREEN, offX);
}
static void drawPanel5(int offX)  { fillPgram(11, 21, 0, 31, -11, GREEN, offX); fillStripes(22, 31, offX); }
static void drawPanel6(int offX)  { fillStripes(0, 31, offX); }
static void drawPanel7(int offX)  { fillStripes(0, 31, offX); }
static void drawPanel8(int offX)  { fillStripes(0, 11, offX); fillRect(22, 0, 31, 30, GREEN, offX); }

static void drawPanorama() {
  fillRect(0, 0, VIRTUAL_W - 1, VIRTUAL_H - 1, BLACK);
  drawPanel1(0); drawPanel2(32); drawPanels3and4(64);
  drawPanel5(128); drawPanel6(160); drawPanel7(192); drawPanel8(224);
}

static void applyState(char state) {
  switch (state) {
    case &#x27;A&#x27;: rotationOffset = 192; break;
    case &#x27;B&#x27;: rotationOffset =   0; break;
    case &#x27;C&#x27;: rotationOffset =  64; break;
    case &#x27;D&#x27;: rotationOffset = 128; break;
    default:
      Serial.print(F(&quot;[DISPLAY] Unknown state: &quot;)); Serial.println(state);
      return;
  }
  drawPanorama();
  Serial.print(F(&quot;[DISPLAY] Showing state &quot;)); Serial.println(state);
}

static void clearDisplay() {
  dma-&gt;clearScreen();
  Serial.println(F(&quot;[DISPLAY] Display off&quot;));
}

// ── Command handler ────────────────────────────────────────────────────────

static void handleCommand(const String&amp; cmd) {
  if (cmd == &quot;OFF&quot;) {
    clearDisplay();
  } else if (cmd.length() == 7 &amp;&amp; cmd.startsWith(&quot;STATE:&quot;)) {
    char s = cmd.charAt(6);
    if (s == &#x27;A&#x27; || s == &#x27;B&#x27; || s == &#x27;C&#x27; || s == &#x27;D&#x27;) applyState(s);
    else { Serial.print(F(&quot;[DISPLAY] Bad state char: &quot;)); Serial.println(s); }
  } else {
    Serial.print(F(&quot;[DISPLAY] Unknown command: &quot;)); Serial.println(cmd);
  }
}

// ── ESP-NOW receive callback ──────────────────────────────────────────────
// NOTE: If this fails to compile, you are on arduino-esp32 2.x.
// Replace the first parameter with:  const uint8_t *mac_addr

static void onDataRecv(const esp_now_recv_info_t* info,
                       const uint8_t* data, int len) {
  if (len &gt; 0 &amp;&amp; len &lt; (int)sizeof(cmdBuf)) {
    memcpy(cmdBuf, data, len);
    cmdBuf[len] = &#x27;\0&#x27;;
    cmdPending = true;
  }
}

// ── setup ─────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(50);

  // WiFi in STA mode — no connection, just uses the radio for ESP-NOW
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, true);   // don&#x27;t reconnect, preserve MAC
  delay(100);

  // Lock to the same channel as the experiment controller&#x27;s AP
  esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

  Serial.print(F(&quot;[DISPLAY] MAC address: &quot;));
  Serial.println(WiFi.macAddress());   // &lt;-- copy this into experiment controller DISPLAY_MAC[]
  Serial.print(F(&quot;[DISPLAY] Channel: &quot;)); Serial.println(ESPNOW_CHANNEL);

  // ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println(F(&quot;[ESP-NOW] Init FAILED — halting&quot;));
    while (true) delay(1000);
  }
  esp_now_register_recv_cb(onDataRecv);
  Serial.println(F(&quot;[ESP-NOW] Ready.&quot;));

  // LED matrix
  HUB75_I2S_CFG mxconfig(64, 32, PANELS_IN_CHAIN, pins);
  mxconfig.driver           = HUB75_I2S_CFG::FM6126A;
  mxconfig.clkphase         = false;
  mxconfig.min_refresh_rate = 1000;
  mxconfig.double_buff = false;
  
  dma = new MatrixPanel_I2S_DMA(mxconfig);
  dma-&gt;begin();
  dma-&gt;setBrightness8(120);

  GREEN = dma-&gt;color565(0, 255, 0);
  BLACK = dma-&gt;color565(0,   0, 0);

  clearDisplay();
  Serial.println(F(&quot;[DISPLAY] Ready. Waiting for experiment controller commands.&quot;));
}

// ── Serial command handler (standalone testing, no experiment controller needed) ────────

static void handleSerial() {
  static String buf;

  while (Serial.available()) {
    char c = (char)Serial.read();

    if (c == &#x27;\n&#x27; || c == &#x27;\r&#x27;) {
      buf.trim();
      if (buf.length() &gt; 0) {
        buf.toUpperCase();
        if (buf == &quot;OFF&quot;) {
          clearDisplay();
        } else if (buf.length() == 1 &amp;&amp;
                   (buf[0] == &#x27;A&#x27; || buf[0] == &#x27;B&#x27; || buf[0] == &#x27;C&#x27; || buf[0] == &#x27;D&#x27;)) {
          applyState(buf[0]);
        } else {
          Serial.print(F(&quot;[DISPLAY] Unknown command: &quot;)); Serial.println(buf);
        }
      }
      buf = &quot;&quot;;      // reset for next line, regardless of \n vs \r vs \r\n
    } else {
      buf += c;
      if (buf.length() &gt; 31) buf = &quot;&quot;;   // guard against runaway garbage
    }
  }
}

// ── loop ──────────────────────────────────────────────────────────────────

void loop() {
  handleSerial();

  if (cmdPending) {
    cmdPending = false;
    String cmd = String(cmdBuf);
    cmd.trim();
    if (cmd.length() &gt; 0) handleCommand(cmd);
  }
}
</code></pre>
</details>
