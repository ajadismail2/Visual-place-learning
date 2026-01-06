/*
  ESP32 UART Temperature Receiver Test - FINAL
  File: test_uart_receiver.ino
  
  PURPOSE: Test UART communication from PyBadge
  - Receives temperature data via UART
  - Displays temperatures in Serial Monitor
  - Verifies data transfer is working correctly
  
  WIRING:
  - ESP32 RX (GPIO 16) ← PyBadge TX (A1)
  - ESP32 TX (GPIO 17) → PyBadge RX (A0)
  - ESP32 GND ↔ PyBadge GND
  
  EXPECTED FORMAT FROM PYBADGE:
  TEMP:A:35.2,B:36.1,C:35.8,D:36.3
  
  UPLOAD INSTRUCTIONS:
  1. Open Arduino IDE
  2. Select Board: "ESP32 Dev Module"
  3. Select Port: Your ESP32 COM port
  4. Upload this sketch
  5. Open Serial Monitor (115200 baud)
  6. Watch for temperature data from PyBadge
*/

#include <HardwareSerial.h>

// ===== UART Configuration =====
HardwareSerial SerialPyBadge(1);
#define RX_PIN 16
#define TX_PIN 17
#define BAUD_RATE 115200

// ===== Temperature Storage =====
struct PeltierTemp {
  char label;
  float temperature;
  bool updated;
  unsigned long lastUpdate;
};

PeltierTemp peltiers[4] = {
  {'A', 0.0, false, 0},
  {'B', 0.0, false, 0},
  {'C', 0.0, false, 0},
  {'D', 0.0, false, 0}
};

// Statistics
unsigned long packetsReceived = 0;
unsigned long lastPacketTime = 0;
unsigned long startTime = 0;

// ===== Function Prototypes =====
void parseTemperatures(String data);
void printTemperatures();
void printStatistics();

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  SerialPyBadge.begin(BAUD_RATE, SERIAL_8N1, RX_PIN, TX_PIN);
  
  delay(1000);
  
  Serial.println();
  Serial.println("================================================");
  Serial.println("ESP32 UART TEMPERATURE RECEIVER TEST");
  Serial.println("================================================");
  Serial.println("Waiting for data from PyBadge...");
  Serial.println("Expected format: TEMP:A:XX.X,B:XX.X,C:XX.X,D:XX.X");
  Serial.println();
  Serial.println("UART Configuration:");
  Serial.println("  RX Pin: GPIO 16");
  Serial.println("  TX Pin: GPIO 17");
  Serial.println("  Baud Rate: 115200");
  Serial.println("================================================");
  Serial.println();
  
  startTime = millis();
}

// ===== MAIN LOOP =====
void loop() {
  // Check for incoming data from PyBadge
  if (SerialPyBadge.available()) {
    String incoming = SerialPyBadge.readStringUntil('\n');
    incoming.trim();
    
    if (incoming.length() > 0) {
      // Record packet time
      lastPacketTime = millis();
      packetsReceived++;
      
      // Print raw received data
      Serial.println();
      Serial.println("--- RAW DATA ---");
      Serial.print("Received: ");
      Serial.println(incoming);
      
      // Parse temperature data
      if (incoming.startsWith("TEMP:")) {
        parseTemperatures(incoming);
        printTemperatures();
      }
      else if (incoming.startsWith("PYBADGE_TEST_READY")) {
        Serial.println();
        Serial.println("✓ PyBadge handshake received!");
        Serial.println("  PyBadge is ready to send temperature data");
      }
      else {
        Serial.println("  (Unknown format - ignoring)");
      }
    }
  }
  
  // Print statistics every 5 seconds
  static unsigned long lastStatsTime = 0;
  if (millis() - lastStatsTime > 5000) {
    if (packetsReceived > 0) {
      printStatistics();
    }
    lastStatsTime = millis();
  }
  
  // Check for timeout (no data for 3 seconds)
  if (packetsReceived > 0 && (millis() - lastPacketTime > 3000)) {
    Serial.println();
    Serial.println("⚠️  WARNING: No data received for 3 seconds!");
    Serial.println("   Check UART connections:");
    Serial.println("   - PyBadge TX (A1) → ESP32 RX (GPIO 16)");
    Serial.println("   - PyBadge GND → ESP32 GND");
    Serial.println("   - Both devices powered on");
    delay(1000);  // Don't spam warnings
  }
  
  delay(10);
}

