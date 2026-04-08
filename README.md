Smart HUD — AI-Powered Ambient Notification Display

Overview

Smart HUD is an embedded system that transforms desktop notifications into concise, meaningful summaries and displays them on a physical device in real time.

It combines:

- OS-level notification capture
- AI-based semantic summarization
- Cloud message transport (MQTT)
- Embedded display with tactile navigation

The result is a low-distraction, ambient interface for managing incoming information.

---

Features

- Notification Capture
  
  - Listens to system notifications via DBus (Linux)

- AI Summarization
  
  - Uses LLMs via OpenRouter to compress notifications into 3–6 word summaries
  - Preserves intent rather than raw wording

- Spam & Noise Filtering
  
  - Removes emoji floods, Unicode noise, and repeated words
  - Normalizes media (GIFs, stickers, etc.)

- Cloud Transport
  
  - Publishes summaries via MQTT (EMQX broker)

- Embedded Display
  
  - ESP32 + 16x2 I2C LCD
  - Real-time updates

- Tactile Navigation
  
  - Potentiometer-based scrolling through last 10 notifications

- Smooth Rendering
  
  - Flicker-free updates
  - Auto horizontal scrolling for long messages

---

Architecture

Desktop Notifications
        ↓
DBus Listener (Python)
        ↓
Sanitize + Summarize (LLM)
        ↓
MQTT (EMQX Broker)
        ↓
ESP32 (MicroPython)
        ↓
LCD Display + Knob Navigation

---

Hardware Requirements

- ESP32
- 16x2 I2C LCD (PCF8574, address 0x27)
- 10k potentiometer
- Breadboard + jumper wires

---

Wiring

LCD (I2C)

- VCC → 5V
- GND → GND
- SDA → GPIO 21
- SCL → GPIO 22

Potentiometer

- Left → GND
- Middle → GPIO 34
- Right → 3.3V

---

Software Requirements

Laptop

- Python 3.10+
- Linux (DBus required)

Install dependencies:

pip install requests python-dotenv paho-mqtt

ESP32

- MicroPython firmware
- "umqtt.simple"
- "pico_i2c_lcd.py"

---

Setup

1. Clone Repository

git clone https://github.com/yourusername/smart-hud
cd smart-hud

---

2. Configure API Key

Create ".env" file:

OPENROUTER_API_KEY=your_key_here

---

3. Run Laptop Server

python server.py

You should see:

Listening to desktop notification daemon...

---

4. Flash ESP32

Upload:

- "main.py"
- "pico_i2c_lcd.py"

---

5. Power On

- ESP32 connects to WiFi
- Subscribes to MQTT
- Displays "HUD Ready"
- Incoming notifications appear automatically

---

Example Output

Input (Notification):

Mom : Hello dont forget to eat snacks 😂😂😂

Output (HUD):

Mom snack reminder

---

Queue Behavior

- Stores last 10 notifications
- New messages appear at index 0
- Rotate potentiometer to browse history

---

Limitations

- Requires Linux (DBus)
- Relies on external LLM API
- 16x2 LCD limits visual richness
- No direct reply functionality (yet)

---

Future Improvements

- OLED / TFT display upgrade
- Quick reply buttons
- Gesture-based interaction
- Sender priority alerts
- Local summarization model
- Battery-powered enclosure

---

License

MIT License

---

Author

Aaron
