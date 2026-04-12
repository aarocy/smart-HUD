# Smart HUD — AI-Powered Ambient Notification Display

## Overview
Smart HUD is an embedded ambient interface that captures desktop notifications, semantically compresses them using AI, and displays them on a dedicated physical screen in real time.

It combines:
- OS-level notification capture
- AI semantic summarization
- MQTT cloud transport
- ESP32 embedded rendering
- Tactile history navigation

The result is a low-distraction, glanceable notification surface for managing incoming information.

---

## Features

### Notification Capture
- Listens to Linux desktop notifications via **DBus**
- Extracts sender, title, and body

### AI Summarization
- Uses **LLMs through OpenRouter**
- Compresses notifications into **3–6 word semantic summaries**
- Preserves intent over literal wording

### Spam + Noise Filtering
- Removes emoji floods
- Strips Unicode noise
- Deduplicates repeated words
- Normalizes media placeholders

### Cloud Transport
- Publishes summaries through **MQTT**
- Uses **EMQX broker**

### Embedded Display
- **ESP32 + 16x2 I2C LCD**
- Real-time updates

### Tactile Navigation
- **10k potentiometer**
- Browse the **last 30 notifications**

### Smooth Rendering
- Flicker-free updates
- Horizontal scrolling for overflow text

---

## Architecture
Desktop Notifications  
↓  
Linux DBus Listener (Python)  
↓  
Sanitize + Summarize (LLM)  
↓  
MQTT Publish (EMQX)  
↓  
ESP32 Subscriber (MicroPython)  
↓  
16x2 LCD + Knob Navigation  

---

## Hardware Requirements
- ESP32
- 16x2 I2C LCD (PCF8574, address `0x27`)
- 10k potentiometer
- Breadboard
- Jumper wires

---

## Wiring

### LCD (I2C)
| LCD Pin | ESP32 |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Potentiometer
| Potentiometer Pin | ESP32 |
|---|---|
| Left | GND |
| Middle | GPIO 34 |
| Right | 3.3V |

---

## Software Requirements

### Laptop
- Python **3.10+**
- Linux with DBus notification daemon

Install:
```bash
pip install requests python-dotenv paho-mqtt
```

### ESP32
- MicroPython firmware
- `umqtt.simple`
- `pico_i2c_lcd.py`

---

## Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/smart-hud
cd smart-hud
```

### 2. Configure API Key
Create `.env`
```env
OPENROUTER_API_KEY=your_key_here
```

### 3. Run Laptop Server
```bash
python server.py
```

Expected output:
```text
Listening to desktop notification daemon...
```

### 4. Flash ESP32
Upload:
- `main.py`
- `pico_i2c_lcd.py`

### 5. Power On
Expected boot flow:
- Connects to WiFi (Don't forget to change the wifi ssid and password)
- Connects to MQTT
- Displays `HUD Ready`
- Streams summaries automatically

---

## Example Output

### Input Notification
```text
Mom: Hello dont forget to eat snacks <gif>
```

### HUD Output
```text
Mom snack reminder
```

---

## Queue Behavior
- Stores **last 10 notifications**
- New entries inserted at **index 0**
- Rotate potentiometer to browse history

---

## Limitations
- Linux only (DBus dependency)
- External LLM API dependency
- LCD constrained to 16x2 characters
- No reply support yet

---

## Future Improvements
- OLED / TFT display migration
- Quick reply buttons
- Gesture navigation
- Sender priority routing
- Local on-device summarization
- Battery-powered enclosure
- Notification category filtering

---

## License
MIT License

---

## Author
Aaron