// ===== Parse Temperature Data =====
void parseTemperatures(String data) {
  // Format: TEMP:A:35.2,B:36.1,C:35.8,D:36.3
  int startIdx = data.indexOf(':') + 1;
  
  while (startIdx < data.length()) {
    int labelIdx = startIdx;
    int colon = data.indexOf(':', labelIdx);
    int comma = data.indexOf(',', colon);
    
    if (colon < 0) break;
    
    char label = data.charAt(labelIdx);
    float temp = data.substring(colon + 1, comma > 0 ? comma : data.length()).toFloat();
    
    // Update matching Peltier
    for (int i = 0; i < 4; i++) {
      if (peltiers[i].label == label) {
        peltiers[i].temperature = temp;
        peltiers[i].updated = true;
        peltiers[i].lastUpdate = millis();
        break;
      }
    }
    
    if (comma < 0) break;
    startIdx = comma + 1;
  }
}

// ===== Print Temperatures =====
void printTemperatures() {
  Serial.println();
  Serial.println("--- PARSED TEMPERATURES ---");
  
  for (int i = 0; i < 4; i++) {
    Serial.print("Peltier ");
    Serial.print(peltiers[i].label);
    Serial.print(": ");
    
    if (peltiers[i].updated) {
      Serial.print(peltiers[i].temperature, 1);
      Serial.print("°C");
      
      // Show temperature range indicator
      if (peltiers[i].temperature >= 34.5 && peltiers[i].temperature <= 35.5) {
        Serial.print("  [HEAT TARGET ✓]");
      } else if (peltiers[i].temperature >= 24.5 && peltiers[i].temperature <= 25.5) {
        Serial.print("  [COOL TARGET ✓]");
      } else if (peltiers[i].temperature < 20.0) {
        Serial.print("  [TOO COLD]");
      } else if (peltiers[i].temperature > 40.0) {
        Serial.print("  [TOO HOT]");
      }
    } else {
      Serial.print("No data yet");
    }
    
    Serial.println();
  }
  
  // Print packet info
  Serial.println();
  Serial.print("Packet #");
  Serial.print(packetsReceived);
  Serial.print(" | Time since start: ");
  Serial.print((millis() - startTime) / 1000);
  Serial.println(" seconds");
}

// ===== Print Statistics =====
void printStatistics() {
  Serial.println();
  Serial.println("------------------------------------------------");
  Serial.println("STATISTICS:");
  Serial.print("  Total packets received: ");
  Serial.println(packetsReceived);
  Serial.print("  Uptime: ");
  Serial.print((millis() - startTime) / 1000);
  Serial.println(" seconds");
  Serial.print("  Average rate: ");
  Serial.print((float)packetsReceived / ((millis() - startTime) / 1000.0), 1);
  Serial.println(" packets/second");
  Serial.println("  Expected rate: 2.0 packets/second");
  
  // Check if all Peltiers have been updated
  bool allUpdated = true;
  for (int i = 0; i < 4; i++) {
    if (!peltiers[i].updated) {
      allUpdated = false;
      break;
    }
  }
  
  if (allUpdated) {
    Serial.println("  Status: ✓ All 4 Peltiers receiving data");
  } else {
    Serial.print("  Status: ⚠️  Some Peltiers missing data (");
    int count = 0;
    for (int i = 0; i < 4; i++) {
      if (peltiers[i].updated) count++;
    }
    Serial.print(count);
    Serial.println("/4 active)");
  }
  
  Serial.println("------------------------------------------------");
  Serial.println();
}