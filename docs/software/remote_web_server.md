# Web-Based Remote Control System

Control the entire visual place learning arena remotely through a web interface powered by a Raspberry Pi server. This system allows researchers to run experiments, adjust parameters, and monitor status from any device connected to the lab WiFi network.

![Web Control Interface](images/web_interface_screenshot.jpg)
*Web interface for arena control accessible from laptop, tablet, or smartphone*

---

## System Architecture

### Overview

The Raspberry Pi acts as a central control hub, hosting a web server that communicates with both ESP32 microcontrollers (thermal and visual display) via serial connections.

```
┌─────────────────┐
│   Your Device   │ (Laptop/Tablet/Phone)
│  Web Browser    │
└────────┬────────┘
         │ WiFi
         ▼
┌─────────────────┐
│  Raspberry Pi   │
│   Web Server    │
│  (Flask/Node)   │
└───┬─────────┬───┘
    │         │ USB Serial
    │         │
    ▼         ▼
┌────────┐  ┌──────────┐
│Thermal │  │ Display  │
│ ESP32  │  │  ESP32   │
└────────┘  └──────────┘
    │            │
    ▼            ▼
┌────────┐  ┌──────────┐
│Peltiers│  │LED Panels│
└────────┘  └──────────┘
```

### Why This Approach?

**Benefits**:
- **Remote operation**: Run experiments from outside the dark experimental room
- **Multi-user access**: Multiple researchers can monitor the same experiment
- **Data logging**: Raspberry Pi automatically logs all commands and system status
- **Mobile-friendly**: Control from smartphone or tablet
- **No specialized software**: Just need a web browser

---

## Hardware Requirements

### Components

| Component | Specification | Purpose |
|-----------|---------------|---------|
| Raspberry Pi | Model 3B+ or 4 (2GB+ RAM) | Web server host |
| microSD card | 16GB+ Class 10 | Operating system |
| USB cables | 2× USB-A to micro-USB | Connect to ESP32s |
| Power supply | 5V 3A USB-C/micro-USB | Power Raspberry Pi |
| WiFi router | Any 2.4/5GHz router | Local network |

**Optional**:
- Ethernet cable (for more stable connection than WiFi)
- Case for Raspberry Pi with cooling fan

![Raspberry Pi Setup](images/raspberry_pi_connections.jpg)
*Raspberry Pi connected to both ESP32 controllers via USB*

---

## Software Setup

### Step 1: Prepare Raspberry Pi

**Install Raspberry Pi OS**:
```bash
# Download Raspberry Pi OS Lite from raspberrypi.com/software
# Flash to microSD card using Raspberry Pi Imager
# Insert card and boot Raspberry Pi

# Connect via SSH (default credentials: pi/raspberry)
ssh pi@raspberrypi.local

# Update system
sudo apt update
sudo apt upgrade -y
```

**Enable WiFi** (if not using Ethernet):
```bash
# Edit WiFi configuration
sudo raspi-config
# Navigate to: System Options → Wireless LAN
# Enter SSID and password
```

### Step 2: Install Python and Dependencies

```bash
# Install Python packages
sudo apt install python3-pip python3-flask python3-serial -y

# Install additional libraries
pip3 install flask-socketio pyserial
```

### Step 3: Create Web Server Application

**Create project directory**:
```bash
mkdir ~/arena_controller
cd ~/arena_controller
```

**Save this as `server.py`**:
```python
from flask import Flask, render_template, request, jsonify
import serial
import time

app = Flask(__name__)

# Connect to ESP32 controllers
try:
    thermal_esp = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    display_esp = serial.Serial('/dev/ttyUSB1', 115200, timeout=1)
    print("Connected to ESP32 controllers")
except:
    print("Warning: ESP32 controllers not connected")
    thermal_esp = None
    display_esp = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_temperature', methods=['POST'])
def set_temperature():
    target_temp = request.json['temperature']
    if thermal_esp:
        thermal_esp.write(f"SET_TEMP:{target_temp}\n".encode())
        response = thermal_esp.readline().decode().strip()
        return jsonify({'status': 'success', 'response': response})
    return jsonify({'status': 'error', 'message': 'ESP32 not connected'})

@app.route('/rotate_display', methods=['POST'])
def rotate_display():
    angle = request.json['angle']
    if display_esp:
        display_esp.write(f"ROTATE:{angle}\n".encode())
        response = display_esp.readline().decode().strip()
        return jsonify({'status': 'success', 'response': response})
    return jsonify({'status': 'error', 'message': 'ESP32 not connected'})

@app.route('/start_trial', methods=['POST'])
def start_trial():
    quadrant = request.json['quadrant']
    # Send commands to both ESP32s
    if thermal_esp and display_esp:
        thermal_esp.write(f"COOL_TILE:{quadrant}\n".encode())
        display_esp.write(f"ROTATE:{quadrant * 90}\n".encode())
        return jsonify({'status': 'success', 'trial_started': True})
    return jsonify({'status': 'error', 'message': 'Controllers not ready'})

@app.route('/status', methods=['GET'])
def get_status():
    status = {
        'thermal_connected': thermal_esp is not None,
        'display_connected': display_esp is not None,
        'timestamp': time.time()
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Step 4: Create Web Interface

**Create templates directory**:
```bash
mkdir ~/arena_controller/templates
```

**Save this as `templates/index.html`**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Arena Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f0f0f0;
        }
        .control-panel {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover {
            background: #45a049;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background: #e7f3ff;
        }
        .quadrant-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="control-panel">
        <h1>🪰 Visual Place Learning Arena Control</h1>
        
        <div class="status" id="status">
            Checking connection...
        </div>

        <h2>Quick Start Trial</h2>
        <div class="quadrant-grid">
            <button onclick="startTrial(0)">Quadrant 1 (0°)</button>
            <button onclick="startTrial(1)">Quadrant 2 (90°)</button>
            <button onclick="startTrial(2)">Quadrant 3 (180°)</button>
            <button onclick="startTrial(3)">Quadrant 4 (270°)</button>
        </div>

        <h2>Manual Controls</h2>
        <button onclick="setTemp(25)">Cool Tile (25°C)</button>
        <button onclick="setTemp(36)">Warm Arena (36°C)</button>
        
        <h2>Display Control</h2>
        <button onclick="rotateDisplay(0)">Rotate 0°</button>
        <button onclick="rotateDisplay(90)">Rotate 90°</button>
        <button onclick="rotateDisplay(180)">Rotate 180°</button>
        <button onclick="rotateDisplay(270)">Rotate 270°</button>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    let statusDiv = document.getElementById('status');
                    if(data.thermal_connected && data.display_connected) {
                        statusDiv.innerHTML = '✅ System Ready';
                        statusDiv.style.background = '#d4edda';
                    } else {
                        statusDiv.innerHTML = '⚠️ Check ESP32 connections';
                        statusDiv.style.background = '#fff3cd';
                    }
                });
        }

        function startTrial(quadrant) {
            fetch('/start_trial', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({quadrant: quadrant})
            })
            .then(response => response.json())
            .then(data => {
                alert('Trial started in Quadrant ' + (quadrant + 1));
            });
        }

        function setTemp(temp) {
            fetch('/set_temperature', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({temperature: temp})
            })
            .then(response => response.json())
            .then(data => console.log('Temperature set:', data));
        }

        function rotateDisplay(angle) {
            fetch('/rotate_display', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({angle: angle})
            })
            .then(response => response.json())
            .then(data => console.log('Display rotated:', data));
        }

        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus();
    </script>
</body>
</html>
```

