// LED_Slave.ino
// Receives state commands from Master_Controller via ESP-NOW (wireless)
// and displays the corresponding panorama rotation on the 8-panel
// HUB75 octagon column. No wires between boards needed.
//
// ── First-time setup ─────────────────────────────────────────────────────
//   1. Flash this sketch.
//   2. Open Serial Monitor at 115200 baud.
//   3. The slave prints its MAC address on boot — copy it into
//      SLAVE_MAC[] in Master_Controller.ino, then flash the master.
//
// ── Commands received from master ────────────────────────────────────────
//   OFF      → blank all panels
//   STATE:A  → rotation offset 192 px
//   STATE:B  → rotation offset   0 px
//   STATE:C  → rotation offset  64 px
//   STATE:D  → rotation offset 128 px
//
// All timing is controlled by the master. This board is purely reactive.
//
// ── Standalone testing over Serial Monitor (115200 baud) ─────────────────
//   Type A, B, C, D or OFF and press enter to preview a rotation without
//   the master board connected.

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>                 // for esp_wifi_set_channel
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

// ── Channel must match master AP_CHANNEL ─────────────────────────────────
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
  if (vy < 0 || vy >= VIRTUAL_H) return;
  vx = ((vx + rotationOffset) % VIRTUAL_W + VIRTUAL_W) % VIRTUAL_W;
  int panel = vx >> 5;
  int lx    = vx & 31;
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
  dma->drawPixel(panel * 64 + nx, ny, c);
}

static inline void fillRect(int x0, int y0, int x1, int y1, uint16_t c, int offX = 0) {
  for (int x = x0; x <= x1; x++)
    for (int y = y0; y <= y1; y++)
      putV(offX + x, y, c);
}

static inline void fillPgram(int xTop0, int xTop1, int y0, int y1, int slant,
                              uint16_t c, int offX = 0) {
  int dy = y1 - y0;
  if (dy <= 0) return;
  for (int y = y0; y <= y1; y++) {
    int shift = ((y - y0) * slant) / dy;
    for (int x = xTop0 + shift; x <= xTop1 + shift; x++)
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
    case 'A': rotationOffset = 192; break;
    case 'B': rotationOffset =   0; break;
    case 'C': rotationOffset =  64; break;
    case 'D': rotationOffset = 128; break;
    default:
      Serial.print(F("[SLAVE] Unknown state: ")); Serial.println(state);
      return;
  }
  drawPanorama();
  Serial.print(F("[SLAVE] Showing state ")); Serial.println(state);
}

static void clearDisplay() {
  dma->clearScreen();
  Serial.println(F("[SLAVE] Display off"));
}

// ── Command handler ────────────────────────────────────────────────────────

static void handleCommand(const String& cmd) {
  if (cmd == "OFF") {
    clearDisplay();
  } else if (cmd.length() == 7 && cmd.startsWith("STATE:")) {
    char s = cmd.charAt(6);
    if (s == 'A' || s == 'B' || s == 'C' || s == 'D') applyState(s);
    else { Serial.print(F("[SLAVE] Bad state char: ")); Serial.println(s); }
  } else {
    Serial.print(F("[SLAVE] Unknown command: ")); Serial.println(cmd);
  }
}

// ── ESP-NOW receive callback ──────────────────────────────────────────────
// NOTE: If this fails to compile, you are on arduino-esp32 2.x.
// Replace the first parameter with:  const uint8_t *mac_addr

static void onDataRecv(const esp_now_recv_info_t* info,
                       const uint8_t* data, int len) {
  if (len > 0 && len < (int)sizeof(cmdBuf)) {
    memcpy(cmdBuf, data, len);
    cmdBuf[len] = '\0';
    cmdPending = true;
  }
}

// ── setup ─────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(50);

  // WiFi in STA mode — no connection, just uses the radio for ESP-NOW
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, true);   // don't reconnect, preserve MAC
  delay(100);

  // Lock to the same channel as the master's AP
  esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

  Serial.print(F("[SLAVE] MAC address: "));
  Serial.println(WiFi.macAddress());   // <-- copy this into master SLAVE_MAC[]
  Serial.print(F("[SLAVE] Channel: ")); Serial.println(ESPNOW_CHANNEL);

  // ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println(F("[ESP-NOW] Init FAILED — halting"));
    while (true) delay(1000);
  }
  esp_now_register_recv_cb(onDataRecv);
  Serial.println(F("[ESP-NOW] Ready."));

  // LED matrix
  HUB75_I2S_CFG mxconfig(64, 32, PANELS_IN_CHAIN, pins);
  mxconfig.driver           = HUB75_I2S_CFG::FM6126A;
  mxconfig.clkphase         = false;
  mxconfig.min_refresh_rate = 1000;
  mxconfig.double_buff = false;
  
  dma = new MatrixPanel_I2S_DMA(mxconfig);
  dma->begin();
  dma->setBrightness8(120);

  GREEN = dma->color565(0, 255, 0);
  BLACK = dma->color565(0,   0, 0);

  clearDisplay();
  Serial.println(F("[SLAVE] Ready. Waiting for master commands."));
}

// ── Serial command handler (standalone testing, no master needed) ────────

static void handleSerial() {
  static String buf;

  while (Serial.available()) {
    char c = (char)Serial.read();

    if (c == '\n' || c == '\r') {
      buf.trim();
      if (buf.length() > 0) {
        buf.toUpperCase();
        if (buf == "OFF") {
          clearDisplay();
        } else if (buf.length() == 1 &&
                   (buf[0] == 'A' || buf[0] == 'B' || buf[0] == 'C' || buf[0] == 'D')) {
          applyState(buf[0]);
        } else {
          Serial.print(F("[SLAVE] Unknown command: ")); Serial.println(buf);
        }
      }
      buf = "";      // reset for next line, regardless of \n vs \r vs \r\n
    } else {
      buf += c;
      if (buf.length() > 31) buf = "";   // guard against runaway garbage
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
    if (cmd.length() > 0) handleCommand(cmd);
  }
}
