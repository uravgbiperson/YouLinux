"""
video player by Uravgbiperson

supports:
- YouTube link input
- Optional rebuild
- Auto download
- Auto frame generation
- Safe audio handling
"""

import numpy as np
import os
import time
import pygame
import sys
import subprocess
import shutil
from threading import Thread
from PIL import Image


# -------------------------
# Remote Control Threads
# -------------------------

def listen_for_pause():
    while True:
        if os.path.isfile("PAUSE.truconf"):
            os.remove("PAUSE.truconf")
            global stopped
            stopped = True
            pygame.mixer.music.pause()


def listen_for_unpause():
    while True:
        if os.path.isfile("UNPAUSE.truconf"):
            os.remove("UNPAUSE.truconf")
            pygame.mixer.music.unpause()
            global stopped
            stopped = False


def listen_for_disable():
    while True:
        if os.path.isfile("DISABLE.truconf"):
            os.remove("DISABLE.truconf")
            pygame.mixer.quit()


def listen_for_move():
    global frame
    while True:
        if os.path.isfile("MOVE.truconf"):
            with open("MOVE.truconf") as f:
                seconds = f.read()
            os.remove("MOVE.truconf")

            global now
            now = True

            with open("UNPAUSE.truconf", 'w') as f:
                f.write("null")

            pygame.mixer.music.play(start=int(seconds))
            frame = int(seconds) * 15


reimu1 = Thread(target=listen_for_pause)
reimu2 = Thread(target=listen_for_unpause)
reimu3 = Thread(target=listen_for_disable)
reimu4 = Thread(target=listen_for_move)


# -------------------------
# ASCII Conversion
# -------------------------

def img2ascii(arr):
    arr = np.array(arr, dtype=np.uint8)
    lookup_table = np.empty(256, dtype=np.dtype('U1'))

    lookup_table[:100] = " "
    lookup_table[100:200] = "*"
    lookup_table[200:] = "#"

    return lookup_table[arr]


# -------------------------
# Main Logic
# -------------------------

if len(sys.argv) < 2:
    print("Usage: python3 main.py <youtube_url>")
    sys.exit()

url = sys.argv[1]

print("Checking terminal size! Please do not resize.")
time.sleep(0.5)

x = os.get_terminal_size().columns
y = os.get_terminal_size().lines
folder = f"converted/{x}x{y}"

# Ask rebuild
if os.path.exists("video.mp4") or os.path.exists("converted"):
    answer = input("Existing files detected. Rebuild everything? (y/n): ").lower()
    if answer == "y":
        print("Cleaning old files...")
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")
        if os.path.exists("audio.mp3"):
            os.remove("audio.mp3")
        if os.path.exists("converted"):
            shutil.rmtree("converted")
    else:
        print("Using existing files.")

# Download if needed
if not os.path.exists("video.mp4"):
    print("Downloading video...")
    subprocess.run([
        "yt-dlp",
        "-f", "best",
        url,
        "-o", "video.mp4"
    ])

# Extract audio safely
print("Extracting audio...")
subprocess.run([
    "ffmpeg",
    "-i", "video.mp4",
    "-q:a", "0",
    "-map", "a?",
    "audio.mp3",
    "-y"
])

# Generate frames
if not os.path.exists(folder):
    print("Generating frames...")
    os.makedirs(folder, exist_ok=True)
    subprocess.run([
        "ffmpeg",
        "-i", "video.mp4",
        "-vf", f"fps=15,scale={x}:{y}:flags=lanczos",
        f"{folder}/new%d.png"
    ])

# Load frames
print("Loading frames...")
data = []
import re

def numeric_sort(f):
    # Extract the number from new123.png
    return int(re.search(r'new(\d+)\.png', f).group(1))

files = sorted(
    [f for f in os.listdir(folder) if f.startswith("new") and f.endswith(".png")],
    key=numeric_sort
)

for f in files:
    with Image.open(f"{folder}/{f}") as img:
        data.append(img.convert("L").getdata())

frames = img2ascii(data)

# Audio playback
if os.path.exists("audio.mp3"):
    pygame.mixer.init()
    pygame.mixer.music.load("audio.mp3")
    pygame.mixer.music.play()

# Start threads
reimu1.start()
reimu2.start()
reimu3.start()
reimu4.start()

stopped = False
frame = 0
next_call = time.perf_counter()
now = False

# Playback loop
while True:
    if stopped:
        next_call = time.perf_counter() + 1/15
        continue

    if time.perf_counter() > next_call or now:
        if now:
            now = False

        next_call += 1/15
        os.system("clear")

        if frame >= len(frames):
            break

        print(''.join(frames[frame]))
        frame += 1