### Step 5: Auto-Start on Boot

**Create systemd service**:
```bash
sudo nano /etc/systemd/system/arena-controller.service
```

**Add this content**:
```ini
[Unit]
Description=Arena Controller Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/arena_controller
ExecStart=/usr/bin/python3 /home/pi/arena_controller/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start service**:
```bash
sudo systemctl enable arena-controller
sudo systemctl start arena-controller
```

---

## Usage

### Connecting to the Interface

1. **Find Raspberry Pi IP address**:
   ```bash
   hostname -I
   # Example output: 192.168.1.100
   ```

2. **Access from any device on same network**:
   - Open web browser
   - Navigate to: `http://192.168.1.100:5000`
   - Bookmark for easy access

![Mobile Interface](images/web_interface_mobile.jpg)
*Web interface works on smartphones and tablets*

### Running an Experiment

**Quick start**:
1. Click quadrant button (e.g., "Quadrant 1")
2. System automatically:
   - Positions cool tile in selected quadrant
   - Rotates visual display to match
3. Run 5-minute trial
4. Repeat for 10 trials

**Manual control**:
- Use temperature buttons to adjust thermal conditions
- Use rotation buttons to change visual display independently
- Monitor connection status in real-time

---

## ESP32 Serial Communication

### Command Protocol

Both ESP32s should implement a simple serial command parser:

**Example ESP32 code**:
```cpp
void setup() {
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    
    if (command.startsWith("SET_TEMP:")) {
      int temp = command.substring(9).toInt();
      setTargetTemperature(temp);
      Serial.println("OK:TEMP_SET");
    }
    else if (command.startsWith("ROTATE:")) {
      int angle = command.substring(7).toInt();
      rotateDisplay(angle);
      Serial.println("OK:DISPLAY_ROTATED");
    }
    else if (command.startsWith("COOL_TILE:")) {
      int quadrant = command.substring(10).toInt();
      activateCoolTile(quadrant);
      Serial.println("OK:COOL_TILE_ACTIVE");
    }
  }
}
```

---

## Troubleshooting

### Can't access web interface

**Check Raspberry Pi is on same network**:
```bash
ping raspberrypi.local
```

**Verify server is running**:
```bash
sudo systemctl status arena-controller
```

**Check firewall** (if enabled):
```bash
sudo ufw allow 5000
```

### ESP32 not responding

**Verify USB connections**:
```bash
ls /dev/ttyUSB*
# Should show /dev/ttyUSB0 and /dev/ttyUSB1
```

**Check permissions**:
```bash
sudo usermod -a -G dialout pi
# Logout and login for changes to take effect
```

**Test serial manually**:
```bash
screen /dev/ttyUSB0 115200
# Type commands manually to test ESP32 response
```

---

## Security Considerations

**For lab-internal use**:
- Default setup is adequate (only accessible on local network)
- Change default Raspberry Pi password: `passwd`

**For remote access** (advanced):
- Set up VPN to access lab network securely
- Add password authentication to Flask app
- Use HTTPS instead of HTTP

---

## Advantages of This System

✅ **Wireless operation** - Control arena without entering dark room  
✅ **Multi-device support** - Monitor from laptop while controlling from phone  
✅ **Automatic logging** - All commands timestamped and recorded  
✅ **Scalable** - Easy to add new controls and sensors  
✅ **No installation** - Works with any web browser  
✅ **Educational** - Great learning opportunity for web development  

---

## Bill of Materials

| Component | Cost (USD) |
|-----------|------------|
| Raspberry Pi 4 (2GB) | $35-45 |
| microSD card (32GB) | $8-12 |
| USB cables (2×) | $5-10 |
| Power supply | $8-12 |
| **Total** | **~$56-79** |

*WiFi router assumed to be already available in lab*

---

## References

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Raspberry Pi Setup**: https://www.raspberrypi.com/documentation/
- **Serial Communication**: https://pyserial.readthedocs.io/

---
