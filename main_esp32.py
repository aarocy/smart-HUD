import network
import time
import ujson
from umqtt.simple import MQTTClient
from machine import Pin, I2C, ADC
from pico_i2c_lcd import I2cLcd

# =========================
# WIFI
# =========================
WIFI_SSID = "Your_wifi_SSID"
WIFI_PASSWORD = "Your_password"

# =========================
# MQTT
# =========================
MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = b"aarondesk/v1/notifs"
CLIENT_ID = b"esp32_hud"

# =========================
# QUEUE + CACHE
# =========================
MAX_QUEUE = 25
CACHE_FILE = "notif_cache.json"

# =========================
# LCD
# =========================
I2C_ADDR = 0x27
ROWS = 2
COLS = 16

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, ROWS, COLS)
lcd.backlight_on()

# =========================
# INPUTS
# =========================
pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)

dismiss_btn = Pin(27, Pin.IN, Pin.PULL_UP)

# active-low 3-pin buzzer
buzzer = Pin(26, Pin.OUT)
buzzer.value(1)

# =========================
# STATE
# =========================
notifications = []
current_index = 0
stable_idx = 0
scroll_offset = 0
last_scroll = time.ticks_ms()
last_display = ""
last_button_press = 0
latest_lock_until = 0

# =========================
# CACHE
# =========================
def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            ujson.dump(notifications, f)
    except Exception as e:
        print("Cache save failed:", e)

def load_cache():
    global notifications
    try:
        with open(CACHE_FILE, "r") as f:
            notifications = ujson.load(f)
    except:
        notifications = []

# =========================
# WIFI
# =========================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        time.sleep(1)

# =========================
# BOOT ANIMATION
# =========================
def boot_animation():
    frames = [
        "SMART HUD      ",
        "> Initializing ",
        ">> Restoring   ",
        ">>> MQTT Link  ",
        "READY          "
    ]

    for frame in frames:
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr(frame[:16])
        lcd.move_to(0, 1)
        lcd.putstr("Ambient AI Desk")
        time.sleep(0.35)

# =========================
# BUZZER
# =========================
def beep(times=1, duration=120, gap=180):
    for _ in range(times):
        buzzer.value(0)
        time.sleep_ms(duration)
        buzzer.value(1)
        time.sleep_ms(gap)

# =========================
# DISPLAY
# =========================
def render_message(msg):
    global scroll_offset, last_scroll, last_display

    msg = str(msg)

    if msg.startswith("!! "):
        msg = msg[3:]
    elif msg.startswith("! "):
        msg = msg[2:]

    if len(msg) > 32:
        if time.ticks_diff(time.ticks_ms(), last_scroll) > 400:
            scroll_offset += 1
            if scroll_offset > len(msg):
                scroll_offset = 0
            last_scroll = time.ticks_ms()

        visible = msg[scroll_offset:scroll_offset + 32]
    else:
        visible = msg[:32]
        scroll_offset = 0

    if visible == last_display:
        return

    last_display = visible

    line1 = visible[:16]
    line2 = visible[16:32]

    line1 += " " * (16 - len(line1))
    line2 += " " * (16 - len(line2))

    lcd.move_to(0, 0)
    lcd.putstr(line1)

    lcd.move_to(0, 1)
    lcd.putstr(line2)

# =========================
# PRIORITY TRIM
# =========================
def trim_queue():
    while len(notifications) > MAX_QUEUE:
        # remove oldest normal first
        removed = False
        for i in range(len(notifications) - 1, -1, -1):
            item = notifications[i]
            if not item.startswith("!"):
                notifications.pop(i)
                removed = True
                break

        # if only priority items remain, remove oldest
        if not removed:
            notifications.pop()

# =========================
# MQTT CALLBACK
# =========================
def on_message(topic, msg):
    global current_index, stable_idx
    global scroll_offset, last_display
    global latest_lock_until

    decoded = msg.decode()
    print("Received:", decoded)

    # tiered buzzer
    if decoded.startswith("!!"):
        beep(3)
    elif decoded.startswith("!"):
        beep(2)
    else:
        beep(1)

    # priority-aware rerank
    if decoded.startswith("!!"):
        notifications.insert(0, decoded)

    elif decoded.startswith("!"):
        insert_at = 0
        while (
            insert_at < len(notifications)
            and notifications[insert_at].startswith("!!")
        ):
            insert_at += 1
        notifications.insert(insert_at, decoded)

    else:
        notifications.append(decoded)

    trim_queue()
    save_cache()

    current_index = 0
    stable_idx = 0
    scroll_offset = 0
    last_display = ""
    latest_lock_until = time.ticks_add(time.ticks_ms(), 2000)

# =========================
# POT STABILIZER
# =========================
def get_stable_index(count):
    global stable_idx

    if count <= 1:
        return 0

    total = 0
    for _ in range(5):
        total += pot.read()
        time.sleep_ms(2)

    value = total // 5
    idx = int((value / 4095) * count)

    if idx >= count:
        idx = count - 1

    if abs(idx - stable_idx) >= 1:
        stable_idx = idx

    return stable_idx

# =========================
# DISMISS
# =========================
def handle_dismiss():
    global current_index, stable_idx
    global scroll_offset, last_display
    global last_button_press

    if not notifications:
        return

    now = time.ticks_ms()

    if dismiss_btn.value() == 0 and time.ticks_diff(now, last_button_press) > 250:
        removed = notifications.pop(current_index)
        print("Dismissed:", removed)

        save_cache()

        if not notifications:
            lcd.clear()
            lcd.putstr("Inbox clear")
            current_index = 0
            stable_idx = 0
        else:
            if current_index >= len(notifications):
                current_index = len(notifications) - 1
            stable_idx = current_index

        scroll_offset = 0
        last_display = ""
        last_button_press = now

# =========================
# MAIN
# =========================
load_cache()
connect_wifi()

client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(on_message)
client.connect()
client.subscribe(MQTT_TOPIC)

boot_animation()

while True:
    client.check_msg()
    handle_dismiss()

    if notifications:
        if time.ticks_diff(latest_lock_until, time.ticks_ms()) > 0:
            idx = 0
        else:
            idx = get_stable_index(len(notifications))

        if idx != current_index:
            scroll_offset = 0
            last_display = ""

        current_index = idx
        render_message(notifications[current_index])

    time.sleep(0.1)
