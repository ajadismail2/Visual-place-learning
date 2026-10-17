#include <Wire.h>
#include <Adafruit_MLX90640.h>

Adafruit_MLX90640 mlx;

float frame[32 * 24];

// Frame header
const uint8_t HEADER1 = 0xAA;
const uint8_t HEADER2 = 0x55;

void setup() {
  Serial.begin(921600);

  // ESP32 I2C pins
  Wire.begin(21, 22);

  // MLX90640 supports high-speed I2C
  Wire.setClock(1000000);

  delay(100);

  if (!mlx.begin(0x33, &Wire)) {
    Serial.println("MLX90640 NOT FOUND");
    while (1) {
      delay(1000);
    }
  }

  // Chess mode is recommended
  mlx.setMode(MLX90640_CHESS);

  // 18-bit resolution
  mlx.setResolution(MLX90640_ADC_18BIT);

  // Start at 8 Hz
  mlx.setRefreshRate(MLX90640_8_HZ);

  delay(100);

  // Send a startup message
  Serial.println("MLX90640_READY");
}

void loop() {

  // Read complete 32x24 frame
  if (mlx.getFrame(frame) != 0) {
    return;
  }

  // Send frame header
  Serial.write(HEADER1);
  Serial.write(HEADER2);

  // Send 768 temperatures
  for (int i = 0; i < 768; i++) {

    // Convert °C to hundredths of °C
    // Example:
    // 36.25 °C -> 3625
    int16_t temp = (int16_t)(frame[i] * 100.0f);

    // Little-endian transmission
    Serial.write((uint8_t)(temp & 0xFF));
    Serial.write((uint8_t)((temp >> 8) & 0xFF));
  }
}