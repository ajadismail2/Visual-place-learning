---
title: Thermal camera stream
description: "An MLX90640 supplies a temperature image for measurement; it does not close the Peltier-plate control loop."
section: Software
---
[← Controller programs](how-the-programs-work.md)

<div class="download-links" markdown="1">

[Download thermal_camera.ino](../downloads/firmware/thermal_camera/thermal_camera.ino){: download="thermal_camera.ino" } · [All sketches (.zip)](../downloads/arena-firmware-2026-10-17.zip)

</div>

The MLX90640 streams **32 × 24 temperature frames** over USB serial, independently of Peltier-plate control.

## Connections and output

| Connection or setting | Value |
| --- | --- |
| ESP32 SDA / SCL | GPIO 21 / 22 |
| Sensor address | 0x33 |
| Refresh setting | 8 Hz |
| Serial rate | 921600 baud |
| Packet | AA 55 header, then 768 signed 16-bit values |
| Conversion | Little-endian integer ÷ 100 gives °C |

Decode each 1,538-byte binary packet using the scale above. Failed frames are skipped.

Requires Adafruit_MLX90640. Validate calibration and optical access before measurement.

## Full source

<details class="source-code">
<summary>Read thermal_camera.ino · 68 lines</summary>
<pre tabindex="0" aria-label="thermal_camera.ino source code"><code>#include &lt;Wire.h&gt;
#include &lt;Adafruit_MLX90640.h&gt;

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

  if (!mlx.begin(0x33, &amp;Wire)) {
    Serial.println(&quot;MLX90640 NOT FOUND&quot;);
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
  Serial.println(&quot;MLX90640_READY&quot;);
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
  for (int i = 0; i &lt; 768; i++) {

    // Convert °C to hundredths of °C
    // Example:
    // 36.25 °C -&gt; 3625
    int16_t temp = (int16_t)(frame[i] * 100.0f);

    // Little-endian transmission
    Serial.write((uint8_t)(temp &amp; 0xFF));
    Serial.write((uint8_t)((temp &gt;&gt; 8) &amp; 0xFF));
  }
}</code></pre>
</details>
