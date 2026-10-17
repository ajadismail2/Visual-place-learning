// Single-panel PCB test for a 64x32 HUB75 panel on DOIT ESP32 DevKit V1.
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

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

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
    dma->fillScreenRGB888(0, 0, 0);   // clear first to avoid ghost pixels
    dma->fillRect(0, 0, PANEL_W, PANEL_H, color);
    Serial.print("Solid: "); Serial.println(name);
}

void testCheckerboard() {
    for (int y = 0; y < PANEL_H; y++)
        for (int x = 0; x < PANEL_W; x++)
            dma->drawPixel(x, y, ((x / 2 + y / 2) % 2) ? WHITE : BLACK);
    Serial.println("Checkerboard 2x2");
}

void testRowSweep() {
    // Sweep one lit row across the panel from top to bottom
    Serial.println("Row sweep (top -> bottom)");
    for (int row = 0; row < PANEL_H; row++) {
        dma->fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
        dma->drawFastHLine(0, row, PANEL_W, GREEN);
        delay(120);
    }
}

void testColSweep() {
    // Sweep one lit column across the panel from left to right
    Serial.println("Column sweep (left -> right)");
    for (int col = 0; col < PANEL_W; col++) {
        dma->fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
        dma->drawFastVLine(col, 0, PANEL_H, RED);
        delay(60);
    }
}

void testCorners() {
    // Lights the four corners and mid-edge points so you can verify geometry
    dma->fillRect(0, 0, PANEL_W, PANEL_H, BLACK);
    dma->drawPixel(0,           0,           RED);      // top-left
    dma->drawPixel(PANEL_W - 1, 0,           GREEN);    // top-right
    dma->drawPixel(0,           PANEL_H - 1, BLUE);     // bottom-left
    dma->drawPixel(PANEL_W - 1, PANEL_H - 1, WHITE);   // bottom-right
    // mid-edges
    dma->drawPixel(PANEL_W / 2, 0,           YELLOW);  // top-mid
    dma->drawPixel(PANEL_W / 2, PANEL_H - 1, CYAN);    // bottom-mid
    dma->drawPixel(0,           PANEL_H / 2, MAGENTA); // left-mid
    dma->drawPixel(PANEL_W - 1, PANEL_H / 2, WHITE);   // right-mid
    Serial.println("Corners + mid-edges (R=TL, G=TR, B=BL, W=BR, Y=Tmid, C=Bmid, M=Lmid, W=Rmid)");
}

void testRainbow() {
    // Vertical color gradient across the width
    for (int x = 0; x < PANEL_W; x++) {
        uint8_t hue = (uint8_t)((x * 255) / (PANEL_W - 1));
        // Simple HSV->RGB for hue only (full S and V)
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
        uint16_t c = dma->color565(r, g, b);
        dma->drawFastVLine(x, 0, PANEL_H, c);
    }
    Serial.println("Rainbow gradient");
}

// ---- Auto-cycle list -----------------------------------------------------

void runAutoStep(int step) {
    switch (step % 9) {
        case 0: testSolid(RED,    "red");    break;
        case 1: testSolid(GREEN,  "green");  break;
        case 2: testSolid(BLUE,   "blue");   break;
        case 3: testSolid(WHITE,  "white");  break;
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
    dma->begin();
    dma->setBrightness8(120);
    dma->clearScreen();

    RED     = dma->color565(255,   0,   0);
    GREEN   = dma->color565(  0, 255,   0);
    BLUE    = dma->color565(  0,   0, 255);
    WHITE   = dma->color565(255, 255, 255);
    BLACK   = dma->color565(  0,   0,   0);
    YELLOW  = dma->color565(255, 255,   0);
    CYAN    = dma->color565(  0, 255, 255);
    MAGENTA = dma->color565(255,   0, 255);

    Serial.println();
    Serial.println("=== Single-panel PCB test ===");
    Serial.println("Commands: R G B W K C H V X  — jump to test");
    Serial.println("          A                  — resume auto-cycle");
    Serial.println("Auto-cycling every 3 s ...");

    runAutoStep(autoStep);
    lastAutoMs = millis();
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\r' || c == '\n') continue;
        if (c >= 'a' && c <= 'z') c -= 32;

        autoMode = false;
        switch (c) {
            case 'R': testSolid(RED,   "red");   break;
            case 'G': testSolid(GREEN, "green"); break;
            case 'B': testSolid(BLUE,  "blue");  break;
            case 'W': testSolid(WHITE, "white"); break;
            case 'K': testSolid(BLACK, "black"); Serial.println("Blank"); break;
            case 'C': testCheckerboard();         break;
            case 'H': testRowSweep();             break;
            case 'V': testColSweep();             break;
            case 'X': testCorners();              break;
            case 'A':
                autoMode = true;
                autoStep = 0;
                lastAutoMs = millis();
                Serial.println("Auto-cycle resumed");
                runAutoStep(autoStep);
                break;
            default:
                Serial.print("Unknown command: "); Serial.println(c);
                break;
        }
    }

    if (autoMode && (millis() - lastAutoMs >= AUTO_INTERVAL_MS)) {
        autoStep++;
        runAutoStep(autoStep);
        lastAutoMs = millis();
    }
}
