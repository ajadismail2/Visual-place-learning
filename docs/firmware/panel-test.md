---
title: Single-panel test
description: "A small display diagnostic separates wiring and panel problems from experiment sequencing."
section: Software
---
[← Controller programs](index.md)

<div class="download-links" markdown="1">

[Download SinglePanelTest.ino](../downloads/firmware/SinglePanelTest/SinglePanelTest.ino){: download="SinglePanelTest.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

Use this program to test one panel before connecting the full enclosure. It uses the same HUB75 pin map as the display program.

## Test commands

| Command | Test |
| --- | --- |
| R / G / B / W | Solid colour |
| K | Blank |
| C | Checkerboard |
| H / V | Row / column sweep |
| X | Corners and edges |
| A | Automatic sequence |

Send commands at 115200 baud. These patterns check colours, address lines and orientation. Flashing this test replaces the LED-slave program on that board.

[Display pin map](../build/wiring.md#display-board-pin-map)

## Full source

<details class="source-code">
<summary>Read SinglePanelTest.ino · 199 lines</summary>
<pre tabindex="0" aria-label="SinglePanelTest.ino source code"><code>// Single-panel PCB test for a 64x32 HUB75 panel on DOIT ESP32 DevKit V1.
// Open Serial Monitor at 115200 baud and send a command letter to jump to
// a specific test, or leave it alone and tests cycle automatically every 3                                                                                                                               s.
//
// Commands:
//   R  — solid red
//   G  — solid green
//   B  — solid blue
//   W  — solid white
//   K  — blank (all off)
//   C  — checkerboard (2x2 blocks)
//   H  — horizontal row sweep
//   V  — vertical column sweep
//   X  — corner + edge dot test
//   A  — auto-cycle through all tests (default)

#include &lt;ESP32-HUB75-MatrixPanel-I2S-DMA.h&gt;

#define PANEL_W  64
#define PANEL_H  32

// ---- Pin mapping — adjust if your PCB differs from panorama renderer ----
HUB75_I2S_CFG::i2s_pins pins = {
    /*R1=*/  2, /*G1=*/ 15, /*B1=*/  4,
    /*R2=*/ 16, /*G2=*/ 27, /*B2=*/ 17,
    /*A =*/  5, /*B =*/ 18, /*C =*/ 19, /*D =*/ 21, /*E =*/ 12,
    /*LAT=*/ 25, /*OE =*/ 26, /*CLK=*/ 22
};

MatrixPanel_I2S_DMA *dma = nullptr;

uint16_t RED, GREEN, BLUE, WHITE, BLACK, YELLOW, CYAN, MAGENTA;

bool autoMode = true;
int  autoStep = 0;
unsigned long lastAutoMs = 0;
#define AUTO_INTERVAL_MS 3000UL

// ---- Test patterns -------------------------------------------------------

void testSolid(uint16_t color, const char *name) {
    dma-&gt;fillScreenRGB888(0, 0, 0);   // clear first to avoid ghost pixels
    dma-&gt;fillRect(0, 0, PANEL_W, PANEL_H, color);
    Serial.print(&quot;Solid: &quot;); Serial.println(name);
}

void testCheckerboard() {
    for (int y = 0; y &lt; PANEL_H; y++)
        for (int x = 0; x &lt; PANEL_W; x++)
            dma-&gt;drawPixel(x, y, ((x / 2 + y / 2) % 2) ? WHITE : BLACK);
    Serial.println(&quot;Checkerboard 2x2&quot;);
}

void testRowSweep() {
    // Sweep one lit row across the panel from top to bottom
    Serial.println(&quot;Row sweep (top -&gt; bottom)&quot;);
    for (int row = 0; row &lt; PANEL_H; row++) {
        dma-&gt;fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
        dma-&gt;drawFastHLine(0, row, PANEL_W, GREEN);
        delay(120);
    }
}

void testColSweep() {
    // Sweep one lit column across the panel from left to right
    Serial.println(&quot;Column sweep (left -&gt; right)&quot;);
    for (int col = 0; col &lt; PANEL_W; col++) {
        dma-&gt;fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
        dma-&gt;drawFastVLine(col, 0, PANEL_H, RED);
        delay(60);
    }
}

void testCorners() {
    // Lights the four corners and mid-edge points so you can verify geometry
    dma-&gt;fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
    dma-&gt;drawPixel(0,           0,           RED);      // top-left
    dma-&gt;drawPixel(PANEL_W - 1, 0,           GREEN);    // top-right
    dma-&gt;drawPixel(0,           PANEL_H - 1, BLUE);     // bottom-left
    dma-&gt;drawPixel(PANEL_W - 1, PANEL_H - 1, WHITE);   // bottom-right
    // mid-edges
    dma-&gt;drawPixel(PANEL_W / 2, 0,           YELLOW);  // top-mid
    dma-&gt;drawPixel(PANEL_W / 2, PANEL_H - 1, CYAN);    // bottom-mid
    dma-&gt;drawPixel(0,           PANEL_H / 2, MAGENTA); // left-mid
    dma-&gt;drawPixel(PANEL_W - 1, PANEL_H / 2, WHITE);   // right-mid
    Serial.println(&quot;Corners + mid-edges (R=TL, G=TR, B=BL, W=BR, Y=Tmid, C=Bmid, M=Lmid, W=Rmid)&quot;);
}

void testRainbow() {
    // Vertical color gradient across the width
    for (int x = 0; x &lt; PANEL_W; x++) {
        uint8_t hue = (uint8_t)((x * 255) / (PANEL_W - 1));
        // Simple HSV-&gt;RGB for hue only (full S and V)
        uint8_t r, g, b;
        uint8_t region = hue / 43;
        uint8_t rem    = (hue - region * 43) * 6;
        uint8_t q = 255 - rem;
        uint8_t t = rem;
        switch (region) {
            case 0: r = 255; g = t;   b = 0;   break;
            case 1: r = q;   g = 255; b = 0;   break;
            case 2: r = 0;   g = 255; b = t;   break;
            case 3: r = 0;   g = q;   b = 255; break;
            case 4: r = t;   g = 0;   b = 255; break;
            default:r = 255; g = 0;   b = q;   break;
        }
        uint16_t c = dma-&gt;color565(r, g, b);
        dma-&gt;drawFastVLine(x, 0, PANEL_H, c);
    }
    Serial.println(&quot;Rainbow gradient&quot;);
}

// ---- Auto-cycle list -----------------------------------------------------

void runAutoStep(int step) {
    switch (step % 9) {
        case 0: testSolid(RED,    &quot;red&quot;);    break;
        case 1: testSolid(GREEN,  &quot;green&quot;);  break;
        case 2: testSolid(BLUE,   &quot;blue&quot;);   break;
        case 3: testSolid(WHITE,  &quot;white&quot;);  break;
        case 4: testCheckerboard();           break;
        case 5: testRowSweep();               break;
        case 6: testColSweep();               break;
        case 7: testCorners();                break;
        case 8: testRainbow();                break;
    }
}

// --------------------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    delay(50);

    HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, 1 /*panels in chain*/, pins);
    mxconfig.driver        = HUB75_I2S_CFG::FM6126A;
    mxconfig.clkphase      = false;
    mxconfig.min_refresh_rate = 250;

    dma = new MatrixPanel_I2S_DMA(mxconfig);
    dma-&gt;begin();
    dma-&gt;setBrightness8(120);
    dma-&gt;clearScreen();

    RED     = dma-&gt;color565(255,   0,   0);
    GREEN   = dma-&gt;color565(  0, 255,   0);
    BLUE    = dma-&gt;color565(  0,   0, 255);
    WHITE   = dma-&gt;color565(255, 255, 255);
    BLACK   = dma-&gt;color565(  0,   0,   0);
    YELLOW  = dma-&gt;color565(255, 255,   0);
    CYAN    = dma-&gt;color565(  0, 255, 255);
    MAGENTA = dma-&gt;color565(255,   0, 255);

    Serial.println();
    Serial.println(&quot;=== Single-panel PCB test ===&quot;);
    Serial.println(&quot;Commands: R G B W K C H V X  — jump to test&quot;);
    Serial.println(&quot;          A                  — resume auto-cycle&quot;);
    Serial.println(&quot;Auto-cycling every 3 s ...&quot;);

    runAutoStep(autoStep);
    lastAutoMs = millis();
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == &#x27;\r&#x27; || c == &#x27;\n&#x27;) continue;
        if (c &gt;= &#x27;a&#x27; &amp;&amp; c &lt;= &#x27;z&#x27;) c -= 32;

        autoMode = false;
        switch (c) {
            case &#x27;R&#x27;: testSolid(RED,   &quot;red&quot;);   break;
            case &#x27;G&#x27;: testSolid(GREEN, &quot;green&quot;); break;
            case &#x27;B&#x27;: testSolid(BLUE,  &quot;blue&quot;);  break;
            case &#x27;W&#x27;: testSolid(WHITE, &quot;white&quot;); break;
            case &#x27;K&#x27;: testSolid(BLACK, &quot;black&quot;); Serial.println(&quot;Blank&quot;); break;
            case &#x27;C&#x27;: testCheckerboard();         break;
            case &#x27;H&#x27;: testRowSweep();             break;
            case &#x27;V&#x27;: testColSweep();             break;
            case &#x27;X&#x27;: testCorners();              break;
            case &#x27;A&#x27;:
                autoMode = true;
                autoStep = 0;
                lastAutoMs = millis();
                Serial.println(&quot;Auto-cycle resumed&quot;);
                runAutoStep(autoStep);
                break;
            default:
                Serial.print(&quot;Unknown command: &quot;); Serial.println(c);
                break;
        }
    }

    if (autoMode &amp;&amp; (millis() - lastAutoMs &gt;= AUTO_INTERVAL_MS)) {
        autoStep++;
        runAutoStep(autoStep);
        lastAutoMs = millis();
    }
}
</code></pre>
</details>
