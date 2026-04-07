import subprocess
import re
import requests
import os
from collections import deque
from dotenv import load_dotenv
import paho.mqtt.publish as publish

# =========================
# ENV + CONFIG
# =========================
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY missing in .env")

MODELS = [
    "qwen/qwen3.6-plus:free",
    "minimax/minimax-m2.5:free",
    "nvidia/nemotron-3-super-120b-a12b:free"
]

MQTT_HOST = "broker.emqx.io"
MQTT_TOPIC = "aarondesk/v1/notifs"

# =========================
# START DAEMON LISTENER
# =========================
cmd = [
    "dbus-monitor",
    "interface='org.freedesktop.Notifications'"
]

print("Listening to desktop notification daemon...\n")

process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

buffer = []
notifications = deque(maxlen=10)

# =========================
# AI SUMMARIZER
# =========================
def summarize(text):
    prompt = (
        "Convert this notification context into a highly meaningful ultra-short LCD summary.\n"
        "Rules:\n"
        "- 3 to 6 words max\n"
        "- preserve sender/person if present\n"
        "- infer real intent\n"
        "- avoid copy-paste wording and dont use markdown or any other formatting\n"
        "- optimize for tiny display readability\n\n"
        f"{text}"
    )

    for model in MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You compress notification context into semantic LCD labels."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=15
            )

            data = response.json()

            if "choices" in data:
                print(f"LLM → {model}")
                result = data["choices"][0]["message"]["content"].strip()

                words = result.split()
                return " ".join(words[:6])

        except Exception:
            pass

    # local fallback
    words = text.split()
    return " ".join(words[:6])

# =========================
# MQTT PUSH
# =========================
def push_to_esp32(summary):
    try:
        publish.single(
            MQTT_TOPIC,
            summary,
            hostname=MQTT_HOST
        )
        print("Published to MQTT")
    except Exception as e:
        print("MQTT publish failed:", e)

# =========================
# PARSE NOTIFICATION
# =========================
def flush_notification(lines):
    strings = []

    for line in lines:
        if "array [" in line:
            break

        match = re.search(r'string "(.*)"', line)
        if match:
            strings.append(match.group(1))

    strings = [s.strip() for s in strings if s.strip()]

    if len(strings) >= 2:
        app = strings[0]

        # use all remaining strings as structured context
        content = " | ".join(strings[1:])

        summary = summarize(content)

        notif = {
            "app": app,
            "content": content,
            "summary": summary
        }

        notifications.appendleft(notif)

        push_to_esp32(summary)

        print(f"[{app}] {summary}")
        print(f"RAW → {content}")
        print(f"Queue size: {len(notifications)}")
        print("-" * 40)

# =========================
# MAIN LOOP
# =========================
try:
    for raw_line in process.stdout:
        line = raw_line.rstrip()

        if "member=Notify" in line:
            if buffer:
                flush_notification(buffer)
                buffer = []
            buffer.append(line)

        elif buffer:
            buffer.append(line)

except KeyboardInterrupt:
    print("\nStopped daemon listener.")
    process.terminate()